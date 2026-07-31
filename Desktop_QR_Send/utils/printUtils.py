# printUtils
"""
汉印 T63R RFID 打印机闭环控制与条形码/标签打印工具库
"""

import os
import sys
import logging
from typing import Optional

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

try:
    from rfid_printer import RfidPrintService, LabelPrintData, PrintResult
    RFID_SERVICE_AVAILABLE = True
except Exception as e:
    logging.warning(f"导入 rfid_printer 模块失败: {e}")
    RFID_SERVICE_AVAILABLE = False

_global_rfid_service: Optional['RfidPrintService'] = None


def get_rfid_service(config_path: str = "config/settings.json") -> Optional['RfidPrintService']:
    """获取全局 RFID 打印服务单例"""
    global _global_rfid_service
    if not RFID_SERVICE_AVAILABLE:
        return None
    if _global_rfid_service is None:
        try:
            abs_cfg = os.path.abspath(os.path.join(PROJECT_ROOT, config_path))
            _global_rfid_service = RfidPrintService(config_path=abs_cfg)
            logging.info("全局 T63R RFID 打印服务单例初始化成功")
        except Exception as e:
            logging.error(f"初始化 RFID 打印服务单例失败: {e}")
    return _global_rfid_service


def print_rfid_box_label(
    case_code: str,
    label_data: Optional['LabelPrintData'] = None,
    allow_reprint: bool = True  # 当前调试阶段关闭防二次写入锁，允许同一箱码重复测试
) -> 'PrintResult':
    """
    核心 RFID 箱标签打印、写卡与 TID 闭环核验入口：
    1. 自动连接 64 位 T63R USB 打印机。
    2. 在 100x80mm 300DPI 画布上绘制“高原安”全字段生产箱标签及 Code 128 条码。
    3. 标签条码使用相机真实识别箱码；RFID EPC 单独写入13位毫秒时间戳。
    4. 当前设 allow_reprint=True，关闭二次写入保护，便于确认后重复测试。
    """
    service = get_rfid_service()
    if service is None:
        res = PrintResult(box_code=case_code)
        res.success = False
        res.error_code = -99
        res.error_message = "RFID 打印服务未初始化或环境不兼容"
        return res

    return service.print_write_verify(case_code, label_data=label_data, allow_reprint_same_code=allow_reprint)


def print_barcode(case_code, printer_name=None, page_width=500, page_height=400, page_num=1, scale_factor=1.0, left_margin=0, top_margin=0):
    """
    兼容原有系统调用的打印函数接口。
    驱动 T63R RFID 打印机执行单张打印，并为RFID生成独立13位时间戳。
    """
    logging.info(f"开始执行 T63R RFID 箱码打印: {case_code}, 原设打印机: {printer_name}, 尺寸: {page_width}x{page_height}")

    result = print_rfid_box_label(case_code, allow_reprint=True)

    if result.success:
        logging.info(f"箱码 '{case_code}' 打印写卡核验成功 (PASS)，TID: {result.read_tid}, EPC: {result.read_epc}")
    else:
        logging.warning(f"箱码 '{case_code}' 打印写卡未通过/被拦截: {result.error_message}")

    return result
