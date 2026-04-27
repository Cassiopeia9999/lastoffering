from __future__ import annotations

from typing import Iterable


CATEGORY_ALIASES = {
    "移动电子设备": [
        "移动电子设备",
        "电子设备",
        "手机",
        "智能手机",
        "iphone",
        "安卓手机",
        "平板",
        "ipad",
        "平板电脑",
        "智能手表",
        "手表",
    ],
    "笔记本电脑": [
        "笔记本电脑",
        "笔记本",
        "电脑",
        "手提电脑",
        "laptop",
        "macbook",
    ],
    "耳机": [
        "耳机",
        "蓝牙耳机",
        "无线耳机",
        "有线耳机",
        "airpods",
        "airdots",
        "耳麦",
    ],
    "充电器/数据线": [
        "充电器/数据线",
        "充电器",
        "充电头",
        "充电线",
        "数据线",
        "充电宝",
        "移动电源",
        "电源适配器",
        "适配器",
    ],
    "包类": [
        "包类",
        "包",
        "书包",
        "背包",
        "双肩包",
        "挎包",
        "手提包",
        "斜挎包",
    ],
    "书籍": [
        "书籍",
        "书",
        "教材",
        "课本",
        "笔记本书",
        "资料",
        "讲义",
    ],
    "文具": [
        "文具",
        "笔",
        "铅笔",
        "中性笔",
        "钢笔",
        "尺子",
        "橡皮",
        "笔袋",
        "文具盒",
    ],
    "证件": [
        "证件",
        "身份证",
        "学生证",
        "校园卡",
        "一卡通",
        "饭卡",
        "银行卡",
        "卡片",
    ],
    "钥匙": [
        "钥匙",
        "钥匙串",
        "钥匙扣",
        "门钥匙",
        "宿舍钥匙",
        "车钥匙",
        "门禁卡",
    ],
    "眼镜": [
        "眼镜",
        "墨镜",
        "近视眼镜",
        "镜框",
    ],
    "饰品": [
        "饰品",
        "首饰",
        "项链",
        "戒指",
        "手链",
        "手镯",
        "耳饰",
        "耳钉",
        "挂件",
    ],
    "水杯": [
        "水杯",
        "杯子",
        "保温杯",
        "马克杯",
        "水壶",
    ],
    "雨伞": [
        "雨伞",
        "伞",
        "遮阳伞",
    ],
    "衣物": [
        "衣物",
        "衣服",
        "外套",
        "卫衣",
        "校服",
        "衬衫",
        "裤子",
        "帽子",
        "围巾",
    ],
    "其他": [
        "其他",
    ],
}

COLOR_ALIASES = {
    "黑色": ["黑色", "纯黑", "深黑", "黑"],
    "白色": ["白色", "米白", "乳白", "象牙白", "白"],
    "蓝色": ["蓝色", "深蓝", "浅蓝", "天蓝", "青色", "藏蓝", "湖蓝"],
    "红色": ["红色", "大红", "深红", "酒红", "玫红"],
    "绿色": ["绿色", "墨绿", "浅绿", "草绿"],
    "黄色": ["黄色", "土黄", "鹅黄", "卡其"],
    "灰色": ["灰色", "深灰", "浅灰", "银灰"],
    "银色": ["银色", "银白", "金属银"],
    "金色": ["金色", "香槟金", "玫瑰金"],
    "紫色": ["紫色", "淡紫"],
    "粉色": ["粉色", "粉红", "浅粉"],
    "橙色": ["橙色", "橘色"],
    "棕色": ["棕色", "咖色", "咖啡色", "褐色"],
}

BRAND_ALIASES = {
    "小米": ["小米", "xiaomi", "mi"],
    "红米": ["红米", "redmi"],
    "华为": ["华为", "huawei"],
    "荣耀": ["荣耀", "honor"],
    "苹果": ["苹果", "apple", "iphone", "ipad", "macbook", "airpods"],
    "vivo": ["vivo"],
    "iQOO": ["iqoo", "i-qoo", "艾酷"],
    "OPPO": ["oppo"],
    "realme": ["realme", "真我"],
    "一加": ["一加", "oneplus", "1+"],
    "联想": ["联想", "lenovo"],
    "戴尔": ["戴尔", "dell"],
    "惠普": ["惠普", "hp"],
    "华硕": ["华硕", "asus"],
    "三星": ["三星", "samsung"],
    "索尼": ["索尼", "sony"],
}

BRAND_FAMILIES = {
    "小米系": ["小米", "红米"],
    "华为系": ["华为", "荣耀"],
    "vivo系": ["vivo", "iQOO"],
    "OPPO系": ["OPPO", "realme", "一加"],
    "苹果系": ["苹果"],
}

