import flet as ft
import os
import base64
from image_processing import calculate_circle_center_height
import cv2
import config


# 辅助函数：将OpenCV图像（numpy array）转换为Base64编码字符串，用于Flet显示。
def image_to_base64(img_np):
    """
    将OpenCV图像（numpy array）转换为Base64编码字符串，用于Flet显示。
    """
    # 确保图片是BGR格式，然后编码为PNG。PNG通常是无损的，适合Base64编码。
    is_success, buffer = cv2.imencode(".png", img_np)
    if not is_success:
        print("Error: Could not encode image to PNG buffer for Base64.")
        return None
    return base64.b64encode(buffer).decode('utf-8')


def main(page: ft.Page):
    page.title = config.APP_TITLE
    page.vertical_alignment = ft.MainAxisAlignment.START
    page.window_width = 1200
    page.window_height = 950
    page.scroll = ft.ScrollMode.ADAPTIVE

    # 设置页面主题色和字体
    page.theme = ft.Theme(
        color_scheme_seed="blue",
        font_family="Roboto",  # 可以尝试其他字体，例如 "Arial", "Noto Sans SC"
    )
    page.theme_mode = ft.ThemeMode.LIGHT  # 可以尝试 DARK

    # UI 元素
    selected_image_path1 = ft.Ref[ft.Text]()
    selected_image_path2 = ft.Ref[ft.Text]()
    image_preview1 = ft.Ref[ft.Image]()  # 用于显示图片
    image_preview2 = ft.Ref[ft.Image]()  # 用于显示图片
    result_text1 = ft.Ref[ft.Text]()
    result_text2 = ft.Ref[ft.Text]()

    # 加载指示器
    loading_indicator1 = ft.Ref[ft.ProgressRing]()
    loading_indicator2 = ft.Ref[ft.ProgressRing]()

    def process_and_display_image(file_path: str, preview_ref: ft.Ref[ft.Image], result_ref: ft.Ref[ft.Text],
                                  loading_ref: ft.Ref[ft.ProgressRing], is_image_1: bool):
        """
        处理单张图片并更新UI显示。
        Args:
            file_path (str): 图片文件的路径。
            preview_ref (ft.Ref[ft.Image]): 对应图片预览控件的引用。
            result_ref (ft.Ref[ft.Text]): 对应结果文本控件的引用。
            loading_ref (ft.Ref[ft.ProgressRing]): 对应加载指示器的引用。
            is_image_1 (bool): 是否是图片1，用于生成结果文本。
        """
        # 显示加载指示器，并隐藏图片和结果
        loading_ref.current.visible = True
        preview_ref.current.visible = False
        result_ref.current.value = "处理中..."
        result_ref.current.color = ft.Colors.BLACK
        page.update()

        # --- 1. 读取原始图片并转换为Base64显示 ---
        original_img_cv = cv2.imread(file_path)
        if original_img_cv is None:
            print(f"Error: Could not read original image from {file_path}")
            preview_ref.current.src_base64 = None
            preview_ref.current.visible = False
            result_ref.current.value = f"图片{1 if is_image_1 else 2}：无法读取图片。"
            result_ref.current.color = ft.Colors.RED_500  # 错误信息用红色
            loading_ref.current.visible = False  # 隐藏加载指示器
            page.update()
            return

        # 调整原始图片大小以适应预览框，避免过大图片导致UI卡顿
        h_orig, w_orig = original_img_cv.shape[:2]
        max_preview_dim = 400  # 预览框的最大尺寸
        if max(h_orig, w_orig) > max_preview_dim:
            scale = max_preview_dim / max(h_orig, w_orig)
            original_img_cv = cv2.resize(original_img_cv, (int(w_orig * scale), int(h_orig * scale)))

        base64_original_img = image_to_base64(original_img_cv)
        if base64_original_img:
            preview_ref.current.src_base64 = base64_original_img
            preview_ref.current.visible = True
        else:
            print("Error: Could not convert original image to Base64.")
            preview_ref.current.visible = False  # 隐藏图片
            result_ref.current.value = f"图片{1 if is_image_1 else 2}：图片编码失败。"
            result_ref.current.color = ft.Colors.RED_500
            loading_ref.current.visible = False
            page.update()
            return

        page.update()  # 立即更新 UI，显示原始图片（加载中或处理前）

        # --- 2. 进行图像处理 ---
        height, processed_img_cv = calculate_circle_center_height(file_path)

        # 隐藏加载指示器
        loading_ref.current.visible = False

        if processed_img_cv is not None:
            # 重新调整处理后的图片大小以适应预览框
            h_proc, w_proc = processed_img_cv.shape[:2]
            if max(h_proc, w_proc) > max_preview_dim:
                scale_proc = max_preview_dim / max(h_proc, w_proc)
                processed_img_cv = cv2.resize(processed_img_cv, (int(w_proc * scale_proc), int(h_proc * scale_proc)))

            base64_processed_img = image_to_base64(processed_img_cv)
            if base64_processed_img:
                preview_ref.current.src_base64 = base64_processed_img  # 更新为处理后的图片
            else:
                print("Error: Could not convert processed image to Base64, displaying original.")
                preview_ref.current.src_base64 = base64_original_img  # 回退显示原始图片
        else:
            print(f"Image {1 if is_image_1 else 2} processing failed, displaying original image.")
            preview_ref.current.src_base64 = base64_original_img  # 保持显示原始图片

        preview_ref.current.visible = True  # 确保图片可见

        # --- 3. 更新结果文本 ---
        if height is not None:
            result_ref.current.value = f"圆心高度 (图片{1 if is_image_1 else 2}): {height:.2f} 像素"
            result_ref.current.color = ft.Colors.BLUE_700  # 成功信息用蓝色
        else:
            result_ref.current.value = f"图片{1 if is_image_1 else 2}：未能识别到圆或V形块。"
            result_ref.current.color = ft.Colors.ORANGE_700  # 未识别用橙色

        page.update()  # 最终更新 UI，显示处理结果和处理后的图片

    def on_dialog_result1(e: ft.FilePickerResultEvent):
        if e.files:
            file_path = e.files[0].path
            selected_image_path1.current.value = os.path.basename(file_path)  # 只显示文件名
            process_and_display_image(file_path, image_preview1, result_text1, loading_indicator1, True)
        else:
            selected_image_path1.current.value = "未选择图片"
            image_preview1.current.src_base64 = None  # 清除图片
            image_preview1.current.visible = False
            result_text1.current.value = ""
            loading_indicator1.current.visible = False
            page.update()

    def on_dialog_result2(e: ft.FilePickerResultEvent):
        if e.files:
            file_path = e.files[0].path
            selected_image_path2.current.value = os.path.basename(file_path)  # 只显示文件名
            process_and_display_image(file_path, image_preview2, result_text2, loading_indicator2, False)
        else:
            selected_image_path2.current.value = "未选择图片"
            image_preview2.current.src_base64 = None
            image_preview2.current.visible = False
            result_text2.current.value = ""
            loading_indicator2.current.visible = False
            page.update()

    file_picker1 = ft.FilePicker(on_result=on_dialog_result1)
    file_picker2 = ft.FilePicker(on_result=on_dialog_result2)

    page.overlay.append(file_picker1)
    page.overlay.append(file_picker2)

    page.add(
        ft.AppBar(
            title=ft.Text("V 形块夹持圆心高度测量工具", color=ft.Colors.WHITE),
            bgcolor=ft.Colors.BLUE_700,  # 应用栏背景色
            center_title=True,
        ),
        ft.Container(
            content=ft.Column(
                [
                    ft.Row(
                        [
                            # 图片 1 列
                            ft.Column(
                                [
                                    ft.Text("图片 1:", size=18, weight=ft.FontWeight.BOLD),
                                    ft.ElevatedButton(
                                        "选择图片",
                                        icon=ft.Icons.UPLOAD_FILE,
                                        icon_color=ft.Colors.WHITE,  # 图标颜色
                                        on_click=lambda _: file_picker1.pick_files(
                                            allow_multiple=False,
                                            allowed_extensions=["png", "jpg", "jpeg", "gif"]
                                        ),
                                        style=ft.ButtonStyle(
                                            bgcolor={ft.ControlState.DEFAULT: ft.Colors.BLUE_500},
                                            color={ft.ControlState.DEFAULT: ft.Colors.WHITE},
                                            padding=ft.padding.symmetric(horizontal=20, vertical=10),
                                            shape=ft.RoundedRectangleBorder(radius=8)
                                        )
                                    ),
                                    ft.Text(ref=selected_image_path1, value="未选择图片", size=14,
                                            color=ft.Colors.GREY_700),
                                    ft.Card(  # 使用 Card 包装图片预览
                                        content=ft.Container(
                                            content=ft.Stack(  # 使用 Stack 放置图片和加载指示器
                                                [
                                                    ft.Image(ref=image_preview1, visible=False, width=400, height=300,
                                                             fit=ft.ImageFit.CONTAIN),
                                                    ft.Container(  # 加载指示器容器
                                                        content=ft.ProgressRing(ref=loading_indicator1, visible=False,
                                                                                stroke_width=4),
                                                        alignment=ft.alignment.center,
                                                        expand=True,
                                                        visible=True  # 默认可见，但 ProgressRing 本身是隐藏的
                                                    )
                                                ],
                                                alignment=ft.alignment.center,
                                            ),
                                            alignment=ft.alignment.center,
                                            margin=ft.margin.all(10),  # Card 内部边距
                                            width=400,  # 图片预览区域宽度
                                            height=300,  # 图片预览区域高度
                                        ),
                                        elevation=5,  # 阴影效果
                                        shape=ft.RoundedRectangleBorder(radius=10)  # 圆角
                                    ),
                                    ft.Text(ref=result_text1, value="", size=16, weight=ft.FontWeight.BOLD,
                                            color=ft.Colors.BLUE_700),
                                ],
                                alignment=ft.MainAxisAlignment.START,
                                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                expand=True,
                                spacing=15  # 增加控件间距
                            ),
                            ft.VerticalDivider(width=1, color=ft.Colors.BLUE_GREY_200),  # 细分界线
                            # 图片 2 列
                            ft.Column(
                                [
                                    ft.Text("图片 2:", size=18, weight=ft.FontWeight.BOLD),
                                    ft.ElevatedButton(
                                        "选择图片",
                                        icon=ft.Icons.UPLOAD_FILE,
                                        icon_color=ft.Colors.WHITE,
                                        on_click=lambda _: file_picker2.pick_files(
                                            allow_multiple=False,
                                            allowed_extensions=["png", "jpg", "jpeg", "gif"]
                                        ),
                                        style=ft.ButtonStyle(
                                        ###########
                                            bgcolor={ft.ControlState.DEFAULT: ft.Colors.BLUE_500},
                                            color={ft.ControlState.DEFAULT: ft.Colors.WHITE},
                                            padding=ft.padding.symmetric(horizontal=20, vertical=10),
                                            shape=ft.RoundedRectangleBorder(radius=8)
                                        )
                                    ),
                                    ft.Text(ref=selected_image_path2, value="未选择图片", size=14,
                                            color=ft.Colors.GREY_700),
                                    ft.Card(  # 使用 Card 包装图片预览
                                        content=ft.Container(
                                            content=ft.Stack(  # 使用 Stack 放置图片和加载指示器
                                                [
                                                    ft.Image(ref=image_preview2, visible=False, width=400, height=300,
                                                             fit=ft.ImageFit.CONTAIN),
                                                    ft.Container(  # 加载指示器容器
                                                        content=ft.ProgressRing(ref=loading_indicator2, visible=False,
                                                                                stroke_width=4),
                                                        alignment=ft.alignment.center,
                                                        expand=True,
                                                        visible=True
                                                    )
                                                ],
                                                alignment=ft.alignment.center,
                                            ),
                                            alignment=ft.alignment.center,
                                            margin=ft.margin.all(10),
                                            width=400,
                                            height=300,
                                        ),
                                        elevation=5,
                                        shape=ft.RoundedRectangleBorder(radius=10)
                                    ),
                                    ft.Text(ref=result_text2, value="", size=16, weight=ft.FontWeight.BOLD,
                                            color=ft.Colors.BLUE_700),
                                ],
                                alignment=ft.MainAxisAlignment.START,
                                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                expand=True,
                                spacing=15
                            )
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_AROUND,
                        vertical_alignment=ft.CrossAxisAlignment.START,
                        expand=True,
                        spacing=30  # 两列之间的大间距
                    )
                ],
                expand=True,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER  # 整体内容的内边距
            ),
            expand=True,
            margin=ft.margin.all(20),  # 整个主内容的外部边距
            padding=ft.padding.all(20),
            border_radius=ft.border_radius.all(15),
            bgcolor=ft.Colors.WHITE,  # 主内容区背景色
            shadow=ft.BoxShadow(  # 增加阴影效果
                spread_radius=1,
                blur_radius=15,
                color=ft.Colors.BLACK26,
                offset=ft.Offset(0, 5),
            ),
        )
    )


if __name__ == "__main__":
    # ft.app(target=main)
    # 使用 FLET_APP 视图启动应用程序，使其以桌面应用的形式运行
    # 这将更严格地控制窗口大小，并提供窗口控件（最大化、最小化、关闭）
    ft.app(target=main, view=ft.AppView.FLET_APP)
