"""WDIP补光灯真实亮度控制与基于识别结果的二分法校准。"""

from __future__ import annotations

import json
import logging
import os
import statistics
import time

from PySide6.QtCore import QThread, Qt, QTimer, Signal, Slot
from PySide6.QtWidgets import (
    QDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSlider,
    QVBoxLayout,
)

from utils.wdip_light_controller import WDIPLightController


logger = logging.getLogger("LightControlDialog")

NATIVE_BTN_STYLE = (
    "QPushButton { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #F8F8F8, stop:1 #E0E0E0); "
    "border: 1px solid #707070; border-radius: 2px; font-weight: bold; color: #000; padding: 4px 10px; } "
    "QPushButton:hover { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #FFFFFF, stop:1 #D8D8D8); border-color: #505050; } "
    "QPushButton:pressed { background: #D0D0D0; border-color: #404040; }"
)


def voltage_for_percent(minimum_voltage_v: float, maximum_voltage_v: float, percent: int) -> float:
    value = max(0, min(100, int(percent)))
    return minimum_voltage_v + (maximum_voltage_v - minimum_voltage_v) * value / 100.0


def percent_for_voltage(minimum_voltage_v: float, maximum_voltage_v: float, voltage_v: float) -> int:
    if maximum_voltage_v <= minimum_voltage_v:
        raise ValueError("补光灯最高电压必须大于最低电压")
    percent = round(
        (float(voltage_v) - minimum_voltage_v)
        / (maximum_voltage_v - minimum_voltage_v)
        * 100.0
    )
    return max(0, min(100, int(percent)))


def load_light_config() -> dict:
    config_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "config", "settings.json")
    )
    try:
        with open(config_path, "r", encoding="utf-8") as stream:
            return dict(json.load(stream).get("light_controller", {}))
    except Exception as exc:
        logger.warning(f"读取补光灯配置失败: {exc}")
        return {}


def save_light_config_updates(updates: dict) -> None:
    """保存真实校准结果，供下次启动直接使用；不涉及数据库。"""
    config_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "config", "settings.json")
    )
    data = {}
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as stream:
            data = json.load(stream)
    light_config = data.setdefault("light_controller", {})
    light_config.update(dict(updates))
    with open(config_path, "w", encoding="utf-8") as stream:
        json.dump(data, stream, ensure_ascii=False, indent=2)


