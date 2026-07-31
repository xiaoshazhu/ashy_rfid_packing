"""箱码标签的版式配置与文本解析。

坐标、宽高均使用毫米，字号使用磅。打印机为单色热敏设备，配置中的颜色
主要用于屏幕/PDF预览；实际打印统一转换为黑色，浅灰分隔线使用 1 像素细线。
"""

from __future__ import annotations

import copy
import re
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional


TEMPLATE_ID = "box_design_v1"
PROFILE_100X80 = "100x80"
PROFILE_150X75 = "150x75"
DEFAULT_FONT = "Microsoft YaHei"
PROJECT_ROOT = Path(__file__).resolve().parents[1]
LOGO_ASSET = "assets/gaoyuanan_logo.png"
REQUIRED_ELEMENT_TYPES = {
    "product_caption",
    "brand_logo",
    "produce_date_label",
    "divider",
    "barcode",
}
INTERNAL_ELEMENT_TYPES = {"box_count", "box_unit"}


def _text(
    elem_type: str,
    label: str,
    value: str,
    x: float,
    y: float,
    w: float,
    h: float,
    font_size: float,
    *,
    bold: bool = False,
    enabled: bool = True,
    color: str = "#2B2B2B",
    type_desc: str = "基础文本",
    required: bool = False,
    template_visible: bool = True,
    print_direct: bool = True,
) -> Dict[str, Any]:
    return {
        "type": elem_type,
        "label": label,
        "value": value,
        "enabled": enabled,
        "type_desc": type_desc,
        "x": x,
        "y": y,
        "w": w,
        "h": h,
        "font_name": DEFAULT_FONT,
        "font_size": font_size,
        "bold": bold,
        "color": color,
        "required": required,
        "template_visible": template_visible,
        "print_direct": print_direct,
    }


def _line(x: float, y: float, w: float) -> Dict[str, Any]:
    return {
        "type": "divider",
        "label": "上下区域分隔线",
        "value": "",
        "enabled": True,
        "type_desc": "设计元素（细实线）",
        "x": x,
        "y": y,
        "w": w,
        "h": 0.0,
        "line_width": 1,
        "line_type": 0,
        "color": "#B7B7B7",
        "required": True,
        "template_visible": True,
    }


def _barcode(x: float, y: float, w: float, h: float) -> Dict[str, Any]:
    return {
        "type": "barcode",
        "label": "真实识别箱码条形码",
        "value": "",
        "enabled": True,
        "type_desc": "真实扫码原文 / Code 128（固定项）",
        "x": x,
        "y": y,
        "w": w,
        "h": h,
        "show_text": True,
        "color": "#000000",
        "required": True,
        "template_visible": True,
    }


def _image(x: float, y: float, w: float, h: float) -> Dict[str, Any]:
    return {
        "type": "brand_logo",
        "label": "高原安品牌图片",
        "value": LOGO_ASSET,
        "asset_path": LOGO_ASSET,
        "enabled": True,
        "type_desc": "固定图片（不可取消）",
        "x": x,
        "y": y,
        "w": w,
        "h": h,
        "color": "#000000",
        "required": True,
        "template_visible": True,
    }


