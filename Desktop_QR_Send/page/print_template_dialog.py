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

class TouchMessageBox(QDialog):
    """触摸屏专用高清大字号、大触控按键、大关闭(X)按钮消息弹窗"""

    def __init__(self, parent=None, title="提示", message="", icon_type="info", buttons=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.result_value = None
        self.title_text = title
        self.message_text = message
        self.icon_type = icon_type
        self.buttons_config = buttons or [("OK", "ok")]
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)

        card = QFrame()
        card.setObjectName("TouchDialogCard")
        card.setStyleSheet("""
            #TouchDialogCard {
                background-color: #FFFFFF;
                border: 2px solid #CBD5E1;
                border-radius: 16px;
            }
        """)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(0, 0, 0, 20)
        card_layout.setSpacing(16)

        # Title bar
        title_bar = QFrame()
        title_bar.setStyleSheet("""
            QFrame {
                background-color: #F1F5F9;
                border-top-left-radius: 14px;
                border-top-right-radius: 14px;
                border-bottom: 1px solid #E2E8F0;
            }
        """)
        tb_layout = QHBoxLayout(title_bar)
        tb_layout.setContentsMargins(20, 10, 12, 10)

        lbl_title = QLabel(self.title_text)
        lbl_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #1E293B; background: transparent;")
        tb_layout.addWidget(lbl_title, stretch=1)

        # 大字号触控关闭按钮 [X]
        btn_close = QPushButton("✕")
        btn_close.setFixedSize(40, 40)
        btn_close.setStyleSheet("""
            QPushButton {
                background: #E2E8F0;
                color: #475569;
                border: none;
                border-radius: 20px;
                font-size: 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #EF4444;
                color: #FFFFFF;
            }
            QPushButton:pressed {
                background: #DC2626;
                color: #FFFFFF;
            }
        """)
        btn_close.clicked.connect(self.reject)
        tb_layout.addWidget(btn_close)
        card_layout.addWidget(title_bar)

        # 内容区
        content_layout = QHBoxLayout()
        content_layout.setContentsMargins(24, 12, 24, 8)
        content_layout.setSpacing(16)

        icon_str = "ℹ️"
        if self.icon_type == "warning":
            icon_str = "⚠️"
        elif self.icon_type in ("error", "critical"):
            icon_str = "❌"
        elif self.icon_type == "question":
            icon_str = "❓"

        lbl_icon = QLabel(icon_str)
        lbl_icon.setStyleSheet("font-size: 36px; background: transparent;")
        lbl_icon.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        content_layout.addWidget(lbl_icon)

        lbl_msg = QLabel(self.message_text)
        lbl_msg.setWordWrap(True)
        lbl_msg.setStyleSheet("font-size: 16px; font-weight: bold; color: #334155; line-height: 1.4; background: transparent;")
        content_layout.addWidget(lbl_msg, stretch=1)

        card_layout.addLayout(content_layout)

        # 按钮区
        btn_row = QHBoxLayout()
        btn_row.setContentsMargins(24, 8, 24, 0)
        btn_row.setSpacing(16)
        btn_row.addStretch(1)

        for btn_text, ret_val in self.buttons_config:
            btn = QPushButton(btn_text)
            btn.setMinimumHeight(48)
            btn.setMinimumWidth(130)
            if ret_val in ("ok", "yes", True):
                btn.setStyleSheet("""
                    QPushButton {
                        background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #2563EB, stop:1 #1D4ED8);
                        color: #FFFFFF;
                        font-size: 17px;
                        font-weight: bold;
                        border: 1px solid #1E40AF;
                        border-radius: 8px;
                        padding: 8px 24px;
                    }
                    QPushButton:hover { background: #1D4ED8; }
                    QPushButton:pressed { background: #1E40AF; }
                """)
            else:
                btn.setStyleSheet("""
                    QPushButton {
                        background: #FFFFFF;
                        color: #475569;
                        font-size: 16px;
                        font-weight: bold;
                        border: 1px solid #CBD5E1;
                        border-radius: 8px;
                        padding: 8px 20px;
                    }
                    QPushButton:hover { background: #F8FAFC; border-color: #94A3B8; }
                    QPushButton:pressed { background: #E2E8F0; }
                """)

            def make_slot(val):
                return lambda: self._on_btn_clicked(val)

            btn.clicked.connect(make_slot(ret_val))
            btn_row.addWidget(btn)

        btn_row.addStretch(1)
        card_layout.addLayout(btn_row)

        main_layout.addWidget(card)
        self.setMinimumWidth(500)

    def _on_btn_clicked(self, val):
        self.result_value = val
        self.accept()

    @classmethod
    def information(cls, parent, title, message):
        dlg = cls(parent, title, message, icon_type="info", buttons=[("OK", "ok")])
        dlg.exec_()

    @classmethod
    def warning(cls, parent, title, message):
        dlg = cls(parent, title, message, icon_type="warning", buttons=[("OK", "ok")])
        dlg.exec_()

    @classmethod
    def critical(cls, parent, title, message):
        dlg = cls(parent, title, message, icon_type="error", buttons=[("OK", "ok")])
        dlg.exec_()

    @classmethod
    def question(cls, parent, title, message, buttons=None):
        if not buttons:
            buttons = [("确定", "yes"), ("取消", "no")]
        dlg = cls(parent, title, message, icon_type="question", buttons=buttons)
        if dlg.exec_() == QDialog.Accepted:
            return dlg.result_value
        return "no"


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
QMessageBox {
    background-color: #FFFFFF;
    min-width: 480px;
}
QMessageBox QLabel {
    font-size: 16px;
    font-weight: bold;
    color: #1E293B;
    padding: 10px;
}
QMessageBox QPushButton {
    background: #2563EB;
    color: #FFFFFF;
    font-size: 16px;
    font-weight: bold;
    border-radius: 8px;
    min-width: 120px;
    min-height: 46px;
    padding: 8px 24px;
}
QMessageBox QPushButton:hover {
    background: #1D4ED8;
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
        btn_150x75 = QPushButton("150x75 (标准全幅)")
        btn_150x75.setStyleSheet(NATIVE_BTN_STYLE)
        btn_150x75.clicked.connect(lambda: self.set_size(150.0, 75.0))
        preset_box.addWidget(btn_150x75)

        btn_200x100 = QPushButton("200x100")
        btn_200x100.setStyleSheet(NATIVE_BTN_STYLE)
        btn_200x100.clicked.connect(lambda: self.set_size(200.0, 100.0))
        preset_box.addWidget(btn_200x100)

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
    """简易单行属性编辑弹窗（只有一行信息输入）"""

    def __init__(self, elem, seq_num_str="", parent=None):
        super().__init__(parent)
        self.elem = elem
        self.elem_type = str(elem.get("type", ""))
        label_title = str(elem.get("label", "字段"))
        self.setWindowTitle(f"✏️ 修改【{label_title}】显示内容")
        self.resize(420, 180)
        self.setStyleSheet(TOUCH_STYLE)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        lbl_title = QLabel(f"修改 【{self.elem.get('label', '字段')}】 显示文本：")
        lbl_title.setStyleSheet("font-weight: bold; font-size: 15px; color: #1E395B;")
        layout.addWidget(lbl_title)

        cur_val = str(self.elem.get("value", "")).strip()
        self.edit_val = QLineEdit(cur_val)
        self.edit_val.setPlaceholderText("请输入要显示的文字内容")
        layout.addWidget(self.edit_val)

        if self.elem_type == "brand_logo":
            logo_box = QHBoxLayout()
            self.edit_logo = QLineEdit(str(self.elem.get("asset_path") or self.elem.get("value") or ""))
            btn_choose = QPushButton("📁 选择文件")
            btn_choose.setStyleSheet(NATIVE_BTN_STYLE)
            btn_choose.clicked.connect(self.on_choose_logo_file)
            logo_box.addWidget(self.edit_logo)
            logo_box.addWidget(btn_choose)
            layout.addLayout(logo_box)

        btn_box = QHBoxLayout()
        btn_ok = QPushButton("确认修改")
        btn_ok.setStyleSheet(GREEN_BTN_STYLE)
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
            "label": str(self.elem.get("label", "")),
            "value": self.edit_val.text().strip(),
            "type_desc": str(self.elem.get("type_desc", "基础文本")),
        }
        if self.elem_type == "brand_logo":
            res["asset_path"] = self.edit_logo.text().strip()
        return res


