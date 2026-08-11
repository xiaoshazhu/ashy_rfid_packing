"""Windows 打印机驱动矢量高清打印模块。

通过 Windows 官方驱动（JiEPRT T63RZ）执行矢量高精度打纸，
解决普通 C SDK 直连模式下文本发淡、条码不清晰、边界未铺满对齐的问题。
"""

from __future__ import annotations

import os
import sys
import logging
from datetime import datetime
from typing import Any, Dict, List, Mapping, Optional

logger = logging.getLogger("WinDriverPrinter")

from PySide6.QtCore import QMarginsF, QRectF, QSizeF, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPageLayout, QPageSize, QPen, QPixmap
from PySide6.QtPrintSupport import QPrinter, QPrinterInfo

from .label_layout import render_text, resolve_asset_path

# Code 128 模式 B 编码表
CODE128_PATTERNS = [
    "212222", "222122", "222221", "121223", "121322", "131222", "122213", "122312", "132212", "221213",
    "221312", "231212", "112232", "122132", "122231", "113222", "123122", "123221", "223211", "221132",
    "221231", "213212", "223112", "312131", "311222", "321122", "321221", "312212", "322112", "322211",
    "212123", "212321", "232121", "111323", "131123", "131321", "112313", "132113", "132311", "211313",
    "231113", "231311", "112133", "112331", "132131", "113123", "113321", "133121", "313121", "211331",
    "231131", "213113", "213311", "213131", "311123", "311321", "331121", "312113", "312311", "332111",
    "314111", "221411", "431111", "111224", "111422", "121124", "121421", "141122", "141221", "112214",
    "112412", "122114", "122411", "142112", "142211", "241211", "221114", "413111", "241112", "134111",
    "111242", "121142", "121241", "114212", "124112", "124211", "411212", "421112", "421211", "212141",
    "214121", "412121", "111143", "111341", "131141", "114113", "114311", "411113", "411311", "113141",
    "114131", "311141", "411131", "211412", "211214", "211232", "2331112"
]


def encode_code128_b_pattern(data: str) -> str:
    """生成 Code 128 模式 B 的黑白模块宽度序列。"""
    if not data:
        data = "0000000000000"
    vals = [104]
    for ch in str(data):
        val = ord(ch) - 32
        if 0 <= val <= 95:
            vals.append(val)
        else:
            vals.append(0)
    checksum = (vals[0] + sum(i * v for i, v in enumerate(vals[1:], 1))) % 103
    vals.append(checksum)
    vals.append(106)
    return "".join(CODE128_PATTERNS[v] for v in vals)


VIRTUAL_PRINTER_KEYWORDS = ("pdf", "xps", "onenote", "fax", "document writer", "file", "prompt", "microsoft print", "virtual")
PHYSICAL_KEYWORDS = (
    "t63", "jieprt", "postek", "热敏", "hprt", "n31", "label", "printer",
    "pos", "zebra", "tsc", "godex", "gprinter", "xprinter", "芯烨", "佳博",
    "博思得", "汉印", "得力", "条码", "标签", "usb", "receipt", "serial"
)


def is_virtual_printer(name: str) -> bool:
    if not name:
        return True
    n_low = str(name).lower()
    return any(kw in n_low for kw in VIRTUAL_PRINTER_KEYWORDS)


def _clean_str(s: str) -> str:
    if not s:
        return ""
    return str(s).lower().replace(" ", "").replace("_", "").replace("-", "").replace("(", "").replace(")", "")


def get_target_windows_printer(printer_name: Optional[str] = None) -> Optional[QPrinterInfo]:
    """多级智能检索本地实体硬件打印机，100% 过滤虚拟 PDF 打印机，杜绝弹出保存文件窗口。"""
    printers = QPrinterInfo.availablePrinters()
    if not printers:
        return None

    # 1. 严格过滤掉所有虚拟 PDF / XPS 打印机，避免弹出文件保存窗口
    physical_printers = [p for p in printers if not is_virtual_printer(p.printerName())]

    # 2. 优先在实体硬件打印机中匹配用户选定的打印机（如 JiEPRT T63RZ、T63R RFID 打印机等）
    if printer_name and str(printer_name).strip():
        raw_target = str(printer_name).strip().lower()
        clean_target = _clean_str(raw_target)

        # 优先在硬件打印机列表中匹配
        search_list = physical_printers if physical_printers else printers
        for p in search_list:
            p_name = p.printerName().lower()
            p_clean = _clean_str(p_name)
            if raw_target == p_name or raw_target in p_name or p_name in raw_target or clean_target == p_clean or clean_target in p_clean:
                if not is_virtual_printer(p.printerName()):
                    return p

        # 分词与前缀子串模糊匹配 (如 "T63R RFID 打印机" 自动提取 "t63"、"jieprt" 命中 "JiEPRT T63RZ")
        tokens = [t for t in raw_target.replace("打印机", "").split() if len(t) >= 2]
        sub_tokens = set(tokens)
        for tok in tokens:
            if len(tok) > 3:
                sub_tokens.add(tok[:3])
                sub_tokens.add(tok.rstrip("r").rstrip("z"))

        for p in search_list:
            p_name = p.printerName().lower()
            if any(stok in p_name for stok in sub_tokens if len(stok) >= 2):
                if not is_virtual_printer(p.printerName()):
                    return p

    if not physical_printers:
        logger.warning("未检测到任何实体硬件打印机（均为虚拟PDF打印机），跳过 GDI 驱动渲染以杜绝弹窗")
        return None

    # 3. 检索常用实体硬件打印机品牌关键词 (t63, jieprt, postek, 热敏, label, printer...)
    for p in physical_printers:
        name_low = p.printerName().lower()
        if any(kw in name_low for kw in PHYSICAL_KEYWORDS):
            return p

    # 4. 检查系统默认打印机（若为实体打印机）
    default_p = QPrinterInfo.defaultPrinter()
    if default_p and not is_virtual_printer(default_p.printerName()):
        return default_p

    # 5. 返回首个实体硬件打印机
    return physical_printers[0]


