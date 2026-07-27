# log.py
from PySide6 import QtWidgets, QtCore
from PySide6.QtWidgets import QFileDialog
import logging  # 导入 logging 模块
import os # 导入 os 模块

from qtDesigner.colored_log import ColoredFormatter
from qtDesigner.qt_log import Ui_Dialog_log  # 导入 qt_log.py 中生成的 UI 类

# 1.  ListViewLogHandler 类 (保持不变，用于未来的实时日志功能，现在暂时不直接使用)
class ListViewLogHandler(logging.Handler):
    def __init__(self, list_view):
        super().__init__()
        self.list_view = list_view
        self.log_messages = []
        self.log_model = QtCore.QStringListModel()
        if self.list_view:
            self.list_view.setModel(self.log_model)

    def set_list_view(self, list_view):
        """在 LogDialog 初始化时，设置 list_view"""
        self.list_view = list_view
        self.log_messages = [] #  每次设置新的 list_view 时，清空之前的日志信息，或者您可以选择不清空
        self.log_model = QtCore.QStringListModel()
        self.list_view.setModel(self.log_model)


    def emit(self, record):
        try:
            msg = self.format(record)
            timestamp = QtCore.QDateTime.currentDateTime().toString("yyyy-MM-dd hh:mm:ss")
            log_entry = f"[{timestamp}] {msg}"
            self.log_messages.append(log_entry)
            if self.list_view:
                self.log_model.setStringList(self.log_messages)
                self.list_view.scrollToBottom()
        except RecursionError:
            self.handleError(record)
        except Exception:
            self.handleError(record)


class LogDialog(QtWidgets.QDialog, Ui_Dialog_log):
    def __init__(self, parent=None):
        super(LogDialog, self).__init__(parent)
        self.setupUi(self)  # 初始化 UI 界面

        # 连接按钮信号和槽函数
        self.pushButton_close_dialog.clicked.connect(self.close_dialog)
        self.pushButton_export_log.clicked.connect(self.export_log)

        self.log_messages = []  # 用于存储日志消息的列表 (用于加载日志文件内容)
        self.log_model = QtCore.QStringListModel() # 用于 listView_log 的数据模型
        self.listView_log.setModel(self.log_model) # 设置 listView_log 的数据模型

        # self.load_log_file_content()  #  <-- 从 __init__ 中移除，移动到 showEvent 中

        logging.info("日志弹窗已创建。") # 记录日志弹窗创建事件 (在 __init__ 中，弹窗只是被创建，还没有显示)

        #  配置控制台日志处理器，并使用 ColoredFormatter (保持不变)
        console_handler = logging.StreamHandler() # 创建 StreamHandler，输出到控制台
        console_handler.setLevel(logging.DEBUG) # 设置控制台日志级别 (可以根据需要调整)
        colored_formatter = ColoredFormatter() # 创建 ColoredFormatter 实例
        console_handler.setFormatter(colored_formatter) # 设置 Formatter
        logging.getLogger().addHandler(console_handler) # 将 ConsoleHandler 添加到 root logger


    def showEvent(self, event):
        """重写 showEvent 方法，每次弹窗显示时重新加载日志文件内容"""
        super().showEvent(event) #  首先调用父类的 showEvent 方法，保证弹窗的正常显示行为
        self.load_log_file_content() #  <--  在弹窗每次显示时，加载日志文件内容
        logging.debug("LogDialog showEvent() 被调用，重新加载日志文件内容。") # 添加 debug 日志，记录日志重新加载


    def load_log_file_content(self):
        """加载日志文件内容到 ListView (最新的日志在最前面)"""
        log_dir = "logs"  # 日志文件存放目录，与 main.py 中的设置保持一致
        log_file_prefix = "app_log" # 日志文件前缀名，与 main.py 中的设置保持一致

        latest_log_file = self.get_latest_log_file(log_dir, log_file_prefix) # 获取最新的日志文件

        if latest_log_file:
            try:
                with open(latest_log_file, 'r', encoding='utf-8') as f:
                    log_lines = f.readlines() # 读取所有行
                    log_lines.reverse() # <---  反转日志行列表，最新的日志在最前面
                    self.log_messages = [line.strip() for line in log_lines] # 去除每行末尾的换行符
                    self.log_model.setStringList(self.log_messages) # 更新模型，listView_log 会自动更新
                    self.listView_log.scrollToTop() #  滚动到顶部，显示最新的日志 (现在最新的在最上面了)
                    logging.info(f"成功加载日志文件内容 (最新的在最前): {latest_log_file}") # 记录日志加载成功事件
            except Exception as e:
                logging.error(f"加载日志文件失败: {e}") # 记录日志加载失败事件
                QtWidgets.QMessageBox.critical(self, "错误", f"加载日志文件失败: {str(e)}")
        else:
            logging.warning("没有找到日志文件。") # 记录没有找到日志文件事件
            QtWidgets.QMessageBox.warning(self, "警告", "没有找到日志文件。")


    def get_latest_log_file(self, log_dir, log_file_prefix):
        """获取最新的日志文件路径 (保持不变)"""
        # 正式程序始终写入 app_log.log。轮转文件名中带日期，按文件名
        # 倒序排序会误选历史文件，导致现场看到的日志不是本次启动日志。
        active_log_file = os.path.join(log_dir, f"{log_file_prefix}.log")
        if os.path.isfile(active_log_file):
            return active_log_file

        log_files = [f for f in os.listdir(log_dir) if f.startswith(log_file_prefix) and f.endswith(".log")] # 获取所有日志文件
        if not log_files:
            return None # 没有日志文件

        log_files.sort(
            key=lambda file_name: os.path.getmtime(os.path.join(log_dir, file_name)),
            reverse=True,
        ) # 活动日志不存在时，按实际修改时间选择最近的日志
        return os.path.join(log_dir, log_files[0]) # 返回最新的日志文件路径


    def close_dialog(self):
        """关闭弹窗 (保持不变)"""
        logging.info("日志弹窗已关闭。") # 记录日志弹窗关闭事件
        self.close()

    def export_log(self):
        """导出日志到文件 (导出当前 ListView 中显示的日志) (保持不变)"""
        if not self.listView_log.model().stringList(): # 从模型中获取日志内容
            QtWidgets.QMessageBox.information(self, "提示", "日志内容为空，无法导出。")
            return

        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getSaveFileName(self, "保存日志文件", "", "文本文件 (*.txt);;所有文件 (*)")

        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    log_content = self.listView_log.model().stringList() # 从模型中获取日志内容
                    for message in log_content:
                        f.write(message + '\n')
                logging.info(f"日志已成功导出到: {file_path}") # 使用 logging 记录导出日志事件
                QtWidgets.QMessageBox.information(self, "提示", f"日志已成功导出到: {file_path}")
            except Exception as e:
                logging.error(f"导出日志失败: {str(e)}") # 使用 logging 记录导出日志失败事件
                QtWidgets.QMessageBox.critical(self, "错误", f"导出日志失败: {str(e)}")

    def add_log_message(self, message):
        """添加日志消息到 ListView (实时追加新日志，如果需要实时日志功能，可以保留此方法并修改 ListViewLogHandler 重新调用它) (保持不变)"""
        #  这个方法可以保留，如果未来需要重新启用实时日志功能，可以修改 ListViewLogHandler 在 emit 方法中调用此方法
        pass


if __name__ == '__main__':
    import sys
    app = QtWidgets.QApplication(sys.argv)
    dialog = LogDialog()
    #  现在运行测试程序，日志弹窗应该会尝试加载日志文件内容
    dialog.show()
    sys.exit(app.exec_())
