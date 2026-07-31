"""
箱码编码、校验与 RFID 读回解析转换模块
"""

import re
import time
from .errors import InvalidBoxCodeError


def normalize_scanned_box_code(box_code: str) -> str:
    """原样保留相机真实识别内容，不截取、不清洗，也不改写为时间戳。"""
    if not isinstance(box_code, str):
        raise InvalidBoxCodeError(f"真实箱码必须为字符串，传入类型为: {type(box_code).__name__}")
    if not box_code.strip():
        raise InvalidBoxCodeError("真实箱码不能为空")
    if len(box_code.encode("utf-8")) > 512:
        raise InvalidBoxCodeError("真实箱码内容超过512字节，不能生成标签条码")
    return box_code


def generate_rfid_timestamp() -> str:
    """生成只用于RFID写入的13位毫秒时间戳。"""
    value = str(int(time.time() * 1000))
    if len(value) > 13:
        value = value[-13:]
    elif len(value) < 13:
        value = value.zfill(13)
    return validate_box_code(value)


def validate_box_code(box_code: str) -> str:
    """
    校验用于RFID写入的13位数字时间戳。
    保留旧函数名以兼容原有调用；真实识别箱码请使用 normalize_scanned_box_code。
    """
    if not isinstance(box_code, str):
        raise InvalidBoxCodeError(f"RFID时间戳必须为字符串类型，传入类型为: {type(box_code).__name__}")

    code = box_code.strip()
    if not code:
        raise InvalidBoxCodeError("RFID时间戳不能为空")

    if len(code) != 13:
        raise InvalidBoxCodeError(f"RFID时间戳必须刚好为13位数字，当前长度为{len(code)}位")

    if not code.isdigit():
        raise InvalidBoxCodeError("RFID时间戳必须全为数字")

    return code


def parse_rfid_read_back(raw_str: str) -> dict:
    """
    解析 SDK DSTP2x_PrintLc 读回的 RFID 十六进制字符串。
    典型格式: "TID:E280...|EPC:3031...|USER:..."
    """
    result = {
        "tid": "",
        "epc": "",
        "user": "",
        "raw": raw_str or ""
    }

    if not raw_str:
        return result

    parts = raw_str.strip().split("|")
    for part in parts:
        if not part:
            continue
        if ":" in part:
            key, val = part.split(":", 1)
            key_upper = key.strip().upper()
            val_clean = val.strip()
            if key_upper == "TID":
                result["tid"] = val_clean
            elif key_upper == "EPC":
                result["epc"] = val_clean
            elif key_upper == "USER":
                result["user"] = val_clean

    return result


def hex_to_ascii(hex_str: str) -> str:
    """
    将十六进制字符串转换回 ASCII 字符串，
    自动去除尾部的 Null 字符 (00) 或空白填补。
    如 '30313233343536373839303132' -> '0123456789012'
    """
    if not hex_str:
        return ""

    clean_hex = re.sub(r'[^0-9a-fA-F]', '', hex_str)
    if not clean_hex or len(clean_hex) % 2 != 0:
        return ""

    try:
        raw_bytes = bytes.fromhex(clean_hex)
        # 过滤控制字符，只提取可打印 ASCII 字符
        ascii_chars = []
        for b in raw_bytes:
            if b == 0:
                break  # 遇到 NUL 终止标志直接结束
            if 32 <= b <= 126:
                ascii_chars.append(chr(b))
            else:
                # 若遇到非可打印字符，跳过或停在可打印范围
                break
        return "".join(ascii_chars)
    except Exception:
        return ""


def verify_box_code_match(original_box_code: str, read_back_ascii: str) -> bool:
    """
    核对读回的 ASCII 字符串与原箱码是否完全一致。
    严格比对字符串，防止 '0123456789012' 被误算成 123456789012。
    """
    clean_original = validate_box_code(original_box_code)
    clean_read = read_back_ascii.strip()
    return clean_original == clean_read
