# RS485Utils.py
import serial
import time
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from serial.tools import list_ports
from page import config

from utils.td39_protocol import (
    TD39_ACTION_DI_COUNT,
    TD39_BAUDRATE,
    TD39_DEFAULT_SLAVE,
    TD39_DI_COUNT,
    TD39_DI_FUNCTION,
    TD39_DI_START,
    TD39_MONITOR_VERSION,
    build_read_inputs as build_modbus_read_di,
    crc16_modbus,
    decode_input_mask,
    format_input_states,
    is_valid_frame as is_valid_modbus_frame,
    states_from_mask,
)


TD39_POLL_INTERVAL_SECONDS = 0.05
TD39_MONITOR_HEARTBEAT_SECONDS = 5.0
TD39_UNCHANGED_NOTICE_SECONDS = 10.0
TD39_RAW_LOG_INTERVAL_SECONDS = 1.0


def _get_input_monitor_logger():
    """创建独立监听日志，避免与业务日志混在一起难以查找。"""
    logger = logging.getLogger("td39_input_monitor")
    if getattr(logger, "_td39_configured", False):
        return logger

    log_dir = Path(__file__).resolve().parents[1] / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    handler = RotatingFileHandler(
        log_dir / "rs485_input_monitor.log",
        maxBytes=5 * 1024 * 1024,
        backupCount=2,
        encoding="utf-8",
    )
    handler.setFormatter(
        logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    )
    logger.handlers.clear()
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False
    logger._td39_configured = True
    return logger


