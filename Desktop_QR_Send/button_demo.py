"""安全的按钮功能演示程序：使用内存模拟数据，不访问业务数据库或硬件功能。"""

from __future__ import annotations

import argparse
import datetime
import logging
import os
import sys
import threading
import time
from dataclasses import dataclass, field
from types import SimpleNamespace
from typing import Dict, List, Optional


CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(CURRENT_DIR)
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

parser = argparse.ArgumentParser(add_help=False)
parser.add_argument("--qt-mode", default="auto")
args, qt_args = parser.parse_known_args()

from runtime_bootstrap import configure_runtime

configure_runtime(args.qt_mode)

from PySide6.QtCore import QObject, QTimer, Qt, Signal
from PySide6.QtWidgets import QApplication, QLabel, QMainWindow

from page import config
from qtDesigner.qt_home import Ui_HomeWindow


GREEN_STYLE = (
    "QGroupBox { background-color: #CAF982; border: 1px solid #797979; "
    "border-radius: 5px; }"
)
RED_STYLE = (
    "QGroupBox { background-color: #EC808D; border: 1px solid #797979; "
    "border-radius: 5px; }"
)
NEUTRAL_STYLE = (
    "QGroupBox { background-color: #F2F2F2; border: 1px solid #797979; "
    "border-radius: 5px; }"
)


def make_box_codes(prefix: str, count: int) -> List[Dict[str, str]]:
    return [
        {"data": f"mock://{prefix}/box/{index}", "type": "QRCODE"}
        for index in range(1, count + 1)
    ]


def initial_demo_state() -> "DemoState":
    case_code = "1781762902048"
    bundles = [
        {"boxContents": make_box_codes(f"case/{case_code}/bundle/{index}", 10)}
        for index in range(1, 5)
    ]
    return DemoState(
        case_code=case_code,
        packed_bundles=bundles,
        current_scan=[],
        recognized_boxes=40,
    )


@dataclass
class DemoState:
    case_code: Optional[str] = None
    packed_bundles: List[Dict[str, List[Dict[str, str]]]] = field(default_factory=list)
    current_scan: List[Dict[str, str]] = field(default_factory=list)
    recognized_boxes: int = 0
    recognized_cases: int = 0
    pending_uploads: int = 0


class ButtonBridge(QObject):
    activated = Signal()

    def click(self) -> None:
        self.activated.emit()


