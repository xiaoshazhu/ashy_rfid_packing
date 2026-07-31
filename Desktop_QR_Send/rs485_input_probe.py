"""TD-39 12 路输入现场监听工具（重点核对前 5 路业务输入）。

运行前必须关闭正式装箱扫码程序，因为同一个 Windows COM 口不能同时被两个
程序占用。本工具只发送 TD-39 手册规定的 0x01 只读查询，不会写入设备参数。
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from pathlib import Path
from typing import Iterable, List, Optional, Tuple

import serial
from serial.tools import list_ports

from utils.td39_protocol import (
    TD39_ACTION_DI_COUNT,
    TD39_BAUDRATE,
    TD39_DEFAULT_SLAVE,
    TD39_DI_COUNT,
    TD39_MONITOR_VERSION,
    TD39ResponseParser,
    build_read_inputs,
    decode_input_mask,
    format_input_states,
    states_from_mask,
)


APP_DIR = Path(__file__).resolve().parent
LOG_PATH = APP_DIR / "logs" / "rs485_input_probe.log"
CONFIG_PATH = APP_DIR / "config.json"
POLL_INTERVAL_SECONDS = 0.05
PORT_PROBE_SECONDS = 3.0
NO_RESPONSE_WARNING_SECONDS = 3.0
HEARTBEAT_SECONDS = 5.0
UNCHANGED_NOTICE_SECONDS = 10.0


def setup_logging() -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
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


def configured_port() -> Optional[str]:
    try:
        with CONFIG_PATH.open("r", encoding="utf-8") as stream:
            value = json.load(stream).get("combobox_comSelect")
        return str(value) if value else None
    except (OSError, ValueError, TypeError):
        return None


def _is_usb_serial(item) -> bool:
    text = f"{item.description or ''} {item.hwid or ''}".upper()
    return any(
        token in text
        for token in ("USB", "CH34", "FTDI", "PL2303", "CP210", "SERIAL", "UART")
    )


def candidate_ports(explicit_port: Optional[str]) -> List[str]:
    """按命令行、软件配置、USB 串口、其他串口的顺序返回去重列表。"""
    items = list(list_ports.comports())
    preferred = [item.device for item in items if _is_usb_serial(item)]
    other = [item.device for item in items if not _is_usb_serial(item)]

    ordered: List[str] = []
    for value in (explicit_port, configured_port(), *preferred, *other):
        if value and value not in ordered:
            ordered.append(value)
    return ordered


def open_port(port: str, baudrate: int):
    connection = serial.Serial(
        port=port,
        baudrate=baudrate,
        bytesize=serial.EIGHTBITS,
        parity=serial.PARITY_NONE,
        stopbits=serial.STOPBITS_ONE,
        timeout=0.08,
    )
    try:
        connection.dtr = True
        connection.rts = True
    except Exception as exc:
        logging.warning("[%s] DTR/RTS 设置失败（自动收发转换器可忽略）: %s", port, exc)
    return connection


def read_valid_frames(connection, parser: TD39ResponseParser) -> Iterable[Tuple[bytes, int]]:
    waiting = connection.in_waiting
    if waiting <= 0:
        return ()

    data = connection.read(waiting)
    logging.debug(
        "RX-RAW port=%s bytes=%s hex=%s",
        connection.port,
        len(data),
        data.hex(" "),
    )

    result = []
    for frame in parser.feed(data):
        if frame[1] & 0x80:
            logging.error(
                "设备返回 Modbus 异常: function=0x%02X code=0x%02X frame=%s",
                frame[1],
                frame[2],
                frame.hex(" "),
            )
            continue
        try:
            mask = decode_input_mask(frame, parser.slave_addr, TD39_DI_COUNT)
        except ValueError as exc:
            logging.warning("忽略无法解析的响应 %s: %s", frame.hex(" "), exc)
            continue
        result.append((frame, mask))
    return result


def probe_port(
    port: str,
    baudrate: int,
    slave_addr: int,
    query: bytes,
    duration: float = PORT_PROBE_SECONDS,
) -> bool:
    """在一个候选 COM 口上寻找至少一帧有效 TD-39 响应。"""
    logging.info(
        "检测串口 %s: baud=%s format=8N1 slave=%s query=%s",
        port,
        baudrate,
        slave_addr,
        query.hex(" "),
    )
    try:
        with open_port(port, baudrate) as connection:
            connection.reset_input_buffer()
            parser = TD39ResponseParser(slave_addr)
            deadline = time.monotonic() + duration
            last_poll = 0.0

            while time.monotonic() < deadline:
                now = time.monotonic()
                if now - last_poll >= POLL_INTERVAL_SECONDS:
                    connection.write(query)
                    connection.flush()
                    last_poll = now

                for frame, mask in read_valid_frames(connection, parser):
                    logging.info(
                        "找到有效 TD-39 响应: port=%s frame=%s states=[%s]",
                        port,
                        frame.hex(" "),
                        format_input_states(states_from_mask(mask)),
                    )
                    return True
                time.sleep(0.02)
    except (serial.SerialException, PermissionError, OSError) as exc:
        message = str(exc)
        if "Access is denied" in message or "拒绝访问" in message:
            logging.error(
                "[%s] 串口被占用。请先关闭正式程序 start.bat 和其他串口工具。",
                port,
            )
        else:
            logging.error("[%s] 无法打开或读取: %s", port, exc)
    return False


def monitor_port(
    port: str,
    baudrate: int,
    slave_addr: int,
    query: bytes,
    duration: float,
) -> int:
    """持续显示全部 12 路的初始状态与每一次状态变化。"""
    logging.info("=" * 72)
    logging.info("已锁定 TD-39 串口: %s @ %s / 8N1 / 从站 %s", port, baudrate, slave_addr)
    logging.info(
        "正在监听全部 %s 路 DI0~DI%s；其中 DI0~DI%s 是当前业务触发范围。",
        TD39_DI_COUNT,
        TD39_DI_COUNT - 1,
        TD39_ACTION_DI_COUNT - 1,
    )
    logging.info("请依次按下并释放按钮/传感器；按 Ctrl+C 可结束。")
    logging.info("查询帧: %s", query.hex(" "))
    logging.info("=" * 72)

    with open_port(port, baudrate) as connection:
        connection.reset_input_buffer()
        parser = TD39ResponseParser(slave_addr)
        previous_mask: Optional[int] = None
        last_poll = 0.0
        last_valid = time.monotonic()
        last_warning = 0.0
        last_heartbeat = 0.0
        last_state_change = time.monotonic()
        last_unchanged_notice = 0.0
        valid_frames = 0
        channel_events = 0
        started_at = time.monotonic()

        while True:
            now = time.monotonic()
            if duration > 0 and now - started_at >= duration:
                break

            if now - last_poll >= POLL_INTERVAL_SECONDS:
                connection.write(query)
                connection.flush()
                last_poll = now

            for frame, mask in read_valid_frames(connection, parser):
                valid_frames += 1
                last_valid = now
                states = states_from_mask(mask)

                if previous_mask is None:
                    last_state_change = now
                    logging.info(
                        "INITIAL frame=%s states=[%s]",
                        frame.hex(" "),
                        format_input_states(states),
                    )
                elif mask != previous_mask:
                    last_state_change = now
                    changed = mask ^ previous_mask
                    logging.info(
                        "STATE-CHANGE frame=%s states=[%s]",
                        frame.hex(" "),
                        format_input_states(states),
                    )
                    for bit in range(TD39_DI_COUNT):
                        if changed & (1 << bit):
                            channel_events += 1
                            logging.info(
                                "CHANNEL-EVENT no=%s 通道%s(DI%s) -> %s scope=%s",
                                channel_events,
                                bit + 1,
                                bit,
                                "闭合" if states[bit] else "断开",
                                "BUSINESS" if bit < TD39_ACTION_DI_COUNT else "DIAGNOSTIC",
                            )
                previous_mask = mask

            if (
                previous_mask is not None
                and now - last_heartbeat >= HEARTBEAT_SECONDS
            ):
                logging.info(
                    "HEARTBEAT valid_frames=%s states=[%s]",
                    valid_frames,
                    format_input_states(states_from_mask(previous_mask)),
                )
                last_heartbeat = now

            if (
                previous_mask is not None
                and now - last_state_change >= UNCHANGED_NOTICE_SECONDS
                and now - last_unchanged_notice >= UNCHANGED_NOTICE_SECONDS
            ):
                logging.warning(
                    "INPUTS-UNCHANGED %.1f 秒：通信正常，但 DI0~DI%s 电平完全没有变化。"
                    "TD-39 的干接点需要外部输入配电，不能只短接 ICOM-DI；"
                    "若 ICOM 接 GND，请使用 +VS-按钮-DI；"
                    "若 ICOM 接 +VS，请使用 GND-按钮-DI。"
                    "同时检查常开/常闭触点和端子顺序。",
                    now - last_state_change,
                    TD39_DI_COUNT - 1,
                )
                last_unchanged_notice = now

            if now - last_valid >= NO_RESPONSE_WARNING_SECONDS and now - last_warning >= 3.0:
                logging.warning(
                    "连续 %.1f 秒没有有效响应；请检查供电、COM 口、A/B 接线、"
                    "从站地址和 9600/8N1 参数。",
                    now - last_valid,
                )
                last_warning = now

            time.sleep(0.02)

    logging.info(
        "监听结束: port=%s valid_frames=%s channel_events=%s log=%s",
        port,
        valid_frames,
        channel_events,
        LOG_PATH,
    )
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="TD-39 12 路输入监听工具")
    parser.add_argument("--port", help="指定串口，例如 COM21；省略时自动检测")
    parser.add_argument(
        "--baud",
        type=int,
        default=TD39_BAUDRATE,
        help=f"波特率，默认 {TD39_BAUDRATE}",
    )
    parser.add_argument(
        "--slave",
        type=int,
        default=TD39_DEFAULT_SLAVE,
        help=f"Modbus 从站地址，默认 {TD39_DEFAULT_SLAVE}",
    )
    parser.add_argument(
        "--duration",
        type=float,
        default=0.0,
        help="监听秒数；0 表示一直监听到 Ctrl+C",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    setup_logging()

    logging.info("TD-39 全 12 路输入监听检测（业务重点为前 5 路）")
    logging.info("监听工具版本: %s", TD39_MONITOR_VERSION)
    logging.info("本工具只发送功能码 0x01 的只读查询，不修改设备参数。")

    try:
        query = build_read_inputs(args.slave, count=TD39_DI_COUNT)
    except ValueError as exc:
        logging.error("参数错误: %s", exc)
        return 2

    ports = candidate_ports(args.port)
    if not ports:
        logging.error("Windows 未检测到任何串口。请检查 USB-RS485 转换器和驱动。")
        return 2

    logging.info("候选串口顺序: %s", ", ".join(ports))
    working_port = None
    for port in ports:
        if probe_port(port, args.baud, args.slave, query):
            working_port = port
            break

    if working_port is None:
        logging.error("所有候选串口均未收到有效 TD-39 响应。")
        logging.error("请优先检查：模块 9~30V 供电、RS485 A/B 是否接反、站号是否为 1。")
        logging.error("完整结果已保存到 %s", LOG_PATH)
        return 2

    try:
        return monitor_port(
            working_port,
            args.baud,
            args.slave,
            query,
            max(0.0, args.duration),
        )
    except KeyboardInterrupt:
        logging.info("用户结束监听。结果已保存到 %s", LOG_PATH)
        return 0
    except (serial.SerialException, PermissionError, OSError) as exc:
        logging.error("监听中断: %s", exc)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
