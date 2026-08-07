import copy
import json
import logging
import os
from datetime import datetime

from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtCore import Signal, Qt, QRectF, QSize
from PySide6.QtGui import QPixmap, QPainter, QColor, QFont, QPen, QIcon, QFontMetrics
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, QTableWidgetItem,
    QPushButton, QHeaderView, QCheckBox, QMessageBox, QLineEdit, QFileDialog,
    QComboBox, QGridLayout, QFrame
)

from rfid_printer.label_layout import (
    TEMPLATE_ID,
    is_required_element,
    is_template_visible,
    profile_name_for_size,
    render_text,
    resolve_asset_path,
    resolve_layout_elements,
)

logger = logging.getLogger("PrintTemplateDialog")

TOUCH_STYLE = """
QDialog { background-color: #F4F6F9; }
QTableWidget {
    background-color: #FFFFFF;
    gridline-color: #E2E8F0;
    font-size: 14px;
    color: #1E293B;
    border: 1px solid #CBD5E1;
    border-radius: 6px;
}
QTableWidget::item {
    padding: 6px 8px;
}
QHeaderView::section {
    background-color: #F1F5F9;
    color: #0F172A;
    font-weight: bold;
    font-size: 14px;
    padding: 8px 4px;
    border: none;
    border-bottom: 2px solid #CBD5E1;
    border-right: 1px solid #E2E8F0;
}
QLineEdit, QComboBox {
    border: 1px solid #CBD5E1;
    border-radius: 6px;
    padding: 6px 10px;
    font-size: 14px;
    background: #FFFFFF;
    color: #0F172A;
    min-height: 36px;
}
QLineEdit:focus, QComboBox:focus {
    border: 2px solid #2563EB;
    background: #FFFFFF;
}
"""

NATIVE_BTN_STYLE = """
QPushButton {
    background: #FFFFFF;
    border: 1px solid #CBD5E1;
    border-radius: 6px;
    font-weight: bold;
    font-size: 14px;
    color: #334155;
    padding: 6px 14px;
    min-height: 36px;
}
QPushButton:hover {
    background: #F8FAFC;
    border-color: #94A3B8;
    color: #0F172A;
}
QPushButton:pressed {
    background: #E2E8F0;
}
"""

GREEN_BTN_STYLE = """
QPushButton {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #34D399, stop:1 #059669);
    border: 1px solid #047857;
    border-radius: 6px;
    font-weight: bold;
    font-size: 14px;
    color: #FFFFFF;
    padding: 6px 14px;
    min-height: 36px;
}
QPushButton:hover {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #6EE7B7, stop:1 #10B981);
}
QPushButton:pressed {
    background: #047857;
}
"""

BLUE_BTN_STYLE = """
QPushButton {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #3B82F6, stop:1 #1D4ED8);
    border: 1px solid #1E40AF;
    border-radius: 6px;
    font-weight: bold;
    font-size: 14px;
    color: #FFFFFF;
    padding: 6px 14px;
    min-height: 36px;
}
QPushButton:hover {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #60A5FA, stop:1 #2563EB);
}
QPushButton:pressed {
    background: #1E40AF;
}
"""


def get_circled_num(index):
    circled_chars = ["①", "②", "③", "④", "⑤", "⑥", "⑦", "⑧", "⑨", "⑩", "⑪", "⑫", "⑬", "⑭", "⑮", "⑯", "⑰", "⑱", "⑲", "⑯"]
    if 1 <= index <= len(circled_chars):
        return circled_chars[index - 1]
    return f"({index})"


def create_blue_checked_icon():
    pix = QPixmap(28, 28)
    pix.fill(Qt.transparent)
    painter = QPainter(pix)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setBrush(QColor("#2563EB"))
    painter.setPen(QPen(QColor("#1D4ED8"), 1))
    painter.drawRoundedRect(1, 1, 26, 26, 5, 5)
    pen = QPen(QColor("#FFFFFF"), 3)
    pen.setCapStyle(Qt.RoundCap)
    pen.setJoinStyle(Qt.RoundJoin)
    painter.setPen(pen)
    painter.drawLine(7, 14, 12, 19)
    painter.drawLine(12, 19, 21, 8)
    painter.end()
    return QIcon(pix)


def create_white_unchecked_icon():
    pix = QPixmap(28, 28)
    pix.fill(Qt.transparent)
    painter = QPainter(pix)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setBrush(QColor("#FFFFFF"))
    painter.setPen(QPen(QColor("#94A3B8"), 2))
    painter.drawRoundedRect(1, 1, 26, 26, 5, 5)
    painter.end()
    return QIcon(pix)


