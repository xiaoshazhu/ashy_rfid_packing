# -*- coding: utf-8 -*-
# home.py

# 

import datetime

import sys

import threading

import time

import asyncio

import logging # 

from PySide6.QtWidgets import QToolTip

from PySide6.QtGui import QFont

from PySide6.QtGui import QColor

from PySide6 import QtWidgets, QtCore

from PySide6.QtWidgets import QGraphicsDropShadowEffect

# 

from hikUtils.CamOperation_class import CameraOperation

from hikUtils.MvImport.CameraParams_const import MV_GIGE_DEVICE, MV_USB_DEVICE

from hikUtils.MvImport.CameraParams_header import MV_CC_DEVICE_INFO_LIST

from hikUtils.MvImport.MvCameraControl_class import MvCamera

from hikUtils.MvImport.MvErrorDefine_const import MV_OK, MV_E_CALLORDER

import os  # 

from page import setting, config

from page.config import CONFIG_DATA

from page.log import LogDialog

# 

from qtDesigner.qt_setting import Ui_form_settings

from utils.Utils import extract_path_after_domain

from utils.printUtils import print_barcode

from utils.pyzbar_utils import process_image

from PySide6.QtCore import QTimer, QDateTime

from utils.SQLite import Database

from utils.upload_data_worker_thread import UploadDataWorkerThread

from utils.local_data_pipeline import (

    LocalTestDatabase,

    is_local_test_mode,

    is_remote_upload_enabled,

)

from page.light_control_dialog import LightControlDialog, load_light_config

from page.print_template_dialog import PrintTemplateDialog

from utils.wdip_light_controller import WDIPLightController

# 

obj_cam_operation = None

# 