def print_canvas_via_win_driver(
    elements: List[Dict[str, Any]],
    preview_data: Mapping[str, Any],
    width_mm: float = 210.0,
    height_mm: float = 100.0,
    printer_name: Optional[str] = None,
) -> bool:
    """使用 Windows 官方驱动（JiEPRT T63RZ）绘制 100% 矢量清晰度标签并出纸。"""
    target_printer = get_target_windows_printer(printer_name)
    if not target_printer:
        return False

    printer = QPrinter(target_printer, QPrinter.PrinterResolution)
    printer.setOutputFormat(QPrinter.NativeFormat)
    printer.setOutputFileName("")

    page_layout = QPageLayout(
        QPageSize(QSizeF(width_mm, height_mm), QPageSize.Millimeter),
        QPageLayout.Portrait,
        QMarginsF(0.0, 0.0, 0.0, 0.0),
        QPageLayout.Millimeter
    )
    printer.setPageLayout(page_layout)
    printer.setFullPage(True)

    painter = QPainter()
    if not painter.begin(printer):
        # 降级尝试 ScreenResolution
        printer = QPrinter(target_printer, QPrinter.ScreenResolution)
        printer.setOutputFormat(QPrinter.NativeFormat)
        printer.setOutputFileName("")
        printer.setPageLayout(page_layout)
        printer.setFullPage(True)
        if not painter.begin(printer):
            logger.warning(f"QPainter.begin(printer) 失败: {target_printer.printerName()}")
            return False

    try:
        dpi = printer.resolution()
        expected_w_px = int(width_mm * dpi / 25.4)
        expected_h_px = int(height_mm * dpi / 25.4)

        full_rect = printer.pageLayout().fullRectPixels(dpi)
        canvas_w_px = max(expected_w_px, full_rect.width())
        canvas_h_px = max(expected_h_px, full_rect.height())

        # 若系统驱动汇报的 width 比 height 小，纠正长宽映射
        if width_mm > height_mm and canvas_w_px < canvas_h_px:
            canvas_w_px, canvas_h_px = canvas_h_px, canvas_w_px

        scale_x = canvas_w_px / max(1.0, width_mm)
        scale_y = canvas_h_px / max(1.0, height_mm)

        data_map = dict(preview_data or {})
        data_map.setdefault("produce_date", datetime.now().strftime("%Y.%m.%d"))
        offset_x_mm = float(data_map.get("offset_x_mm", 0.0))
        offset_y_mm = float(data_map.get("offset_y_mm", 0.0))

        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.TextAntialiasing, True)

        for elem in elements:
            elem_type = str(elem.get("type", ""))
            if elem_type in ("box_count", "box_unit"):
                box_spec_elem = next((item for item in elements if item.get("type") == "box_spec"), {})
                if not box_spec_elem or not box_spec_elem.get("enabled", True):
                    continue
            elif elem_type != "barcode" and not elem.get("enabled", True):
                continue

            if elem.get("print_direct") is False:
                continue

            x = (float(elem.get("x", 0.0)) + offset_x_mm) * scale_x
            y = (float(elem.get("y", 0.0)) + offset_y_mm) * scale_y
            w = float(elem.get("w", 0.0)) * scale_x
            h = float(elem.get("h", 0.0)) * scale_y

            if elem_type == "divider":
                pen_w = max(1, int(float(elem.get("line_width", 1)) * scale_y / 3.0))
                painter.setPen(QPen(QColor(0, 0, 0), pen_w))
                painter.drawLine(int(x), int(y), int(x + w), int(y))
                continue

            if elem_type == "brand_logo":
                logo_path = resolve_asset_path(str(elem.get("asset_path") or elem.get("value") or ""))
                if os.path.exists(logo_path):
                    logo = QPixmap(logo_path)
                    if not logo.isNull():
                        painter.drawPixmap(QRectF(x, y, w, h), logo, QRectF(logo.rect()))
                continue

            if elem_type == "barcode":
                code = str(data_map.get("barcode") or elem.get("value") or "0123456789130").strip()
                pattern_str = encode_code128_b_pattern(code)

                text_h_px = max(14, int(5.0 * scale_y))
                bars_h_px = max(10, int(h - text_h_px))

                total_modules = len(pattern_str)
                mod_w_px = w / max(1.0, total_modules)

                painter.setPen(Qt.NoPen)
                painter.setBrush(QColor(0, 0, 0))

                curr_x = x
                for i, char in enumerate(pattern_str):
                    mod_width = int(char) * mod_w_px
                    if i % 2 == 0:  # 黑条
                        painter.drawRect(QRectF(curr_x, y, mod_width, bars_h_px))
                    curr_x += mod_width

                # 绘制条形码下方 13 位数字 (带足够的文字高度与居中，彻底消除裁切)
                font_code = QFont("Arial")
                font_code.setPixelSize(max(10, int(3.6 * scale_y)))
                font_code.setBold(True)
                painter.setFont(font_code)
                painter.setPen(QPen(QColor(0, 0, 0)))
                painter.drawText(QRectF(x, y + bars_h_px, w, text_h_px), Qt.AlignCenter | Qt.AlignVCenter, code)
                continue

            text_str = render_text(elem, data_map)
            if not text_str:
                continue

            font_name = str(elem.get("font_name", "Microsoft YaHei"))
            font_size_pt = float(elem.get("font_size", 8.0))
            font = QFont(font_name)
            font.setBold(bool(elem.get("bold", False)))

            # 驱动矢量打纸字号自适应算法
            pixel_size = max(8, int(font_size_pt * 25.4 / 72.0 * scale_y))
            font.setPixelSize(pixel_size)
            from PySide6.QtGui import QFontMetricsF
            fm = QFontMetricsF(font)
            text_rect = fm.boundingRect(text_str)
            min_pixel_size = max(6, int(4.5 * 25.4 / 72.0 * scale_y))
            while (text_rect.width() > w or text_rect.height() > h) and pixel_size > min_pixel_size:
                pixel_size -= 1
                font.setPixelSize(pixel_size)
                fm = QFontMetricsF(font)
                text_rect = fm.boundingRect(text_str)

            painter.setFont(font)
            painter.setPen(QPen(QColor(0, 0, 0)))

            alignment = Qt.AlignLeft | Qt.AlignVCenter
            if elem_type in ("produce_date_label", "produce_date"):
                alignment = Qt.AlignRight | Qt.AlignVCenter

            painter.drawText(QRectF(x, y, w, h), alignment, text_str)

        return True
    finally:
        painter.end()