class RS485Utils:
    def __init__(self, port, baudrate, home_instance, slave_addr=TD39_DEFAULT_SLAVE):
        logging.info(f"RS485Utils 初始化，初始端口: {port}, 波特率: {baudrate}")
        self.port = port
        self.baudrate = int(baudrate or TD39_BAUDRATE)
        self.slave_addr = int(slave_addr)
        self.ser = None
        self._receive_buffer = bytearray()
        self.home_instance = home_instance
        self._last_trigger_time = {}
        self._prev_modbus_mask = None
        self._idle_modbus_mask = None
        self._listen_started_at = None
        self._last_valid_response_at = None
        self._last_no_response_warning_at = None
        self._last_monitor_heartbeat_at = None
        self._last_state_change_at = None
        self._last_unchanged_notice_at = None
        self._last_raw_sample_log_at = None
        self._monitor_rx_bytes = 0
        self._monitor_valid_frames = 0
        self._monitor_events = 0
        self._monitor_logger = _get_input_monitor_logger()
        self.running = True
        logging.debug("RS485Utils 对象创建完成，按 TD-39 Modbus-RTU 协议监听。")

    def get_available_ports(self):
        """获取系统当前可用端口，优先真实 USB 串口芯片，排查主板虚拟 COM2/COM1。"""
        items = list(list_ports.comports())
        usb_ports = []
        other_ports = []
        for item in items:
            desc = (item.description or "").upper()
            hwid = (item.hwid or "").upper()
            device = item.device
            if any(token in desc or token in hwid for token in ("USB", "CH34", "FTDI", "PL2303", "CP210", "SERIAL", "UART")):
                usb_ports.append(device)
            else:
                other_ports.append(device)

        # 优先选择 USB 端口 (如 COM3/COM4)，避免卡在主板虚拟 COM2
        return usb_ports + [p for p in other_ports if p not in usb_ports]

    def connect(self):
        if self.ser and self.ser.is_open:
            try:
                self.ser.close()
            except Exception:
                pass

        try:
            self.ser = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=0.08,
            )
            try:
                # 沿用设备现场文档中的控制线状态。多数自动收发 USB-RS485
                # 转换器会忽略这两根控制线。
                self.ser.dtr = True
                self.ser.rts = True
            except Exception as exc:
                logging.debug(f"设置串口 DTR/RTS 状态失败（可忽略于自动收发转换器）: {exc}")
        except serial.SerialException as e:
            logging.debug(f"尝试打开 [{self.port} @ {self.baudrate}] 失败: {e}")
            raise

    def listen(self):
        logging.info(
            f"开始监听 TD-39 RS485: 端口={self.port}, 波特率={self.baudrate}, "
            f"从站={self.slave_addr}, 功能码=0x{TD39_DI_FUNCTION:02X}, "
            f"监测=全部{TD39_DI_COUNT}路(DI0~DI{TD39_DI_COUNT - 1}), "
            f"业务触发=前{TD39_ACTION_DI_COUNT}路(DI0~DI{TD39_ACTION_DI_COUNT - 1})"
        )
        last_poll_time = 0
        self._listen_started_at = time.monotonic()
        query_frame = build_modbus_read_di(slave_addr=self.slave_addr)
        self._monitor_logger.info(
            "START version=%s port=%s baud=%s format=8N1 slave=%s function=0x%02X "
            "monitor_channels=DI0~DI%s action_channels=DI0~DI%s query=%s",
            TD39_MONITOR_VERSION,
            self.port,
            self.baudrate,
            self.slave_addr,
            TD39_DI_FUNCTION,
            TD39_DI_COUNT - 1,
            TD39_ACTION_DI_COUNT - 1,
            query_frame.hex(" "),
        )

        try:
            if not self.ser or not self.ser.is_open:
                self.connect()
            logging.info(f"TD-39 串口已打开: [{self.port}] @ {self.baudrate} baud")
        except Exception as exc:
            logging.error(f"TD-39 串口打开失败 [{self.port}]: {exc}")
            raise

        try:
            while self.running:
                # 设置页保存了新串口或明确禁用时，退出本轮监听，让主程序重新决策。
                saved_port = config.CONFIG_DATA.get("combobox_comSelect")
                if saved_port is None:
                    logging.info("设置中已禁用 RS485 实体按钮，停止监听")
                    return
                if saved_port != self.port:
                    available_ports = self.get_available_ports()
                    if saved_port in available_ports:
                        logging.info(f"检测到串口设置改变 ({self.port} -> {saved_port})，准备重连")
                        return

                now = time.monotonic()

                # 读取整块 12 路板的 DI0~DI11。
                if now - last_poll_time >= TD39_POLL_INTERVAL_SECONDS:
                    if self.ser and self.ser.is_open:
                        try:
                            poll_cmd = build_modbus_read_di(slave_addr=self.slave_addr)
                            self.ser.write(poll_cmd)
                            logging.debug(f"TD-39 发送查询: {poll_cmd.hex(' ')}")
                        except Exception as exc:
                            logging.error(f"TD-39 查询发送失败: {exc}")
                            raise
                    last_poll_time = now

                if self.ser and self.ser.is_open and self.ser.in_waiting > 0:
                    data = self.ser.read(self.ser.in_waiting)
                    hex_data = data.hex(" ")
                    self._monitor_rx_bytes += len(data)

                    logging.debug(f"RS485 [{self.port}] 收到数据 (Hex): {hex_data}")
                    # 保持50ms实体按钮轮询，但原始帧最多每秒记录一次，避免持续磁盘写入拖慢界面。
                    if (
                        self._last_raw_sample_log_at is None
                        or now - self._last_raw_sample_log_at
                        >= TD39_RAW_LOG_INTERVAL_SECONDS
                    ):
                        self._monitor_logger.info(
                            "RX-SAMPLE port=%s bytes=%s total_bytes=%s hex=%s",
                            self.port,
                            len(data),
                            self._monitor_rx_bytes,
                            hex_data,
                        )
                        self._last_raw_sample_log_at = now

                    raw_data_callback = getattr(
                        self.home_instance, "on_rs485_raw_data", None
                    )
                    if callable(raw_data_callback):
                        raw_data_callback(self.port, hex_data)

                    self._receive_buffer.extend(data)
                    self._process_receive_buffer()

                response_reference = (
                    self._last_valid_response_at
                    if self._last_valid_response_at is not None
                    else self._listen_started_at
                )
                if now - response_reference >= 3.0:
                    if (
                        self._last_no_response_warning_at is None
                        or now - self._last_no_response_warning_at >= 10.0
                    ):
                        logging.warning(
                            "TD-39 未收到有效响应：请核对设置中的 COM 口、A/B 接线、"
                            f"站号 {self.slave_addr}、9600/8N1；当前查询帧="
                            f"{build_modbus_read_di(self.slave_addr).hex(' ')}"
                        )
                        self._monitor_logger.warning(
                            "NO-VALID-RESPONSE port=%s silence=%.1fs "
                            "check=COM/A-B/power/slave/9600-8N1 query=%s",
                            self.port,
                            now - response_reference,
                            query_frame.hex(" "),
                        )
                        self._last_no_response_warning_at = now

                time.sleep(0.02)

        except serial.SerialException as e:
            logging.error(f"串行通信错误: {e}")
        except Exception as e:
            logging.error(f"监听线程发生未知错误: {e}")
        finally:
            logging.info(f"停止监听 RS485 串口数据 ({self.port})。")
            self._monitor_logger.info(
                "STOP port=%s valid_frames=%s rx_bytes=%s channel_events=%s",
                self.port,
                self._monitor_valid_frames,
                self._monitor_rx_bytes,
                self._monitor_events,
            )

    def _process_receive_buffer(self):
        """从连续字节流中提取完整的 TD-39 Modbus 帧或兼容 AA 帧。"""
        while self._receive_buffer:
            first = self._receive_buffer[0]

            if first == 0xAA:
                if len(self._receive_buffer) < 3:
                    return
                door_number = self._receive_buffer[1]
                state = self._receive_buffer[2]
                if door_number not in range(1, 17) or state not in (0, 1):
                    logging.warning("丢弃格式错误的 AA 按钮帧起始字节")
                    del self._receive_buffer[0]
                    continue
                del self._receive_buffer[:3]
                if self._receive_buffer and self._receive_buffer[0] == 0x2C:
                    del self._receive_buffer[0]
                is_press = state == 1
                logging.info(
                    f"AA帧解包成功 - 实体按钮通道 {door_number}: "
                    f"{'按下' if is_press else '释放'}"
                )
                self._handle_button_event(door_number, is_press)
                continue

            if first != self.slave_addr:
                logging.debug(f"丢弃无法识别的串口字节: 0x{first:02X}")
                del self._receive_buffer[0]
                continue

            if len(self._receive_buffer) < 2:
                return

            func_code = self._receive_buffer[1]
            if func_code & 0x80:
                frame_len = 5
            elif func_code == TD39_DI_FUNCTION:
                if len(self._receive_buffer) < 3:
                    return
                byte_count = self._receive_buffer[2]
                if byte_count > 250:
                    logging.warning(f"TD-39 响应字节数异常: {byte_count}")
                    del self._receive_buffer[0]
                    continue
                frame_len = 3 + byte_count + 2
            else:
                logging.warning(f"收到未请求的 Modbus 功能码 0x{func_code:02X}，尝试重新同步")
                del self._receive_buffer[0]
                continue

            if len(self._receive_buffer) < frame_len:
                return

            frame = bytes(self._receive_buffer[:frame_len])
            if not is_valid_modbus_frame(frame):
                logging.warning(f"Modbus CRC 校验失败，丢弃起始字节；候选帧: {frame.hex(' ')}")
                self._monitor_logger.warning(
                    "CRC-ERROR port=%s candidate=%s",
                    self.port,
                    frame.hex(" "),
                )
                del self._receive_buffer[0]
                continue

            del self._receive_buffer[:frame_len]
            if func_code & 0x80:
                logging.error(
                    f"TD-39 返回 Modbus 异常: 功能码=0x{func_code:02X}, "
                    f"异常码=0x{frame[2]:02X}"
                )
                self._monitor_logger.error(
                    "MODBUS-EXCEPTION port=%s function=0x%02X code=0x%02X frame=%s",
                    self.port,
                    func_code,
                    frame[2],
                    frame.hex(" "),
                )
                continue

            self._process_modbus_response(frame)

    def _process_modbus_response(self, data: bytes):
        """解析已通过 CRC 校验的 TD-39 0x01 输入状态响应。"""
        if len(data) < 6 or data[0] != self.slave_addr or data[1] != TD39_DI_FUNCTION:
            logging.warning(f"忽略非 TD-39 输入状态响应: {data.hex(' ')}")
            return

        byte_count = data[2]
        if byte_count < 1 or len(data) != 3 + byte_count + 2:
            logging.warning(f"TD-39 输入响应长度错误: {data.hex(' ')}")
            return

        try:
            mask = decode_input_mask(data, self.slave_addr, TD39_DI_COUNT)
        except ValueError as exc:
            logging.warning(f"TD-39 输入响应解析失败: {exc}; frame={data.hex(' ')}")
            self._monitor_logger.warning(
                "DECODE-ERROR port=%s reason=%s frame=%s",
                self.port,
                exc,
                data.hex(" "),
            )
            return
        now = time.monotonic()
        self._last_valid_response_at = now
        self._monitor_valid_frames += 1
        states_text = format_input_states(states_from_mask(mask, TD39_DI_COUNT))
        if self._prev_modbus_mask is None:
            self._prev_modbus_mask = mask
            self._idle_modbus_mask = mask
            self._last_state_change_at = now
            logging.info(f"TD-39 输入初始状态: 0b{mask:08b}")
            self._monitor_logger.info(
                "RX-VALID port=%s frame_no=%s frame=%s states=[%s]",
                self.port,
                self._monitor_valid_frames,
                data.hex(" "),
                states_text,
            )
            self._last_monitor_heartbeat_at = now
            return

        changed = mask ^ self._prev_modbus_mask
        if changed:
            self._last_state_change_at = now
            self._monitor_logger.info(
                "STATE-CHANGE port=%s frame_no=%s frame=%s states=[%s]",
                self.port,
                self._monitor_valid_frames,
                data.hex(" "),
                states_text,
            )
            for bit in range(TD39_DI_COUNT):
                if changed & (1 << bit):
                    channel = bit + 1
                    raw_closed = bool(mask & (1 << bit))
                    idle_closed = bool(self._idle_modbus_mask & (1 << bit))
                    is_press = raw_closed != idle_closed
                    self._monitor_events += 1
                    logging.info(
                        f"TD-39 输入通道 {channel}: 原始状态="
                        f"{'闭合' if raw_closed else '断开'}, 解释为="
                        f"{'按下' if is_press else '释放'}"
                    )
                    self._monitor_logger.info(
                        "CHANNEL-EVENT event_no=%s channel=%s module_input=DI%s "
                        "electrical=%s interpreted=%s",
                        self._monitor_events,
                        channel,
                        bit,
                        "CLOSED" if raw_closed else "OPEN",
                        "PRESSED" if is_press else "RELEASED",
                    )
                    self._handle_button_event(channel, is_press)
            self._last_monitor_heartbeat_at = now
        elif (
            self._last_monitor_heartbeat_at is None
            or now - self._last_monitor_heartbeat_at
            >= TD39_MONITOR_HEARTBEAT_SECONDS
        ):
            self._monitor_logger.info(
                "HEARTBEAT port=%s valid_frames=%s rx_bytes=%s states=[%s]",
                self.port,
                self._monitor_valid_frames,
                self._monitor_rx_bytes,
                states_text,
            )
            self._last_monitor_heartbeat_at = now

        if (
            self._last_state_change_at is not None
            and now - self._last_state_change_at >= TD39_UNCHANGED_NOTICE_SECONDS
            and (
                self._last_unchanged_notice_at is None
                or now - self._last_unchanged_notice_at
                >= TD39_UNCHANGED_NOTICE_SECONDS
            )
        ):
            self._monitor_logger.info(
                "INPUTS-UNCHANGED port=%s seconds=%.1f states=[%s] "
                "meaning=通信正常但端子电平没有变化；TD-39的干接点需要外部输入配电，"
                "不能只短接ICOM-DI。若ICOM接GND，应使用+VS-按钮-DI；"
                "若ICOM接+VS，应使用GND-按钮-DI",
                self.port,
                now - self._last_state_change_at,
                states_text,
            )
            self._last_unchanged_notice_at = now
        self._prev_modbus_mask = mask

    def _queue_button_click(self, button_name: str):
        """把串口线程中的按钮动作排队投递到 Qt 主线程。"""
        main_win = getattr(self.home_instance, "main_window", None)
        if main_win is None:
            logging.warning("未找到 main_window 属性，无法触发按钮")
            return

        button = getattr(main_win, button_name, None)
        if button is None:
            logging.warning(f"界面上找不到控件: {button_name}")
            return

        try:
            from PySide6.QtCore import QMetaObject, Qt
            queued = QMetaObject.invokeMethod(button, "click", Qt.QueuedConnection)
            if queued is False:
                logging.error(f"Qt 拒绝排队触发界面按钮: {button_name}")
                return
            logging.info(f"已排队到 Qt 主线程触发界面按钮: {button_name}")
        except Exception as exc:
            logging.error(f"Qt 队列投递失败，未触发界面按钮 {button_name}: {exc}")

    def _handle_button_event(self, door_number: int, is_press: bool):
        """处理实体按钮按下沿，释放沿只记录状态，不重复执行功能。"""
        event_callback = getattr(self.home_instance, "on_rs485_event", None)
        if callable(event_callback):
            event_callback(self.port, door_number, is_press)

        if not is_press:
            logging.debug(f"通道 {door_number} 已释放，不重复触发界面功能")
            return

        now = time.monotonic()
        last_time = self._last_trigger_time.get(door_number, 0)
        if now - last_time < 0.3:
            logging.debug(f"通道 {door_number} 处于消抖冷却期，忽略本次触发")
            return
        self._last_trigger_time[door_number] = now

        # 面板硬件按钮与软件功能对应表 (按实物面板从左至右排序)
        # 按钮 1 (通道 1): 复位 -> button_cancel
        # 按钮 2 (通道 2): 打印箱码 -> button_print
        # 按钮 3 (通道 3): 拍照识别 -> button_again
        # 按钮 4 (通道 4): 重新装箱 -> button_reset
        # 输入 5 (通道 5): 光电传感器/到位信号 -> button_again
        event_mapping = {
            1: ("button_cancel", "复位"),
            2: ("button_print", "打印箱码"),
            3: ("button_again", "拍照识别"),
            4: ("button_reset", "重新装箱"),
            5: ("button_again", "光电触发拍照识别"),
        }

        mapping = event_mapping.get(door_number)
        if mapping is None:
            logging.info(f"实体输入通道 {door_number} 已按下，但未配置对应功能")
            return

        button_name, function_name = mapping
        logging.info(
            f"实体按钮通道 {door_number} 按下，触发界面功能: 【{function_name}】 ({button_name})"
        )
        self._queue_button_click(button_name)

    def stop(self):
        self.running = False

    def close(self):
        self.running = False
        logging.info("关闭 RS485 串口连接...")
        if self.ser:
            try:
                self.ser.close()
            except Exception as e:
                logging.warning(f"关闭串口时发生异常: {e}")
            self.ser = None
            logging.info("串行连接已关闭。")
        else:
            logging.info("串行连接之前未打开，无需关闭。")