class Home:

    # 

    def __init__(self, main_window):

        # 

        self.log_dialog = None #

        self.light_dialog = None

        self.template_dialog = None

        self.timer = None  # 

        self.isPrint = None  # 

        self.sacn_box_data = None  #  

        self.pageData = {

            'label_data_box': 0,  #  

            'label_data_case': 0,  #  

            'label_data_unline': 0,  # 

        }

        self.scan_case_data = []  #  

        self.pending_box_scans = []  # 

        self._last_bundle_staged = False

        self._recognition_sequence_active = False

        self._recognition_best_result = []

        self._recognition_best_boxes = None

        self._last_recognition_boxes = None

        self.case = None  # 

        self.preview_case_code = None  # 

        self.main_window = main_window

        # 

        self.styleInit()

        self.setup_recognition_snapshot_overlay()

        self.eventInit()

        self.hiKInit()

        self.pageInit()

        self.setup_manual_operation_pagination()

        self.autoPageData()#

        # 

        # 

        self.timer = QTimer(self.main_window)

        # 

        self.timer.timeout.connect(self.update_time)

        # 1000 = 1

        self.timer.start(1000)

        # HomeTD-39

        self.initialize_default_light_output()

    # 

    def update_time(self):

        # 

        current_time = QDateTime.currentDateTime()

        # label_date

        self.main_window.label_date.setText(current_time.toString("yyyy.MM.dd hh:mm:ss"))

    def eventInit(self):

        # 

        self.main_window.button_ok.clicked.connect(self.force_ok_clicked)  # 

        self.main_window.button_cancel.clicked.connect(self.on_button_cancel_clicked)  # 

        self.main_window.button_setting.clicked.connect(self.open_settings)  # 

        self.main_window.button_print.clicked.connect(self.on_button_print)  # 

        self.main_window.button_again.clicked.connect(self.on_button_again)  # 

        self.main_window.pushButton.clicked.connect(self.manualUpdateData)  # 

        self.main_window.label_clear.clicked.connect(self.clear_page_data) # 

        self.main_window.button_logs.clicked.connect(self.show_log_dialog) # 

        self.main_window.button_Restart.clicked.connect(self.restart_app)  # 

        self.main_window.button_reset.clicked.connect(self.reset_data)  # 

    def setup_recognition_snapshot_overlay(self):

        """SDKQt"""

        return

    def _sync_recognition_snapshot_geometry(self):

        return

    def show_recognition_boxes(

        self, boxes, source_width, source_height, source_image=None

    ):

        if obj_cam_operation is None or not boxes:

            return

        normalized = [tuple(map(int, box)) for box in boxes]

        self._last_recognition_boxes = (

            normalized,

            int(source_width),

            int(source_height),

            source_image.copy() if source_image is not None else None,

        )

        obj_cam_operation.set_recognition_snapshot(

            source_image,

            normalized,

            display_seconds=2.0,

        )

        logging.info(f" {len(normalized)} ")

    def clear_recognition_boxes(self):

        if obj_cam_operation is not None:

            obj_cam_operation.clear_recognition_boxes()

        self._last_recognition_boxes = None

    def setup_manual_operation_pagination(self):
        """配置左下角【手动操作】区域 4 个核心按键 (上下 8px 舒适空隙、33px标准高度、底边线 100% 完整清晰露出来)"""
        theme_btn_style = (
            "QPushButton { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #FFFFFF, stop:1 #E0E4E8); "
            "border: 1px solid #ACAEB1; border-radius: 4px; font-weight: bold; font-size: 14px; color: #000000; "
            "min-height: 33px; max-height: 33px; padding: 2px 2px; } "
            "QPushButton:hover { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #FFFFFF, stop:1 #D9E1F0); border-color: #3C7FB1; } "
            "QPushButton:pressed { background: #C2D1E5; border-color: #2B579A; }"
        )
        group_box = getattr(self.main_window, "groupBox", None)
        if not group_box:
            return

        btn_cancel = getattr(self.main_window, "button_cancel", None) # 设备复位
        btn_again = getattr(self.main_window, "button_again", None)   # 手动识别
        btn_print = getattr(self.main_window, "button_print", None)   # 打印箱码
        btn_ok = getattr(self.main_window, "button_ok", None)         # 确认录入 (隐藏)
        if btn_ok:
            btn_ok.hide()

        self.button_rebox = QtWidgets.QPushButton("重新装箱")         # 重新装箱
        self.button_rebox.clicked.connect(self.reset_data)

        # 容器 12, 40, 200, 86；垂直间距 8px 确保上下排按键有舒适间距，底边线 100% 露出来！
        manual_container = QtWidgets.QWidget(group_box)
        manual_container.setGeometry(12, 40, 200, 86)
        grid = QtWidgets.QGridLayout(manual_container)
        grid.setContentsMargins(0, 2, 0, 6)
        grid.setHorizontalSpacing(8)
        grid.setVerticalSpacing(8)

        if btn_cancel: grid.addWidget(btn_cancel, 0, 0)
        if btn_again: grid.addWidget(btn_again, 0, 1)
        if btn_print: grid.addWidget(btn_print, 1, 0)
        grid.addWidget(self.button_rebox, 1, 1)

        manual_container.show()

        for b in [btn_cancel, btn_again, btn_print, self.button_rebox]:
            if b:
                b.setStyleSheet(theme_btn_style)

    def show_temporary_tooltip(self, widget, title, message, *args, **kwargs):
        """在指定控件上方显示大字半透明提示泡 (兼容任意多参数，防止 TypeError)"""
        try:
            from PySide6.QtWidgets import QToolTip
            from PySide6.QtGui import QFont
            QToolTip.setFont(QFont('Microsoft YaHei', 22, QFont.Bold))
            if not widget or not hasattr(widget, "rect"):
                widget = getattr(self, "main_window", None)
            if widget:
                pos = widget.rect().center()
                global_pos = widget.mapToGlobal(pos)
                duration = 3000
                if args and isinstance(args[0], (int, float)):
                    duration = int(args[0])
                elif "duration" in kwargs:
                    duration = int(kwargs["duration"])

                text_html = f"<div style='text-align: center; color: #1E395B; font-weight: bold;'>{title}</div><div style='text-align: center; color: #333333;'>{message}</div>"
                QToolTip.showText(global_pos, text_html, widget, widget.rect(), duration)
        except Exception as e:
            logging.error(f"显示临时提示框异常: {e}")

    def open_settings_dialog(self, initial_tab=0):
        """防重复高压锁 + 0.8s 强制防抖：彻底解决设置窗口需要关3次的问题"""
        import time
        now = time.time()
        if getattr(self, '_settings_dialog_active', False) or (now - getattr(self, '_last_settings_close_time', 0) < 0.8):
            return
        self._settings_dialog_active = True
        try:
            from page.settings_dialog import SystemSettingsDialog
            dlg = SystemSettingsDialog(self, parent=self.main_window)
            dlg.tab_widget.setCurrentIndex(initial_tab)
            dlg.exec_()
        finally:
            self._settings_dialog_active = False
            self._last_settings_close_time = time.time()
            try:
                self.scan_code(0)
                self.scan_case()
            except Exception:
                pass

    def open_light_control_dialog(self):
        """打开【设置 -> 💡 亮度控制与校准】选项卡"""
        self.open_settings_dialog(initial_tab=2)

    def on_light_calibrate_clicked(self):
        """主界面【亮度校准】触发：单例激活并跳转到第3页"""
        self.open_settings_dialog(initial_tab=2)

    def shutdown_light_output(self) -> bool:

        """关闭 WDIP 补光灯输出。"""
        dialog_result = True

        if self.light_dialog:

            dialog_result = self.light_dialog.shutdown_output()

        light_config = load_light_config()

        port = str(light_config.get("port") or "").strip()

        if not port:

            logging.warning("WDIP补光灯端口未配置，跳过关闭输出")

            return False

        try:

            controller = WDIPLightController(

                port=port,

                baudrate=int(light_config.get("baudrate", 9600)),

                slave_addr=int(light_config.get("slave_addr", 1)),

                timeout=float(light_config.get("timeout_seconds", 0.8)),

                minimum_request_interval=float(

                    light_config.get("minimum_request_interval_ms", 250)

                ) / 1000.0,

                write_settle_seconds=float(

                    light_config.get("write_settle_ms", 400)

                ) / 1000.0,

                shared_exchange=getattr(

                    self.main_window, "exchange_shared_rs485", None

                ),

            )

            # 双重关灯保全：同时向硬件发送设置电压 0.00V 与关闭输出 (OFF) 寄存器指令
            controller.set_output_enabled_direct(False)
            time.sleep(0.12)
            try:
                controller.set_voltage_direct(0.0)
            except Exception:
                pass
            time.sleep(0.12)
            controller.set_output_enabled_direct(False)

            logging.info(f"WDIP补光灯输出已关闭: {port}")

            return dialog_result

        except Exception as exc:

            logging.exception(f"关闭WDIP补光灯失败: {exc}")

            return False

    def initialize_default_light_output(self) -> bool:
        """启动时将 WDIP 补光灯设置为 8~12V 范围内的默认电压并开启输出。"""
        light_config = load_light_config()
        port = str(light_config.get("port") or "").strip()
        if not port:
            logging.warning("WDIP补光灯端口未配置，跳过默认亮度设置")
            return False

        # 给予后台 RS485 监听线程最多 3 秒建立串口句柄
        for _ in range(30):
            active_rs485 = getattr(self.main_window, "rs485", None)
            if active_rs485 and getattr(active_rs485, "ser", None) and active_rs485.ser.is_open:
                break
            time.sleep(0.1)

        try:
            controller = WDIPLightController(
                port=port,
                baudrate=int(light_config.get("baudrate", 9600)),
                slave_addr=int(light_config.get("slave_addr", 1)),
                timeout=float(light_config.get("timeout_seconds", 0.8)),
                minimum_request_interval=float(
                    light_config.get("minimum_request_interval_ms", 250)
                ) / 1000.0,
                write_settle_seconds=float(
                    light_config.get("write_settle_ms", 400)
                ) / 1000.0,
                shared_exchange=getattr(
                    self.main_window, "exchange_shared_rs485", None
                ),
            )
            minimum_voltage = float(light_config.get("minimum_voltage_v", 8.0))
            maximum_voltage = float(light_config.get("maximum_voltage_v", 12.0))
            startup_voltage = float(light_config.get("startup_voltage_v", 8.0))
            startup_voltage = max(minimum_voltage, min(maximum_voltage, startup_voltage))

            controller.set_voltage_direct(startup_voltage)
            controller.set_output_enabled_direct(True)
            logging.info(f"WDIP补光灯已开启，启动电压={startup_voltage:.2f}V")
            return True
        except Exception as exc:
            logging.exception(f"设置WDIP默认8V补光灯输出失败: {exc}")
            return False

    def open_print_template_dialog(self):

        """"""

        if not self.template_dialog:

            self.template_dialog = PrintTemplateDialog(config_path="config/settings.json", parent=self.main_window)

        self.template_dialog.load_elements_config()

        current_code = str(self.case or self.preview_case_code or CONFIG_DATA.get("caseCode") or "").strip()
        preview_update = {
            "produce_date": datetime.datetime.now().strftime("%Y.%m.%d"),
        }
        if current_code:
            preview_update["barcode"] = current_code

        self.template_dialog.set_preview_data(preview_update)
        self.template_dialog.populate_table()

        try:

            self.template_dialog.exec_()

        finally:

            # 

            # SDK

            self.stop_line()

            self.main_window.widgetDisplay.update()

            QTimer.singleShot(150, self.ensure_camera_display)

    def pageInit(self):

        #   

        # 

        if CONFIG_DATA['pageData'] is not None and len(CONFIG_DATA['pageData']) > 0:

            self.pageData = CONFIG_DATA['pageData']

        # 

        if CONFIG_DATA['caseData'] is not None and len(CONFIG_DATA['caseData']) > 0:

            self.scan_case_data = CONFIG_DATA['caseData']

            # 

            self.scan_case()

        # 

        cached_case_code = str(CONFIG_DATA.get("caseCode") or "").strip()

        has_case_progress = len(self.scan_case_data) >= 1

        if self.is_valid_case_code(cached_case_code):

            self.updataPageCase(cached_case_code)

        elif has_case_progress:

            generated_case_code = self.generate_case_code()

            self.updataPageCase(generated_case_code)

            logging.info(f"已恢复缓存装箱进度：{len(self.scan_case_data)}捆")

        elif cached_case_code:

            logging.warning(f"13: {cached_case_code}")

            config.setConfig({"caseCode": None})

        if not has_case_progress and not self.is_valid_case_code(cached_case_code):
            self.updataPageCase(None)

        # 启动时始终刷新真实计数显示，空数据就是 0/10 盒、0/10 捆。
        self.scan_code(0)
        self.scan_case()
        self.updatePage()

    @staticmethod

    def is_valid_case_code(case_code):

        value = str(case_code or "").strip()

        return len(value) == 13 and value.isdigit()

    def generate_case_code(self):

        """13"""

        value = str(int(time.time() * 1000))

        return value[-13:].zfill(13)

    def clear_page_data(self):
        self.pageData['label_data_box'] = 0
        self.pageData['label_data_case'] = 0
        self.updatePage()

    def reset_data(self):
        self._recognition_sequence_active = False
        self._recognition_best_result = []
        self._recognition_best_boxes = None
        self.clear_recognition_boxes()
        self.sacn_box_data = None
        self.pending_box_scans = []
        self._last_bundle_staged = False
        self.preview_case_code = None
        self.case = None
        self.scan_case_data = []
        self.isPrint = False
        btn_print = getattr(self.main_window, "button_print", None)
        if btn_print:
            btn_print.setEnabled(True)
        config.setConfig({"caseData": self.scan_case_data})
        config.setConfig({"caseCode": self.case})

        self.scan_code(0)
        self.scan_code_end()
        self.scan_case()
        self.scan_case_end()
        self.updataPageCase(None)

        try:

            self.show_temporary_tooltip(
                self.main_window.groupBox_7,
                "【重新装箱提示】",
                "已成功重置当前装箱进度与盒码！"
            )

            self.main_window.play_warning()

        except Exception:

            pass

    def restart_app(self):

        """ ()"""

        reply = QtWidgets.QMessageBox.question(
            self.main_window,
            "确认重启",
            "确定要重新启动程序吗？",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            QtWidgets.QMessageBox.No
        )

        if reply == QtWidgets.QMessageBox.Yes:  #  "Yes" 

            python_executable = sys.executable  #  Python 

            # 

            current_dir = os.path.dirname(os.path.abspath(__file__))  # Desktop_QR_Send/page

            main_script_path = os.path.abspath(os.path.join(current_dir, "..", "main.py"))  # Desktop_QR_Send/main.py

            if not os.path.exists(main_script_path):

                main_script_path = os.path.abspath(sys.argv[0])

            try:
                # 1. 首先下发指令关闭 WDIP 补光灯物理输出
                try:
                    self.shutdown_light_output()
                except Exception as light_err:
                    logging.warning(f"重启前关闭补光灯异常: {light_err}")

                # 2. 主动解绑关闭后台 RS485 串口连接，释放 Windows 系统 COM3 端口句柄
                if hasattr(self.main_window, "_stop_rs485_thread"):
                    self.main_window._stop_rs485_thread = True
                if hasattr(self.main_window, "rs485") and self.main_window.rs485:
                    try:
                        self.main_window.rs485.close()
                        self.main_window.rs485 = None
                        logging.info("重启清理：后台 RS485 串口句柄已释放")
                    except Exception as rs_err:
                        logging.warning(f"重启清理 RS485 串口异常: {rs_err}")

                # 3. 停止相机抓图并彻底释放海康相机 SDK 句柄
                logging.info("重启清理：正在停止相机抓图并释放设备资源...")
                try:
                    self.stop_grabbing()
                    self.close_device()
                except Exception as cam_err:
                    logging.warning(f"重启时释放相机资源异常: {cam_err}")

                logging.info(f"正在重启程序: {python_executable} {main_script_path}")
                import subprocess
                # 给予底层硬件 SDK 与 Windows 串口驱动 1.0 秒缓冲时间彻底解绑释放端口
                QtCore.QThread.msleep(1000)
                subprocess.Popen([python_executable, main_script_path])
                QtWidgets.QApplication.quit()

            except Exception as e:
                logging.error(f"重启程序失败: {e}")

        else:

            #  "No" 

            pass  # 

    def show_log_dialog(self):

        """"""

        if not self.log_dialog:  #  log_dialog 

            self.log_dialog = LogDialog(self.main_window)  #  self (MainWindow)  parent

        self.log_dialog.show()  # 

        self.log_dialog.raise_()  #  ()

        self.log_dialog.activateWindow()  #  ()

    def show_large_warning_dialog(self, title: str, message: str):
        """弹出宽敞清晰的大号提示弹窗，按钮与关闭控件更大易触按。"""
        dlg = QtWidgets.QDialog(self.main_window)
        dlg.setWindowTitle(title)
        dlg.setMinimumSize(460, 240)
        dlg.setStyleSheet("""
            QDialog {
                background-color: #FFFFFF;
                border-radius: 12px;
            }
            QLabel#dlg_title {
                font-size: 19px;
                font-weight: bold;
                color: #1E293B;
            }
            QLabel#dlg_msg {
                font-size: 16px;
                color: #334155;
                line-height: 1.5;
            }
            QPushButton#btn_ok {
                font-size: 20px;
                font-weight: bold;
                color: #FFFFFF;
                background-color: #2563EB;
                border: none;
                border-radius: 10px;
                min-height: 54px;
                min-width: 180px;
                padding: 0 32px;
            }
            QPushButton#btn_ok:hover {
                background-color: #1D4ED8;
            }
            QPushButton#btn_ok:pressed {
                background-color: #1E40AF;
            }
        """)

        layout = QtWidgets.QVBoxLayout(dlg)
        layout.setContentsMargins(24, 20, 24, 24)
        layout.setSpacing(16)

        # 顶栏标题
        top_bar = QtWidgets.QHBoxLayout()
        lbl_title = QtWidgets.QLabel(title)
        lbl_title.setObjectName("dlg_title")

        top_bar.addWidget(lbl_title)
        top_bar.addStretch()
        layout.addLayout(top_bar)

        # 提示内容正文
        lbl_msg = QtWidgets.QLabel(message)
        lbl_msg.setObjectName("dlg_msg")
        lbl_msg.setWordWrap(True)
        layout.addWidget(lbl_msg)

        layout.addStretch()

        # 底部大号【确 定】按钮
        bottom_bar = QtWidgets.QHBoxLayout()
        bottom_bar.addStretch()
        btn_ok = QtWidgets.QPushButton("确 定")
        btn_ok.setObjectName("btn_ok")
        btn_ok.setCursor(QtCore.Qt.PointingHandCursor)
        btn_ok.clicked.connect(dlg.accept)
        bottom_bar.addWidget(btn_ok)
        bottom_bar.addStretch()
        layout.addLayout(bottom_bar)

        dlg.exec()

    def on_button_again(self):
        max_xiang = int(CONFIG_DATA.get('edit_max_xiang', 10))
        if len(self.scan_case_data) >= max_xiang:
            logging.info(f"当前箱已达到最大上限：{max_xiang}/{max_xiang}捆")
            self.show_large_warning_dialog(
                "装箱已满提示",
                f"当前箱装箱进度已达到 <b>{max_xiang}/{max_xiang} 捆</b> 上限！<br/><br/>请先点击<b>【打印箱码】</b>或<b>【重新装箱】</b>，再继续扫描。"
            )
            return

        if self._recognition_sequence_active:

            logging.info("")

            return

        logging.info("开始一次真实相机识别")

        # 10

        if self._last_bundle_staged:

            self.pending_box_scans = []

            self.sacn_box_data = None

            self.preview_case_code = None

            self._last_bundle_staged = False

            self.scan_code(0)

        # 5250ms

        # 2

        self._recognition_sequence_active = True
        self._recognition_best_result = []
        self._recognition_best_boxes = None

        # 立即触发抓拍，零人为延迟，保障扫码响应极速流畅！
        self._run_recognition_attempt(1)

    def _run_recognition_attempt(self, attempt_number):

        if not self._recognition_sequence_active:

            return

        self.sacn_box_data = None

        # 触发一次相机软抓拍与激光/曝光触发
        try:
            self.trigger_once()
        except Exception as err:
            logging.warning(f"触发相机拍照异常: {err}")

        self.capture_and_save_image(show_feedback=False)

        candidate = [dict(item) for item in (self.sacn_box_data or [])]

        if len(candidate) > len(self._recognition_best_result):

            self._recognition_best_result = candidate

            self._recognition_best_boxes = self._last_recognition_boxes

        expected_boxes = int(CONFIG_DATA.get("edit_max_jian", 10))

        if len(self._recognition_best_result) >= expected_boxes or attempt_number >= 2:

            self._finish_recognition_sequence()

            return

        QTimer.singleShot(
            50,
            lambda: self._run_recognition_attempt(attempt_number + 1),
        )

    def _finish_recognition_sequence(self):
        self._recognition_sequence_active = False
        recognized = [dict(item) for item in self._recognition_best_result]
        self._recognition_best_result = []

        if self._recognition_best_boxes:
            boxes, source_width, source_height, source_image = self._recognition_best_boxes
            self.show_recognition_boxes(
                boxes,
                source_width,
                source_height,
                source_image=source_image,
            )
        self._recognition_best_boxes = None

        if recognized:
            expected_boxes = int(CONFIG_DATA.get("edit_max_jian") or 10)

            # 1. 汇总当前未封捆 (pending_box_scans) 与已封捆 (scan_case_data) 的所有历史盒码
            existing_codes = set()
            for p_item in self.pending_box_scans:
                code_val = str(p_item.get("code") or p_item.get("data") or "").strip()
                if code_val:
                    existing_codes.add(code_val)

            for b_bundle in (self.scan_case_data or []):
                for b_box in b_bundle.get("boxContents", []):
                    code_val = str(b_box.get("code") or b_box.get("data") or "").strip()
                    if code_val:
                        existing_codes.add(code_val)

            # 2. 过滤本次识别结果，精确剔除重复盒码
            new_unique_items = []
            duplicate_count = 0
            scanned_in_attempt = set()

            for item in recognized:
                code_val = str(item.get("code") or item.get("data") or "").strip()
                if not code_val:
                    continue
                if code_val in existing_codes or code_val in scanned_in_attempt:
                    duplicate_count += 1
                else:
                    scanned_in_attempt.add(code_val)
                    new_unique_items.append(dict(item))

            # 3. 计算本捆剩余空间并追加新盒码
            remaining_capacity = max(0, expected_boxes - len(self.pending_box_scans))
            items_to_add = new_unique_items[:remaining_capacity]
            added_count = len(items_to_add)

            if added_count > 0:
                self.pending_box_scans.extend(items_to_add)

            self.sacn_box_data = [dict(item) for item in self.pending_box_scans]
            current_count = len(self.sacn_box_data)
            self.scan_code(current_count)

            # 4. 判定与反馈识别结果
            if current_count == expected_boxes:
                # 凑满整捆（如 10/10 盒），自动封捆进组（由 stage_recognized_bundle 统一给出“第 X 捆成功加入”提示与播放音）
                self.stage_recognized_bundle()
                return

            elif added_count > 0:
                # 成功录入新盒码但尚未凑满一捆
                still_needed = expected_boxes - current_count
                self.show_temporary_tooltip(
                    self.main_window.groupBox_7,
                    "【扫描识别成功】",
                    f"新增 {added_count} 个有效新盒码，当前进度：{current_count}/{expected_boxes} 盒，还差 {still_needed} 盒，请继续补扫。",
                )
                self.main_window.play_success()

            elif duplicate_count > 0:
                # 识别到的全部为重复盒码
                self.show_temporary_tooltip(
                    self.main_window.groupBox_7,
                    "【重复扫描提醒】",
                    f"检测到 {duplicate_count} 个重复盒码已自动剔除！当前进度：{current_count}/{expected_boxes} 盒。",
                )
                self.main_window.play_warning()

            return

        self.sacn_box_data = (
            [dict(item) for item in self.pending_box_scans]
            if self.pending_box_scans else None
        )
        self.scan_code(len(self.pending_box_scans))
        self.show_temporary_tooltip(
            self.main_window.groupBox_7,
            "【识别失败】",
            "当前画面未识别到完整盒码，请调整摆放方向、反光和焦距。",
        )
        self.main_window.play_warning()

    def stage_recognized_bundle(self):

        expected_boxes = int(CONFIG_DATA.get("edit_max_jian") or 10)

        max_bundles = int(CONFIG_DATA.get("edit_max_xiang") or 10)

        if not self.sacn_box_data or len(self.sacn_box_data) != expected_boxes:

            return False

        if len(self.scan_case_data) >= max_bundles:

            self.show_temporary_tooltip(
                self.main_window.groupBox_7,
                "【已计数提醒】",
                "当前识别组已经计入装箱进度，不重复录入！"
            )

            return False

        self.scan_case_data.append({

            "boxContents": [dict(item) for item in self.sacn_box_data],

            "database_status": "pending_case",

        })

        config.setConfig({"caseData": self.scan_case_data})

        self.pageData["label_data_box"] += len(self.sacn_box_data)

        self.scan_case()

        self.updatePage()

        # 1

        # boxContents

        if len(self.scan_case_data) == 1 and not self.is_valid_case_code(self.case):

            case_code = self.generate_case_code()

            self.preview_case_code = case_code

            self.updataPageCase(case_code)

            logging.info(f"1/{max_bundles}13: {case_code}")

        # 写入本地 SQLite 数据库并推送到 WS 线上服务器（单条防重写、推送一次）
        try:
            db = Database()
            for sacn_box_item in (self.sacn_box_data or []):
                boxContent = sacn_box_item.get('data') if isinstance(sacn_box_item, dict) else str(sacn_box_item)
                boxContent = str(boxContent or "").strip()
                if boxContent:
                    cid = extract_path_after_domain(boxContent)
                    # 匹配阿里云 yk_store_case_box 表结构的 BigInt 主键 id
                    bigint_id = int(time.time() * 1000000)

                    case_code_val = self.case or getattr(self, 'preview_case_code', '') or ""
                    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
                    data = {
                        'id': cid,
                        'caseContent': case_code_val,
                        'boxContent': boxContent,
                        'type': '生产装箱',
                        'createTime': now_str,
                        'isLine': 0
                    }

                    # 只要线上 WS 连接就绪，立刻将扫码结果推送至远端 WebSocket 服务
                    if (
                        getattr(self.main_window, "client", None)
                        and getattr(self.main_window, "loop", None)
                        and self.main_window.client.get_connection_status()
                    ):
                        try:
                            asyncio.run_coroutine_threadsafe(self.main_window.client.send(data), self.main_window.loop)
                            logging.info(f"扫码数据实时推送到 WS 成功: ID={cid} 箱码={case_code_val} 盒码={boxContent}")
                        except Exception as ws_err:
                            logging.error(f"WS 数据实时推送异常: {ws_err}")

                    # 本地历史防重记录（安全落库，不对现有数据库进行任何删除修改）
                    if not db.is_uploaded(cid):
                        try:
                            db.box_case_insert_data(data)
                        except Exception as db_insert_err:
                            logging.warning(f"本地防重记录保存跳过: {db_insert_err}")
                    else:
                        logging.info(f"盒码 ID: {cid} 已在本地历史记录中，已仅通过 WS 完成推送。")
        except Exception as db_err:
            logging.error(f"扫码数据落库或推送发生错误: {db_err}")

        logging.info(


            "本次真实识别结果已计入装箱进度。"

        )

        current_bundles = len(self.scan_case_data)
        self.show_temporary_tooltip(
            self.main_window.groupBox_7,
            f"【第 {current_bundles} 捆成功加入】",
            f"✅ 已成功录入第 <b>{current_bundles}/{max_bundles} 捆</b>！（本捆共 {expected_boxes} 盒）",
        )

        self.main_window.play_success()

        self._last_bundle_staged = True

        # 封捆成功后清空当前捆缓存，重置底部识别结果显示，为下一捆扫描做好准备
        self.pending_box_scans = []
        self.sacn_box_data = []
        self.scan_code(0)

        # 检查当前箱装箱进度：如果已满 10 捆（1箱），提示装箱完成（必须由人工手动点击【打印箱码】按钮触发打印）
        if len(self.scan_case_data) >= max_bundles:
            logging.info(f"装箱进度已满 {len(self.scan_case_data)}/{max_bundles} 捆（1箱），请手动点击【打印箱码】按钮下发打印任务。")
            self.show_large_warning_dialog(
                "装箱完成提示",
                f"当前箱装箱进度已满 <b>{max_bundles}/{max_bundles} 捆</b>（1箱）！<br/><br/>请手动点击<b>【打印箱码】</b>按钮下发打印任务。"
            )

        return True

    def show_scanned_print_preview(self):

        case_code = str(self.case or "").strip()

        if not case_code:

            return False

        if not self.template_dialog:

            self.template_dialog = PrintTemplateDialog(

                config_path="config/settings.json",

                parent=self.main_window,

            )

        self.template_dialog.load_elements_config()

        self.template_dialog.set_preview_data({

            "barcode": case_code,

            "produce_date": datetime.datetime.now().strftime("%Y.%m.%d"),

        })
        self.template_dialog.save_elements_config()

        return self.template_dialog.show_preview_dialog(parent=self.main_window)

    def force_ok_clicked(self):

        self.on_button_ok_clicked(True)#

    def on_button_ok_clicked(self,force = False):

        # 

        logging.info("数据录入按钮被点击了。")

        if is_local_test_mode():

            # 

            # RFID

            if self._last_bundle_staged:

                logging.info("")

                return

            if not self.stage_recognized_bundle():

                self.show_temporary_tooltip(
                    self.main_window.groupBox_7,
                    "【无法录入】",
                    "请先完成一整捆真实盒码识别，再录入装箱进度。",
                )

                self.main_window.play_warning()

            return

        # 

        max_xiang = int(CONFIG_DATA.get('edit_max_xiang', 10))

        if len(self.scan_case_data) >= max_xiang:

            logging.info(


                "请先完成一整捆真实盒码识别，再录入装箱进度。"

            )

            return

        # 

        if self.sacn_box_data is None:

            logging.info("没有识别到有效盒码。")

            self.show_temporary_tooltip(
                self.main_window.groupBox_7,
                "【无效盒码提醒】",
                "未能识别到有效盒码，请重新进行扫描！"
            )

            #    

            self.main_window.play_warning()

            return

        if self._last_bundle_staged:

            logging.info("当前识别组已经计入装箱进度，不重复录入。")

            self.show_temporary_tooltip(
                self.main_window.groupBox_7,
                "【已计数提醒】",
                "当前识别组已经计入装箱进度，不重复录入！",
            )

            return

        # 

        if self.case is None:

            # 

            item = {'boxContents': self.sacn_box_data}

            self.scan_case_data.append(item)

            # 

            self.sacn_box_data = None

            self.scan_code_end()

            # if len(self.scan_case_data) == max_jian:

            #     # +1

            #     self.pageData['label_data_case'] += 1

            #     # 

            #     self.scan_case_data = []

            #     # 

            #     self.scan_case_end()

            #     # 

            #     self.on_button_print()

            # else:

            #     # 

            #     self.scan_case()

            #

            self.scan_case()

            # 

            self.updatePage()

        else:

            # 

            logging.info("") #  logging.info  print

            # 

            self.show_temporary_tooltip(
                self.main_window.groupBox_7,
                "【装箱进度已更新】",
                "本次真实识别结果已计入装箱进度。",
            )

            # 

            self.main_window.play_warning()

    def on_button_cancel_clicked(self):
        logging.info("执行复位操作（清空当次识别结果、刷新摄像机页面，保留已装箱进度）...")
        self._recognition_sequence_active = False
        self._recognition_best_result = []
        self._recognition_best_boxes = None
        self.clear_recognition_boxes()
        self.sacn_box_data = None
        self.pending_box_scans = []
        self._last_bundle_staged = False
        self.preview_case_code = None
        self.scan_code(0)
        self.scan_code_end()

        # 刷新并保证摄像机预览画面正常运行
        if obj_cam_operation is None or not obj_cam_operation.b_open_device:
            logging.warning("复位检测：相机连接关闭，尝试重新初始化...")
            self.hiKInit()
        else:
            self.ensure_camera_display()

        try:
            self.show_temporary_tooltip(
                self.main_window.groupBox_7,
                "【设备复位成功】",
                "相机预览与当前未录入识别结果已复位，保留已装箱进度。",
            )
            self.main_window.play_success()
        except Exception:
            pass

    def open_settings(self):
        """打开设置中心，只调起唯一一个 SystemSettingsDialog，只执行一次 exec_()！"""
        self.open_settings_dialog(initial_tab=0)

    def updatePage(self):

        self.main_window.label_data_box.setText(f"{self.pageData['label_data_box']}")

        self.main_window.label_data_case.setText(f"{self.pageData['label_data_case']}")

        self.main_window.label_data_unline.setText(f"{self.pageData['label_data_unline']}")

        config.setConfig({"pageData": self.pageData})

        config.setConfig({"caseData": self.scan_case_data})

        config.setConfig({"caseCode": self.case})

    @QtCore.Slot(float)
    def update_progress_bar_slot(self, percen):
        self.main_window.pushButton.setText(f"上传进度 {percen}%")
        if percen >= 100:
            self.main_window.pushButton.setText("手动数据上传")
            self.main_window.pushButton.setEnabled(True)

    # 

    def manualUpdateData(self):
        from utils.local_data_pipeline import load_pipeline_config
        cfg = load_pipeline_config()
        mode = str(cfg.get("mode", "local_mysql")).lower()

        if mode == "local_mysql" or is_remote_upload_enabled():
            self.main_window.pushButton.setEnabled(False)
            max_limit = 10000
            self.upload_worker_thread = UploadDataWorkerThread(self.main_window, max_limit)
            self.upload_worker_thread.update_progress_signal.connect(self.update_progress_bar_slot)
            self.upload_worker_thread.start()
            logging.info("手动数据同步任务已触发...")
        else:
            self.show_temporary_tooltip(
                self.main_window.groupBox_7,
                "【本地模式】",
                "当前数据保存在本地数据库中。",
            )

            self.show_temporary_tooltip(
                self.main_window.groupBox_7,
                "【装箱进度已更新】",
                "真实识别结果已成功录入当前装箱进度。",
            )

