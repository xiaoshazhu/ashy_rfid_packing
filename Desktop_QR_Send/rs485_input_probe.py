"""RS485 顶部按钮只读通信探针 v4.0。"""

from __future__ import annotations

import argparse
import logging
import os
import sys
import time
from pathlib import Path
from typing import List, Optional, Tuple

import serial
from serial.tools import list_ports


APP_DIR = Path(__file__).resolve().parent
LOG_PATH = APP_DIR / "logs" / "rs485_input_probe.log"

TEST_BAUDRATES = (9600, 4800, 19200, 38400, 57600, 115200)
TEST_PARITIES = (
    ("N", serial.PARITY_NONE),
    ("E", serial.PARITY_EVEN),
    ("O", serial.PARITY_ODD),
)
TEST_RTS_STATES = (False, True)
TEST_SLAVES = tuple(range(1, 17))


def setup_logging() -> None:
    LOG_PATH.parent.mkdir(exist_ok=True)
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    root = logging.getLogger()
    root.handlers.clear()
    root.setLevel(logging.INFO)

    file_handler = logging.FileHandler(LOG_PATH, mode="w", encoding="utf-8")
    file_handler.setFormatter(formatter)
    root.addHandler(file_handler)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root.addHandler(console_handler)


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


def build_modbus_read(slave_addr: int, func_code: int, start: int = 0, count: int = 8) -> bytes:
    payload = bytes([slave_addr, func_code, (start >> 8) & 0xFF, start & 0xFF, (count >> 8) & 0xFF, count & 0xFF])
    crc = crc16_modbus(payload)
    return payload + bytes([crc & 0xFF, (crc >> 8) & 0xFF])


def parse_button_event(raw: bytes) -> Optional[str]:
    """尝试将收到的字节解析为已知协议格式。"""
    # 1. 尝试 AA 被动协议格式: AA channel state
    buf = bytearray(raw)
    while len(buf) >= 3:
        if buf[0] == 0xAA and buf[1] in range(1, 17) and buf[2] in (0, 1):
            ch = buf[1]
            st = "按下" if buf[2] == 1 else "释放"
            return f"AA协议 -> 通道【{ch}】 | 状态【{st}】"
        buf.pop(0)

    # 2. 尝试 TD-39 0x01 或 WDIP24-15-R 0x03 响应格式
    if len(raw) >= 5 and raw[1] in (0x01, 0x03):
        slave = raw[0]
        func = raw[1]
        byte_cnt = raw[2]
        if len(raw) >= 3 + byte_cnt + 2:
            frame = raw[:3 + byte_cnt + 2]
            expected_crc = crc16_modbus(frame[:-2])
            actual_crc = frame[-2] | (frame[-1] << 8)
            if expected_crc != actual_crc:
                return None
            if func == 0x01:
                mask = raw[3]
                return f"TD-39响应(从站{slave}) -> 输入掩码: 0x{mask:02X} (二进制: {mask:08b})"
            if func == 0x03 and byte_cnt == 16:
                registers = [
                    (raw[3 + index * 2] << 8) | raw[4 + index * 2]
                    for index in range(8)
                ]
                return f"WDIP24-15-R响应(从站{slave}) -> Reg0~7={registers}"

    return None


def probe_port_mode(
    port_name: str,
    baud: int,
    parity,
    rts: bool,
    duration: float = 0.8,
) -> Tuple[bool, Optional[bytes]]:
    """在指定的串口、波特率、RTS控制模式下测试并主动轮询。"""
    try:
        with serial.Serial(
            port=port_name,
            baudrate=baud,
            bytesize=serial.EIGHTBITS,
            parity=parity,
            stopbits=serial.STOPBITS_ONE,
            timeout=0.1,
        ) as ser:
            try:
                ser.dtr = True
                ser.rts = rts
            except Exception:
                pass

            ser.reset_input_buffer()

            # 只读扫描：TD-39 使用 0x01，WDIP24-15-R 使用 0x03。
            for slave in TEST_SLAVES:
                for func in (0x01, 0x03):
                    try:
                        cmd = build_modbus_read(slave, func, 0, 8)
                        ser.write(cmd)
                        ser.flush()
                        time.sleep(0.01)
                    except Exception:
                        pass

            # 监听该模式下是否有数据返回（主动响应或被动按键）
            deadline = time.monotonic() + duration
            received = bytearray()

            while time.monotonic() < deadline:
                if ser.in_waiting > 0:
                    data = ser.read(ser.in_waiting)
                    received.extend(data)
                    # 等待分段响应拼完整；只有识别出完整协议帧才提前返回。
                    if parse_button_event(bytes(received)) is not None:
                        return True, bytes(received)
                time.sleep(0.03)

            if received:
                return True, bytes(received)

    except (serial.SerialException, PermissionError, OSError) as exc:
        exc_msg = str(exc)
        if "Access is denied" in exc_msg or "拒绝访问" in exc_msg:
            logging.error(f"⚠️ [{port_name}] 串口被独占！请务必关闭 start.bat 程序！")
        return False, None

    return False, None


