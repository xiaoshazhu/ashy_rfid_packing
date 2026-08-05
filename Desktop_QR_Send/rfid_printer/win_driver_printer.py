"""Windows 打印机驱动矢量高清打印模块。

通过 Windows 官方驱动（JiEPRT T63RZ）执行矢量高精度打纸，
解决普通 C SDK 直连模式下文本发淡、条码不清晰、边界未铺满对齐的问题。
"""

from __future__ import annotations

import os
import sys
from datetime import datetime
from typing import Any, Dict, List, Mapping, Optional

from PySide6.QtCore import QRectF, QSizeF, Qt
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


def get_target_windows_printer() -> Optional[QPrinterInfo]:
    """寻找本地连接的 JiEPRT T63RZ 或热敏打印机驱动。"""
    printers = QPrinterInfo.availablePrinters()
    for p in printers:
        name = p.printerName()
        if "T63" in name or "JiEPRT" in name or "Postek" in name or "热敏" in name:
            return p
    if printers:
        return QPrinterInfo.defaultPrinter()
    return None


def print_canvas_via_win_driver(
    elements: List[Dict[str, Any]],
    preview_data: Mapping[str, Any],
    width_mm: float = 100.0,
    height_mm: float = 80.0,
) -> bool:
    """使用 Windows 官方驱动（JiEPRT T63RZ）绘制 100% 矢量清晰度标签并出纸。"""
    target_printer = get_target_windows_printer()
    if not target_printer:
        return False

    printer = QPrinter(target_printer, QPrinter.HighResolution)
    page_size = QPageSize(QSizeF(width_mm, height_mm), QPageSize.Millimeter)
    printer.setPageSize(page_size)
    printer.setFullPage(True)

    page_rect = printer.pageLayout().paintRectPixels(printer.resolution())
    canvas_w_px = max(100, page_rect.width())
    canvas_h_px = max(100, page_rect.height())

    scale_x = canvas_w_px / max(1.0, width_mm)
    scale_y = canvas_h_px / max(1.0, height_mm)

    data_map = dict(preview_data or {})
    data_map.setdefault("produce_date", datetime.now().strftime("%Y.%m.%d"))

    painter = QPainter()
    if not painter.begin(printer):
        return False

    try:
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

            x = float(elem.get("x", 0.0)) * scale_x
            y = float(elem.get("y", 0.0)) * scale_y
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
                code = str(data_map.get("barcode") or elem.get("value") or "")
                pattern_str = encode_code128_b_pattern(code)

                text_h_px = max(12, int(3.5 * scale_y))
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

                # 绘制条形码下方 13 位数字
                font_code = QFont("Arial")
                font_code.setPixelSize(max(10, int(3.2 * scale_y)))
                font_code.setBold(True)
                painter.setFont(font_code)
                painter.setPen(QPen(QColor(0, 0, 0)))
                painter.drawText(QRectF(x, y + bars_h_px, w, text_h_px), Qt.AlignCenter, code)
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
                alignment = Qt.AlignCenter
            elif elem_type == "box_count":
                alignment = Qt.AlignRight | Qt.AlignVCenter

            painter.drawText(QRectF(x, y, w, h), alignment, text_str)

        return True
    finally:
        painter.end()
