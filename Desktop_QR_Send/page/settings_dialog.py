"""
统一系统设置中心弹窗 (SystemSettingsDialog)
精简轻量版 (820x560 舒适窗口)：
  1. ⚙️ 参数配置（打印机/串口选择、WS服务器地址、装箱规格、纸张尺寸、ROI裁剪）
  2. 🏷️ 打印模板与实时预览（精简嵌入预览图 520x300，彻底取消全屏巨型弹窗）
  3. 💡 亮度控制与校准（完全集成二分法自动校准进度条与实时采样日志，彻底无子弹窗）
"""

import copy
import json
import logging
import os
from datetime import datetime

try:
    import serial.tools.list_ports
except Exception:
    serial = None

from PySide6.QtPrintSupport import QPrinterInfo
from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtCore import Qt, QRectF, QTimer, Signal
from PySide6.QtGui import QPixmap, QPainter, QColor, QFont, QPen, QFontMetrics
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QLineEdit,
    QPushButton, QComboBox, QGroupBox, QSpinBox, QSlider, QProgressBar,
    QMessageBox, QTabWidget, QWidget, QScrollArea, QFileDialog, QDateEdit
)

from page import config
from page.print_template_dialog import PrintTemplateDialog
from rfid_printer.label_layout import (
    TEMPLATE_ID,
    resolve_asset_path,
    resolve_layout_elements,
    render_text,
)

logger = logging.getLogger("SystemSettingsDialog")

NATIVE_BTN_STYLE = (
    "QPushButton { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #F8F8F8, stop:1 #E0E0E0); "
    "border: 1px solid #707070; border-radius: 5px; font-weight: bold; font-size: 15px; color: #000; padding: 6px 14px; min-height: 38px; } "
    "QPushButton:hover { background: #FFFFFF; } "
    "QPushButton:pressed { background: #D0D0D0; }"
)

INPUT_STYLE = (
    "QLineEdit, QComboBox { border: 1px solid #A0A0A0; border-radius: 4px; "
    "padding: 3px 6px; font-size: 15px; background: #FFFFFF; min-height: 36px; color: #000000; } "
    "QLineEdit:focus, QComboBox:focus { border: 2px solid #2B579A; background: #FAFAFA; }"
)

GROUP_STYLE = (
    "QGroupBox { font-weight: bold; font-size: 15px; color: #1E395B; border: 1px solid #B0B0B0; "
    "border-radius: 6px; margin-top: 8px; padding-top: 12px; background-color: #FFFFFF; } "
    "QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top left; left: 12px; padding: 0 4px; }"
)


class InteractivePreviewLabel(QLabel):
    """支持双击与点击坐标精准命中的内嵌预览图 QLabel 控件"""
    double_clicked = Signal(float, float)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCursor(Qt.PointingHandCursor)

    def _emit_relative_pos(self, event):
        pos = event.position() if hasattr(event, "position") else event.pos()
        px = pos.x()
        py = pos.y()

        w_label = max(1.0, float(self.width()))
        h_label = max(1.0, float(self.height()))

        pm = self.pixmap()
        if pm and not pm.isNull():
            w_pm = float(pm.width())
            h_pm = float(pm.height())
            offset_x = (w_label - w_pm) / 2.0
            offset_y = (h_label - h_pm) / 2.0

            rel_x = (px - offset_x) / max(1.0, w_pm)
            rel_y = (py - offset_y) / max(1.0, h_pm)
        else:
            rel_x = px / w_label
            rel_y = py / h_label

        rel_x = max(0.0, min(1.0, rel_x))
        rel_y = max(0.0, min(1.0, rel_y))
        self.double_clicked.emit(rel_x, rel_y)

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._emit_relative_pos(event)
        super().mouseDoubleClickEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._emit_relative_pos(event)
        super().mousePressEvent(event)


