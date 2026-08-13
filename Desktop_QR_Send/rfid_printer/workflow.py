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

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
logger = logging.getLogger("RfidPrintWorkflow")

class RfidPrintService:
    """RFID 打印写卡及闭环核验服务"""

    def __init__(self, config_path: Optional[str] = None):
        if not config_path:
            self.config_path = os.path.join(PROJECT_ROOT, "config", "settings.json")
        else:
            self.config_path = os.path.abspath(config_path)

        self.config = self._load_config()

        vendor_dir = os.path.join(PROJECT_ROOT, "vendor", "t63r_x64")
        if not os.path.exists(vendor_dir):
            vendor_dir = os.path.abspath(self.config.get("vendor_dir", "vendor/t63r_x64"))

        self.sdk = T63RSdk(vendor_dir=vendor_dir)
        self.connected_dev_name: str = ""
        self.dev_hdl: int = 0
        self.csv_path = os.path.join(PROJECT_ROOT, "records", "print_records.csv")

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
        if not os.path.exists(self.csv_path) or os.path.getsize(self.csv_path) == 0:
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
        self._ensure_csv_header()
        try:
            ts = getattr(result, "timestamp", "") or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            box_code = getattr(result, "box_code", "")
            written_val = getattr(result, "written_value", "") or box_code
            tid = getattr(result, "read_tid", "")
            epc = getattr(result, "read_epc", "")
            user = getattr(result, "read_user", "")
            ascii_val = getattr(result, "read_ascii", "")
            success_str = "PASS" if getattr(result, "success", True) else "FAIL"
            elapsed = round(float(getattr(result, "elapsed_ms", 0.0)), 2)
            err_code = getattr(result, "error_code", 0)
            err_msg = getattr(result, "error_message", "")

            with open(self.csv_path, "a", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                writer.writerow([
                    ts, box_code, self.config.get("rfid", {}).get("target_region", "EPC"),
                    written_val, tid, epc, user, ascii_val, success_str, elapsed, err_code, err_msg
                ])
            logger.info(f"✅ [成功追加历史打印记录] 箱码={box_code}, RFID={written_val}")
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
                        if len(row) > 1 and row[1].strip():
                            printed_set.add(row[1].strip())
                        if len(row) > 3 and row[3].strip():
                            printed_set.add(row[3].strip())
            except Exception as e:
                logger.warning(f"读取 CSV 历史记录失败: {e}")

        try:
            from utils.SQLite import db
            conn = db.get_connection()
            with db.lock:
                cursor = conn.cursor()
                cursor.execute("SELECT DISTINCT caseContent FROM yk_box_case_history WHERE caseContent IS NOT NULL AND caseContent != ''")
                for r in cursor.fetchall():
                    if r[0]:
                        printed_set.add(str(r[0]).strip())
                cursor.execute("SELECT DISTINCT case_code FROM packing_case WHERE case_code IS NOT NULL AND case_code != ''")
                for r in cursor.fetchall():
                    if r[0]:
                        printed_set.add(str(r[0]).strip())
        except Exception:
            pass

        try:
            from utils.local_data_pipeline import get_db_connection
            l_conn = get_db_connection()
            if l_conn:
                l_cursor = l_conn.cursor()
                l_cursor.execute("SELECT DISTINCT case_code FROM local_test_print_records WHERE case_code IS NOT NULL AND case_code != ''")
                for r in l_cursor.fetchall():
                    if r[0]:
                        printed_set.add(str(r[0]).strip())
                l_conn.close()
        except Exception:
            pass

        return printed_set

    def list_usb_printers(self) -> List[str]:
        self.sdk.load_and_init()
        return self.sdk.enum_usb_devices()

    def connect(self, dev_name: Optional[str] = None) -> PrinterDeviceInfo:
        self.sdk.load_and_init()

        target_name = dev_name
        devices = []
        try:
            devices = self.sdk.enum_usb_devices()
        except Exception as e:
            logger.warning(f"枚举 USB 设备提示: {e}")

        candidate_names = []
        if target_name:
            candidate_names.append(target_name)
        if devices:
            for d in devices:
                if d not in candidate_names:
                    candidate_names.append(d)

        # 候选设备与常见 USB 标识符
        for fallback_str in ("usb://", "usb://0", "usb://1", "usb://MC335218@JiEPRTT63RZ$V2867P1508MC$0JJ125350016."):
            if fallback_str not in candidate_names:
                candidate_names.append(fallback_str)

        if self.dev_hdl:
            self.disconnect()

        last_err = None
        for dev_str in candidate_names:
            for retry in range(2):
                try:
                    self.dev_hdl = self.sdk.connect_device(dev_str)
                    self.connected_dev_name = dev_str
                    logger.info(f"成功连接设备: '{dev_str}'")
                    break
                except Exception as e:
                    last_err = e
                    self.dev_hdl = 0
                    time.sleep(0.2)
            if self.dev_hdl:
                break

        if not self.dev_hdl:
            try:
                self.sdk.clear_and_unload()
                self.sdk.load_and_init()
                self.dev_hdl = self.sdk.connect_device("usb://")
                self.connected_dev_name = "usb://"
            except Exception:
                raise DeviceNotFoundError(
                    f"连接 USB 打印机失败: {last_err or '请检查 USB 数据线与电源开关'}"
                )

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
        for attempt in range(2):
            res = self.sdk.read_rfid_direct(self.dev_hdl)
            if res.get("epc") or res.get("tid"):
                return res
            if attempt < 1:
                time.sleep(0.1)
        return res

    def print_write_verify(
        self,
        box_code: str,
        label_data: Optional[LabelPrintData] = None,
        allow_reprint_same_code: Optional[bool] = None
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
            # RFID 写入值与箱码完全一致，即 13 位箱码原文！
            rfid_code = scanned_box_code
            result.box_code = scanned_box_code
            result.written_value = rfid_code

            label_cfg = self.config.get("label", {})
            width_mm = float(label_cfg.get("width_mm", 150.0))
            height_mm = float(label_cfg.get("height_mm", 75.0))
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

            is_already_printed = False
            allow_reprint = allow_reprint_same_code if allow_reprint_same_code is not None else bool(self.config.get("rfid", {}).get("allow_reprint_same_code", False))
            printed_codes = self.list_printed_epcs_from_csv()
            if scanned_box_code in printed_codes and not allow_reprint:
                is_already_printed = True
                logger.info(f"【防二次写入锁生效】检测到 13 位箱码 '{scanned_box_code}' 已存在于历史记录中，跳过 RFID 写入 (未下发 set_rfid_data)，仅物理纸面打纸。")

            if not self.dev_hdl:
                try:
                    self.connect()
                except Exception as conn_err:
                    logger.warning(f"尝试连接打印机 C SDK 提示: {conn_err}")

            # 物理芯片防二次写入保护锁：若芯片内已存在有效 RFID 数据，自动拦截并跳过写卡
            if not is_already_printed and self.dev_hdl:
                try:
                    chip_info = self.read_chip_status()
                    existing_epc = str(chip_info.get("epc", "")).strip().upper()
                    if existing_epc and existing_epc != "000000000000000000000000" and len(existing_epc) >= 12 and not allow_reprint:
                        is_already_printed = True
                        logger.info(f"检测到当前物理标签芯片内已存在有效 RFID 数据 (EPC: {existing_epc})，激活物理芯片防二次写入锁：跳过 RFID 写卡，仅物理纸面排版打纸出纸。")
                except Exception as read_err:
                    logger.warning(f"预读物理芯片状态告警 ({read_err})，按标准流程下发...")

            # 设置 203 DPI 印头与 ZPL 打印语言模式
            dpi_type = int(self.config.get("label", {}).get("dpi_type", 1))
            self.sdk.set_img_dpi(self.dev_hdl, dpi_type)           # 203 DPI 点阵点对点映射
            self.sdk.set_prn_emulation(self.dev_hdl, 1)            # ZPL 仿真模式

            # 物理打纸画布拓展（不影响预览）：右边伸长 60mm，上下伸长 30mm
            print_ext_w = width_mm + 60.0
            print_ext_h = height_mm + 30.0

            lc_hdl = self.sdk.create_label(print_ext_w, print_ext_h)
            self.sdk.set_lc_prn_mode(lc_hdl, 0)
            canvas_rotate = int(layout.get("canvas_rotate", 0))
            self.sdk.set_lc_prn_rotate(lc_hdl, canvas_rotate)

            try:
                resolved_elements = resolve_layout_elements(layout, print_ext_w, print_ext_h)
                barcode_type = int(layout.get("barcode_type_code", 20))
                data_map = label_data.to_dict()

                for elem in resolved_elements:
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
                        is_right = elem_type in ("produce_date_label", "produce_date")
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
                            align_right=is_right,
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

                if not is_already_printed:
                    try:
                        self.sdk.set_rfid_data(lc_hdl, rgn_type, fmt_code, rfid_payload)
                        # 首次写入数据时同步下发物理芯片死锁指令 (Permanent Lock)
                        # 注意：依据 T63R SDK 规范及 UHF Gen2 协议，物理锁定密码必须是非全0的 8 位十六进制字符串 (如 '12345678')
                        lock_type = int(rfid_cfg.get("lock_type", 0))  # 0代表永久物理死锁
                        password = str(rfid_cfg.get("lock_password", "12345678")).strip()
                        if not password or password == "00000000":
                            password = "12345678"

                        if self.dev_hdl:
                            # 1. 将 Access 访问密码由默认 00000000 修改为专用密钥
                            try:
                                self.sdk.change_access_password(self.dev_hdl, old_pw="00000000", new_pw=password)
                            except Exception as pe:
                                logger.warning(f"修改访问密码提示: {pe}")

                            # 2. 授权带密码写入 EPC 区
                            try:
                                self.sdk.set_password_with_write(self.dev_hdl, rfid_area=rgn_type, password=password)
                            except Exception as pe:
                                logger.warning(f"授权带密码写入提示: {pe}")

                            # 3. 设置为永久物理锁 (Permanent lock = 0)
                            try:
                                self.sdk.rfid_lock_type_setting(self.dev_hdl, rfid_area=rgn_type, lock_type=lock_type, temporary=0)
                            except Exception as pe:
                                logger.warning(f"设置芯片死锁类型提示: {pe}")

                            # 4. 下发物理死锁操作
                            try:
                                self.sdk.rfid_lock_operate(self.dev_hdl, rfid_area=rgn_type, password=password)
                            except Exception as pe:
                                logger.warning(f"执行物理芯片锁死提示: {pe}")

                            # 5. 给予 USB 通讯端口 200ms 缓冲，彻底防止死锁指令与 PrintLc 画布出纸发生 25182208 占用冲突
                            time.sleep(0.2)
                    except Exception as e:
                        logger.warning(f"设置 RFID 数据及芯片锁告警: {e}")

                try:
                    read_mask = 0 if is_already_printed else read_type_mask
                    raw_rfid_str = self.sdk.print_label_and_read_rfid(
                        self.dev_hdl, lc_hdl, read_type=read_mask
                    )
                    result.raw_rfid_str = raw_rfid_str
                    if not is_already_printed:
                        try:
                            chip_info = self.read_chip_status()
                            result.read_tid = chip_info.get("tid", "")
                            result.read_epc = chip_info.get("epc", "")
                            result.read_user = chip_info.get("user", "")
                        except Exception:
                            pass
                        self.append_record_to_csv(result)
                        result.success = True
                        result.error_message = (
                            f"标签打纸成功，RFID已成功写入13位箱码 {rfid_code} (PASS)"
                        )
                    else:
                        result.success = True
                        result.error_message = (
                            f"标签重新打印成功（已开启防二次写入保护，跳过 RFID 写卡）"
                        )
                except Exception as rfid_err:
                    logger.warning(f"C SDK RFID 闭环未响应 ({rfid_err})，自动原位尝试 C SDK 纯打纸出纸模式(read_type=0)...")
                    try:
                        self.sdk.print_label_and_read_rfid(self.dev_hdl, lc_hdl, read_type=0)
                        self.append_record_to_csv(result)
                        result.success = True
                        result.error_message = f"标签纸面打印成功 (RFID防二次写入锁生效，芯片写锁保护维持原数据)"
                    except Exception as pure_err:
                        logger.warning(f"C SDK 纯打纸模式提示 ({pure_err})，即将自动触发底层 RAW 端口出纸模式...")
                        self.disconnect()
                        result.success = False
                        result.error_message = f"C SDK 提示: {rfid_err}"
                        return result
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
        allow_reprint_same_code: Optional[bool] = None
    ) -> List[PrintResult]:
        results = []
        logger.info(f"开始执行连续批量打印写卡任务，总计: {len(item_list)} 张标签...")
        for idx, item in enumerate(item_list, 1):
            logger.info(f"--- 连续打印 [第 {idx}/{len(item_list)} 张] 箱码: {item.box_code} ({item.product_name}) ---")
            res = self.print_write_verify(item.box_code, label_data=item, allow_reprint_same_code=allow_reprint_same_code)
            results.append(res)
            time.sleep(0.3)
        return results

