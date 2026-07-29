# RS485Utils.py
import serial
import time
import logging
from serial.tools import list_ports
from page import config

WDIP_DEFAULT_SLAVE = 1
WDIP_BAUDRATE = 9600
WDIP_READ_FUNCTION = 0x03
WDIP_REGISTER_START = 0
WDIP_REGISTER_COUNT = 8
WDIP_POLL_INTERVAL_SECONDS = 0.2


def crc16_modbus(data: bytes) -> int:
    crc = 0xFFFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 1:
                crc = (crc >> 1) ^ 0xA001
            else:
                crc >>= 1
    return crc


def build_modbus_read_registers(
    slave_addr: int = WDIP_DEFAULT_SLAVE,
    start: int = WDIP_REGISTER_START,
    count: int = WDIP_REGISTER_COUNT,
) -> bytes:
    """按 WDIP24-15-R 手册使用 0x03 读取保持寄存器。"""
    if not 1 <= slave_addr <= 247:
        raise ValueError("Modbus 从站地址必须在 1~247 之间")
    if not 0 <= start <= 0xFFFF:
        raise ValueError("Modbus 起始地址必须在 0~65535 之间")
    if not 1 <= count <= 125:
        raise ValueError("Modbus 0x03 读取寄存器数量必须在 1~125 之间")

    payload = bytes([
        slave_addr,
        WDIP_READ_FUNCTION,
        (start >> 8) & 0xFF,
        start & 0xFF,
        (count >> 8) & 0xFF,
        count & 0xFF,
    ])
    crc = crc16_modbus(payload)
    return payload + bytes([crc & 0xFF, (crc >> 8) & 0xFF])


def is_valid_modbus_frame(frame: bytes) -> bool:
    """校验完整 Modbus-RTU 帧的 CRC（CRC 低字节在前）。"""
    if len(frame) < 4:
        return False
    expected = crc16_modbus(frame[:-2])
    received = frame[-2] | (frame[-1] << 8)
    return expected == received


