import cv2
import numpy as np


def calculate_circle_center_height(image_path):
    """
    识别图片中V形块夹持的圆的圆心高度。
    高度定义为圆心到V形块底部顶点的垂直距离。

    Args:
        image_path (str): 图片文件的路径。

    Returns:
        tuple: (height, annotated_image)
               height (float): 圆心高度，如果未能识别到圆或V形块，则返回None。
               annotated_image (numpy.ndarray): 带有识别结果标注的图片（OpenCV BGR格式）。
    """
    img = cv2.imread(image_path)
    if img is None:
        print(f"Error: Could not read image from {image_path}")
        return None, None

    # 将图像尺寸调整到合理大小，以便于处理和显示，同时保持比例
    max_dim = 800
    h, w = img.shape[:2]
    if max(h, w) > max_dim:
        scale = max_dim / max(h, w)
        img = cv2.resize(img, (int(w * scale), int(h * scale)))

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blurred, 50, 150)

    # --- 1. 检测 V 形块的底部顶点 ---
    lines = cv2.HoughLinesP(edges, 1, np.pi / 180, threshold=50, minLineLength=50, maxLineGap=10)
    v_lines = []
    if lines is not None:
        for line in lines:
            x1, y1, x2, y2 = line[0]
            angle_rad = np.arctan2(y2 - y1, x2 - x1)
            angle_deg = np.degrees(angle_rad)
            # 筛选出斜率接近 V 形块边缘的线 (例如，倾斜角在 30-60 度或 120-150 度之间)
            # 对于您提供的样例图片，V形块的线条较为垂直，更接近 90度左右的斜线。
            # 如果是标准V形块，夹角可能在 30-60 度。这里根据您的图，调整一下角度范围
            # 假设两条线是左倾斜和右倾斜的，绝对值在 30-60 或 120-150
            # 考虑到您提供的图片，V形块的直线可能更接近 +/- 45 度左右
            if (abs(angle_deg) > 30 and abs(angle_deg) < 80) or \
                    (abs(angle_deg) > 100 and abs(angle_deg) < 150):
                v_lines.append(line[0])

    v_bottom_point = None
    if len(v_lines) >= 2:
        # 简化处理：找到两条线的交点作为V形块的底部顶点
        # 实际项目中，需要更鲁棒的算法来匹配并找到正确的V形两条边和它们的交点

        potential_intersections = []
        for i in range(len(v_lines)):
            for j in range(i + 1, len(v_lines)):
                line1 = v_lines[i]
                line2 = v_lines[j]

                x1, y1, x2, y2 = line1
                x3, y3, x4, y4 = line2

                # 计算斜率
                denom1 = (x2 - x1)
                denom2 = (x4 - x3)

                m1 = (y2 - y1) / denom1 if denom1 != 0 else float('inf')
                m2 = (y4 - y3) / denom2 if denom2 != 0 else float('inf')

                # 如果平行或近似平行，则跳过
                if abs(m1 - m2) < 0.1:  # 允许微小误差
                    continue

                if denom1 == 0:  # line1 is vertical
                    x_intersect = x1
                    y_intersect = m2 * (x1 - x3) + y3
                elif denom2 == 0:  # line2 is vertical
                    x_intersect = x3
                    y_intersect = m1 * (x3 - x1) + y1
                else:
                    x_intersect = ((m1 * x1 - y1) - (m2 * x3 - y3)) / (m1 - m2)
                    y_intersect = m1 * (x_intersect - x1) + y1

                # 检查交点是否在图像范围内，并且Y坐标在图像底部区域
                if 0 <= x_intersect < img.shape[1] and 0 <= y_intersect < img.shape[0]:
                    # 仅考虑图像下半部分的交点，避免检测到上部无关的交点
                    if y_intersect > img.shape[0] * 0.5:  # 假设V形块在图片下半部分
                        potential_intersections.append((int(x_intersect), int(y_intersect)))

        # 找到y坐标最低的交点作为V形块的底部顶点 (假设V形开口向上)
        if potential_intersections:
            v_bottom_point = min(potential_intersections, key=lambda p: p[1])
            cv2.circle(img, v_bottom_point, 5, (0, 255, 0), -1)  # 绿色圆点标记V形块底部
            # 绘制检测到的V形线（调试用）
            # for line in v_lines:
            #     cv2.line(img, (line[0], line[1]), (line[2], line[3]), (255, 0, 0), 2)

    # --- 2. 检测圆 ---
    # 霍夫圆变换参数可能需要针对您的实际图片进行调整
    # 图像分辨率、圆的大小、图像清晰度等都会影响参数的选择
    circles = cv2.HoughCircles(
        blurred,
        cv2.HOUGH_GRADIENT,
        dp=1.2,  # 累加器分辨率与图像分辨率的反比。值越大，累加器分辨率越低，处理速度快，但可能漏掉细节。
        minDist=100,  # 两个圆心之间的最小距离。避免检测到多个重叠的圆。
        param1=100,  # Canny边缘检测的高阈值。
        param2=30,  # 累加器阈值。越小检测到的圆越多，但可能包含假圆。
        minRadius=50,  # 最小圆半径
        maxRadius=200  # 最大圆半径
    )

    circle_center = None
    if circles is not None:
        circles = np.uint16(np.around(circles))
        # 找到最大的圆（假设是夹持的圆），并确保圆心在图像下半部分（与V形块区域一致）
        largest_circle = None
        max_radius = 0
        img_height = img.shape[0]
        for i in circles[0, :]:
            center_x, center_y, radius = i[0], i[1], i[2]
            # 仅考虑圆心在图像下半部分的圆
            if center_y > img_height * 0.3 and radius > max_radius:  # 调整 0.3 为更合适的比例
                max_radius = radius
                largest_circle = i

        if largest_circle is not None:
            circle_center = (largest_circle[0], largest_circle[1])
            radius = largest_circle[2]
            # 绘制圆和圆心
            cv2.circle(img, circle_center, radius, (0, 0, 255), 3)  # 红色圆
            cv2.circle(img, circle_center, 3, (255, 0, 0), -1)  # 蓝色圆心

    # --- 3. 计算圆心高度 ---
    height = None
    if v_bottom_point and circle_center:
        # 高度为V形块底部Y坐标减去圆心Y坐标
        # 假设图像y轴正方向向下，所以y坐标越大越低
        height = v_bottom_point[1] - circle_center[1]
        cv2.line(img, (circle_center[0], circle_center[1]),
                 (circle_center[0], v_bottom_point[1]), (255, 255, 0), 2)  # 黄色垂直线
        cv2.putText(img, f"Height: {height:.2f} px", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)  # 青色文字

    return height, img