class DemoWindow(QMainWindow, Ui_HomeWindow):
    serial_status = Signal(str)
    hardware_event = Signal(str, int, bool)
    raw_serial_data = Signal(str, str)

    def __init__(self) -> None:
        super().__init__()
        self.setupUi(self)
        self.setWindowTitle("扫码识别系统 - 按钮功能演示模式")

        self.state = initial_demo_state()
        self.event_history: List[str] = []
        self.rs485_connections = {}

        self._create_status_panel()
        self._connect_demo_buttons()
        self._create_rs485_bridges()
        self.serial_status.connect(self.record_event)
        self.hardware_event.connect(self.on_hardware_event)
        self.raw_serial_data.connect(self.on_raw_serial_data)

        self.clock_timer = QTimer(self)
        self.clock_timer.timeout.connect(self.update_clock)
        self.clock_timer.start(1000)
        self.update_clock()

        self.render_from_state()
        self.record_event(
            "演示启动：已加载1个模拟箱码和4组装箱数据；可点击左下角按钮或实体按钮。"
        )
        self._start_rs485_listener()

    def _create_status_panel(self) -> None:
        self.status_panel = QLabel(self.widgetDisplay)
        self.status_panel.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.status_panel.setWordWrap(True)
        self.status_panel.setStyleSheet(
            "QLabel { color: #63FF8B; background-color: rgba(0, 0, 0, 205); "
            "border: 2px solid #63FF8B; border-radius: 12px; padding: 18px; "
            "font-size: 20px; font-weight: bold; }"
        )
        self._resize_status_panel()
        self.status_panel.show()

    def _resize_status_panel(self) -> None:
        width = max(420, self.widgetDisplay.width() - 60)
        self.status_panel.setGeometry(30, 30, width, 360)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        if hasattr(self, "status_panel"):
            self._resize_status_panel()

    def _connect_demo_buttons(self) -> None:
        self.button_cancel.clicked.connect(self.demo_device_reset)
        self.button_ok.clicked.connect(self.demo_confirm_entry)
        self.button_again.clicked.connect(self.demo_manual_recognition)
        self.button_print.clicked.connect(self.demo_print_case_code)

        self.label_clear.clicked.connect(self.demo_clear_counts)
        self.button_reset.clicked.connect(self.demo_full_reset)
        self.button_Restart.clicked.connect(self.demo_restart)
        self.pushButton.clicked.connect(
            lambda: self.record_event("手动数据上传：演示模式不会连接服务器或上传数据。")
        )
        self.button_logs.clicked.connect(
            lambda: self.record_event("日志按钮：正式程序用于查看运行日志。")
        )
        self.button_setting.clicked.connect(
            lambda: self.record_event("设置按钮：正式程序用于配置串口、打印机和服务器。")
        )

    def _create_rs485_bridges(self) -> None:
        mapping = {
            "button_again": self.button_again,
            "button_cancel": self.button_cancel,
            "button_ok": self.button_ok,
            "button_print": self.button_print,
        }
        proxy_buttons = {}
        self.rs485_bridges = []
        for name, real_button in mapping.items():
            bridge = ButtonBridge(self)
            bridge.activated.connect(real_button.click)
            self.rs485_bridges.append(bridge)
            proxy_buttons[name] = bridge
        self.rs485_home_adapter = SimpleNamespace(
            main_window=SimpleNamespace(**proxy_buttons),
            on_rs485_event=lambda port, channel, pressed: self.hardware_event.emit(
                port, channel, pressed
            ),
            on_rs485_raw_data=lambda port, hex_data: self.raw_serial_data.emit(
                port, hex_data
            ),
        )

    def _start_rs485_listener(self) -> None:
        try:
            from serial.tools import list_ports

            port_items = list(list_ports.comports())
            available_ports = [item.device for item in port_items]
            if not available_ports:
                self.record_event("实体按钮测试：没有发现任何COM串口。")
                return
            port_details = "; ".join(
                f"{item.device}={item.description}" for item in port_items
            )
            self.record_event(
                f"发现串口：{port_details}"
            )
            self.record_event(
                f"正在同时监听 {', '.join(available_ports)}，请逐个按顶部4个按钮。"
            )
            for port in available_ports:
                worker = threading.Thread(
                    target=self._listen_to_rs485,
                    args=(port,),
                    daemon=True,
                )
                worker.start()
        except Exception as exc:
            self.record_event(f"RS485初始化失败：{exc}；仍可使用界面按钮演示。")

    def _listen_to_rs485(self, port: str) -> None:
        try:
            from utils.RS485Utils import RS485Utils

            connection = RS485Utils(
                port=port,
                baudrate=9600,
                home_instance=self.rs485_home_adapter,
            )
            self.rs485_connections[port] = connection
            connection.connect()
            self.serial_status.emit(f"已打开 {port}，正在等待顶部实体按钮数据。")
            connection.listen()
        except Exception as exc:
            self.serial_status.emit(
                f"{port}打开失败：{exc}"
            )

    def on_hardware_event(self, port: str, channel: int, pressed: bool) -> None:
        action = "按下" if pressed else "释放"
        self.record_event(f"顶部实体输入：{port} / 通道{channel} / {action}")

    def on_raw_serial_data(self, port: str, hex_data: str) -> None:
        self.record_event(f"串口原始数据：{port} → {hex_data}")

    def update_clock(self) -> None:
        self.label_date.setText(datetime.datetime.now().strftime("%Y年%m月%d日 %H:%M:%S"))

    def record_event(self, message: str) -> None:
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        self.event_history.append(f"{timestamp}  {message}")
        self.event_history = self.event_history[-6:]
        mapping_text = (
            "按钮映射：\n"
            "通道1=拍照识别； 通道2=打印箱码；\n"
            "通道3=确认录入； 通道4=设备复位。\n\n"
            "最近反馈：\n"
        )
        self.status_panel.setText(mapping_text + "\n".join(self.event_history))
        logging.info(message)

    def render_from_state(self) -> None:
        self.label_data_case.setText(str(self.state.recognized_cases))
        self.label_data_box.setText(str(self.state.recognized_boxes))
        self.label_data_unline.setText(str(self.state.pending_uploads))

        if self.state.case_code:
            self.taps_20.setText(self.state.case_code)
            self.groupBox_box_0.setStyleSheet(GREEN_STYLE)
        else:
            self.taps_20.setText("请打印箱码")
            self.groupBox_box_0.setStyleSheet(RED_STYLE)

        bundle_count = min(len(self.state.packed_bundles), 10)
        self.label_result_case.setText(f"【{bundle_count}/10捆】")
        case_groups = [getattr(self, f"groupBox_box_{index}") for index in range(1, 11)]
        for index, group in enumerate(case_groups, start=1):
            group.setStyleSheet(GREEN_STYLE if index <= bundle_count else RED_STYLE)

        scan_count = min(len(self.state.current_scan), 10)
        self.label_result_box.setText(f"【{scan_count}/10盒】")
        result_groups = [
            getattr(self, f"groupBox_result_{index}") for index in range(1, 11)
        ]
        for index, group in enumerate(result_groups, start=1):
            if scan_count == 0:
                group.setStyleSheet(NEUTRAL_STYLE)
            else:
                group.setStyleSheet(GREEN_STYLE if index <= scan_count else RED_STYLE)

    def demo_manual_recognition(self) -> None:
        if not self.state.case_code:
            self.record_event("手动识别：当前没有箱码；正式程序会提示先打印箱码。")
            return
        stamp = int(time.time() * 1000)
        self.state.current_scan = make_box_codes(f"scan/{stamp}", 6)
        self.render_from_state()
        self.record_event(
            "手动识别：模拟识别到6个盒码，下方1～6变绿、7～10变红。"
        )

    def demo_confirm_entry(self) -> None:
        if not self.state.current_scan:
            self.record_event("确认录入：没有本次识别数据，正式程序会提示先扫描盒码。")
            return
        if not self.state.case_code:
            self.record_event("确认录入：没有箱码，正式程序会拒绝录入。")
            return
        previous = len(self.state.packed_bundles)
        self.state.packed_bundles.append(
            {"boxContents": list(self.state.current_scan)}
        )
        self.state.recognized_boxes += len(self.state.current_scan)
        accepted = len(self.state.current_scan)
        self.state.current_scan = []
        self.render_from_state()
        self.record_event(
            f"确认录入：模拟录入{accepted}个盒码，装箱进度{previous}→{len(self.state.packed_bundles)}。"
        )

    def demo_device_reset(self) -> None:
        self.state.current_scan = []
        self.render_from_state()
        self.record_event(
            "设备复位：清除本次识别结果并恢复实时画面；箱码和装箱进度保留。"
        )

    def demo_print_case_code(self) -> None:
        self.state.case_code = str(int(time.time() * 1000))
        self.state.packed_bundles = []
        self.state.current_scan = []
        self.render_from_state()
        self.record_event(
            "打印箱码：生成新箱码并清空当前装箱进度；演示模式不会调用打印机。"
        )

    def demo_clear_counts(self) -> None:
        self.state.recognized_boxes = 0
        self.state.recognized_cases = 0
        self.render_from_state()
        self.record_event(
            "计数归零：只清零已识别箱/盒累计数，当前箱码和装箱进度不变。"
        )

    def demo_full_reset(self) -> None:
        self.state.case_code = None
        self.state.packed_bundles = []
        self.state.current_scan = []
        self.render_from_state()
        self.record_event("顶部重置：清除当前箱码、装箱进度和本次识别数据。")

    def demo_restart(self) -> None:
        self.state = initial_demo_state()
        self.render_from_state()
        self.record_event("顶部重启：演示数据已恢复到初始的4/10状态。")

    def closeEvent(self, event) -> None:
        for connection in self.rs485_connections.values():
            try:
                connection.close()
            except Exception:
                pass
        event.accept()


def main() -> int:
    log_dir = os.path.join(CURRENT_DIR, "logs")
    os.makedirs(log_dir, exist_ok=True)
    log_handler = logging.FileHandler(
        os.path.join(log_dir, "button_demo.log"),
        encoding="utf-8",
    )
    console_handler = logging.StreamHandler()
    logging.basicConfig(
        handlers=[log_handler, console_handler],
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )

    app = QApplication([sys.argv[0], *qt_args])
    window = DemoWindow()
    window.showFullScreen()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
