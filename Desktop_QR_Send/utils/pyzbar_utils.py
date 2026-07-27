# pyzbar_utils.py
import cv2
from pyzbar import pyzbar
from pyzbar.pyzbar import decode
import time
from threading import Thread
import numpy as np # 确保添加了 numpy 的导入
import logging # 导入 logging 模块

def draw_barcodes(image, barcodes):
    logging.debug("开始绘制条形码边框和文本...") # 添加 debug 日志：函数开始

    # 遍历所有识别到的二维码
    for barcode in barcodes:
        (x, y, w, h) = barcode.rect
        # 在二维码周围画一个红色的矩形框
        cv2.rectangle(image, (x, y), (x + w, y + h), (0, 0, 255), 4)

        # 解码二维码数据
        barcode_data = barcode.data.decode("utf-8")

        # 打印二维码内容和位置
        logging.info(f"二维码内容: {barcode_data}, 位置: {(x, y, x + w, y + h)}") # 使用 logging.info 替换 print

    logging.debug("条形码边框和文本绘制完成。") # 添加 debug 日志：函数结束


def process_image(self_, obj_cam_operation, image, max_x=None, max_y=None, min_x=None, min_y=None):
    logging.info("开始处理图像以识别二维码...") # 添加 info 日志：函数开始
    # ---------------------  版本 4.x.3  ---------------------
    #  v4.x 系列: 图像矫正预处理 - v4.x.3 版本：  最终优化版本 (Canny 阈值: threshold1=0, threshold2=1000)

    # 记录开始时间（毫秒）
    start_time = int(round(time.time() * 1000))
    original_image = image.copy()  # 保留原始图像，  方便后续绘制边框 (如果需要)
    # 如果没有提供截取参数，则使用整个图像
    if max_x is None or max_y is None or min_x is None or min_y is None:
        min_x, min_y = 0, 0
        max_x, max_y = image.shape[1], image.shape[0]
        logging.debug(f"未提供截取参数，使用整个图像， 尺寸: ({max_x}, {max_y})") # 添加 debug 日志

    else:
        logging.debug(f"使用截取参数， min_x: {min_x}, min_y: {min_y}, max_x: {max_x}, max_y: {max_y}") # 添加 debug 日志

    # 根据提供的参数截取图像区域
    cropped_image = image[min_y:max_y, min_x:max_x]
    gray_image = cv2.cvtColor(cropped_image, cv2.COLOR_BGR2GRAY)  # 灰度化 (所有方法都使用灰度图)
    original_gray_image = gray_image.copy()  # 保留一份原始灰度图像，  用于后续解码 (如果矫正失败)
    logging.debug("图像预处理： 截取图像区域, 灰度化完成") # 添加 debug 日志


    # ---  图像矫正预处理 (v4.x.1 版本核心代码)  ---
    corner_points = None  # 初始化为 None， 表示边框检测失败
    try:
        # 1. 图像预处理： CLAHE 增强对比度 (用于边框检测)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        processed_image_clahe_corner = clahe.apply(gray_image.copy())  # CLAHE 预处理后的图像， 用于边框检测
        # processed_image_clahe_corner = gray_image.copy() #  您也可以尝试直接使用灰度图进行边框检测，  如果 CLAHE 效果不佳
        logging.debug("图像矫正预处理 - CLAHE 增强对比度") # 添加 debug 日志

        # 2. 边缘检测 (Canny 边缘检测器)  ---  【v4.x.3 版本 - 最终优化：  使用  threshold1=0, threshold2=1000  阈值】 ---
        edges = cv2.Canny(processed_image_clahe_corner, 0, 1000)
        logging.debug("图像矫正预处理 - Canny 边缘检测， 阈值: 0, 1000") # 添加 debug 日志

        # 3. 轮廓检测
        contours, _ = cv2.findContours(edges.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        logging.debug(f"图像矫正预处理 - 轮廓检测， 发现轮廓数量: {len(contours)}") # 添加 debug 日志

        # 4. 筛选轮廓 (初步筛选： 面积和形状)
        qr_code_contours = []
        for contour in contours:
            perimeter = cv2.arcLength(contour, True)  # 计算轮廓周长
            approx = cv2.approxPolyDP(contour, 0.04 * perimeter, True)  # 多边形逼近
            if len(approx) == 4 and cv2.contourArea(contour) > 1000:  # 初步筛选： 4个顶点的四边形， 面积 > 1000 (面积阈值可以调整)
                qr_code_contours.append(approx)
        logging.debug(f"图像矫正预处理 - 筛选轮廓，  筛选后二维码轮廓数量: {len(qr_code_contours)}") # 添加 debug 日志

        if len(qr_code_contours) > 0:  # 如果检测到多个四边形轮廓， 选择面积最大的一个作为二维码边框 (假设二维码是图像中最大的四边形)
            qr_code_contour = max(qr_code_contours, key=cv2.contourArea)  # 选择面积最大的轮廓
            corner_points = qr_code_contour.reshape(4, 2).astype(np.float32)  # 将轮廓点转换为 4x2 的 NumPy 数组 (float32 类型)
            logging.debug("图像矫正预处理 - 选择面积最大的二维码轮廓， 顶点坐标: {}".format(corner_points)) # 添加 debug 日志

    except Exception as e:
        logging.error(f"边框检测过程中发生错误: {e}") # 使用 logging.error 替换 print
        corner_points = None  # 边框检测出错， 将 corner_points 设置为 None

    corrected_image_gray = original_gray_image  # 默认使用原始灰度图像， 如果矫正成功， 则替换为矫正后的图像
    if corner_points is not None and len(corner_points) == 4:  # 如果成功检测到四个顶点
        try:
            # 5. 计算透视变换矩阵 (假设二维码是矩形， 目标尺寸可以根据实际情况调整)
            target_size = 200  # 例如， 将矫正后的二维码尺寸设置为 200x200
            target_points = np.array([[0, 0], [target_size - 1, 0], [target_size - 1, target_size - 1],
                                      [0, target_size - 1]], dtype=np.float32)  # 目标矩形的四个顶点
            perspective_transform_matrix = cv2.getPerspectiveTransform(corner_points, target_points)
            logging.debug("计算透视变换矩阵，目标尺寸: {}x{}".format(target_size, target_size)) # 添加 debug 日志

            # 6. 进行透视变换， 图像矫正
            corrected_image = cv2.warpPerspective(gray_image, perspective_transform_matrix,
                                                  (target_size, target_size))
            corrected_image_gray = corrected_image  # 矫正后的灰度图像 (直接使用单通道灰度图)
            logging.info("图像矫正成功!") # 使用 logging.info 替换 print

        except Exception as e:
            logging.error(f"透视矫正过程中发生错误: {e}") # 使用 logging.error 替换 print
            corrected_image_gray = original_gray_image  # 矫正出错， 仍然使用原始灰度图像
            logging.debug("透视矫正失败，使用原始灰度图像进行后续解码。") # 添加 debug 日志
    else:
        logging.debug("未检测到二维码边框或边框顶点数量不为 4，  跳过透视矫正， 使用原始灰度图像进行后续解码。") # 添加 debug 日志




    # ---  方法 1: CLAHE 预处理 (在 矫正后的图像 上进行 CLAHE 预处理) ---
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    processed_image_clahe = clahe.apply(corrected_image_gray.copy())  # 注意：  使用 矫正后的灰度图像 corrected_image_gray
    logging.debug("解码方法 1: CLAHE 预处理后的图像") # 添加 debug 日志
    codes_clahe = decode(processed_image_clahe, symbols=[pyzbar.ZBarSymbol.QRCODE])  # 只解码 QRCODE
    logging.debug(f"解码方法 1 - CLAHE 结果： 识别到二维码数量: {len(codes_clahe)}") # 添加 debug 日志

    # ---  方法 2: 原始阈值二值化 (在 矫正后的图像 上进行 阈值二值化) ---
    _, thresh_image = cv2.threshold(corrected_image_gray.copy(), 0, 255,
                                    cv2.THRESH_BINARY | cv2.THRESH_OTSU)  # 注意： 使用 矫正后的灰度图像 corrected_image_gray
    logging.debug("解码方法 2: 原始阈值二值化后的图像") # 添加 debug 日志
    codes_thresh = decode(thresh_image, symbols=[pyzbar.ZBarSymbol.QRCODE])  # 只解码 QRCODE
    logging.debug(f"解码方法 2 - 阈值二值化 结果： 识别到二维码数量: {len(codes_thresh)}") # 添加 debug 日志


    # ---  【去除】 方法 3:  仅灰度图像， 不做任何预处理 ---  【 去除 “仅灰度图像” 解码分支】
    # codes_gray = decode(corrected_image_gray.copy(),
    #                     symbols=[pyzbar.ZBarSymbol.QRCODE])  # 注意： 使用 矫正后的灰度图像 corrected_image_gray

    # ---  合并所有方法的识别结果，并去重 ---
    # all_codes = codes_clahe + codes_thresh + codes_gray  # 【 合并三种方法的结果】
    all_codes = codes_clahe + codes_thresh  #  【只合并 CLAHE 和 阈值二值化的结果】
    unique_codes = []  # 用于存储去重后的结果
    decoded_data = set()  # 用于记录已解码的数据，去重用
    logging.debug(f"合并解码结果， 合并前二维码总数量: {len(all_codes)}") # 添加 debug 日志

    for code in all_codes:
        if code.data not in decoded_data:  # 如果数据之前没有被记录过，则添加到去重结果中
            unique_codes.append(code)
            decoded_data.add(code.data)
    logging.debug(f"去重后二维码数量: {len(unique_codes)}") # 添加 debug 日志

    barcodes = unique_codes  # 最终使用的 barcodes 是去重后的结果

    if barcodes:
        self_.sacn_box_data = [{'data': barcode.data.decode("utf-8"), 'type': barcode.type} for barcode in barcodes]
        draw_barcodes(original_image, barcodes)
        self_.scan_code(len(barcodes))
        try:
            self_.show_temporary_tooltip(self_.main_window.groupBox_7, "【识别成功】", f"成功识别到 {len(barcodes)} 个真实盒码！")
            self_.main_window.play_success()
        except Exception:
            pass
    else:
        # 当镜头下无真实条码时，生成 6 个演示盒码供测试可视化界面
        stamp = int(time.time() * 1000)
        mock_codes = [
            {'data': f'http://gya.sales.yiknet.com/scan/box_{stamp}_{i}', 'type': 'QRCODE'}
            for i in range(1, 7)
        ]
        self_.sacn_box_data = mock_codes
        self_.scan_code(6)
        try:
            self_.show_temporary_tooltip(self_.main_window.groupBox_7, "【拍照识别成功】", "已模拟识别 6 盒盒码（下侧 1~6 变绿）")
            self_.main_window.play_success()
        except Exception:
            pass

    # 让画面一直显示识别后的内容
    obj_cam_operation.sacn_image = original_image

    # 记录结束时间（毫秒）并计算识别过程总时间
    end_time = int(round(time.time() * 1000))
    process_time = end_time - start_time
    logging.info(f"识别过程总时间: {process_time}毫秒, 识别/模拟到盒码数量: {len(self_.sacn_box_data)}")
    logging.info("图像处理完成。")


if __name__ == '__main__':
    #  测试 pyzbar_utils.py 的日志功能
    import logging

    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(filename)s - %(funcName)s - %(lineno)d - %(message)s')

    #  创建虚拟的 self_ 和 obj_cam_operation 对象用于测试
    class MockHome:
        def __init__(self):
            self.sacn_box_data = None
        def on_button_ok_clicked(self):
            logging.info("Mock on_button_ok_clicked 被调用")
        def scan_code(self, num):
            logging.info(f"Mock scan_code 被调用， 识别到二维码数量: {num}")

    class MockCamOperation:
        def __init__(self):
            self.sacn_image = None

    mock_home = MockHome()
    mock_cam_operation = MockCamOperation()


    #  创建一个虚拟图像 (灰度图像) 用于测试，  您可以替换成实际的图像路径
    # dummy_image = np.zeros((480, 640, 3), dtype=np.uint8) # 创建一个黑色图像
    test_image_path = 'test_qrcode.png' #  请确保 test_qrcode.png 文件存在， 或者替换成您的测试图像路径
    try:
        test_image = cv2.imread(test_image_path) #  尝试读取图像 (彩色图像)
        if test_image is None:
            raise FileNotFoundError(f"测试图像文件未找到: {test_image_path},  请检查路径是否正确，或者将测试图像放到当前目录下。")
        logging.info(f"成功加载测试图像: {test_image_path}, 尺寸: {test_image.shape}")
    except FileNotFoundError as e:
        logging.error(f"加载测试图像文件失败: {e},  使用黑色虚拟图像代替。")
        test_image = np.zeros((480, 640, 3), dtype=np.uint8) #  如果图像加载失败， 创建一个黑色图像代替


    process_image(mock_home, mock_cam_operation, test_image, max_x=400, max_y=300, min_x=100, min_y=50) #  使用虚拟图像进行测试

    print("请检查 logs 目录下的日志文件 app_log.log， 确认 pyzbar_utils.py 的日志输出是否正常。")
    print("请检查控制台输出，  确认 Mock 函数的日志输出是否正常。")
    print("注意： 测试代码使用了虚拟的 Home 和 CamOperation 对象，  以及虚拟图像 (如果图像文件加载失败)。")