"""T63R 打印机/RFID 只读状态检查：不打印、不走纸、不写 RFID。"""

import os
import sys
import json
import traceback


ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from rfid_printer.sdk import T63RSdk


def main():
    config_path = os.path.join(ROOT_DIR, "config", "settings.json")
    with open(config_path, "r", encoding="utf-8") as config_file:
        config = json.load(config_file)
    vendor_dir = str(config.get("vendor_dir", "vendor/t63r_x64"))
    if not os.path.isabs(vendor_dir):
        vendor_dir = os.path.join(ROOT_DIR, vendor_dir)
    sdk = T63RSdk(vendor_dir)
    dev_hdl = 0
    try:
        print("安全说明：本工具只读，不打印、不走纸、不写RFID、不连接数据库。")
        sdk.load_and_init()
        devices = sdk.enum_usb_devices()
        print(f"枚举到的USB打印机: {devices}")
        if not devices:
            print("检查失败：没有枚举到T63R，请检查电源、USB线和其他占用打印机的程序。")
            return 2

        dev_hdl = sdk.connect_device(devices[0])
        info = sdk.get_device_info(dev_hdl)
        print(f"名称: {info.name or '<空>'}")
        print(f"序列号: {info.sn or '<空>'}")
        print(f"固件: {info.fw_ver or '<空>'}")
        status = sdk.get_device_status_detail(dev_hdl)
        print("设备状态: " + sdk.format_device_status(status))

        chip = sdk.read_rfid_direct(dev_hdl)
        code = int(chip.get("result_code", -1))
        if code == 0:
            print("当前RFID标签只读成功。")
            print(f"TID: {chip.get('tid') or '<空>'}")
            print(f"EPC: {chip.get('epc') or '<空>'}")
            print(f"USER: {chip.get('user') or '<空>'}")
        else:
            print(f"当前RFID标签只读失败: {code} (0x{code & 0xFFFFFFFF:08X})")
            print("这通常表示RFID标签未在天线位置、使用了普通纸，或尚未做RFID标签定位校准。")
        return 0
    except Exception as exc:
        print(f"检查异常: {exc}")
        traceback.print_exc()
        return 1
    finally:
        if dev_hdl:
            sdk.disconnect_device(dev_hdl)
        sdk.clear_and_unload()


if __name__ == "__main__":
    raise SystemExit(main())
