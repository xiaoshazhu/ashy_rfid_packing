# pyzbar_utils.py
import cv2
from pyzbar import pyzbar
from pyzbar.pyzbar import decode
import time
from threading import Thread
import numpy as np # 确保添加了 numpy 的导入
import logging # 导入 logging 模块
from collections import namedtuple


CodeRect = namedtuple("CodeRect", "left top width height")


class OpenCvDecodedCode:
    """OpenCV 真实解码结果，保持与 pyzbar 结果相同的业务接口。"""

    def __init__(self, data, rect):
        self.data = data
        self.type = "QRCODE"
        self.rect = rect


def decode_opencv_qr(image):
    """使用 OpenCV 的多二维码解码器作为 pyzbar 的真实识别补充。

    只返回已经真正解出非空内容的二维码；不根据轮廓猜测数量，
    不会为未解码的图形补框或生成数据。
    """
    if image is None or getattr(image, "size", 0) == 0:
        return []

    detector = cv2.QRCodeDetector()
    if not hasattr(detector, "detectAndDecodeMulti"):
        return []
    try:
        ok, decoded_info, points, _ = detector.detectAndDecodeMulti(image)
    except (cv2.error, ValueError):
        return []

    if not ok or points is None:
        return []

    results = []
    values = decoded_info if decoded_info is not None else ()
    for value, polygon in zip(values, points):
        value = str(value or "").strip()
        if not value:
            continue
        polygon = np.asarray(polygon, dtype=np.float32).reshape(-1, 2)
        x, y, width, height = cv2.boundingRect(polygon)
        if width <= 0 or height <= 0:
            continue
        results.append(
            OpenCvDecodedCode(
                value.encode("utf-8"),
                CodeRect(int(x), int(y), int(width), int(height)),
            )
        )
    return results

SCAN_SYMBOLS = [
    symbol for symbol in (
        getattr(pyzbar.ZBarSymbol, "QRCODE", None),
        getattr(pyzbar.ZBarSymbol, "CODE128", None),
        getattr(pyzbar.ZBarSymbol, "EAN13", None),
    )
    if symbol is not None
]

def draw_barcodes(image, barcodes, offset_x=0, offset_y=0):
    logging.debug("开始绘制条形码边框和文本...") # 添加 debug 日志：函数开始

    # 遍历所有识别到的二维码
    for barcode in barcodes:
        (x, y, w, h) = barcode.rect
        x += int(offset_x)
        y += int(offset_y)
        # 在二维码周围画一个红色的矩形框
        cv2.rectangle(image, (x, y), (x + w, y + h), (0, 0, 255), 4)

        # 解码二维码数据
        barcode_data = barcode.data.decode("utf-8")

        # 打印二维码内容和位置
        logging.info(f"二维码内容: {barcode_data}, 位置: {(x, y, x + w, y + h)}") # 使用 logging.info 替换 print

    logging.debug("条形码边框和文本绘制完成。") # 添加 debug 日志：函数结束


def decode_image_codes(image):
    """对一帧真实相机图像进行无副作用识别，供灯光校准采样。

    不修改页面状态、不填充模拟数据，也不触发数据库录入。返回值按码内容去重。
    """
    if image is None or getattr(image, "size", 0) == 0:
        return []
    if len(image.shape) == 2:
        gray = image.copy()
    else:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)
    _, thresholded = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)

    unique = []
    seen = set()
    for candidate in (gray, enhanced, thresholded):
        for code in decode(candidate, symbols=SCAN_SYMBOLS):
            if code.data in seen:
                continue
            seen.add(code.data)
            unique.append(code)
    for code in decode_opencv_qr(gray):
        if code.data in seen:
            continue
        seen.add(code.data)
        unique.append(code)
    # 与正式装箱识别保持同一业务口径：画面里存在二维码时，商品EAN条码
    # 不计入识别数量，防止灯光校准被非盒码条码误导。
    qr_codes = [code for code in unique if str(code.type).upper() == "QRCODE"]
    return qr_codes if qr_codes else unique


