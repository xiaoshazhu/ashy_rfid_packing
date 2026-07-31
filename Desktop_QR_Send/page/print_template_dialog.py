"""
本地化打印模板管理与复选框勾选控制对话框 (PrintTemplateDialog)
具备飞书多维表格风格的 🔍 模糊搜索 与 🌪️ 字段筛选条件
支持 100% 互不遮挡的动态排版与可编辑类型说明列
"""

import os
import json
import logging
from datetime import datetime
from PySide6 import QtCore, QtWidgets, QtGui
from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QPixmap, QPainter, QColor, QFont, QPen
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, QTableWidgetItem,
    QPushButton, QHeaderView, QCheckBox, QMessageBox, QInputDialog, QLineEdit,
    QDoubleSpinBox, QComboBox
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

NATIVE_BTN_STYLE = (
    "QPushButton { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #F8F8F8, stop:1 #E0E0E0); "
    "border: 1px solid #707070; border-radius: 2px; font-weight: bold; color: #000; padding: 4px 10px; } "
    "QPushButton:hover { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #FFFFFF, stop:1 #D8D8D8); border-color: #505050; } "
    "QPushButton:pressed { background: #D0D0D0; border-color: #404040; }"
)


class PrintPreviewDialog(QDialog):
    """打印效果可视化预览弹窗 (支持动态自动避让排版，确保 100% 互不遮挡)"""

    def __init__(self, elements, width_mm=100.0, height_mm=80.0, preview_data=None, parent=None):
        super().__init__(parent)
        self.width_mm = width_mm
        self.height_mm = height_mm
        self.setWindowTitle(f"🏷️ 标签纸排版打印效果预览 ({width_mm:.0f}mm x {height_mm:.0f}mm)")
        self.resize(540, 460)
        self.elements = elements
        self.preview_data = dict(preview_data or {})
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        info_lbl = QLabel(f"页面排版全真效果图（画面纵横比已自动适配：{self.width_mm:.0f}mm x {self.height_mm:.0f}mm）：")
        info_lbl.setStyleSheet("font-weight: bold; color: #2B579A;")
        layout.addWidget(info_lbl)

        self.preview_lbl = QLabel()
        self.preview_lbl.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.preview_lbl)

        btn_close = QPushButton("关闭预览")
        btn_close.setFixedWidth(100)
        btn_close.setStyleSheet(NATIVE_BTN_STYLE)
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close, alignment=Qt.AlignCenter)

        self.render_preview()

    def render_preview(self):
        """按毫米坐标绘制与实际打印一致的固定版式预览。"""
        max_canvas_w, max_canvas_h = 460, 340
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

        # 绘制纸张外边框
        pen_border = QPen(QColor(160, 160, 160), 2)
        painter.setPen(pen_border)
        painter.drawRect(1, 1, width_px - 2, height_px - 2)

        scale_x = width_px / max(1.0, self.width_mm)
        scale_y = height_px / max(1.0, self.height_mm)

        # 可编辑字段使用弹窗当前值，真实扫码箱码和当天日期由外部预览数据覆盖。
        preview_data = {
            elem.get("type"): elem.get("value", "")
            for elem in self.elements
            if elem.get("type")
        }
        preview_data.update(self.preview_data)
        preview_data.setdefault("produce_date", datetime.now().strftime("%Y.%m.%d"))

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

            x = float(elem.get("x", 0.0)) * scale_x
            y = float(elem.get("y", 0.0)) * scale_y
            w = float(elem.get("w", 0.0)) * scale_x
            h = float(elem.get("h", 0.0)) * scale_y
            color = QColor(str(elem.get("color", "#000000")))

            if elem_type == "divider":
                pen = QPen(color, max(1, int(elem.get("line_width", 1))))
                painter.setPen(pen)
                painter.drawLine(int(x), int(y), int(x + w), int(y))
                continue

            if elem_type == "brand_logo":
                logo = QPixmap(resolve_asset_path(str(elem.get("asset_path") or elem.get("value") or "")))
                if not logo.isNull():
                    painter.drawPixmap(QRectF(x, y, w, h), logo, QRectF(logo.rect()))
                continue

            if elem_type == "barcode":
                code = str(preview_data.get("barcode") or elem.get("value") or "")
                text_height = max(10, int(3.4 * scale_y))
                bars_bottom = int(y + h - text_height)
                painter.setPen(Qt.NoPen)
                painter.setBrush(QColor(0, 0, 0))
                # 按 2/3/4 像素宽度循环绘制预览条，实际打印由 SDK 生成 Code 128。
                bx = int(x)
                index = 0
                widths = (2, 1, 3, 1, 2, 2, 1, 4)
                while bx < int(x + w):
                    bar_w = max(1, int(widths[index % len(widths)] * scale_x / 2.5))
                    if index % 2 == 0:
                        painter.drawRect(bx, int(y), min(bar_w, int(x + w) - bx), max(1, bars_bottom - int(y)))
                    bx += bar_w
                    index += 1
                font_code = QFont("Arial")
                font_code.setPixelSize(max(8, int(2.8 * scale_y)))
                painter.setFont(font_code)
                painter.setPen(QPen(QColor(0, 0, 0)))
                painter.drawText(QRectF(x, bars_bottom, w, text_height), Qt.AlignCenter, code)
                continue

            text_str = render_text(elem, preview_data)
            if not text_str:
                continue
            font = QFont(str(elem.get("font_name", "Microsoft YaHei")))
            font_size_pt = float(elem.get("font_size", 8.0))
            font.setPixelSize(max(6, int(font_size_pt * 25.4 / 72.0 * scale_y)))
            font.setBold(bool(elem.get("bold", False)))
            painter.setFont(font)
            painter.setPen(QPen(color))
            alignment = Qt.AlignLeft | Qt.AlignVCenter
            if elem_type in ("produce_date_label", "produce_date"):
                alignment = Qt.AlignCenter
            painter.drawText(QRectF(x, y, w, h), alignment, text_str)

        painter.end()
        self.preview_lbl.setPixmap(pix)