def send_raw_tspl_to_win_printer(printer_name: str, box_code: str, width_mm: float = 210.0, height_mm: float = 100.0) -> bool:
    """通过 Windows 底层 Spooler 向物理打印机端口直接发送 RAW TSPL 指令 (第三重硬件出纸保险)。"""
    import ctypes
    import time
    class DOC_INFO_1W(ctypes.Structure):
        _fields_ = [
            ("pDocName", ctypes.c_wchar_p),
            ("pOutputFile", ctypes.c_wchar_p),
            ("pDatatype", ctypes.c_wchar_p),
        ]

    try:
        winspool = ctypes.WinDLL("winspool.drv")
        h_printer = ctypes.c_void_p()
        opened = False
        for attempt in range(3):
            if winspool.OpenPrinterW(ctypes.c_wchar_p(printer_name), ctypes.byref(h_printer), None) != 0:
                opened = True
                break
            time.sleep(0.2)
        if not opened:
            return False

        try:
            doc_info = DOC_INFO_1W("BoxLabelRAW", None, "RAW")
            job_id = winspool.StartDocPrinterW(h_printer, 1, ctypes.byref(doc_info))
            if job_id == 0:
                return False

            try:
                if winspool.StartPagePrinter(h_printer) != 0:
                    tspl_cmd = (
                        f"SIZE {int(width_mm)} mm, {int(height_mm)} mm\r\n"
                        f"GAP 3 mm, 0 mm\r\n"
                        f"DIRECTION 1\r\n"
                        f"CLS\r\n"
                        f"BARCODE 928,472,\"128\",224,1,0,3,6,\"{box_code}\"\r\n"
                        f"TEXT 928,700,\"TSS24.BF2\",0,2,2,\"{box_code}\"\r\n"
                        f"PRINT 1,1\r\n"
                    ).encode("gbk", errors="ignore")

                    bytes_written = ctypes.c_ulong(0)
                    winspool.WritePrinter(h_printer, tspl_cmd, len(tspl_cmd), ctypes.byref(bytes_written))
                    winspool.EndPagePrinter(h_printer)
                    return bytes_written.value > 0
                return False
            finally:
                winspool.EndDocPrinter(h_printer)
        finally:
            winspool.ClosePrinter(h_printer)
    except Exception:
        return False
