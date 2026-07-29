"""
T63R 打印机 DPI 与仿真语言 4 模式组合攻坚排查脚本
"""

import sys
import os
import ctypes
from ctypes import create_string_buffer, c_int, c_double, c_uint64, byref

def run_combo(dpi_val, emulation_val, mode_name):
    print(f"\n---> 开始组合排查: {mode_name} (DPI={dpi_val}, 仿真={emulation_val})")

    vendor_dir = os.path.abspath("vendor/t63r_x64")
    dll_path = os.path.join(vendor_dir, "libDSThermal.dll")
    if hasattr(os, "add_dll_directory"):
        os.add_dll_directory(vendor_dir)
    dll = ctypes.WinDLL(dll_path)

    buf = create_string_buffer(512)
    blen = c_int(512)
    dll.DSTP2x_Lib_Init(None, 0, buf, byref(blen))

    dev_buf = create_string_buffer(4096)
    dev_size = c_int(4096)
    dev_num = c_int(0)
    dll.DSTP2x_EnumDev(1, dev_buf, byref(dev_size), byref(dev_num))
    devs = [d.strip() for d in dev_buf.value.decode('utf-8', errors='ignore').split('\n') if d.strip()]
    if not devs:
        print("     [FAIL] 未枚举到 USB 打印机")
        dll.DSTP2x_Lib_Clear()
        return -1
    target_dev = devs[0]

    dev_hdl = c_uint64(0)
    r_conn = dll.DSTP2x_ConnEnumeratedDev(target_dev.encode('utf-8'), byref(dev_hdl))
    if r_conn != 0 or dev_hdl.value == 0:
        print("     [FAIL] 设备连接失败")
        dll.DSTP2x_Lib_Clear()
        return -1

    dll.DSTP2x_SetImgDpi(dev_hdl, dpi_val)
    dll.DSTP2x_SetPrnEmulation(dev_hdl, emulation_val)

    lc = c_uint64(0)
    dll.DSTP2x_CreateLabelContext(c_double(100.0), c_double(80.0), byref(lc))
    dll.DSTP2x_SetLcPrnMode(lc, 0)
    dll.DSTP2x_LcDraw_SetTextFontName(lc, 0, "Arial".encode('utf-8'))
    dll.DSTP2x_LcDraw_SetTextFontSize(lc, 0, c_double(10.0))
    dll.DSTP2x_Lbl_DrawText(lc, c_double(10.0), c_double(10.0), c_double(80.0), c_double(10.0), "高原安测试页".encode('utf-8'))
    dll.DSTP2x_Lbl_DrawBarCode(lc, c_double(10.0), c_double(25.0), c_double(80.0), c_double(20.0), 20, "0123456789025".encode('utf-8'))

    ret = dll.DSTP2x_PrintLc(dev_hdl, lc, None, None, 0, None, None)
    print(f"     [打纸结果] 返回码: {ret} ({'PASS 成功吐纸!' if ret == 0 else 'FAIL'})")

    dll.DSTP2x_DeleteLabelContext(lc)
    dll.DSTP2x_DisconnDev(dev_hdl)
    dll.DSTP2x_Lib_Clear()
    return ret

def main():
    print("==================================================")
    print("  T63R 打印机 4 种 DPI/仿真模式组合排查工具")
    print("==================================================")

    run_combo(1, 1, "组合 1: 203 DPI + ZPL 仿真")
    run_combo(2, 1, "组合 2: 300 DPI + ZPL 仿真")
    run_combo(1, 2, "组合 3: 203 DPI + TSPL 仿真")
    run_combo(2, 2, "组合 4: 300 DPI + TSPL 仿真")

if __name__ == "__main__":
    main()
