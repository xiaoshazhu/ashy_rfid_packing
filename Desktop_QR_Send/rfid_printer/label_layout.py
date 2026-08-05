"""箱码标签的版式配置与文本解析。

坐标、宽高均使用毫米，字号使用磅。打印机为单色热敏设备，配置中的颜色
主要用于屏幕/PDF预览；实际打印统一转换为黑色，浅灰分隔线使用 1 像素细线。
"""

from __future__ import annotations

import copy
import os
import re
from datetime import datetime
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
        "type_desc": "Logo图片（支持更换）",
        "x": x,
        "y": y,
        "w": w,
        "h": h,
        "color": "#000000",
        "required": False,
        "template_visible": True,
    }


PROFILE_140X120 = "140x120"
DEFAULT_PROFILE = PROFILE_140X120

PROFILE_ELEMENTS: Dict[str, List[Dict[str, Any]]] = {
    # 140x120 基准版式 (40 与 盒/箱 紧密贴合位于 x=6.0 和 x=28.0)
    PROFILE_140X120: [
        _text("product_caption", "产品名称标题", "产品名称/PRODUCT NAME", 6.0, 6.0, 95.0, 6.0, 12.0, bold=True, required=True),
        _image(108.0, 5.0, 26.0, 12.0),
        _text("product_name", "产品名称", "高原安藏式甜茶", 6.0, 14.0, 128.0, 16.0, 32.0, bold=True, color="#000000"),
        _text("spec", "产品规格", "200g (20g×10条)/盒", 6.0, 33.0, 98.0, 6.5, 14.0, bold=True),
        _text("shelf_life", "保质期", "18个月", 6.0, 41.0, 98.0, 6.5, 14.0, bold=True),
        _text("storage", "储存条件", "干燥、阴凉、通风处", 6.0, 49.0, 98.0, 6.5, 14.0, bold=True),
        _text("manufacturer", "生产商", "乌兰察布蒙帝乳业有限责任公司", 6.0, 57.0, 98.0, 6.5, 13.0, bold=True),
        _text("produce_date_label", "生产日期标题", "生产日期", 114.0, 36.0, 20.0, 6.0, 13.0, bold=True, required=False),
        _text("produce_date", "日期", "", 110.0, 44.0, 24.0, 10.0, 13.0, bold=True, color="#000000"),
        _line(6.0, 66.0, 128.0),
        _text("box_count", "每箱数量", "40", 6.0, 68.0, 22.0, 20.0, 48.0, bold=True, color="#000000", template_visible=False),
        _text("box_unit", "箱规单位", "盒/箱", 28.0, 80.0, 16.0, 6.0, 13.0, bold=True, color="#000000", template_visible=False),
        _text("unit_net_weight", "单盒内容", "单盒净含量 200 g", 6.0, 94.0, 54.0, 6.0, 12.0, bold=True),
        _barcode(60.0, 68.0, 72.0, 30.0),
        _text(
            "box_spec",
            "箱规",
            "40盒/箱",
            6.0,
            62.0,
            98.0,
            6.0,
            13.0,
            bold=True,
            enabled=True,
            type_desc="可选字段（控制左下角数量与单位）",
            print_direct=False,
        ),
    ],
}

CONTENT_FIELDS = ("label", "value", "enabled", "type_desc", "asset_path")


def profile_name_for_size(width_mm: float, height_mm: float) -> str:
    return DEFAULT_PROFILE


def default_elements(width_mm: float = 140.0, height_mm: float = 120.0) -> List[Dict[str, Any]]:
    return copy.deepcopy(PROFILE_ELEMENTS[DEFAULT_PROFILE])


