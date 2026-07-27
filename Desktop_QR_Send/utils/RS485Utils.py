# RS485Utils.py
import serial
import time
import logging
from serial.tools import list_ports
from page import config

BAUDRATES_TO_TRY = (9600, 115200, 19200)
RTS_MODES = (False, True)


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


def build_modbus_read_di(slave_addr: int = 1, start: int = 0, count: int = 8) -> bytes:
    payload = bytes([slave_addr, 0x02, (start >> 8) & 0xFF, start & 0xFF, (count >> 8) & 0xFF, count & 0xFF])
    crc = crc16_modbus(payload)
    return payload + bytes([crc & 0xFF, (crc >> 8) & 0xFF])


class RS485Utils:
    def __init__(self, port, baudrate, home_instance):
        logging.info(f"RS485Utils 初始化，初始端口: {port}, 波特率: {baudrate}")
        self.port = port
        self.baudrate = baudrate
        self.ser = None
        self._receive_buffer = bytearray()
        self.home_instance = home_instance
        self._last_trigger_time = {}
        self._prev_modbus_mask = None
        self.running = True
        self.baudrate_locked = False
        self.current_rts = False
        logging.debug("RS485Utils 对象创建完成，开启全端口全波特率自适应。")

    def get_available_ports(self):
        """获取系统当前可用端口，优先 USB 转接器。"""
        items = list(list_ports.comports())
        usb_ports = []
        other_ports = []
        for item in items:
            desc = (item.description or "").upper()
            hwid = (item.hwid or "").upper()
            if any(token in desc or token in hwid for token in ("USB", "CH34", "FTDI", "PL2303", "CP210", "SERIAL", "UART")):
                usb_ports.append(item.device)
            else:
                other_ports.append(item.device)
        res = usb_ports + other_ports
        return res if res else ["COM3", "COM1", "COM2"]

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
                self.ser.dtr = True
                self.ser.rts = self.current_rts
            except Exception as e:
                pass
        except serial.SerialException as e:
            logging.debug(f"尝试打开 [{self.port} @ {self.baudrate}] 失败: {e}")
            raise

    def listen(self):
        logging.info(f"开始全端口自适应监听 RS485 数据...")
        last_poll_time = 0
        last_switch_time = time.monotonic()

        all_ports = self.get_available_ports()
        port_idx = 0
        baud_idx = 0
        rts_idx = 0

        if self.port in all_ports:
            port_idx = all_ports.index(self.port)

        try:
            # 首次连接
            self.connect()
            logging.info(f"✅ 当前测试端口: [{self.port}] @ {self.baudrate} baud (RTS={self.current_rts})")
        except Exception:
            pass

        try:
            while self.running:
                # 检查全局设置中的串口是否被手动更改
                saved_port = config.CONFIG_DATA.get("combobox_comSelect")
                if saved_port and saved_port != self.port and self.baudrate_locked:
                    logging.info(
                        f"检测到设置中手动切换了串口 ({self.port} -> {saved_port})，即将重连到新端口..."
                    )
                    self.port = saved_port
                    self.connect()
                    break

                now = time.monotonic()

                # 未锁定时，每 2.0 秒自动轮换端口、波特率和 RTS 模式
                if not self.baudrate_locked and (now - last_switch_time > 2.0):
                    baud_idx += 1
                    if baud_idx >= len(BAUDRATES_TO_TRY):
                        baud_idx = 0
                        rts_idx += 1
                        if rts_idx >= len(RTS_MODES):
                            rts_idx = 0
                            all_ports = self.get_available_ports()
                            port_idx = (port_idx + 1) % len(all_ports)

                    self.port = all_ports[port_idx]
                    self.baudrate = BAUDRATES_TO_TRY[baud_idx]
                    self.current_rts = RTS_MODES[rts_idx]

                    logging.info(
                        f"🔄 自适应切换 ➔ 端口: [{self.port}] | 波特率: {self.baudrate} | RTS: {self.current_rts} (请按下按钮...)"
                    )
                    try:
                        self.connect()
                    except Exception:
                        pass
                    last_switch_time = now

                # 每 150ms 发送 Modbus 0x02 主动查询
                if now - last_poll_time > 0.15:
                    if self.ser and self.ser.is_open:
                        try:
                            for slave in (1, 2):
                                poll_cmd = build_modbus_read_di(slave_addr=slave, start=0, count=8)
                                self.ser.write(poll_cmd)
                        except Exception:
                            pass
                    last_poll_time = now

                if self.ser and self.ser.is_open and self.ser.in_waiting > 0:
                    data = self.ser.read(self.ser.in_waiting)
                    hex_data = data.hex(" ")

                    if not self.baudrate_locked:
                        self.baudrate_locked = True
                        logging.info("=" * 60)
                        logging.info(
                            f"🎉🎉🎉【成功锁死按键端口与通信参数！】"
                        )
                        logging.info(
                            f"📌 端口: {self.port} | 波特率: {self.baudrate} | RTS: {self.current_rts}"
                        )
                        logging.info("=" * 60)
                        # 将锁定的成功串口保存到配置文件 config.json
                        config.setConfig({"combobox_comSelect": self.port})

                    logging.info(f"RS485 [{self.port}] 收到数据 (Hex): {hex_data}")

                    raw_data_callback = getattr(
                        self.home_instance, "on_rs485_raw_data", None
                    )
                    if callable(raw_data_callback):
                        raw_data_callback(self.port, hex_data)

                    self._receive_buffer.extend(data)
                    self._process_receive_buffer()
                    self._process_modbus_response(bytes(data))

                time.sleep(0.03)

        except serial.SerialException as e:
            logging.error(f"串行通信错误: {e}")
        except Exception as e:
            logging.error(f"监听线程发生未知错误: {e}")
        finally:
            logging.info(f"停止监听 RS485 串口数据 ({self.port})。")

    def _process_receive_buffer(self):
        """提取 AA + 通道 + 状态 (被动 AA 帧解析)。"""
        while len(self._receive_buffer) >= 3:
            if self._receive_buffer[0] != 0xAA:
                self._receive_buffer.pop(0)
                continue

            door_number = self._receive_buffer[1]
            state = self._receive_buffer[2]

            if door_number not in range(1, 17) or state not in (0, 1):
                self._receive_buffer.pop(0)
                continue

            del self._receive_buffer[:3]
            if self._receive_buffer and self._receive_buffer[0] == 0x2C:
                del self._receive_buffer[0]

            is_press = state == 1
            logging.info(
                f"AA帧解包成功 - 实体按钮通道 {door_number}: {'按下' if is_press else '释放'}"
            )
            self._handle_button_event(door_number, is_press)

    def _process_modbus_response(self, data: bytes):
        """解析 Modbus RTU 0x02 响应。"""
        if len(data) >= 5 and data[1] == 0x02:
            byte_cnt = data[2]
            if len(data) >= 3 + byte_cnt + 2:
                mask = data[3]
                if self._prev_modbus_mask is not None and mask != self._prev_modbus_mask:
                    changed = mask ^ self._prev_modbus_mask
                    for bit in range(8):
                        if changed & (1 << bit):
                            ch = bit + 1
                            is_press = bool(mask & (1 << bit))
                            logging.info(
                                f"Modbus帧解包成功 - 实体按钮通道 {ch}: {'按下' if is_press else '释放'}"
                            )
                            self._handle_button_event(ch, is_press)
                self._prev_modbus_mask = mask

    def _queue_button_click(self, button_name: str):
        """把串口线程中的动作安全投递到 Qt 界面线程。"""
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
            if hasattr(button, "animateClick"):
                QMetaObject.invokeMethod(button, "animateClick", Qt.QueuedConnection)
            else:
                QMetaObject.invokeMethod(button, "click", Qt.QueuedConnection)
        except Exception as exc:
            logging.warning(f"Qt 队列投递失败，降级执行: {exc}")
            button.click()

    def _handle_button_event(self, door_number: int, is_press: bool):
        """处理实体按钮与传感器动作触发逻辑，带 300ms 防抖。"""
        event_callback = getattr(self.home_instance, "on_rs485_event", None)
        if callable(event_callback):
            event_callback(self.port, door_number, is_press)

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
            (1, True): ("button_cancel", "复位"),
            (1, False): ("button_cancel", "复位"),
            (2, True): ("button_print", "打印箱码"),
            (2, False): ("button_print", "打印箱码"),
            (3, True): ("button_again", "拍照识别"),
            (3, False): ("button_again", "拍照识别"),
            (4, True): ("button_reset", "重新装箱"),
            (4, False): ("button_reset", "重新装箱"),
        }

        mapping = event_mapping.get((door_number, is_press))
        if mapping is None:
            logging.info(
                f"实体输入 通道{door_number} ({'按下' if is_press else '释放'})，未配置对应功能"
            )
            return

        button_name, function_name = mapping
        logging.info(
            f"实体按钮 通道{door_number} ({'按下' if is_press else '释放'}) 触发界面功能: 【{function_name}】 ({button_name})"
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