LOCATION_ALIASES = {
    "教学楼": [
        "教学楼", "教室", "课堂", "讲堂", "教学区", "教学楼下",
        "一教", "二教", "三教", "四教", "五教", "六教", "七教",
        "主教", "逸夫楼", "综合楼",
    ],
    "图书馆": [
        "图书馆", "阅览室", "借阅区", "自习区", "馆内", "图书馆大厅",
        "图书馆门口", "图书馆一楼", "图书馆二楼", "图书馆三楼",
    ],
    "宿舍": [
        "宿舍", "寝室", "公寓", "宿舍楼", "宿舍区", "寝室楼",
        "宿舍门口", "楼道", "寝室楼下",
        "竹园", "梅园", "兰园", "菊园", "荷园", "桂园",
        "竹园宿舍", "梅园宿舍", "兰园宿舍", "公寓区",
    ],
    "食堂": [
        "食堂", "餐厅", "饭堂", "一食堂", "二食堂", "三食堂",
        "四食堂", "清真食堂", "老食堂", "新食堂",
        "食堂门口", "窗口", "餐盘回收处", "美食城",
    ],
    "操场": [
        "操场", "田径场", "体育场", "第一田径场", "第二田径场",
        "一田", "二田", "运动场", "跑道", "看台", "主席台",
        "篮球场", "羽毛球场", "乒乓球场", "排球场", "网球场",
        "体育馆", "球场", "健身区",
    ],
    "实验室": [
        "实验室", "实验楼", "机房", "计算机房", "电子实验室",
        "实训室", "工作室", "信达楼", "气象楼",
    ],
    "快递站": [
        "快递站", "驿站", "菜鸟驿站", "快递点", "取件点",
        "收发室", "快递柜",
    ],
    "校门": [
        "校门", "正门", "东门", "西门", "南门", "北门", "门口",
        "校门口", "大门口", "门卫处",
    ],
    "大厅": [
        "大厅", "大堂", "门厅", "前厅", "中庭",
    ],
    "商业区": [
        "天猫超市", "超市", "便利店", "小卖部", "商业街",
        "奶茶店", "水果店",
    ],
    "广场": [
        "小罗马广场", "广场", "中心广场", "下沉广场",
    ],
    "道路": [
        "银杏大道", "大道", "林荫道", "主干道", "校道",
    ],
}


def normalize_text(value: str | None) -> str:
    return (value or "").strip().lower()


def _normalize_alias_map(alias_map: dict[str, list[str]]) -> dict[str, list[str]]:
    return {
        canonical: list(dict.fromkeys([normalize_text(canonical), *[normalize_text(item) for item in aliases]]))
        for canonical, aliases in alias_map.items()
    }


_CATEGORY_ALIASES = _normalize_alias_map(CATEGORY_ALIASES)
_COLOR_ALIASES = _normalize_alias_map(COLOR_ALIASES)
_BRAND_ALIASES = _normalize_alias_map(BRAND_ALIASES)
_LOCATION_ALIASES = _normalize_alias_map(LOCATION_ALIASES)


def _build_alias_lookup(alias_map: dict[str, list[str]]) -> dict[str, str]:
    lookup: dict[str, str] = {}
    for canonical, aliases in alias_map.items():
        for alias in aliases:
            lookup[alias] = canonical
    return lookup


_CATEGORY_LOOKUP = _build_alias_lookup(_CATEGORY_ALIASES)
_COLOR_LOOKUP = _build_alias_lookup(_COLOR_ALIASES)
_BRAND_LOOKUP = _build_alias_lookup(_BRAND_ALIASES)
_LOCATION_LOOKUP = _build_alias_lookup(_LOCATION_ALIASES)

_BRAND_TO_FAMILY = {
    brand: family
    for family, brands in BRAND_FAMILIES.items()
    for brand in brands
}


