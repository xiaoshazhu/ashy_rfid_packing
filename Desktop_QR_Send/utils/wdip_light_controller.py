"""WDIP24-15-R 可调电源（补光灯）Modbus-RTU 控制。

协议依据项目内《WDIP24-15-R导轨式隔离型可调电源Modbus通讯协议》：
- 默认 9600/8N1、从站 1
- 功能码 0x03 读取 0x0000~0x0007
- 0x0003 为设置输出电压，单位 0.01V，最大 24.00V
- 0x0005 为输出控制，1=打开
- 功能码 0x06 写单寄存器
"""

from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass
from typing import Iterable, Optional

import serial
from serial.tools import list_ports

from utils.td39_protocol import append_crc, is_valid_frame


logger = logging.getLogger("WDIPLightController")

WDIP_DEFAULT_SLAVE = 1
WDIP_DEFAULT_BAUDRATE = 9600
WDIP_REGISTER_COUNT = 8
WDIP_SET_VOLTAGE_REGISTER = 0x0003
WDIP_SET_CURRENT_REGISTER = 0x0004
WDIP_OUTPUT_CONTROL_REGISTER = 0x0005
WDIP_BAUDRATE_REGISTER = 0x0006
WDIP_OPERATING_REGISTER_START = WDIP_SET_VOLTAGE_REGISTER
WDIP_OPERATING_REGISTER_COUNT = 4
WDIP_MAX_VOLTAGE_CENTIVOLTS = 2400
WDIP_MAX_CURRENT_MILLIAMPS = 2000
WDIP_MAX_OUTPUT_POWER_WATTS = 15.0


@dataclass(frozen=True)
class WDIPState:
    reserved: int
    output_voltage_v: float
    output_current_a: float
    set_voltage_v: float
    set_current_a: float
    output_enabled: bool
    baudrate_code: int
    saved: int


def build_read_registers(slave_addr: int = WDIP_DEFAULT_SLAVE) -> bytes:
    payload = bytes((slave_addr, 0x03, 0x00, 0x00, 0x00, WDIP_REGISTER_COUNT))
    return append_crc(payload)


def build_write_register(slave_addr: int, register: int, value: int) -> bytes:
    if not 1 <= int(slave_addr) <= 247:
        raise ValueError("WDIP 从站地址必须在1~247之间")
    if not 0 <= int(register) <= 0xFFFF or not 0 <= int(value) <= 0xFFFF:
        raise ValueError("WDIP 寄存器地址和值必须在0~65535之间")
    payload = bytes(
        (
            int(slave_addr),
            0x06,
            (int(register) >> 8) & 0xFF,
            int(register) & 0xFF,
            (int(value) >> 8) & 0xFF,
            int(value) & 0xFF,
        )
    )
    return append_crc(payload)


def build_write_multiple_registers(
    slave_addr: int,
    start_register: int,
    values: Iterable[int],
) -> bytes:
    """构造功能码0x10写多个寄存器帧（数值按大端序，CRC低字节先发）。"""
    register_values = [int(value) for value in values]
    if not 1 <= int(slave_addr) <= 247:
        raise ValueError("WDIP 从站地址必须在1~247之间")
    if not 0 <= int(start_register) <= 0xFFFF:
        raise ValueError("WDIP 起始寄存器地址必须在0~65535之间")
    if not 1 <= len(register_values) <= 123:
        raise ValueError("WDIP 多寄存器写入数量必须在1~123之间")
    if any(not 0 <= value <= 0xFFFF for value in register_values):
        raise ValueError("WDIP 寄存器值必须在0~65535之间")

    payload = bytearray(
        (
            int(slave_addr),
            0x10,
            (int(start_register) >> 8) & 0xFF,
            int(start_register) & 0xFF,
            (len(register_values) >> 8) & 0xFF,
            len(register_values) & 0xFF,
            len(register_values) * 2,
        )
    )
    for value in register_values:
        payload.extend(((value >> 8) & 0xFF, value & 0xFF))
    return append_crc(bytes(payload))


