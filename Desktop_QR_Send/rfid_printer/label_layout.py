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


PROFILE_100X80 = "100x80"
PROFILE_140X120 = "140x120"
PROFILE_150X75 = "150x75"
PROFILE_210X100 = "210x100"
DEFAULT_PROFILE = PROFILE_210X100

PROFILE_ELEMENTS: Dict[str, List[Dict[str, Any]]] = {
    # 210x100 标准特大箱标版式 (100% 满幅无缝排版，整体有效绘图区域: X从 2.0mm 至 206.0mm, Y从 2.0mm 至 98.0mm)
    # 规则: 生产日期/时间/条形码右靠齐(206.0mm)；条形码尺寸适度扩大为 100x33mm；分割线从 x=2.0mm 贯穿至 206.0mm 无覆盖
    PROFILE_210X100: [
        # 1. 顶部标题与 Logo 区域 (y=2.0mm)
        _text("product_caption", "产品名称标题", "产品名称/PRODUCT NAME", 3.0, 2.0, 120.0, 6.0, 11.0, bold=False, required=True),
        _image(156.0, 2.0, 50.0, 18.0),  # 右侧品牌 Logo (右边界: 156.0 + 50.0 = 206.0mm)
        _text("product_name", "产品名称", "高原安藏式甜茶", 3.0, 9.0, 150.0, 18.0, 34.0, bold=True, color="#000000"),  # 超大产品名称 (34pt)

        # 2. 中部产品信息参数列表 (纵向延伸，宽度 135mm)
        _text("spec", "产品规格", "• 产品规格：200g (20g×10条)/盒", 3.0, 28.0, 135.0, 6.0, 12.0, bold=False),
        _text("shelf_life", "保质期", "26个月", 3.0, 35.0, 135.0, 6.0, 12.0, bold=False),
        _text("storage", "储存条件", "• 储存条件：干燥、阴凉、通风处", 3.0, 42.0, 135.0, 6.0, 12.0, bold=False),
        _text("manufacturer", "生产商", "• 生 产 商：乌兰察布蒙帝乳业有限责任公司", 3.0, 49.0, 135.0, 6.0, 12.0, bold=False),

        # 3. 中部右侧生产日期信息 (往右靠齐，与 Logo 和条形码最右边缘 206.0mm 严格对齐)
        _text("produce_date_label", "生产日期标题", "生产日期", 156.0, 34.0, 50.0, 6.0, 12.0, bold=False, required=False),
        _text("produce_date", "日期", "", 126.0, 41.0, 80.0, 12.0, 20.0, bold=False, color="#000000"),  # 日期大字 (20pt，右边界截至 206.0mm)

        # 4. 上下区域分割实线 (y=56.0mm，从左 x=2.0mm 贯穿至右 x=206.0mm，精准与条形码右边缘靠齐)
        _line(2.0, 56.0, 204.0),

        # 5. 下半部分左侧：装箱数量与单位 (纵向 y=59.0mm ~ 98.0mm)
        _text("box_count", "每箱数量", "40", 3.0, 59.0, 45.0, 32.0, 60.0, bold=False, color="#000000", template_visible=True),  # 数量霸气超大字 (60pt)
        _text("box_unit", "箱规单位", "盒/箱", 50.0, 78.0, 28.0, 8.0, 13.0, bold=False, color="#000000", template_visible=True),
        _text("unit_net_weight", "单盒净含量", "单盒净含量 200 g", 3.0, 91.0, 75.0, 7.0, 11.5, bold=False),

        # 6. 下半部分右侧：箱码条形码 (高度 38mm 宽度 115mm, x从 91.0 至 206.0mm，右边缘靠齐 206.0mm)
        _barcode(91.0, 60.0, 115.0, 38.0),

        # 7. 辅助箱规属性
        _text(
            "box_spec",
            "箱规",
            "40盒/箱",
            3.0,
            80.0,
            120.0,
            8.0,
            14.0,
            bold=True,
            enabled=True,
            type_desc="可选字段（控制左下角数量与单位）",
            print_direct=False,
        ),
    ],
}
PROFILE_ELEMENTS[PROFILE_140X120] = PROFILE_ELEMENTS[PROFILE_210X100]
PROFILE_ELEMENTS[PROFILE_150X75] = PROFILE_ELEMENTS[PROFILE_210X100]
PROFILE_ELEMENTS[PROFILE_210X100] = PROFILE_ELEMENTS[PROFILE_210X100]

def _try_load_saved_elements():
    try:
        config_file = PROJECT_ROOT / "config" / "settings.json"
        if config_file.exists():
            import json
            with open(config_file, "r", encoding="utf-8") as f:
                cfg = json.load(f)
                elems = cfg.get("layout", {}).get("elements") or cfg.get("elements")
                if elems and isinstance(elems, list) and len(elems) > 0:
                    PROFILE_ELEMENTS[DEFAULT_PROFILE] = copy.deepcopy(elems)
                    PROFILE_ELEMENTS[PROFILE_210X100] = copy.deepcopy(elems)
    except Exception:
        pass

_try_load_saved_elements()

CONTENT_FIELDS = ("label", "value", "enabled", "type_desc", "asset_path")


def profile_name_for_size(width_mm: float, height_mm: float) -> str:
    return DEFAULT_PROFILE


