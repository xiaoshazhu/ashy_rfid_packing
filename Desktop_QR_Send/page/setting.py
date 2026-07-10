# setting.py
from PySide6.QtWidgets import QWidget
import serial.tools.list_ports
from PySide6.QtPrintSupport import QPrinterInfo
import logging  # 导入 logging 模块

from page import config


class Setting(QWidget):
    def __init__(self, main_window, settings_dialog):
        super().__init__()
        self.form_data = {
            'combobox_printSelect': None,  # 打印机
            'combobox_comSelect': None,  # 串口
            'edit_service': None,  # 服务器地址
            'edit_max_jian': None,  # 一捆数量
            'edit_max_xiang': None,  # 一箱数量
            'edit_min_x': None,  # X轴起始
            'edit_max_x': None,  # X轴截至
            'edit_min_y': None,  # Y轴起始
            'edit_max_y': None,  # Y轴截至
            'edit_page_width': None,  # 打印机纸张的宽度
            'edit_page_height': None,  # 打印机纸张的高度
            'edit_page_num': None,  # 打印机打印份数
        }
        self.main_window = main_window
        self.settings_dialog = settings_dialog

    def settingInit(self):
        logging.info("初始化设置页面...") #  添加日志：初始化设置页面

        # 连接信号和槽
        self.main_window.button_setting_cancel.clicked.connect(self.button_setting_cancel)
        self.main_window.button_setting_save.clicked.connect(self.button_setting_save)

        # 读取全局变量 config 读取main.py的CONFIG_DATA
        self.form_data = config.CONFIG_DATA
        logging.debug(f"从 config.CONFIG_DATA 加载配置数据: {self.form_data}") #  添加 debug 日志：加载配置数据

        # 初始化UI和信号槽


        # 调用更新串口列表的方法
        self.update_com_ports()

        # 调用更新打印机列表的方法
        self.update_printers()

        # 设置参数,将self.form_data的参数一个个放到控件中作为默认值
        self.main_window.combobox_printSelect.setCurrentIndex(
            self.main_window.combobox_printSelect.findData(self.form_data['combobox_printSelect']))
        self.main_window.combobox_comSelect.setCurrentIndex(
            self.main_window.combobox_comSelect.findData(self.form_data['combobox_comSelect']))
        self.main_window.edit_service.setText(self.form_data['edit_service'])
        self.main_window.edit_max_jian.setText(self.form_data['edit_max_jian'])
        self.main_window.edit_max_xiang.setText(self.form_data['edit_max_xiang'])
        self.main_window.edit_min_x.setText(self.form_data['edit_min_x'])
        self.main_window.edit_max_x.setText(self.form_data['edit_max_x'])
        self.main_window.edit_min_y.setText(self.form_data['edit_min_y'])
        self.main_window.edit_max_y.setText(self.form_data['edit_max_y'])
        self.main_window.edit_page_width.setText(self.form_data['edit_page_width'])
        self.main_window.edit_page_height.setText(self.form_data['edit_page_height'])
        self.main_window.edit_page_num.setText(self.form_data['edit_page_num'])

        logging.info("设置页面初始化完成。") #  添加日志：设置页面初始化完成


    # 加载串口列表
    def update_com_ports(self):
        logging.info("更新串口列表...") #  添加日志：更新串口列表
        # 检测并显示所有可用的串口
        self.main_window.combobox_comSelect.clear()
        ports = serial.tools.list_ports.comports()
        com_ports_list = [] # 用于记录串口列表的列表
        for port, desc, hwid in sorted(ports):
            self.main_window.combobox_comSelect.addItem(f"{desc}", port)
            com_ports_list.append({'port': port, 'desc': desc, 'hwid': hwid}) # 记录串口信息
        logging.debug(f"检测到串口: {com_ports_list}") #  添加 debug 日志：检测到的串口列表
        logging.info(f"串口列表更新完成，共找到 {len(com_ports_list)} 个串口。") #  添加日志：串口列表更新完成

    # 加载打印机列表
    def update_printers(self):
        logging.info("更新打印机列表...") #  添加日志：更新打印机列表
        # 检测并显示所有可用的打印机
        self.main_window.combobox_printSelect.clear()
        printers = QPrinterInfo.availablePrinters()
        printer_names = [] # 用于记录打印机名称的列表
        for printer in printers:
            printer_name = printer.printerName()
            self.main_window.combobox_printSelect.addItem(printer_name, printer_name)
            printer_names.append(printer_name) # 记录打印机名称
        logging.debug(f"检测到打印机: {printer_names}") #  添加 debug 日志：检测到的打印机列表
        logging.info(f"打印机列表更新完成，共找到 {len(printer_names)} 个打印机。") #  添加日志：打印机列表更新完成

    # 取消
    def button_setting_cancel(self):
        logging.info("点击 '取消' 按钮，设置页面关闭。") #  添加日志：点击取消按钮
        # 关闭弹窗
        self.settings_dialog.close()

    # 保存
    def button_setting_save(self):
        logging.info("点击 '保存' 按钮，尝试保存设置...") #  添加日志：点击保存按钮
        # 读取值
        self.form_data['combobox_printSelect'] = self.main_window.combobox_printSelect.currentData()
        self.form_data['combobox_comSelect'] = self.main_window.combobox_comSelect.currentData()
        self.form_data['edit_service'] = self.main_window.edit_service.text()
        self.form_data['edit_max_jian'] = self.main_window.edit_max_jian.text()
        self.form_data['edit_max_xiang'] = self.main_window.edit_max_xiang.text()
        self.form_data['edit_min_x'] = self.main_window.edit_min_x.text()
        self.form_data['edit_max_x'] = self.main_window.edit_max_x.text()
        self.form_data['edit_min_y'] = self.main_window.edit_min_y.text()
        self.form_data['edit_max_y'] = self.main_window.edit_max_y.text()
        self.form_data['edit_page_width'] = self.main_window.edit_page_width.text()
        self.form_data['edit_page_height'] = self.main_window.edit_page_height.text()
        self.form_data['edit_page_num'] = self.main_window.edit_page_num.text()
        logging.debug(f"读取到的设置表单数据: {self.form_data}") #  添加 debug 日志：读取到的表单数据

        # 将self.form_data 赋值到 CONFIG_DATA，调用main.py的setConfig
        try:
            config.setConfig(self.form_data)
            logging.info("配置已成功保存并应用。") #  添加日志：配置保存成功
        except Exception as e:
            logging.error(f"保存配置时发生错误: {e}") #  使用 logging.error 替换 print
        # 关闭弹窗
        self.settings_dialog.close()
        logging.info("设置页面已关闭。") #  添加日志：设置页面关闭

if __name__ == '__main__':
    #  测试 setting.py 的日志功能
    import sys
    from PySide6.QtWidgets import QApplication, QDialog
    from qtDesigner.qt_setting import Ui_form_settings
    import logging

    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(filename)s - %(funcName)s - %(lineno)d - %(message)s')

    app = QApplication(sys.argv)
    dialog = QDialog()
    ui = Ui_form_settings()
    ui.setupUi(dialog)

    setting_page = Setting(ui, dialog)
    setting_page.settingInit() # 初始化设置页面，会触发日志输出

    dialog.show()
    sys.exit(app.exec_())