def main() -> int:
    parser = argparse.ArgumentParser(description="Multi-Mode Auto Sweeper Probe")
    parser.add_argument("--port", help="指定探测串口 (例如 COM3)")
    args = parser.parse_args()

    setup_logging()

    logging.info("=========================================================")
    logging.info("       RS485 顶部按钮只读通信探针 v4.0                ")
    logging.info("=========================================================")

    items = list(list_ports.comports())
    if not items:
        logging.error("❌ 错误：当前系统没有检测到任何串口设备！请检查插头。")
        return 1

    usb_ports = []
    other_ports = []
    for item in items:
        desc = (item.description or "").upper()
        hwid = (item.hwid or "").upper()
        info = f"{item.device} ({item.description})"
        if any(token in desc or token in hwid for token in ("USB", "CH34", "FTDI", "PL2303", "CP210", "SERIAL", "UART")):
            usb_ports.append((item.device, info))
        else:
            other_ports.append((item.device, info))

    ports_to_test = [dev for dev, info in usb_ports + other_ports]
    if args.port:
        ports_to_test = [args.port]

    logging.info(f"优先测试串口序列: {', '.join(ports_to_test)}")
    logging.info("说明：仅发送 Modbus 读取命令，扫描常见波特率、N/E/O校验、RTS状态和1~16站号。")
    logging.info("读取协议：TD-39=0x01；WDIP24-15-R=0x03；不会写寄存器、数据库或配置。")
    logging.info("💡 提示：在扫描过程中，请保持【反复按下顶部第 1 个按钮】！")
    logging.info("---------------------------------------------------------")

    found_working_config = False

    for port_name in ports_to_test:
        logging.info(f"\n🔍 >>> 开始测试串口: 【{port_name}】 <<<")

        for baud in TEST_BAUDRATES:
            for parity_name, parity_value in TEST_PARITIES:
                for rts in TEST_RTS_STATES:
                    mode_str = f"{port_name} @ {baud} baud | {parity_name}81 | RTS={rts}"
                    logging.info(f"正在扫描: {mode_str} ... (请持续按住/反复点击顶部按钮)")

                    got_data, raw_bytes = probe_port_mode(
                        port_name,
                        baud,
                        parity_value,
                        rts,
                        duration=0.8,
                    )

                    if got_data and raw_bytes:
                        hex_repr = raw_bytes.hex(" ")
                        parsed_info = parse_button_event(raw_bytes)

                        logging.info("=" * 60)
                        logging.info("【成功接收到串口数据】")
                        logging.info(f"匹配串口组合: {mode_str}")
                        logging.info(f"接收到的原始 Hex 数据: {hex_repr}")
                        if parsed_info:
                            logging.info(f"自动协议解包成功: {parsed_info}")
                        else:
                            logging.warning("收到字节，但尚未形成CRC正确的TD-39/WDIP完整响应。")
                        logging.info("=" * 60)

                        found_working_config = True

                        # 发现工作模式后，进入相同参数的持续只读监听。
                        logging.info(f"\n进入【{mode_str}】模式的实时只读监听...")
                        logging.info("现在请依次按下顶部 4 个按钮，观察通道显示：")

                        try:
                            with serial.Serial(
                                port=port_name,
                                baudrate=baud,
                                bytesize=serial.EIGHTBITS,
                                parity=parity_value,
                                stopbits=serial.STOPBITS_ONE,
                                timeout=0.1,
                            ) as live_ser:
                                live_ser.dtr = True
                                live_ser.rts = rts
                                live_ser.reset_input_buffer()

                                last_poll = 0

                                while True:
                                    now = time.monotonic()
                                    if now - last_poll > 0.5:
                                        for slave in TEST_SLAVES:
                                            for func in (0x01, 0x03):
                                                try:
                                                    live_ser.write(build_modbus_read(slave, func, 0, 8))
                                                    live_ser.flush()
                                                    time.sleep(0.01)
                                                except Exception:
                                                    pass
                                        last_poll = now

                                    if live_ser.in_waiting > 0:
                                        data = live_ser.read(live_ser.in_waiting)
                                        h_str = data.hex(" ")
                                        logging.info(f"[{port_name}] 收到数据: {h_str}")
                                        evt = parse_button_event(bytes(data))
                                        if evt:
                                            logging.info(evt)

                                    time.sleep(0.04)

                        except KeyboardInterrupt:
                            logging.info("用户结束测试。")
                            return 0
                        except Exception as exc:
                            logging.error(f"监听中断: {exc}")

    if not found_working_config:
        logging.error(
            "\n结论：在常见波特率、N/E/O校验、RTS状态及Modbus 1~16站号轮询下均未收到任何数据字节。"
        )
        logging.error("排查建议：")
        logging.error("1. 请确认 USB 转 RS485 转换线的 A、B 两根接线没有接反（A接A，B接B；尝试将 A/B 两根线对调）。")
        logging.error("2. 请确认 RS485 采集模块是否有 12V/24V 供电线未连接。")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
