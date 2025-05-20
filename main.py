import flet as ft
import os
import base64
from image_processing import calculate_circle_center_height
import cv2
import numpy as np


# 不再需要临时目录，因为我们直接使用 Base64 编码的图片数据

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
    page.title = "V 形块夹持圆心高度测量"
    page.vertical_alignment = ft.MainAxisAlignment.START
    page.window_width = 1000
    page.window_height = 800
    page.scroll = ft.ScrollMode.ADAPTIVE

    # UI 元素
    selected_image_path1 = ft.Ref[ft.Text]()
    selected_image_path2 = ft.Ref[ft.Text]()
    image_preview1 = ft.Ref[ft.Image]()  # 用于显示图片
    image_preview2 = ft.Ref[ft.Image]()  # 用于显示图片
    result_text1 = ft.Ref[ft.Text]()
    result_text2 = ft.Ref[ft.Text]()

    def process_and_display_image(file_path: str, preview_ref: ft.Ref[ft.Image], result_ref: ft.Ref[ft.Text],
                                  is_image_1: bool):
        """
  处理单张图片并更新UI显示。
  Args:
      file_path (str): 图片文件的路径。
      preview_ref (ft.Ref[ft.Image]): 对应图片预览控件的引用。
      result_ref (ft.Ref[ft.Text]): 对应结果文本控件的引用。
      is_image_1 (bool): 是否是图片1，用于生成结果文本。
  """
        # --- 1. 读取原始图片并转换为Base64显示 ---
        original_img_cv = cv2.imread(file_path)
        if original_img_cv is None:
            print(f"Error: Could not read original image from {file_path}")
            preview_ref.current.src_base64 = None
            preview_ref.current.visible = False
            result_ref.current.value = f"图片{1 if is_image_1 else 2}：无法读取图片。"
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
        page.update()  # 立即更新 UI，显示原始图片（加载中或处理前）

        # --- 2. 进行图像处理 ---
        height, processed_img_cv = calculate_circle_center_height(file_path)

        if processed_img_cv is not None:
            base64_processed_img = image_to_base64(processed_img_cv)
            if base64_processed_img:
                preview_ref.current.src_base64 = base64_processed_img  # 更新为处理后的图片
                # preview_ref.current.visible 已经设置为 True
            else:
                print("Error: Could not convert processed image to Base64.")
                preview_ref.current.src_base64 = base64_original_img  # 回退显示原始图片
        else:
            print(f"Image {1 if is_image_1 else 2} processing failed, displaying original image.")
            preview_ref.current.src_base64 = base64_original_img  # 保持显示原始图片
            preview_ref.current.visible = True  # 确保图片可见

        # --- 3. 更新结果文本 ---
        if height is not None:
            result_ref.current.value = f"圆心高度 (图片{1 if is_image_1 else 2}): {height:.2f} 像素"
        else:
            result_ref.current.value = f"图片{1 if is_image_1 else 2}：未能识别到圆或V形块。"

        page.update()  # 最终更新 UI，显示处理结果和处理后的图片

    def on_dialog_result1(e: ft.FilePickerResultEvent):
        if e.files:
            file_path = e.files[0].path
            selected_image_path1.current.value = file_path
            process_and_display_image(file_path, image_preview1, result_text1, True)
        else:
            selected_image_path1.current.value = "未选择图片"
            image_preview1.current.src_base64 = None  # 清除图片
            image_preview1.current.visible = False
            result_text1.current.value = ""
            page.update()

    def on_dialog_result2(e: ft.FilePickerResultEvent):
        if e.files:
            file_path = e.files[0].path
            selected_image_path2.current.value = file_path
            process_and_display_image(file_path, image_preview2, result_text2, False)
        else:
            selected_image_path2.current.value = "未选择图片"
            image_preview2.current.src_base64 = None
            image_preview2.current.visible = False
            result_text2.current.value = ""
            page.update()

    file_picker1 = ft.FilePicker(on_result=on_dialog_result1)
    file_picker2 = ft.FilePicker(on_result=on_dialog_result2)

    page.overlay.append(file_picker1)
    page.overlay.append(file_picker2)

    page.add(
        ft.AppBar(title=ft.Text("V 形块夹持圆心高度测量工具")),
        ft.Column(
            [
                ft.Row(
                    [
                        ft.Column(
                            [
                                ft.Text("图片 1:"),
                                ft.ElevatedButton(
                                    "选择图片",
                                    icon=ft.Icons.UPLOAD_FILE,
                                    on_click=lambda _: file_picker1.pick_files(
                                        allow_multiple=False,
                                        allowed_extensions=["png", "jpg", "jpeg", "gif"]
                                    )
                                ),
                                ft.Text(ref=selected_image_path1, value="未选择图片"),
                                ft.Container(
                                    content=ft.Image(ref=image_preview1, visible=False, width=400, height=300,
                                                     fit=ft.ImageFit.CONTAIN),
                                    alignment=ft.alignment.center,
                                    margin=ft.margin.only(top=10, bottom=10),
                                    border_radius=ft.border_radius.all(5),
                                    border=ft.border.all(1, ft.Colors.BLUE_GREY_100),
                                    width=420,
                                    height=320,
                                ),
                                ft.Text(ref=result_text1, value="", size=16, weight=ft.FontWeight.BOLD),
                            ],
                            alignment=ft.MainAxisAlignment.START,
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            expand=True
                        ),
                        ft.VerticalDivider(),
                        ft.Column(
                            [
                                ft.Text("图片 2:"),
                                ft.ElevatedButton(
                                    "选择图片",
                                    icon=ft.Icons.UPLOAD_FILE,
                                    on_click=lambda _: file_picker2.pick_files(
                                        allow_multiple=False,
                                        allowed_extensions=["png", "jpg", "jpeg", "gif"]
                                    )
                                ),
                                ft.Text(ref=selected_image_path2, value="未选择图片"),
                                ft.Container(
                                    content=ft.Image(ref=image_preview2, visible=False, width=400, height=300,
                                                     fit=ft.ImageFit.CONTAIN),
                                    alignment=ft.alignment.center,
                                    margin=ft.margin.only(top=10, bottom=10),
                                    border_radius=ft.border_radius.all(5),
                                    border=ft.border.all(1, ft.Colors.BLUE_GREY_100),
                                    width=420,
                                    height=320,
                                ),
                                ft.Text(ref=result_text2, value="", size=16, weight=ft.FontWeight.BOLD),
                            ],
                            alignment=ft.MainAxisAlignment.START,
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            expand=True
                        )
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_AROUND,
                    vertical_alignment=ft.CrossAxisAlignment.START,
                    expand=True
                )
            ],
            expand=True,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER
        )
    )


if __name__ == "__main__":
    ft.app(target=main)