class LabelSizeDialog(QDialog):
    """标签尺寸设定弹窗 (触控微调与快捷设定)"""

    def __init__(self, width_mm=140.0, height_mm=120.0, parent=None):
        super().__init__(parent)
        self.width_mm = width_mm
        self.height_mm = height_mm
        self.setWindowTitle("🏷️ 设置标签纸规格")
        self.resize(380, 260)
        self.setStyleSheet(TOUCH_STYLE)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        lbl_tip = QLabel("修改标签纸毫米尺寸 (长x宽)：")
        lbl_tip.setStyleSheet("font-weight: bold; font-size: 15px; color: #1E395B;")
        layout.addWidget(lbl_tip)

        grid = QGridLayout()
        grid.addWidget(QLabel("宽度 (mm)："), 0, 0)
        self.lbl_w = QLabel(f"{self.width_mm:.0f}")
        self.lbl_w.setStyleSheet("font-size: 18px; font-weight: bold; color: #2563EB;")
        grid.addWidget(self.lbl_w, 0, 1, Qt.AlignCenter)

        btn_w_sub = QPushButton("- 5")
        btn_w_sub.setFixedWidth(50)
        btn_w_sub.setStyleSheet(NATIVE_BTN_STYLE)
        btn_w_sub.clicked.connect(lambda: self.change_width(-5))
        grid.addWidget(btn_w_sub, 0, 2)

        btn_w_add = QPushButton("+ 5")
        btn_w_add.setFixedWidth(50)
        btn_w_add.setStyleSheet(NATIVE_BTN_STYLE)
        btn_w_add.clicked.connect(lambda: self.change_width(5))
        grid.addWidget(btn_w_add, 0, 3)

        grid.addWidget(QLabel("高度 (mm)："), 1, 0)
        self.lbl_h = QLabel(f"{self.height_mm:.0f}")
        self.lbl_h.setStyleSheet("font-size: 18px; font-weight: bold; color: #2563EB;")
        grid.addWidget(self.lbl_h, 1, 1, Qt.AlignCenter)

        btn_h_sub = QPushButton("- 5")
        btn_h_sub.setFixedWidth(50)
        btn_h_sub.setStyleSheet(NATIVE_BTN_STYLE)
        btn_h_sub.clicked.connect(lambda: self.change_height(-5))
        grid.addWidget(btn_h_sub, 1, 2)

        btn_h_add = QPushButton("+ 5")
        btn_h_add.setFixedWidth(50)
        btn_h_add.setStyleSheet(NATIVE_BTN_STYLE)
        btn_h_add.clicked.connect(lambda: self.change_height(5))
        grid.addWidget(btn_h_add, 1, 3)

        layout.addLayout(grid)

        # 常用尺寸快捷预设
        preset_box = QHBoxLayout()
        btn_140x120 = QPushButton("140x120 (标准)")
        btn_140x120.setStyleSheet(NATIVE_BTN_STYLE)
        btn_140x120.clicked.connect(lambda: self.set_size(140.0, 120.0))
        preset_box.addWidget(btn_140x120)

        btn_100x80 = QPushButton("100x80")
        btn_100x80.setStyleSheet(NATIVE_BTN_STYLE)
        btn_100x80.clicked.connect(lambda: self.set_size(100.0, 80.0))
        preset_box.addWidget(btn_100x80)

        layout.addLayout(preset_box)

        btn_confirm = QPushButton("确认修改尺寸")
        btn_confirm.setStyleSheet(BLUE_BTN_STYLE)
        btn_confirm.clicked.connect(self.accept)
        layout.addWidget(btn_confirm)

    def change_width(self, delta):
        self.width_mm = max(20.0, self.width_mm + delta)
        self.lbl_w.setText(f"{self.width_mm:.0f}")

    def change_height(self, delta):
        self.height_mm = max(20.0, self.height_mm + delta)
        self.lbl_h.setText(f"{self.height_mm:.0f}")

    def set_size(self, w, h):
        self.width_mm = w
        self.height_mm = h
        self.lbl_w.setText(f"{w:.0f}")
        self.lbl_h.setText(f"{h:.0f}")

    def get_size(self):
        return self.width_mm, self.height_mm


class InteractivePreviewLabel(QLabel):
    double_clicked_signal = Signal(float, float)

    def __init__(self, parent=None):
        super().__init__(parent)

    def mouseDoubleClickEvent(self, event):
        super().mouseDoubleClickEvent(event)
        pix = self.pixmap()
        if not pix or pix.isNull():
            return
        pos = event.position()
        lbl_w, lbl_h = self.width(), self.height()
        pix_w, pix_h = pix.width(), pix.height()
        if lbl_w <= 0 or lbl_h <= 0 or pix_w <= 0 or pix_h <= 0:
            return
        offset_x = (lbl_w - pix_w) / 2.0
        offset_y = (lbl_h - pix_h) / 2.0
        click_x = pos.x() - offset_x
        click_y = pos.y() - offset_y
        if 0 <= click_x <= pix_w and 0 <= click_y <= pix_h:
            rel_x = click_x / pix_w
            rel_y = click_y / pix_h
            self.double_clicked_signal.emit(rel_x, rel_y)


