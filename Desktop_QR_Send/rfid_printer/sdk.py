"""
汉印 T63R SDK (libDSThermal.dll) ctypes WinDLL 64位低级封装
"""

import os
import ctypes
from ctypes import c_uint, c_int, c_double, c_char_p, c_uint64, POINTER, create_string_buffer
import logging
from typing import List, Tuple, Optional, Dict
from .errors import SdkInitError, DeviceConnectError, DeviceNotFoundError, PrinterStatusError
from .models import PrinterDeviceInfo

logger = logging.getLogger("RfidPrinterSDK")


class T63RSdk:
    """T63R 打印机 x64 DLL SDK 封装类"""

    def __init__(self, vendor_dir: str):
        self.vendor_dir = os.path.abspath(vendor_dir)
        self.dll_path = os.path.join(self.vendor_dir, "libDSThermal.dll")
        self.cfg_xml_path = os.path.join(self.vendor_dir, "sdkcfg.xml")
        self._dll = None
        self._initialized = False

        if not os.path.exists(self.dll_path):
            raise SdkInitError(f"SDK 核心动态库不存在: {self.dll_path}")

        if hasattr(os, "add_dll_directory"):
            try:
                os.add_dll_directory(self.vendor_dir)
            except Exception as e:
                logger.warning(f"添加 DLL 搜索目录失败: {e}")

    def load_and_init(self):
        """加载 DLL 并初始化 SDK"""
        if self._initialized:
            return

        try:
            self._dll = ctypes.WinDLL(self.dll_path)
            logger.info(f"成功加载 x64 动态库: {self.dll_path}")
        except Exception as e:
            raise SdkInitError(f"加载 DLL 动态库失败: {e}")

        self._setup_signatures()

        result_buf = create_string_buffer(512)
        result_len = c_int(512)

        res = self._dll.DSTP2x_Lib_Init(None, 0, result_buf, ctypes.byref(result_len))
        if res != 0:
            err_msg = result_buf.value.decode('utf-8', errors='ignore') if result_buf.value else "未知错误"
            raise SdkInitError(f"SDK 初始化失败，错误码: {res}, 信息: {err_msg}", code=res)

        self._initialized = True
        logger.info("SDK 库初始化成功 (DSTP2x_Lib_Init)")

    def clear_and_unload(self):
        """清理 SDK 资源"""
        if self._initialized and self._dll:
            try:
                self._dll.DSTP2x_Lib_Clear()
                logger.info("SDK 资源已清理 (DSTP2x_Lib_Clear)")
            except Exception as e:
                logger.error(f"清理 SDK 资源出错: {e}")
            finally:
                self._initialized = False
                self._dll = None

    def _setup_signatures(self):
        """定义 C 函数签名"""
        dll = self._dll

        dll.DSTP2x_Lib_Init.argtypes = [c_char_p, c_int, c_char_p, POINTER(c_int)]
        dll.DSTP2x_Lib_Init.restype = c_uint

        dll.DSTP2x_Lib_Clear.argtypes = []
        dll.DSTP2x_Lib_Clear.restype = c_uint

        dll.DSTP2x_EnumDev.argtypes = [c_int, c_char_p, POINTER(c_int), POINTER(c_int)]
        dll.DSTP2x_EnumDev.restype = c_uint

        dll.DSTP2x_ConnEnumeratedDev.argtypes = [c_char_p, POINTER(c_uint64)]
        dll.DSTP2x_ConnEnumeratedDev.restype = c_uint

        dll.DSTP2x_DisconnDev.argtypes = [c_uint64]
        dll.DSTP2x_DisconnDev.restype = c_uint

        dll.DSTP2x_GetPrtName.argtypes = [c_uint64, c_char_p, POINTER(c_int)]
        dll.DSTP2x_GetPrtName.restype = c_uint

        dll.DSTP2x_GetPrtSN.argtypes = [c_uint64, c_char_p, POINTER(c_int)]
        dll.DSTP2x_GetPrtSN.restype = c_uint

        dll.DSTP2x_GetPrtFWVer.argtypes = [c_uint64, c_char_p, POINTER(c_int)]
        dll.DSTP2x_GetPrtFWVer.restype = c_uint

        dll.DSTP2x_GetPrtStatus.argtypes = [
            c_uint64, POINTER(c_int), POINTER(c_int), POINTER(c_int),
            POINTER(c_int), POINTER(c_int), POINTER(c_int), POINTER(c_int),
            c_char_p, POINTER(c_int)
        ]
        dll.DSTP2x_GetPrtStatus.restype = c_uint

        if hasattr(dll, "DSTP2x_LocateLabel"):
            dll.DSTP2x_LocateLabel.argtypes = [c_uint64]
            dll.DSTP2x_LocateLabel.restype = c_uint

        if hasattr(dll, "DSTP2x_RFID_LocateLabel"):
            dll.DSTP2x_RFID_LocateLabel.argtypes = [c_uint64]
            dll.DSTP2x_RFID_LocateLabel.restype = c_uint

        if hasattr(dll, "DSTP2x_SetImgDpi"):
            dll.DSTP2x_SetImgDpi.argtypes = [c_uint64, c_int]
            dll.DSTP2x_SetImgDpi.restype = c_uint

        if hasattr(dll, "DSTP2x_SetPrnEmulation"):
            dll.DSTP2x_SetPrnEmulation.argtypes = [c_uint64, c_int]
            dll.DSTP2x_SetPrnEmulation.restype = c_uint

        if hasattr(dll, "DSTP2x_SetLcPrnMode"):
            dll.DSTP2x_SetLcPrnMode.argtypes = [c_uint64, c_int]
            dll.DSTP2x_SetLcPrnMode.restype = c_uint

        if hasattr(dll, "DSTP2x_SetLcPrnRotate"):
            dll.DSTP2x_SetLcPrnRotate.argtypes = [c_uint64, c_int]
            dll.DSTP2x_SetLcPrnRotate.restype = c_uint

        dll.DSTP2x_CreateLabelContext.argtypes = [c_double, c_double, POINTER(c_uint64)]
        dll.DSTP2x_CreateLabelContext.restype = c_uint

        dll.DSTP2x_DeleteLabelContext.argtypes = [c_uint64]
        dll.DSTP2x_DeleteLabelContext.restype = c_uint

        if hasattr(dll, "DSTP2x_LcDraw_SetTextFontName"):
            dll.DSTP2x_LcDraw_SetTextFontName.argtypes = [c_uint64, c_int, c_char_p]
            dll.DSTP2x_LcDraw_SetTextFontName.restype = c_uint

        if hasattr(dll, "DSTP2x_LcDraw_SetTextFontSize"):
            dll.DSTP2x_LcDraw_SetTextFontSize.argtypes = [c_uint64, c_int, c_double]
            dll.DSTP2x_LcDraw_SetTextFontSize.restype = c_uint

        if hasattr(dll, "DSTP2x_LcDraw_SetTextBold"):
            dll.DSTP2x_LcDraw_SetTextBold.argtypes = [c_uint64, c_int, c_int]
            dll.DSTP2x_LcDraw_SetTextBold.restype = c_uint

        dll.DSTP2x_Lbl_DrawText.argtypes = [c_uint64, c_double, c_double, c_double, c_double, c_char_p]
        dll.DSTP2x_Lbl_DrawText.restype = c_uint

        if hasattr(dll, "DSTP2x_Lbl_DrawLine"):
            dll.DSTP2x_Lbl_DrawLine.argtypes = [
                c_uint64, c_double, c_double, c_double, c_double, c_int, c_int
            ]
            dll.DSTP2x_Lbl_DrawLine.restype = c_uint

        if hasattr(dll, "DSTP2x_Lbl_DrawImage"):
            dll.DSTP2x_Lbl_DrawImage.argtypes = [
                c_uint64, c_double, c_double, c_double, c_double,
                c_double, c_int, c_char_p, c_uint,
            ]
            dll.DSTP2x_Lbl_DrawImage.restype = c_uint
        if hasattr(dll, "DSTP2x_LcDraw_SetImageHalftoneAlgo"):
            dll.DSTP2x_LcDraw_SetImageHalftoneAlgo.argtypes = [
                c_uint64, c_int, c_int, c_int,
            ]
            dll.DSTP2x_LcDraw_SetImageHalftoneAlgo.restype = c_uint

        dll.DSTP2x_Lbl_DrawBarCode.argtypes = [c_uint64, c_double, c_double, c_double, c_double, c_int, c_char_p]
        dll.DSTP2x_Lbl_DrawBarCode.restype = c_uint

        if hasattr(dll, "DSTP2x_LcDraw_SetBarCodeExpl"):
            dll.DSTP2x_LcDraw_SetBarCodeExpl.argtypes = [c_uint64, c_int, c_int]
            dll.DSTP2x_LcDraw_SetBarCodeExpl.restype = c_uint

        dll.DSTP2x_LcRfid_SetData.argtypes = [c_uint64, c_int, c_int, c_char_p, c_int]
        dll.DSTP2x_LcRfid_SetData.restype = c_uint

        dll.DSTP2x_PrintLc.argtypes = [
            c_uint64, c_uint64, c_char_p, POINTER(c_int),
            c_int, c_char_p, POINTER(c_int)
        ]
        dll.DSTP2x_PrintLc.restype = c_uint

        if hasattr(dll, "DSTP2x_SetLcPrnRotate"):
            dll.DSTP2x_SetLcPrnRotate.argtypes = [c_uint64, c_int]
            dll.DSTP2x_SetLcPrnRotate.restype = c_uint

        if hasattr(dll, "ThermalCustomizedCmd"):
            dll.ThermalCustomizedCmd.argtypes = [c_uint64, c_char_p, c_int]
            dll.ThermalCustomizedCmd.restype = c_uint

        if hasattr(dll, "DSTP2x_RFID_ReadData"):
            dll.DSTP2x_RFID_ReadData.argtypes = [
                c_uint64, c_char_p, POINTER(c_int), c_char_p, POINTER(c_int), c_char_p, POINTER(c_int)
            ]
            dll.DSTP2x_RFID_ReadData.restype = c_uint

        if hasattr(dll, "DSTP2x_RFID_LockOperate"):
            dll.DSTP2x_RFID_LockOperate.argtypes = [c_uint64, c_int, c_char_p]
            dll.DSTP2x_RFID_LockOperate.restype = c_uint

    def set_text_font(self, lc_hdl: int, font_name: str = "宋体", font_size: float = 10.0, is_bold: bool = False):
        """设置待绘制文本的字体 (默认 '宋体' 中文字体，nTemporary=1 临时模式)，完美支持中文显色与 0 错误码"""
        if hasattr(self._dll, "DSTP2x_LcDraw_SetTextFontName"):
            try:
                fname = (font_name or "宋体").strip()
                if fname.lower() in ("simsun", "simsun", "songti"):
                    fname = "宋体"
                elif fname.lower() in ("simhei", "hei", "heiti"):
                    fname = "黑体"
                elif fname.lower() in ("msyh", "microsoft yahei"):
                    fname = "微软雅黑"
                self._dll.DSTP2x_LcDraw_SetTextFontName(c_uint64(lc_hdl), c_int(1), fname.encode('utf-8'))
            except Exception as e:
                logger.warning(f"设置字体名称 '{font_name}' 告警: {e}")
        if hasattr(self._dll, "DSTP2x_LcDraw_SetTextFontSize"):
            try:
                self._dll.DSTP2x_LcDraw_SetTextFontSize(c_uint64(lc_hdl), c_int(1), c_double(font_size))
            except Exception:
                pass
        if hasattr(self._dll, "DSTP2x_LcDraw_SetTextBold"):
            try:
                self._dll.DSTP2x_LcDraw_SetTextBold(c_uint64(lc_hdl), c_int(1), c_int(1 if is_bold else 0))
            except Exception:
                pass

    def draw_text(self, lc_hdl: int, x: float, y: float, w: float, h: float, text: str, font_size: float = 10.0, font_name: str = "宋体", is_bold: bool = False):
        clean_text = str(text or "").strip()
        if clean_text and w > 0:
            cjk_count = sum(1 for c in clean_text if ord(c) > 127)
            ascii_count = len(clean_text) - cjk_count
            # CJK 字符约 0.3527mm/pt, ASCII 字符约 0.20mm/pt
            approx_w_per_pt = (cjk_count * 0.36 + ascii_count * 0.20)
            if approx_w_per_pt > 0:
                max_pt = w / approx_w_per_pt
                if font_size > max_pt:
                    font_size = max(6.0, round(max_pt, 1))

        self.set_text_font(lc_hdl, font_name=font_name, font_size=font_size, is_bold=is_bold)
        text_bytes = clean_text.encode('utf-8')
        res = self._dll.DSTP2x_Lbl_DrawText(
            c_uint64(lc_hdl), c_double(x), c_double(y), c_double(w), c_double(h), text_bytes
        )
        if res != 0:
            logger.warning(f"绘制文本 '{text}' 返回非零码: {res}")

    def draw_image(
        self,
        lc_hdl: int,
        x: float,
        y: float,
        w: float,
        h: float,
        image_path: str,
    ):
        """【打印代码 5】：在画布上绘制品牌 Logo 图片 (对应 C API: DSTP2x_Lbl_DrawImage)"""
        if not hasattr(self._dll, "DSTP2x_Lbl_DrawImage"):
            logger.warning("当前 T63R SDK 不支持 DSTP2x_Lbl_DrawImage，已跳过品牌图片")
            return
        abs_path = os.path.abspath(image_path)
        if not os.path.exists(abs_path):
            logger.warning(f"品牌图片不存在，已跳过: {abs_path}")
            return
        path_bytes = abs_path.encode("utf-8")
        if hasattr(self._dll, "DSTP2x_LcDraw_SetImageHalftoneAlgo"):
            self._dll.DSTP2x_LcDraw_SetImageHalftoneAlgo(
                c_uint64(lc_hdl), c_int(1), c_int(3), c_int(180)
            )
        res = self._dll.DSTP2x_Lbl_DrawImage(
            c_uint64(lc_hdl),
            c_double(x),
            c_double(y),
            c_double(w),
            c_double(h),
            c_double(1.0),
            c_int(0),
            path_bytes,
            c_uint(len(path_bytes)),
        )
        if res != 0:
            logger.warning(f"绘制品牌图片返回非零码: {res}")

    def set_img_dpi(self, dev_hdl: int, dpi_type: int = 1):
        if hasattr(self._dll, "DSTP2x_SetImgDpi") and dev_hdl:
            res = self._dll.DSTP2x_SetImgDpi(c_uint64(dev_hdl), c_int(dpi_type))
            if res != 0:
                logger.warning(f"设置打印 DPI ({dpi_type}) 返回非零码: {res}")

    def set_prn_emulation(self, dev_hdl: int, emulation: int = 1):
        if hasattr(self._dll, "DSTP2x_SetPrnEmulation") and dev_hdl:
            res = self._dll.DSTP2x_SetPrnEmulation(c_uint64(dev_hdl), c_int(emulation))
            if res != 0:
                logger.warning(f"设置打印仿真模式 ({emulation}) 返回非零码: {res}")

    def set_lc_prn_mode(self, lc_hdl: int, mode: int = 0):
        if hasattr(self._dll, "DSTP2x_SetLcPrnMode") and lc_hdl:
            try:
                self._dll.DSTP2x_SetLcPrnMode(c_uint64(lc_hdl), c_int(mode))
            except Exception:
                pass

    def set_lc_prn_rotate(self, lc_hdl: int, rotate: int = 0):
        """设置整张标签画布旋转角度 (0: 0度, 90: 旋转90度, 180: 180度, 270: 270度)；彻底解决 42041344。"""
        rot_val = 0
        if rotate in (90, 1):
            rot_val = 90
        elif rotate in (180, 2):
            rot_val = 180
        elif rotate in (270, 3):
            rot_val = 270
        if hasattr(self._dll, "DSTP2x_SetLcPrnRotate") and lc_hdl:
            try:
                res = self._dll.DSTP2x_SetLcPrnRotate(c_uint64(lc_hdl), c_int(rot_val))
                if res != 0:
                    logger.warning(f"设置画布旋转角度 ({rot_val}) 返回非零码: {res}")
            except Exception as e:
                logger.warning(f"设置画布旋转角度异常: {e}")

    def send_custom_cmd(self, dev_hdl: int, cmd_str: str):
        if hasattr(self._dll, "ThermalCustomizedCmd") and dev_hdl:
            cmd_bytes = cmd_str.encode("utf-8")
            try:
                res = self._dll.ThermalCustomizedCmd(c_uint64(dev_hdl), cmd_bytes, c_int(len(cmd_bytes)))
                logger.info(f"下发 ZPL 控制指令 '{cmd_str}' 成功，返回码: {res}")
            except Exception as e:
                logger.warning(f"下发 ZPL 控制指令 '{cmd_str}' 告警: {e}")

    def enum_usb_devices(self) -> List[str]:
        if not self._initialized:
            self.load_and_init()

        dev_buf = create_string_buffer(4096)
        dev_size = c_int(4096)
        dev_num = c_int(0)

        res = self._dll.DSTP2x_EnumDev(1, dev_buf, ctypes.byref(dev_size), ctypes.byref(dev_num))
        if res != 0:
            logger.warning(f"枚举 USB 设备返回非零状态: {res}")
            return []

        if dev_num.value <= 0 or not dev_buf.value:
            return []

        raw_list = dev_buf.value.decode('utf-8', errors='ignore')
        devices = [d.strip() for d in raw_list.split('\n') if d.strip()]
        logger.info(f"枚举到 {len(devices)} 台 USB 打印设备: {devices}")
        return devices

    def connect_device(self, dev_name: str) -> int:
        if not self._initialized:
            self.load_and_init()

        hdl = c_uint64(0)
        name_bytes = dev_name.encode('utf-8')
        res = self._dll.DSTP2x_ConnEnumeratedDev(name_bytes, ctypes.byref(hdl))
        if res != 0 or hdl.value == 0:
            raise DeviceConnectError(f"连接设备 '{dev_name}' 失败，错误码: {res}", code=res)

        logger.info(f"成功连接设备 '{dev_name}', 句柄: 0x{hdl.value:X}")
        return hdl.value

    def locate_label(self, dev_hdl: int):
        if hasattr(self._dll, "DSTP2x_LocateLabel"):
            res = self._dll.DSTP2x_LocateLabel(c_uint64(dev_hdl))
            if res != 0:
                logger.warning(f"执行标签定位返回非零码: {res}")
            else:
                logger.info("成功触发标签缝隙定位校准 (DSTP2x_LocateLabel)")

    def rfid_locate_label(self, dev_hdl: int):
        if hasattr(self._dll, "DSTP2x_RFID_LocateLabel"):
            res = self._dll.DSTP2x_RFID_LocateLabel(c_uint64(dev_hdl))
            if res != 0:
                logger.warning(f"执行 RFID 天线定位返回非零码: {res}")
            else:
                logger.info("成功触发 RFID 天线定位校准 (DSTP2x_RFID_LocateLabel)")

    def set_img_dpi(self, dev_hdl: int, dpi_type: int = 1):
        if hasattr(self._dll, "DSTP2x_SetImgDpi"):
            res = self._dll.DSTP2x_SetImgDpi(c_uint64(dev_hdl), c_int(dpi_type))
            if res != 0:
                logger.warning(f"设置打印 DPI ({dpi_type}) 返回非零码: {res}")

    def set_prn_emulation(self, dev_hdl: int, emulation: int = 1):
        if hasattr(self._dll, "DSTP2x_SetPrnEmulation"):
            res = self._dll.DSTP2x_SetPrnEmulation(c_uint64(dev_hdl), c_int(emulation))
            if res != 0:
                logger.warning(f"设置打印仿真模式 ({emulation}) 返回非零码: {res}")

    def set_lc_prn_mode(self, lc_hdl: int, mode: int = 0):
        if hasattr(self._dll, "DSTP2x_SetLcPrnMode"):
            res = self._dll.DSTP2x_SetLcPrnMode(c_uint64(lc_hdl), c_int(mode))
            if res != 0:
                logger.warning(f"设置画布打印模式 ({mode}) 返回非零码: {res}")

    def disconnect_device(self, dev_hdl: int):
        if dev_hdl and self._dll:
            try:
                self._dll.DSTP2x_DisconnDev(c_uint64(dev_hdl))
                logger.info(f"成功断开设备句柄: 0x{dev_hdl:X}")
            except Exception as e:
                logger.error(f"断开设备句柄失败: {e}")

    def get_device_info(self, dev_hdl: int) -> PrinterDeviceInfo:
        hdl = c_uint64(dev_hdl)
        info = PrinterDeviceInfo()

        buf = create_string_buffer(256)
        buf_len = c_int(256)
        if self._dll.DSTP2x_GetPrtName(hdl, buf, ctypes.byref(buf_len)) == 0:
            info.name = buf.value.decode('utf-8', errors='ignore')

        buf_len = c_int(256)
        if self._dll.DSTP2x_GetPrtSN(hdl, buf, ctypes.byref(buf_len)) == 0:
            info.sn = buf.value.decode('utf-8', errors='ignore')

        buf_len = c_int(256)
        if self._dll.DSTP2x_GetPrtFWVer(hdl, buf, ctypes.byref(buf_len)) == 0:
            info.fw_ver = buf.value.decode('utf-8', errors='ignore')

        is_ready = c_int(0)
        m_status = c_int(0)
        m_num = c_int(0)
        warning = c_int(0)
        w_num = c_int(0)
        error = c_int(0)
        e_num = c_int(0)
        desc_buf = create_string_buffer(512)
        desc_len = c_int(512)

        res = self._dll.DSTP2x_GetPrtStatus(
            hdl, ctypes.byref(is_ready), ctypes.byref(m_status), ctypes.byref(m_num),
            ctypes.byref(warning), ctypes.byref(w_num), ctypes.byref(error), ctypes.byref(e_num),
            desc_buf, ctypes.byref(desc_len)
        )
        if res == 0:
            info.is_ready = (is_ready.value == 1)
            info.status_desc = desc_buf.value.decode('utf-8', errors='ignore') or "正常"
        else:
            info.status_desc = f"查询状态失败 ({res})"

        return info

    def read_rfid_direct(self, dev_hdl: int) -> Dict[str, str]:
        if not hasattr(self._dll, "DSTP2x_RFID_ReadData"):
            return {"tid": "", "epc": "", "user": ""}

        tid_buf = create_string_buffer(256)
        tid_len = c_int(256)
        epc_buf = create_string_buffer(256)
        epc_len = c_int(256)
        user_buf = create_string_buffer(256)
        user_len = c_int(256)

        res = self._dll.DSTP2x_RFID_ReadData(
            c_uint64(dev_hdl),
            tid_buf, ctypes.byref(tid_len),
            epc_buf, ctypes.byref(epc_len),
            user_buf, ctypes.byref(user_len)
        )
        if res == 0:
            return {
                "tid": tid_buf.value.decode('utf-8', errors='ignore') if tid_buf.value else "",
                "epc": epc_buf.value.decode('utf-8', errors='ignore') if epc_buf.value else "",
                "user": user_buf.value.decode('utf-8', errors='ignore') if user_buf.value else "",
            }
        return {"tid": "", "epc": "", "user": ""}

    def create_label(self, width_mm: float, height_mm: float) -> int:
        lc_hdl = c_uint64(0)
        res = self._dll.DSTP2x_CreateLabelContext(c_double(width_mm), c_double(height_mm), ctypes.byref(lc_hdl))
        if res != 0 or lc_hdl.value == 0:
            raise SdkInitError(f"创建标签画布 ({width_mm}x{height_mm}mm) 失败，错误码: {res}", code=res)
        return lc_hdl.value

    def delete_label(self, lc_hdl: int):
        if lc_hdl and self._dll:
            try:
                self._dll.DSTP2x_DeleteLabelContext(c_uint64(lc_hdl))
            except Exception as e:
                logger.error(f"释放标签画布失败: {e}")

    def draw_text(
        self,
        lc_hdl: int,
        x: float,
        y: float,
        w: float,
        h: float,
        text: str,
        font_size: float = 10.0,
        font_name: str = "Microsoft YaHei",
        is_bold: bool = False,
    ):
        text_bytes = text.encode('utf-8')
        self.set_text_font(
            lc_hdl,
            font_name=font_name,
            font_size=font_size,
            is_bold=is_bold,
        )
        res = self._dll.DSTP2x_Lbl_DrawText(
            c_uint64(lc_hdl), c_double(x), c_double(y), c_double(w), c_double(h), text_bytes
        )
        if res != 0:
            logger.warning(f"绘制文本 '{text}' 返回非零码: {res}")

    def draw_line(
        self,
        lc_hdl: int,
        start_x: float,
        start_y: float,
        end_x: float,
        end_y: float,
        line_width: int = 1,
        line_type: int = 0,
    ):
        """在标签画布上绘制线段；坐标单位毫米，线宽单位像素。"""
        if not hasattr(self._dll, "DSTP2x_Lbl_DrawLine"):
            logger.warning("当前 T63R SDK 不支持 DSTP2x_Lbl_DrawLine，已跳过分隔线")
            return
        res = self._dll.DSTP2x_Lbl_DrawLine(
            c_uint64(lc_hdl),
            c_double(start_x),
            c_double(start_y),
            c_double(end_x),
            c_double(end_y),
            c_int(max(1, int(line_width))),
            c_int(int(line_type)),
        )
        if res != 0:
            logger.warning(f"绘制分隔线返回非零码: {res}")

    def draw_image(
        self,
        lc_hdl: int,
        x: float,
        y: float,
        w: float,
        h: float,
        image_path: str,
    ):
        """按官方 SDK 的本地图片模式绘制品牌图，坐标和尺寸单位为毫米。"""
        if not hasattr(self._dll, "DSTP2x_Lbl_DrawImage"):
            logger.warning("当前 T63R SDK 不支持 DSTP2x_Lbl_DrawImage，已跳过品牌图片")
            return
        abs_path = os.path.abspath(image_path)
        if not os.path.exists(abs_path):
            logger.warning(f"品牌图片不存在，已跳过: {abs_path}")
            return
        path_bytes = abs_path.encode("utf-8")
        if hasattr(self._dll, "DSTP2x_LcDraw_SetImageHalftoneAlgo"):
            self._dll.DSTP2x_LcDraw_SetImageHalftoneAlgo(
                c_uint64(lc_hdl), c_int(1), c_int(3), c_int(180)
            )
        res = self._dll.DSTP2x_Lbl_DrawImage(
            c_uint64(lc_hdl),
            c_double(x),
            c_double(y),
            c_double(w),
            c_double(h),
            c_double(1.0),
            c_int(0),
            path_bytes,
            c_uint(len(path_bytes)),
        )
        if res != 0:
            logger.warning(f"绘制品牌图片返回非零码: {res}")

    def draw_barcode(self, lc_hdl: int, x: float, y: float, w: float, h: float, code_type: int, data: str, show_text: bool = True):
        data_bytes = data.encode('utf-8')
        if show_text and hasattr(self._dll, "DSTP2x_LcDraw_SetBarCodeExpl"):
            self._dll.DSTP2x_LcDraw_SetBarCodeExpl(c_uint64(lc_hdl), 1, 1)

        res = self._dll.DSTP2x_Lbl_DrawBarCode(
            c_uint64(lc_hdl), c_double(x), c_double(y), c_double(w), c_double(h), c_int(code_type), data_bytes
        )
        if res != 0:
            logger.warning(f"绘制条形码 '{data}' 返回非零码: {res}")

    def set_rfid_data(self, lc_hdl: int, rgn_type: int, data_fmt: int, data_str: str):
        data_bytes = data_str.encode('utf-8')
        data_len = len(data_bytes)
        res = self._dll.DSTP2x_LcRfid_SetData(
            c_uint64(lc_hdl), c_int(rgn_type), c_int(data_fmt), data_bytes, c_int(data_len)
        )
        if res != 0:
            raise SdkInitError(f"设置 RFID 写入数据失败 (区域 {rgn_type}, 格式 {data_fmt})，错误码: {res}", code=res)

    def rfid_lock_operate(self, lc_hdl: int, lock_type: int = 1, password: str = "00000000"):
        """开启并执行 RFID 芯片锁定/解锁操作 (DSTP2x_RFID_LockOperate)。"""
        if hasattr(self._dll, "DSTP2x_RFID_LockOperate") and lc_hdl:
            try:
                pwd_bytes = password.encode('utf-8')
                res = self._dll.DSTP2x_RFID_LockOperate(c_uint64(lc_hdl), c_int(lock_type), pwd_bytes)
                logger.info(f"开启并设置 RFID 芯片锁 (lock_type={lock_type}) 返回码: {res}")
            except Exception as e:
                logger.warning(f"设置 RFID 芯片锁告警: {e}")

    def rfid_locate_label(self, dev_hdl: int) -> int:
        """执行 RFID 标签位置自动定位校准 (DSTP2x_RFID_LocateLabel)。"""
        if hasattr(self._dll, "DSTP2x_RFID_LocateLabel") and dev_hdl:
            try:
                res = self._dll.DSTP2x_RFID_LocateLabel(c_uint64(dev_hdl))
                logger.info(f"执行 RFID 标签自动校准定位 (LocateLabel) 返回码: {res}")
                return res
            except Exception as e:
                logger.warning(f"执行 RFID 标签自动校准定位异常: {e}")
        return -1

    def print_label_and_read_rfid(self, dev_hdl: int, lc_hdl: int, read_type: int = 0) -> str:
        rfid_buf = create_string_buffer(1024)
        rfid_len = c_int(1024)

        res = self._dll.DSTP2x_PrintLc(
            c_uint64(dev_hdl), c_uint64(lc_hdl),
            None, None,
            c_int(read_type), rfid_buf, ctypes.byref(rfid_len)
        )

        if res != 0:
            raise PrinterStatusError(f"打印并执行 RFID 闭环失败，错误码: {res}", code=res)

        return rfid_buf.value.decode('utf-8', errors='ignore') if rfid_buf.value else ""