PROFILE_ELEMENTS: Dict[str, List[Dict[str, Any]]] = {
    # 100x80 测试纸：保持 150x75 原稿的视觉层级，针对较窄纸张重新排版。
    PROFILE_100X80: [
        _text("product_caption", "产品名称标题", "产品名称/PRODUCT NAME", 5.0, 4.5, 62.0, 4.0, 7.0, required=True),
        _image(72.0, 4.5, 23.0, 8.0),
        _text("product_name", "产品名称", "高原安藏式甜茶", 5.0, 10.0, 66.0, 10.0, 20.0, bold=True, color="#000000"),
        _text("spec", "产品规格", "200g (20g×10条)/盒", 5.0, 23.5, 61.0, 4.2, 7.2),
        _text("shelf_life", "保质期", "18个月", 5.0, 28.3, 61.0, 4.2, 7.2),
        _text("storage", "储存条件", "干燥、阴凉、通风处", 5.0, 33.1, 61.0, 4.2, 7.2),
        _text("manufacturer", "生产商", "乌兰察布蒙帝乳业有限责任公司", 5.0, 37.9, 61.0, 4.2, 7.0),
        _text("produce_date_label", "生产日期标题", "生产日期", 70.0, 24.5, 25.0, 4.0, 7.0, required=True),
        _text("produce_date", "日期", "", 67.0, 29.5, 28.0, 6.0, 12.0, bold=True, color="#000000"),
        _line(5.0, 46.0, 90.0),
        _text("box_count", "每箱数量", "40", 5.0, 49.5, 22.5, 17.0, 38.0, bold=True, color="#000000", template_visible=False),
        _text("box_unit", "箱规单位", "盒/箱", 28.0, 61.0, 13.0, 5.0, 9.0, bold=True, color="#000000", template_visible=False),
        _text("unit_net_weight", "单盒内容", "单盒净含量 200 g", 5.0, 71.0, 35.0, 4.0, 7.2),
        _barcode(43.0, 51.5, 52.0, 21.0),
        _text(
            "box_spec",
            "箱规",
            "40盒/箱",
            5.0,
            42.0,
            61.0,
            4.0,
            7.0,
            enabled=True,
            type_desc="可选字段（控制左下角数量与单位）",
            print_direct=False,
        ),
    ],
    # 150x75 最终纸：坐标来自箱码设计.ai（Adobe Illustrator 画板）。
    PROFILE_150X75: [
        _text("product_caption", "产品名称标题", "产品名称/PRODUCT NAME", 6.0, 6.4, 31.0, 3.0, 7.0, required=True),
        _image(124.4, 5.9, 19.6, 5.8),
        _text("product_name", "产品名称", "高原安藏式甜茶", 5.9, 11.6, 59.0, 8.5, 23.8, bold=True, color="#000000"),
        _text("spec", "产品规格", "200g (20g×10条)/盒", 6.0, 24.7, 61.0, 3.5, 7.0),
        _text("shelf_life", "保质期", "18个月", 6.0, 29.5, 61.0, 3.5, 7.0),
        _text("storage", "储存条件", "干燥、阴凉、通风处", 6.0, 34.3, 61.0, 3.5, 7.0),
        _text("manufacturer", "生产商", "乌兰察布蒙帝乳业有限责任公司", 6.0, 39.0, 61.0, 3.5, 7.0),
        _text("produce_date_label", "生产日期标题", "生产日期", 134.3, 33.9, 10.0, 3.0, 7.0, required=True),
        _text("produce_date", "日期", "", 120.9, 38.4, 23.2, 4.6, 12.55, bold=True, color="#000000"),
        _line(6.0, 46.0, 137.9),
        _text("box_count", "每箱数量", "40", 5.8, 51.5, 20.0, 16.9, 47.7, bold=True, color="#000000", template_visible=False),
        _text("box_unit", "箱规单位", "盒/箱", 26.6, 60.7, 8.0, 3.3, 9.0, bold=True, color="#000000", template_visible=False),
        _text("unit_net_weight", "单盒内容", "单盒净含量 200 g", 5.9, 66.8, 30.0, 3.0, 7.0),
        _barcode(73.1, 50.2, 70.9, 18.8),
        _text(
            "box_spec",
            "箱规",
            "40盒/箱",
            6.0,
            42.0,
            61.0,
            3.5,
            7.0,
            enabled=True,
            type_desc="可选字段（控制左下角数量与单位）",
            print_direct=False,
        ),
    ],
}


CONTENT_FIELDS = ("label", "value", "enabled", "type_desc")


def profile_name_for_size(width_mm: float, height_mm: float) -> str:
    """根据纸张尺寸选择最接近的内置版式。"""
    if abs(width_mm - 150.0) <= 0.6 and abs(height_mm - 75.0) <= 0.6:
        return PROFILE_150X75
    return PROFILE_100X80


def default_elements(width_mm: float = 100.0, height_mm: float = 80.0) -> List[Dict[str, Any]]:
    return copy.deepcopy(PROFILE_ELEMENTS[profile_name_for_size(width_mm, height_mm)])


def merge_content(
    base_elements: Iterable[Mapping[str, Any]],
    content_elements: Iterable[Mapping[str, Any]],
) -> List[Dict[str, Any]]:
    """把弹窗中可编辑的内容合并到固定版式，不覆盖坐标、字号等设计参数。"""
    content_by_type = {
        str(item.get("type")): item
        for item in content_elements
        if item.get("type")
    }
    merged: List[Dict[str, Any]] = []
    seen = set()
    for base in base_elements:
        item = copy.deepcopy(dict(base))
        elem_type = str(item.get("type", ""))
        current = content_by_type.get(elem_type)
        if current:
            for key in CONTENT_FIELDS:
                if key in current:
                    item[key] = current[key]
        merged.append(item)
        seen.add(elem_type)

    # 保留用户在弹窗中新增的自定义字段及其已有坐标。
    for current in content_elements:
        elem_type = str(current.get("type", ""))
        if elem_type and elem_type not in seen:
            merged.append(copy.deepcopy(dict(current)))
    return merged


