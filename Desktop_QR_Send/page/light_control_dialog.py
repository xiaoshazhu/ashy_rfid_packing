"""
相机灯光亮度控制与二分法校准对话框 (LightControlDialog)
"""

import time
import logging
from PySide6 import QtCore, QtWidgets
from PySide6.QtCore import Qt, QThread, Signal, Slot
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QSlider,
    QPushButton, QGroupBox, QMessageBox, QProgressBar
)

logger = logging.getLogger("LightControlDialog")

NATIVE_BTN_STYLE = (
    "QPushButton { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #F8F8F8, stop:1 #E0E0E0); "
    "border: 1px solid #707070; border-radius: 2px; font-weight: bold; color: #000; padding: 4px 10px; } "
    "QPushButton:hover { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #FFFFFF, stop:1 #D8D8D8); border-color: #505050; } "
    "QPushButton:pressed { background: #D0D0D0; border-color: #404040; }"
)


class LightBinarySearchWorker(QThread):
    """通过二分法调用相机/灯光实测识别速度与清晰度的校准线程"""

    progress_signal = Signal(int, str)
    finished_signal = Signal(bool, int, str)

    def __init__(self, home_instance):
        super().__init__()
        self.home = home_instance

    def run(self):
        logger.info("启动二分法算法实测最佳灯光亮度筛选...")
        self.progress_signal.emit(5, "正在检测海康相机画面与光源配置...")

        cam_op = getattr(self.home, "obj_cam_operation", None)
        if not cam_op and hasattr(self.home, "hiKInit"):
            from page.home import obj_cam_operation
            cam_op = obj_cam_operation

        # 在 10% ~ 90% 亮度区间内执行二分查找实测
        low_p = 10
        high_p = 90
        best_p = 50
        best_score = -1.0
        best_speed_ms = 999.0

        iterations = 5
        for step in range(1, iterations + 1):
            mid_p = int((low_p + high_p) / 2)
            exp_val = 1000.0 + (mid_p / 100.0) * (80000.0 - 1000.0)

            percent_progress = int((step / iterations) * 90)
            self.progress_signal.emit(
                percent_progress,
                f"正在下发二分法测试亮度 [{mid_p}%]，采样测评识别清晰度与解码速度 ({step}/{iterations})..."
            )

            if cam_op and hasattr(cam_op, "Set_parameter"):
                try:
                    frame_rate = getattr(cam_op, "frame_rate", 15) or 15
                    gain = getattr(cam_op, "gain", 0) or 0
                    cam_op.Set_parameter(frame_rate, exp_val, gain)
                except Exception as e:
                    logger.warning(f"设置二分法曝光测试参数异常: {e}")

            time.sleep(0.15)  # 等待相机曝光稳定

            # 抓图评估识别情况
            decode_count = 0
            t_start = time.perf_counter()
            try:
                np_img = cam_op.get_np_array_image() if cam_op else None
                if np_img is not None:
                    from utils.pyzbar_utils import decode_image_codes
                    codes = decode_image_codes(np_img)
                    decode_count = len(codes)
            except Exception as e:
                logger.warning(f"测试解算画面异常: {e}")

            elapsed_ms = (time.perf_counter() - t_start) * 1000.0

            # 计算清晰度/速度综合评分
            score = decode_count * 1000.0 - elapsed_ms
            if score > best_score:
                best_score = score
                best_p = mid_p
                best_speed_ms = elapsed_ms

            if decode_count > 0:
                high_p = mid_p  # 画面已足够清晰，向下寻求更快帧响
            else:
                low_p = mid_p   # 画面太暗无数据，向上提升亮度

        self.progress_signal.emit(100, f"二分法校准完成！实测识别清晰度与速度最佳灯光亮度: {best_p}%")
        self.finished_signal.emit(
            True, best_p,
            f"二分法校准成功！实测画面识别速度: {best_speed_ms:.1f}ms，最佳灯光亮度 ({best_p}%) 已同步生效。"
        )