class RS485Utils:
    def __init__(self, port, baudrate, home_instance, slave_addr=WDIP_DEFAULT_SLAVE):
        logging.info(f"RS485Utils 初始化，初始端口: {port}, 波特率: {baudrate}")
        self.port = port
        self.baudrate = int(baudrate or WDIP_BAUDRATE)
        self.slave_addr = int(slave_addr)
        self.ser = None
        self._receive_buffer = bytearray()
        self.home_instance = home_instance
        self._last_trigger_time = {}
        self._last_wdip_registers = None
        self._listen_started_at = None
        self._last_valid_response_at = None
        self._last_no_response_warning_at = None
        self.running = True
        logging.debug("RS485Utils 对象创建完成，按 WDIP24-15-R Modbus-RTU 只读协议监听。")

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
            f"开始监听 WDIP24-15-R RS485（只读测试）: 端口={self.port}, 波特率={self.baudrate}, "
            f"从站={self.slave_addr}, 功能码=0x{WDIP_READ_FUNCTION:02X}"
        )
        last_poll_time = 0
        self._listen_started_at = time.monotonic()

        try:
            if not self.ser or not self.ser.is_open:
                self.connect()
            logging.info(f"WDIP24-15-R 串口已打开: [{self.port}] @ {self.baudrate} baud")
        except Exception as exc:
            logging.error(f"WDIP24-15-R 串口打开失败 [{self.port}]: {exc}")
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

                # WDIP24-15-R 手册：0x03 只读寄存器 0x0000~0x0007。
                if now - last_poll_time >= WDIP_POLL_INTERVAL_SECONDS:
                    if self.ser and self.ser.is_open:
                        try:
                            poll_cmd = build_modbus_read_registers(slave_addr=self.slave_addr)
                            self.ser.write(poll_cmd)
                            logging.debug(f"WDIP24-15-R 发送只读查询: {poll_cmd.hex(' ')}")
                        except Exception as exc:
                            logging.error(f"WDIP24-15-R 查询发送失败: {exc}")
                            raise
                    last_poll_time = now

                if self.ser and self.ser.is_open and self.ser.in_waiting > 0:
                    data = self.ser.read(self.ser.in_waiting)
                    hex_data = data.hex(" ")

                    logging.info(f"RS485 [{self.port}] 收到数据 (Hex): {hex_data}")

                    raw_data_callback = getattr(
                        self.home_instance, "on_rs485_raw_data", None
                    )
                    if callable(raw_data_callback):
                        raw_data_callback(self.port, hex_data)

                    self._receive_buffer.extend(data)
                    self._process_receive_buffer()

                if self._last_valid_response_at is None and now - self._listen_started_at >= 3.0:
                    if (
                        self._last_no_response_warning_at is None
                        or now - self._last_no_response_warning_at >= 10.0
                    ):
                        logging.warning(
                            "WDIP24-15-R 未收到有效响应：请核对设置中的 COM 口、A/B 接线、"
                            f"站号 {self.slave_addr}、9600/8N1；当前只读查询帧="
                            f"{build_modbus_read_registers(self.slave_addr).hex(' ')}"
                        )
                        self._last_no_response_warning_at = now

                time.sleep(0.02)

        except serial.SerialException as e:
            logging.error(f"串行通信错误: {e}")
        except Exception as e:
            logging.error(f"监听线程发生未知错误: {e}")
        finally:
            logging.info(f"停止监听 RS485 串口数据 ({self.port})。")

    def _process_receive_buffer(self):
        """从连续字节流中提取完整的 WDIP Modbus 帧或兼容 AA 帧。"""
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
            elif func_code == WDIP_READ_FUNCTION:
                if len(self._receive_buffer) < 3:
                    return
                byte_count = self._receive_buffer[2]
                if byte_count > 250:
                    logging.warning(f"WDIP24-15-R 响应字节数异常: {byte_count}")
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
                del self._receive_buffer[0]
                continue

            del self._receive_buffer[:frame_len]
            if func_code & 0x80:
                logging.error(
                    f"WDIP24-15-R 返回 Modbus 异常: 功能码=0x{func_code:02X}, "
                    f"异常码=0x{frame[2]:02X}"
                )
                continue

            self._process_modbus_response(frame)

    def _process_modbus_response(self, data: bytes):
        """解析已通过 CRC 校验的 WDIP24-15-R 0x03 寄存器响应。"""
        if len(data) < 7 or data[0] != self.slave_addr or data[1] != WDIP_READ_FUNCTION:
            logging.warning(f"忽略非 WDIP24-15-R 寄存器响应: {data.hex(' ')}")
            return

        byte_count = data[2]
        expected_byte_count = WDIP_REGISTER_COUNT * 2
        if byte_count != expected_byte_count or len(data) != 3 + byte_count + 2:
            logging.warning(
                f"WDIP24-15-R 寄存器响应长度错误: 期望 {expected_byte_count} 字节，"
                f"实际 {byte_count} 字节；帧={data.hex(' ')}"
            )
            return

        registers = tuple(
            (data[3 + index * 2] << 8) | data[4 + index * 2]
            for index in range(WDIP_REGISTER_COUNT)
        )
        self._last_valid_response_at = time.monotonic()
        if registers != self._last_wdip_registers:
            logging.info(
                "WDIP24-15-R 有效响应: "
                f"Reg0(保留)={registers[0]}, "
                f"输出电压={registers[1] / 100:.2f}V, "
                f"输出电流={registers[2] / 1000:.3f}A, "
                f"设定电压={registers[3] / 100:.2f}V, "
                f"设定电流={registers[4] / 1000:.3f}A, "
                f"输出控制={registers[5]}, 波特率编号={registers[6]}, "
                f"串口保存={registers[7]}"
            )
            self._last_wdip_registers = registers

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
        event_mapping = {
            1: ("button_cancel", "复位"),
            2: ("button_print", "打印箱码"),
            3: ("button_again", "拍照识别"),
            4: ("button_reset", "重新装箱"),
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
