# home.py
# 导入PySide6相关模块，用于GUI开发
import datetime
import sys
import threading
import time
import asyncio
import logging # 导入 logging 模块

from PySide6.QtWidgets import QToolTip
from PySide6.QtGui import QFont
from PySide6.QtGui import QColor
from PySide6 import QtWidgets, QtCore
from PySide6.QtWidgets import QGraphicsDropShadowEffect

# 导入海康相机操作类和常量
from hikUtils.CamOperation_class import CameraOperation
from hikUtils.MvImport.CameraParams_const import MV_GIGE_DEVICE, MV_USB_DEVICE
from hikUtils.MvImport.CameraParams_header import MV_CC_DEVICE_INFO_LIST
from hikUtils.MvImport.MvCameraControl_class import MvCamera
from hikUtils.MvImport.MvErrorDefine_const import MV_OK, MV_E_CALLORDER
import os  # 引入 os 模块

from page import setting, config
from page.config import CONFIG_DATA
from page.log import LogDialog
# 导入UI设计文件
from qtDesigner.qt_setting import Ui_form_settings
from utils.Utils import extract_path_after_domain
from utils.printUtils import print_barcode

from utils.pyzbar_utils import process_image
from PySide6.QtCore import QTimer, QDateTime
from utils.SQLite import Database
from utils.upload_data_worker_thread import UploadDataWorkerThread

from page.light_control_dialog import LightControlDialog
from page.print_template_dialog import PrintTemplateDialog