class PrintTemplateDialog(QDialog):
    """本地化打印模板管理对话框 (飞书多维表格风格：支持 🔍 模糊搜索 与 🌪️ 可编辑类型说明)"""

    def __init__(self, config_path="config/settings.json", preview_data=None, parent=None):
        super().__init__(parent)
        self.config_path = os.path.abspath(config_path)
        self.setWindowTitle("打印模板管理 (飞书表格风格与搜索筛选)")
        self.resize(780, 540)
        self.setWindowModality(Qt.WindowModal)

        self.elements = []
        self.label_width_mm = 100.0
        self.label_height_mm = 80.0
        self.preview_data = dict(preview_data or {})
        self.load_elements_config()
        self.init_ui()
        self.populate_table()

    def load_elements_config(self):
        """从本地 json 配置文件读取模板列表与纸张长宽"""
        data = {}
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception as e:
                logger.error(f"读取模板配置失败: {e}")

        label_cfg = data.get("label", {})
        self.label_width_mm = float(label_cfg.get("width_mm", 100.0))
        self.label_height_mm = float(label_cfg.get("height_mm", 80.0))
        self.loaded_profile = profile_name_for_size(
            self.label_width_mm, self.label_height_mm
        )
        self.elements = resolve_layout_elements(
            data.get("layout", {}),
            self.label_width_mm,
            self.label_height_mm,
        )
        if hasattr(self, "spin_width"):
            self.spin_width.setValue(self.label_width_mm)
            self.spin_height.setValue(self.label_height_mm)

    def set_preview_data(self, preview_data=None):
        """设置来自本次真实扫码的临时预览数据，不保存到配置或数据库。"""
        self.preview_data = dict(preview_data or {})
        if hasattr(self, "table"):
            self.populate_table()

    def show_preview_dialog(self, elements=None, parent=None):
        """显示内存预览；不保存配置，不连接打印机、RFID或数据库。"""
        box_code = str(self.preview_data.get("barcode", "")).strip()
        if not box_code:
            QMessageBox.warning(
                parent or self,
                "无法预览",
                "尚未取得相机真实识别箱码，请先触发相机完成真实识别。",
            )
            return False

        self.preview_data["barcode"] = box_code
        preview_dlg = PrintPreviewDialog(
            elements or self.elements,
            width_mm=self.spin_width.value() if hasattr(self, "spin_width") else self.label_width_mm,
            height_mm=self.spin_height.value() if hasattr(self, "spin_height") else self.label_height_mm,
            preview_data=self.preview_data,
            parent=parent or self,
        )
        preview_dlg.exec_()
        return True

    def save_elements_config(self):
        """保存配置及长宽尺寸到本地 settings.json"""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception:
                data = {}
        else:
            data = {}

        if "label" not in data:
            data["label"] = {}
        data["label"]["width_mm"] = self.spin_width.value()
        data["label"]["height_mm"] = self.spin_height.value()

        if "layout" not in data:
            data["layout"] = {}
        target_profile = profile_name_for_size(
            self.spin_width.value(), self.spin_height.value()
        )
        if target_profile != getattr(self, "loaded_profile", target_profile):
            self.elements = resolve_layout_elements(
                {
                    "template_id": TEMPLATE_ID,
                    "profile": getattr(self, "loaded_profile", target_profile),
                    "elements": self.elements,
                },
                self.spin_width.value(),
                self.spin_height.value(),
            )
        data["layout"]["template_id"] = TEMPLATE_ID
        data["layout"]["profile"] = target_profile
        data["layout"]["elements"] = self.elements

        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info("已成功保存打印模板及纸张长宽至本地 settings.json")
        except Exception as e:
            logger.error(f"保存打印模板失败: {e}")

    def init_ui(self):
        main_layout = QVBoxLayout(self)

        # 1. 飞书多维表格风格工具栏 (尺寸设置 + 🔍 模糊搜索 + 🌪️ 筛选条件)
        filter_bar = QHBoxLayout()

        lbl_size_title = QLabel("📏 标签尺寸:")
        lbl_size_title.setStyleSheet("font-weight: bold; color: #2B579A;")
        filter_bar.addWidget(lbl_size_title)

        filter_bar.addWidget(QLabel("宽(mm):"))
        self.spin_width = QDoubleSpinBox()
        self.spin_width.setRange(10.0, 300.0)
        self.spin_width.setValue(self.label_width_mm)
        self.spin_width.setFixedWidth(65)
        filter_bar.addWidget(self.spin_width)

        filter_bar.addWidget(QLabel("高(mm):"))
        self.spin_height = QDoubleSpinBox()
        self.spin_height.setRange(10.0, 300.0)
        self.spin_height.setValue(self.label_height_mm)
        self.spin_height.setFixedWidth(65)
        filter_bar.addWidget(self.spin_height)

        filter_bar.addSpacing(15)

        # 🔍 飞书风格模糊搜索框
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 搜索包含的字段内容...")
        self.search_input.setClearButtonEnabled(True)
        self.search_input.setFixedWidth(160)
        self.search_input.textChanged.connect(self.apply_filter_search)
        filter_bar.addWidget(self.search_input)

        # 🌪️ 飞书风格多维筛选下拉框
        filter_bar.addWidget(QLabel("🌪️ 筛选条件:"))
        self.combo_filter = QComboBox()
        self.combo_filter.addItems(["全部字段", "仅看已勾选", "仅看未勾选", "基础文本", "真实箱码条形码", "自定义扩展"])
        self.combo_filter.setFixedWidth(110)
        self.combo_filter.currentIndexChanged.connect(self.apply_filter_search)
        filter_bar.addWidget(self.combo_filter)

        filter_bar.addStretch()

        self.btn_select_all = QPushButton("☑️ 全选")
        self.btn_select_all.setStyleSheet(NATIVE_BTN_STYLE)
        self.btn_select_all.clicked.connect(self.on_select_all)
        filter_bar.addWidget(self.btn_select_all)

        self.btn_deselect_all = QPushButton("🔳 反选")
        self.btn_deselect_all.setStyleSheet(NATIVE_BTN_STYLE)
        self.btn_deselect_all.clicked.connect(self.on_deselect_all)
        filter_bar.addWidget(self.btn_deselect_all)

        main_layout.addLayout(filter_bar)

        # 2. 表格控件：3 列 (打印勾选, 字段内容, 类型说明【支持自由双击编辑】)
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["打印勾选", "字段内容 (双击编辑，例如：品牌：高原安)", "类型说明 (双击编辑，例如：扫码读取)"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        main_layout.addWidget(self.table)

        # 3. 底部操作栏：新增、编辑、删除勾选了的、打印预览、保存、取消
        btn_box = QHBoxLayout()

        self.btn_add = QPushButton("➕ 新增字段")
        self.btn_add.setStyleSheet(NATIVE_BTN_STYLE)
        self.btn_add.clicked.connect(self.on_add_field)
        btn_box.addWidget(self.btn_add)

        self.btn_edit = QPushButton("✏️ 编辑内容")
        self.btn_edit.setStyleSheet(NATIVE_BTN_STYLE)
        self.btn_edit.clicked.connect(self.on_edit_field)
        btn_box.addWidget(self.btn_edit)

        self.btn_delete_checked = QPushButton("🗑️ 删除勾选了的")
        self.btn_delete_checked.setStyleSheet(NATIVE_BTN_STYLE)
        self.btn_delete_checked.clicked.connect(self.on_delete_checked_fields)
        btn_box.addWidget(self.btn_delete_checked)

        self.btn_preview = QPushButton("👁️ 打印预览")
        self.btn_preview.setStyleSheet(NATIVE_BTN_STYLE)
        self.btn_preview.clicked.connect(self.on_preview_clicked)
        btn_box.addWidget(self.btn_preview)

        btn_box.addStretch()

        self.btn_save = QPushButton("💾 保存配置并应用")
        self.btn_save.setStyleSheet(NATIVE_BTN_STYLE)
        self.btn_save.clicked.connect(self.on_save_and_close)
        btn_box.addWidget(self.btn_save)

        self.btn_cancel = QPushButton("取消")
        self.btn_cancel.setStyleSheet(NATIVE_BTN_STYLE)
        self.btn_cancel.clicked.connect(self.reject)
        btn_box.addWidget(self.btn_cancel)

        main_layout.addLayout(btn_box)

    def populate_table(self):
        self.table.setRowCount(0)
        for elem in self.elements:
            if not is_template_visible(elem):
                continue
            row = self.table.rowCount()
            self.table.insertRow(row)

            # Column 0: 复选框
            chk_widget = QtWidgets.QWidget()
            chk_layout = QHBoxLayout(chk_widget)
            chk_layout.setContentsMargins(0, 0, 0, 0)
            chk_layout.setAlignment(Qt.AlignCenter)
            chk = QCheckBox()
            chk.setChecked(elem.get("enabled", True))

            if is_required_element(elem):
                chk.setEnabled(False)
                chk.setChecked(True)

            chk_layout.addWidget(chk)
            self.table.setCellWidget(row, 0, chk_widget)

            # Column 1: 内容
            label_name = elem.get("label", "")
            val_text = elem.get("value", "")
            if elem.get("type") == "barcode":
                real_code = str(self.preview_data.get("barcode") or "")
                content_str = f"真实识别箱码条形码：{real_code or '等待真实扫码'}"
            elif elem.get("type") == "brand_logo":
                content_str = "高原安品牌图片：图二"
            elif label_name:
                content_str = f"{label_name}：{val_text}"
            else:
                content_str = val_text

            content_item = QTableWidgetItem(content_str)
            content_item.setData(Qt.UserRole, str(elem.get("type", "")))
            if is_required_element(elem):
                content_item.setFlags(content_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, 1, content_item)

            # Column 2: 类型说明 (彻底开放为可编辑单元格，方便用户自由填写备注/读取类型)
            type_desc = elem.get("type_desc", "")
            if not type_desc:
                if elem.get("type") == "barcode":
                    type_desc = "真实识别箱码条形码 (固定项)"
                elif elem.get("type") in ["brand", "product_name", "spec", "box_spec", "shelf_life", "produce_date", "storage", "manufacturer"]:
                    type_desc = "基础文本"
                else:
                    type_desc = "自定义扩展"

            type_item = QTableWidgetItem(type_desc)
            if is_required_element(elem):
                type_item.setFlags(type_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, 2, type_item)

    def apply_filter_search(self):
        """响应飞书多维表格风格的 🔍 模糊搜索 与 🌪️ 筛选条件"""
        query = self.search_input.text().strip().lower()
        filter_mode = self.combo_filter.currentText()

        for row in range(self.table.rowCount()):
            chk_widget = self.table.cellWidget(row, 0)
            chk = chk_widget.findChild(QCheckBox) if chk_widget else None
            is_checked = chk.isChecked() if chk else False

            content_text = self.table.item(row, 1).text().lower()
            type_text = self.table.item(row, 2).text().lower() if self.table.item(row, 2) else ""

            # 1. 匹配文本模糊搜索 (兼顾内容与类型说明)
            matches_search = (not query) or (query in content_text) or (query in type_text)

            # 2. 匹配下拉筛选条件
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

    def collect_elements_from_table(self):
        updated_by_type = {
            str(elem.get("type", "")): dict(elem)
            for elem in self.elements
            if elem.get("type")
        }
        original_order = [str(elem.get("type", "")) for elem in self.elements if elem.get("type")]

        for row in range(self.table.rowCount()):
            chk_widget = self.table.cellWidget(row, 0)
            chk = chk_widget.findChild(QCheckBox) if chk_widget else None
            is_enabled = chk.isChecked() if chk else True

            content_str = self.table.item(row, 1).text().strip()
            type_desc_str = self.table.item(row, 2).text().strip() if self.table.item(row, 2) else ""
            content_item = self.table.item(row, 1)
            elem_type = str(content_item.data(Qt.UserRole) or f"custom_{row}")
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

            # 弹窗界面仍只编辑内容和勾选状态；毫米坐标、字号、粗体、颜色等
            # 设计参数隐藏保留，避免保存一次后破坏箱码设计稿版式。
            new_item = dict(orig)
            new_item.update({
                "type": elem_type,
                "label": label_name,
                "value": val_text,
                "type_desc": type_desc_str,
                "enabled": is_enabled,
            })
            new_item.setdefault("x", 8.0)
            new_item.setdefault("y", 6.0 + row * 5.5)
            new_item.setdefault("w", 84.0)
            new_item.setdefault("h", 5.0)
            new_item.setdefault("font_name", "Microsoft YaHei")
            new_item.setdefault("font_size", 8.0)
            new_item.setdefault("bold", False)
            new_item.setdefault("color", "#000000")
            updated_by_type[elem_type] = new_item

        result = [updated_by_type[item_type] for item_type in original_order if item_type in updated_by_type]
        known = set(original_order)
        result.extend(item for item_type, item in updated_by_type.items() if item_type not in known)
        return result

    def on_select_all(self):
        for row in range(self.table.rowCount()):
            chk_widget = self.table.cellWidget(row, 0)
            chk = chk_widget.findChild(QCheckBox) if chk_widget else None
            if chk and chk.isEnabled():
                chk.setChecked(True)
        self.apply_filter_search()

    def on_deselect_all(self):
        for row in range(self.table.rowCount()):
            chk_widget = self.table.cellWidget(row, 0)
            chk = chk_widget.findChild(QCheckBox) if chk_widget else None
            if chk and chk.isEnabled():
                chk.setChecked(not chk.isChecked())
        self.apply_filter_search()

    def on_add_field(self):
        content_str, ok = QInputDialog.getText(self, "新增打印字段", "请输入新建字段内容 (如：生产批号：20260728-A):")
        if not ok or not content_str.strip():
            return

        type_desc, _ = QInputDialog.getText(self, "新增字段类型说明", "请输入类型说明 (如：扫码读取 / 文本输入):", QLineEdit.Normal, "自定义扩展")

        row_idx = len(self.elements)
        self.elements.append({
            "type": f"custom_{int(QtCore.QDateTime.currentMSecsSinceEpoch())}",
            "label": content_str.strip(),
            "value": "",
            "type_desc": type_desc.strip() if type_desc else "自定义扩展",
            "enabled": True,
            "x": 8.0,
            "y": 6.0 + row_idx * 5.5,
            "w": 84.0,
            "h": 5.0
        })
        self.populate_table()
        self.apply_filter_search()

    def on_edit_field(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "提示", "请先点击选中表格中要编辑的一行！")
            return

        elem_type = str(self.table.item(row, 1).data(Qt.UserRole) or "")
        elem = next((item for item in self.elements if item.get("type") == elem_type), {})
        if is_required_element(elem):
            QMessageBox.information(self, "提示", "这是固定打印板块，不能编辑或取消。")
            return

        curr_content = self.table.item(row, 1).text()
        new_content, ok = QInputDialog.getText(self, "编辑字段内容", "修改字段内容:", QLineEdit.Normal, curr_content)
        if ok and new_content.strip():
            self.table.item(row, 1).setText(new_content.strip())
            self.apply_filter_search()

    def on_delete_checked_fields(self):
        current_elems = self.collect_elements_from_table()
        checked_count = sum(
            1 for e in current_elems
            if is_template_visible(e) and e.get("enabled", True) and not is_required_element(e)
        )
        if checked_count <= 0:
            QMessageBox.warning(self, "提示", "没有被勾选的可删除字段！")
            return

        reply = QMessageBox.question(
            self, "确认删除", f"确定要删除所有被勾选的 {checked_count} 个字段吗？",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            remaining = [
                e for e in current_elems
                if is_required_element(e) or not is_template_visible(e) or not e.get("enabled", True)
            ]
            self.elements = remaining
            self.populate_table()
            self.apply_filter_search()

    def on_preview_clicked(self):
        curr_elems = self.collect_elements_from_table()
        w_mm = self.spin_width.value()
        h_mm = self.spin_height.value()
        preview_elements = resolve_layout_elements(
            {
                "template_id": TEMPLATE_ID,
                "profile": getattr(self, "loaded_profile", profile_name_for_size(w_mm, h_mm)),
                "elements": curr_elems,
            },
            w_mm,
            h_mm,
        )
        self.show_preview_dialog(preview_elements, parent=self)

    def on_save_and_close(self):
        self.elements = self.collect_elements_from_table()
        self.save_elements_config()
        QMessageBox.information(self, "保存成功", "【打印模板保存成功】\n打纸时将严格按照您输入的长宽与勾选字段进行绘制打印！")
        self.accept()
