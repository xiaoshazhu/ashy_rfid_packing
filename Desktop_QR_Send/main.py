import sys
import os

# 自动定位当前脚本根目录并锁定为工作目录，防止跨路径启动引发的相对路径错误
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(CURRENT_DIR)
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

# 必须在导入任何 PySide6 模块前完成 DLL 引导；返回的目录句柄由该模块持续保存。
from runtime_bootstrap import configure_runtime

configure_runtime()

import asyncio
import threading
import time

from PySide6.QtWidgets import QApplication, QMainWindow
from PySide6.QtGui import QGuiApplication
from threading import Thread
from page.home import Home
from qtDesigner.colored_log import ColoredFormatter
from qtDesigner.qt_home import Ui_HomeWindow
from utils import sound_player
from utils.RS485Utils import RS485Utils
from page import config
from utils.web_socket_client import startWS
import logging
import datetime
from logging.handlers import TimedRotatingFileHandler
from serial.tools import list_ports

class MainWindow(QMainWindow, Ui_HomeWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        # 配置日志记录器
        self.setup_logging()

        # 尝试读取本地配置参数
        try:
            config.loadConfig()
        except Exception as e:
            logging.error(f"无法加载配置文件: {e}")  # 使用 logging.error 替换 print

        self.resize(1920, 1080)
        self.centerWindow()
        self.setupUi(self)

        # 主程序main.py 初始化建立 WebSocket
        try:
            websocket_uri = config.CONFIG_DATA["edit_service"]
            self.client = startWS(websocket_uri=websocket_uri)

            # 启动异步事件循环（在单独线程中）
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            self.loop_thread = Thread(target=self.run_loop, daemon=True)
            self.loop_thread.start()
        except Exception as e:
            logging.error(f"WebSocket 连接失败: {e}") # 使用 logging.error 替换 print


        # 实例化 Home 类并初始化
        self.home = Home(main_window=self)

        # 初始化 RS485 监听线程
        self.rs485_thread = Thread(target=self.listen_to_rs485, daemon=True)
        self.rs485_thread.start()

        # 创建 SoundPlayer 实例
        self.player = sound_player.SoundPlayer()

    def play_success(self):
        threading.Thread(target=self.player.play_sound, args=(True,)).start()

    def play_warning(self):
        threading.Thread(target=self.player.play_sound, args=(False,)).start()


    def setup_logging(self):
        """配置日志记录 (同时输出到文件和控制台，控制台彩色)"""
        log_dir = "logs"  # 日志文件存放目录
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

        log_file_name = os.path.join(log_dir, "app_log")  # 日志文件前缀名，不包含日期

        # -------- 1. 配置文件日志处理器 (FileHandler) --------
        log_handler = TimedRotatingFileHandler(
            filename=f"{log_file_name}.log",  # 基础日志文件名
            when="midnight",  # 每天凌晨 00:00:00 轮转
            interval=1,  # 轮转间隔为 1 天
            backupCount=5,  # 最多保留 5 个备份文件
            encoding='utf-8'
        )
        log_handler.suffix = "%Y-%m-%d.log"  # 轮转后的日志文件名后缀，包含日期
        log_handler.extMatch = r"^\d{4}-\d{2}-\d{2}.log$"  # 匹配轮转日志文件名的正则表达式
        log_formatter_file = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(filename)s - %(funcName)s - %(lineno)d - %(message)s')  # 文件日志格式 (纯文本)
        log_handler.setFormatter(log_formatter_file)

        # -------- 2. 配置控制台日志处理器 (StreamHandler) --------
        console_handler = logging.StreamHandler()  # 创建 StreamHandler，输出到控制台
        console_handler.setLevel(logging.DEBUG)  # 设置控制台日志级别为 DEBUG (可以根据需要调整)
        colored_formatter = ColoredFormatter()  # 创建 ColoredFormatter 实例 (彩色格式化器)
        console_handler.setFormatter(colored_formatter)  # 设置控制台 Handler 的 Formatter 为彩色格式化器

        # -------- 3. 获取 Root Logger 并添加两个 Handlers --------
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)  # 设置全局日志级别为 INFO (或者 DEBUG，根据需要调整)

        root_logger.addHandler(log_handler)  # 添加文件日志处理器
        root_logger.addHandler(console_handler)  # 添加控制台日志处理器

        logging.info("日志系统初始化完成，同时输出到文件和控制台 (控制台彩色)。")  # 记录日志系统启动信息

    def run_loop(self):
        """在单独线程中运行 asyncio 事件循环"""
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()


    def listen_to_rs485(self):
        """监听 RS485 数据"""
        global rs485
        while True:
            config.loadConfig()
            comSelect = config.CONFIG_DATA.get("combobox_comSelect")

            port_items = list(list_ports.comports())
            all_ports = [port.device for port in port_items]

            # 区分 USB 串口芯片（如 CH340, FTDI）与主板原生 COM1/COM2
            usb_ports = []
            other_ports = []
            for item in port_items:
                desc = (item.description or "").upper()
                hwid = (item.hwid or "").upper()
                if any(token in desc or token in hwid for token in ("USB", "CH34", "FTDI", "PL2303", "CP210", "SERIAL", "UART")):
                    usb_ports.append(item.device)
                else:
                    other_ports.append(item.device)

            preferred_ports = usb_ports + other_ports
            logging.info(f"当前可用串口: {all_ports} (按 USB 转换器优先排序: {preferred_ports})")

            target_port = None
            if comSelect and comSelect in all_ports:
                target_port = comSelect
            elif preferred_ports:
                target_port = preferred_ports[0]
                logging.info(
                    f"配置串口 ({comSelect}) 未连接或未配置，优先自适应匹配端口: {target_port}"
                )
            else:
                logging.warning("未检测到任何可用串口，3秒后重试...")
                time.sleep(3)
                continue

            rs485 = RS485Utils(port=target_port, baudrate=9600, home_instance=self.home)
            try:
                rs485.connect()
                rs485.listen()
            except KeyboardInterrupt:
                logging.info("RS485 监听停止 (KeyboardInterrupt).")
                break
            except Exception as exc:
                logging.error(f"RS485 [{target_port}] 连接或监听失败: {exc}")
            finally:
                rs485.close()
                logging.info(f"RS485 端口 [{target_port}] 已关闭.")

            logging.warning("3秒后重新连接RS485串口...")
            time.sleep(3)

    def centerWindow(self):
        """设置窗口居中"""
        screen = QGuiApplication.primaryScreen().geometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)

    def closeEvent(self, event):
        """窗口关闭事件"""
        logging.info("程序开始关闭...") # 记录程序关闭日志
        self.home.stop_grabbing()
        self.home.close_device()
        if self.client and self.client.get_connection_status():
            asyncio.run_coroutine_threadsafe(self.client.close(), self.loop)
        self.loop.stop()

    def centerWindow(self):
        """设置窗口居中"""
        screen = QGuiApplication.primaryScreen().geometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)

    def closeEvent(self, event):
        """窗口关闭事件"""
        logging.info("程序开始关闭...") # 记录程序关闭日志
        self.home.stop_grabbing()
        self.home.close_device()
        if self.client and self.client.get_connection_status():
            asyncio.run_coroutine_threadsafe(self.client.close(), self.loop)
        self.loop.stop()
        logging.info("Asyncio 事件循环已停止.") # 记录事件循环停止日志
        logging.info("WebSocket 连接已关闭 (如果已建立).") # 记录 WebSocket 关闭日志
        logging.info("设备资源已释放.") # 记录设备资源释放日志
        logging.info("程序关闭完成.") # 记录程序完全关闭日志
        event.accept()

if __name__ == "__main__":
    import sys
    from PySide6.QtCore import QTimer
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.showFullScreen()  # 全屏显示
    main_window.show()
    # 延时 300ms 绑定渲染窗口句柄 HWND，解决黑屏问题
    QTimer.singleShot(300, main_window.home.ensure_camera_display)
    logging.info("GUI 程序启动。") # 记录 GUI 程序启动日志
    sys.exit(app.exec())