class DateEditDialog(QDialog):
    """日期双击编辑弹窗（自由选择 / 默认当天 - 大尺寸舒服触控版）"""

    def __init__(self, elem, parent=None):
        super().__init__(parent)
        self.elem = elem
        self.setWindowTitle("✏️ 编辑生产日期")
        self.resize(520, 260)
        self.setStyleSheet(TOUCH_STYLE)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        lbl_title = QLabel("编辑生产日期（自由点选日历或一键设为默认当天）：")
        lbl_title.setStyleSheet("font-weight: bold; font-size: 16px; color: #1E395B;")
        layout.addWidget(lbl_title)

        cur_val = str(self.elem.get("value", "")).strip()

        hbox_date = QHBoxLayout()
        hbox_date.setSpacing(12)
        lbl_date = QLabel("生产日期:")
        lbl_date.setStyleSheet("font-size: 16px; font-weight: bold; color: #334155;")
        self.date_picker = QtWidgets.QDateEdit()
        self.date_picker.setCalendarPopup(True)
        self.date_picker.setDisplayFormat("yyyy.MM.dd")
        self.date_picker.setStyleSheet(
            "QDateEdit { border: 2px solid #CBD5E1; border-radius: 8px; padding: 8px 14px; font-size: 18px; font-weight: bold; color: #0F172A; min-height: 48px; background: #FFFFFF; } "
            "QDateEdit:focus { border: 2px solid #2563EB; } "
            "QDateEdit::drop-down { subcontrol-origin: padding; subcontrol-position: top right; width: 44px; border-left: 1px solid #CBD5E1; border-top-right-radius: 8px; border-bottom-right-radius: 8px; background: #F8FAFC; } "
            "QDateEdit::drop-down:hover { background: #EFF6FF; } "
            "QDateEdit::down-arrow { width: 0px; height: 0px; border-left: 7px solid transparent; border-right: 7px solid transparent; border-top: 9px solid #334155; }"
        )

        cal = self.date_picker.calendarWidget()
        if cal:
            cal.setMinimumSize(460, 350)
            cal.setStyleSheet(
                "QCalendarWidget { background-color: #FFFFFF; font-size: 16px; } "
                "QCalendarWidget QWidget#qt_calendar_navigationbar { background-color: #2563EB; min-height: 48px; } "
                "QCalendarWidget QToolButton { font-size: 16px; font-weight: bold; color: #FFFFFF; background-color: transparent; height: 36px; icon-size: 24px; border: none; border-radius: 4px; padding: 0px 8px; } "
                "QCalendarWidget QToolButton:hover { background-color: #1D4ED8; } "
                "QCalendarWidget QToolButton::menu-indicator { image: none; } "
                "QCalendarWidget QSpinBox { font-size: 16px; font-weight: bold; color: #0F172A; background: #FFFFFF; min-height: 34px; border-radius: 4px; padding: 2px; } "
                "QCalendarWidget QAbstractItemView:enabled { font-size: 16px; font-weight: bold; color: #0F172A; selection-background-color: #2563EB; selection-color: #FFFFFF; gridline-color: #E2E8F0; } "
                "QCalendarWidget QTableView { selection-background-color: #2563EB; selection-color: #FFFFFF; font-size: 16px; }"
            )

        try:
            if cur_val and cur_val not in ("默认当天", "日期", "自由选择/默认当天"):
                clean_d = cur_val.replace("-", ".").replace("/", ".")
                parts = [int(p) for p in clean_d.split(".") if p.isdigit()]
                if len(parts) == 3:
                    qd = QtCore.QDate(parts[0], parts[1], parts[2])
                    if qd.isValid():
                        self.date_picker.setDate(qd)
                    else:
                        self.date_picker.setDate(QtCore.QDate.currentDate())
                else:
                    self.date_picker.setDate(QtCore.QDate.currentDate())
            else:
                self.date_picker.setDate(QtCore.QDate.currentDate())
        except Exception:
            self.date_picker.setDate(QtCore.QDate.currentDate())

        btn_today = QPushButton("📅 默认当天")
        btn_today.setStyleSheet(
            "QPushButton { background: #FFFFFF; border: 2px solid #2563EB; border-radius: 8px; font-weight: bold; font-size: 16px; color: #2563EB; padding: 8px 20px; min-height: 48px; } "
            "QPushButton:hover { background: #EFF6FF; border-color: #1D4ED8; } "
            "QPushButton:pressed { background: #DBEAFE; }"
        )
        btn_today.clicked.connect(lambda: self.date_picker.setDate(QtCore.QDate.currentDate()))

        hbox_date.addWidget(lbl_date)
        hbox_date.addWidget(self.date_picker, stretch=1)
        hbox_date.addWidget(btn_today)
        layout.addLayout(hbox_date)

        btn_box = QHBoxLayout()
        btn_box.setSpacing(14)
        btn_ok = QPushButton("确认修改")
        btn_ok.setStyleSheet(
            "QPushButton { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #34D399, stop:1 #059669); border: 1px solid #047857; border-radius: 8px; font-weight: bold; font-size: 17px; color: #FFFFFF; padding: 8px 28px; min-height: 48px; } "
            "QPushButton:hover { background: #10B981; } "
            "QPushButton:pressed { background: #047857; }"
        )
        btn_ok.clicked.connect(self.accept)

        btn_cancel = QPushButton("取消")
        btn_cancel.setStyleSheet(
            "QPushButton { background: #FFFFFF; border: 1px solid #CBD5E1; border-radius: 8px; font-weight: bold; font-size: 16px; color: #334155; padding: 8px 22px; min-height: 48px; } "
            "QPushButton:hover { background: #F8FAFC; }"
        )
        btn_cancel.clicked.connect(self.reject)

        btn_box.addWidget(btn_ok)
        btn_box.addWidget(btn_cancel)
        layout.addLayout(btn_box)

    def get_data(self):
        selected_qdate = self.date_picker.date()
        return {
            "value": selected_qdate.toString("yyyy.MM.dd")
        }