# 定义全局相机操作对象 (在 Home 类外部)
obj_cam_operation = None
# 主页类
class Home:
    # 类初始化方法
    def __init__(self, main_window):
        # 初始化主窗口变量
        self.log_dialog = None #日志窗口是否被打开
        self.light_dialog = None
        self.template_dialog = None
        self.timer = None  # 时间钟
        self.isPrint = None  # 是否正在打印箱码

        self.sacn_box_data = None  # 存储扫描的临时数据 整捆
        self.pageData = {
            'label_data_box': 0,  # 已识别 盒
            'label_data_case': 0,  # 已识别 箱
            'label_data_unline': 0,  # 未上传数据
        }
        self.scan_case_data = []  # 存储扫描的临时数据 整箱
        self.case = None  # 箱码
        self.main_window = main_window

        # 调用样式初始化、事件初始化和海康相机初始化方法
        self.styleInit()
        self.eventInit()
        self.hiKInit()
        self.pageInit()
        self.setup_manual_operation_pagination()
        self.autoPageData()#自动更新未上传数据
        # 实时显示时间
        # 创建定时器
        self.timer = QTimer(self.main_window)
        # 设置定时器超时连接到update_time槽函数
        self.timer.timeout.connect(self.update_time)
        # 设置定时器间隔（1000毫秒 = 1秒）
        self.timer.start(1000)




    # 添加更新时间的槽函数
    def update_time(self):
        # 获取当前的日期和时间
        current_time = QDateTime.currentDateTime()
        # 设置label_date的文本为当前时间
        self.main_window.label_date.setText(current_time.toString("yyyy年MM月dd日 hh:mm:ss"))

    def eventInit(self):
        # 连接事件处理函数
        self.main_window.button_ok.clicked.connect(self.force_ok_clicked)  # 确认录入
        self.main_window.button_cancel.clicked.connect(self.on_button_cancel_clicked)  # 初始化
        self.main_window.button_setting.clicked.connect(self.open_settings)  # 设置
        self.main_window.button_print.clicked.connect(self.on_button_print)  # 打印箱码
        self.main_window.button_again.clicked.connect(self.on_button_again)  # 手动识别
        self.main_window.pushButton.clicked.connect(self.manualUpdateData)  # 手动上传数据
        self.main_window.label_clear.clicked.connect(self.clear_page_data) # 清空统计
        self.main_window.button_logs.clicked.connect(self.show_log_dialog) # 日志
        self.main_window.button_Restart.clicked.connect(self.restart_app)  # 重启程序
        self.main_window.button_reset.clicked.connect(self.reset_data)  # 重置数据

    def setup_manual_operation_pagination(self):
        """配置左下角【手动操作/手动设置】区域 (self.main_window.groupBox) 的 2 页切换"""
        group_box = getattr(self.main_window, "groupBox", None)
        if not group_box:
            return

        if getattr(self, "_manual_page_stack", None):
            return

        # 与‘计数归零’完全一致的 UI 原生渐变按钮样式
        native_btn_style = (
            "QPushButton { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #F8F8F8, stop:1 #E0E0E0); "
            "border: 1px solid #707070; border-radius: 2px; font-weight: bold; color: #000; min-height: 28px; font-size: 13px; } "
            "QPushButton:hover { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #FFFFFF, stop:1 #D8D8D8); border-color: #505050; } "
            "QPushButton:pressed { background: #D0D0D0; border-color: #404040; }"
        )

        # 1. 调整原有的 self.taps_1 标题对象宽度 (10, 7, 85, 23)，支持在‘手动操作’与‘手动设置’间无缝切换
        self.taps_1 = getattr(self.main_window, "taps_1", None)
        if self.taps_1:
            self.taps_1.setGeometry(10, 7, 85, 23)
            font_title = self.taps_1.font()
            font_title.setPointSize(13)
            font_title.setBold(True)
            self.taps_1.setFont(font_title)
            self.taps_1.setText("手动操作")

        # 2. 在标题右侧紧凑无缝排列‘上一页’与‘下一页’双按钮 (绝对不重叠遮挡标题)
        self.btn_prev_page = QtWidgets.QPushButton("◀ 上一页", group_box)
        self.btn_prev_page.setGeometry(98, 5, 54, 24)
        self.btn_prev_page.clicked.connect(self.goto_prev_manual_page)
        self.btn_prev_page.show()

        self.btn_next_page = QtWidgets.QPushButton("下一页 ▶", group_box)
        self.btn_next_page.setGeometry(155, 5, 54, 24)
        self.btn_next_page.clicked.connect(self.goto_next_manual_page)
        self.btn_next_page.show()

        # 3. 获取 4 个原始按钮 (button_cancel 是 设备复位)
        btn_cancel = getattr(self.main_window, "button_cancel", None) # 设备复位
        btn_ok = getattr(self.main_window, "button_ok", None)         # 确认录入
        btn_again = getattr(self.main_window, "button_again", None)   # 手动识别
        btn_print = getattr(self.main_window, "button_print", None)   # 打印箱码

        for b in [btn_cancel, btn_ok, btn_again, btn_print]:
            if b:
                b.setStyleSheet(native_btn_style)

        # 4. 创建第 2 页的 3 个新功能按钮控件
        self.button_print_template = QtWidgets.QPushButton("打印模板")
        self.button_light_control = QtWidgets.QPushButton("亮度控制")
        self.button_light_calibrate = QtWidgets.QPushButton("亮度校准")

        for b in [self.button_print_template, self.button_light_control, self.button_light_calibrate]:
            b.setStyleSheet(native_btn_style)

        self.button_print_template.clicked.connect(self.open_print_template_dialog)
        self.button_light_control.clicked.connect(self.open_light_control_dialog)
        self.button_light_calibrate.clicked.connect(self.on_light_calibrate_clicked)

        # 5. 构建 2 页 StackedWidget
        self._manual_page_stack = QtWidgets.QStackedWidget(group_box)
        self._manual_page_stack.setGeometry(10, 42, 200, 95)

        # 第 1 页 (手动操作: 设备复位, 确认录入, 手动识别, 打印箱码)
        page1 = QtWidgets.QWidget()
        grid1 = QtWidgets.QGridLayout(page1)
        grid1.setContentsMargins(0, 0, 0, 0)
        grid1.setHorizontalSpacing(10)
        grid1.setVerticalSpacing(8)
        if btn_cancel: grid1.addWidget(btn_cancel, 0, 0)
        if btn_ok: grid1.addWidget(btn_ok, 0, 1)
        if btn_again: grid1.addWidget(btn_again, 1, 0)
        if btn_print: grid1.addWidget(btn_print, 1, 1)

        # 第 2 页 (手动设置: 打印模板, 亮度控制, 亮度校准，右下留空)
        page2 = QtWidgets.QWidget()
        grid2 = QtWidgets.QGridLayout(page2)
        grid2.setContentsMargins(0, 0, 0, 0)
        grid2.setHorizontalSpacing(10)
        grid2.setVerticalSpacing(8)
        grid2.addWidget(self.button_print_template, 0, 0)
        grid2.addWidget(self.button_light_control, 0, 1)
        grid2.addWidget(self.button_light_calibrate, 1, 0)

        self._manual_page_stack.addWidget(page1)
        self._manual_page_stack.addWidget(page2)
        self._manual_page_stack.show()

        # 初始高亮状态刷新
        self.update_manual_page_buttons_style()

    def update_manual_page_buttons_style(self):
        """刷新‘上一页/下一页’的灰亮高亮状态与‘手动操作/手动设置’标题切换"""
        curr = self._manual_page_stack.currentIndex()

        active_btn_style = (
            "QPushButton { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #FFFFFF, stop:1 #D0D0D0); "
            "border: 1px solid #505050; border-radius: 2px; font-weight: bold; color: #000; font-size: 11px; padding: 2px 4px; } "
            "QPushButton:hover { background: #E5E5E5; }"
        )

        disabled_btn_style = (
            "QPushButton { background: #F0F0F0; border: 1px solid #C5C5C5; border-radius: 2px; color: #959595; font-size: 11px; padding: 2px 4px; }"
        )

        if curr == 0:
            if self.taps_1:
                self.taps_1.setText("手动操作")
            self.btn_prev_page.setEnabled(False)
            self.btn_prev_page.setStyleSheet(disabled_btn_style)
            self.btn_next_page.setEnabled(True)
            self.btn_next_page.setStyleSheet(active_btn_style)
        else:
            if self.taps_1:
                self.taps_1.setText("手动设置")
            self.btn_prev_page.setEnabled(True)
            self.btn_prev_page.setStyleSheet(active_btn_style)
            self.btn_next_page.setEnabled(False)
            self.btn_next_page.setStyleSheet(disabled_btn_style)

    def goto_prev_manual_page(self):
        curr = self._manual_page_stack.currentIndex()
        if curr > 0:
            self._manual_page_stack.setCurrentIndex(curr - 1)
            self.update_manual_page_buttons_style()

    def goto_next_manual_page(self):
        curr = self._manual_page_stack.currentIndex()
        if curr < self._manual_page_stack.count() - 1:
            self._manual_page_stack.setCurrentIndex(curr + 1)
            self.update_manual_page_buttons_style()

    def open_light_control_dialog(self):
        """打开【亮度控制与二分法调光】弹窗"""
        if not self.light_dialog:
            self.light_dialog = LightControlDialog(self, parent=self.main_window)
        self.light_dialog.load_current_camera_brightness()
        self.light_dialog.exec_()

    def on_light_calibrate_clicked(self):
        """主界面左下角第 2 页【亮度校准】按钮触发"""
        if not self.light_dialog:
            self.light_dialog = LightControlDialog(self, parent=self.main_window)
        self.light_dialog.on_calibrate_clicked()

    def open_print_template_dialog(self):
        """打开【打印模板管理】弹窗"""
        if not self.template_dialog:
            self.template_dialog = PrintTemplateDialog(config_path="config/settings.json", parent=self.main_window)
        self.template_dialog.load_elements_config()
        self.template_dialog.populate_table()
        self.template_dialog.exec_()

    def pageInit(self):
        #  读取缓存的信息 将缓存的信息存入到对应的对象
        # 统计数据
        if CONFIG_DATA['pageData'] is not None and len(CONFIG_DATA['pageData']) > 0:
            self.pageData = CONFIG_DATA['pageData']
        # 装箱进度
        if CONFIG_DATA['caseData'] is not None and len(CONFIG_DATA['caseData']) > 0:
            self.scan_case_data = CONFIG_DATA['caseData']
            # 更新扫码的页面
            self.scan_case()
        # 箱码
        if CONFIG_DATA['caseCode'] is not None:
            self.updataPageCase(CONFIG_DATA['caseCode'])
        #  更新数据统计的信息
        self.updatePage()

    def clear_page_data(self):
        #清除箱码以及盒码的计数统计
        self.pageData['label_data_box'] = 0
        self.pageData['label_data_case'] = 0
        # 更新页面数据
        self.updatePage()

    def reset_data(self):
        # 清除箱码盒马 装箱进度
        self.sacn_box_data = None #重置 扫码临时数据
        self.case = None #重置 当前操作的箱码
        self.scan_case_data = [] # 重置 当前正在扫码的 箱码的绑定记录
        config.setConfig({"caseData": self.scan_case_data})
        config.setConfig({"caseCode": self.case})
        # 更新页面显示
        self.scan_code(0)
        self.scan_code_end()
        self.scan_case()
        self.scan_case_end()
        self.updataPageCase(None)
        try:
            self.show_temporary_tooltip(self.main_window.groupBox_7, "【重新装箱成功】", "已清空箱码、当前装箱进度及盒码")
            self.main_window.play_warning()
        except Exception:
            pass

    def restart_app(self):
        """重启程序 (带确认弹窗)"""
        reply = QtWidgets.QMessageBox.question(
            self.main_window,  # 使用 self.main_window 作为父窗口 (假设您的主窗口实例是 self.main_window)
            "重启确认",  # 对话框标题
            "确定要重启程序吗?",  # 对话框内容
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,  # 按钮类型: Yes 和 No
            QtWidgets.QMessageBox.No  # 默认选中的按钮: No (取消)
        )

        if reply == QtWidgets.QMessageBox.Yes:  # 如果用户点击了 "Yes" 按钮
            python_executable = sys.executable  # 获取 Python 解释器路径
            # 正确获取主程序入口 main.py 的绝对路径，修复之前指向 home.py 导致的重启失败问题
            current_dir = os.path.dirname(os.path.abspath(__file__))  # Desktop_QR_Send/page
            main_script_path = os.path.abspath(os.path.join(current_dir, "..", "main.py"))  # Desktop_QR_Send/main.py
            if not os.path.exists(main_script_path):
                main_script_path = os.path.abspath(sys.argv[0])

            try:
                logging.info(f"正在重启程序: {python_executable} {main_script_path}")
                os.execv(python_executable, [python_executable, main_script_path])  # 使用 execv 重启
            except OSError as e:
                QtWidgets.QMessageBox.critical(self.main_window, "错误", f"重启程序失败: {e}")
                logging.error(f"重启程序失败: {e}") # 使用 logging.error 替换 print
        else:
            # 如果用户点击 "No" 或关闭对话框，则不执行重启操作，可以在这里添加一些取消操作后的提示信息 (可选)
            pass  # 或者直接 pass，不执行任何操作


    def show_log_dialog(self):
        """显示日志弹窗"""
        if not self.log_dialog:  # 如果 log_dialog 还没有被创建，则创建
            self.log_dialog = LogDialog(self.main_window)  # 传递 self (MainWindow) 作为 parent
        self.log_dialog.show()  # 显示弹窗
        self.log_dialog.raise_()  # 将弹窗置于顶层并给予焦点 (可选)
        self.log_dialog.activateWindow()  # 激活窗口 (可选)

    def on_button_again(self):
        # 先判断是否有箱码，测试模式下若无箱码自动生成一个
        if self.case is None:
            self.updataPageCase(self.generate_case_code())

        # 检查是否已达到满箱上限 (10/10 捆)
        max_jian = int(CONFIG_DATA.get('edit_max_jian', 10))
        if len(self.scan_case_data) >= max_jian:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self.main_window, "装箱已满", f"【当前箱已满额 {max_jian}/{max_jian} 捆】\n无法继续添加！请先点击[重置]或重新[打印箱码]以开启新一箱！")
            return

        logging.info("手动识别/拍照识别被触发 (硬件解包与测试模拟)") # 使用 logging.info 替换 print
        if obj_cam_operation and obj_cam_operation.sacn_image is not None:
            self.stop_line()
            time.sleep(0.1)

        # 1. 尝试抓取真实相机画面并解包
        self.capture_and_save_image()

        # 2. 如果画面无真实条码 (sacn_box_data 为空)，充入测试盒码数据与 1 捆装箱进度供测试
        if self.sacn_box_data is None:
            logging.info("【测试模拟】镜头前无真实条码，自动充入 6 盒测试盒码与 1 捆装箱进度")
            stamp = int(time.time() * 1000)
            mock_codes = [
                {'data': f'http://gya.sales.yiknet.com/scan/box_{stamp}_{i}', 'type': 'QRCODE'}
                for i in range(1, 7)
            ]
            self.sacn_box_data = mock_codes
            self.scan_code(6)
            self.on_button_ok_clicked(force=True)

    def force_ok_clicked(self):
        self.on_button_ok_clicked(True)#强制录入数据

    def on_button_ok_clicked(self,force = False):
        # 数据录入
        logging.info("数据录入按钮被点击了。") # 使用 logging.info 替换 print
        # 检查是否已达到满箱上限 (10/10 捆)，防止 11/10 溢出
        max_jian = int(CONFIG_DATA.get('edit_max_jian', 10))
        if len(self.scan_case_data) >= max_jian:
            logging.info(f"当前箱已满额: {len(self.scan_case_data)}/{max_jian}")
            self.show_temporary_tooltip(self.main_window.groupBox_7, '【装箱已满】', f'当前箱已达到最大上限【{max_jian}/{max_jian}捆】，请重置或打印新箱码。')
            self.main_window.play_warning()
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self.main_window, "装箱已满", f"【当前箱已满额 {max_jian}/{max_jian} 捆】\n无法继续添加！请先点击[重置]或重新[打印箱码]以开启下一箱！")
            return

        # 判断是否有数据识别
        if self.sacn_box_data is None:
            logging.info("没有识别盒码。") # 使用 logging.info 替换 print
            self.show_temporary_tooltip(self.main_window.groupBox_7, '【无效盒码】', '请先扫描盒码。')
            # 扫码失败提示音
            self.main_window.play_warning()
            return
        # 判断是否有箱码
        if self.case is None:
            logging.info("没有箱码。") # 使用 logging.info 替换 print
            self.show_temporary_tooltip(self.main_window.groupBox_7, '【无法录入】', '请先打印箱码。')
            # 扫码失败提示音
            self.main_window.play_warning()
            return
        # 判断数据是否符合规定
        max_jian = int(CONFIG_DATA['edit_max_jian'])
        if len(self.sacn_box_data) == max_jian or force:
            # 判断云端API是否在线
            if self.main_window.client and self.main_window.client.connected:
                # 将数据上传到云端
                logging.info("将数据上传到云端") # 使用 logging.info 替换 print
                db = Database()
                for i, sacn_box_data in enumerate(self.sacn_box_data, start=1):
                    boxContent = sacn_box_data['data']
                    # # 判断盒码是否重复
                    # for j, box in self.scan_case_data:
                    #     if box['boxContent'] == boxContent:
                    #         # 扫码重复
                    #         logging.warning(f"扫码重复")
                    #         self.show_temporary_tooltip(self.main_window.groupBox_7, '【无法录入】', '扫码重复。')
                    # # 扫码失败提示音
                    # self.main_window.play_warning()
                    #         return
                    data = {
                        'id': extract_path_after_domain(boxContent),
                        'caseContent': self.case,
                        'boxContent': boxContent,
                        'type': '生产装箱',
                        'createTime': datetime.datetime.now(),
                        'isLine': 0
                    }

                    db.box_case_insert_data(data)#数据存储到本地数据库
                    try:
                        future = asyncio.run_coroutine_threadsafe(self.main_window.client.send(data), self.main_window.loop)
                    except Exception as e:
                        logging.error(f"调用消息出错: {e}") # 使用 logging.error 替换 print
            else:
              #云端API不在线将数据存储到记录里
              # 将数据存入到数据库
              logging.info("将数据存入到数据库") # 使用 logging.info 替换 print
              db = Database()
              for i, sacn_box_data in enumerate(self.sacn_box_data, start=1):
                  boxContent = sacn_box_data['data']
                  # # 判断盒码是否重复
                  # for j, box in self.scan_case_data:
                  #     if box['boxContent'] == boxContent:
                  #         # 扫码重复
                  #         logging.warning(f"扫码重复")
                  #         self.show_temporary_tooltip(self.main_window.groupBox_7, '【无法录入】', '扫码重复。')
                  # # 扫码失败提示音
                  # self.main_window.play_warning()
                  #         return
                  data = {
                      'id': extract_path_after_domain(boxContent),
                      'caseContent': self.case,
                      'boxContent': boxContent,
                      'type': '生产装箱',
                      'createTime': datetime.datetime.now(),
                      'isLine': 0
                  }
                  db.box_case_insert_data(data)#数据存储到本地数据库

            # 扫码成功提示音
            self.main_window.play_success()
            # 数据插入完成
            self.pageData['label_data_box'] += len(self.sacn_box_data)
            # 更新临时识别的存储数据
            item = {'boxContents': self.sacn_box_data}
            self.scan_case_data.append(item)
            # 更新扫码临时数据
            self.sacn_box_data = None
            self.scan_code_end()

            if len(self.scan_case_data) >= max_jian:
                self.show_temporary_tooltip(self.main_window.groupBox_7, '【提示】', '请注意打印箱码')
            # # 判断一箱有没有装满
            # if len(self.scan_case_data) == max_jian:
            #     # 计数+1
            #     self.pageData['label_data_case'] += 1
            #     # 恢复临时数据
            #     self.scan_case_data = []
            #     # 恢复装箱进度
            #     self.scan_case_end()
            #     # 重新生成箱码
            #     self.on_button_print()
            # else:
            #     # 更新装箱进度
            #     self.scan_case()
            #更新装箱进度
            self.scan_case()
            # 更新页面数据
            self.updatePage()

        else:
            # 不符合规定，弹窗提示
            logging.info("弹窗开启") # 使用 logging.info 替换 print
            # 不符合规定，显示悬浮提示
            self.show_temporary_tooltip(self.main_window.groupBox_7, '【无法录入】', '数据不符合标准。')
            # 扫码失败提示音
            self.main_window.play_warning()

    # 提示方法
    def show_temporary_tooltip(self, widget, title, message):
        QToolTip.setFont(QFont('SansSerif', 26))
        # 计算提示显示的位置，这里我们选择在窗口中心显示
        pos = widget.rect().center()
        global_pos = widget.mapToGlobal(pos)
        QToolTip.showText(global_pos,
                          "<div style='text-align: center'>" + title + "</div>" + "<div style='text-align: center'>" + message + "</div>",
                          widget, widget.rect(), 3000)

    def on_button_cancel_clicked(self):
        # 初始化
        logging.info("还原初始化") # 使用 logging.info 替换 print
        # 关闭相机流
        self.stop_grabbing()
        # 关闭相机
        self.close_device()
        # 相机初始化
        self.hiKInit()
        self.scan_code_end()  # 显示的内容
        self.sacn_box_data = None  # 扫描的临时数据
        self.isPrint = False  # 打印机状态恢复
        self.scan_code_end()  # 扫码识别结果恢复
        self.stop_line()  # 画面显示实时画面
        logging.info("复位结束") # 使用 logging.info 替换 print
        try:
            self.show_temporary_tooltip(self.main_window.groupBox_7, "【设备复位成功】", "相机预览与未录入识别结果已复位")
            self.main_window.play_warning()
        except Exception:
            pass

    def open_settings(self):
        # 打开设置窗口
        settings_dialog = QtWidgets.QDialog(self.main_window)
        settings_dialog.setWindowModality(QtCore.Qt.WindowModal)

        settings_ui = Ui_form_settings()  # 创建UI对象
        settings_ui.setupUi(settings_dialog)  # 设置UI
        seetings = setting.Setting(settings_ui, settings_dialog)
        seetings.settingInit()
        settings_dialog.exec_()  # 显示窗口

    # 更新页面数据
    def updatePage(self):
        self.main_window.label_data_box.setText(f"{self.pageData['label_data_box']}")
        self.main_window.label_data_case.setText(f"{self.pageData['label_data_case']}")
        self.main_window.label_data_unline.setText(f"{self.pageData['label_data_unline']}")
        config.setConfig({"pageData": self.pageData})
        config.setConfig({"caseData": self.scan_case_data})
        config.setConfig({"caseCode": self.case})

    @QtCore.Slot(float)
    def update_progress_bar_slot(self, percen):  # 槽函数，接收进度百分比
        self.main_window.pushButton.setText(f"数据上传中...【{percen}%】！！请勿做其他操作！！")
        if percen >= 100:
            self.main_window.pushButton.setText(f"手动数据上传")
            self.main_window.pushButton.setEnabled(True)  # 上传完成后，重新启用按钮

    # 点击按钮触发手动上传数据
    def manualUpdateData(self):
        if self.main_window.client and self.main_window.client.connected:
            self.main_window.pushButton.setEnabled(False)  # 禁用按钮 (主线程 UI 操作)

            max_limit = 10000
            # 创建并启动工作线程 (在主线程中)
            self.upload_worker_thread = UploadDataWorkerThread(self.main_window, max_limit)  # 创建工作线程实例，传递 main_window 和 max_limit
            self.upload_worker_thread.update_progress_signal.connect(self.update_progress_bar_slot)  # 连接信号和槽
            self.upload_worker_thread.start()  # 启动工作线程，开始后台任务
        else:
            self.show_temporary_tooltip(self.main_window.groupBox_7, '【无法上传】', '无连接到服务器')