class SystemSettingsDialog(QDialog):
    """主界面顶端【🔑 设置】专属系统管理中心"""

    def __init__(self, home_instance, parent=None):
        super().__init__(parent)
        self.home = home_instance
        self.setWindowTitle("⚙️ 系统功能设置中心")
        self.resize(820, 560)
        self.setStyleSheet("QDialog { background-color: #F4F5F7; }")

        self.form_data = dict(config.CONFIG_DATA or {})
        self.light_controller = getattr(home_instance, "wdip_light_controller", None)
        self.safe_min_v = 8.0
        self.safe_max_v = 12.0
        self.calib_worker = None
        # 设置页、模板字段表、打印预览共用的当前模板副本。
        # 打开模板管理后由 elements_changed 实时更新，避免嵌入预览继续读旧文件。
        self._template_elements = None

        self.init_ui()
        self.load_param_values()
        QTimer.singleShot(0, self.refresh_embedded_preview)

    def showEvent(self, event):
        super().showEvent(event)
        QTimer.singleShot(0, self.refresh_embedded_preview)

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(10)

        # 顶部标题
        top_bar = QHBoxLayout()
        title_lbl = QLabel("🔑 系统功能设置中心")
        title_lbl.setStyleSheet("font-size: 18px; font-weight: bold; color: #1E395B;")
        top_bar.addWidget(title_lbl)
        top_bar.addStretch()
        main_layout.addLayout(top_bar)

        # 3 大选项卡
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet(
            "QTabWidget::pane { border: 1px solid #B0B0B0; background: #FFFFFF; border-radius: 6px; } "
            "QTabBar::tab { background: #E4E7ED; border: 1px solid #B0B0B0; padding: 8px 20px; "
            "font-size: 15px; font-weight: bold; color: #333; margin-right: 4px; border-top-left-radius: 6px; border-top-right-radius: 6px; } "
            "QTabBar::tab:selected { background: #FFFFFF; color: #2B579A; border-bottom-color: #FFFFFF; }"
        )
        self.tab_widget.currentChanged.connect(self.on_tab_changed)

        # 1. 参数配置
        self.tab_params = QWidget()
        self.setup_params_tab()
        self.tab_widget.addTab(self.tab_params, "⚙️ 参数配置")

        # 2. 打印模板与实时预览
        self.tab_template = QWidget()
        self.setup_template_tab()
        self.tab_widget.addTab(self.tab_template, "🏷️ 打印模板与实时预览")

        # 3. 亮度控制与校准
        self.tab_light = QWidget()
        self.setup_light_tab()
        self.tab_widget.addTab(self.tab_light, "💡 亮度控制与校准")

        main_layout.addWidget(self.tab_widget)

    def on_tab_changed(self, index):
        if index == 1:
            self.refresh_embedded_preview()

    def setup_param_tab(self):
        """兼容别名方法，映射至 setup_params_tab"""
        return self.setup_params_tab()

    def setup_params_tab(self):
        layout = QVBoxLayout(self.tab_params)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        group_dev = QGroupBox("硬件设备与服务器接口通信设置")
        group_dev.setStyleSheet(GROUP_STYLE)
        grid_dev = QGridLayout(group_dev)
        grid_dev.setHorizontalSpacing(12)
        grid_dev.setVerticalSpacing(10)

        lbl_prn = QLabel("选择打印机:")
        lbl_prn.setStyleSheet("font-size: 14px; font-weight: bold;")
        self.combobox_printSelect = QComboBox()
        self.combobox_printSelect.setStyleSheet(INPUT_STYLE)

        lbl_com = QLabel("选择串口(RS485):")
        lbl_com.setStyleSheet("font-size: 14px; font-weight: bold;")
        self.combobox_comSelect = QComboBox()
        self.combobox_comSelect.setStyleSheet(INPUT_STYLE)

        lbl_ws = QLabel("设置服务器地址:")
        lbl_ws.setStyleSheet("font-size: 14px; font-weight: bold;")
        self.edit_service = QLineEdit()
        self.edit_service.setStyleSheet(INPUT_STYLE)

        grid_dev.addWidget(lbl_prn, 0, 0)
        grid_dev.addWidget(self.combobox_printSelect, 0, 1)
        grid_dev.addWidget(lbl_com, 0, 2)
        grid_dev.addWidget(self.combobox_comSelect, 0, 3)
        grid_dev.addWidget(lbl_ws, 1, 0)
        grid_dev.addWidget(self.edit_service, 1, 1, 1, 3)

        layout.addWidget(group_dev)

        group_spec = QGroupBox("装箱规格与打印机纸张参数")
        group_spec.setStyleSheet(GROUP_STYLE)
        grid_spec = QGridLayout(group_spec)
        grid_spec.setHorizontalSpacing(12)
        grid_spec.setVerticalSpacing(10)

        lbl_jian = QLabel("一捆数量 (盒):")
        lbl_jian.setStyleSheet("font-size: 14px; font-weight: bold;")
        self.edit_max_jian = QLineEdit()
        self.edit_max_jian.setStyleSheet(INPUT_STYLE)

        lbl_xiang = QLabel("一箱数量 (捆):")
        lbl_xiang.setStyleSheet("font-size: 14px; font-weight: bold;")
        self.edit_max_xiang = QLineEdit()
        self.edit_max_xiang.setStyleSheet(INPUT_STYLE)

        lbl_pw = QLabel("纸张宽度 (mm):")
        lbl_pw.setStyleSheet("font-size: 14px; font-weight: bold;")
        self.edit_paper_width = QLineEdit("150")
        self.edit_paper_width.setStyleSheet(INPUT_STYLE)
        self.edit_paper_width.textChanged.connect(self._on_paper_input_changed)

        lbl_ph = QLabel("纸张高度 (mm):")
        lbl_ph.setStyleSheet("font-size: 14px; font-weight: bold;")
        self.edit_paper_height = QLineEdit("75")
        self.edit_paper_height.setStyleSheet(INPUT_STYLE)
        self.edit_paper_height.textChanged.connect(self._on_paper_input_changed)

        lbl_copies = QLabel("打印数量 (份):")
        lbl_copies.setStyleSheet("font-size: 14px; font-weight: bold;")
        self.sp_print_copies = QSpinBox()
        self.sp_print_copies.setRange(1, 99)
        self.sp_print_copies.setValue(1)
        self.sp_print_copies.setStyleSheet("QSpinBox { font-size: 14px; font-weight: bold; padding: 4px; }")

        grid_spec.addWidget(lbl_jian, 0, 0)
        grid_spec.addWidget(self.edit_max_jian, 0, 1)
        grid_spec.addWidget(lbl_xiang, 0, 2)
        grid_spec.addWidget(self.edit_max_xiang, 0, 3)

        grid_spec.addWidget(lbl_pw, 1, 0)
        grid_spec.addWidget(self.edit_paper_width, 1, 1)
        grid_spec.addWidget(lbl_ph, 1, 2)
        grid_spec.addWidget(self.edit_paper_height, 1, 3)

        grid_spec.addWidget(lbl_copies, 2, 0)
        grid_spec.addWidget(self.sp_print_copies, 2, 1)

        layout.addWidget(group_spec)

        group_crop = QGroupBox("海康相机识别区域 (ROI 裁剪像素)")
        group_crop.setStyleSheet(GROUP_STYLE)
        grid_crop = QGridLayout(group_crop)
        grid_crop.setHorizontalSpacing(12)
        grid_crop.setVerticalSpacing(10)

        lbl_min_x = QLabel("X轴起始:")
        lbl_min_x.setStyleSheet("font-size: 14px; font-weight: bold;")
        self.edit_min_x = QLineEdit()
        self.edit_min_x.setStyleSheet(INPUT_STYLE)

        lbl_max_x = QLabel("X轴截至:")
        lbl_max_x.setStyleSheet("font-size: 14px; font-weight: bold;")
        self.edit_max_x = QLineEdit()
        self.edit_max_x.setStyleSheet(INPUT_STYLE)

        lbl_min_y = QLabel("Y轴起始:")
        lbl_min_y.setStyleSheet("font-size: 14px; font-weight: bold;")
        self.edit_min_y = QLineEdit()
        self.edit_min_y.setStyleSheet(INPUT_STYLE)

        lbl_max_y = QLabel("Y轴截至:")
        lbl_max_y.setStyleSheet("font-size: 14px; font-weight: bold;")
        self.edit_max_y = QLineEdit()
        self.edit_max_y.setStyleSheet(INPUT_STYLE)

        grid_crop.addWidget(lbl_min_x, 0, 0)
        grid_crop.addWidget(self.edit_min_x, 0, 1)
        grid_crop.addWidget(lbl_max_x, 0, 2)
        grid_crop.addWidget(self.edit_max_x, 0, 3)

        grid_crop.addWidget(lbl_min_y, 1, 0)
        grid_crop.addWidget(self.edit_min_y, 1, 1)
        grid_crop.addWidget(lbl_max_y, 1, 2)
        grid_crop.addWidget(self.edit_max_y, 1, 3)

        layout.addWidget(group_crop)

        btn_bar = QHBoxLayout()
        btn_bar.addStretch()

        self.btn_cancel = QPushButton("取消")
        self.btn_cancel.setStyleSheet(NATIVE_BTN_STYLE)
        self.btn_cancel.clicked.connect(self.reject)

        self.btn_save = QPushButton("💾 保存参数配置")
        self.btn_save.setStyleSheet(
            "QPushButton { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #337AB7, stop:1 #2E6DA4); "
            "border: 1px solid #2E6DA4; border-radius: 4px; font-weight: bold; font-size: 15px; color: #FFF; padding: 6px 18px; min-height: 38px; } "
            "QPushButton:hover { background: #286090; }"
        )
        self.btn_save.clicked.connect(self.save_params)

        btn_bar.addWidget(self.btn_cancel)
        btn_bar.addWidget(self.btn_save)
        layout.addLayout(btn_bar)

    def setup_template_tab(self):
        """Tab 2 打印模板：极简无干扰全真排版效果图 (支持在图上直接双击编辑)"""
        layout = QVBoxLayout(self.tab_template)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        group_preview = QGroupBox("全真排版打印效果图（支持直接在图上双击文字或点击 ✏️ 标志实时编辑）")
        group_preview.setStyleSheet(GROUP_STYLE)
        vbox_p = QVBoxLayout(group_preview)
        vbox_p.setContentsMargins(8, 8, 8, 8)

        self.lbl_embedded_preview = InteractivePreviewLabel()
        self.lbl_embedded_preview.setAlignment(Qt.AlignCenter)
        self.lbl_embedded_preview.double_clicked.connect(self._on_preview_double_clicked)
        vbox_p.addWidget(self.lbl_embedded_preview)

        layout.addWidget(group_preview)
        self.refresh_embedded_preview()

    def _get_current_template_elements(self):
        """获取当前有效的模板元素列表，带多级退避保底，确保绝不返回空列表。"""
        if self._template_elements is not None and len(self._template_elements) > 0:
            return copy.deepcopy(self._template_elements)

        config_path = os.path.abspath("config/settings.json")
        if os.path.exists(config_path):
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    cfg_data = json.load(f)
                    if isinstance(cfg_data, dict) and cfg_data.get("elements"):
                        self._template_elements = copy.deepcopy(cfg_data["elements"])
                        return copy.deepcopy(self._template_elements)
            except Exception as e:
                logger.warning(f"读取 settings.json 模板元素失败: {e}")

        from rfid_printer.label_layout import PROFILE_ELEMENTS, PROFILE_150X75, profile_name_for_size
        w_mm = float(self.edit_paper_width.text().strip() if hasattr(self, "edit_paper_width") and self.edit_paper_width.text().strip() else 150.0)
        h_mm = float(self.edit_paper_height.text().strip() if hasattr(self, "edit_paper_height") and self.edit_paper_height.text().strip() else 75.0)
        p_name = profile_name_for_size(w_mm, h_mm)
        self._template_elements = copy.deepcopy(PROFILE_ELEMENTS.get(p_name, PROFILE_ELEMENTS[PROFILE_150X75]))
        return copy.deepcopy(self._template_elements)

    def _save_template_elements_to_config(self, elements):
        """将修改后的模板元素持久化写入 config/settings.json 配置文件，并同步全局 PROFILE_ELEMENTS"""
        try:
            config_path = os.path.abspath("config/settings.json")
            cfg_dict = {}
            if os.path.exists(config_path):
                try:
                    with open(config_path, "r", encoding="utf-8") as f:
                        cfg_dict = json.load(f)
                except Exception:
                    cfg_dict = {}
            
            # 双向同步根节点 elements 与 layout.elements，彻底解决“下次打开恢复原始”问题！
            cfg_dict["elements"] = copy.deepcopy(elements)
            if "layout" not in cfg_dict or not isinstance(cfg_dict["layout"], dict):
                cfg_dict["layout"] = {}
            cfg_dict["layout"]["elements"] = copy.deepcopy(elements)

            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(cfg_dict, f, ensure_ascii=False, indent=2)

            # 同步更新内存缓存，防止切屏恢复
            from rfid_printer import label_layout
            w_mm = float(self.edit_paper_width.text().strip() if hasattr(self, "edit_paper_width") and self.edit_paper_width.text().strip() else 150.0)
            h_mm = float(self.edit_paper_height.text().strip() if hasattr(self, "edit_paper_height") and self.edit_paper_height.text().strip() else 75.0)
            p_name = label_layout.profile_name_for_size(w_mm, h_mm)
            label_layout.PROFILE_ELEMENTS[p_name] = copy.deepcopy(elements)

            logging.info("修改后的排版元素已成功持久化写入 config/settings.json (双路同步)")
        except Exception as exc:
            logger.error(f"持久化保存编辑元素失败: {exc}")

    def _on_preview_double_clicked(self, rel_x, rel_y):
        """用户在内嵌全真预览图上双击或单击 ✏️ 记号时，调起极简单行编辑弹窗"""
        try:
            pix = self.lbl_embedded_preview.pixmap()
            pix_w = float(pix.width()) if pix and not pix.isNull() else 680.0
            pix_h = float(pix.height()) if pix and not pix.isNull() else 380.0

            click_x_px = rel_x * pix_w
            click_y_px = rel_y * pix_h

            hit_elem = None
            # 1. 优先 100% 精准匹配点击的 ✏️ 徽章小图标
            for item in getattr(self, "_embedded_badge_hit_rects", []):
                if item["badge_rect"].contains(click_x_px, click_y_px):
                    hit_elem = item["elem"]
                    break

            # 2. 其次匹配文本区域
            if not hit_elem:
                for item in getattr(self, "_embedded_badge_hit_rects", []):
                    if item["text_rect"].contains(click_x_px, click_y_px):
                        hit_elem = item["elem"]
                        break

            # 3. 距离最近邻捕获
            if not hit_elem:
                best_dist = 99999.0
                for item in getattr(self, "_embedded_badge_hit_rects", []):
                    bc = item["badge_rect"].center()
                    tc = item["text_rect"].center()
                    d = min((click_x_px - bc.x())**2 + (click_y_px - bc.y())**2, (click_x_px - tc.x())**2 + (click_y_px - tc.y())**2)
                    if d < best_dist and d <= 2500.0:
                        best_dist = d
                        hit_elem = item["elem"]

            if hit_elem:
                target_type = hit_elem.get("type")
                elements = self._get_current_template_elements()
                orig_elem = next((e for e in elements if e.get("type") == target_type), hit_elem)
                
                from page.print_template_dialog import EditFieldDialog, DateEditDialog
                if target_type in ("produce_date", "produce_date_label"):
                    date_elem = next((e for e in elements if e.get("type") == "produce_date"), orig_elem)
                    dlg = DateEditDialog(date_elem, parent=self)
                    if dlg.exec_() == QDialog.Accepted:
                        new_data = dlg.get_data()
                        for e in elements:
                            if e.get("type") in ("produce_date", "produce_date_label"):
                                e["value"] = new_data["value"]
                        self._template_elements = copy.deepcopy(elements)
                        self._save_template_elements_to_config(self._template_elements)
                        self.refresh_embedded_preview(self._template_elements)
                else:
                    dlg = EditFieldDialog(orig_elem, parent=self)
                    if dlg.exec_() == QDialog.Accepted:
                        new_data = dlg.get_data()
                        updated_val = new_data.get("value", "").strip()
                        for e in elements:
                            if e.get("type") == target_type:
                                e["value"] = updated_val
                        self._template_elements = copy.deepcopy(elements)
                        self._save_template_elements_to_config(self._template_elements)
                        self.refresh_embedded_preview(self._template_elements)
        except Exception as e:
            logger.error(f"双击预览图编辑元素失败: {e}")

    def refresh_embedded_preview(self, elements=None, width_mm=None, height_mm=None):
        """在页面内部渲染全真排版打印效果图 (带 ✏️ 标志交互编辑)"""
        try:
            self._embedded_badge_hit_rects = []
            if elements is not None:
                self._template_elements = copy.deepcopy(elements)

            config_path = os.path.abspath("config/settings.json")
            data = {}
            if os.path.exists(config_path):
                with open(config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)

            w_mm = 150.0
            h_mm = 75.0
            if hasattr(self, 'edit_paper_width') and self.edit_paper_width.text().strip():
                try:
                    w_mm = float(self.edit_paper_width.text().strip())
                except ValueError:
                    w_mm = 150.0
            if hasattr(self, 'edit_paper_height') and self.edit_paper_height.text().strip():
                try:
                    h_mm = float(self.edit_paper_height.text().strip())
                except ValueError:
                    h_mm = 75.0

            from rfid_printer.label_layout import PROFILE_ELEMENTS, PROFILE_150X75, PROFILE_140X120, resolve_layout_elements, profile_name_for_size
            p_name = profile_name_for_size(w_mm, h_mm)
            if self._template_elements is not None:
                tmpl_elements = copy.deepcopy(self._template_elements)
            else:
                tmpl_elements = copy.deepcopy(PROFILE_ELEMENTS.get(p_name, PROFILE_ELEMENTS[PROFILE_150X75]))

            elements = resolve_layout_elements(
                {"template_id": p_name, "elements": tmpl_elements},
                w_mm,
                h_mm,
            )

            max_w, max_h = 680, 380
            aspect = w_mm / max(1.0, h_mm)
            if aspect >= 1.0:
                width_px = max_w
                height_px = int(max_w / aspect)
            else:
                height_px = max_h
                width_px = int(max_h * aspect)

            pix = QPixmap(width_px, height_px)
            pix.fill(QColor(255, 255, 255))

            painter = QPainter(pix)
            painter.setRenderHint(QPainter.Antialiasing)

            try:
                pen_border = QPen(QColor(160, 160, 160), 2)
                painter.setPen(pen_border)
                painter.drawRect(1, 1, width_px - 2, height_px - 2)

                scale_x = width_px / max(1.0, w_mm)
                scale_y = height_px / max(1.0, h_mm)

                preview_data = {
                    elem.get("type"): elem.get("value", "")
                    for elem in elements
                    if elem.get("type")
                }
                
                # 动态从主界面或配置中心获取最新的13位箱码
                latest_case_code = None
                if hasattr(self, 'home') and getattr(self.home, 'case', None):
                    latest_case_code = str(self.home.case).strip()
                if not latest_case_code:
                    try:
                        from page.config import CONFIG_DATA
                        latest_case_code = CONFIG_DATA.get("caseCode")
                    except Exception:
                        pass
                
                if latest_case_code:
                    preview_data["barcode"] = str(latest_case_code).strip()
                else:
                    preview_data.setdefault("barcode", "1785813377794")

                preview_data.setdefault("produce_date", datetime.now().strftime("%Y.%m.%d"))

                for elem in elements:
                    elem_type = elem.get("type")
                    if elem_type != "barcode" and not elem.get("enabled", True):
                        continue

                    if elem.get("print_direct") is False:
                        continue

                    x = float(elem.get("x", 0.0)) * scale_x
                    y = float(elem.get("y", 0.0)) * scale_y
                    w = float(elem.get("w", 0.0)) * scale_x
                    h = float(elem.get("h", 0.0)) * scale_y
                    color = QColor(str(elem.get("color", "#000000")))

                    if elem_type == "box_unit":
                        box_count_elem = next((e for e in elements if e.get("type") == "box_count"), {})
                        if box_count_elem:
                            bc_str = render_text(box_count_elem, preview_data)
                            bc_font = QFont(str(box_count_elem.get("font_name", "SimSun")))
                            bc_font.setPixelSize(max(10, int(float(box_count_elem.get("font_size", 34.0)) * scale_y * 0.42)))
                            bc_font.setBold(bool(box_count_elem.get("bold", False)))
                            bc_fm = QFontMetrics(bc_font)
                            bc_w = bc_fm.horizontalAdvance(bc_str) if hasattr(bc_fm, "horizontalAdvance") else bc_fm.width(bc_str)
                            bc_x_px = float(box_count_elem.get("x", 6.0)) * scale_x
                            bc_y_px = float(box_count_elem.get("y", 47.0)) * scale_y
                            bc_h_px = float(box_count_elem.get("h", 14.0)) * scale_y
                            x = bc_x_px + bc_w + 6.0
                            y = bc_y_px + bc_h_px - h - 1.0

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
                        code = str(preview_data.get("barcode") or "1785813377794")
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
                            if elem_type == "spec" and "：" in text_str:
                                text_str = "• 产品规格：" + text_str.split("：", 1)[1]
                            elif elem_type == "shelf_life" and "：" in text_str:
                                text_str = "• 保 质 期：" + text_str.split("：", 1)[1]
                            elif elem_type == "storage" and "：" in text_str:
                                text_str = "• 储存条件：" + text_str.split("：", 1)[1]
                            elif elem_type == "manufacturer" and "：" in text_str:
                                text_str = "• 生 产 商：" + text_str.split("：", 1)[1]

                            font = QFont(str(elem.get("font_name", "Microsoft YaHei")))
                            font_size_pt = float(elem.get("font_size", 10.0))
                            font.setPixelSize(max(10, int(font_size_pt * scale_y * 0.42)))

                            font.setBold(bool(elem.get("bold", False)))
                            painter.setFont(font)
                            painter.setPen(QPen(color))
                            alignment = Qt.AlignLeft | Qt.AlignVCenter
                            if elem_type in ("produce_date_label", "produce_date"):
                                alignment = Qt.AlignCenter
                            painter.drawText(QRectF(x, y, w, h), alignment, text_str)

                            # 全平台绝对兼容的 ✏ 蓝底白字高亮区分标志 (100% 1 对 1 对应的精准位移)
                            if elem_type in ("product_name", "spec", "shelf_life", "storage", "manufacturer", "produce_date", "box_count", "box_unit", "box_spec", "unit_net_weight"):
                                try:
                                    fm = QFontMetrics(font)
                                    str_w = fm.horizontalAdvance(text_str) if hasattr(fm, "horizontalAdvance") else fm.width(text_str)
                                    real_str_w = min(str_w, w) if w > 0 else str_w
                                    
                                    bw, bh = 18.0, max(12.0, min(16.0, h))
                                    by = y + (h - bh) / 2.0
                                    badge_x = min(width_px - bw - 4.0, max(x + 10.0, x + real_str_w + 5.0))
                                    if elem_type in ("produce_date", "produce_date_label"):
                                        badge_x = min(width_px - bw - 4.0, x + (w + real_str_w) / 2.0 + 4.0)
                                    elif elem_type == "box_unit":
                                        badge_x = min(width_px - bw - 4.0, x + real_str_w + 6.0)

                                    badge_rect = QRectF(badge_x - 4.0, by - 4.0, bw + 8.0, bh + 8.0)
                                    text_rect = QRectF(x - 2.0, y - 2.0, w + 4.0, h + 4.0)
                                    self._embedded_badge_hit_rects.append({
                                        "elem": elem,
                                        "badge_rect": badge_rect,
                                        "text_rect": text_rect
                                    })
                                    
                                    painter.save()
                                    painter.setPen(QPen(QColor("#1D4ED8"), 1))
                                    painter.setBrush(QColor("#2563EB"))
                                    painter.drawRoundedRect(QRectF(badge_x, by, bw, bh), 3, 3)
                                    
                                    b_font = QFont("Segoe UI Emoji", 8, QFont.Bold)
                                    painter.setFont(b_font)
                                    painter.setPen(QColor("#FFFFFF"))
                                    painter.drawText(QRectF(badge_x, by, bw, bh), Qt.AlignCenter, "✏️")
                                    painter.restore()
                                except Exception:
                                    pass
            finally:
                painter.end()

            self.lbl_embedded_preview.setPixmap(pix)
        except Exception as e:
            logger.error(f"渲染嵌入预览失败: {e}")
            if hasattr(self, "lbl_embedded_preview") and self.lbl_embedded_preview:
                fallback_pix = QPixmap(680, 340)
                fallback_pix.fill(QColor(255, 255, 255))
                self.lbl_embedded_preview.setPixmap(fallback_pix)

    def _on_template_elements_changed(self, elements):
        """接收字段表/打印预览的变更，立即刷新设置页内嵌预览。"""
        self._template_elements = copy.deepcopy(elements or [])
        self.refresh_embedded_preview(self._template_elements)

    def setup_light_tab(self):
        """Tab 3 亮度控制：完全集成二分法自动校准进度条与采样日志，彻底无子弹窗！"""
        layout = QVBoxLayout(self.tab_light)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(14)

        group_manual = QGroupBox("WDIP 物理补光灯手动大滑块调节")
        group_manual.setStyleSheet(GROUP_STYLE)
        vbox_m = QVBoxLayout(group_manual)
        vbox_m.setContentsMargins(14, 14, 14, 14)
        vbox_m.setSpacing(12)

        self.lbl_light_voltage = QLabel("直接控制目标: 0% (8.00V)")
        self.lbl_light_voltage.setStyleSheet("font-size: 16px; font-weight: bold; color: #1E395B;")
        vbox_m.addWidget(self.lbl_light_voltage)

        self.btn_output_toggle = QPushButton("直接开启 8.00V 灯光输出")
        self.btn_output_toggle.setStyleSheet(
            "QPushButton { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #F8F8F8, stop:1 #E0E0E0); "
            "border: 1px solid #707070; border-radius: 4px; font-weight: bold; font-size: 15px; color: #000; min-height: 40px; } "
            "QPushButton:hover { background: #FFFFFF; } "
            "QPushButton:pressed { background: #D0D0D0; }"
        )
        self.btn_output_toggle.clicked.connect(self.on_toggle_light_output)
        vbox_m.addWidget(self.btn_output_toggle)

        self.slider_light = QSlider(Qt.Horizontal)
        self.slider_light.setRange(0, 100)
        self.slider_light.setValue(0)
        self.slider_light.setFixedHeight(44)
        self.slider_light.setStyleSheet(
            "QSlider::groove:horizontal { height: 16px; background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #EBECEF, stop:0.5 #D6D9E0, stop:1 #B8BCC6); border: 1px solid #A0A5B5; border-radius: 8px; } "
            "QSlider::handle:horizontal { width: 36px; height: 36px; margin: -10px 0; border-radius: 18px; "
            "background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #FFFFFF, stop:1 #E5E7EB); border: 2px solid #8B92A0; } "
            "QSlider::handle:horizontal:hover { background: #FFFFFF; border: 2px solid #2B579A; }"
        )
        self.slider_light.valueChanged.connect(self.on_slider_voltage_changed)
        vbox_m.addWidget(self.slider_light)

        layout.addWidget(group_manual)

        group_calib = QGroupBox("二分法真实识别亮度自动校准 (实时进阶检测)")
        group_calib.setStyleSheet(GROUP_STYLE)
        vbox_c = QVBoxLayout(group_calib)
        vbox_c.setContentsMargins(14, 14, 14, 14)
        vbox_c.setSpacing(12)

        # 校准操作按钮栏 (包含开始与取消按钮)
        hbox_calib_btns = QHBoxLayout()
        self.btn_calibrate = QPushButton("⚡ 开始真实二分法亮度自动校准")
        self.btn_calibrate.setStyleSheet(
            "QPushButton { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #F0AD4E, stop:1 #EEA236); "
            "border: 1px solid #EEA236; border-radius: 5px; font-weight: bold; font-size: 16px; color: #FFF; min-height: 44px; } "
            "QPushButton:hover { background: #EC971F; } "
            "QPushButton:pressed { background: #D58512; }"
        )
        self.btn_calibrate.clicked.connect(self.on_start_light_calibrate)
        hbox_calib_btns.addWidget(self.btn_calibrate, stretch=3)

        self.btn_cancel_calib = QPushButton("🛑 停止校准")
        self.btn_cancel_calib.setEnabled(False)
        self.btn_cancel_calib.setStyleSheet(
            "QPushButton { background: #D9534F; border: 1px solid #D43F3A; border-radius: 5px; font-weight: bold; font-size: 16px; color: #FFF; min-height: 44px; } "
            "QPushButton:hover { background: #C9302C; } "
            "QPushButton:disabled { background: #E0E0E0; border-color: #CCCCCC; color: #888888; }"
        )
        self.btn_cancel_calib.clicked.connect(self.on_stop_light_calibrate)
        hbox_calib_btns.addWidget(self.btn_cancel_calib, stretch=1)
        vbox_c.addLayout(hbox_calib_btns)

        # 进度条直观展示 (始终可见，带有绿色高亮进阶百分比)
        self.progress_calib = QProgressBar()
        self.progress_calib.setRange(0, 100)
        self.progress_calib.setValue(0)
        self.progress_calib.setFixedHeight(30)
        self.progress_calib.setStyleSheet(
            "QProgressBar { font-size: 14px; font-weight: bold; border: 1px solid #A0A0A0; border-radius: 6px; text-align: center; background: #E9ECEF; } "
            "QProgressBar::chunk { background-color: #5CB85C; border-radius: 5px; }"
        )
        vbox_c.addWidget(self.progress_calib)

        self.lbl_calib_status = QLabel("状态: 补光灯已就绪。")
        self.lbl_calib_status.setStyleSheet("font-size: 14px; font-weight: bold; color: #1E395B;")
        vbox_c.addWidget(self.lbl_calib_status)

        self.lbl_calib_detail = QLabel("区间二分实测采样日志将在此实时滚动展示...")
        self.lbl_calib_detail.setStyleSheet("font-size: 13px; color: #666666;")
        vbox_c.addWidget(self.lbl_calib_detail)

        layout.addWidget(group_calib)
        layout.addStretch()

    def on_slider_voltage_changed(self, percent):
        voltage = self.safe_min_v + (self.safe_max_v - self.safe_min_v) * (percent / 100.0)
        self.lbl_light_voltage.setText(f"直接控制目标: {percent}% ({voltage:.2f}V)")

    def on_toggle_light_output(self):
        percent = self.slider_light.value()
        voltage = self.safe_min_v + (self.safe_max_v - self.safe_min_v) * (percent / 100.0)
        btn_text = self.btn_output_toggle.text()
        if "开启" in btn_text:
            self.btn_output_toggle.setText(f"直接关闭 {voltage:.2f}V 灯光输出")
            self.lbl_calib_status.setText(f"已直接开启灯光输出: {voltage:.2f}V")
        else:
            self.btn_output_toggle.setText(f"直接开启 {voltage:.2f}V 灯光输出")
            self.lbl_calib_status.setText("已关闭灯光输出。")

    def on_start_light_calibrate(self):
        """点击触发二分法亮度自动校准，实时在 Tab3 更新进度条与采样日志"""
        try:
            from page.light_control_dialog import LightCalibrateWorker
            self.btn_calibrate.setEnabled(False)
            self.btn_cancel_calib.setEnabled(True)
            self.progress_calib.setValue(0)
            self.lbl_calib_status.setText("⚡ 二分法自动校准进行中...")
            self.lbl_calib_detail.setText("正在连接WDIP控制器并开始采集多帧识别图像...")

            self.calib_worker = LightCalibrateWorker(self.home)
            self.calib_worker.sig_progress.connect(self.progress_calib.setValue)
            self.calib_worker.sig_log.connect(self.lbl_calib_detail.setText)
            self.calib_worker.sig_step.connect(self.lbl_calib_status.setText)
            self.calib_worker.sig_finished.connect(self.on_calib_finished)
            self.calib_worker.start()
        except Exception as e:
            logger.error(f"启动二分法校准线程失败: {e}")
            self.btn_calibrate.setEnabled(True)
            self.btn_cancel_calib.setEnabled(False)
            if hasattr(self.home, "on_light_calibrate_clicked"):
                self.home.on_light_calibrate_clicked()
            else:
                QMessageBox.information(self, "亮度校准", "二分法自动校准指令已触发。")

    def on_stop_light_calibrate(self):
        """手动中途停止二分法亮度自动校准。"""
        if hasattr(self, 'calib_worker') and self.calib_worker and self.calib_worker.isRunning():
            try:
                self.calib_worker.requestInterruption()
                self.calib_worker.terminate()
            except Exception as exc:
                logger.warning(f"终止校准线程异常: {exc}")
        self.btn_calibrate.setEnabled(True)
        self.btn_cancel_calib.setEnabled(False)
        self.lbl_calib_status.setText("🛑 二分法自动校准已手动停止。")
        self.lbl_calib_detail.setText("用户已手动中途取消校准。")

    def on_calib_finished(self, success, msg, results):
        self.btn_calibrate.setEnabled(True)
        self.btn_cancel_calib.setEnabled(False)
        if success:
            self.progress_calib.setValue(100)
            self.lbl_calib_status.setText(f"✅ 校准成功: {msg}")
            best_pct = results.get("best_percent", 0)
            best_v = results.get("best_voltage", 8.0)
            self.slider_light.setValue(int(best_pct))
            self.lbl_light_voltage.setText(f"直接控制目标: {best_pct}% ({best_v:.2f}V)")
            self.lbl_calib_detail.setText(f"最优识别参数已定位: {best_pct}% ({best_v:.2f}V)")
        else:
            self.lbl_calib_status.setText(f"❌ 校准完成: {msg}")
            self.lbl_calib_detail.setText(f"详细情况: {msg}")

    def _on_paper_input_changed(self):
        """纸张宽度或高度输入改变时，实时热联动更新 Tab 2 的打印预览伸缩图"""
        self.refresh_embedded_preview()

    def load_param_values(self):
        self.combobox_printSelect.clear()
        printers = QPrinterInfo.availablePrinters()
        p_names = [p.printerName() for p in printers]

        default_hardware = ["HPRT N31", "T63R RFID 打印机", "USB T63R 打印机"]
        for hw in default_hardware:
            if hw not in p_names:
                p_names.insert(0, hw)

        saved_prn = self.form_data.get('combobox_printSelect')
        for name in p_names:
            self.combobox_printSelect.addItem(name, name)
        prn_idx = self.combobox_printSelect.findData(saved_prn)
        if prn_idx >= 0:
            self.combobox_printSelect.setCurrentIndex(prn_idx)

        self.combobox_comSelect.clear()
        self.combobox_comSelect.addItem("不启用RS485实体按钮（无串口）", None)
        saved_com = self.form_data.get('combobox_comSelect')
        try:
            if serial and hasattr(serial, "tools"):
                ports = serial.tools.list_ports.comports()
                for port, desc, hwid in sorted(ports):
                    text = f"{port} - {desc}" if desc and port not in desc else (desc or port)
                    self.combobox_comSelect.addItem(text, port)
        except Exception as e:
            logger.warning(f"枚举串口失败: {e}")
        com_idx = self.combobox_comSelect.findData(saved_com)
        if com_idx >= 0:
            self.combobox_comSelect.setCurrentIndex(com_idx)
        elif self.combobox_comSelect.count() > 1:
            self.combobox_comSelect.setCurrentIndex(1)

        self.edit_service.setText(str(self.form_data.get('edit_service', '') or ''))
        self.edit_max_jian.setText(str(self.form_data.get('edit_max_jian', '10') or '10'))
        self.edit_max_xiang.setText(str(self.form_data.get('edit_max_xiang', '10') or '10'))
        self.edit_paper_width.setText(str(self.form_data.get('paper_width', '150') or '150'))
        self.edit_paper_height.setText(str(self.form_data.get('paper_height', '75') or '75'))
        self.edit_min_x.setText(str(self.form_data.get('edit_min_x', '0') or '0'))
        self.edit_max_x.setText(str(self.form_data.get('edit_max_x', '0') or '0'))
        self.edit_min_y.setText(str(self.form_data.get('edit_min_y', '0') or '0'))
        self.edit_max_y.setText(str(self.form_data.get('edit_max_y', '0') or '0'))

    def save_params(self):
        updates = {
            'combobox_printSelect': self.combobox_printSelect.currentData(),
            'combobox_comSelect': self.combobox_comSelect.currentData(),
            'edit_service': self.edit_service.text().strip(),
            'edit_max_jian': self.edit_max_jian.text().strip(),
            'edit_max_xiang': self.edit_max_xiang.text().strip(),
            'paper_width': self.edit_paper_width.text().strip(),
            'paper_height': self.edit_paper_height.text().strip(),
            'edit_min_x': self.edit_min_x.text().strip(),
            'edit_max_x': self.edit_max_x.text().strip(),
            'edit_min_y': self.edit_min_y.text().strip(),
            'edit_max_y': self.edit_max_y.text().strip(),
        }
        config.setConfig(updates)
        self.refresh_embedded_preview()
        QMessageBox.information(self, "保存成功", "✅【系统参数配置保存成功】\n所有更改已成功持久化，打印模板已联动同步生效！")

    def open_template_dialog(self):
        dlg = PrintTemplateDialog(config_path="config/settings.json", parent=self)
        dlg.elements_changed.connect(self._on_template_elements_changed)
        if dlg.exec_() == QDialog.Accepted:
            self.refresh_embedded_preview(self._template_elements)