class EditFieldDialog(QDialog):
    """字段双击编辑弹窗"""

    def __init__(self, elem, seq_num_str="", parent=None):
        super().__init__(parent)
        self.elem = elem
        self.seq_num_str = seq_num_str
        self.elem_type = str(elem.get("type", ""))
        self.setWindowTitle(f"✏️ 编辑字段属性 {seq_num_str}")
        self.resize(440, 280)
        self.setStyleSheet(TOUCH_STYLE)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        lbl_title = QLabel(f"编辑 {self.seq_num_str} 字段文本与属性：")
        lbl_title.setStyleSheet("font-weight: bold; font-size: 15px; color: #1E395B;")
        layout.addWidget(lbl_title)

        grid = QGridLayout()

        grid.addWidget(QLabel("字段名称 (Label)："), 0, 0)
        self.edit_label = QLineEdit(str(self.elem.get("label", "")))
        grid.addWidget(self.edit_label, 0, 1)

        grid.addWidget(QLabel("显示内容 (Value)："), 1, 0)
        self.edit_val = QLineEdit(str(self.elem.get("value", "")))
        grid.addWidget(self.edit_val, 1, 1)

        grid.addWidget(QLabel("类型说明 (Desc)："), 2, 0)
        self.edit_desc = QLineEdit(str(self.elem.get("type_desc", "")))
        grid.addWidget(self.edit_desc, 2, 1)

        if self.elem_type == "brand_logo":
            grid.addWidget(QLabel("Logo 图片路径："), 3, 0)
            logo_box = QHBoxLayout()
            self.edit_logo = QLineEdit(str(self.elem.get("asset_path") or self.elem.get("value") or ""))
            btn_choose_logo = QPushButton("📁 浏览")
            btn_choose_logo.setStyleSheet(NATIVE_BTN_STYLE)
            btn_choose_logo.clicked.connect(self.on_choose_logo_file)
            logo_box.addWidget(self.edit_logo)
            logo_box.addWidget(btn_choose_logo)
            grid.addLayout(logo_box, 3, 1)

        layout.addLayout(grid)

        btn_box = QHBoxLayout()
        btn_ok = QPushButton("确认修改")
        btn_ok.setStyleSheet(BLUE_BTN_STYLE)
        btn_ok.clicked.connect(self.accept)

        btn_cancel = QPushButton("取消")
        btn_cancel.setStyleSheet(NATIVE_BTN_STYLE)
        btn_cancel.clicked.connect(self.reject)

        btn_box.addWidget(btn_ok)
        btn_box.addWidget(btn_cancel)
        layout.addLayout(btn_box)

    def on_choose_logo_file(self):
        fpath, _ = QFileDialog.getOpenFileName(self, "选择Logo图片", "", "图片文件 (*.png *.jpg *.jpeg *.bmp)")
        if fpath:
            self.edit_logo.setText(fpath)

    def get_data(self):
        res = {
            "label": self.edit_label.text().strip(),
            "value": self.edit_val.text().strip(),
            "type_desc": self.edit_desc.text().strip(),
        }
        if self.elem_type == "brand_logo":
            res["asset_path"] = self.edit_logo.text().strip()
        return res