def default_elements(width_mm: float = 150.0, height_mm: float = 75.0) -> List[Dict[str, Any]]:
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
    """
    解析版式并采用 150x75 满幅自适应比例算法。
    自动根据目标标签尺寸 (width_mm * height_mm) 换算并拉伸坐标，
    使文字、分隔线与条形码在 150x75 标签纸上 100% 铺满延伸，消除四周非必要留白。
    """
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

    # 确定基准参考宽高 (默认按 210.0mm x 100.0mm 原始排版坐标系统进行自适应缩放)
    base_w = float(layout.get("width_mm", 210.0)) if layout and layout.get("width_mm") else 210.0
    base_h = float(layout.get("height_mm", 100.0)) if layout and layout.get("height_mm") else 100.0

    # 扩大扩展：右侧定格 148mm (留 2mm 边距)，顶部定格 1mm，底部扩展至 74mm 满幅铺满
    scale_x = width_mm / max(1.0, base_w)
    scale_y = height_mm / max(1.0, base_h)
    scale_uniform = max(scale_x, scale_y)

    # 靠右对齐的元素集合 ( Logo / 生产日期标题 / 生产日期 / 条形码 )，统一定格右边缘
    RIGHT_ALIGNED_TYPES = {"brand_logo", "produce_date_label", "produce_date", "barcode"}

    scaled_result = []

    for elem in raw_list:
        item = copy.deepcopy(elem)
        elem_type = str(item.get("type", ""))
        orig_x = float(item.get("x", 0.0))
        orig_y = float(item.get("y", 0.0))
        orig_w = float(item.get("w", 0.0))
        orig_h = float(item.get("h", 0.0))

        # 纵向与横向坐标及宽高扩大放缩计算
        item["y"] = round(orig_y * scale_y * 0.95, 2)  # 顶部向上微调 5%，填充顶部留白
        item["h"] = round(orig_h * scale_y * 1.05, 2)  # 高度扩大 5%，填充底部留白

        if elem_type in RIGHT_ALIGNED_TYPES:
            # 右对齐逻辑：根据右侧边距进行精确定局扩大
            right_offset = base_w - (orig_x + orig_w)
            scaled_w = orig_w * scale_x * 1.05  # 横向向右扩大 5%
            item["w"] = round(scaled_w, 2)
            item["x"] = round(width_mm - (right_offset * scale_x + scaled_w) + 2.0, 2)
        elif elem_type == "divider":
            right_offset = base_w - (orig_x + orig_w)
            item["x"] = round(orig_x * scale_x, 2)
            item["w"] = round(width_mm - (orig_x + right_offset) * scale_x + 2.0, 2)
            item["h"] = 0.0
        else:
            item["x"] = round(orig_x * scale_x, 2)
            item["w"] = round(orig_w * scale_x * 1.05, 2)

        # 比例变化时自动同比例扩充字号
        if "font_size" in item and scale_uniform != 1.0:
            item["font_size"] = round(float(item["font_size"]) * scale_uniform, 1)

        scaled_result.append(item)

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
        if val and val not in ("默认当天", "日期", "自由选择/默认当天") and not val.startswith("默认"):
            return val.replace("-", ".").replace("/", ".")
        d = str(preview_data.get("produce_date") or "").strip()
        if not d or d in ("默认当天", "日期"):
            d = datetime.now().strftime("%Y.%m.%d")
        return d.replace("-", ".").replace("/", ".")
    if t == "box_count":
        return str(preview_data.get("box_count") or val or "40")
    if t == "box_unit":
        return str(preview_data.get("box_unit") or val or "盒/箱")
    if t == "produce_date_label":
        if val and (val.replace(".", "").replace("-", "").replace("/", "").isdigit() or "202" in val):
            return "生产日期"
        return val or label or "生产日期"
    if t in ("product_caption", "product_name"):
        return val or label

    if t == "spec":
        clean_v = val.split("：", 1)[-1].split(":", 1)[-1].strip() if ("：" in val or ":" in val) else val
        return f"• 产品规格：{clean_v}" if clean_v else "• 产品规格：200g (20g×10条)/盒"
    if t == "shelf_life":
        clean_v = val.split("：", 1)[-1].split(":", 1)[-1].strip() if ("：" in val or ":" in val) else val
        return f"• 保 质 期：{clean_v}" if clean_v else "• 保 质 期：18个月"
    if t == "storage":
        clean_v = val.split("：", 1)[-1].split(":", 1)[-1].strip() if ("：" in val or ":" in val) else val
        return f"• 储存条件：{clean_v}" if clean_v else "• 储存条件：干燥、阴凉、通风处"
    if t == "manufacturer":
        clean_v = val.split("：", 1)[-1].split(":", 1)[-1].strip() if ("：" in val or ":" in val) else val
        return f"• 生 产 商：{clean_v}" if clean_v else "• 生 产 商：乌兰察布蒙帝乳业有限责任公司"
    if t in ("unit_net_weight", "net_weight"):
        clean_v = val
        if clean_v.startswith("单盒内容：") or clean_v.startswith("单盒内容:"):
            clean_v = clean_v.split(":", 1)[-1].split("：", 1)[-1].strip()
        return clean_v if clean_v else "单盒净含量 200 g"

    if "：" in val or ":" in val or (label and val.startswith(label)):
        return val
    if label and val and label != val:
        return f"{label}：{val}"
    return val or label