class PrintPreviewDialog(QDialog):
    """打印效果可视化预览弹窗 (全真排版效果预览)"""

    elements_changed = Signal(object)

    def __init__(self, elements, width_mm=140.0, height_mm=120.0, preview_data=None, parent=None):
        super().__init__(parent)
        self.width_mm = width_mm
        self.height_mm = height_mm
        self.setWindowTitle(f"🏷️ 打印效果预览 ({width_mm:.0f}x{height_mm:.0f}mm)")
        self.setWindowFlags(Qt.Dialog | Qt.WindowStaysOnTopHint)
        self.setWindowModality(Qt.ApplicationModal)
        self.resize(680, 480)
        self.setStyleSheet(TOUCH_STYLE)
        self.elements = copy.deepcopy(elements or [])
        self.preview_data = dict(preview_data or {})
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)

        info_lbl = QLabel(f"全真排版效果预览图 ({self.width_mm:.0f}mm x {self.height_mm:.0f}mm)：")
        info_lbl.setStyleSheet("font-weight: bold; font-size: 15px; color: #1E395B;")
        layout.addWidget(info_lbl)

        self.lbl_preview_canvas = InteractivePreviewLabel()
        self.lbl_preview_canvas.setAlignment(Qt.AlignCenter)
        self.lbl_preview_canvas.setMinimumSize(640, 360)
        self.lbl_preview_canvas.setStyleSheet("border: 1px solid #CBD5E1; background-color: #FFFFFF; border-radius: 8px;")
        self.lbl_preview_canvas.double_clicked_signal.connect(self.on_preview_canvas_double_clicked)
        layout.addWidget(self.lbl_preview_canvas, stretch=1)

        btn_close = QPushButton("关闭预览")
        btn_close.setFixedWidth(140)
        btn_close.setStyleSheet(GREEN_BTN_STYLE)
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
                TouchMessageBox.information(self, "提示", "【灰底序号】为系统核心固定字段 (非手动可编辑)。\n【蓝底序号】为可双击编辑字段！")
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
        if not hasattr(self, "lbl_preview_canvas"):
            return
        pix = render_label_preview_pixmap(
            self.elements,
            self.width_mm,
            self.height_mm,
            self.preview_data,
            max_canvas_w=640,
            max_canvas_h=360,
        )
        self.lbl_preview_canvas.setPixmap(pix)
        self.lbl_preview_canvas.update()