#  

    def autoPageData(self):

        periodic_thread = threading.Thread(target=self.periodic_task)


        periodic_thread.start()

    def periodic_task(self):
        while True:
            try:
                if is_local_test_mode():
                    label_data_unline = LocalTestDatabase().pending_upload_count()
                else:
                    label_data_unline = int(Database().box_case_count_unuploaded())

                pageData = config.CONFIG_DATA.get("pageData", {})
                if pageData.get('label_data_unline') != label_data_unline:
                    pageData['label_data_unline'] = label_data_unline
                    config.setConfig({"pageData": pageData})
                    self.main_window.label_data_unline.setText(
                        f"{pageData['label_data_unline']}"
                    )
                time.sleep(2.0)
            except Exception as exc:
                logging.warning(f"后台统计待上传数据提示: {exc}")
                time.sleep(3.0)


    # =================================================

    # 

    def capture_and_save_image(self, show_feedback=True):

        # 

        if obj_cam_operation is None or not obj_cam_operation.b_start_grabbing:

            logging.info("") #  logging.info  print

            self.sacn_box_data = None

            self.preview_case_code = None

            if show_feedback:

                self.scan_code(0)

                self.show_temporary_tooltip(
                    self.main_window.groupBox_7,
                    "【识别失败】",
                    "相机尚未开始推流，未使用任何模拟数据。",
                )

            return False

        # 

        if obj_cam_operation.buf_save_image is None:

            logging.info("") #  logging.info  print

            self.sacn_box_data = None

            self.preview_case_code = None

            if show_feedback:

                self.scan_code(0)

                self.show_temporary_tooltip(
                    self.main_window.groupBox_7,
                    "【识别失败】",
                    "相机没有有效图像帧，未使用任何模拟数据。",
                )

            return False

        np_array_image = obj_cam_operation.get_np_array_image()

        if np_array_image is None or getattr(np_array_image, "size", 0) == 0:

            logging.warning("")

            self.sacn_box_data = None

            self.preview_case_code = None

            if show_feedback:

                self.scan_code(0)

            return False

        logging.info(

            ": shape=%s, =%.1f, =%s, =%s",

            tuple(np_array_image.shape),

            float(np_array_image.mean()),

            int(np_array_image.min()),

            int(np_array_image.max()),

        )

        # pyzbar_utilsprocess_image

        process_image(

            self,

            obj_cam_operation,

            np_array_image,

            show_feedback=show_feedback,

        )

        return True

    # =================================================

    # ================================================

    # 

    def on_button_print(self):
        if self.isPrint:
            logging.info("打印任务正在处理中，请稍候...")
            return

        max_bundles = int(CONFIG_DATA.get("edit_max_xiang") or 10)
        scanned_bundles = len(self.scan_case_data) if hasattr(self, 'scan_case_data') and self.scan_case_data else 0

        if scanned_bundles < max_bundles:
            logging.warning(f"无法打印：当前仅扫描 {scanned_bundles}/{max_bundles} 捆，未满 {max_bundles} 捆（1箱），不允许打印。")
            self.show_temporary_tooltip(
                self.main_window.groupBox_7,
                "【未满箱无法打印】",
                f"当前仅扫描 {scanned_bundles}/{max_bundles} 捆，需满 {max_bundles} 捆（1箱）才能打印！",
            )
            QTimer.singleShot(0, lambda: getattr(self.main_window, 'play_warning', lambda: None)())
            return

        case_code = self.case
        if not case_code or not self.is_valid_case_code(case_code):
            case_code = self.generate_case_code()
            self.updataPageCase(case_code)

        self.isPrint = True
        btn_print = getattr(self.main_window, "button_print", None)
        if btn_print:
            btn_print.setEnabled(False)

        def _async_print_job():
            try:
                try:
                    local_database = LocalTestDatabase()
                except Exception as exc:
                    logging.exception(f"本地数据库不可用: {exc}")
                    QTimer.singleShot(0, lambda: self.show_temporary_tooltip(
                        self.main_window.groupBox_7,
                        "【暂不能打印】",
                        f"本地测试数据库无法使用：{exc}",
                    ))
                    QTimer.singleShot(0, lambda: getattr(self.main_window, 'play_warning', lambda: None)())
                    return

                result = self.print_barcode(case_code)
                if not getattr(result, "success", False):
                    error_message = getattr(result, "error_message", "打印机未返回成功状态。")
                    logging.warning(f"打印失败: {error_message}")
                    QTimer.singleShot(0, lambda msg=error_message: self.show_temporary_tooltip(
                        self.main_window.groupBox_7,
                        "【打印失败】",
                        str(msg),
                    ))
                    QTimer.singleShot(0, lambda: getattr(self.main_window, 'play_warning', lambda: None)())
                    return

                try:
                    local_record_id = local_database.save_successful_print(
                        case_code,
                        self.scan_case_data,
                        result,
                    )
                    logging.info(f"record_id={local_record_id}")
                except Exception as exc:
                    logging.exception(f"本地入库失败: {exc}")
                    QTimer.singleShot(0, lambda e=exc: self.show_temporary_tooltip(
                        self.main_window.groupBox_7,
                        "【打印成功但入库失败】",
                        f"标签已经打印，请勿重复打印；本地入库错误：{e}",
                    ))
                    QTimer.singleShot(0, lambda: getattr(self.main_window, 'play_warning', lambda: None)())
                    return

                # 后台异步写入本地 MySQL 数据库
                try:
                    from utils.local_data_pipeline import load_pipeline_config
                    cfg = load_pipeline_config()
                    if str(cfg.get("mode", "local_mysql")).lower() == "local_mysql":
                        from utils.MySQL import MySQLDatabase
                        mysql_db = MySQLDatabase()
                        create_time_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
                        bundles = self.scan_case_data or []
                        inserted_count = 0
                        base_id = int(time.time() * 1000)

                        for bundle in bundles:
                            boxes = []
                            if isinstance(bundle, dict):
                                boxes = bundle.get("boxContents", [])
                                if not boxes and "boxContent" in bundle:
                                    boxes = [bundle]
                            elif isinstance(bundle, list):
                                boxes = bundle
                            else:
                                boxes = [bundle]

                            for box in boxes:
                                if isinstance(box, dict):
                                    b_content = box.get("data") or box.get("boxContent") or box.get("box_content") or str(box)
                                    b_content = str(b_content).strip()
                                    if ".cn/" in b_content:
                                        b_content = b_content.split(".cn/")[-1].strip()
                                    b_type = box.get("type", "QRCODE")
                                else:
                                    b_content = str(box).strip()
                                    if ".cn/" in b_content:
                                        b_content = b_content.split(".cn/")[-1].strip()
                                    b_type = "QRCODE"

                                inserted_count += 1
                                record_dict = {
                                    "id": base_id + inserted_count,
                                    "caseContent": case_code,
                                    "boxContent": b_content,
                                    "type": b_type,
                                    "createTime": create_time_str
                                }
                                mysql_db.box_case_insert_data(record_dict)
                        logging.info(f"【本地 MySQL 自动落库成功】箱码={case_code}，已同步写入 {inserted_count} 条数据")
                except Exception as mysql_err:
                    logging.error(f"同步写入本地 MySQL 发生错误: {mysql_err}")

                QTimer.singleShot(0, lambda code=case_code: self.show_temporary_tooltip(
                    self.main_window.groupBox_7,
                    "【打印箱码成功】",
                    f"已生成箱码：{code}（绿框显示）；已同步保存到本地数据库。",
                ))
                QTimer.singleShot(0, lambda: getattr(self.main_window, 'play_success', lambda: None)())

            except Exception as exc:
                logging.exception(f"打印过程异常: {exc}")
                QTimer.singleShot(0, lambda e=exc: self.show_temporary_tooltip(
                    self.main_window.groupBox_7,
                    "【打印失败】",
                    f"打印机通信异常：{e}",
                ))
                QTimer.singleShot(0, lambda: getattr(self.main_window, 'play_warning', lambda: None)())
            finally:
                time.sleep(1.5)  # 物理冷却等待 1.5 秒，保证驱动与端口句柄完全归还
                self.isPrint = False
                if btn_print:
                    QTimer.singleShot(0, lambda: btn_print.setEnabled(True))
                QTimer.singleShot(0, self.reset_data)

        threading.Thread(target=_async_print_job, daemon=True).start()

    # 

    def updataPageCase(self, case_code):

        if case_code is None:

            self.main_window.taps_20.setText("请打印箱码")

            self.main_window.groupBox_box_0.setStyleSheet(

                "QGroupBox { background-color: #EC808D; border: 1px solid #797979; border-radius: 5px; }")

        else:
            self.case = case_code
            self.preview_case_code = case_code
            self.main_window.taps_20.setText(f"{self.case}")
            self.main_window.groupBox_box_0.setStyleSheet(
                "QGroupBox { background-color: #CAF982; border: 1px solid #797979; border-radius: 5px; }")

            config.setConfig({"caseCode": case_code})

    #  ( T63R RFID )

    def print_barcode(self, case_code):

        printer_name = CONFIG_DATA.get('combobox_printSelect', '')

        page_width = int(CONFIG_DATA.get('edit_page_width', 500))

        page_height = int(CONFIG_DATA.get('edit_page_height', 400))

        page_num = int(CONFIG_DATA.get('edit_page_num', 1))

        #  printUtils  T63R RFID 

        res = print_barcode(case_code, printer_name, page_width, page_height, page_num)

        if getattr(res, "success", False):

            logging.info(f": {case_code}")

        else:

            logging.warning(

                ": case=%s, code=%s, message=%s",

                case_code,

                getattr(res, "error_code", ""),

                getattr(res, "error_message", ""),

            )

        return res #  logging.info  print

    # =================================================

    # ======================== =========================

    # 

    def scan_code(self, num):
        expected_boxes = max(1, int(CONFIG_DATA.get("edit_max_jian") or 10))
        current_boxes = max(0, min(int(num), expected_boxes))
        if hasattr(self.main_window, "label_result_box"):
            self.main_window.label_result_box.setText(f"【{current_boxes}/{expected_boxes}盒】")

        # 模式 1：当盒数 <= 10 时，直接使用原版 QtDesigner 原生控件，100% 保持原界面样式与比例，零变形！
        if expected_boxes <= 10:
            if hasattr(self, "_box_scroll_area") and self._box_scroll_area:
                self._box_scroll_area.hide()

            group_boxes = [
                getattr(self.main_window, f"groupBox_result_{i}", None)
                for i in range(1, 11)
            ]
            for i, group_box in enumerate(group_boxes, start=1):
                if not group_box:
                    continue
                if i <= expected_boxes:
                    group_box.show()
                    if i <= num:
                        group_box.setStyleSheet("QGroupBox { background-color: #CAF982; border: 1px solid #797979; border-radius: 5px; }")
                    else:
                        group_box.setStyleSheet("QGroupBox { background-color: #EC808D; border: 1px solid #797979; border-radius: 5px; }")
                else:
                    group_box.hide()
            return

        # 模式 2：当盒数 > 10 时，隐藏原生 10 个控件，唤醒完全透明的动态 ScrollArea 滑块
        for i in range(1, 11):
            gb = getattr(self.main_window, f"groupBox_result_{i}", None)
            if gb:
                gb.hide()

        if not hasattr(self, "_box_scroll_area") or self._box_scroll_area is None:
            parent_gb = getattr(self.main_window, "groupBox_2", None)
            if parent_gb:
                from PySide6.QtWidgets import QScrollArea, QWidget, QHBoxLayout
                from PySide6.QtCore import Qt, QRect

                scroll = QScrollArea(parent_gb)
                scroll.setGeometry(QRect(10, 38, 536, 102))
                scroll.setWidgetResizable(True)
                scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
                scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
                scroll.setStyleSheet(
                    "QScrollArea { border: none; background: transparent; } "
                    "QWidget { background: transparent; } "
                    "QScrollBar:horizontal { height: 6px; background: transparent; border-radius: 3px; } "
                    "QScrollBar::handle:horizontal { background: #A0A0A0; border-radius: 3px; min-width: 20px; } "
                    "QScrollBar::handle:horizontal:hover { background: #707070; }"
                )

                container = QWidget()
                container.setStyleSheet("background: transparent;")
                layout = QHBoxLayout(container)
                layout.setContentsMargins(2, 2, 2, 8)
                layout.setSpacing(18)
                scroll.setWidget(container)

                self._box_scroll_area = scroll
                self._box_container = container
                self._box_layout = layout

        if hasattr(self, "_box_scroll_area") and self._box_scroll_area:
            self._box_scroll_area.show()

        if hasattr(self, "_box_layout") and self._box_layout:
            while self._box_layout.count():
                child = self._box_layout.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()

            from PySide6.QtWidgets import QGroupBox, QLabel, QVBoxLayout
            from PySide6.QtCore import Qt
            from PySide6.QtGui import QFont

            for i in range(1, expected_boxes + 1):
                box_gb = QGroupBox()
                box_gb.setFixedSize(34, 86)

                vbox = QVBoxLayout(box_gb)
                vbox.setContentsMargins(0, 0, 0, 0)
                vbox.setAlignment(Qt.AlignCenter)

                lbl = QLabel(str(i))
                lbl.setFixedSize(27, 30)
                lbl.setAlignment(Qt.AlignCenter)
                font = QFont("宋体", 18, QFont.Bold)
                lbl.setFont(font)
                lbl.setStyleSheet(
                    "QLabel { background-color: #FFFFFF; border: 3px solid #797979; border-radius: 5px; color: #797979; }"
                )
                vbox.addWidget(lbl)

                if i <= num:
                    box_gb.setStyleSheet("QGroupBox { background-color: #CAF982; border: 1px solid #797979; border-radius: 5px; }")
                else:
                    box_gb.setStyleSheet("QGroupBox { background-color: #EC808D; border: 1px solid #797979; border-radius: 5px; }")
                self._box_layout.addWidget(box_gb)

    def scan_code_end(self):
        self.scan_code(0)

    def scan_case(self):
        num = len(self.scan_case_data) if hasattr(self, "scan_case_data") and self.scan_case_data else 0
        expected_bundles = max(1, int(CONFIG_DATA.get("edit_max_xiang") or 10))
        current_bundles = max(0, min(num, expected_bundles))
        if hasattr(self.main_window, "label_result_case"):
            self.main_window.label_result_case.setText(f"【{current_bundles}/{expected_bundles}捆】")

        # 模式 1：当捆数 <= 10 时，直接使用原版 QtDesigner 原生控件，100% 对应第一张图，零变形！
        if expected_bundles <= 10:
            if hasattr(self, "_case_scroll_area") and self._case_scroll_area:
                self._case_scroll_area.hide()

            group_boxes = [
                getattr(self.main_window, f"groupBox_box_{i}", None)
                for i in range(1, 11)
            ]
            for i, group_box in enumerate(group_boxes, start=1):
                if not group_box:
                    continue
                if i <= expected_bundles:
                    group_box.show()
                    if i <= num:
                        group_box.setStyleSheet("QGroupBox { background-color: #CAF982; border: 1px solid #797979; border-radius: 5px; }")
                    else:
                        group_box.setStyleSheet("QGroupBox { background-color: #EC808D; border: 1px solid #797979; border-radius: 5px; }")
                else:
                    group_box.hide()
            return

        # 模式 2：当捆数 > 10 时，隐藏原生 10 个控件，唤醒完全透明的动态 ScrollArea 滑块（保持原 10 个的大小与完美间隔）
        for i in range(1, 11):
            gb = getattr(self.main_window, f"groupBox_box_{i}", None)
            if gb:
                gb.hide()

        if not hasattr(self, "_case_scroll_area") or self._case_scroll_area is None:
            parent_gb = getattr(self.main_window, "groupBox_3", None)
            if parent_gb:
                from PySide6.QtWidgets import QScrollArea, QWidget, QGridLayout
                from PySide6.QtCore import Qt, QRect

                scroll = QScrollArea(parent_gb)
                scroll.setGeometry(QRect(10, 335, 445, 410))
                scroll.setWidgetResizable(True)
                scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
                scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
                scroll.setStyleSheet(
                    "QScrollArea { border: none; background: transparent; } "
                    "QWidget { background: transparent; } "
                    "QScrollBar:vertical { width: 6px; background: transparent; border-radius: 3px; } "
                    "QScrollBar::handle:vertical { background: #A0A0A0; border-radius: 3px; min-height: 20px; } "
                    "QScrollBar::handle:vertical:hover { background: #707070; }"
                )

                container = QWidget()
                container.setStyleSheet("background: transparent;")
                grid = QGridLayout(container)
                grid.setContentsMargins(10, 7, 10, 7)
                grid.setHorizontalSpacing(43)
                grid.setVerticalSpacing(50)
                scroll.setWidget(container)

                self._case_scroll_area = scroll
                self._case_container = container
                self._case_grid = grid

        if hasattr(self, "_case_scroll_area") and self._case_scroll_area:
            self._case_scroll_area.show()

        if hasattr(self, "_case_grid") and self._case_grid:
            while self._case_grid.count():
                child = self._case_grid.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()

            from PySide6.QtWidgets import QGroupBox, QLabel, QHBoxLayout
            from PySide6.QtCore import Qt
            from PySide6.QtGui import QFont

            for i in range(1, expected_bundles + 1):
                bundle_gb = QGroupBox()
                bundle_gb.setFixedSize(190, 40)

                hbox = QHBoxLayout(bundle_gb)
                hbox.setContentsMargins(0, 0, 0, 0)
                hbox.setAlignment(Qt.AlignCenter)

                lbl = QLabel(str(i))
                lbl.setFixedSize(30, 30)
                lbl.setAlignment(Qt.AlignCenter)
                font = QFont("宋体", 18, QFont.Bold)
                lbl.setFont(font)
                lbl.setStyleSheet(
                    "QLabel { background-color: #FFFFFF; border: 3px solid #797979; border-radius: 5px; color: #797979; }"
                )
                hbox.addWidget(lbl)

                if i <= num:
                    bundle_gb.setStyleSheet("QGroupBox { background-color: #CAF982; border: 1px solid #797979; border-radius: 5px; }")
                else:
                    bundle_gb.setStyleSheet("QGroupBox { background-color: #EC808D; border: 1px solid #797979; border-radius: 5px; }")

                row = (i - 1) // 2
                col = (i - 1) % 2
                self._case_grid.addWidget(bundle_gb, row, col)

    def on_rfid_calibrate_clicked(self):

        """ RFID """

        try:

            self.print_service.calibrate()

            QtWidgets.QMessageBox.information(
                self.main_window,
                "RFID校准",
                "请按打印机配套软件完成标签定位校准，再回到本程序测试。",
            )

        except Exception as e:
            logging.exception(f"RFID校准失败: {e}")

    def scan_case_end(self):

        # n/s

        # label_result_box

        self.scan_case()

        # groupBox

        group_boxes = [

            self.main_window.groupBox_box_1, self.main_window.groupBox_box_2,

            self.main_window.groupBox_box_3, self.main_window.groupBox_box_4,

            self.main_window.groupBox_box_5, self.main_window.groupBox_box_6,

            self.main_window.groupBox_box_7, self.main_window.groupBox_box_8,

            self.main_window.groupBox_box_9, self.main_window.groupBox_box_10

        ]

        # groupBox

        for group_box in group_boxes:

            group_box.setStyleSheet("""

                QGroupBox {

                    background-color: #F2F2F2;

                    border: 1px solid #797979;

                    border-radius: 5px;

                }

            """)

    # ======================== =========================

    # =================================================

    # 

    def hiKInit(self):

        # 

        self.initCamera()

    # 

    def initCamera(self):

        # 

        deviceList = MV_CC_DEVICE_INFO_LIST()

        # 

        cam = MvCamera()

        # 0

        nSelCamIndex = 0

        # 

        global obj_cam_operation

        obj_cam_operation = CameraOperation(cam, deviceList, nSelCamIndex)

        # 

        ret = MvCamera.MV_CC_EnumDevices(MV_GIGE_DEVICE | MV_USB_DEVICE, deviceList)

        # 

        if ret != MV_OK:

            logging.error(f"{ret}") #  logging.error  print

            return

        # 

        if deviceList.nDeviceNum == 0:

            logging.info("") #  logging.info  print

            return

        # 

        logging.info(f" {deviceList.nDeviceNum} ") #  logging.info  print

        # 

        ret = obj_cam_operation.Open_device()

        # 

        if ret != MV_OK:

            logging.error(f"{ret}") #  logging.error  print

            return

        # 

        self.start_grabbing()

    # 

    def start_grabbing(self):

        if obj_cam_operation is None:

            return MV_E_CALLORDER

        win_id = self.main_window.widgetDisplay.winId()

        # SDKHWND/

        if obj_cam_operation.b_start_grabbing:

            obj_cam_operation.sacn_image = None

            logging.info(f" HWND={win_id}")

            return MV_OK

        # 

        ret = obj_cam_operation.Start_grabbing(win_id)

        # 

        if ret != MV_OK:

            logging.error(f"{ret}")

        else:

            logging.info(f" HWND={win_id}")

    def ensure_camera_display(self):
        """确保主窗口完全显示后平滑校验 HWND 物理窗口句柄，保持相机画面顺畅播放。"""
        try:
            global obj_cam_operation
            if obj_cam_operation is not None and getattr(obj_cam_operation, 'b_open_device', False):
                win_id = int(self.main_window.widgetDisplay.winId())
                obj_cam_operation.n_win_gui_id = win_id
                if not obj_cam_operation.b_start_grabbing:
                    ret = obj_cam_operation.Start_grabbing(win_id)
                    logging.info(f"【摄像机平滑启动抓流】HWND={win_id}, ret={ret}")
                else:
                    if hasattr(obj_cam_operation, "obj_cam") and obj_cam_operation.obj_cam:
                        try:
                            obj_cam_operation.obj_cam.MV_CC_Display(win_id)
                        except Exception:
                            pass
                    logging.info(f"【摄像机抓流保持正常运行】HWND={win_id}")
            else:
                self.hiKInit()
        except Exception as err:
            logging.error(f"校验相机渲染句柄发生异常: {err}")

    def stop_line(self):
        if obj_cam_operation is not None:
            obj_cam_operation.sacn_image = None

    def stop_grabbing(self):

        # 

        if not obj_cam_operation.b_start_grabbing:

            logging.info("") #  logging.info  print

            return MV_E_CALLORDER

        # 

        ret = obj_cam_operation.Stop_grabbing()

        # 

        if ret != MV_OK:

            logging.error(f"{ret}") #  logging.error  print

    # 

    def close_device(self):

        # 

        obj_cam_operation.Close_device()

    # 

    def set_continue_mode(self):

        # False

        ret = obj_cam_operation.Set_trigger_mode(False)

        # 

        if ret != MV_OK:

            logging.error(f"{ret}") #  logging.error  print

    # 

    def set_software_trigger_mode(self):

        # True

        ret = obj_cam_operation.Set_trigger_mode(True)

        # 

        if ret != MV_OK:

            logging.error(f"{ret}") #  logging.error  print

    # 

    def trigger_once(self):

        # 

        ret = obj_cam_operation.Trigger_once()

        # 

        if ret != MV_OK:

            logging.error(f"{ret}") #  logging.error  print

    # BMP

    def save_bmp(self):

        # BMP

        ret = obj_cam_operation.Save_Bmp()

        # BMP

        if ret != MV_OK:

            logging.error(f"BMP{ret}") #  logging.error  print

        else:

            # 

            logging.info("") #  logging.info  print

    # =================================================

    # ========================Style=========================

    # 

    def styleInit(self):

        # 

        self.main_window.setStyleSheet("QMainWindow {background-color: white;}")

        # 

        shadow = QGraphicsDropShadowEffect()




        # groupBox_7

        self.main_window.groupBox_7.setStyleSheet("QGroupBox {background-color: transparent; border: 0px;}")

        # groupBoxgroupBox_2groupBox_3widgetDisplayF2F3F520

        group_boxes = [self.main_window.groupBox, self.main_window.groupBox_2, self.main_window.groupBox_3]

        for group_box in group_boxes:

            group_box.setStyleSheet(

                "QGroupBox { background-color: #F2F3F5; border-radius: 20px; border: 1px solid #797979;}")


        # widgetDisplay

        self.main_window.widgetDisplay.setStyleSheet(

            "background-color: #F2F3F5; border-radius: 20px; border: 1px solid #797979;")

        # SDKwidgetDisplayHWNDQt

        # 

        # label_date#909399

        self.main_window.label_date.setStyleSheet("color: #909399;")

        # label_result_boxlabel_data_unlinelabel_result_box#D9001B

        self.main_window.label_result_box.setStyleSheet("color: #D9001B;")

        self.main_window.label_data_unline.setStyleSheet("color: #D9001B;")

        self.main_window.label_result_case.setStyleSheet("color: #D9001B;")

        # groupBox_4groupBox_5groupBox_620px

        self.main_window.groupBox_4.setStyleSheet("background-color: white; border-radius: 20px;")

        self.main_window.groupBox_5.setStyleSheet("background-color: white; border-radius: 20px;")

        self.main_window.groupBox_6.setStyleSheet("background-color: white; border-radius: 20px;")

        # groupBox_result_1groupBox_result_10

        group_boxes = [

            self.main_window.groupBox_result_1, self.main_window.groupBox_result_2, self.main_window.groupBox_result_3,

            self.main_window.groupBox_result_4, self.main_window.groupBox_result_5, self.main_window.groupBox_result_6,

            self.main_window.groupBox_result_7, self.main_window.groupBox_result_8, self.main_window.groupBox_result_9,

            self.main_window.groupBox_result_10

        ]

        for group_box in group_boxes:

            group_box.setStyleSheet("""

                QGroupBox {

                    background-color: #F2F2F2;

                    border: 1px solid #797979;

                    border-radius: 5px;

                }

            """)

        # taps_3taps_12

        taps_list = [

            self.main_window.taps_3, self.main_window.taps_4, self.main_window.taps_5, self.main_window.taps_6,

            self.main_window.taps_7,

            self.main_window.taps_8, self.main_window.taps_9, self.main_window.taps_10, self.main_window.taps_11,

            self.main_window.taps_12

        ]

        for tap in taps_list:

            tap.setStyleSheet("""

                QLabel {

                    background-color: white;

                    border: 3px solid #797979;

                    border-radius: 20px;

                    color: #797979;

                }

            """)

        #  groupBox_box_0  groupBox_box_10 

        group_boxes = [

            self.main_window.groupBox_box_1, self.main_window.groupBox_box_2,

            self.main_window.groupBox_box_3,

            self.main_window.groupBox_box_4, self.main_window.groupBox_box_5,

            self.main_window.groupBox_box_6,

            self.main_window.groupBox_box_7, self.main_window.groupBox_box_8,

            self.main_window.groupBox_box_9,

            self.main_window.groupBox_box_10, self.main_window.groupBox_box_0

        ]

        for group_box in group_boxes:

            group_box.setStyleSheet("""

                            QGroupBox {

                                background-color: #F2F2F2;

                                border: 1px solid #797979;

                                border-radius: 5px;

                                color: #333333

                            }

                        """)

        #  taps_21  taps_29 

        taps_list = [

            self.main_window.taps_21, self.main_window.taps_22, self.main_window.taps_23, self.main_window.taps_24,

            self.main_window.taps_25,

            self.main_window.taps_26, self.main_window.taps_27, self.main_window.taps_28, self.main_window.taps_29,

            self.main_window.taps_30

        ]

        for tap in taps_list:

            tap.setStyleSheet("""

                        QLabel {

                            background-color: white;

                            border: 3px solid #333333;

                            border-radius: 20px;

                            color: #333333;

                        }

                    """)
