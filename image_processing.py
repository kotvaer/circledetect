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
    # 这一步是为了确保图像处理的输入尺寸相对一致，减少参数调整的复杂性
    max_process_dim = 800
    h, w = img.shape[:2]
    if max(h, w) > max_process_dim:
        scale = max_process_dim / max(h, w)
        img = cv2.resize(img, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # 使用中值滤波降噪，比高斯模糊更能保持边缘锐利度
    blurred = cv2.medianBlur(gray, 5)  # 奇数内核大小，例如 3, 5, 7
    edges = cv2.Canny(blurred, 50, 150)  # Canny 边缘检测

    # --- 1. 检测 V 形块的底部顶点 ---
    # 霍夫直线变换参数：
    # threshold：累加器阈值，低于此值的直线会被忽略
    # minLineLength：最小线段长度
    # maxLineGap：最大允许点之间连接的距离（一条线段上的点）
    lines = cv2.HoughLinesP(edges, 1, np.pi / 180, threshold=80, minLineLength=100,
                            maxLineGap=10)  # 调高 threshold 和 minLineLength
    v_lines = []
    if lines is not None:
        for line in lines:
            x1, y1, x2, y2 = line[0]
            # 计算线的角度 (弧度)
            angle_rad = np.arctan2(y2 - y1, x2 - x1)
            angle_deg = np.degrees(angle_rad)

            # 筛选 V 形块的两条边
            # 假设 V 形块的两条边是倾斜的，且斜率方向相反
            # 根据您提供的CAD图，V形块的直线大致在 +/- 45度到 +/- 70度之间
            # (斜率绝对值较大，接近垂直)
            # 我们寻找两条倾斜方向相反的线
            # 线的角度通常在 -90 到 90 度之间 (atan2 结果)
            # 我们可以将所有线规范到 0-180 度进行比较
            # 或者直接根据斜率的正负来判断倾斜方向

            # 筛选出近似垂直且有一定倾斜角度的线
            # 比如，我们寻找角度在 30-70 度 和 110-150 度（或 -70到-30度）的线
            # 这里我根据您的CAD图做了调整，更偏向垂直
            abs_angle_deg = abs(angle_deg)
            if (abs_angle_deg > 30 and abs_angle_deg < 85) or \
                    (abs_angle_deg > 95 and abs_angle_deg < 150):  # 调整角度范围
                v_lines.append(line[0])
                # cv2.line(img, (x1, y1), (x2, y2), (255, 0, 255), 2) # 调试用：绘制筛选后的直线

    v_bottom_point = None
    if len(v_lines) >= 2:
        potential_intersections = []
        for i in range(len(v_lines)):
            for j in range(i + 1, len(v_lines)):
                line1 = v_lines[i]
                line2 = v_lines[j]

                x1, y1, x2, y2 = line1
                x3, y3, x4, y4 = line2

                # 计算斜率和截距
                # Line 1: y = m1*x + c1
                # Line 2: y = m2*x + c2
                # x_intersect = (c2 - c1) / (m1 - m2)
                # y_intersect = m1 * x_intersect + c1

                # 避免垂直线导致的除零错误
                denom1 = (x2 - x1)
                denom2 = (x4 - x3)

                # 对于垂直线特殊处理
                if denom1 == 0 and denom2 == 0:  # 两条线都垂直，平行或重合
                    continue
                elif denom1 == 0:  # line1 is vertical
                    x_intersect = x1
                    m2 = (y4 - y3) / denom2 if denom2 != 0 else float('inf')  # 确保m2不是垂直线的斜率
                    if m2 == float('inf'): continue  # 如果line2也垂直，则忽略
                    y_intersect = m2 * (x1 - x3) + y3
                elif denom2 == 0:  # line2 is vertical
                    x_intersect = x3
                    m1 = (y2 - y1) / denom1 if denom1 != 0 else float('inf')  # 确保m1不是垂直线的斜率
                    if m1 == float('inf'): continue  # 如果line1也垂直，则忽略
                    y_intersect = m1 * (x3 - x1) + y1
                else:
                    m1 = (y2 - y1) / denom1
                    c1 = y1 - m1 * x1
                    m2 = (y4 - y3) / denom2
                    c2 = y3 - m2 * x3

                    if abs(m1 - m2) < 0.1:  # 如果斜率非常接近，视为平行，跳过
                        continue

                    x_intersect = (c2 - c1) / (m1 - m2)
                    y_intersect = m1 * x_intersect + c1

                # 检查交点是否在图像范围内，并且Y坐标在图像底部区域（确保是V形块的底部）
                # 假设V形块的底部在图像的下半部分
                if 0 <= x_intersect < img.shape[1] and 0 <= y_intersect < img.shape[0]:
                    if y_intersect > img.shape[0] * 0.4:  # 调整此阈值，例如 0.4 表示图像下部 60% 区域
                        potential_intersections.append((int(x_intersect), int(y_intersect)))

        # 找到y坐标最低的交点作为V形块的底部顶点 (假设V形开口向上)
        if potential_intersections:
            v_bottom_point = min(potential_intersections, key=lambda p: p[1])
            cv2.circle(img, v_bottom_point, 7, (0, 255, 0), -1)  # 绿色圆点标记V形块底部，增大半径使其更明显

    # --- 2. 检测圆 ---
    # 霍夫圆变换参数：
    # dp：累加器分辨率的反比，越小越精确，但计算量大。1表示与图像分辨率相同。
    # minDist：检测到的圆心之间的最小距离。
    # param1：Canny边缘检测的高阈值。
    # param2：累加器阈值。投票数低于此值的圆会被丢弃。
    # minRadius/maxRadius：圆的最小/最大半径。

    # 对于您的CAD图，圆边缘非常清晰，可以尝试更低的 dp 和更高的 param2
    # 调整 minRadius 和 maxRadius 以精确匹配图片中的圆大小
    circles = cv2.HoughCircles(
        blurred,
        cv2.HOUGH_GRADIENT,
        dp=1.0,  # 尝试更精确的 dp，例如 1.0
        minDist=150,  # 增大最小距离，防止检测到同心圆或伪影
        param1=100,  # Canny边缘检测的高阈值
        param2=25,  # 累加器阈值，适当降低可检测到更多圆，但仍需控制假阳性
        minRadius=80,  # 根据您的图片调整，例如，圆的半径可能在 80-150 像素之间
        maxRadius=150  # 假设圆半径范围，精确设定可提高准确性
    )

    circle_center = None
    if circles is not None:
        circles = np.uint16(np.around(circles))

        # 找到最可能的目标圆
        # 我们可以根据圆的大小和位置来筛选
        largest_circle = None
        max_radius = 0
        img_height = img.shape[0]

        for i in circles[0, :]:
            center_x, center_y, radius = i[0], i[1], i[2]

            # 筛选条件：
            # 1. 确保圆心在图片中央偏下区域，通常夹持的圆会出现在这里
            # 2. 找到最大的圆（假设目标圆是最大的）
            # 3. 排除那些明显过小的或过大的圆（尽管minRadius/maxRadius已部分过滤）

            # 假设圆心在图像中下部 1/3 到 2/3 的高度区域
            if (img_height * 0.3 < center_y < img_height * 0.7) and (radius > max_radius):
                max_radius = radius
                largest_circle = i

        if largest_circle is not None:
            circle_center = (largest_circle[0], largest_circle[1])
            radius = largest_circle[2]
            # 绘制圆和圆心
            cv2.circle(img, circle_center, radius, (0, 0, 255), 3)  # 红色圆
            cv2.circle(img, circle_center, 5, (255, 0, 0), -1)  # 蓝色圆心，增大半径使其更明显

    # --- 3. 计算圆心高度 ---
    height = None
    if v_bottom_point and circle_center:
        # 高度为V形块底部Y坐标减去圆心Y坐标
        # 假设图像y轴正方向向下，所以y坐标越大越低
        height = v_bottom_point[1] - circle_center[1]
        cv2.line(img, (circle_center[0], circle_center[1]),
                 (circle_center[0], v_bottom_point[1]), (255, 255, 0), 2)  # 黄色垂直线

        # 在图片上标注高度
        # 文本位置调整到圆心上方或 V 形块顶点附近，避免遮挡
        text_x = circle_center[0] - 50  # 文本 X 坐标
        text_y = int(v_bottom_point[1] - height / 2) - 10  # 文本 Y 坐标，在中间偏上

        # 确保文本不会超出图片边界
        if text_y < 20: text_y = 20
        if text_x < 10: text_x = 10

        cv2.putText(img, f"Height: {height:.2f} px", (text_x, text_y),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2, cv2.LINE_AA)  # 青色文字，增加抗锯齿

    return height, img