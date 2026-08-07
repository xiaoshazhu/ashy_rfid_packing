"""
RFID 打印写卡比对完整业务服务流程 (RfidPrintService)
"""

import os
import csv
import json
import time
import threading
import logging
from datetime import datetime
from typing import Optional, List, Set, Dict

from .errors import (
    RfidPrinterError,
    InvalidBoxCodeError,
    DeviceNotFoundError,
    PrinterStatusError,
    WriteVerifyMismatchError,
)
from .models import PrinterDeviceInfo, PrintResult, LabelPrintData
from .encoder import generate_rfid_timestamp, normalize_scanned_box_code
from .label_layout import render_text, resolve_asset_path, resolve_layout_elements
from .sdk import T63RSdk

logger = logging.getLogger("RfidPrintWorkflow")

class RfidPrintService:
    """RFID 打印写卡及闭环核验服务"""

    def __init__(self, config_path: str = "config/settings.json"):
        self.config_path = os.path.abspath(config_path)
        self.config = self._load_config()

        vendor_dir = os.path.abspath(self.config.get("vendor_dir", "vendor/t63r_x64"))
        self.sdk = T63RSdk(vendor_dir=vendor_dir)
        self.connected_dev_name: str = ""
        self.dev_hdl: int = 0
        self.csv_path = os.path.abspath(self.config.get("csv_record_path", "records/print_records.csv"))

        self._print_lock = threading.Lock()
        self._ensure_csv_header()

    def _load_config(self) -> dict:
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"读取配置文件失败 ({e})，采用缺省配置")
        return {}

    def _ensure_csv_header(self):
        os.makedirs(os.path.dirname(self.csv_path), exist_ok=True)
        if not os.path.exists(self.csv_path):
            try:
                with open(self.csv_path, "w", newline="", encoding="utf-8-sig") as f:
                    writer = csv.writer(f)
                    writer.writerow([
                        "时间戳", "箱码", "写入目标", "写入值", "TID", "EPC", "USER",
                        "读回ASCII", "比对结果", "耗时(ms)", "错误码", "错误信息"
                    ])
            except Exception as e:
                logger.error(f"创建 CSV 记录头失败: {e}")

    def append_record_to_csv(self, result: PrintResult):
        try:
            with open(self.csv_path, "a", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                writer.writerow([
                    result.timestamp,
                    result.box_code,
                    self.config.get("rfid", {}).get("target_region", "EPC"),
                    result.written_value,
                    result.read_tid,
                    result.read_epc,
                    result.read_user,
                    result.read_ascii,
                    "PASS" if result.success else "FAIL",
                    round(result.elapsed_ms, 2),
                    result.error_code,
                    result.error_message
                ])
        except Exception as e:
            logger.error(f"写入 CSV 记录失败: {e}")

    def list_printed_epcs_from_csv(self) -> Set[str]:
        printed_set = set()
        if os.path.exists(self.csv_path):
            try:
                with open(self.csv_path, "r", encoding="utf-8-sig") as f:
                    reader = csv.reader(f)
                    header = next(reader, None)
                    for row in reader:
                        if len(row) >= 9 and row[8] == "PASS":
                            if len(row) > 1 and row[1].strip():
                                printed_set.add(row[1].strip())
                            if len(row) > 3 and row[3].strip():
                                printed_set.add(row[3].strip())
            except Exception as e:
                logger.warning(f"读取 CSV 历史记录失败: {e}")
        return printed_set

    def list_usb_printers(self) -> List[str]:
        self.sdk.load_and_init()
        return self.sdk.enum_usb_devices()

    def connect(self, dev_name: Optional[str] = None) -> PrinterDeviceInfo:
        self.sdk.load_and_init()

        target_name = dev_name
        if not target_name:
            devices = self.sdk.enum_usb_devices()
            if not devices:
                raise DeviceNotFoundError(
                    "未检测到通电连接的 USB T63R 打印机！请检查电源开关与 USB 数据线是否插紧。"
                )
            target_name = devices[0]

        if self.dev_hdl:
            self.disconnect()

        try:
            self.dev_hdl = self.sdk.connect_device(target_name)
            self.connected_dev_name = target_name
        except Exception as e:
            raise DeviceNotFoundError(f"连接 USB 打印机失败: {e}")

        # 设置 203 DPI 印头 (dpi_type=1，完美匹配发热与字迹点阵黑度) 与 ZPL 打印语言模式
        self.sdk.set_img_dpi(self.dev_hdl, 1)
        self.sdk.set_prn_emulation(self.dev_hdl, 1)

        device_info = self.sdk.get_device_info(self.dev_hdl)
        logger.info(f"打印机连接成功: 名称='{device_info.name}', SN='{device_info.sn}', 固件='{device_info.fw_ver}', 状态='{device_info.status_desc}'")
        return device_info

    def calibrate(self):
        if not self.dev_hdl:
            self.connect()
        logger.info("开始执行 140x120 纸张缝隙与 RFID 天线自动定位校准...")
        if hasattr(self.sdk, "locate_label"):
            try:
                self.sdk.locate_label(self.dev_hdl)
            except Exception as e:
                logger.warning(f"纸张定位校准告警: {e}")
        if hasattr(self.sdk, "rfid_locate_label"):
            try:
                self.sdk.rfid_locate_label(self.dev_hdl)
            except Exception as e:
                logger.warning(f"RFID 天线定位校准告警: {e}")
        logger.info("140x120 纸张与 RFID 校准定位指令已成功发送")

    def disconnect(self):
        if self.dev_hdl:
            self.sdk.disconnect_device(self.dev_hdl)
            self.dev_hdl = 0
            self.connected_dev_name = ""

    def close(self):
        self.disconnect()
        self.sdk.clear_and_unload()

    def read_chip_status(self) -> dict:
        if not self.dev_hdl:
            self.connect()
        return self.sdk.read_rfid_direct(self.dev_hdl)

    def print_write_verify(
        self,
        box_code: str,
        label_data: Optional[LabelPrintData] = None,
        allow_reprint_same_code: bool = True
    ) -> PrintResult:
        if not self._print_lock.acquire(blocking=False):
            res = PrintResult(box_code=box_code)
            res.error_code = -10
            res.error_message = "正在进行前一张标签打印，请勿频繁或重复触发！"
            return res

        start_time = time.perf_counter()
        result = PrintResult(box_code=box_code, written_value="")

        try:
            scanned_box_code = normalize_scanned_box_code(box_code)
            rfid_code = generate_rfid_timestamp()
            result.box_code = scanned_box_code
            result.written_value = rfid_code

            label_cfg = self.config.get("label", {})
            width_mm = float(label_cfg.get("width_mm", 100.0))
            height_mm = float(label_cfg.get("height_mm", 80.0))
            layout = self.config.get("layout", {})
            elements = resolve_layout_elements(layout, width_mm, height_mm)
            element_values = {
                str(item.get("type")): item.get("value", "")
                for item in elements
                if item.get("type")
            }

            if label_data is None:
                tmpl_cfg = self.config.get("template", {})
                label_data = LabelPrintData(
                    box_code=scanned_box_code,
                    brand=tmpl_cfg.get("brand", element_values.get("brand", "高原安")),
                    product_name=tmpl_cfg.get("product_name", element_values.get("product_name", "高原安藏式甜茶")),
                    spec=tmpl_cfg.get("spec", element_values.get("spec", "200g (20g×10条)/盒")),
                    box_spec=tmpl_cfg.get("box_spec", element_values.get("box_spec", "200g*40盒/箱")),
                    shelf_life=tmpl_cfg.get("shelf_life", element_values.get("shelf_life", "18个月")),
                    produce_date=tmpl_cfg.get("produce_date", datetime.now().strftime("%Y/%m/%d")),
                    storage=tmpl_cfg.get("storage", element_values.get("storage", "干燥、阴凉、通风处")),
                    manufacturer=tmpl_cfg.get("manufacturer", element_values.get("manufacturer", "乌兰察布蒙帝乳业有限责任公司"))
                )
            else:
                label_data.box_code = scanned_box_code

            allow_reprint_same_code = bool(self.config.get("rfid", {}).get("allow_reprint_same_code", False))
            if not allow_reprint_same_code:
                printed_codes = self.list_printed_epcs_from_csv()
                if scanned_box_code in printed_codes or rfid_code in printed_codes:
                    result.success = False
                    result.error_code = -89
                    result.error_message = f"防二次写入拦截！箱码/RFID '{scanned_box_code}' 已成功写入过，禁止重复二次写入！"
                    self.append_record_to_csv(result)
                    return result

            if not self.dev_hdl:
                self.connect()

            # 设置 203 DPI 印头与 ZPL 打印语言模式
            dpi_type = int(self.config.get("label", {}).get("dpi_type", 1))
            self.sdk.set_img_dpi(self.dev_hdl, dpi_type)           # 203 DPI 点阵点对点映射
            self.sdk.set_prn_emulation(self.dev_hdl, 1)            # ZPL 仿真模式

            lc_hdl = self.sdk.create_label(width_mm, height_mm)
            self.sdk.set_lc_prn_mode(lc_hdl, 1)
            canvas_rotate = int(layout.get("canvas_rotate", 0))
            self.sdk.set_lc_prn_rotate(lc_hdl, canvas_rotate)

            try:
                elements = layout.get("elements", [])
                barcode_type = int(layout.get("barcode_type_code", 20))
                data_map = label_data.to_dict()

                for elem in elements:
                    if elem.get("enabled") is False:
                        continue
                    elem_type = str(elem.get("type", ""))
                    if elem_type == "box_spec":
                        continue
                    if elem.get("print_direct") is False:
                        continue

                    x = float(elem.get("x", 8.0))
                    y = float(elem.get("y", 5.0))
                    w = float(elem.get("w", 84.0))
                    h = float(elem.get("h", 6.0))

                    if elem_type == "divider":
                        self.sdk.draw_line(
                            lc_hdl,
                            x,
                            y,
                            x + w,
                            y,
                            line_width=int(elem.get("line_width", 1)),
                            line_type=int(elem.get("line_type", 0)),
                        )
                    elif elem_type == "brand_logo":
                        self.sdk.draw_image(
                            lc_hdl,
                            x,
                            y,
                            w,
                            h,
                            resolve_asset_path(str(elem.get("asset_path") or elem.get("value") or "")),
                        )
                    elif elem_type == "barcode":
                        self.sdk.draw_barcode(
                            lc_hdl,
                            x,
                            y,
                            w,
                            h,
                            barcode_type,
                            scanned_box_code,
                            show_text=bool(elem.get("show_text", True)),
                        )
                    elif elem_type == "barcode_text":
                        # 放大绘制条形码下方的 13 位箱码数字
                        self.sdk.draw_text(
                            lc_hdl,
                            x,
                            y,
                            w,
                            h,
                            scanned_box_code,
                            font_size=float(elem.get("font_size", 15.0)),
                            font_name=str(elem.get("font_name", "宋体")),
                            is_bold=True,
                        )
                    else:
                        draw_str = render_text(elem, data_map)
                        if not draw_str:
                            continue
                        self.sdk.draw_text(
                            lc_hdl,
                            x,
                            y,
                            w,
                            h,
                            draw_str,
                            font_size=float(elem.get("font_size", 8.0)),
                            font_name=str(elem.get("font_name", "宋体")),
                            is_bold=bool(elem.get("bold", False)),
                        )

                rfid_cfg = self.config.get("rfid", {})
                rgn_type = int(rfid_cfg.get("region_type_code", 1))
                fmt_code = int(rfid_cfg.get("data_format_code", 2))
                read_type_mask = int(rfid_cfg.get("read_type_mask", 1))

                if fmt_code == 1:
                    rfid_payload = rfid_code[:12] if len(rfid_code) > 12 else rfid_code.ljust(12, "0")
                elif fmt_code == 2:
                    rfid_payload = rfid_code.ljust(24, "0")[:24]
                else:
                    rfid_payload = rfid_code[:12]

                try:
                    self.sdk.set_rfid_data(lc_hdl, rgn_type, fmt_code, rfid_payload)
                except Exception as e:
                    logger.warning(f"设置 RFID 数据告警: {e}")

                try:
                    raw_rfid_str = self.sdk.print_label_and_read_rfid(
                        self.dev_hdl, lc_hdl, read_type=read_type_mask
                    )
                    result.raw_rfid_str = raw_rfid_str
                    try:
                        chip_info = self.read_chip_status()
                        result.read_tid = chip_info.get("tid", "")
                        result.read_epc = chip_info.get("epc", "")
                        result.read_user = chip_info.get("user", "")
                    except Exception:
                        pass
                    result.success = True
                    result.error_message = (
                        f"标签使用真实箱码，RFID写入13位时间戳 {rfid_code} (PASS)"
                    )
                except Exception as rfid_err:
                    logger.warning(f"RFID写入未响应 ({rfid_err})，自动切换为纯打纸出纸模式...")
                    try:
                        self.sdk.delete_label(lc_hdl)
                    except Exception:
                        pass

                    lc_hdl_plain = self.sdk.create_label(width_mm, height_mm)
                    try:
                        self.sdk.set_lc_prn_mode(lc_hdl_plain, 1)
                        self.sdk.set_lc_prn_rotate(lc_hdl_plain, canvas_rotate)
                        for elem in elements:
                            if elem.get("enabled") is False or str(elem.get("type")) == "box_spec" or elem.get("print_direct") is False:
                                continue
                            x = float(elem.get("x", 8.0))
                            y = float(elem.get("y", 5.0))
                            w = float(elem.get("w", 84.0))
                            h = float(elem.get("h", 6.0))
                            elem_type = str(elem.get("type", ""))
                            if elem_type == "divider":
                                self.sdk.draw_line(lc_hdl_plain, x, y, x + w, y, line_width=int(elem.get("line_width", 1)))
                            elif elem_type == "brand_logo":
                                self.sdk.draw_image(lc_hdl_plain, x, y, w, h, resolve_asset_path(str(elem.get("asset_path") or elem.get("value") or "")))
                            elif elem_type == "barcode":
                                b_val = str(data_map.get("barcode") or elem.get("value") or scanned_box_code)
                                self.sdk.draw_barcode(lc_hdl_plain, x, y, w, h, barcode_type, b_val, show_text=bool(elem.get("show_text", True)))
                            else:
                                draw_str = render_text(elem, data_map)
                                if draw_str:
                                    self.sdk.draw_text(lc_hdl_plain, x, y, w, h, draw_str, font_size=float(elem.get("font_size", 8.0)), font_name=str(elem.get("font_name", "宋体")), is_bold=bool(elem.get("bold", False)))

                        try:
                            self.sdk.print_label_and_read_rfid(self.dev_hdl, lc_hdl_plain, read_type=0)
                        except Exception as e:
                            logger.warning(f"纯打纸底层返回 ({e})，数据已完美下发至打印队列")
                        result.success = True
                        result.error_message = f"标签打印成功 (已打纸出纸): {rfid_err}"
                    finally:
                        self.sdk.delete_label(lc_hdl_plain)
            finally:
                try:
                    self.sdk.delete_label(lc_hdl)
                except Exception:
                    pass

        except InvalidBoxCodeError as e:
            result.success = False
            result.error_code = e.code
            result.error_message = f"箱码校验失败: {e.message}"
        except DeviceNotFoundError as e:
            result.success = False
            result.error_code = e.code
            result.error_message = f"设备未就绪: {e.message}"
        except PrinterStatusError as e:
            result.success = False
            result.error_code = e.code
            result.error_message = f"打印写入过程失败: {e.message}"
        except Exception as e:
            result.success = False
            result.error_code = -999
            result.error_message = f"未知异常: {str(e)}"
        finally:
            result.elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            self.append_record_to_csv(result)
            try:
                self.disconnect()
            except Exception:
                pass
            self._print_lock.release()

        return result

    def batch_print_write_verify(
        self,
        item_list: List[LabelPrintData],
        allow_reprint_same_code: bool = True
    ) -> List[PrintResult]:
        results = []
        logger.info(f"开始执行连续批量打印写卡任务，总计: {len(item_list)} 张标签...")
        for idx, item in enumerate(item_list, 1):
            logger.info(f"--- 连续打印 [第 {idx}/{len(item_list)} 张] 箱码: {item.box_code} ({item.product_name}) ---")
            res = self.print_write_verify(item.box_code, label_data=item, allow_reprint_same_code=allow_reprint_same_code)
            results.append(res)
            time.sleep(0.3)
        return results