class LightBinarySearchWorker(QThread):
    """真实控制WDIP输出电压，并用真实相机解码成功率和耗时选择亮度。"""

    progress_signal = Signal(int, str)
    finished_signal = Signal(bool, int, str)

    def __init__(
        self,
        home_instance,
        controller: WDIPLightController,
        safe_min_voltage_v: float,
        safe_max_voltage_v: float,
        samples_per_level: int = 5,
        settle_ms: int = 350,
        minimum_percent: int = 0,
        direct_voltage_control: bool = False,
        original_voltage_v: float = None,
        original_percent: int = 0,
    ):
        super().__init__()
        self.home = home_instance
        self.controller = controller
        self.safe_min_voltage_v = float(safe_min_voltage_v)
        self.safe_max_voltage_v = float(safe_max_voltage_v)
        self.samples_per_level = max(2, int(samples_per_level))
        self.settle_seconds = max(0.15, int(settle_ms) / 1000.0)
        self.minimum_percent = max(0, min(90, int(minimum_percent)))
        self.direct_voltage_control = bool(direct_voltage_control)
        self.original_voltage_v = (
            None if original_voltage_v is None else float(original_voltage_v)
        )
        self.original_percent = int(original_percent)
        self._is_interrupted = False
        try:
            from page.config import CONFIG_DATA
            self.expected_code_count = max(
                1, int(CONFIG_DATA.get("edit_max_jian", 10))
            )
        except Exception:
            self.expected_code_count = 10

    def requestInterruption(self):
        self._is_interrupted = True
        super().requestInterruption()

    def is_interrupted(self) -> bool:
        if getattr(self, "_is_interrupted", False):
            return True
        if self.isInterruptionRequested():
            return True
        try:
            curr = QThread.currentThread()
            if curr and curr.isInterruptionRequested():
                return True
        except Exception:
            pass
        return False

    def _sleep_with_check(self, seconds: float):
        deadline = time.monotonic() + max(0.0, float(seconds))
        while time.monotonic() < deadline:
            if self.is_interrupted():
                raise InterruptedError("用户终止灯光校准")
            time.sleep(min(0.04, max(0.001, deadline - time.monotonic())))

    def _camera(self):
        from page.home import obj_cam_operation

        return obj_cam_operation

    def _measure_level(self, cam_op, percent: int, sample_count=None):
        from utils.pyzbar_utils import decode_image_codes

        if self.is_interrupted():
            raise InterruptedError("用户终止灯光校准")

        voltage = voltage_for_percent(
            self.safe_min_voltage_v,
            self.safe_max_voltage_v,
            percent,
        )
        if self.direct_voltage_control:
            # 现场WDIP返回数据受串口转换器影响不能稳定通过CRC，但同一条写入命令
            # 已能真实改变灯泡亮度。校准直接复用手动调光的可靠写入路径。
            self.controller.set_voltage_direct(voltage)
            applied_voltage = voltage
        else:
            state = self.controller.set_voltage(voltage)
            if not state.output_enabled:
                raise RuntimeError("WDIP输出处于关闭状态，不能进行真实灯光校准")
            applied_voltage = state.set_voltage_v

        self._sleep_with_check(self.settle_seconds)

        counts = []
        elapsed_values = []
        sample_total = max(
            2,
            int(sample_count if sample_count is not None else self.samples_per_level),
        )
        for _ in range(sample_total):
            if self.is_interrupted():
                raise InterruptedError("用户终止灯光校准")
            self._sleep_with_check(0.10)
            image = cam_op.get_np_array_image()
            start = time.perf_counter()
            codes = decode_image_codes(image)
            elapsed_values.append((time.perf_counter() - start) * 1000.0)
            counts.append(len(codes))

        success_samples = sum(1 for count in counts if count > 0)
        full_samples = sum(
            1 for count in counts if count >= self.expected_code_count
        )
        return {
            "percent": percent,
            "voltage": applied_voltage,
            "success_rate": success_samples / sample_total,
            "full_rate": full_samples / sample_total,
            "average_count": sum(counts) / len(counts),
            "count_stdev": statistics.pstdev(counts) if len(counts) > 1 else 0.0,
            "median_ms": statistics.median(elapsed_values),
            "counts": counts,
        }

    def run(self):
        original_voltage = None
        try:
            cam_op = self._camera()
            if not cam_op or not getattr(cam_op, "b_start_grabbing", False):
                raise RuntimeError("海康相机尚未开始真实取流")

            if self.direct_voltage_control:
                original_voltage = self.original_voltage_v
            else:
                initial_state = self.controller.read_state()
                original_voltage = initial_state.set_voltage_v
                if not initial_state.output_enabled:
                    raise RuntimeError("WDIP补光灯输出未打开，请先在电源控制器上打开输出")
            if not 0 <= self.safe_min_voltage_v < self.safe_max_voltage_v <= 24:
                raise RuntimeError("补光灯安全电压范围必须满足 0≤最低值<最高值≤24V")

            logger.info(
                "开始真实灯光二分校准: port=%s range=%.2f~%.2fV samples=%s direct=%s",
                self.controller.port,
                self.safe_min_voltage_v,
                self.safe_max_voltage_v,
                self.samples_per_level,
                self.direct_voltage_control,
            )

            results = []
            max_iterations = 7
            total_levels = max_iterations + 1

            # 先实测打开页面时的真实安全上限，再按区间宽度逐层二分。
            # 识别效果不一定随亮度单调变化，因此不能用“成功就向低、失败就向高”的假设。
            self.progress_signal.emit(
                5,
                f"实测安全范围上限 100%（{self.safe_max_voltage_v:.2f}V），"
                f"采样{self.samples_per_level}帧...",
            )
            baseline = self._measure_level(cam_op, 100)
            results.append(baseline)
            logger.info(
                "LIGHT-SAMPLE percent=%s voltage=%.2f success=%.0f%% avg_codes=%.2f median=%.1fms counts=%s",
                baseline["percent"],
                baseline["voltage"],
                baseline["success_rate"] * 100,
                baseline["average_count"],
                baseline["median_ms"],
                baseline["counts"],
            )

            intervals = [(self.minimum_percent, 99)]
            step = 0
            tested_percents = {100}
            while intervals and step < max_iterations:
                if self.is_interrupted():
                    raise InterruptedError("用户终止灯光校准")
                interval_index, (low, high) = max(
                    enumerate(intervals),
                    key=lambda item: item[1][1] - item[1][0],
                )
                intervals.pop(interval_index)
                if low > high:
                    continue
                step += 1
                mid = (low + high) // 2
                if mid in tested_percents:
                    continue
                tested_percents.add(mid)
                voltage = voltage_for_percent(
                    self.safe_min_voltage_v,
                    self.safe_max_voltage_v,
                    mid,
                )
                self.progress_signal.emit(
                    int((step + 1) / total_levels * 90),
                    f"区间二分实测 {mid}%（{voltage:.2f}V），"
                    f"采样{self.samples_per_level}帧识别结果和耗时 ({step}/{max_iterations})...",
                )
                measurement = self._measure_level(cam_op, mid)
                results.append(measurement)
                logger.info(
                    "LIGHT-SAMPLE percent=%s voltage=%.2f success=%.0f%% avg_codes=%.2f median=%.1fms counts=%s",
                    mid,
                    measurement["voltage"],
                    measurement["success_rate"] * 100,
                    measurement["average_count"],
                    measurement["median_ms"],
                    measurement["counts"],
                )
                if low <= mid - 1:
                    intervals.append((low, mid - 1))
                if mid + 1 <= high:
                    intervals.append((mid + 1, high))

            valid_results = [item for item in results if item["success_rate"] > 0]
            if not valid_results:
                if original_voltage is not None:
                    if self.direct_voltage_control:
                        self.controller.set_voltage_direct(original_voltage)
                    else:
                        self.controller.set_voltage(original_voltage)
                raise RuntimeError(
                    "所有实测亮度均未识别到真实码；已恢复校准前电压，请确认盒子在取景区内"
                )

            def rank_measurement(item):
                return (
                    item["full_rate"],
                    item["average_count"],
                    item["success_rate"],
                    -item["count_stdev"],
                    -item["median_ms"],
                    -item["percent"],
                )

            # 第一阶段只负责找候选区间；对前三名各增加至少10个真实帧复测，
            # 防止某一档偶然识别好就被选为最终亮度。
            shortlist = sorted(
                valid_results,
                key=rank_measurement,
                reverse=True,
            )[:3]
            verification_samples = max(10, self.samples_per_level * 2)
            verified_results = []
            for verify_index, candidate in enumerate(shortlist, start=1):
                self.progress_signal.emit(
                    90 + verify_index * 2,
                    f"稳定性复测 {candidate['percent']}%（{candidate['voltage']:.2f}V），"
                    f"连续采样{verification_samples}个真实帧 ({verify_index}/{len(shortlist)})...",
                )
                verified = self._measure_level(
                    cam_op,
                    candidate["percent"],
                    sample_count=verification_samples,
                )
                verified_results.append(verified)
                logger.info(
                    "LIGHT-VERIFY percent=%s voltage=%.2f full=%.0f%% success=%.0f%% "
                    "avg_codes=%.2f stdev=%.2f median=%.1fms counts=%s",
                    verified["percent"],
                    verified["voltage"],
                    verified["full_rate"] * 100,
                    verified["success_rate"] * 100,
                    verified["average_count"],
                    verified["count_stdev"],
                    verified["median_ms"],
                    verified["counts"],
                )

            verified_valid = [
                item for item in verified_results if item["success_rate"] > 0
            ]
            if not verified_valid:
                raise RuntimeError(
                    "候选亮度复测时均未识别到真实码；请保持产品和相机完全不动后重试"
                )
            best = max(verified_valid, key=rank_measurement)
            if self.direct_voltage_control:
                self.controller.set_voltage_direct(best["voltage"])
                final_voltage = best["voltage"]
                voltage_text = f"目标输出{final_voltage:.2f}V"
            else:
                final_state = self.controller.set_voltage(best["voltage"])
                final_voltage = final_state.set_voltage_v
                voltage_text = f"回读{final_voltage:.2f}V"
            message = (
                f"真实校准完成：WDIP端口 {self.controller.port}，"
                f"最佳亮度 {best['percent']}%（{voltage_text}）；"
                f"{self.expected_code_count}盒完整识别率 {best['full_rate'] * 100:.0f}%，"
                f"任意码识别率 {best['success_rate'] * 100:.0f}%，"
                f"平均识别 {best['average_count']:.1f} 个码/帧，"
                f"数量波动 {best['count_stdev']:.2f}，"
                f"解码中位耗时 {best['median_ms']:.1f}ms。"
            )
            self.progress_signal.emit(100, message)
            self.finished_signal.emit(True, int(best["percent"]), message)
        except InterruptedError as exc:
            if original_voltage is not None:
                try:
                    if self.direct_voltage_control:
                        self.controller.set_voltage_direct(original_voltage)
                    else:
                        self.controller.set_voltage(original_voltage)
                except Exception:
                    pass
            self.finished_signal.emit(False, 0, str(exc))
        except Exception as exc:
            logger.exception("真实灯光二分校准失败")
            restore_message = ""
            if original_voltage is not None:
                try:
                    if self.direct_voltage_control:
                        self.controller.set_voltage_direct(original_voltage)
                        restored_voltage = original_voltage
                    else:
                        restored_state = self.controller.set_voltage(original_voltage)
                        restored_voltage = restored_state.set_voltage_v
                    restore_message = f"；已恢复校准前电压 {restored_voltage:.2f}V"
                except Exception as restore_exc:
                    logger.exception("灯光校准失败后恢复原电压也失败")
                    restore_message = f"；恢复原电压失败：{restore_exc}"
            self.finished_signal.emit(False, 0, f"{exc}{restore_message}")


