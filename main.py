import flet as ft
import os
import base64
from image_processing import calculate_circle_center_height
import cv2
import numpy as np  # 确保这一行还在，因为cv2.imencode可能返回numpy array
import config


# 辅助函数：将OpenCV图像（numpy array）转换为Base64编码字符串，用于Flet显示。
def image_to_base64(img_np):
    """
    将OpenCV图像（numpy array）转换为Base64编码字符串，用于Flet显示。
    """
    is_success, buffer = cv2.imencode(".png", img_np)
    if not is_success:
        print("Error: Could not encode image to PNG buffer for Base64.")
        return None
    return base64.b64encode(buffer).decode('utf-8')


def main(page: ft.Page):
    page.title = config.APP_TITLE
    page.vertical_alignment = ft.MainAxisAlignment.START
    page.window_width = config.WINDOW_WIDTH
    page.window_height = config.WINDOW_HEIGHT
    page.scroll = ft.ScrollMode.ADAPTIVE

    page.theme = ft.Theme(
        color_scheme_seed="blue",
        font_family="Roboto",
    )
    page.theme_mode = ft.ThemeMode.LIGHT

    # UI 元素
    selected_image_path1 = ft.Ref[ft.Text]()
    selected_image_path2 = ft.Ref[ft.Text]()
    image_preview1 = ft.Ref[ft.Image]()
    image_preview2 = ft.Ref[ft.Image]()
    result_text1 = ft.Ref[ft.Text]()
    result_text2 = ft.Ref[ft.Text]()

    loading_indicator1 = ft.Ref[ft.ProgressRing]()
    loading_indicator2 = ft.Ref[ft.ProgressRing]()

    # 新增：用于存储已上传图片的路径，以便“开始计算”按钮使用
    uploaded_file_path1 = ft.Ref[str]()
    uploaded_file_path2 = ft.Ref[str]()

    # 新增：开始计算按钮，先设置为不可用
    start_calculate_button = ft.Ref[ft.ElevatedButton]()

    def update_start_calculate_button_state():
        """根据两张图片是否都已上传来更新“开始计算”按钮的状态"""
        if uploaded_file_path1.current and uploaded_file_path2.current:
            start_calculate_button.current.disabled = False
        else:
            start_calculate_button.current.disabled = True
        page.update()

    def display_original_image(file_path: str, preview_ref: ft.Ref[ft.Image], result_ref: ft.Ref[ft.Text],
                               is_image_1: bool):
        """
        只显示原始图片，不进行计算。
        """
        result_ref.current.value = ""  # 清空之前的计算结果
        result_ref.current.color = ft.Colors.BLACK

        original_img_cv = cv2.imread(file_path)
        if original_img_cv is None:
            print(f"Error: Could not read original image from {file_path}")
            preview_ref.current.src_base64 = None
            preview_ref.current.visible = False
            result_ref.current.value = f"图片{1 if is_image_1 else 2}：无法读取图片。"
            result_ref.current.color = ft.Colors.RED_500
            page.update()
            return False  # 表示加载失败

        # 调整原始图片大小以适应预览框
        h_orig, w_orig = original_img_cv.shape[:2]
        max_preview_dim = config.MAX_PREVIEW_DIM
        if max(h_orig, w_orig) > max_preview_dim:
            scale = max_preview_dim / max(h_orig, w_orig)
            original_img_cv = cv2.resize(original_img_cv, (int(w_orig * scale), int(h_orig * scale)))

        base64_original_img = image_to_base64(original_img_cv)
        if base64_original_img:
            preview_ref.current.src_base64 = base64_original_img
            preview_ref.current.visible = True
            page.update()
            return True  # 表示加载成功
        else:
            print("Error: Could not convert original image to Base64.")
            preview_ref.current.visible = False
            result_ref.current.value = f"图片{1 if is_image_1 else 2}：图片编码失败。"
            result_ref.current.color = ft.Colors.RED_500
            page.update()
            return False  # 表示加载失败

    def perform_calculation(file_path: str, preview_ref: ft.Ref[ft.Image], result_ref: ft.Ref[ft.Text],
                            loading_ref: ft.Ref[ft.ProgressRing], is_image_1: bool):
        """
        执行图像计算并更新显示为处理后的图片。
        """
        # 显示加载指示器，并更新文本
        loading_ref.current.visible = True
        preview_ref.current.visible = False  # 隐藏图片，显示加载圈
        result_ref.current.value = "计算中..."
        result_ref.current.color = ft.Colors.BLACK
        page.update()

        height, processed_img_cv = calculate_circle_center_height(file_path)

        loading_ref.current.visible = False  # 隐藏加载指示器

        # 如果计算失败，则重新显示原始图片并给出提示
        if processed_img_cv is None:
            print(f"Image {1 if is_image_1 else 2} processing failed.")
            # 尝试重新加载并显示原始图片
            if not display_original_image(file_path, preview_ref, result_ref, is_image_1):
                # 如果原始图片也无法显示，则隐藏预览
                preview_ref.current.visible = False
            result_ref.current.value = f"图片{1 if is_image_1 else 2}：未能识别到圆或V形块。"
            result_ref.current.color = ft.Colors.ORANGE_700
            page.update()
            return

        # 调整处理后的图片大小以适应预览框
        h_proc, w_proc = processed_img_cv.shape[:2]
        max_preview_dim = config.MAX_PREVIEW_DIM
        if max(h_proc, w_proc) > max_preview_dim:
            scale_proc = max_preview_dim / max(h_proc, w_proc)
            processed_img_cv = cv2.resize(processed_img_cv, (int(w_proc * scale_proc), int(h_proc * scale_proc)))

        base64_processed_img = image_to_base64(processed_img_cv)
        if base64_processed_img:
            preview_ref.current.src_base64 = base64_processed_img
            preview_ref.current.visible = True
        else:
            print("Error: Could not convert processed image to Base64 after calculation, displaying original.")
            # 如果处理后的图片编码失败，尝试回退显示原始图片
            if not display_original_image(file_path, preview_ref, result_ref, is_image_1):
                preview_ref.current.visible = False  # 如果原始图片也无法显示
            result_ref.current.value = f"图片{1 if is_image_1 else 2}：处理后的图片编码失败。"
            result_ref.current.color = ft.Colors.RED_500
            page.update()
            return

        # 更新结果文本
        if height is not None:
            result_ref.current.value = f"圆心高度 (图片{1 if is_image_1 else 2}): {height:.2f} 像素"
            result_ref.current.color = ft.Colors.BLUE_700
        else:
            result_ref.current.value = f"图片{1 if is_image_1 else 2}：未能识别到圆或V形块。"
            result_ref.current.color = ft.Colors.ORANGE_700

        page.update()

    def on_dialog_result1(e: ft.FilePickerResultEvent):
        if e.files:
            file_path = e.files[0].path
            uploaded_file_path1.current = file_path  # 存储文件路径
            selected_image_path1.current.value = os.path.basename(file_path)
            display_original_image(file_path, image_preview1, result_text1, True)
            update_start_calculate_button_state()  # 更新按钮状态
        else:
            uploaded_file_path1.current = None
            selected_image_path1.current.value = "未选择图片"
            image_preview1.current.src_base64 = None
            image_preview1.current.visible = False
            result_text1.current.value = ""
            loading_indicator1.current.visible = False
            update_start_calculate_button_state()
            page.update()

    def on_dialog_result2(e: ft.FilePickerResultEvent):
        if e.files:
            file_path = e.files[0].path
            uploaded_file_path2.current = file_path  # 存储文件路径
            selected_image_path2.current.value = os.path.basename(file_path)
            display_original_image(file_path, image_preview2, result_text2, False)
            update_start_calculate_button_state()  # 更新按钮状态
        else:
            uploaded_file_path2.current = None
            selected_image_path2.current.value = "未选择图片"
            image_preview2.current.src_base64 = None
            image_preview2.current.visible = False
            result_text2.current.value = ""
            loading_indicator2.current.visible = False
            update_start_calculate_button_state()
            page.update()

    def on_start_calculate_click(e):
        """点击“开始计算”按钮时的处理函数"""
        # 确保两张图片都已上传才能开始计算
        if uploaded_file_path1.current:
            perform_calculation(uploaded_file_path1.current, image_preview1, result_text1, loading_indicator1, True)
        if uploaded_file_path2.current:
            perform_calculation(uploaded_file_path2.current, image_preview2, result_text2, loading_indicator2, False)
        # 计算完成后，按钮可能仍然是启用状态，因为图片还在。如果你希望计算完再点击时重新计算，可以不禁用。
        # 如果希望计算完后按钮变为不可用，直到重新选择图片，可以在这里禁用。
        # start_calculate_button.current.disabled = True
        # page.update()

    file_picker1 = ft.FilePicker(on_result=on_dialog_result1)
    file_picker2 = ft.FilePicker(on_result=on_dialog_result2)

    page.overlay.append(file_picker1)
    page.overlay.append(file_picker2)

    # 初始化按钮状态
    start_calculate_button.current = ft.ElevatedButton(
        "开始计算",
        icon=ft.Icons.PLAY_ARROW,
        icon_color=ft.Colors.WHITE,
        on_click=on_start_calculate_click,
        disabled=True,  # 初始状态禁用
        style=ft.ButtonStyle(
            bgcolor={ft.ControlState.DEFAULT: ft.Colors.GREEN_500},
            color={ft.ControlState.DEFAULT: ft.Colors.WHITE},
            padding=ft.padding.symmetric(horizontal=30, vertical=15),
            shape=ft.RoundedRectangleBorder(radius=10)
        )
    )

    page.add(
        ft.AppBar(
            title=ft.Text(config.APP_TITLE, color=ft.Colors.WHITE),
            bgcolor=ft.Colors.BLUE_700,
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
                                        icon_color=ft.Colors.WHITE,
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
                                    ft.Card(
                                        content=ft.Container(
                                            content=ft.Stack(
                                                [
                                                    ft.Image(ref=image_preview1, visible=False, width=400, height=300,
                                                             fit=ft.ImageFit.CONTAIN),
                                                    ft.Container(
                                                        content=ft.ProgressRing(ref=loading_indicator1, visible=False,
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
                                    ft.Text(ref=result_text1, value="", size=16, weight=ft.FontWeight.BOLD,
                                            color=ft.Colors.BLUE_700),
                                ],
                                alignment=ft.MainAxisAlignment.START,
                                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                expand=True,
                                spacing=15
                            ),
                            ft.VerticalDivider(width=1, color=ft.Colors.BLUE_GREY_200),
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
                                            bgcolor={ft.ControlState.DEFAULT: ft.Colors.BLUE_500},
                                            color={ft.ControlState.DEFAULT: ft.Colors.WHITE},
                                            padding=ft.padding.symmetric(horizontal=20, vertical=10),
                                            shape=ft.RoundedRectangleBorder(radius=8)
                                        )
                                    ),
                                    ft.Text(ref=selected_image_path2, value="未选择图片", size=14,
                                            color=ft.Colors.GREY_700),
                                    ft.Card(
                                        content=ft.Container(
                                            content=ft.Stack(
                                                [
                                                    ft.Image(ref=image_preview2, visible=False, width=400, height=300,
                                                             fit=ft.ImageFit.CONTAIN),
                                                    ft.Container(
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
                        spacing=30
                    ),
                    # 新增：开始计算按钮
                    ft.Container(
                        content=start_calculate_button.current,
                        margin=ft.margin.only(top=30, bottom=20),  # 按钮上下间距
                    )
                ],
                expand=True,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER
            ),
            expand=True,
            margin=ft.margin.all(20),
            padding=ft.padding.all(20),
            border_radius=ft.border_radius.all(15),
            bgcolor=ft.Colors.WHITE,
            shadow=ft.BoxShadow(
                spread_radius=1,
                blur_radius=15,
                color=ft.Colors.BLACK26,
                offset=ft.Offset(0, 5),
            ),
        )
    )

    # 首次加载时，更新按钮状态
    update_start_calculate_button_state()


if __name__ == "__main__":
    ft.app(target=main, view=ft.AppView.FLET_APP)