def merge_content(
    base_elements: Iterable[Mapping[str, Any]],
    content_elements: Iterable[Mapping[str, Any]],
) -> List[Dict[str, Any]]:
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
    """解析版式并采用左右锚定 + 比例统一算法，防止宽x高切换时元素错位与【40与盒/箱离老远】的问题！"""
    layout = layout or {}
    base = copy.deepcopy(PROFILE_ELEMENTS[DEFAULT_PROFILE])
    stored = list(layout.get("elements", []) or [])

    if stored:
        defaults_by_type = {
            str(item.get("type")): item for item in base if item.get("type")
        }
        raw_list = []
        for stored_item in stored:
            elem_type = str(stored_item.get("type", ""))
            item = copy.deepcopy(defaults_by_type.get(elem_type, {}))
            item.update(copy.deepcopy(stored_item))
            raw_list.append(item)
    else:
        raw_list = base

    base_w, base_h = 140.0, 120.0
    scale_uniform = min(width_mm / base_w, height_mm / base_h)
    scale_x = width_mm / base_w
    scale_y = height_mm / base_h

    RIGHT_ALIGNED_TYPES = {"brand_logo", "produce_date_label", "produce_date", "barcode"}

    scaled_result = []
    box_count_item = None

    for elem in raw_list:
        item = copy.deepcopy(elem)
        elem_type = str(item.get("type", ""))
        orig_x = float(item.get("x", 0.0))
        orig_y = float(item.get("y", 0.0))
        orig_w = float(item.get("w", 0.0))
        orig_h = float(item.get("h", 0.0))

        item["y"] = round(orig_y * scale_y, 2)
        item["h"] = round(orig_h * scale_y, 2)

        if elem_type in RIGHT_ALIGNED_TYPES:
            right_offset = base_w - (orig_x + orig_w)
            scaled_w = orig_w * scale_uniform
            item["w"] = round(scaled_w, 2)
            item["x"] = round(width_mm - (right_offset * scale_x + scaled_w), 2)
        elif elem_type == "divider":
            item["x"] = round(orig_x * scale_x, 2)
            item["w"] = round(width_mm - 2 * (orig_x * scale_x), 2)
        elif elem_type == "box_count":
            item["x"] = round(orig_x * scale_uniform, 2)
            item["w"] = round(max(orig_w, 48.0) * scale_uniform, 2)
        elif elem_type == "box_unit" and box_count_item:
            # 根据每箱数量(box_count)字符长度，智能计算【盒/箱】的起始 X 坐标，完全避免重叠！
            bc_str = render_text(box_count_item, layout.get("preview_data", {}) if layout else {})
            digit_count = max(1, len(str(bc_str).strip()))
            # 每个数字字符在 48pt 大字号下约占用 11.5mm 宽度
            dynamic_offset = max(22.0, digit_count * 11.5)
            item["w"] = round(orig_w * scale_uniform, 2)
            item["x"] = round(box_count_item["x"] + dynamic_offset * scale_uniform, 2)
            item["y"] = round(box_count_item["y"] + 14.0 * scale_y, 2)
        elif elem_type in ("unit_net_weight", "net_weight"):
            item["x"] = round(orig_x * scale_uniform, 2)
            item["w"] = round(max(55.0 * scale_x, width_mm * 0.48), 2)
        else:
            item["x"] = round(orig_x * scale_uniform, 2)
            item["w"] = round(orig_w * scale_uniform, 2)

        if "font_size" in item:
            item["font_size"] = round(float(item["font_size"]) * scale_uniform, 1)

        if elem_type == "box_count":
            box_count_item = item

        scaled_result.append(item)

    # 动态纵向自适应紧密排版：序号 3(spec), 4(shelf_life), 储存条件, 5(manufacturer)
    # 无论勾选哪几个，可见字段自动按合适间距紧密均匀排列，彻底解决 3,4,5 离老远的问题！
    MIDDLE_STACK_TYPES = ["spec", "shelf_life", "storage", "manufacturer"]
    visible_stack = [item for item in scaled_result if str(item.get("type")) in MIDDLE_STACK_TYPES and item.get("enabled", True)]
    if visible_stack:
        aspect = width_mm / max(1.0, height_mm)
        y_start = 24.0 * scale_y if aspect >= 1.4 else 30.0 * scale_y
        y_step = 7.0 * scale_y if aspect >= 1.4 else 8.5 * scale_y
        for idx, item in enumerate(visible_stack):
            item["y"] = round(y_start + idx * y_step, 2)

    return scaled_result


def is_required_element(elem: Mapping[str, Any]) -> bool:
    return str(elem.get("type")) in REQUIRED_ELEMENT_TYPES or bool(elem.get("required"))


def is_template_visible(elem: Mapping[str, Any]) -> bool:
    return bool(elem.get("template_visible", True))


def resolve_asset_path(asset_path: str) -> str:
    path_str = str(asset_path or LOGO_ASSET)
    if os.path.isabs(path_str) and os.path.exists(path_str):
        return path_str
    candidate = PROJECT_ROOT / path_str
    if candidate.exists():
        return str(candidate)
    return str(PROJECT_ROOT / LOGO_ASSET)


def render_text(elem: Mapping[str, Any], preview_data: Mapping[str, Any]) -> str:
    t = str(elem.get("type", ""))
    label = str(elem.get("label", "") or "").strip()
    val = str(elem.get("value", "") or "").strip()

    if t == "produce_date":
        d = str(preview_data.get("produce_date") or val or "").strip()
        if not d or d in ("默认当天", "日期"):
            d = datetime.now().strftime("%Y.%m.%d")
        return d.replace("-", ".").replace("/", ".")
    if t == "box_count":
        return str(preview_data.get("box_count") or val or "40")
    if t == "box_unit":
        return str(preview_data.get("box_unit") or val or "盒/箱")
    if t in ("product_caption", "product_name", "produce_date_label"):
        return val or label

    if "：" in val or ":" in val or (label and val.startswith(label)):
        return val
    if label and val and label != val:
        return f"{label}：{val}"
    return val or label
