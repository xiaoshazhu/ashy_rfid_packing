"""只读测试USB-RS485转换器的DTR/RTS收发方式。

每种模式只发送厂家协议规定的寄存器读取帧，不写任何寄存器。
"""

from __future__ import annotations

import time

import serial

from utils.td39_protocol import is_valid_frame
from utils.wdip_light_controller import build_read_registers, parse_read_registers


PORT = "COM3"
BAUDRATE = 9600
SLAVE = 1
QUERY = build_read_registers(SLAVE)


PROFILES = (
    ("驱动默认", None, None, None),
    ("DTR=1 RTS=1", True, True, None),
    ("DTR=1 RTS=0", True, False, None),
    ("DTR=0 RTS=1", False, True, None),
    ("DTR=0 RTS=0", False, False, None),
    ("RTS发送高/接收低", True, True, False),
    ("RTS发送低/接收高", True, False, True),
)


def find_valid_frame(raw: bytes) -> bytes | None:
    for start in range(max(0, len(raw) - 21 + 1)):
        frame = raw[start : start + 21]
        if (
            len(frame) == 21
            and frame[0] == SLAVE
            and frame[1] == 0x03
            and frame[2] == 0x10
            and is_valid_frame(frame)
        ):
            return frame
    return None


def read_once(connection: serial.Serial, receive_rts: bool | None) -> bytes:
    connection.reset_input_buffer()
    connection.write(QUERY)
    connection.flush()
    if receive_rts is not None:
        time.sleep(0.01)
        connection.rts = receive_rts
    deadline = time.monotonic() + 0.7
    raw = bytearray()
    while time.monotonic() < deadline:
        chunk = connection.read(64)
        if chunk:
            raw.extend(chunk)
        if find_valid_frame(bytes(raw)) is not None:
            break
    return bytes(raw)


def main() -> int:
    print(f"只读查询帧: {QUERY.hex(' ')}")
    print("将测试7种串口控制线模式，每种最多读取3次，不会写设备。")
    print()
    for name, dtr, transmit_rts, receive_rts in PROFILES:
        print(f"===== {name} =====")
        try:
            with serial.Serial(
                port=PORT,
                baudrate=BAUDRATE,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=0.08,
                write_timeout=0.7,
                xonxoff=False,
                rtscts=False,
                dsrdtr=False,
            ) as connection:
                if dtr is not None:
                    connection.dtr = dtr
                if transmit_rts is not None:
                    connection.rts = transmit_rts
                time.sleep(0.25)
                for attempt in range(1, 4):
                    if transmit_rts is not None:
                        connection.rts = transmit_rts
                    raw = read_once(connection, receive_rts)
                    frame = find_valid_frame(raw)
                    print(
                        f"第{attempt}次: length={len(raw)} data="
                        f"{raw.hex(' ') if raw else '<空响应>'}"
                    )
                    if frame is not None:
                        state = parse_read_registers(frame, SLAVE)
                        print(f"[成功模式] {name}")
                        print(
                            f"设定={state.set_voltage_v:.2f}V/{state.set_current_a:.3f}A，"
                            f"实际={state.output_voltage_v:.2f}V/{state.output_current_a:.3f}A，"
                            f"输出={'ON' if state.output_enabled else 'OFF'}"
                        )
                        return 0
                    time.sleep(0.25)
        except Exception as exc:
            print(f"模式失败: {exc}")
        time.sleep(0.35)
    print()
    print("[未找到有效模式] 所有返回都未通过标准Modbus CRC。")
    return 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("\n用户终止测试。")
        raise SystemExit(130)
