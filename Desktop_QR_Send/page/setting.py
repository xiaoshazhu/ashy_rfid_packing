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
        logging.info("初始化设置页面...")

        # 连接信号和槽
        self.main_window.button_setting_cancel.clicked.connect(self.button_setting_cancel)
        self.main_window.button_setting_save.clicked.connect(self.button_setting_save)

        # 读取全局变量 config
        self.form_data = config.CONFIG_DATA
        logging.debug(f"从 config.CONFIG_DATA 加载配置数据: {self.form_data}")

        # 调用更新串口列表的方法
        self.update_com_ports()

        # 调用更新打印机列表的方法
        self.update_printers()

        # 设置参数，将 self.form_data 的参数一个个放到控件中作为默认值
        self.main_window.combobox_printSelect.setCurrentIndex(
            self.main_window.combobox_printSelect.findData(self.form_data.get('combobox_printSelect'))
        )

        saved_com = self.form_data.get('combobox_comSelect')
        com_idx = self.main_window.combobox_comSelect.findData(saved_com)
        if com_idx >= 0:
            self.main_window.combobox_comSelect.setCurrentIndex(com_idx)
        elif self.main_window.combobox_comSelect.count() > 1:
            # 如果原配置串口未接入，但系统中有可用串口，自动默认选中第1个真实串口
            first_port = self.main_window.combobox_comSelect.itemData(1)
            logging.info(f"原配置串口 {saved_com} 未在列表中，自动选择已接入的串口: {first_port}")
            self.main_window.combobox_comSelect.setCurrentIndex(1)
        else:
            self.main_window.combobox_comSelect.setCurrentIndex(0)

        self.main_window.edit_service.setText(self.form_data.get('edit_service', '') or '')
        self.main_window.edit_max_jian.setText(str(self.form_data.get('edit_max_jian', '10') or '10'))
        self.main_window.edit_max_xiang.setText(str(self.form_data.get('edit_max_xiang', '10') or '10'))
        self.main_window.edit_min_x.setText(str(self.form_data.get('edit_min_x', '0') or '0'))
        self.main_window.edit_max_x.setText(str(self.form_data.get('edit_max_x', '0') or '0'))
        self.main_window.edit_min_y.setText(str(self.form_data.get('edit_min_y', '0') or '0'))
        self.main_window.edit_max_y.setText(str(self.form_data.get('edit_max_y', '0') or '0'))
        self.main_window.edit_page_width.setText(str(self.form_data.get('edit_page_width', '600') or '600'))
        self.main_window.edit_page_height.setText(str(self.form_data.get('edit_page_height', '400') or '400'))
        self.main_window.edit_page_num.setText(str(self.form_data.get('edit_page_num', '2') or '2'))

        logging.info("设置页面初始化完成。")

    # 加载串口列表
    def update_com_ports(self):
        logging.info("更新串口列表...")
        self.main_window.combobox_comSelect.clear()
        self.main_window.combobox_comSelect.addItem("不启用RS485实体按钮（无串口）", None)
        ports = serial.tools.list_ports.comports()
        com_ports_list = []
        for port, desc, hwid in sorted(ports):
            display_text = f"{port} - {desc}" if desc and port not in desc else (desc or port)
            self.main_window.combobox_comSelect.addItem(display_text, port)
            com_ports_list.append({'port': port, 'desc': desc, 'hwid': hwid})
        logging.debug(f"检测到串口: {com_ports_list}")
        logging.info(f"串口列表更新完成，共找到 {len(com_ports_list)} 个串口。")

    # 加载打印机列表
    def update_printers(self):
        logging.info("更新打印机列表...")
        self.main_window.combobox_printSelect.clear()
        printers = QPrinterInfo.availablePrinters()
        printer_names = []
        for printer in printers:
            printer_name = printer.printerName()
            self.main_window.combobox_printSelect.addItem(printer_name, printer_name)
            printer_names.append(printer_name)
        logging.debug(f"检测到打印机: {printer_names}")
        logging.info(f"打印机列表更新完成，共找到 {len(printer_names)} 个打印机。")

    # 取消
    def button_setting_cancel(self):
        logging.info("点击 '取消' 按钮，设置页面关闭。")
        self.settings_dialog.close()

    # 保存
    def button_setting_save(self):
        logging.info("点击 '保存' 按钮，尝试保存设置...")
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
        logging.debug(f"读取到的设置表单数据: {self.form_data}")

        try:
            config.setConfig(self.form_data)
            logging.info("配置已成功保存并应用。")
        except Exception as e:
            logging.error(f"保存配置时发生错误: {e}")
        self.settings_dialog.close()
        logging.info("设置页面已关闭。")


if __name__ == '__main__':
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
    setting_page.settingInit()

    dialog.show()
    sys.exit(app.exec_())