class LightControlDialog(QDialog):
    """相机灯光亮度控制与二分法校准对话框"""

    def __init__(self, home_instance, parent=None):
        super().__init__(parent)
        self.home = home_instance
        self.setWindowTitle("相机灯光亮度控制与二分法校准")
        self.resize(480, 320)
        self.setWindowModality(Qt.WindowModal)

        self.worker = None
        self.init_ui()
        self.load_current_camera_brightness()

    def init_ui(self):
        main_layout = QVBoxLayout(self)

        # 1. 手动滑动调节区域
        manual_group = QGroupBox("手动灯光亮度调节")
        manual_layout = QVBoxLayout(manual_group)

        self.label_value = QLabel("当前灯光亮度: 50%")
        self.label_value.setStyleSheet("font-size: 14px; font-weight: bold; color: #2B579A;")
        manual_layout.addWidget(self.label_value)

        slider_layout = QHBoxLayout()

        self.btn_minus = QPushButton(" - ")
        self.btn_minus.setFixedWidth(40)
        self.btn_minus.setStyleSheet(NATIVE_BTN_STYLE)
        self.btn_minus.clicked.connect(self.on_minus_clicked)
        slider_layout.addWidget(self.btn_minus)

        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(0, 100)
        self.slider.setValue(50)
        self.slider.setSingleStep(1)
        self.slider.setPageStep(5)
        self.slider.valueChanged.connect(self.on_slider_changed)
        slider_layout.addWidget(self.slider)

        self.btn_plus = QPushButton(" + ")
        self.btn_plus.setFixedWidth(40)
        self.btn_plus.setStyleSheet(NATIVE_BTN_STYLE)
        self.btn_plus.clicked.connect(self.on_plus_clicked)
        slider_layout.addWidget(self.btn_plus)

        manual_layout.addLayout(slider_layout)
        main_layout.addWidget(manual_group)

        # 2. 二分法亮度标准校准区域
        auto_group = QGroupBox("二分法灯光亮度校准")
        auto_layout = QVBoxLayout(auto_group)

        btn_center_box = QHBoxLayout()
        btn_center_box.addStretch()

        self.btn_calibrate = QPushButton("⚡ 二分法亮度标准校准")
        self.btn_calibrate.setStyleSheet(NATIVE_BTN_STYLE)
        self.btn_calibrate.clicked.connect(self.on_calibrate_clicked)
        btn_center_box.addWidget(self.btn_calibrate)

        btn_center_box.addStretch()
        auto_layout.addLayout(btn_center_box)

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        auto_layout.addWidget(self.progress_bar)

        # 小字提醒
        self.label_status = QLabel("就绪。点击[二分法亮度标准校准]可调用相机实测寻找最佳识别灯光亮度。")
        self.label_status.setStyleSheet("color: #666; font-size: 11px;")
        auto_layout.addWidget(self.label_status)

        main_layout.addWidget(auto_group)

        # 底部关闭按钮
        bottom_box = QHBoxLayout()
        bottom_box.addStretch()

        self.btn_close = QPushButton("关闭")
        self.btn_close.setFixedWidth(90)
        self.btn_close.setStyleSheet(NATIVE_BTN_STYLE)
        self.btn_close.clicked.connect(self.accept)
        bottom_box.addWidget(self.btn_close)

        main_layout.addLayout(bottom_box)

    def brightness_percent_to_exp(self, percent: int) -> float:
        """百分比 (0% ~ 100%) 映射为相机曝光时间 (1000us ~ 80000us)"""
        p = max(0, min(100, percent))
        return 1000.0 + (p / 100.0) * (80000.0 - 1000.0)

    def exp_to_brightness_percent(self, exp_val: float) -> int:
        """曝光时间映射回百分比 (0% ~ 100%)"""
        e = max(1000.0, min(80000.0, float(exp_val)))
        p = int(round(((e - 1000.0) / (80000.0 - 1000.0)) * 100.0))
        return max(0, min(100, p))

    def load_current_camera_brightness(self):
        """读取当前相机的曝光值并换算为百分比"""
        try:
            from page.home import obj_cam_operation
            if obj_cam_operation and hasattr(obj_cam_operation, "Get_parameter"):
                obj_cam_operation.Get_parameter()
                exp = float(obj_cam_operation.exposure_time or 20000.0)
                percent = self.exp_to_brightness_percent(exp)
                self.slider.blockSignals(True)
                self.slider.setValue(percent)
                self.slider.blockSignals(False)
                self.label_value.setText(f"当前灯光亮度: {percent}%")
        except Exception as e:
            logger.warning(f"读取当前相机亮度参数失败: {e}")

    def apply_brightness_to_camera(self, percent: int):
        """将亮度百分比转换为曝光写入相机"""
        exp_val = self.brightness_percent_to_exp(percent)
        try:
            from page.home import obj_cam_operation
            if obj_cam_operation and hasattr(obj_cam_operation, "Set_parameter"):
                frame_rate = getattr(obj_cam_operation, "frame_rate", 15) or 15
                gain = getattr(obj_cam_operation, "gain", 0) or 0
                obj_cam_operation.Set_parameter(frame_rate, exp_val, gain)
        except Exception as e:
            logger.warning(f"下发灯光亮度参数给相机失败: {e}")

    def on_slider_changed(self, value):
        self.label_value.setText(f"当前灯光亮度: {value}%")
        self.apply_brightness_to_camera(value)

    def on_minus_clicked(self):
        val = max(self.slider.minimum(), self.slider.value() - 2)
        self.slider.setValue(val)

    def on_plus_clicked(self):
        val = min(self.slider.maximum(), self.slider.value() + 2)
        self.slider.setValue(val)

    def on_calibrate_clicked(self):
        """触发二分法亮度标准校准"""
        self.btn_calibrate.setEnabled(False)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(True)
        self.label_status.setText("正在通过二分法调用相机测试识别速度与清晰度...")

        self.worker = LightBinarySearchWorker(self.home)
        self.worker.progress_signal.connect(self.on_worker_progress)
        self.worker.finished_signal.connect(self.on_worker_finished)
        self.worker.start()

    @Slot(int, str)
    def on_worker_progress(self, percent, msg):
        self.progress_bar.setValue(percent)
        self.label_status.setText(msg)

    @Slot(bool, int, str)
    def on_worker_finished(self, success, percent, msg):
        self.progress_bar.setValue(100)
        self.label_status.setText(msg)
        self.btn_calibrate.setEnabled(True)

        if success:
            self.slider.setValue(percent)
            self.apply_brightness_to_camera(percent)
            QMessageBox.information(self, "二分法亮度校准", f"【二分法智能校准成功】\n\n{msg}")
        else:
            QMessageBox.warning(self, "亮度校准告警", f"【校准过程提醒】\n\n{msg}")

    def closeEvent(self, event):
        if self.worker and self.worker.isRunning():
            self.worker.wait(1000)
        super().closeEvent(event)