class LightControlDialog(QDialog):
    """直接控制WDIP输出电压，从而调节物理灯泡亮度。"""

    def __init__(self, home_instance, parent=None):
        super().__init__(parent)
        self.home = home_instance
        self.setWindowTitle("WDIP输出电压与灯光亮度控制")
        self.resize(500, 230)
        self.setWindowModality(Qt.WindowModal)

        self.worker = None
        self.controller = None
        self._loading_value = False
        self._commanded_output_enabled = None
        self.light_config = load_light_config()
        self.direct_voltage_control = bool(
            self.light_config.get("direct_voltage_control", False)
        )
        self.safe_min_voltage_v = float(self.light_config.get("minimum_voltage_v", 8.0))
        self.safe_max_voltage_v = float(self.light_config.get("maximum_voltage_v", 12.0))
        self.apply_timer = QTimer(self)
        self.apply_timer.setSingleShot(True)
        # 只有滑块停止一段时间后才真正写电压，拖动过程不会连续轰炸RS485。
        self.apply_timer.setInterval(600)
        self.apply_timer.timeout.connect(self.apply_slider_value)
        self.init_ui()
        if self.direct_voltage_control:
            self.prepare_direct_voltage_control()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        manual_group = QGroupBox("WDIP物理补光灯手动调节")
        manual_layout = QVBoxLayout(manual_group)

        self.label_value = QLabel("当前灯光亮度: 正在读取真实控制器...")
        self.label_value.setStyleSheet("font-size: 14px; font-weight: bold; color: #2B579A;")
        manual_layout.addWidget(self.label_value)

        configured_port = self.light_config.get("port") or "自动查找"
        self.btn_refresh = QPushButton(f"读取/重新连接WDIP（{configured_port}）")
        self.btn_refresh.setStyleSheet(NATIVE_BTN_STYLE)
        self.btn_refresh.clicked.connect(self.load_current_camera_brightness)
        manual_layout.addWidget(self.btn_refresh)

        self.btn_output = QPushButton("读取后可开启灯光输出")
        self.btn_output.setStyleSheet(NATIVE_BTN_STYLE)
        self.btn_output.setEnabled(False)
        self.btn_output.clicked.connect(self.on_output_clicked)
        manual_layout.addWidget(self.btn_output)

        slider_layout = QHBoxLayout()
        self.btn_minus = QPushButton(" - ")
        self.btn_minus.setFixedWidth(40)
        self.btn_minus.setStyleSheet(NATIVE_BTN_STYLE)
        self.btn_minus.setEnabled(False)
        self.btn_minus.setFixedWidth(50)
        self.btn_minus.setFixedHeight(45)

        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(0, 100)
        self.slider.setValue(0)
        self.slider.setSingleStep(1)
        self.slider.setPageStep(5)
        self.slider.setMinimumHeight(48)
        self.slider.setEnabled(False)
        self.slider.setStyleSheet("""
            QSlider::groove:horizontal {
                border: 1px solid #b0b0b0;
                height: 16px;
                background: #e0e0e0;
                border-radius: 8px;
            }
            QSlider::sub-page:horizontal {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #1890ff, stop:1 #52c41a);
                border-radius: 8px;
            }
            QSlider::handle:horizontal {
                background: #ffffff;
                border: 3px solid #1890ff;
                width: 36px;
                height: 36px;
                margin: -10px 0;
                border-radius: 18px;
            }
            QSlider::handle:horizontal:hover {
                background: #e6f7ff;
                border-color: #40a9ff;
            }
        """)
        self.slider.valueChanged.connect(self.on_slider_changed)
        slider_layout.addWidget(self.slider)

        self.btn_plus = QPushButton(" + ")
        self.btn_plus.setFixedWidth(50)
        self.btn_plus.setFixedHeight(45)
        self.btn_plus.setStyleSheet(NATIVE_BTN_STYLE)
        self.btn_plus.setEnabled(False)
        self.btn_plus.clicked.connect(self.on_plus_clicked)
        slider_layout.addWidget(self.btn_plus)
        manual_layout.addLayout(slider_layout)
        main_layout.addWidget(manual_group)

        auto_group = QGroupBox("二分法真实识别亮度校准")
        auto_layout = QVBoxLayout(auto_group)
        btn_center_box = QHBoxLayout()
        btn_center_box.addStretch()
        self.btn_calibrate = QPushButton("⚡ 开始真实二分法校准")
        self.btn_calibrate.setStyleSheet(NATIVE_BTN_STYLE)
        self.btn_calibrate.setEnabled(False)
        self.btn_calibrate.clicked.connect(self.on_calibrate_clicked)
        btn_center_box.addWidget(self.btn_calibrate)
        btn_center_box.addStretch()
        auto_layout.addLayout(btn_center_box)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        auto_layout.addWidget(self.progress_bar)

        self.label_status = QLabel("正在查找并读取真实WDIP补光灯控制器。")
        self.label_status.setStyleSheet("color: #666; font-size: 11px;")
        self.label_status.setWordWrap(True)
        main_layout.addWidget(auto_group)
        auto_group.setVisible(True)
        main_layout.addWidget(self.label_status)

        bottom_box = QHBoxLayout()
        bottom_box.addStretch()
        self.btn_close = QPushButton("关闭")
        self.btn_close.setFixedWidth(90)
        self.btn_close.setStyleSheet(NATIVE_BTN_STYLE)
        self.btn_close.clicked.connect(self.accept)
        bottom_box.addWidget(self.btn_close)
        main_layout.addLayout(bottom_box)

    def _create_controller(self):
        from page.config import CONFIG_DATA

        button_port = CONFIG_DATA.get("combobox_comSelect")
        configured_port = self.light_config.get("port") or None
        return WDIPLightController(
            port=configured_port,
            baudrate=int(self.light_config.get("baudrate", 9600)),
            slave_addr=int(self.light_config.get("slave_addr", 1)),
            timeout=float(self.light_config.get("timeout_seconds", 0.8)),
            excluded_ports=[] if configured_port else [button_port],
            allow_stable_crc_mismatch_readback=bool(
                self.light_config.get("allow_stable_crc_mismatch_readback", False)
            ),
            minimum_request_interval=float(
                self.light_config.get("minimum_request_interval_ms", 250)
            ) / 1000.0,
            write_settle_seconds=float(
                self.light_config.get("write_settle_ms", 400)
            ) / 1000.0,
            shared_exchange=getattr(
                self.home.main_window, "exchange_shared_rs485", None
            ),
        )

    def prepare_direct_voltage_control(self):
        """启用8~12V直接写入；不要求WDIP先返回有效数据。"""
        if self.controller is None:
            self.controller = self._create_controller()
        if not getattr(self, "_direct_mode_prepared", False):
            configured_voltage = float(
                self.light_config.get("startup_voltage_v", self.safe_min_voltage_v)
            )
            configured_voltage = max(
                self.safe_min_voltage_v,
                min(self.safe_max_voltage_v, configured_voltage),
            )
            self._loading_value = True
            self.slider.setValue(
                percent_for_voltage(
                    self.safe_min_voltage_v,
                    self.safe_max_voltage_v,
                    configured_voltage,
                )
            )
            self._loading_value = False
            self._direct_mode_prepared = True
        self.btn_refresh.setVisible(False)
        self.slider.setEnabled(True)
        self.btn_minus.setEnabled(True)
        self.btn_plus.setEnabled(True)
        self.btn_output.setEnabled(True)
        self.btn_calibrate.setEnabled(True)
        voltage = voltage_for_percent(
            self.safe_min_voltage_v,
            self.safe_max_voltage_v,
            self.slider.value(),
        )
        self.label_value.setText(
            f"直接控制目标: {self.slider.value()}%（{voltage:.2f}V）"
        )
        if self._commanded_output_enabled:
            self.btn_output.setText("直接关闭灯光输出")
        else:
            self.btn_output.setText(f"直接开启{voltage:.2f}V灯光输出")
        self.label_status.setText(
            "直接控制模式：调节滑块会向WDIP发送8~12V设定命令；"
            "不依赖设备返回数据，是否生效以灯泡实际亮度为准。"
        )

    def load_current_camera_brightness(self):
        """兼容原调用名：实际读取WDIP物理灯的设置电压，不读取相机曝光。"""
        self.btn_refresh.setEnabled(False)
        self.label_status.setText("正在通过串口读取WDIP真实电压状态...")
        try:
            if self.controller is None:
                self.controller = self._create_controller()
            if not 0 <= self.safe_min_voltage_v < self.safe_max_voltage_v <= 24:
                raise RuntimeError("灯光电压范围配置错误，必须满足 0≤最低值<最高值≤24V")
            state = self.controller.discover() if not self.controller.port else self.controller.read_state()
            self._show_state(state)
        except Exception as exc:
            logger.warning(f"读取真实补光灯状态失败: {exc}")
            self.slider.setEnabled(self.direct_voltage_control)
            self.btn_minus.setEnabled(self.direct_voltage_control)
            self.btn_plus.setEnabled(self.direct_voltage_control)
            self.btn_output.setEnabled(self.direct_voltage_control)
            self.btn_calibrate.setEnabled(self.direct_voltage_control)
            self.label_value.setText("当前灯光亮度: 未读取到真实控制器")
            detail = str(exc)
            if "PermissionError" in detail or "拒绝访问" in detail:
                port = self.light_config.get("port") or "目标串口"
                detail = (
                    f"{port}被其他程序占用，主程序无法直接控制WDIP。"
                    "请完全退出WDIP厂家上位机；若已退出，请确认顶部按钮监听没有占用同一串口，"
                    "然后点击上方“读取/重新连接WDIP”重试。"
                )
            suffix = (
                "；仍可使用8~12V直接控制，实际结果以灯泡亮度为准。"
                if self.direct_voltage_control and "被其他程序占用" not in detail
                else ""
            )
            self.label_status.setText(f"读取WDIP失败：{detail}{suffix}")
        finally:
            self.btn_refresh.setEnabled(True)

    def _show_state(self, state, action_text=""):
        has_voltage = 0 <= self.safe_min_voltage_v < self.safe_max_voltage_v <= 24
        has_current = state.set_current_a > 0
        percent = 0
        if has_voltage:
            percent = percent_for_voltage(
                self.safe_min_voltage_v,
                self.safe_max_voltage_v,
                state.set_voltage_v,
            )
            self._loading_value = True
            self.slider.setValue(percent)
            self._loading_value = False

        manual_enabled = bool(
            has_voltage and (state.output_enabled or self.direct_voltage_control)
        )
        self.slider.setEnabled(manual_enabled)
        self.btn_minus.setEnabled(manual_enabled)
        self.btn_plus.setEnabled(manual_enabled)
        self.btn_calibrate.setEnabled(manual_enabled)
        self.btn_output.setEnabled(bool(has_voltage and has_current))
        self.btn_output.setText("关闭灯光输出" if state.output_enabled else "开启灯光输出")
        self._commanded_output_enabled = state.output_enabled
        output_text = "已打开" if state.output_enabled else "已关闭"
        self.label_value.setText(
            f"灯光输出{output_text}；设定 {state.set_voltage_v:.2f}V / {state.set_current_a:.3f}A；"
            f"实际 {state.output_voltage_v:.2f}V / {state.output_current_a:.3f}A"
        )

        details = action_text or f"已连接WDIP控制器 {self.controller.port}。"
        if not has_voltage:
            details += " 当前设定电压为0V，不能打开输出；请先按灯具铭牌设置真实电压。"
        elif not has_current:
            details += " 当前设定电流为0A，不能打开输出；请先按灯具铭牌设置真实电流。"
        elif not state.output_enabled:
            details += (
                f" 可点击“开启灯光输出”；若当前电压不在"
                f"{self.safe_min_voltage_v:.2f}~{self.safe_max_voltage_v:.2f}V内，"
                f"将先调整到最近边界值。程序不会自动改写电流。"
            )
        else:
            details += (
                f" 当前调光位置{percent}%（范围{self.safe_min_voltage_v:.2f}~"
                f"{self.safe_max_voltage_v:.2f}V）；可手动调节，"
                "连接相机后再进行真实二分法校准。"
            )
        self.label_status.setText(details)

    def on_output_clicked(self):
        if not self.controller:
            return
        self.apply_timer.stop()
        if self.direct_voltage_control:
            try:
                enable = not bool(self._commanded_output_enabled)
                if enable:
                    voltage = voltage_for_percent(
                        self.safe_min_voltage_v,
                        self.safe_max_voltage_v,
                        self.slider.value(),
                    )
                    self.controller.set_voltage_direct(voltage)
                self.controller.set_output_enabled_direct(enable)
                self._commanded_output_enabled = enable
                self.btn_output.setText(
                    "直接关闭灯光输出" if enable else "直接开启灯光输出"
                )
                self.label_status.setText(
                    f"已向WDIP直接发送输出{'ON' if enable else 'OFF'}命令；"
                    "未采用返回数据，请观察灯泡实际状态。"
                )
            except Exception as exc:
                logger.exception("直接切换WDIP灯光输出失败")
                self.label_status.setText(f"直接切换灯光输出失败：{exc}")
            return
        try:
            current = self.controller.read_state()
            if current.output_enabled:
                state = self.controller.set_output_enabled(False)
                self._show_state(state, "已写入输出关闭命令并回读确认。")
                return
            if current.set_voltage_v <= 0 or current.set_current_a <= 0:
                QMessageBox.warning(
                    self,
                    "不能开启灯光",
                    "WDIP当前设定电压或电流为0。请先依据灯具铭牌设置真实参数。",
                )
                self._show_state(current)
                return
            target_voltage = max(
                self.safe_min_voltage_v,
                min(self.safe_max_voltage_v, current.set_voltage_v),
            )
            voltage_notice = ""
            if abs(target_voltage - current.set_voltage_v) > 0.011:
                voltage_notice = (
                    f"\n当前电压不在{self.safe_min_voltage_v:.2f}~"
                    f"{self.safe_max_voltage_v:.2f}V范围内，将先调整为 "
                    f"{target_voltage:.2f}V。"
                )
            answer = QMessageBox.question(
                self,
                "确认开启真实灯光输出",
                f"设备当前设定为 {current.set_voltage_v:.2f}V / {current.set_current_a:.3f}A。"
                f"{voltage_notice}\n"
                "WDIP模块最大输出功率为15W。\n\n"
                "请确认这与灯具铭牌要求一致，是否开启真实输出？",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if answer != QMessageBox.Yes:
                return
            if abs(target_voltage - current.set_voltage_v) > 0.011:
                current = self.controller.set_voltage(target_voltage)
            state = self.controller.set_output_enabled(True)
            self._show_state(state, "已写入输出开启命令并回读确认。")
        except Exception as exc:
            logger.exception("切换WDIP灯光输出失败")
            self.label_status.setText(f"切换灯光输出失败：{exc}")

    def apply_slider_value(self):
        if not self.controller or not self.safe_max_voltage_v:
            return
        percent = self.slider.value()
        if self.direct_voltage_control:
            voltage = voltage_for_percent(
                self.safe_min_voltage_v,
                self.safe_max_voltage_v,
                percent,
            )
            try:
                self.controller.set_voltage_direct(voltage)
                self.label_value.setText(
                    f"已发送灯光亮度: {percent}%（目标输出 {voltage:.2f}V）"
                )
                self.label_status.setText(
                    f"已向WDIP {self.controller.port} 直接发送 {voltage:.2f}V；"
                    "未采用返回数据，请观察灯泡亮度。"
                )
                save_light_config_updates({
                    "startup_voltage_v": round(float(voltage), 2),
                    "startup_percent": int(percent),
                })
            except Exception as exc:
                logger.warning(f"直接发送WDIP电压失败: {exc}")
                self.label_status.setText(f"直接发送电压失败：{exc}")
            return
        try:
            current = self.controller.read_state()
            if not current.output_enabled:
                self._show_state(current, "灯光输出已关闭，未调整电压。")
                return
            voltage = voltage_for_percent(
                self.safe_min_voltage_v,
                self.safe_max_voltage_v,
                percent,
            )
            state = self.controller.set_voltage(voltage)
            self.label_value.setText(
                f"当前灯光亮度: {percent}%（真实回读设定 {state.set_voltage_v:.2f}V）"
            )
            self.label_status.setText(f"WDIP {self.controller.port} 已确认写入并回读一致。")
        except Exception as exc:
            logger.warning(f"下发真实补光灯亮度失败: {exc}")
            self.label_status.setText(f"灯光调节失败：{exc}")

    def on_slider_changed(self, value):
        if self._loading_value:
            return
        voltage = voltage_for_percent(
            self.safe_min_voltage_v,
            self.safe_max_voltage_v,
            value,
        )
        self.label_value.setText(f"准备设置灯光亮度: {value}%（{voltage:.2f}V）")
        self.apply_timer.start()

    def on_minus_clicked(self):
        self.slider.setValue(max(self.slider.minimum(), self.slider.value() - 2))

    def on_plus_clicked(self):
        self.slider.setValue(min(self.slider.maximum(), self.slider.value() + 2))

    def on_calibrate_clicked(self):
        if not self.controller or not self.safe_max_voltage_v:
            QMessageBox.warning(self, "无法校准", "尚未建立WDIP补光灯控制对象。")
            return
        cam_op = getattr(__import__("page.home", fromlist=["obj_cam_operation"]), "obj_cam_operation", None)
        if not cam_op or not getattr(cam_op, "b_start_grabbing", False):
            QMessageBox.warning(self, "无法校准", "海康相机尚未开始真实取流，请先确认实时画面正常。")
            return
        try:
            if self.direct_voltage_control:
                original_voltage = voltage_for_percent(
                    self.safe_min_voltage_v,
                    self.safe_max_voltage_v,
                    self.slider.value(),
                )
                # 校准动作由用户明确触发，先保证真实灯光输出为ON，再逐档改变电压。
                self.controller.set_output_enabled_direct(True)
                self._commanded_output_enabled = True
                self.btn_output.setText("直接关闭灯光输出")
            else:
                current = self.controller.read_state()
                if not current.output_enabled:
                    QMessageBox.warning(self, "无法校准", "请先开启WDIP真实灯光输出。")
                    self._show_state(current)
                    return
                original_voltage = current.set_voltage_v
        except Exception as exc:
            logger.exception("开始灯光校准前准备失败")
            QMessageBox.warning(self, "无法校准", f"灯光校准准备失败：{exc}")
            self.label_status.setText(f"灯光校准准备失败：{exc}")
            return
        self.apply_timer.stop()
        self.btn_calibrate.setEnabled(False)
        self.slider.setEnabled(False)
        self.btn_minus.setEnabled(False)
        self.btn_plus.setEnabled(False)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(True)
        self.label_status.setText("正在真实改变补光灯电压并采样相机识别成功率、数量和耗时...")

        self.worker = LightBinarySearchWorker(
            self.home,
            self.controller,
            self.safe_min_voltage_v,
            self.safe_max_voltage_v,
            samples_per_level=int(self.light_config.get("samples_per_level", 5)),
            settle_ms=int(self.light_config.get("settle_ms", 500)),
            minimum_percent=int(self.light_config.get("minimum_percent", 0)),
            direct_voltage_control=self.direct_voltage_control,
            original_voltage_v=original_voltage,
        )
        self.worker.progress_signal.connect(self.on_worker_progress)
        self.worker.finished_signal.connect(self.on_worker_finished)
        self.worker.start()

    @Slot(int, str)
    def on_worker_progress(self, percent, msg):
        self.progress_bar.setValue(percent)
        self.label_status.setText(msg)

    @Slot(bool, int, str)
    def on_worker_finished(self, success, percent, msg):
        self.progress_bar.setValue(100 if success else 0)
        self.label_status.setText(msg)
        self.btn_calibrate.setEnabled(True)
        self.slider.setEnabled(True)
        self.btn_minus.setEnabled(True)
        self.btn_plus.setEnabled(True)
        if success:
            self._loading_value = True
            self.slider.setValue(percent)
            self._loading_value = False
            calibrated_voltage = voltage_for_percent(
                self.safe_min_voltage_v,
                self.safe_max_voltage_v,
                percent,
            )
            if self.direct_voltage_control:
                self.label_value.setText(
                    f"校准结果: {percent}%（目标输出 {calibrated_voltage:.2f}V）"
                )
            else:
                try:
                    state = self.controller.read_state()
                    calibrated_voltage = state.set_voltage_v
                    self._show_state(state, msg)
                except Exception as exc:
                    logger.warning(f"校准完成后读取补光灯状态失败: {exc}")
                    self.label_value.setText(
                        f"校准结果: {percent}%（完成后回读失败，请检查连接）"
                    )
            try:
                save_light_config_updates({
                    "startup_voltage_v": round(float(calibrated_voltage), 2),
                    "calibrated_percent": int(percent),
                })
                self.light_config["startup_voltage_v"] = round(float(calibrated_voltage), 2)
                self.light_config["calibrated_percent"] = int(percent)
                logger.info(
                    "已保存真实校准结果作为下次启动亮度: %.2fV (%s%%)",
                    calibrated_voltage,
                    percent,
                )
            except Exception as exc:
                logger.exception(f"保存真实灯光校准结果失败: {exc}")
            QMessageBox.information(self, "真实灯光亮度校准", msg)
        else:
            if not self.direct_voltage_control:
                try:
                    self._show_state(self.controller.read_state(), msg)
                except Exception:
                    pass
            QMessageBox.warning(self, "灯光校准未完成", msg)

    def closeEvent(self, event):
        self.apply_timer.stop()
        if self.worker and self.worker.isRunning():
            self.worker.requestInterruption()
            self.worker.wait(5000)
        super().closeEvent(event)

    def shutdown_output(self) -> bool:
        """主程序正常退出时关闭由本程序控制的WDIP灯光输出。"""
        self.apply_timer.stop()
        if self.worker and self.worker.isRunning():
            self.worker.requestInterruption()
            self.worker.wait(5000)

        if not self.controller:
            logger.info("程序退出：本次运行未建立WDIP灯光控制连接，无需发送关闭命令。")
            return True

        try:
            if self.direct_voltage_control:
                self.controller.set_output_enabled_direct(False)
                logger.info("程序退出：已直接发送WDIP灯光输出OFF命令。")
                return True
            current = self.controller.read_state()
            if not current.output_enabled:
                logger.info("程序退出：WDIP灯光输出原本已关闭。")
                return True
            state = self.controller.set_output_enabled(False)
            if state.output_enabled:
                logger.error("程序退出：已发送WDIP关闭命令，但回读仍为ON。")
                return False
            logger.info("程序退出：WDIP灯光输出已关闭并回读确认。")
            return True
        except Exception as exc:
            logger.exception(f"程序退出时关闭WDIP灯光输出失败: {exc}")
            return False


class LightCalibrateWorker(QThread):
    """供 SettingsDialog Tab3 调用的二分法校准线程适配器。"""

    sig_progress = Signal(int)
    sig_log = Signal(str)
    sig_step = Signal(str)
    sig_finished = Signal(bool, str, dict)

    def __init__(
        self,
        home_instance,
        parent=None,
        original_voltage_v: float = None,
        original_percent: int = 0,
    ):
        super().__init__(parent)
        self.home = home_instance
        self.light_config = load_light_config()
        self.safe_min_v = float(self.light_config.get("minimum_voltage_v", 8.0))
        self.safe_max_v = float(self.light_config.get("maximum_voltage_v", 12.0))
        self.direct_control = bool(
            self.light_config.get("direct_voltage_control", True)
        )
        self.original_voltage_v = (
            float(original_voltage_v)
            if original_voltage_v is not None
            else float(self.light_config.get("startup_voltage_v", 8.0))
        )
        self.original_percent = int(original_percent)
        self._is_interrupted = False

        button_port = None
        try:
            from page.config import CONFIG_DATA

            button_port = CONFIG_DATA.get("combobox_comSelect")
        except Exception:
            pass

        configured_port = self.light_config.get("port") or None
        self.controller = WDIPLightController(
            port=configured_port,
            baudrate=int(self.light_config.get("baudrate", 9600)),
            slave_addr=int(self.light_config.get("slave_addr", 1)),
            timeout=float(self.light_config.get("timeout_seconds", 0.8)),
            excluded_ports=[] if configured_port else ([button_port] if button_port else []),
            allow_stable_crc_mismatch_readback=bool(
                self.light_config.get("allow_stable_crc_mismatch_readback", False)
            ),
            minimum_request_interval=float(
                self.light_config.get("minimum_request_interval_ms", 250)
            ) / 1000.0,
            write_settle_seconds=float(
                self.light_config.get("write_settle_ms", 400)
            ) / 1000.0,
            shared_exchange=getattr(
                getattr(self.home, "main_window", None),
                "exchange_shared_rs485",
                None,
            ),
        )

        samples = int(self.light_config.get("samples_per_level", 5))
        settle_ms = int(self.light_config.get("settle_ms", 350))
        min_pct = int(self.light_config.get("minimum_percent", 0))

        self.inner_worker = LightBinarySearchWorker(
            home_instance=self.home,
            controller=self.controller,
            safe_min_voltage_v=self.safe_min_v,
            safe_max_voltage_v=self.safe_max_v,
            samples_per_level=samples,
            settle_ms=settle_ms,
            minimum_percent=min_pct,
            direct_voltage_control=self.direct_control,
            original_voltage_v=self.original_voltage_v,
            original_percent=self.original_percent,
        )
        self.inner_worker.progress_signal.connect(self._on_inner_progress)
        self.inner_worker.finished_signal.connect(self._on_inner_finished)

    def requestInterruption(self):
        self._is_interrupted = True
        super().requestInterruption()
        if hasattr(self, "inner_worker") and self.inner_worker:
            self.inner_worker.requestInterruption()

    def _on_inner_progress(self, percent: int, message: str):
        self.sig_progress.emit(percent)
        self.sig_step.emit(f"⚡ 二分法采样进度: {percent}%")
        self.sig_log.emit(message)

    def _on_inner_finished(self, success: bool, best_percent: int, message: str):
        if success:
            best_voltage = voltage_for_percent(
                self.safe_min_v, self.safe_max_v, best_percent
            )
            save_light_config_updates(
                {
                    "startup_voltage_v": best_voltage,
                    "startup_percent": best_percent,
                }
            )
            final_percent = best_percent
            final_voltage = best_voltage
        else:
            final_percent = self.original_percent
            final_voltage = self.original_voltage_v

        results = {
            "best_percent": final_percent,
            "best_voltage": final_voltage,
            "original_percent": self.original_percent,
            "original_voltage": self.original_voltage_v,
        }
        self.sig_finished.emit(success, message, results)

    def run(self):
        self.inner_worker.run()

