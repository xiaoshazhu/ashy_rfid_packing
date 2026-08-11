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

            # 

            # 

            controller.set_output_enabled_direct(False)

            time.sleep(0.25)

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

            logging.info(


                f"WDIP补光灯已开启，启动电压={startup_voltage:.2f}V"

            )

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

        #

        self.pageData['label_data_box'] = 0

        self.pageData['label_data_case'] = 0

        # 

        self.updatePage()

    def reset_data(self):

        # 

        self._recognition_sequence_active = False

        self._recognition_best_result = []

        self._recognition_best_boxes = None

        self.clear_recognition_boxes()

        self.sacn_box_data = None # 

        self.pending_box_scans = []

        self._last_bundle_staged = False

        self.preview_case_code = None # 

        self.case = None # 

        self.scan_case_data = [] #   

        config.setConfig({"caseData": self.scan_case_data})

        config.setConfig({"caseCode": self.case})

        # 

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
                # 1. 停止相机抓图并彻底关闭/释放海康相机设备连接
                logging.info("重启清理：正在停止相机抓图并释放设备资源...")
                try:
                    self.stop_grabbing()
                    self.close_device()
                except Exception as cam_err:
                    logging.warning(f"重启时释放相机资源异常: {cam_err}")

                # 2. 关闭补光灯输出
                if not self.shutdown_light_output():
                    logging.warning("WDIP补光灯关闭失败，重启前请确认串口未被厂家软件占用")

                logging.info(f"正在重启程序: {python_executable} {main_script_path}")
                import subprocess
                # 给予底层硬件 SDK 0.5秒缓冲时间彻底释放网络/USB句柄
                QtCore.QThread.msleep(500)
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

    def on_button_again(self):

        #  (10/10 )

        max_xiang = int(CONFIG_DATA.get('edit_max_xiang', 10))

        if len(self.scan_case_data) >= max_xiang:

            logging.info(f"当前箱已达到最大上限：{max_xiang}/{max_xiang}捆")

            QtWidgets.QMessageBox.warning(

                self.main_window,

                "装箱已满",
                f"当前箱已达到 {max_xiang}/{max_xiang} 捆。\n请先打印箱码或点击重新装箱，再继续扫描。",

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

        QTimer.singleShot(150, lambda: self._run_recognition_attempt(1))

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

            150,

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

            self.sacn_box_data = recognized

            expected_boxes = int(CONFIG_DATA.get("edit_max_jian", 10))

            remaining = max(0, expected_boxes - len(self.pending_box_scans))

            newly_recognized = [dict(item) for item in recognized[:remaining]]

            self.pending_box_scans.extend(newly_recognized)

            self.sacn_box_data = [dict(item) for item in self.pending_box_scans]

            self.scan_code(len(self.sacn_box_data))

            logging.info(



                ""

            )

            if len(self.sacn_box_data) == expected_boxes:

                self.stage_recognized_bundle()

                current_bundles = len(self.scan_case_data)

                max_bundles = int(CONFIG_DATA.get("edit_max_xiang", 10))

                self.show_temporary_tooltip(
                    self.main_window.groupBox_7,
                    "【10/10盒识别成功】",
                    f"本组真实识别到 {expected_boxes} 盒，已计入第 {current_bundles}/{max_bundles} 捆装箱进度。",
                )

                self.main_window.play_success()

            else:

                self.show_temporary_tooltip(
                    self.main_window.groupBox_7,
                    "【识别成功】",
                    f"本次识别到 {len(self.sacn_box_data)}/{expected_boxes} 个真实盒码，请继续扫描。",
                )

                self.main_window.play_success()

            return

        self.sacn_box_data = (

            [dict(item) for item in self.pending_box_scans]

            if self.pending_box_scans else None

        )

        self.scan_code(len(self.pending_box_scans))

        logging.info("2")

        self.show_temporary_tooltip(
            self.main_window.groupBox_7,
            "【识别失败】",
            "当前画面未识别到完整盒码，请调整摆放方向、反光和焦距。",
        )

        self.main_window.play_warning()

    def stage_recognized_bundle(self):

        expected_boxes = int(CONFIG_DATA.get("edit_max_jian", 10))

        max_bundles = int(CONFIG_DATA.get("edit_max_xiang", 10))

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

                    # 如果已经在历史表中（说明之前已经成功上传过），绝不重复上传
                    if db.is_uploaded(cid):
                        logging.info(f"盒码 ID: {cid} 已在历史记录中（已上传），跳过重复上传。")
                        continue

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
                    db.box_case_insert_data(data)
                    if (
                        getattr(self.main_window, "client", None)
                        and getattr(self.main_window, "loop", None)
                        and self.main_window.client.get_connection_status()
                    ):
                        try:
                            asyncio.run_coroutine_threadsafe(self.main_window.client.send(data), self.main_window.loop)
                            logging.info(f"扫码数据实时推送到 WS 成功 (仅推送一次), ID: {cid}")
                        except Exception as ws_err:
                            logging.error(f"WS 数据实时推送异常: {ws_err}")
        except Exception as db_err:
            logging.error(f"扫码数据落库或推送发生错误: {db_err}")

        logging.info(


            "本次真实识别结果已计入装箱进度。"

        )

        self.show_temporary_tooltip(
            self.main_window.groupBox_7,
            "【装箱进度已更新】",
            f"已完成一捆真实盒码识别，当前装箱进度：{len(self.scan_case_data)}/{max_bundles}捆。",
        )

        self.main_window.play_success()

        self._last_bundle_staged = True

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

        logging.info("")

        self._recognition_sequence_active = False

        self._recognition_best_result = []

        self._recognition_best_boxes = None

        self.clear_recognition_boxes()

        self.pending_box_scans = []

        self.sacn_box_data = None

        self._last_bundle_staged = False

        if self.case is None:

            self.preview_case_code = None

        self.isPrint = False

        self.scan_code_end()

        self.stop_line()

        # 

        if obj_cam_operation is None or not obj_cam_operation.b_open_device:

            logging.warning("")

            self.hiKInit()

        else:

            self.ensure_camera_display()

        logging.info("")

        try:

            self.show_temporary_tooltip(
                self.main_window.groupBox_7,
                "【设备复位成功】",
                "相机预览与未录入识别结果已复位。",
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

    def update_progress_bar_slot(self, percen):  # 

        self.main_window.pushButton.setText(f"上传进度 {percen}%")

        if percen >= 100:

            self.main_window.pushButton.setText(f"")

            self.main_window.pushButton.setEnabled(True)  # 

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

        # n/s

        # label_result_box

        expected_boxes = int(CONFIG_DATA.get("edit_max_jian", 10))
        current_boxes = max(0, min(int(num), expected_boxes))
        self.main_window.label_result_box.setText(f"【{current_boxes}/{expected_boxes}盒】")

        # groupBox

        group_boxes = [

            self.main_window.groupBox_result_1, self.main_window.groupBox_result_2,

            self.main_window.groupBox_result_3, self.main_window.groupBox_result_4,

            self.main_window.groupBox_result_5, self.main_window.groupBox_result_6,

            self.main_window.groupBox_result_7, self.main_window.groupBox_result_8,

            self.main_window.groupBox_result_9, self.main_window.groupBox_result_10

        ]

        # groupBox

        for i, group_box in enumerate(group_boxes, start=1):

            if i <= num:

                group_box.setStyleSheet(

                    "QGroupBox { background-color: #CAF982; border: 1px solid #797979; border-radius: 5px; }")

            else:

                group_box.setStyleSheet(

                    "QGroupBox { background-color: #EC808D; border: 1px solid #797979; border-radius: 5px; }")

    def scan_code_end(self):

        # n/s

        # label_result_box

        self.scan_code(0)

        # groupBox

        group_boxes = [

            self.main_window.groupBox_result_1, self.main_window.groupBox_result_2,

            self.main_window.groupBox_result_3, self.main_window.groupBox_result_4,

            self.main_window.groupBox_result_5, self.main_window.groupBox_result_6,

            self.main_window.groupBox_result_7, self.main_window.groupBox_result_8,

            self.main_window.groupBox_result_9, self.main_window.groupBox_result_10

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

    # 

    def scan_case(self):

        num = len(self.scan_case_data) | 0

        # n/s

        # label_result_box

        expected_bundles = int(CONFIG_DATA.get("edit_max_xiang", 10))
        current_bundles = max(0, min(num, expected_bundles))
        self.main_window.label_result_case.setText(f"【{current_bundles}/{expected_bundles}捆】")

        # groupBox

        group_boxes = [

            self.main_window.groupBox_box_1, self.main_window.groupBox_box_2,

            self.main_window.groupBox_box_3, self.main_window.groupBox_box_4,

            self.main_window.groupBox_box_5, self.main_window.groupBox_box_6,

            self.main_window.groupBox_box_7, self.main_window.groupBox_box_8,

            self.main_window.groupBox_box_9, self.main_window.groupBox_box_10

        ]

        # groupBox

        for i, group_box in enumerate(group_boxes, start=1):

            if i <= num:

                group_box.setStyleSheet(

                    "QGroupBox { background-color: #CAF982; border: 1px solid #797979; border-radius: 5px; }")

            else:

                group_box.setStyleSheet(

                    "QGroupBox { background-color: #EC808D; border: 1px solid #797979; border-radius: 5px; }")

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
