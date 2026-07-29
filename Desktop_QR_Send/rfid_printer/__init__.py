"""
RfidPrinter 模块对外导出接口
"""

from .sdk import T63RSdk
from .encoder import validate_box_code, parse_rfid_read_back, hex_to_ascii, verify_box_code_match
from .workflow import RfidPrintService
from .models import PrinterDeviceInfo, PrintResult, LabelPrintData
from .errors import (
    RfidPrinterError,
    SdkInitError,
    DeviceConnectError,
    InvalidBoxCodeError,
    DeviceNotFoundError,
    PrinterStatusError,
    WriteVerifyMismatchError,
)

__all__ = [
    "T63RSdk",
    "RfidPrintService",
    "PrinterDeviceInfo",
    "PrintResult",
    "LabelPrintData",
    "validate_box_code",
    "parse_rfid_read_back",
    "hex_to_ascii",
    "verify_box_code_match",
    "RfidPrinterError",
    "SdkInitError",
    "DeviceConnectError",
    "InvalidBoxCodeError",
    "DeviceNotFoundError",
    "PrinterStatusError",
    "WriteVerifyMismatchError",
]