def render_label_preview_pixmap(elements, width_mm, height_mm, preview_data=None, max_canvas_w=560, max_canvas_h=320):
    """通用标签画板渲染函数 (生成高保真 QPixmap 效果图)"""
    aspect = width_mm / max(1.0, height_mm)

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

    scale_x = width_px / max(1.0, width_mm)
    scale_y = height_px / max(1.0, height_mm)

    merged_data = {
        elem.get("type"): elem.get("value", "")
        for elem in elements
        if elem.get("type")
    }
    if isinstance(preview_data, dict):
        merged_data.update(preview_data)

    if not merged_data.get("barcode"):
        try:
            from page.config import CONFIG_DATA
            latest_case = CONFIG_DATA.get("caseCode")
            if latest_case and str(latest_case).strip():
                merged_data["barcode"] = str(latest_case).strip()
            else:
                merged_data["barcode"] = "0123456789130"
        except Exception:
            merged_data["barcode"] = "0123456789130"

    seq_idx = 0
    placed_badge_rects = []
    for elem in elements:
        elem_type = elem.get("type")
        if elem_type in ("box_count", "box_unit"):
            box_spec_elem = next((item for item in elements if item.get("type") == "box_spec"), {})
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
            code = str(merged_data.get("barcode") or "0123456789130").strip()
            try:
                from rfid_printer.win_driver_printer import encode_code128_b_pattern
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
                    if i % 2 == 0:
                        painter.drawRect(QRectF(curr_x, y, mod_width, bars_h_px))
                    curr_x += mod_width

                font_code = QFont("Arial", max(9, int(3.2 * scale_y)), QFont.Bold)
                painter.setFont(font_code)
                painter.setPen(QPen(QColor(0, 0, 0)))
                painter.drawText(QRectF(x, y + bars_h_px, w, text_h_px), Qt.AlignCenter | Qt.AlignVCenter, code)
            except Exception:
                pass
        else:
            text_str = render_text(elem, merged_data)
            if text_str:
                font = QFont(str(elem.get("font_name", "SimSun")))
                font_size_pt = float(elem.get("font_size", 10.0))
                px_size = max(8, int(font_size_pt * 25.4 / 72.0 * scale_y))
                font.setPixelSize(px_size)
                font.setBold(bool(elem.get("bold", False)))

                fm = QFontMetrics(font)
                text_w = fm.horizontalAdvance(text_str)
                if text_w > w and w > 0:
                    scaled_size = max(6, int(px_size * (w / text_w)))
                    font.setPixelSize(scaled_size)

                painter.setFont(font)
                painter.setPen(QPen(color))
                alignment = Qt.AlignLeft | Qt.AlignVCenter
                if elem_type in ("produce_date_label", "produce_date"):
                    alignment = Qt.AlignRight | Qt.AlignVCenter
                painter.drawText(QRectF(x, y, w, h), alignment, text_str)

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

        if elem_type in ("produce_date", "produce_date_label"):
            cur_bx = max(2.0, min(width_px - bw_size - 2.0, x + w - bw_size))
            cur_by = min(height_px - bh_size - 2.0, y + h + 2.0)
        elif elem_type == "box_unit":
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
    return pix