def process_image(
    self_, obj_cam_operation, image,
    max_x=None, max_y=None, min_x=None, min_y=None,
    show_feedback=True,
):
    logging.info("开始处理图像以识别二维码...") # 添加 info 日志：函数开始
    # ---------------------  版本 4.x.3  ---------------------
    #  v4.x 系列: 图像矫正预处理 - v4.x.3 版本：  最终优化版本 (Canny 阈值: threshold1=0, threshold2=1000)

    # 记录开始时间（毫秒）
    start_time = int(round(time.time() * 1000))
    # 识别只读取本次真实相机帧，不把处理图像写回相机预览。
    # 实时画面始终由海康SDK连续刷新，避免红框静态帧长期覆盖造成卡顿/白屏。
    obj_cam_operation.sacn_image = None
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
        processed_image_clahe_corner = gray_image
        # processed_image_clahe_corner = gray_image.copy() #  您也可以尝试直接使用灰度图进行边框检测，  如果 CLAHE 效果不佳
        logging.debug("图像矫正预处理 - CLAHE 增强对比度") # 添加 debug 日志

        # 多盒同屏不适合“找最大四边形并透视成单码”的旧算法。
        # 停止Canny/轮廓透视分支，既保持原始坐标，也减少每次识别的无效耗时。
        contours = []

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




    # 多盒同屏时，旧逻辑会把面积最大的一个四边形拉伸到200x200，
    # 但随后又把变形后的rect当成原图坐标绘制，导致现场红框严重偏移。
    # 正式识别必须保留相机原始ROI坐标；透视尝试不再参与多码解码。
    corrected_image_gray = original_gray_image

    # ---  方法 1: CLAHE 预处理（尺寸和坐标与原始ROI一致） ---
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    processed_image_clahe = clahe.apply(corrected_image_gray.copy())  # 注意：  使用 矫正后的灰度图像 corrected_image_gray
    logging.debug("解码方法 1: CLAHE 预处理后的图像") # 添加 debug 日志
    codes_clahe = decode(processed_image_clahe, symbols=SCAN_SYMBOLS)
    logging.debug(f"解码方法 1 - CLAHE 结果： 识别到二维码数量: {len(codes_clahe)}") # 添加 debug 日志

    # ---  方法 2: 原始阈值二值化 (在 矫正后的图像 上进行 阈值二值化) ---
    _, thresh_image = cv2.threshold(corrected_image_gray.copy(), 0, 255,
                                    cv2.THRESH_BINARY | cv2.THRESH_OTSU)  # 注意： 使用 矫正后的灰度图像 corrected_image_gray
    logging.debug("解码方法 2: 原始阈值二值化后的图像") # 添加 debug 日志
    codes_thresh = decode(thresh_image, symbols=SCAN_SYMBOLS)
    logging.debug(f"解码方法 2 - 阈值二值化 结果： 识别到二维码数量: {len(codes_thresh)}") # 添加 debug 日志


    # ---  方法 3: 原始灰度图 ---
    # 部分低对比度码经CLAHE或二值化后会丢失，保留原始灰度解码以减少漏标。
    codes_gray = decode(corrected_image_gray.copy(), symbols=SCAN_SYMBOLS)

    # ---  合并所有方法的识别结果，并去重 ---
    # 三种图像尺寸完全一致，返回的rect均可直接映射回相机原图。
    # OpenCV 与 pyzbar 是两个独立的真实解码器；前者常能补出一部分
    # pyzbar 因反光、对比度低而漏掉的码。两者坐标都基于同一原始 ROI。
    codes_opencv = decode_opencv_qr(corrected_image_gray)
    all_codes = codes_gray + codes_clahe + codes_thresh + codes_opencv
    unique_codes = []  # 用于存储去重后的结果
    decoded_data = set()  # 用于记录已解码的数据，去重用
    logging.debug(f"合并解码结果， 合并前二维码总数量: {len(all_codes)}") # 添加 debug 日志

    for code in all_codes:
        if code.data not in decoded_data:  # 如果数据之前没有被记录过，则添加到去重结果中
            unique_codes.append(code)
            decoded_data.add(code.data)
    logging.debug(f"去重后二维码数量: {len(unique_codes)}") # 添加 debug 日志

    # 同一盒包装上通常同时存在业务二维码和商品EAN条码。现场10盒测试中，
    # 10个业务二维码加1个重复商品条码会被误显示成11/10。只要画面内存在
    # QRCODE，就仅把QRCODE作为盒码；没有二维码时才兼容CODE128/EAN13。
    qr_codes = [code for code in unique_codes if str(code.type).upper() == "QRCODE"]
    barcodes = qr_codes if qr_codes else unique_codes
    if qr_codes and len(qr_codes) != len(unique_codes):
        ignored_types = sorted({
            str(code.type) for code in unique_codes if str(code.type).upper() != "QRCODE"
        })
        logging.info(
            f"检测到业务二维码，本帧忽略非盒码类型 {ignored_types}，"
            f"候选总数={len(unique_codes)}，有效盒码={len(qr_codes)}"
        )

    # 按画面从上到下、从左到右排序，保证显示与截断顺序稳定。
    barcodes = sorted(barcodes, key=lambda code: (code.rect.top, code.rect.left))
    try:
        from page.config import CONFIG_DATA
        expected_count = max(1, int(CONFIG_DATA.get("edit_max_jian", 10)))
    except Exception:
        expected_count = 10
    if len(barcodes) > expected_count:
        logging.warning(
            f"本帧识别到 {len(barcodes)} 个有效候选盒码，超过配置上限 {expected_count}；"
            "页面和装箱逻辑只保留排序后的前N个，禁止出现11/10"
        )
        barcodes = barcodes[:expected_count]

    if barcodes:
        self_.sacn_box_data = [{'data': barcode.data.decode("utf-8"), 'type': barcode.type} for barcode in barcodes]
        boxes = [
            (
                int(barcode.rect.left) + int(min_x),
                int(barcode.rect.top) + int(min_y),
                int(barcode.rect.width),
                int(barcode.rect.height),
            )
            for barcode in barcodes
        ]
        self_.show_recognition_boxes(
            boxes,
            image.shape[1],
            image.shape[0],
            source_image=image,
        )
        if show_feedback:
            try:
                self_.show_temporary_tooltip(
                    self_.main_window.groupBox_7,
                    "【识别成功】",
                    f"本帧真实识别到 {len(barcodes)} 个盒码。",
                )
                self_.main_window.play_success()
            except Exception:
                pass
    else:
        # 生产测试只接受相机真实识别结果，不再自动填充模拟盒码或触发录入。
        self_.sacn_box_data = None
        if show_feedback:
            try:
                self_.show_temporary_tooltip(self_.main_window.groupBox_7, "【识别失败】", "没有识别到真实盒码，请调整盒子位置后重试。")
                self_.main_window.play_warning()
            except Exception:
                pass

    # 页面计数由Home根据“本轮累计真实结果”统一更新一次；这里不再先显示
    # 本帧9个、随后又显示累计10个，避免肉眼看到9/10来回跳动。
    obj_cam_operation.sacn_image = None

    # 记录结束时间（毫秒）并计算识别过程总时间
    end_time = int(round(time.time() * 1000))
    process_time = end_time - start_time
    recognized_count = len(self_.sacn_box_data or [])
    logging.info(f"识别过程总时间: {process_time}毫秒, 真实识别盒码数量: {recognized_count}")
    logging.info("图像处理完成。")