# 线程自动查询数据库 更新页面数据（未上传的数据）
    def autoPageData(self):
        periodic_thread = threading.Thread(target=self.periodic_task)
        periodic_thread.daemon = True  # 设置为守护线程，主线程退出时子线程也会退出 (可选)
        periodic_thread.start()

    def periodic_task(self):
        """
        定时执行的任务函数
        """

        while True:
            # 初始化数据库
            database = Database()
            label_data_unline = int(database.box_case_count_unuploaded())
            pageData = config.CONFIG_DATA["pageData"]
            if  pageData['label_data_unline'] != label_data_unline:
                pageData['label_data_unline'] = label_data_unline
                config.setConfig({"pageData": pageData})
                self.main_window.label_data_unline.setText(f"{pageData['label_data_unline']}")
            time.sleep(5)  # 每 5 秒执行一次



    # ========================图片解析代码开始=========================
    # 拍照并保存图片
    def capture_and_save_image(self):
        # 确保相机已经开始推流
        if not obj_cam_operation.b_start_grabbing:
            logging.info("相机尚未开始推流") # 使用 logging.info 替换 print
            return
        # 获取图像数据
        if obj_cam_operation.buf_save_image is None:
            logging.info("没有图像数据") # 使用 logging.info 替换 print
            return

        np_array_image = obj_cam_operation.get_np_array_image()

        # 调用pyzbar_utils中的process_image方法处理图像
        process_image(self, obj_cam_operation, np_array_image)

    # ========================图片解析代码结束=========================

    # =======================打印箱码开始=========================
    # 打印一个箱码
    def on_button_print(self):
        # 判断是否正在打印
        if self.isPrint:
            logging.info("正在打印") # 使用 logging.info 替换 print
            return
        # 判断箱码是否已经存在
        if self.case:
            logging.info("箱码已经存在，重新打印箱码") # 使用 logging.info 替换 print
            # 恢复识别结果
            self.sacn_box_data = None
            self.scan_code_end()
            # 恢复装箱进度
            self.scan_case_data = []
            self.scan_case_end()
            # 回复缓存的内容
            config.setConfig({"caseData": self.scan_case_data})

        self.isPrint = True  # 改变打印状态
        # 生成一个箱码
        case_code = self.generate_case_code()
        # 存储箱码
        db = Database()
        db.case_insert_data(case_code)
        # 打印箱码
        try:
            self.print_barcode(case_code)
        except Exception as exc:
            logging.warning(f"打印机通信异常 (可正常展示可视化箱码): {exc}")

        self.isPrint = False  # 改变打印状态
        # 更新箱码
        self.updataPageCase(case_code)
        try:
            self.show_temporary_tooltip(self.main_window.groupBox_7, "【打印箱码成功】", f"已生成箱码：{case_code}（绿框显示）")
            self.main_window.play_success()
        except Exception:
            pass

    # 更新箱码页面内容
    def updataPageCase(self, case_code):
        if case_code is None:
            self.main_window.taps_20.setText(f"请打印箱码")
            self.main_window.groupBox_box_0.setStyleSheet(
                "QGroupBox { background-color: #EC808D; border: 1px solid #797979; border-radius: 5px; }")
        else:
            self.case = case_code
            self.main_window.taps_20.setText(f"{self.case}")
            self.main_window.groupBox_box_0.setStyleSheet(
                "QGroupBox { background-color: #CAF982; border: 1px solid #797979; border-radius: 5px; }")
            # 更新缓存的内容
            config.setConfig({"caseCode": case_code})

    # 生成一个 13 位纯数字时间戳作为箱码
    def generate_case_code(self):
        timestamp = int(round(time.time() * 1000))
        code_str = str(timestamp)
        if len(code_str) > 13:
            code_str = code_str[:13]
        elif len(code_str) < 13:
            code_str = code_str.zfill(13)
        return code_str

    # 打印箱码 (调用 T63R RFID 打印写卡闭环引擎)
    def print_barcode(self, case_code):
        printer_name = CONFIG_DATA.get('combobox_printSelect', '')
        page_width = int(CONFIG_DATA.get('edit_page_width', 500))
        page_height = int(CONFIG_DATA.get('edit_page_height', 400))
        page_num = int(CONFIG_DATA.get('edit_page_num', 1))
        # 调用 printUtils 中的 T63R RFID 闭环打印引擎
        res = print_barcode(case_code, printer_name, page_width, page_height, page_num)
        logging.info(f"打印箱码闭环完成: {case_code}")
        return res # 使用 logging.info 替换 print

    # ========================打印箱码结束=========================

    # ========================页面数据 代码开始=========================
    # 扫码识别结果更新
    def scan_code(self, num):
        # 更新【n/s】提示内容
        # 更新label_result_box的文本内容
        self.main_window.label_result_box.setText(f"【{num}/10盒】")

        # 创建groupBox列表
        group_boxes = [
            self.main_window.groupBox_result_1, self.main_window.groupBox_result_2,
            self.main_window.groupBox_result_3, self.main_window.groupBox_result_4,
            self.main_window.groupBox_result_5, self.main_window.groupBox_result_6,
            self.main_window.groupBox_result_7, self.main_window.groupBox_result_8,
            self.main_window.groupBox_result_9, self.main_window.groupBox_result_10
        ]

        # 更新groupBox的背景色
        for i, group_box in enumerate(group_boxes, start=1):
            if i <= num:
                group_box.setStyleSheet(
                    "QGroupBox { background-color: #CAF982; border: 1px solid #797979; border-radius: 5px; }")
            else:
                group_box.setStyleSheet(
                    "QGroupBox { background-color: #EC808D; border: 1px solid #797979; border-radius: 5px; }")

    def scan_code_end(self):
        # 更新【n/s】提示内容
        # 更新label_result_box的文本内容
        self.main_window.label_result_box.setText("【0/10盒】")

        # 创建groupBox列表
        group_boxes = [
            self.main_window.groupBox_result_1, self.main_window.groupBox_result_2,
            self.main_window.groupBox_result_3, self.main_window.groupBox_result_4,
            self.main_window.groupBox_result_5, self.main_window.groupBox_result_6,
            self.main_window.groupBox_result_7, self.main_window.groupBox_result_8,
            self.main_window.groupBox_result_9, self.main_window.groupBox_result_10
        ]

        # 更新groupBox的背景色
        for group_box in group_boxes:
            group_box.setStyleSheet("""
                QGroupBox {
                    background-color: #F2F2F2;
                    border: 1px solid #797979;
                    border-radius: 5px;
                }
            """)

    # 扫码识别结果更新
    def scan_case(self):
        num = len(self.scan_case_data) | 0
        # 更新【n/s】提示内容
        # 更新label_result_box的文本内容
        self.main_window.label_result_case.setText(f"【{num}/10捆】")

        # 创建groupBox列表
        group_boxes = [
            self.main_window.groupBox_box_1, self.main_window.groupBox_box_2,
            self.main_window.groupBox_box_3, self.main_window.groupBox_box_4,
            self.main_window.groupBox_box_5, self.main_window.groupBox_box_6,
            self.main_window.groupBox_box_7, self.main_window.groupBox_box_8,
            self.main_window.groupBox_box_9, self.main_window.groupBox_box_10
        ]

        # 更新groupBox的背景色
        for i, group_box in enumerate(group_boxes, start=1):
            if i <= num:
                group_box.setStyleSheet(
                    "QGroupBox { background-color: #CAF982; border: 1px solid #797979; border-radius: 5px; }")
            else:
                group_box.setStyleSheet(
                    "QGroupBox { background-color: #EC808D; border: 1px solid #797979; border-radius: 5px; }")

    def scan_case_end(self):
        # 更新【n/s】提示内容
        # 更新label_result_box的文本内容
        self.main_window.label_result_case.setText(f"【0/10捆】")

        # 创建groupBox列表
        group_boxes = [
            self.main_window.groupBox_box_1, self.main_window.groupBox_box_2,
            self.main_window.groupBox_box_3, self.main_window.groupBox_box_4,
            self.main_window.groupBox_box_5, self.main_window.groupBox_box_6,
            self.main_window.groupBox_box_7, self.main_window.groupBox_box_8,
            self.main_window.groupBox_box_9, self.main_window.groupBox_box_10
        ]

        # 更新groupBox的背景色
        for group_box in group_boxes:
            group_box.setStyleSheet("""
                QGroupBox {
                    background-color: #F2F2F2;
                    border: 1px solid #797979;
                    border-radius: 5px;
                }
            """)

    # ========================页面数据 代码结束=========================

    # ========================海康代码开始=========================
    # 海康相机初始化方法
    def hiKInit(self):
        # 调用相机初始化方法
        self.initCamera()

    # 相机初始化方法
    def initCamera(self):
        # 创建相机设备列表对象
        deviceList = MV_CC_DEVICE_INFO_LIST()
        # 创建相机对象
        cam = MvCamera()
        # 选择相机索引，默认为0
        nSelCamIndex = 0
        # 创建相机操作对象，传入相机对象、设备列表和相机索引
        global obj_cam_operation
        obj_cam_operation = CameraOperation(cam, deviceList, nSelCamIndex)

        # 枚举相机设备
        ret = MvCamera.MV_CC_EnumDevices(MV_GIGE_DEVICE | MV_USB_DEVICE, deviceList)
        # 如果枚举失败，打印错误信息
        if ret != MV_OK:
            logging.error(f"枚举设备失败，错误码：{ret}") # 使用 logging.error 替换 print
            return
        # 如果没有发现设备，打印提示信息
        if deviceList.nDeviceNum == 0:
            logging.info("未发现任何设备") # 使用 logging.info 替换 print
            return
        # 打印发现的设备数量
        logging.info(f"发现 {deviceList.nDeviceNum} 个设备！") # 使用 logging.info 替换 print

        # 打开相机设备
        ret = obj_cam_operation.Open_device()
        # 如果打开失败，打印错误信息
        if ret != MV_OK:
            logging.error(f"打开设备失败，错误码：{ret}") # 使用 logging.error 替换 print
            return

        # 开始推流
        self.start_grabbing()

    # 开始取流方法
    def start_grabbing(self):
        if obj_cam_operation is None:
            return MV_E_CALLORDER
        win_id = self.main_window.widgetDisplay.winId()
        # 判断是否正在推流中
        if obj_cam_operation.b_start_grabbing:
            logging.info(f"相机重新取流，重新绑定渲染句柄: {win_id}")
            obj_cam_operation.Stop_grabbing()
        # 开始推流
        ret = obj_cam_operation.Start_grabbing(win_id)
        # 如果开始推流失败，打印错误信息
        if ret != MV_OK:
            logging.error(f"开始推流失败，错误码：{ret}")
        else:
            logging.info(f"开启推流成功，渲染句柄 HWND={win_id}")

    def ensure_camera_display(self):
        """确保主窗口完全显示后调用此方法，绑定有效 WinID 重新渲染画面"""
        self.start_grabbing()

    def stop_line(self):
        obj_cam_operation.sacn_image = None  # 页面正常显示实时画面

    def stop_grabbing(self):
        # 判断是否已经停止推流了
        if not obj_cam_operation.b_start_grabbing:
            logging.info("相机已经停止取流。") # 使用 logging.info 替换 print
            return MV_E_CALLORDER
        # 调用相机操作对象的停止取流方法
        ret = obj_cam_operation.Stop_grabbing()
        # 如果停止取流失败，打印错误信息
        if ret != MV_OK:
            logging.error(f"停止取流失败，错误码：{ret}") # 使用 logging.error 替换 print

    # 关闭设备方法
    def close_device(self):
        # 调用相机操作对象的关闭设备方法
        obj_cam_operation.Close_device()

    # 设置连续触发模式方法
    def set_continue_mode(self):
        # 调用相机操作对象的设置触发模式方法，参数为False表示连续模式
        ret = obj_cam_operation.Set_trigger_mode(False)
        # 如果设置连续模式失败，打印错误信息
        if ret != MV_OK:
            logging.error(f"设置连续模式失败，错误码：{ret}") # 使用 logging.error 替换 print

    # 设置软触发模式方法
    def set_software_trigger_mode(self):
        # 调用相机操作对象的设置触发模式方法，参数为True表示软触发模式
        ret = obj_cam_operation.Set_trigger_mode(True)
        # 如果设置软触发模式失败，打印错误信息
        if ret != MV_OK:
            logging.error(f"设置软触发模式失败，错误码：{ret}") # 使用 logging.error 替换 print

    # 触发一次方法
    def trigger_once(self):
        # 调用相机操作对象的软触发方法
        ret = obj_cam_operation.Trigger_once()
        # 如果软触发失败，打印错误信息
        if ret != MV_OK:
            logging.error(f"软触发失败，错误码：{ret}") # 使用 logging.error 替换 print

    # 保存图像为BMP格式方法
    def save_bmp(self):
        # 调用相机操作对象的保存BMP方法
        ret = obj_cam_operation.Save_Bmp()
        # 如果保存BMP失败，打印错误信息
        if ret != MV_OK:
            logging.error(f"保存BMP失败，错误码：{ret}") # 使用 logging.error 替换 print
        else:
            # 如果保存成功，打印成功信息
            logging.info("保存图像成功") # 使用 logging.info 替换 print

    # ========================海康代码结束=========================

    # ========================自定义Style样式开始=========================
    # 初始化样式
    def styleInit(self):
        # 应用自定义样式
        self.main_window.setStyleSheet("QMainWindow {background-color: white;}")

        # 创建阴影效果
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)  # 阴影模糊半径
        shadow.setColor(QColor(255, 255, 255, 80))  # 阴影颜色
        shadow.setOffset(5, 5)  # 阴影偏移量

        # 设置groupBox_7无背景色
        self.main_window.groupBox_7.setStyleSheet("QGroupBox {background-color: transparent; border: 0px;}")

        # 设置groupBox、groupBox_2、groupBox_3、widgetDisplay背景色为F2F3F5，圆角半径为20
        group_boxes = [self.main_window.groupBox, self.main_window.groupBox_2, self.main_window.groupBox_3]
        for group_box in group_boxes:
            group_box.setStyleSheet(
                "QGroupBox { background-color: #F2F3F5; border-radius: 20px; border: 1px solid #797979;}")
            group_box.setGraphicsEffect(shadow)  # 应用阴影效果

        # 设置widgetDisplay圆角展示
        self.main_window.widgetDisplay.setStyleSheet(
            "background-color: #F2F3F5; border-radius: 20px; border: 1px solid #797979;")
        self.main_window.widgetDisplay.setGraphicsEffect(shadow)  # 应用阴影效果

        # 设置label_date字体颜色为#909399
        self.main_window.label_date.setStyleSheet("color: #909399;")

        # 设置label_result_box、label_data_unline、label_result_box字体颜色为#D9001B
        self.main_window.label_result_box.setStyleSheet("color: #D9001B;")
        self.main_window.label_data_unline.setStyleSheet("color: #D9001B;")
        self.main_window.label_result_case.setStyleSheet("color: #D9001B;")

        # 设置groupBox_4、groupBox_5、groupBox_6背景色为白色，圆角20px
        self.main_window.groupBox_4.setStyleSheet("background-color: white; border-radius: 20px;")
        self.main_window.groupBox_5.setStyleSheet("background-color: white; border-radius: 20px;")
        self.main_window.groupBox_6.setStyleSheet("background-color: white; border-radius: 20px;")

        # 设置groupBox_result_1到groupBox_result_10的样式
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

        # 设置taps_3到taps_12的样式
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

        # 设置 groupBox_box_0 到 groupBox_box_10 的样式
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

        # 设置 taps_21 到 taps_29 的样式
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