class PrintPreviewDialog(QDialog):
    """打印效果可视化预览弹窗 (全真排版效果预览)"""

    elements_changed = Signal(object)

    def __init__(self, elements, width_mm=140.0, height_mm=120.0, preview_data=None, parent=None):
        super().__init__(parent)
        self.width_mm = width_mm
        self.height_mm = height_mm
        self.setWindowTitle(f"🏷️ 打印效果预览 ({width_mm:.0f}x{height_mm:.0f}mm)")
        self.resize(680, 480)
        self.setStyleSheet(TOUCH_STYLE)
        self.elements = copy.deepcopy(elements or [])
        self.preview_data = dict(preview_data or {})
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)

        info_lbl = QLabel(f"全真排版效果预览图 ({self.width_mm:.0f}mm x {self.height_mm:.0f}mm)：")
        info_lbl.setStyleSheet("font-weight: bold; font-size: 14px; color: #1E395B; margin-bottom: 4px;")
        layout.addWidget(info_lbl)

        self.preview_lbl = InteractivePreviewLabel()
        self.preview_lbl.setAlignment(Qt.AlignCenter)
        self.preview_lbl.double_clicked_signal.connect(self.on_preview_canvas_double_clicked)
        layout.addWidget(self.preview_lbl)

        btn_close = QPushButton("关闭预览")
        btn_close.setFixedWidth(120)
        btn_close.setStyleSheet(NATIVE_BTN_STYLE)
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close, alignment=Qt.AlignCenter)

        self.render_preview()

    def set_preview_data(self, data):
        if isinstance(data, dict):
            self.preview_data.update(data)
            self.render_preview()

    def on_preview_canvas_double_clicked(self, rel_x, rel_y):
        click_x_mm = rel_x * float(self.width_mm)
        click_y_mm = rel_y * float(self.height_mm)

        hit_elem = None
        for elem in self.elements:
            ex = float(elem.get("x", 0.0))
            ey = float(elem.get("y", 0.0))
            ew = float(elem.get("w", 20.0))
            eh = float(elem.get("h", 10.0))
            if ex <= click_x_mm <= ex + ew and ey <= click_y_mm <= ey + eh:
                hit_elem = elem
                break

        if not hit_elem and self.elements:
            hit_elem = self.elements[0]

        if hit_elem:
            elem_type = str(hit_elem.get("type", ""))
            EDITABLE_TYPES = {"spec", "shelf_life", "storage", "manufacturer", "unit_net_weight", "net_weight", "produce_date", "box_count", "box_unit"}
            is_editable = elem_type in EDITABLE_TYPES or bool(hit_elem.get("custom", False))

            if not is_editable:
                QMessageBox.information(self, "提示", "【灰底序号】为系统核心固定字段 (非手动可编辑)。\n【蓝底序号】为可双击编辑字段！")
                return

            dlg = EditFieldDialog(hit_elem, seq_num_str="✏️ 预览双击编辑", parent=self)
            if dlg.exec_() == QDialog.Accepted:
                data = dlg.get_data()
                hit_elem["label"] = data["label"]
                hit_elem["value"] = data["value"]
                hit_elem["type_desc"] = data["type_desc"]
                if elem_type == "brand_logo":
                    hit_elem["asset_path"] = data.get("asset_path", data["value"])

                self.render_preview()
                self.elements_changed.emit(copy.deepcopy(self.elements))

    def render_preview(self):
        max_canvas_w, max_canvas_h = 620, 360
        aspect = self.width_mm / max(1.0, self.height_mm)

        if aspect >= 1.0:
            width_px = max_canvas_w
            height_px = int(max_canvas_w / aspect)
        else:
            height_px = max_canvas_h
            width_px = int(max_canvas_h * aspect)

        pix = QPixmap(width_px, height_px)
        pix.fill(QColor(255, 255, 255))

        painter = QPainter(pix)
        painter.setRenderHint(QPainter.Antialiasing)

        pen_border = QPen(QColor(160, 160, 160), 2)
        painter.setPen(pen_border)
        painter.drawRect(1, 1, width_px - 2, height_px - 2)

        scale_x = width_px / max(1.0, self.width_mm)
        scale_y = height_px / max(1.0, self.height_mm)

        preview_data = {
            elem.get("type"): elem.get("value", "")
            for elem in self.elements
            if elem.get("type")
        }
        preview_data.update(self.preview_data)

        # 优先使用实时最新的13位箱码
        if not preview_data.get("barcode"):
            try:
                from page.config import CONFIG_DATA
                latest_case = CONFIG_DATA.get("caseCode")
                if latest_case:
                    preview_data["barcode"] = str(latest_case).strip()
            except Exception:
                pass

        seq_idx = 0
        placed_badge_rects = []
        for elem in self.elements:
            elem_type = elem.get("type")
            if elem_type in ("box_count", "box_unit"):
                box_spec_elem = next((item for item in self.elements if item.get("type") == "box_spec"), {})
                if not box_spec_elem or not box_spec_elem.get("enabled", True):
                    continue
            elif elem_type != "barcode" and not elem.get("enabled", True):
                continue

            if elem.get("print_direct") is False:
                continue

            seq_idx += 1
            circled_badge = get_circled_num(seq_idx)

            x = float(elem.get("x", 0.0)) * scale_x
            y = float(elem.get("y", 0.0)) * scale_y
            w = float(elem.get("w", 0.0)) * scale_x
            h = float(elem.get("h", 0.0)) * scale_y
            color = QColor(str(elem.get("color", "#000000")))

            if elem_type == "divider":
                pen = QPen(color, max(1, int(elem.get("line_width", 1))))
                painter.setPen(pen)
                painter.drawLine(int(x), int(y), int(x + w), int(y))
            elif elem_type == "brand_logo":
                logo_path = resolve_asset_path(str(elem.get("asset_path") or elem.get("value") or ""))
                logo = QPixmap(logo_path)
                if not logo.isNull():
                    painter.drawPixmap(QRectF(x, y, w, h), logo, QRectF(logo.rect()))
            elif elem_type == "barcode":
                code = str(preview_data.get("barcode") or elem.get("value") or "1785813377794").strip()
                if preview_data.get("barcode"):
                    code = str(preview_data.get("barcode")).strip()
                text_height = max(8, int(2.8 * scale_y))
                bars_bottom = int(y + h - text_height)
                painter.setPen(Qt.NoPen)
                painter.setBrush(QColor(0, 0, 0))
                bx = int(x)
                index = 0
                widths = (2, 1, 3, 1, 2, 2, 1, 4)
                while bx < int(x + w):
                    bar_w = max(1, int(widths[index % len(widths)] * scale_x / 2.5))
                    if index % 2 == 0:
                        painter.drawRect(bx, int(y), min(bar_w, int(x + w) - bx), max(1, bars_bottom - int(y)))
                    bx += bar_w
                    index += 1
                if code:
                    font_c = QFont("Arial", max(8, int(2.8 * scale_y)), QFont.Bold)
                    painter.setFont(font_c)
                    painter.setPen(QPen(QColor(0, 0, 0)))
                    painter.drawText(QRectF(x, bars_bottom, w, text_height), Qt.AlignCenter, code)
            else:
                text_str = render_text(elem, preview_data)
                if text_str:
                    font = QFont(str(elem.get("font_name", "SimSun")))
                    font_size_pt = float(elem.get("font_size", 10.0))
                    px_size = max(8, int(font_size_pt * 25.4 / 72.0 * scale_y))
                    font.setPixelSize(px_size)
                    font.setBold(bool(elem.get("bold", False)))

                    # 动态测量字宽并自动适应容器宽度
                    fm = QFontMetrics(font)
                    text_w = fm.horizontalAdvance(text_str)
                    if text_w > w and w > 0:
                        scaled_size = max(6, int(px_size * (w / text_w)))
                        font.setPixelSize(scaled_size)

                    painter.setFont(font)
                    painter.setPen(QPen(color))
                    alignment = Qt.AlignLeft | Qt.AlignVCenter
                    if elem_type in ("produce_date_label", "produce_date"):
                        alignment = Qt.AlignCenter
                    painter.drawText(QRectF(x, y, w, h), alignment, text_str)

            # 绘制小序号角标 ①, ②, ③ (清晰区分两大类颜色 + 严密防碰撞遮挡算法)
            EDITABLE_TYPES = {"spec", "shelf_life", "storage", "manufacturer", "unit_net_weight", "net_weight", "produce_date", "box_count", "box_unit"}
            is_editable = elem_type in EDITABLE_TYPES or bool(elem.get("custom", False))

            badge_bg = QColor("#2B579A") if is_editable else QColor("#505A69")
            badge_txt_color = QColor("#FFFFFF")

            badge_font = QFont("Microsoft YaHei", max(9, int(3.0 * scale_y)), QFont.Bold)
            painter.setFont(badge_font)
            painter.setPen(Qt.NoPen)
            painter.setBrush(badge_bg)

            bw_size, bh_size = 20.0, 17.0
            cur_bx = max(2.0, min(width_px - bw_size - 2.0, x - 20.0 if x >= 20.0 else x))
            cur_by = max(2.0, min(height_px - bh_size - 2.0, y - 2.0))

            if elem_type == "box_unit":
                cur_bx = max(2.0, min(width_px - bw_size - 2.0, x - 2.0))
                cur_by = max(2.0, min(height_px - bh_size - 2.0, y - 2.0))
            elif elem_type == "barcode":
                cur_bx = min(width_px - bw_size - 2.0, x - 22.0)
                cur_by = min(height_px - bh_size - 2.0, y + 2.0)

            for prev_rect in placed_badge_rects:
                px1, py1, pw1, ph1 = prev_rect
                if not (cur_bx + bw_size <= px1 or cur_bx >= px1 + pw1 or cur_by + bh_size <= py1 or cur_by >= py1 + ph1):
                    cur_by = min(height_px - bh_size - 2.0, py1 + ph1 + 2.0)

            placed_badge_rects.append((cur_bx, cur_by, bw_size, bh_size))

            painter.drawRoundedRect(QRectF(cur_bx, cur_by, bw_size, bh_size), 4, 4)
            painter.setPen(QPen(badge_txt_color))
            painter.drawText(QRectF(cur_bx, cur_by, bw_size, bh_size), Qt.AlignCenter, circled_badge)

        painter.end()
        self.preview_lbl.setPixmap(pix)


