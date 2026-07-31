"""TD-39 开关量输入模块的 Modbus-RTU 协议工具。

本模块不依赖串口或界面库，供正式程序、现场监听工具和自动测试共同使用。
TD-39 用户手册 V1.3 规定：

- 默认从站地址：1
- 默认串口参数：9600 / 8N1
- 功能码 0x01：读取多个线圈（开关量输入）状态
- 照片中的硬件为 12 路板，00001~00012 对应 DI0~DI11
- 位值 1 表示闭合，0 表示断开
"""

from __future__ import annotations

from typing import Iterable, List


TD39_DEFAULT_SLAVE = 1
TD39_BAUDRATE = 9600
TD39_DI_FUNCTION = 0x01
TD39_DI_START = 0
TD39_DI_COUNT = 12
TD39_ACTION_DI_COUNT = 5
TD39_MONITOR_VERSION = "2.1-12DI-50MS"


def crc16_modbus(data: bytes) -> int:
    """计算 Modbus CRC16，返回低字节在帧中先发送的整数值。"""
    crc = 0xFFFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 1:
                crc = (crc >> 1) ^ 0xA001
            else:
                crc >>= 1
    return crc


def append_crc(payload: bytes) -> bytes:
    """为不含 CRC 的 Modbus 数据追加低字节在前的 CRC。"""
    crc = crc16_modbus(payload)
    return payload + bytes((crc & 0xFF, (crc >> 8) & 0xFF))


def build_read_inputs(
    slave_addr: int = TD39_DEFAULT_SLAVE,
    start: int = TD39_DI_START,
    count: int = TD39_DI_COUNT,
) -> bytes:
    """构造读取 TD-39 输入状态的 0x01 请求帧。"""
    if not 1 <= slave_addr <= 247:
        raise ValueError("Modbus 从站地址必须在 1~247 之间")
    if not 0 <= start <= 0xFFFF:
        raise ValueError("Modbus 起始地址必须在 0~65535 之间")
    if not 1 <= count <= 2000:
        raise ValueError("Modbus 读取数量必须在 1~2000 之间")

    payload = bytes(
        (
            slave_addr,
            TD39_DI_FUNCTION,
            (start >> 8) & 0xFF,
            start & 0xFF,
            (count >> 8) & 0xFF,
            count & 0xFF,
        )
    )
    return append_crc(payload)


def is_valid_frame(frame: bytes) -> bool:
    """校验完整 Modbus-RTU 帧的 CRC。"""
    if len(frame) < 4:
        return False
    expected = crc16_modbus(frame[:-2])
    received = frame[-2] | (frame[-1] << 8)
    return expected == received


def decode_input_mask(
    frame: bytes,
    slave_addr: int = TD39_DEFAULT_SLAVE,
    count: int = TD39_DI_COUNT,
) -> int:
    """解析 0x01 响应并返回输入状态位掩码。

    返回值的 bit0 对应模块 DI0（软件显示为通道 1），以此类推。
    """
    if not is_valid_frame(frame):
        raise ValueError("Modbus 响应 CRC 校验失败")
    if len(frame) < 6:
        raise ValueError("Modbus 响应长度不足")
    if frame[0] != slave_addr:
        raise ValueError(f"响应从站地址不匹配: {frame[0]}")
    if frame[1] & 0x80:
        raise ValueError(f"设备返回 Modbus 异常码: 0x{frame[2]:02X}")
    if frame[1] != TD39_DI_FUNCTION:
        raise ValueError(f"响应功能码不是 0x01: 0x{frame[1]:02X}")

    byte_count = frame[2]
    expected_byte_count = (count + 7) // 8
    if byte_count < expected_byte_count:
        raise ValueError(
            f"响应状态字节不足: 实际 {byte_count}，至少需要 {expected_byte_count}"
        )
    if len(frame) != 3 + byte_count + 2:
        raise ValueError("Modbus 响应声明长度与实际长度不一致")

    mask = 0
    for index, value in enumerate(frame[3 : 3 + byte_count]):
        mask |= value << (index * 8)
    return mask & ((1 << count) - 1)


def states_from_mask(mask: int, count: int = TD39_DI_COUNT) -> List[bool]:
    """把位掩码转换为前 count 路状态，True=闭合，False=断开。"""
    if count < 1:
        raise ValueError("通道数量必须大于 0")
    return [bool(mask & (1 << bit)) for bit in range(count)]


def format_input_states(
    states: Iterable[bool],
    include_module_names: bool = True,
) -> str:
    """将状态格式化为便于现场查看的一行中文文本。"""
    parts = []
    for index, closed in enumerate(states, start=1):
        name = f"通道{index}"
        if include_module_names:
            name += f"(DI{index - 1})"
        parts.append(f"{name}={'闭合' if closed else '断开'}")
    return " | ".join(parts)


class TD39ResponseParser:
    """从可能粘包、拆包或夹杂噪声的串口字节流中提取响应帧。"""

    def __init__(self, slave_addr: int = TD39_DEFAULT_SLAVE):
        self.slave_addr = slave_addr
        self.buffer = bytearray()

    def feed(self, data: bytes) -> List[bytes]:
        self.buffer.extend(data)
        frames: List[bytes] = []

        while self.buffer:
            if self.buffer[0] != self.slave_addr:
                del self.buffer[0]
                continue

            if len(self.buffer) < 2:
                break

            function = self.buffer[1]
            if function & 0x80:
                frame_length = 5
            elif function == TD39_DI_FUNCTION:
                if len(self.buffer) < 3:
                    break
                byte_count = self.buffer[2]
                if byte_count > 250:
                    del self.buffer[0]
                    continue
                frame_length = 3 + byte_count + 2
            else:
                del self.buffer[0]
                continue

            if len(self.buffer) < frame_length:
                break

            frame = bytes(self.buffer[:frame_length])
            if not is_valid_frame(frame):
                del self.buffer[0]
                continue

            del self.buffer[:frame_length]
            frames.append(frame)

        return frames
