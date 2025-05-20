import cv2
import numpy as np

def calculate_circle_center_height(image_path):
    """
    检测图像中的圆，并计算其圆心到底座的高度。
    假设底座是图像的最底部边缘。

    Args:
        image_path (str): 图像文件的路径。

    Returns:
        tuple: (height, img_with_annotations)
               height (float): 圆心到底座的高度（像素单位）。
                               如果没有检测到圆，则返回 None。
               img_with_annotations (numpy.ndarray): 带有圆和高度标注的图像。
    """
    try:
        img = cv2.imread(image_path)
        if img is None:
            raise FileNotFoundError(f"无法加载图像：{image_path}")

        output_img = img.copy()
        height, width, _ = img.shape

        # 1. 预处理图像
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        # 增加高斯模糊有助于减少噪声，使圆检测更稳定
        blurred = cv2.GaussianBlur(gray, (9, 9), 2)

        # 2. 检测圆
        # 参数说明：
        # - image: 8位，单通道，灰度图像。
        # - method: 检测方法，HOUGH_GRADIENT是目前唯一实现的方法。
        # - dp: 累加器分辨率与图像分辨率的反比。dp=1表示与图像分辨率相同。
        # - minDist: 两个不同圆圆心之间的最小距离。
        # - param1: Canny边缘检测的高阈值。
        # - param2: 累加器阈值。越小，检测到的假圆越多；越大，漏掉的真圆越多。
        # - minRadius: 最小圆半径。
        # - maxRadius: 最大圆半径。
        circles = cv2.HoughCircles(blurred, cv2.HOUGH_GRADIENT, dp=1, minDist=50,
                                   param1=100, param2=30, minRadius=20, maxRadius=200)

        circle_center_y = None
        base_line_y = height - 1 # 假设底座是图像的最底部边缘

        if circles is not None:
            # HoughCircles返回的圆是(x, y, r)格式，且可能检测到多个
            circles = np.uint16(np.around(circles))
            # 为了简化，我们假设只处理第一个检测到的圆
            # 如果需要处理多个圆，则需要遍历 circles
            x, y, r = circles[0][0] # 获取第一个圆的圆心和半径

            circle_center_y = y

            # 3. 绘制检测到的圆和圆心
            cv2.circle(output_img, (x, y), r, (0, 255, 0), 2) # 圆周
            cv2.circle(output_img, (x, y), 2, (0, 0, 255), 3) # 圆心

            # 4. 绘制底座线
            cv2.line(output_img, (0, base_line_y), (width, base_line_y), (255, 0, 0), 2)

            # 5. 计算高度
            # 这里的y轴是图像坐标系，原点在左上角，y向下增长
            # 所以圆心到底座的高度是 base_line_y - circle_center_y
            calculated_height = base_line_y - circle_center_y

            # 6. 标注高度
            # 绘制高度线
            cv2.line(output_img, (x, y), (x, base_line_y), (0, 255, 255), 1)
            # 标注高度文本
            text_pos_x = x + 10
            text_pos_y = int((y + base_line_y) / 2)
            cv2.putText(output_img, f"Height: {calculated_height:.2f}px",
                        (text_pos_x, text_pos_y), cv2.FONT_HERSHEY_SIMPLEX, 0.7,
                        (0, 255, 255), 2)

            return calculated_height, output_img
        else:
            print("未检测到任何圆。")
            return None, output_img

    except FileNotFoundError as e:
        print(e)
        return None, None
    except Exception as e:
        print(f"处理图像时发生错误: {e}")
        return None, None

# 示例用法：
if __name__ == '__main__':
    # 创建一个简单的图像文件进行测试
    # 注意：在实际使用时，请替换为您的图像路径
    # 例如：
    # from PIL import Image, ImageDraw
    # img_size = (300, 300)
    # test_img = Image.new('RGB', img_size, color = 'white')
    # draw = ImageDraw.Draw(test_img)
    # draw.ellipse((100, 50, 200, 150), fill='blue', outline='blue')
    # test_img_path = "test_circle.png"
    # test_img.save(test_img_path)

    # 假设你有一个名为 'test_circle.png' 的图像文件在当前目录下
    # 或者你可以自己创建一个简单的图像文件
    # 比如在paint或者其他绘图工具中画一个圆，然后保存为png
    # 或者运行下面的代码创建一个简单的测试图像

    # 简单生成一个带圆的图像用于测试
    dummy_image = np.zeros((400, 400, 3), dtype=np.uint8)
    cv2.circle(dummy_image, (200, 150), 70, (0, 255, 0), -1) # 在(200, 150)画一个半径70的绿色圆
    test_image_path = "dummy_circle_test.png"
    cv2.imwrite(test_image_path, dummy_image)


    height, annotated_img = calculate_circle_center_height(test_image_path)

    if height is not None:
        print(f"圆心到底座的高度为: {height:.2f} 像素")
        cv2.imshow("检测结果", annotated_img)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
    else:
        print("未能计算高度。")