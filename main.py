import flet as ft
import os
import base64
from image_processing import calculate_circle_center_height
import cv2
import numpy as np

# 保存处理后的图片的临时目录
TEMP_DIR = "temp_processed_images"
os.makedirs(TEMP_DIR, exist_ok=True)


def main(page: ft.Page):
    page.title = "V 形块夹持圆心高度测量"
    page.vertical_alignment = ft.MainAxisAlignment.START
    page.window_width = 1000
    page.window_height = 800
    page.scroll = ft.ScrollMode.ADAPTIVE

    # UI 元素
    selected_image_path1 = ft.Ref[ft.Text]()
    selected_image_path2 = ft.Ref[ft.Text]()
    image_preview1 = ft.Ref[ft.Image]()
    image_preview2 = ft.Ref[ft.Image]()
    result_text1 = ft.Ref[ft.Text]()
    result_text2 = ft.Ref[ft.Text]()

    def image_to_base64(img_np):
        """将OpenCV图像（numpy array）转换为Base64编码字符串，用于Flet显示。"""
        _, buffer = cv2.imencode('.png', img_np)
        return base64.b64encode(buffer).decode('utf-8')

    def on_dialog_result1(e: ft.FilePickerResultEvent):
        if e.files:
            file_path = e.files[0].path
            selected_image_path1.current.value = file_path

            height, processed_img = calculate_circle_center_height(file_path)

            if processed_img is not None:
                # 将处理后的图像保存到临时文件并显示
                temp_file_name = os.path.join(TEMP_DIR, f"processed_1_{os.path.basename(file_path)}")
                cv2.imwrite(temp_file_name, processed_img)
                image_preview1.current.src = temp_file_name
                image_preview1.current.visible = True
            else:
                image_preview1.current.src = None
                image_preview1.current.visible = False

            if height is not None:
                result_text1.current.value = f"圆心高度 (图片1): {height:.2f} 像素"
            else:
                result_text1.current.value = "图片1：未能识别到圆或V形块。"
        else:
            selected_image_path1.current.value = "未选择图片"
            image_preview1.current.src = None
            image_preview1.current.visible = False
            result_text1.current.value = ""

        page.update()

    def on_dialog_result2(e: ft.FilePickerResultEvent):
        if e.files:
            file_path = e.files[0].path
            selected_image_path2.current.value = file_path

            height, processed_img = calculate_circle_center_height(file_path)

            if processed_img is not None:
                temp_file_name = os.path.join(TEMP_DIR, f"processed_2_{os.path.basename(file_path)}")
                cv2.imwrite(temp_file_name, processed_img)
                image_preview2.current.src = temp_file_name
                image_preview2.current.visible = True
            else:
                image_preview2.current.src = None
                image_preview2.current.visible = False

            if height is not None:
                result_text2.current.value = f"圆心高度 (图片2): {height:.2f} 像素"
            else:
                result_text2.current.value = "图片2：未能识别到圆或V形块。"
        else:
            selected_image_path2.current.value = "未选择图片"
            image_preview2.current.src = None
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