def unique_strings(values: Iterable[str | None]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        if not value:
            continue
        text = str(value).strip()
        if not text:
            continue
        key = normalize_text(text)
        if key in seen:
            continue
        seen.add(key)
        result.append(text)
    return result


def _normalize_by_lookup(value: str | None, alias_map: dict[str, list[str]], alias_lookup: dict[str, str]) -> str | None:
    text = normalize_text(value)
    if not text:
        return None
    if text in alias_lookup:
        return alias_lookup[text]
    for alias, canonical in alias_lookup.items():
        if alias and alias in text:
            return canonical
    for canonical, aliases in alias_map.items():
        if any(text in alias or alias in text for alias in aliases):
            return canonical
    return str(value).strip() or None


def normalize_category(value: str | None) -> str | None:
    return _normalize_by_lookup(value, _CATEGORY_ALIASES, _CATEGORY_LOOKUP)


def normalize_color(value: str | None) -> str | None:
    return _normalize_by_lookup(value, _COLOR_ALIASES, _COLOR_LOOKUP)


def normalize_brand(value: str | None) -> str | None:
    return _normalize_by_lookup(value, _BRAND_ALIASES, _BRAND_LOOKUP)


def normalize_location(value: str | None) -> str | None:
    return _normalize_by_lookup(value, _LOCATION_ALIASES, _LOCATION_LOOKUP)


def expand_category_terms(value: str | None) -> list[str]:
    canonical = normalize_category(value)
    if not canonical:
        return []
    return unique_strings([canonical, *CATEGORY_ALIASES.get(canonical, [])])


def expand_color_terms(value: str | None) -> list[str]:
    canonical = normalize_color(value)
    if not canonical:
        return []
    return unique_strings([canonical, *COLOR_ALIASES.get(canonical, [])])


def expand_brand_terms(value: str | None) -> list[str]:
    canonical = normalize_brand(value)
    if not canonical:
        return []
    terms = [canonical, *BRAND_ALIASES.get(canonical, [])]
    family = brand_family_of(canonical)
    if family:
        terms.extend(BRAND_FAMILIES.get(family, []))
    return unique_strings(terms)


def expand_location_terms(value: str | None) -> list[str]:
    canonical = normalize_location(value)
    if not canonical:
        return []
    return unique_strings([canonical, *LOCATION_ALIASES.get(canonical, [])])


def brand_family_of(value: str | None) -> str | None:
    brand = normalize_brand(value)
    if not brand:
        return None
    return _BRAND_TO_FAMILY.get(brand)


def same_brand_family(left: str | None, right: str | None) -> bool:
    left_family = brand_family_of(left)
    right_family = brand_family_of(right)
    return bool(left_family and right_family and left_family == right_family)


def semantic_equal(left: str | None, right: str | None, field_type: str) -> bool:
    if field_type == "category":
        return normalize_category(left) == normalize_category(right) and bool(normalize_category(left))
    if field_type == "color":
        return normalize_color(left) == normalize_color(right) and bool(normalize_color(left))
    if field_type == "brand":
        return normalize_brand(left) == normalize_brand(right) and bool(normalize_brand(left))
    if field_type == "location":
        return normalize_location(left) == normalize_location(right) and bool(normalize_location(left))
    return normalize_text(left) == normalize_text(right) and bool(normalize_text(left))


def semantic_contains(query: str | None, values: Iterable[str | None], field_type: str) -> tuple[bool, str | None]:
    if field_type == "category":
        terms = expand_category_terms(query)
        canonical = normalize_category(query)
    elif field_type == "color":
        terms = expand_color_terms(query)
        canonical = normalize_color(query)
    elif field_type == "brand":
        terms = expand_brand_terms(query)
        canonical = normalize_brand(query)
    elif field_type == "location":
        terms = expand_location_terms(query)
        canonical = normalize_location(query)
    else:
        terms = unique_strings([query])
        canonical = query

    if not terms:
        return False, None

    normalized_values = [normalize_text(value) for value in values if normalize_text(value)]
    if not normalized_values:
        return False, canonical

    for term in terms:
        normalized_term = normalize_text(term)
        if any(normalized_term in value for value in normalized_values):
            return True, canonical or term

    if field_type == "location" and canonical:
        normalized_canonical = normalize_text(canonical)
        for value in normalized_values:
            if normalized_canonical and (normalized_canonical in value or value in normalized_canonical):
                return True, canonical

    return False, canonical


def normalize_keyword(value: str | None) -> str | None:
    text = (value or "").strip()
    if not text:
        return None

    for normalizer in (normalize_category, normalize_color, normalize_brand, normalize_location):
        normalized = normalizer(text)
        if normalized and normalize_text(normalized) != normalize_text(text):
            return normalized
    return text


def normalize_keywords(values: Iterable[str | None]) -> list[str]:
    return unique_strings(normalize_keyword(value) for value in values)


def semantic_keyword_overlap(source: Iterable[str] | None, target: Iterable[str] | None) -> tuple[float, list[str]]:
    source_terms = {normalize_text(item) for item in normalize_keywords(source or []) if normalize_text(item)}
    target_terms = {normalize_text(item) for item in normalize_keywords(target or []) if normalize_text(item)}
    if not source_terms or not target_terms:
        return 0.0, []
    union = source_terms | target_terms
    shared = source_terms & target_terms
    if not union:
        return 0.0, []
    return len(shared) / len(union), sorted(shared)
