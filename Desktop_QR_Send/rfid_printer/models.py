"""
数据模型定义
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from datetime import datetime


@dataclass
class PrinterDeviceInfo:
    """打印机设备信息"""
    name: str = ""
    sn: str = ""
    fw_ver: str = ""
    is_ready: bool = False
    status_desc: str = ""
    connect_time: Optional[datetime] = None


@dataclass
class LabelPrintData:
    """真实生产箱标签模板数据字段（后续可由 API / 数据库直接赋值）"""
    box_code: str = "0123456789012"                   # 13 位箱码
    brand: str = "高原安"                             # 品牌
    product_name: str = "高原安藏式甜茶"               # 产品名称
    spec: str = "200g(20g*10条)/盒"                   # 规格
    box_spec: str = "200g*40盒/箱"                    # 箱规
    shelf_life: str = "18个月"                        # 保质期
    produce_date: str = field(default_factory=lambda: datetime.now().strftime("%Y/%m/%d"))  # 生产日期
    storage: str = "干燥、阴凉、通风处"                # 储存条件
    manufacturer: str = "乌兰察布蒙帝乳业有限责任公司" # 生产商

    def to_dict(self) -> Dict[str, Any]:
        return {
            "box_code": self.box_code,
            "brand": self.brand,
            "product_name": self.product_name,
            "spec": self.spec,
            "box_spec": self.box_spec,
            "shelf_life": self.shelf_life,
            "produce_date": self.produce_date,
            "storage": self.storage,
            "manufacturer": self.manufacturer,
        }


@dataclass
class PrintResult:
    """一次打印写入与读回比对的任务结果"""
    success: bool = False
    box_code: str = ""
    written_value: str = ""
    read_tid: str = ""
    read_epc: str = ""
    read_user: str = ""
    read_ascii: str = ""
    raw_rfid_str: str = ""
    elapsed_ms: float = 0.0
    error_code: int = 0
    error_message: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "box_code": self.box_code,
            "written_value": self.written_value,
            "read_tid": self.read_tid,
            "read_epc": self.read_epc,
            "read_user": self.read_user,
            "read_ascii": self.read_ascii,
            "raw_rfid_str": self.raw_rfid_str,
            "elapsed_ms": round(self.elapsed_ms, 2),
            "error_code": self.error_code,
            "error_message": self.error_message,
            "timestamp": self.timestamp,
        }