def resolve_layout_elements(
    layout: Optional[Mapping[str, Any]],
    width_mm: float,
    height_mm: float,
) -> List[Dict[str, Any]]:
    """解析当前纸张应使用的版式，并兼容旧版 settings.json。"""
    layout = layout or {}
    profile_name = profile_name_for_size(width_mm, height_mm)
    base = default_elements(width_mm, height_mm)
    stored = list(layout.get("elements", []) or [])

    if (
        layout.get("template_id") == TEMPLATE_ID
        and layout.get("profile") == profile_name
        and stored
    ):
        # 同一版式以已保存项目为准，避免用户在弹窗中删除的字段下次又出现；
        # 内置默认项只负责补齐旧配置缺失的坐标和样式键。
        defaults_by_type = {
            str(item.get("type")): item for item in base if item.get("type")
        }
        result = []
        for stored_item in stored:
            elem_type = str(stored_item.get("type", ""))
            item = copy.deepcopy(defaults_by_type.get(elem_type, {}))
            item.update(copy.deepcopy(stored_item))
            result.append(item)
        return result

    # 新版模板切换纸张尺寸时保留用户已经删除的字段；旧版配置首次升级时
    # 则补齐完整设计板块。
    if layout.get("template_id") == TEMPLATE_ID and stored:
        present_types = {str(item.get("type", "")) for item in stored}
        base = [item for item in base if str(item.get("type", "")) in present_types]

    # 旧版配置或纸张尺寸切换：继承内容/勾选状态，换用目标版式坐标。
    return merge_content(base, stored)


def format_produce_date(value: str) -> str:
    return re.sub(r"[-/]", ".", str(value or "").strip())


def resolve_asset_path(value: str) -> str:
    path = Path(str(value or ""))
    if not path.is_absolute():
        path = PROJECT_ROOT / path
    return str(path.resolve())


def is_required_element(elem: Mapping[str, Any]) -> bool:
    return bool(elem.get("required")) or str(elem.get("type", "")) in REQUIRED_ELEMENT_TYPES


def is_template_visible(elem: Mapping[str, Any]) -> bool:
    return bool(elem.get("template_visible", True)) and str(elem.get("type", "")) not in INTERNAL_ELEMENT_TYPES


def extract_box_count(box_spec: str, fallback: str = "40") -> str:
    text = str(box_spec or "")
    patterns = (
        r"(\d+)\s*盒\s*/\s*箱",
        r"[*×xX]\s*(\d+)\s*盒",
        r"(\d+)\s*(?:盒|瓶)\s*/\s*箱",
    )
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1)
    return fallback


def extract_box_unit(box_spec: str, fallback: str = "盒/箱") -> str:
    text = str(box_spec or "")
    match = re.search(r"\d+\s*([^\d\s*/]+)\s*/\s*箱", text)
    if match:
        return f"{match.group(1)}/箱"
    return fallback


def extract_unit_weight(spec: str, fallback: str = "200 g") -> str:
    match = re.search(r"(\d+(?:\.\d+)?)\s*(kg|g|克|千克)", str(spec or ""), re.IGNORECASE)
    if not match:
        return fallback
    number, unit = match.groups()
    normalized_unit = {"克": "g", "千克": "kg"}.get(unit.lower(), unit.lower())
    return f"{number} {normalized_unit}"


def render_text(elem: Mapping[str, Any], data: Mapping[str, Any]) -> str:
    """生成某一设计元素的实际打印文本。"""
    elem_type = str(elem.get("type", ""))
    value = str(elem.get("value", ""))
    label = str(elem.get("label", ""))

    if elem_type == "product_caption":
        return value or "产品名称/PRODUCT NAME"
    if elem_type == "brand":
        brand = str(data.get("brand") or value or "高原安").rstrip("®").rstrip()
        return f"{brand}®"
    if elem_type == "product_name":
        return str(data.get("product_name") or value)
    if elem_type == "spec":
        return f"• 产品规格： {data.get('spec') or value}"
    if elem_type == "shelf_life":
        return f"• 保 质 期： {data.get('shelf_life') or value}"
    if elem_type == "storage":
        return f"• 储存条件： {data.get('storage') or value}"
    if elem_type == "manufacturer":
        return f"• 生 产 商： {data.get('manufacturer') or value}"
    if elem_type == "produce_date_label":
        return value or "生产日期"
    if elem_type == "produce_date":
        return format_produce_date(str(data.get("produce_date") or value))
    if elem_type == "box_count":
        return extract_box_count(str(data.get("box_spec") or ""), value or "40")
    if elem_type == "box_unit":
        return extract_box_unit(str(data.get("box_spec") or ""), value or "盒/箱")
    if elem_type == "unit_net_weight":
        content = str(data.get("unit_net_weight") or value).strip()
        if not content:
            return ""
        if content.startswith("单盒"):
            return content
        return f"单盒净含量 {content}"
    if elem_type == "box_spec":
        return f"箱规：{data.get('box_spec') or value}"
    if elem_type.startswith("custom_"):
        return f"{label}：{value}" if label else value
    return value