class PrintTemplateDialog(QDialog):
    """本地化打印模板管理对话框 (1120x640 双栏宽屏窗口，内置实时排版效果预览)"""

    elements_changed = Signal(object)

    def __init__(self, config_path="config/settings.json", preview_data=None, parent=None):
        super().__init__(parent)
        self.config_path = os.path.abspath(config_path)
        self.setWindowTitle("🏷️ 打印模板管理与双栏实时预览")
        self.resize(1120, 640)
        self.setStyleSheet(TOUCH_STYLE)
        self.setWindowModality(Qt.WindowModal)

        self.elements = []
        self.label_width_mm = 210.0
        self.label_height_mm = 100.0
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
        self.label_width_mm = float(label_cfg.get("width_mm", 210.0))
        self.label_height_mm = float(label_cfg.get("height_mm", 100.0))

        saved_preview = data.get("preview_data", {})
        if isinstance(saved_preview, dict) and saved_preview:
            for k, v in saved_preview.items():
                if v or k not in self.preview_data:
                    self.preview_data[k] = v

        self.elements = resolve_layout_elements(
            data.get("layout", {}),
            self.label_width_mm,
            self.label_height_mm,
        )

    def init_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(12)

        # ------------------ 左侧：字段管理面板 (宽 520px) ------------------
        left_frame = QtWidgets.QFrame()
        left_frame.setStyleSheet("QFrame { background-color: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; }")
        left_layout = QVBoxLayout(left_frame)
        left_layout.setContentsMargins(10, 10, 10, 10)
        left_layout.setSpacing(8)

        # 1. 顶部操作栏
        top_bar = QHBoxLayout()
        self.btn_size_dialog = QPushButton(f"🏷️ 纸张: {self.label_width_mm:.0f}x{self.label_height_mm:.0f}mm")
        self.btn_size_dialog.setStyleSheet(BLUE_BTN_STYLE)
        self.btn_size_dialog.clicked.connect(self.on_open_size_dialog)
        top_bar.addWidget(self.btn_size_dialog)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 搜索字段...")
        self.search_input.setClearButtonEnabled(True)
        self.search_input.setFixedWidth(160)
        self.search_input.textChanged.connect(self.apply_filter_search)
        top_bar.addWidget(self.search_input)

        self.combo_filter = QComboBox()
        self.combo_filter.addItems(["全部字段", "仅看已勾选", "仅看未勾选", "基础文本", "真实箱码条形码"])
        self.combo_filter.setFixedWidth(110)
        self.combo_filter.currentIndexChanged.connect(self.apply_filter_search)
        top_bar.addWidget(self.combo_filter)

        self.btn_select_all = QPushButton("☑️ 全选")
        self.btn_select_all.setStyleSheet(NATIVE_BTN_STYLE)
        self.btn_select_all.clicked.connect(self.on_select_all)
        top_bar.addWidget(self.btn_select_all)

        self.btn_deselect_all = QPushButton("🔳 反选")
        self.btn_deselect_all.setStyleSheet(NATIVE_BTN_STYLE)
        self.btn_deselect_all.clicked.connect(self.on_deselect_all)
        top_bar.addWidget(self.btn_deselect_all)

        left_layout.addLayout(top_bar)

        # 2. 字段表格
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["序号", "勾选", "字段内容 (双击编辑)", "类型说明"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        self.table.setColumnWidth(0, 50)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Fixed)
        self.table.setColumnWidth(1, 65)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.verticalHeader().setDefaultSectionSize(42)
        self.table.itemDoubleClicked.connect(self.on_table_double_clicked)
        left_layout.addWidget(self.table)

        # 3. 字段操作按钮栏
        field_btn_bar = QHBoxLayout()
        self.btn_add = QPushButton("➕ 新增字段")
        self.btn_add.setStyleSheet(NATIVE_BTN_STYLE)
        self.btn_add.clicked.connect(self.on_add_field)
        field_btn_bar.addWidget(self.btn_add)

        self.btn_edit = QPushButton("✏️ 编辑内容")
        self.btn_edit.setStyleSheet(NATIVE_BTN_STYLE)
        field_btn_bar.addWidget(self.btn_edit)

        self.btn_delete = QPushButton("🗑️ 删除勾选")
        self.btn_delete.setStyleSheet(NATIVE_BTN_STYLE)
        self.btn_delete.clicked.connect(self.on_delete_checked_fields)
        field_btn_bar.addWidget(self.btn_delete)
        left_layout.addLayout(field_btn_bar)

        main_layout.addWidget(left_frame, stretch=5)

        # ------------------ 右侧：内置 100% 实时渲染预览面板 (宽 580px) ------------------
        right_frame = QtWidgets.QFrame()
        right_frame.setStyleSheet("QFrame { background-color: #FFFFFF; border: 1px solid #CBD5E1; border-radius: 8px; }")
        right_layout = QVBoxLayout(right_frame)
        right_layout.setContentsMargins(10, 10, 10, 10)
        right_layout.setSpacing(8)

        self.lbl_preview_title = QLabel(f"🏷️ 实时渲染排版效果预览 ({self.label_width_mm:.0f}mm x {self.label_height_mm:.0f}mm)：")
        self.lbl_preview_title.setStyleSheet("font-weight: bold; font-size: 15px; color: #1E395B;")
        right_layout.addWidget(self.lbl_preview_title)

        self.embedded_preview_canvas = InteractivePreviewLabel()
        self.embedded_preview_canvas.setAlignment(Qt.AlignCenter)
        self.embedded_preview_canvas.setMinimumSize(520, 320)
        self.embedded_preview_canvas.setStyleSheet("border: 1px dashed #94A3B8; background-color: #FAFAFA; border-radius: 6px;")
        self.embedded_preview_canvas.double_clicked_signal.connect(self.on_embedded_preview_double_clicked)
        right_layout.addWidget(self.embedded_preview_canvas, stretch=1)

        bottom_btn_bar = QHBoxLayout()
        self.btn_preview = QPushButton("👁️ 全屏放大预览")
        self.btn_preview.setStyleSheet(GREEN_BTN_STYLE)
        self.btn_preview.clicked.connect(self.on_preview_clicked)
        bottom_btn_bar.addWidget(self.btn_preview)

        bottom_btn_bar.addStretch()

        self.btn_save = QPushButton("💾 保存配置并应用")
        self.btn_save.setStyleSheet(BLUE_BTN_STYLE)
        self.btn_save.clicked.connect(self.on_save_and_close)
        bottom_btn_bar.addWidget(self.btn_save)

        self.btn_cancel = QPushButton("取消")
        self.btn_cancel.setStyleSheet(NATIVE_BTN_STYLE)
        self.btn_cancel.clicked.connect(self.reject)
        bottom_btn_bar.addWidget(self.btn_cancel)

        right_layout.addLayout(bottom_btn_bar)
        main_layout.addWidget(right_frame, stretch=6)

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
        self.update_embedded_preview()

    def update_embedded_preview(self):
        if not hasattr(self, "embedded_preview_canvas"):
            return
        pix = render_label_preview_pixmap(
            self.elements,
            self.label_width_mm,
            self.label_height_mm,
            self.preview_data,
            max_canvas_w=540,
            max_canvas_h=320,
        )
        self.lbl_preview_title.setText(f"🏷️ 实时渲染排版效果预览 ({self.label_width_mm:.0f}mm x {self.label_height_mm:.0f}mm)：")
        self.embedded_preview_canvas.setPixmap(pix)
        self.embedded_preview_canvas.update()

    def on_embedded_preview_double_clicked(self, rel_x, rel_y):
        self.on_preview_clicked()

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

        self.update_embedded_preview()

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
            TouchMessageBox.warning(self, "提示", "请先点击选中表格中要编辑的一行！")
            return
        self.edit_row_by_dialog(row)

    def edit_row_by_dialog(self, row):
        content_item = self.table.item(row, 2)
        elem_type = str(content_item.data(Qt.UserRole) or "") if content_item else ""
        elem = next((item for item in self.elements if item.get("type") == elem_type), {})
        if elem_type in ("barcode", "divider", "product_caption"):
            TouchMessageBox.information(self, "提示", "这是基础核心绘制图层，参数固定不可编辑。")
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
            TouchMessageBox.information(self, "提示", "请先在表格第二列勾选要删除的自定义/可选字段！\n（固定核心图层不可删除）")
            return

        reply = TouchMessageBox.question(self, "确认删除", f"确定要删除勾选的 {len(checked_rows)} 个字段吗？", [("确定", "yes"), ("取消", "no")])
        if reply == "yes":
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
        dlg.setWindowFlags(Qt.Dialog | Qt.WindowStaysOnTopHint)
        dlg.setWindowModality(Qt.ApplicationModal)
        dlg.elements_changed.connect(self._on_preview_elements_changed)
        dlg.show()
        dlg.raise_()
        dlg.activateWindow()
        dlg.exec_()

    def set_preview_data(self, preview_data=None):
        if isinstance(preview_data, dict):
            for k, v in preview_data.items():
                if v or k not in self.preview_data:
                    self.preview_data[k] = v
            self.populate_table()

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
        dlg.setWindowFlags(Qt.Dialog | Qt.WindowStaysOnTopHint)
        dlg.setWindowModality(Qt.ApplicationModal)
        dlg.elements_changed.connect(self._on_preview_elements_changed)
        dlg.show()
        dlg.raise_()
        dlg.activateWindow()
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
        TouchMessageBox.information(self, "保存成功", "【打印模板保存成功】\n打纸时将严格按照您输入的尺寸与勾选字段进行 100% 动态排版打印！")
        self.accept()

    def save_elements_config(self):
        data = {}
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception:
                pass
        label_cfg = data.get("label", {})
        label_cfg["width_mm"] = self.label_width_mm
        label_cfg["height_mm"] = self.label_height_mm
        data["label"] = label_cfg
        data["elements"] = copy.deepcopy(self.elements)
        if "layout" not in data or not isinstance(data["layout"], dict):
            data["layout"] = {}
        data["layout"]["elements"] = copy.deepcopy(self.elements)
        data["preview_data"] = copy.deepcopy(self.preview_data)
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logging.info("打印模板元素及预览数据已成功持久化写入 settings.json！")
        except Exception as e:
            logger.error(f"保存模板配置失败: {e}")