class PrintTemplateDialog(QDialog):
    """本地化打印模板管理对话框 (840x540 舒适轻量窗口，带蓝色纸张按钮与①②③图标)"""

    elements_changed = Signal(object)

    def __init__(self, config_path="config/settings.json", preview_data=None, parent=None):
        super().__init__(parent)
        self.config_path = os.path.abspath(config_path)
        self.setWindowTitle("🏷️ 打印模板管理与勾选")
        self.resize(840, 540)
        self.setStyleSheet(TOUCH_STYLE)
        self.setWindowModality(Qt.WindowModal)

        self.elements = []
        self.label_width_mm = 140.0
        self.label_height_mm = 120.0
        self.preview_data = dict(preview_data or {})

        self.icon_checked = create_blue_checked_icon()
        self.icon_unchecked = create_white_unchecked_icon()

        self.load_elements_config()
        self.init_ui()
        self.populate_table()

    def load_elements_config(self):
        data = {}
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception as e:
                logger.error(f"读取模板配置失败: {e}")

        label_cfg = data.get("label", {})
        self.label_width_mm = float(label_cfg.get("width_mm", 140.0))
        self.label_height_mm = float(label_cfg.get("height_mm", 120.0))

        self.elements = resolve_layout_elements(
            data.get("layout", {}),
            self.label_width_mm,
            self.label_height_mm,
        )

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(10)

        # 1. 顶部全功能操作栏 (包含蓝色大尺寸按钮、🔍 搜索、🌪️ 筛选、全选/反选)
        top_bar = QHBoxLayout()

        self.btn_size_dialog = QPushButton(f"🏷️ 纸张: {self.label_width_mm:.0f}x{self.label_height_mm:.0f}mm")
        self.btn_size_dialog.setStyleSheet(BLUE_BTN_STYLE)
        self.btn_size_dialog.clicked.connect(self.on_open_size_dialog)
        top_bar.addWidget(self.btn_size_dialog)

        top_bar.addSpacing(10)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 搜索字段内容/类型说明...")
        self.search_input.setClearButtonEnabled(True)
        self.search_input.setFixedWidth(240)
        self.search_input.textChanged.connect(self.apply_filter_search)
        top_bar.addWidget(self.search_input)

        lbl_filter = QLabel("🌪️ 筛选:")
        lbl_filter.setStyleSheet("font-weight: bold; color: #334155;")
        top_bar.addWidget(lbl_filter)

        self.combo_filter = QComboBox()
        self.combo_filter.addItems(["全部字段", "仅看已勾选", "仅看未勾选", "基础文本", "真实箱码条形码", "自定义扩展"])
        self.combo_filter.setFixedWidth(120)
        self.combo_filter.currentIndexChanged.connect(self.apply_filter_search)
        top_bar.addWidget(self.combo_filter)

        top_bar.addStretch()

        self.btn_select_all = QPushButton("☑️ 全选")
        self.btn_select_all.setStyleSheet(NATIVE_BTN_STYLE)
        self.btn_select_all.clicked.connect(self.on_select_all)
        top_bar.addWidget(self.btn_select_all)

        self.btn_deselect_all = QPushButton("🔳 反选")
        self.btn_deselect_all.setStyleSheet(NATIVE_BTN_STYLE)
        self.btn_deselect_all.clicked.connect(self.on_deselect_all)
        top_bar.addWidget(self.btn_deselect_all)

        main_layout.addLayout(top_bar)

        # 2. 核心表格 (4 列：序号, 打印勾选, 字段内容, 类型说明)
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["序号", "打印勾选", "字段内容 (双击编辑内容)", "类型说明 (双击编辑说明)"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        self.table.setColumnWidth(0, 60)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Fixed)
        self.table.setColumnWidth(1, 90)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.verticalHeader().setDefaultSectionSize(46)
        self.table.itemDoubleClicked.connect(self.on_table_double_clicked)
        main_layout.addWidget(self.table)

        # 3. 底部主要操作按钮 (带绿色高亮打印预览 & 宝蓝高亮保存)
        btn_bar = QHBoxLayout()

        self.btn_add = QPushButton("➕ 新增字段")
        self.btn_add.setStyleSheet(NATIVE_BTN_STYLE)
        self.btn_add.clicked.connect(self.on_add_field)
        btn_bar.addWidget(self.btn_add)

        self.btn_edit = QPushButton("✏️ 编辑内容")
        self.btn_edit.setStyleSheet(NATIVE_BTN_STYLE)
        self.btn_edit.clicked.connect(self.on_edit_field)
        btn_bar.addWidget(self.btn_edit)

        self.btn_delete = QPushButton("🗑️ 删除勾选了的")
        self.btn_delete.setStyleSheet(NATIVE_BTN_STYLE)
        self.btn_delete.clicked.connect(self.on_delete_checked_fields)
        btn_bar.addWidget(self.btn_delete)

        self.btn_preview = QPushButton("👁️ 打印效果预览")
        self.btn_preview.setStyleSheet(GREEN_BTN_STYLE)
        self.btn_preview.clicked.connect(self.on_preview_clicked)
        btn_bar.addWidget(self.btn_preview)

        btn_bar.addStretch()

        self.btn_save = QPushButton("💾 保存配置并应用")
        self.btn_save.setStyleSheet(BLUE_BTN_STYLE)
        self.btn_save.clicked.connect(self.on_save_and_close)
        btn_bar.addWidget(self.btn_save)

        self.btn_cancel = QPushButton("取消")
        self.btn_cancel.setStyleSheet(NATIVE_BTN_STYLE)
        self.btn_cancel.clicked.connect(self.reject)
        btn_bar.addWidget(self.btn_cancel)

        main_layout.addLayout(btn_bar)

    def on_open_size_dialog(self):
        dlg = LabelSizeDialog(self.label_width_mm, self.label_height_mm, parent=self)
        if dlg.exec_() == QDialog.Accepted:
            w, h = dlg.get_size()
            self.label_width_mm = w
            self.label_height_mm = h
            self.btn_size_dialog.setText(f"🏷️ 纸张: {w:.0f}x{h:.0f}mm")
            self.elements = resolve_layout_elements(
                {"template_id": TEMPLATE_ID, "elements": self.elements},
                w, h
            )
            self.populate_table()
            self._emit_elements_changed()

    def _emit_elements_changed(self):
        self.elements_changed.emit(copy.deepcopy(self.elements))

    def populate_table(self):
        self.table.setRowCount(0)
        visible_idx = 0
        for elem in self.elements:
            if not is_template_visible(elem):
                continue
            row = self.table.rowCount()
            self.table.insertRow(row)
            visible_idx += 1

            # Column 0: 序号 (①, ②, ③...)
            circled_str = get_circled_num(visible_idx)
            seq_item = QTableWidgetItem(circled_str)
            seq_item.setTextAlignment(Qt.AlignCenter)
            seq_item.setFlags(seq_item.flags() & ~Qt.ItemIsEditable)
            seq_item.setFont(QFont("Microsoft YaHei", 14, QFont.Bold))
            self.table.setItem(row, 0, seq_item)

            # Column 1: 纯蓝底白勾 ☑️ 图标触控复选按钮
            is_chk = elem.get("enabled", True)
            chk_btn = QPushButton()
            chk_btn.setIcon(self.icon_checked if is_chk else self.icon_unchecked)
            chk_btn.setIconSize(QSize(28, 28))
            chk_btn.setFixedSize(36, 36)
            chk_btn.setFlat(True)
            chk_btn.setProperty("is_checked", is_chk)

            if elem.get("type") in ("barcode", "divider", "product_caption"):
                chk_btn.setEnabled(False)
                chk_btn.setIcon(self.icon_checked)
                chk_btn.setProperty("is_checked", True)

            chk_btn.clicked.connect(lambda _, b=chk_btn: self.toggle_chk_btn(b))

            chk_widget = QtWidgets.QWidget()
            chk_layout = QHBoxLayout(chk_widget)
            chk_layout.setContentsMargins(0, 0, 0, 0)
            chk_layout.setAlignment(Qt.AlignCenter)
            chk_layout.addWidget(chk_btn)
            self.table.setCellWidget(row, 1, chk_widget)

            # Column 2: 内容
            label_name = elem.get("label", "")
            val_text = elem.get("value", "")
            if elem.get("type") == "barcode":
                real_code = str(self.preview_data.get("barcode") or "")
                content_str = f"箱码条形码：{real_code or '1785813377794'}"
            elif elem.get("type") == "brand_logo":
                asset_p = elem.get("asset_path") or val_text or "assets/gaoyuanan_logo.png"
                content_str = f"高原安 Logo 图片路径：{asset_p}"
            elif label_name and val_text and label_name != val_text:
                content_str = f"{label_name}：{val_text}"
            else:
                content_str = val_text or label_name

            content_item = QTableWidgetItem(content_str)
            content_item.setData(Qt.UserRole, str(elem.get("type", "")))
            if elem.get("type") in ("barcode", "divider", "product_caption"):
                content_item.setFlags(content_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, 2, content_item)

            # Column 3: 类型说明
            type_desc = elem.get("type_desc", "")
            if not type_desc:
                if elem.get("type") == "barcode":
                    type_desc = "固定条形码 (不可取消)"
                elif elem.get("type") == "brand_logo":
                    type_desc = "Logo图片 (可取消/更换)"
                elif elem.get("type") == "divider":
                    type_desc = "固定分隔线 (不可取消)"
                elif elem.get("type") == "product_caption":
                    type_desc = "固定标题 (不可取消)"
                else:
                    type_desc = "可选产品字段"

            type_item = QTableWidgetItem(type_desc)
            if elem.get("type") in ("barcode", "divider", "product_caption"):
                type_item.setFlags(type_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, 3, type_item)

    def toggle_chk_btn(self, btn):
        curr = bool(btn.property("is_checked"))
        nxt = not curr
        btn.setProperty("is_checked", nxt)
        btn.setIcon(self.icon_checked if nxt else self.icon_unchecked)
        self.elements = self.collect_elements_from_table()
        self._emit_elements_changed()

    def apply_filter_search(self):
        query = self.search_input.text().strip().lower()
        filter_mode = self.combo_filter.currentText()

        for row in range(self.table.rowCount()):
            chk_widget = self.table.cellWidget(row, 1)
            chk_btn = chk_widget.findChild(QPushButton) if chk_widget else None
            is_checked = bool(chk_btn.property("is_checked")) if chk_btn else False

            content_text = self.table.item(row, 2).text().lower() if self.table.item(row, 2) else ""
            type_text = self.table.item(row, 3).text().lower() if self.table.item(row, 3) else ""

            matches_search = (not query) or (query in content_text) or (query in type_text)

            matches_filter = True
            if filter_mode == "仅看已勾选":
                matches_filter = is_checked
            elif filter_mode == "仅看未勾选":
                matches_filter = not is_checked
            elif filter_mode == "基础文本":
                matches_filter = ("基础文本" in type_text)
            elif filter_mode == "真实箱码条形码":
                matches_filter = ("真实识别箱码" in type_text or "条码" in type_text)
            elif filter_mode == "自定义扩展":
                matches_filter = ("自定义" in type_text or "扩展" in type_text)

            show_row = matches_search and matches_filter
            self.table.setRowHidden(row, not show_row)

    def on_select_all(self):
        for elem in self.elements:
            elem["enabled"] = True
        self.populate_table()
        self._emit_elements_changed()

    def on_deselect_all(self):
        for elem in self.elements:
            if not is_required_element(elem):
                elem["enabled"] = False
        self.populate_table()
        self._emit_elements_changed()

    def collect_elements_from_table(self):
        updated_by_type = {
            str(elem.get("type", "")): dict(elem)
            for elem in self.elements
            if elem.get("type")
        }
        original_order = [str(elem.get("type", "")) for elem in self.elements if elem.get("type")]

        for row in range(self.table.rowCount()):
            chk_widget = self.table.cellWidget(row, 1)
            chk_btn = chk_widget.findChild(QPushButton) if chk_widget else None
            is_enabled = bool(chk_btn.property("is_checked")) if chk_btn else True

            content_item = self.table.item(row, 2)
            content_str = content_item.text().strip() if content_item else ""
            type_desc_item = self.table.item(row, 3)
            type_desc_str = type_desc_item.text().strip() if type_desc_item else ""

            elem_type = str(content_item.data(Qt.UserRole) or f"custom_{row}") if content_item else f"custom_{row}"
            orig = updated_by_type.get(elem_type, {})
            if is_required_element(orig):
                is_enabled = True

            if is_required_element(orig):
                label_name = str(orig.get("label", ""))
                val_text = str(orig.get("value", ""))
            elif "：" in content_str:
                parts = content_str.split("：", 1)
                label_name = parts[0].strip()
                val_text = parts[1].strip()
            elif ":" in content_str:
                parts = content_str.split(":", 1)
                label_name = parts[0].strip()
                val_text = parts[1].strip()
            else:
                label_name = content_str
                val_text = ""

            new_item = dict(orig)
            new_item.update({
                "type": elem_type,
                "label": label_name,
                "value": val_text,
                "type_desc": type_desc_str,
                "enabled": is_enabled,
            })
            updated_by_type[elem_type] = new_item

        result = [updated_by_type[item_type] for item_type in original_order if item_type in updated_by_type]
        for item_type, item in updated_by_type.items():
            if item_type not in original_order:
                result.append(item)
        return result

    def on_table_double_clicked(self, item):
        row = item.row()
        self.edit_row_by_dialog(row)

    def on_edit_field(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "提示", "请先点击选中表格中要编辑的一行！")
            return
        self.edit_row_by_dialog(row)

    def edit_row_by_dialog(self, row):
        content_item = self.table.item(row, 2)
        elem_type = str(content_item.data(Qt.UserRole) or "") if content_item else ""
        elem = next((item for item in self.elements if item.get("type") == elem_type), {})
        if elem_type in ("barcode", "divider", "product_caption"):
            QMessageBox.information(self, "提示", "这是基础核心绘制图层，参数固定不可编辑。")
            return

        seq_str = self.table.item(row, 0).text() if self.table.item(row, 0) else ""
        dlg = EditFieldDialog(elem, seq_num_str=seq_str, parent=self)
        if dlg.exec_() == QDialog.Accepted:
            data = dlg.get_data()
            new_label = data["label"]
            new_val = data["value"]
            new_desc = data["type_desc"]

            if elem_type == "brand_logo":
                elem["asset_path"] = data.get("asset_path", new_val)
            elem["label"] = new_label
            elem["value"] = new_val
            elem["type_desc"] = new_desc

            self.populate_table()
            self.apply_filter_search()
            self._emit_elements_changed()

    def on_add_field(self):
        elem = {"label": "新字段", "value": "自定义内容", "type_desc": "可选字段", "type": f"custom_{len(self.elements)+1}"}
        dlg = EditFieldDialog(elem, seq_num_str="➕ 新增", parent=self)
        if dlg.exec_() == QDialog.Accepted:
            data = dlg.get_data()
            new_elem = {
                "type": f"custom_{len(self.elements)+1}",
                "label": data["label"] or "新字段",
                "value": data["value"] or "自定义内容",
                "type_desc": data["type_desc"] or "可选字段",
                "enabled": True,
                "custom": True,
                "x": 6.0,
                "y": 55.0,
                "w": 98.0,
                "h": 6.5,
                "font_size": 13.0,
                "bold": True,
                "color": "#000000",
            }
            self.elements.append(new_elem)
            self.populate_table()
            self._emit_elements_changed()

    def on_delete_checked_fields(self):
        checked_rows = []
        for row in range(self.table.rowCount()):
            chk_widget = self.table.cellWidget(row, 1)
            chk_btn = chk_widget.findChild(QPushButton) if chk_widget else None
            if chk_btn and bool(chk_btn.property("is_checked")):
                content_item = self.table.item(row, 2)
                elem_type = str(content_item.data(Qt.UserRole) or "") if content_item else ""
                orig = next((item for item in self.elements if item.get("type") == elem_type), {})
                if not is_required_element(orig):
                    checked_rows.append(elem_type)

        if not checked_rows:
            QMessageBox.information(self, "提示", "请先在表格第二列勾选要删除的自定义/可选字段！\n（固定核心图层不可删除）")
            return

        reply = QMessageBox.question(self, "确认删除", f"确定要删除勾选的 {len(checked_rows)} 个字段吗？", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.elements = [item for item in self.elements if item.get("type") not in checked_rows]
            self.populate_table()
            self._emit_elements_changed()

    def on_preview_clicked(self):
        curr_elems = self.collect_elements_from_table()
        self.elements = curr_elems
        self._emit_elements_changed()
        w_mm = self.label_width_mm
        h_mm = self.label_height_mm
        preview_elements = resolve_layout_elements(
            {
                "template_id": TEMPLATE_ID,
                "elements": curr_elems,
            },
            w_mm,
            h_mm,
        )
        sample_preview_data = dict(self.preview_data or {})
        if not sample_preview_data.get("barcode"):
            sample_preview_data["barcode"] = "1785813377794"

        dlg = PrintPreviewDialog(preview_elements, w_mm, h_mm, sample_preview_data, parent=self)
        dlg.elements_changed.connect(self._on_preview_elements_changed)
        dlg.exec_()

    def set_preview_data(self, preview_data=None):
        self.preview_data = dict(preview_data or {})

    def show_preview_dialog(self, parent=None):
        curr_elems = self.collect_elements_from_table()
        self.elements = curr_elems
        self._emit_elements_changed()
        w_mm = self.label_width_mm
        h_mm = self.label_height_mm
        preview_elements = resolve_layout_elements(
            {"template_id": TEMPLATE_ID, "elements": curr_elems},
            w_mm,
            h_mm,
        )
        sample_preview_data = dict(self.preview_data or {})
        if not sample_preview_data.get("barcode"):
            sample_preview_data["barcode"] = "1785813377794"
        dlg = PrintPreviewDialog(
            preview_elements,
            w_mm,
            h_mm,
            sample_preview_data,
            parent=parent or self,
        )
        dlg.elements_changed.connect(self._on_preview_elements_changed)
        return dlg.exec_() == QDialog.Accepted

    def _on_preview_elements_changed(self, elements):
        self.elements = copy.deepcopy(elements or [])
        self.populate_table()
        self.apply_filter_search()
        self._emit_elements_changed()

    def on_save_and_close(self):
        self.elements = self.collect_elements_from_table()
        self.save_elements_config()
        self._emit_elements_changed()
        QMessageBox.information(self, "保存成功", "【打印模板保存成功】\n打纸时将严格按照您输入的尺寸与勾选字段进行 100% 动态排版打印！")
        self.accept()

    def save_elements_config(self):
        data = {}
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception:
                pass
        data["label"] = {"width_mm": self.label_width_mm, "height_mm": self.label_height_mm}
        data["layout"] = {"elements": self.elements}
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存模板到本地失败: {e}")