def parse_read_registers(
    frame: bytes,
    slave_addr: int = WDIP_DEFAULT_SLAVE,
    require_valid_crc: bool = True,
) -> WDIPState:
    if len(frame) != 21 or (require_valid_crc and not is_valid_frame(frame)):
        raw = frame.hex(" ") if frame else "<空响应>"
        raise ValueError(f"WDIP读取响应长度或CRC错误: length={len(frame)} data={raw}")
    if frame[0] != slave_addr or frame[1] != 0x03 or frame[2] != 16:
        raise ValueError("WDIP 读取响应站号、功能码或字节数错误")
    registers = [
        int.from_bytes(frame[3 + index * 2 : 5 + index * 2], "big")
        for index in range(WDIP_REGISTER_COUNT)
    ]
    return WDIPState(
        reserved=registers[0],
        output_voltage_v=registers[1] / 100.0,
        output_current_a=registers[2] / 1000.0,
        set_voltage_v=registers[3] / 100.0,
        set_current_a=registers[4] / 1000.0,
        output_enabled=registers[5] == 1,
        baudrate_code=registers[6],
        saved=registers[7],
    )


class WDIPLightController:
    def __init__(
        self,
        port: Optional[str] = None,
        baudrate: int = WDIP_DEFAULT_BAUDRATE,
        slave_addr: int = WDIP_DEFAULT_SLAVE,
        timeout: float = 0.3,
        excluded_ports: Iterable[str] = (),
        allow_stable_crc_mismatch_readback: bool = False,
        minimum_request_interval: float = 0.25,
        write_settle_seconds: float = 0.4,
        shared_exchange=None,
    ):
        self.port = str(port).strip() if port else None
        self.baudrate = int(baudrate)
        self.slave_addr = int(slave_addr)
        self.timeout = float(timeout)
        self.excluded_ports = {str(item).upper() for item in excluded_ports if item}
        self.allow_stable_crc_mismatch_readback = bool(
            allow_stable_crc_mismatch_readback
        )
        self.minimum_request_interval = max(0.05, float(minimum_request_interval))
        self.write_settle_seconds = max(0.1, float(write_settle_seconds))
        self.shared_exchange = shared_exchange
        self._io_lock = threading.RLock()
        self._last_exchange_finished_at = 0.0

    def _candidate_ports(self):
        if self.port:
            return [self.port]
        items = list(list_ports.comports())
        usb = []
        other = []
        for item in items:
            device = item.device
            if str(device).upper() in self.excluded_ports:
                continue
            marker = f"{item.description or ''} {item.hwid or ''}".upper()
            target = usb if any(token in marker for token in ("USB", "CH34", "FTDI", "CP210", "PL2303")) else other
            target.append(device)
        return usb + other

    def _exchange(self, port: str, request: bytes, response_size: int) -> bytes:
        """串行、限速执行一次Modbus事务，写入后为电源调整预留稳定时间。"""
        with self._io_lock:
            elapsed = time.monotonic() - self._last_exchange_finished_at
            remaining = self.minimum_request_interval - elapsed
            if remaining > 0:
                time.sleep(remaining)
            response = self._exchange_unlocked(port, request, response_size)
            if len(request) > 1 and request[1] in (0x06, 0x10):
                time.sleep(self.write_settle_seconds)
            self._last_exchange_finished_at = time.monotonic()
            return response

    def _exchange_unlocked(self, port: str, request: bytes, response_size: int) -> bytes:
        if callable(self.shared_exchange):
            # 当配置了共享 RS485 时，最多重试 4 次通过共享总线与硬件通信
            for attempt in range(4):
                try:
                    shared_response = self.shared_exchange(
                        port, request, response_size, self.timeout
                    )
                    if shared_response is not None and len(shared_response) > 0:
                        raw = bytes(shared_response)
                        normalized = self._extract_response(request, raw, response_size)
                        return normalized if normalized is not None else raw
                except Exception as err:
                    logger.debug(f"共享RS485第 {attempt + 1} 次尝试异常: {err}")
                time.sleep(0.12)
            # 共享总线已启用时，绝不擅自打开独立串口避免引发 PermissionError 拒绝访问
            return b""

        # 仅在未配置共享总线时，独立尝试独占打开串口，带 3 次重试与异常捕获
        last_error = None
        for attempt in range(3):
            try:
                with serial.Serial(
                    port=port,
                    baudrate=self.baudrate,
                    bytesize=serial.EIGHTBITS,
                    parity=serial.PARITY_NONE,
                    stopbits=serial.STOPBITS_ONE,
                    timeout=0.05,
                    write_timeout=self.timeout,
                ) as connection:
                    time.sleep(0.12)
                    longest_response = b""
                    for _ in range(2):
                        connection.reset_input_buffer()
                        connection.write(request)
                        connection.flush()
                        deadline = time.monotonic() + self.timeout
                        response = bytearray()
                        while time.monotonic() < deadline:
                            remaining = max(1, response_size * 3 - len(response))
                            chunk = connection.read(min(64, remaining))
                            if chunk:
                                response.extend(chunk)
                            normalized = self._extract_response(
                                request, bytes(response), response_size
                            )
                            if normalized is not None:
                                return normalized
                            if len(response) >= response_size * 3:
                                break
                        if len(response) > len(longest_response):
                            longest_response = bytes(response)
                        time.sleep(self.minimum_request_interval)
                    return longest_response
            except Exception as exc:
                last_error = exc
                time.sleep(0.2)

        if last_error:
            logger.warning(f"直接打开串口 [{port}] 尝试失败: {last_error}")
        return b""

    def _extract_response(self, request: bytes, raw: bytes, response_size: int) -> Optional[bytes]:
        """从可能含本地发送回显的数据中提取一个完整有效的Modbus帧。"""
        if len(request) < 2:
            return None
        slave_addr, function = request[0], request[1]
        if function == 0x03:
            for start in range(max(0, len(raw) - response_size + 1)):
                frame = raw[start : start + response_size]
                if (
                    len(frame) == response_size
                    and frame[0] == slave_addr
                    and frame[1] == function
                    and frame[2] == 16
                    and (
                        is_valid_frame(frame)
                        or self.allow_stable_crc_mismatch_readback
                    )
                ):
                    return frame
            return None
        if function == 0x06:
            for start in range(max(0, len(raw) - len(request) + 1)):
                frame = raw[start : start + len(request)]
                if frame[:6] == request[:6] and (
                    is_valid_frame(frame)
                    or self.allow_stable_crc_mismatch_readback
                ):
                    return frame
        if function == 0x10:
            # 0x10响应为：站号、功能码、起始地址、寄存器数量、CRC，共8字节。
            expected_prefix = request[:6]
            for start in range(max(0, len(raw) - 8 + 1)):
                frame = raw[start : start + 8]
                if (
                    len(frame) == 8
                    and frame[:6] == expected_prefix
                    and (
                        is_valid_frame(frame)
                        or self.allow_stable_crc_mismatch_readback
                    )
                ):
                    return frame
        return None

    def read_state(self, port: Optional[str] = None) -> WDIPState:
        target = port or self.port
        if not target:
            raise RuntimeError("尚未确定WDIP补光灯串口")
        request = build_read_registers(self.slave_addr)
        response = self._exchange(target, request, 21)
        if is_valid_frame(response):
            state = parse_read_registers(response, self.slave_addr)
            self.port = target
            return state

        if not self.allow_stable_crc_mismatch_readback:
            state = parse_read_registers(response, self.slave_addr)
            self.port = target
            return state

        first = parse_read_registers(
            response,
            self.slave_addr,
            require_valid_crc=False,
        )
        confirmation_response = self._exchange(target, request, 21)
        confirmation = parse_read_registers(
            confirmation_response,
            self.slave_addr,
            require_valid_crc=is_valid_frame(confirmation_response),
        )
        first_control = (
            first.set_voltage_v,
            first.set_current_a,
            first.output_enabled,
            first.baudrate_code,
            first.saved,
        )
        confirmation_control = (
            confirmation.set_voltage_v,
            confirmation.set_current_a,
            confirmation.output_enabled,
            confirmation.baudrate_code,
            confirmation.saved,
        )
        if first_control != confirmation_control:
            raise RuntimeError(
                "WDIP连续两次CRC异常响应的关键寄存器不一致，拒绝采用："
                f"first={response.hex(' ')} second={confirmation_response.hex(' ')}"
            )
        logger.warning(
            "WDIP响应CRC异常，但连续两次关键寄存器一致，采用稳定回读："
            "port=%s voltage=%.2fV current=%.3fA output=%s saved=%s",
            target,
            confirmation.set_voltage_v,
            confirmation.set_current_a,
            "ON" if confirmation.output_enabled else "OFF",
            confirmation.saved,
        )
        state = confirmation
        self.port = target
        return state

    def discover(self) -> WDIPState:
        errors = []
        for port in self._candidate_ports():
            try:
                state = self.read_state(port)
                logger.info(
                    "发现WDIP补光灯控制器: port=%s set_voltage=%.2fV output=%s",
                    port,
                    state.set_voltage_v,
                    "ON" if state.output_enabled else "OFF",
                )
                return state
            except Exception as exc:
                errors.append(f"{port}: {exc}")
        detail = "; ".join(errors) if errors else "没有可用候选串口"
        raise RuntimeError(f"未发现WDIP补光灯控制器（{detail}）")

    def _write_register(self, register: int, value: int) -> WDIPState:
        if not self.port:
            raise RuntimeError("尚未发现WDIP补光灯控制器")
        request = build_write_register(self.slave_addr, register, value)
        response = self._exchange(self.port, request, len(request))
        acknowledgement_valid = response == request and is_valid_frame(response)
        if not acknowledgement_valid:
            logger.warning(
                "WDIP写寄存器回显异常，将以连续稳定回读确认是否写入成功: "
                "register=0x%04X request=%s response=%s",
                register,
                request.hex(" "),
                response.hex(" ") if response else "<空响应>",
            )
        state = self.read_state()
        expected_matches = {
            WDIP_SET_VOLTAGE_REGISTER: abs(state.set_voltage_v - value / 100.0) <= 0.011,
            WDIP_SET_CURRENT_REGISTER: abs(state.set_current_a - value / 1000.0) <= 0.0011,
            WDIP_OUTPUT_CONTROL_REGISTER: state.output_enabled is bool(value),
            WDIP_BAUDRATE_REGISTER: state.baudrate_code == value,
        }.get(register, acknowledgement_valid)
        if not expected_matches:
            raise RuntimeError(
                "WDIP写寄存器后回读不一致: "
                f"register=0x{register:04X} request={request.hex(' ')} "
                f"response={response.hex(' ') if response else '<空响应>'}"
            )
        return state

    def _write_operating_registers(
        self,
        voltage_centivolts: int,
        current_milliamps: int,
        output_enabled: bool,
        baudrate_code: int,
    ) -> WDIPState:
        """按厂家上位机方式，用0x10一次写入Reg3~Reg6。"""
        if not self.port:
            raise RuntimeError("尚未发现WDIP补光灯控制器")
        request = build_write_multiple_registers(
            self.slave_addr,
            WDIP_OPERATING_REGISTER_START,
            (
                voltage_centivolts,
                current_milliamps,
                1 if output_enabled else 0,
                baudrate_code,
            ),
        )
        response = self._exchange(self.port, request, 8)
        acknowledgement_valid = not (
            len(response) != 8
            or response[:6] != request[:6]
            or not is_valid_frame(response)
        )
        if not acknowledgement_valid:
            logger.warning(
                "WDIP写Reg3~Reg6响应异常，将以连续稳定回读确认是否写入成功: "
                "request=%s response=%s",
                request.hex(" "),
                response.hex(" ") if response else "<空响应>",
            )
        state = self.read_state()
        if (
            abs(state.set_voltage_v - voltage_centivolts / 100.0) > 0.011
            or abs(state.set_current_a - current_milliamps / 1000.0) > 0.0011
            or state.output_enabled is not bool(output_enabled)
            or state.baudrate_code != baudrate_code
        ):
            raise RuntimeError(
                "WDIP写Reg3~Reg6后回读不一致: "
                f"request={request.hex(' ')} response="
                f"{response.hex(' ') if response else '<空响应>'}"
            )
        return state

    def set_voltage(self, voltage_v: float) -> WDIPState:
        centivolts = int(round(float(voltage_v) * 100.0))
        if not 0 <= centivolts <= WDIP_MAX_VOLTAGE_CENTIVOLTS:
            raise ValueError("WDIP设置电压必须在0.00V~24.00V之间")
        current = self.read_state()
        if centivolts / 100.0 * current.set_current_a > WDIP_MAX_OUTPUT_POWER_WATTS + 0.001:
            raise ValueError(
                f"目标电压{centivolts / 100.0:.2f}V与当前电流上限"
                f"{current.set_current_a:.3f}A的乘积超过WDIP最大15W"
            )
        state = self._write_operating_registers(
            centivolts,
            int(round(current.set_current_a * 1000.0)),
            current.output_enabled,
            current.baudrate_code,
        )
        if abs(state.set_voltage_v - centivolts / 100.0) > 0.011:
            raise RuntimeError(
                f"WDIP设置电压回读不一致: 期望{centivolts / 100.0:.2f}V，实际{state.set_voltage_v:.2f}V"
            )
        return state

    def set_voltage_direct(self, voltage_v: float) -> bytes:
        """只发送设定电压命令，不以WDIP返回内容作为成功前提。"""
        if not self.port:
            raise RuntimeError("尚未指定WDIP补光灯串口")
        centivolts = int(round(float(voltage_v) * 100.0))
        if not 0 <= centivolts <= WDIP_MAX_VOLTAGE_CENTIVOLTS:
            raise ValueError("WDIP设置电压必须在0.00V~24.00V之间")
        request = build_write_register(
            self.slave_addr,
            WDIP_SET_VOLTAGE_REGISTER,
            centivolts,
        )
        response = self._exchange(self.port, request, len(request))
        logger.info(
            "WDIP直接发送设定电压: port=%s voltage=%.2fV request=%s response=%s",
            self.port,
            centivolts / 100.0,
            request.hex(" "),
            response.hex(" ") if response else "<未收到/未采用返回>",
        )
        return request

    def set_output_enabled_direct(self, enabled: bool) -> bytes:
        """只发送输出开关命令，不要求WDIP返回通过CRC或回读确认。"""
        if not self.port:
            raise RuntimeError("尚未指定WDIP补光灯串口")
        request = build_write_register(
            self.slave_addr,
            WDIP_OUTPUT_CONTROL_REGISTER,
            1 if enabled else 0,
        )
        response = self._exchange(self.port, request, len(request))
        logger.info(
            "WDIP直接发送输出%s: port=%s request=%s response=%s",
            "ON" if enabled else "OFF",
            self.port,
            request.hex(" "),
            response.hex(" ") if response else "<未收到/未采用返回>",
        )
        return request

    def set_current(self, current_a: float) -> WDIPState:
        """设置输出电流上限；调用方必须使用灯具铭牌规定的真实参数。"""
        milliamps = int(round(float(current_a) * 1000.0))
        if not 0 <= milliamps <= WDIP_MAX_CURRENT_MILLIAMPS:
            raise ValueError("WDIP设置电流必须在0.000A~2.000A之间")
        current = self.read_state()
        if current.set_voltage_v * milliamps / 1000.0 > WDIP_MAX_OUTPUT_POWER_WATTS + 0.001:
            raise ValueError(
                f"当前电压{current.set_voltage_v:.2f}V与目标电流上限"
                f"{milliamps / 1000.0:.3f}A的乘积超过WDIP最大15W"
            )
        state = self._write_operating_registers(
            int(round(current.set_voltage_v * 100.0)),
            milliamps,
            current.output_enabled,
            current.baudrate_code,
        )
        if abs(state.set_current_a - milliamps / 1000.0) > 0.0011:
            raise RuntimeError(
                f"WDIP设置电流回读不一致: 期望{milliamps / 1000.0:.3f}A，实际{state.set_current_a:.3f}A"
            )
        return state

    def set_output_enabled(self, enabled: bool) -> WDIPState:
        """打开或关闭真实输出；不会擅自改动设备已有电压、电流设定。"""
        if enabled:
            current = self.read_state()
            if current.set_voltage_v <= 0:
                raise RuntimeError("WDIP设定电压为0V，拒绝打开输出")
            if current.set_current_a <= 0:
                raise RuntimeError("WDIP设定电流为0A，拒绝打开输出")
            if (
                current.set_voltage_v * current.set_current_a
                > WDIP_MAX_OUTPUT_POWER_WATTS + 0.001
            ):
                raise RuntimeError(
                    f"当前设定{current.set_voltage_v:.2f}V×{current.set_current_a:.3f}A"
                    "超过WDIP最大15W，拒绝打开输出"
                )
        state = self._write_register(WDIP_OUTPUT_CONTROL_REGISTER, 1 if enabled else 0)
        if state.output_enabled is not bool(enabled):
            expected = "打开" if enabled else "关闭"
            actual = "打开" if state.output_enabled else "关闭"
            raise RuntimeError(f"WDIP输出控制回读不一致: 期望{expected}，实际{actual}")
        return state
