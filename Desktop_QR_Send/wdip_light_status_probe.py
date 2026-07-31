"""WDIP24-15-R 补光灯电源只读状态检查。

运行前必须关闭正式装箱扫码程序和厂家上位机，避免两个程序同时占用
同一个 COM 口。本工具只发送功能码 0x03 的读取请求，不写寄存器。
"""

from __future__ import annotations

import argparse
import sys
from typing import Iterable

from serial.tools import list_ports

from utils.wdip_light_controller import WDIPLightController, build_read_registers


def available_ports() -> list[str]:
    return [item.device for item in list_ports.comports()]


def candidate_ports(explicit_port: str | None, ports: Iterable[str]) -> list[str]:
    ordered: list[str] = []
    for port in ([explicit_port] if explicit_port else []) + list(ports):
        if port and port not in ordered:
            ordered.append(port)
    return ordered


def print_state(port: str, controller: WDIPLightController) -> None:
    state = controller.read_state(port)
    print(f"[成功] WDIP 设备端口: {port}")
    print(f"[只读] 查询帧: {build_read_registers(controller.slave_addr).hex(' ')}")
    print(f"[状态] 实际输出电压: {state.output_voltage_v:.2f} V")
    print(f"[状态] 实际输出电流: {state.output_current_a:.3f} A")
    print(f"[设置] 设定输出电压: {state.set_voltage_v:.2f} V")
    print(f"[设置] 设定输出电流: {state.set_current_a:.3f} A")
    print(f"[设置] 输出控制: {'打开(1)' if state.output_enabled else '关闭(0)'}")
    print(f"[设置] 波特率代码: {state.baudrate_code}")
    print(f"[设置] 串口数据保存: {state.saved}")
    print()

    if not state.output_enabled:
        print("[结论] 输出控制寄存器 0x0005 为 0；设定值即使能读写，灯也不会亮。")
    elif state.set_voltage_v <= 0:
        print("[结论] 输出已打开，但设定电压为 0 V；灯不会亮。")
    elif state.set_current_a <= 0:
        print("[结论] 输出已打开，但设定电流为 0 A；灯不会亮。")
    elif state.output_voltage_v <= 0.01 and state.output_current_a <= 0.001:
        print("[结论] 设置值和输出开关有效，但实际输出接近 0；需检查输入电源、VO+/VO-和负载接线。")
    else:
        print("[结论] WDIP 已有真实电压/电流输出；若灯仍不亮，应核对灯具极性和额定参数。")


def main() -> int:
    parser = argparse.ArgumentParser(description="只读检查 WDIP24-15-R 的 8 个寄存器")
    parser.add_argument("--port", help="优先检查的串口，例如 COM3")
    parser.add_argument("--baudrate", type=int, default=9600)
    parser.add_argument("--slave", type=int, default=1)
    parser.add_argument("--timeout", type=float, default=0.6)
    args = parser.parse_args()

    ports = available_ports()
    candidates = candidate_ports(args.port, ports)
    print(f"[信息] 当前可用串口: {ports or '无'}")
    print("[安全] 本工具只读，不会修改电压、电流、输出开关、地址或保存参数。")
    if not candidates:
        print("[失败] 没有可检查的串口。")
        return 2

    errors: list[str] = []
    for port in candidates:
        controller = WDIPLightController(
            port=port,
            baudrate=args.baudrate,
            slave_addr=args.slave,
            timeout=args.timeout,
        )
        try:
            print_state(port, controller)
            return 0
        except Exception as exc:
            errors.append(f"{port}: {exc}")

    # 厂家协议允许以下6档波特率，现场设备地址也可能被旧上位机修改过。
    # 这里只发送0x03读取命令，扫描不会改写任何设备数据。
    scan_port = args.port or (ports[0] if ports else None)
    if scan_port:
        print(f"[扫描] 默认参数未找到设备，开始只读扫描 {scan_port} 的波特率和站号1~10...")
        for baudrate in (9600, 4800, 19200, 38400, 57600, 115200):
            for slave_addr in range(1, 11):
                if baudrate == args.baudrate and slave_addr == args.slave:
                    continue
                controller = WDIPLightController(
                    port=scan_port,
                    baudrate=baudrate,
                    slave_addr=slave_addr,
                    timeout=min(args.timeout, 0.18),
                )
                try:
                    state = controller.read_state()
                    print(f"[扫描成功] 波特率={baudrate}，站号={slave_addr}")
                    print_state(scan_port, controller)
                    return 0
                except Exception:
                    pass

    print("[失败] 所有候选串口都没有收到有效 WDIP 响应：")
    for error in errors:
        print(f"  - {error}")
    print("[提示] 若显示‘拒绝访问/PermissionError’，说明主程序或厂家上位机仍占用该串口。")
    print("[提示] 若只有 CRC/长度错误，检查 A/B 是否接反、站号是否为 1、波特率是否为 9600。")
    return 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("\n[信息] 用户终止检查。")
        raise SystemExit(130)
