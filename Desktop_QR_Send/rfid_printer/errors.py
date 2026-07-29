"""
自定义异常类体系
"""

class RfidPrinterError(Exception):
    """RFID 打印机测试项目的基础异常类"""
    def __init__(self, message: str, code: int = -1):
        super().__init__(message)
        self.message = message
        self.code = code

    def __str__(self):
        return f"[{self.code}] {self.message}"


class SdkInitError(RfidPrinterError):
    """SDK 初始化失败"""
    pass


class DeviceNotFoundError(RfidPrinterError):
    """未找到打印机设备"""
    pass


class DeviceConnectError(RfidPrinterError):
    """连接打印机失败"""
    pass


class InvalidBoxCodeError(RfidPrinterError):
    """13 位箱码格式无效"""
    pass


class PrinterStatusError(RfidPrinterError):
    """打印机状态异常（如缺纸、开盖、报错等）"""
    pass


class WriteVerifyMismatchError(RfidPrinterError):
    """RFID 读回数据与原箱码不一致"""
    def __init__(self, message: str, box_code: str = "", read_value: str = "", code: int = -2):
        super().__init__(message, code)
        self.box_code = box_code
        self.read_value = read_value
