"""WDIP24-15-R 独立灯光开关和亮度测试。

本工具不会猜测或改写灯具电流，也不会写保存寄存器。亮度百分比只会在
打开工具时读取到的原设定电压以内调低或恢复，绝不会擅自升高上限。
"""

from __future__ import annotations

import argparse

from utils.wdip_light_controller import WDIPLightController


def voltage_for_percent(minimum_voltage_v: float, maximum_voltage_v: float, percent: int) -> float:
    return minimum_voltage_v + (maximum_voltage_v - minimum_voltage_v) * percent / 100.0


def show_state(
    controller: WDIPLightController,
    minimum_voltage_v: float,
    maximum_voltage_v: float,
) -> None:
    state = controller.read_state()
    percent = int(
        round(
            (state.set_voltage_v - minimum_voltage_v)
            / (maximum_voltage_v - minimum_voltage_v)
            * 100
        )
    )
    print()
    print(f"端口: {controller.port}")
    print(f"输出控制: {'打开(ON)' if state.output_enabled else '关闭(OFF)'}")
    print(f"设定参数: {state.set_voltage_v:.2f} V / {state.set_current_a:.3f} A")
    print(f"实际输出: {state.output_voltage_v:.2f} V / {state.output_current_a:.3f} A")
    print(
        f"调光位置: {max(0, min(100, percent))}%"
        f"（固定范围 {minimum_voltage_v:.2f}~{maximum_voltage_v:.2f} V）"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="WDIP真实灯光独立控制测试")
    parser.add_argument("--port", default="COM3")
    parser.add_argument("--baudrate", type=int, default=9600)
    parser.add_argument("--slave", type=int, default=1)
    parser.add_argument("--timeout", type=float, default=0.6)
    parser.add_argument("--min-voltage", type=float, default=8.0)
    parser.add_argument("--max-voltage", type=float, default=12.0)
    args = parser.parse_args()
    if not 0 <= args.min_voltage < args.max_voltage <= 24:
        parser.error("电压范围必须满足 0≤最低值<最高值≤24V")

    controller = WDIPLightController(
        port=args.port,
        baudrate=args.baudrate,
        slave_addr=args.slave,
        timeout=args.timeout,
    )
    initial = controller.read_state()
    show_state(controller, args.min_voltage, args.max_voltage)

    if initial.set_current_a <= 0:
        print()
        print("当前设定电压或电流为0，软件拒绝打开输出。")
        print("请先按灯具铭牌使用厂家上位机设置真实电压、电流，再重新运行本工具。")
        return 2

    print()
    print("可用命令：")
    print("  on       开启真实灯光输出（需要再次输入 ON 确认）")
    print("  off      关闭真实灯光输出")
    print("  p 50     将电压调到10V；百分比0~100对应8~12V")
    print("  r        重新读取真实状态")
    print("  q        退出（不自动改变当前输出状态）")

    while True:
        command = input("\nWDIP> ").strip()
        lowered = command.lower()
        try:
            if lowered == "q":
                return 0
            if lowered == "r":
                show_state(controller, args.min_voltage, args.max_voltage)
                continue
            if lowered == "off":
                controller.set_output_enabled(False)
                print("已关闭灯光输出，并已回读确认。")
                show_state(controller, args.min_voltage, args.max_voltage)
                continue
            if lowered == "on":
                current = controller.read_state()
                print(
                    f"即将按设备已有设定 {current.set_voltage_v:.2f}V / "
                    f"{current.set_current_a:.3f}A 开启真实输出。"
                )
                print("请确认参数与灯具铭牌一致，且WDIP最大输出功率为15W。")
                if input("确认请输入大写 ON：").strip() != "ON":
                    print("已取消，没有写入输出开启命令。")
                    continue
                target_voltage = max(
                    args.min_voltage,
                    min(args.max_voltage, current.set_voltage_v),
                )
                if abs(target_voltage - current.set_voltage_v) > 0.011:
                    controller.set_voltage(target_voltage)
                controller.set_output_enabled(True)
                print("已开启灯光输出，并已回读确认。")
                show_state(controller, args.min_voltage, args.max_voltage)
                continue
            if lowered.startswith("p "):
                percent = int(lowered.split(maxsplit=1)[1])
                if not 0 <= percent <= 100:
                    raise ValueError("百分比必须在0~100之间")
                current = controller.read_state()
                if not current.output_enabled:
                    raise RuntimeError("灯光输出处于关闭状态，请先执行 on")
                voltage = voltage_for_percent(
                    args.min_voltage,
                    args.max_voltage,
                    percent,
                )
                controller.set_voltage(voltage)
                print(f"已将亮度设为 {percent}%（{voltage:.2f}V），并已回读确认。")
                show_state(controller, args.min_voltage, args.max_voltage)
                continue
            print("命令无效，请输入 on、off、p 0~100、r 或 q。")
        except Exception as exc:
            print(f"操作失败：{exc}")


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("\n已退出；没有自动改变当前灯光输出状态。")
        raise SystemExit(130)
