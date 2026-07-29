"""
T63R RFID 打印机测试与闭环验证脚本 (运行在 Desktop_QR_Send 工程目录下)
"""

import sys
import os
import time
import argparse
import logging

try:
    import runtime_bootstrap
    runtime_bootstrap.configure_runtime()
except Exception as e:
    print(f"[提示] runtime_bootstrap 加载告警: {e}")

from rfid_printer import RfidPrintService, validate_box_code, LabelPrintData
from utils.printUtils import print_rfid_box_label

os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler("logs/test_rfid_printer.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger("TestRfidPrinter")

def generate_timestamp_13():
    """获取毫秒级时间戳并截取前 13 位纯数字"""
    ts = str(int(time.time() * 1000))
    return ts[:13] if len(ts) >= 13 else ts.zfill(13)

MOCK_BATCH = [
    LabelPrintData(
        box_code=generate_timestamp_13(),
        brand="高原安",
        product_name="高原安藏药红景天胶囊",
        spec="0.3g*60粒/瓶",
        box_spec="0.3g*100瓶/箱",
        shelf_life="24个月",
        produce_date="2026/07/28",
        storage="密封干燥处",
        manufacturer="西藏高原安药业有限公司"
    )
]


def main():
    parser = argparse.ArgumentParser(description="Desktop_QR_Send T63R RFID 打印机测试验证工具")
    parser.add_argument("--probe", action="store_true", help="探测并测试 USB 打印机连接")
    parser.add_argument("--calibrate", action="store_true", help="触发自动测纸与 RFID 天线定位校准")
    parser.add_argument("--code", type=str, default="", help="13位箱码 (默认使用13位时间戳截取)")
    parser.add_argument("--batch3", action="store_true", help="连续批量打印标签测试")
    parser.add_argument("--config", type=str, default="config/settings.json", help="配置文件路径")
    args = parser.parse_args()

    print("==================================================")
    print("  Desktop_QR_Send T63R RFID 打印写卡闭环验证工具")
    print("==================================================")

    service = RfidPrintService(config_path=args.config)

    try:
        if args.probe:
            print("\n[测试 1] 正在枚举已连接的 USB 打印机...")
            devices = service.list_usb_printers()
            print(f"  - 找到设备数量: {len(devices)}")
            if devices:
                print(f"  - 连接第一台设备: {devices[0]}")
                info = service.connect(devices[0])
                print(f"   [OK] 连接成功！名称: {info.name} | SN: {info.sn} | 固件: {info.fw_ver} | 状态: {info.status_desc}")
            else:
                print("   [FAIL] 未检测到通电的 USB 打印机，请核对 USB 线缆与电源开关。")
            return

        if args.calibrate:
            print("\n[测试 2] 正在下发自动测纸与 RFID 天线校准定位...")
            devices = service.list_usb_printers()
            if not devices:
                print("   [FAIL] 未找到 USB 打印机！")
                return
            service.connect(devices[0])
            service.calibrate()
            print("   [OK] 定位指令下发成功！")
            return

        if args.batch3:
            print("\n[测试 3] 正在执行连续生产箱标签流水线打印写卡...")
            devices = service.list_usb_printers()
            if not devices:
                print("   [FAIL] 未找到 USB 打印机！")
                return
            service.connect(devices[0])
            results = service.batch_print_write_verify(MOCK_BATCH, allow_reprint_same_code=True)
            print("\n================ 批量测试结果汇总 ================")
            for idx, res in enumerate(results, 1):
                status_str = "[PASS] 一致" if res.success else "[FAIL] 失败/拦截"
                print(f"  第 {idx} 张: 箱码={res.box_code} | 状态={status_str} | TID={res.read_tid or 'N/A'} | EPC={res.read_epc or 'N/A'} | 耗时={res.elapsed_ms:.1f}ms")
            print("==================================================")
            return

        # 单张测试 (默认自动使用 13 位毫秒时间戳截取)
        box_code_input = args.code or generate_timestamp_13()
        clean_code = validate_box_code(box_code_input)

        print(f"\n[测试 4] 即将对 13 位时间戳箱码 '{clean_code}' 执行单张“高原安”标签打印、EPC 写入与 TID 比对...")
        res = print_rfid_box_label(clean_code, allow_reprint=True)

        print("\n---------------- 单张测试结果 ----------------")
        print(f"  通过状态  : {'[PASS] 一致' if res.success else '[FAIL] 拦截/失败'}")
        print(f"  测试箱码  : {res.box_code}")
        print(f"  芯片 TID  : {res.read_tid or 'N/A'}")
        print(f"  EPC Hex  : {res.read_epc or 'N/A'}")
        print(f"  EPC ASCII: {res.read_ascii or 'N/A'}")
        print(f"  执行耗时  : {res.elapsed_ms:.1f} ms")
        print(f"  结果说明  : {res.error_message}")
        print("----------------------------------------------")
        print(f"详细历史记录已保存至: {service.csv_path}")

    except Exception as e:
        logger.error(f"运行发生异常: {e}", exc_info=True)
        print(f"\n[FAIL] 程序异常: {e}")
    finally:
        service.close()


if __name__ == "__main__":
    main()
