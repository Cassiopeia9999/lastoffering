import re
from typing import Any

import requests
import urllib3

from backend.app.core.config import settings
from backend.app.models.item import ITEM_CATEGORIES
from backend.app.services.local_nlp import extract_feature_phrases, tokenize_text
from backend.app.services.semantic_rules import (
    BRAND_ALIASES,
    CATEGORY_ALIASES,
    COLOR_ALIASES,
    LOCATION_ALIASES,
    normalize_brand,
    normalize_category,
    normalize_color,
    normalize_keywords,
    normalize_location,
)

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

COLOR_WORDS = [item for aliases in COLOR_ALIASES.values() for item in aliases]
BRAND_WORDS = [item for aliases in BRAND_ALIASES.values() for item in aliases]
CATEGORY_KEYWORDS = {
    canonical: aliases
    for canonical, aliases in CATEGORY_ALIASES.items()
    if canonical != "其他"
}
LOCATION_HINTS = [item for aliases in LOCATION_ALIASES.values() for item in aliases]


def has_ark_config() -> bool:
    return bool(settings.ARK_API_KEY and settings.ARK_ENDPOINT_ID)


def call_ark_chat(messages: list[dict[str, Any]], temperature: float = 0.2, max_tokens: int = 600) -> str:
    if not has_ark_config():
        raise RuntimeError("ARK_API_KEY or ARK_ENDPOINT_ID is not configured")

    print(
        f"[ARK AI] requesting model={settings.ARK_ENDPOINT_ID}, "
        f"temperature={temperature}, max_tokens={max_tokens}"
    )
    session = requests.Session()
    session.verify = False
    response = session.post(
        f"{settings.ARK_BASE_URL.rstrip('/')}/chat/completions",
        headers={
            "Authorization": f"Bearer {settings.ARK_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": settings.ARK_ENDPOINT_ID,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        },
        timeout=60,
    )
    response.raise_for_status()
    result = response.json()
    content = result["choices"][0]["message"]["content"].strip()
    print(f"[ARK AI] response received, length={len(content)}")
    return content


def normalize_string_list(values: Any) -> list[str]:
    if values is None:
        return []
    if isinstance(values, str):
        values = re.split(r"[，、；;。\s]+", values)
    return normalize_keywords(values)


def infer_category(message: str) -> str | None:
    lowered = message.lower()
    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(keyword.lower() in lowered for keyword in keywords):
            return category
    return next((name for name in ITEM_CATEGORIES if name in message), None)


def infer_location(message: str) -> str | None:
    for hint in LOCATION_HINTS:
        if hint in message:
            return normalize_location(hint)
    return None


def infer_precise_location(message: str) -> str | None:
    patterns = [
        r"教室\d{3,4}",
        r"教学楼\d{3,4}",
        r"[东南西北一二三四五六七八九十\d]+教\d{3,4}",
        r"图书馆[一二三四五六七八九十\d]+楼",
        r"宿舍\d+[栋舍楼]?\d*",
        r"(竹园|梅园|兰园|菊园|荷园|桂园)[^\s，。；,;]{0,10}",
        r"(一食堂|二食堂|三食堂|四食堂|老食堂|新食堂|清真食堂)",
        r"(小罗马广场|银杏大道|天猫超市|信达楼|气象楼)",
        r"(第一田径场|第二田径场|一田|二田|篮球场|羽毛球场|乒乓球场|排球场|网球场|体育馆)",
    ]
    for pattern in patterns:
        match = re.search(pattern, message)
        if match:
            return match.group(0)
    return None


def extract_explicit_locations(message: str) -> list[str]:
    found: list[tuple[int, str]] = []
    for aliases in LOCATION_ALIASES.values():
        for alias in aliases:
            index = message.find(alias)
            if index >= 0:
                found.append((index, alias))

    precise_patterns = [
        r"教室\d{3,4}",
        r"教学楼\d{3,4}",
        r"[东南西北一二三四五六七八九十\d]+教\d{3,4}",
        r"图书馆[一二三四五六七八九十\d]+楼",
        r"宿舍\d+[栋舍楼]?\d*",
    ]
    for pattern in precise_patterns:
        for match in re.finditer(pattern, message):
            found.append((match.start(), match.group(0)))

    found.sort(key=lambda item: item[0])
    result: list[str] = []
    for _, token in found:
        if token not in result:
            result.append(token)

    compacted: list[str] = []
    for token in result:
        if any(token != other and token in other for other in result):
            continue
        compacted.append(token)
    return compacted[:3]


def normalize_location_group(raw_location: str | None) -> str | None:
    if not raw_location:
        return None
    normalized: list[str] = []
    for part in [segment.strip() for segment in raw_location.split("、") if segment.strip()]:
        canonical = normalize_location(part)
        if canonical and canonical not in normalized:
            normalized.append(canonical)
    return "、".join(normalized) if normalized else None


def infer_brand(message: str) -> str | None:
    lowered = message.lower()
    for brand in BRAND_WORDS:
        if brand.lower() in lowered:
            return normalize_brand(brand)
    return None


def infer_color(message: str) -> str | None:
    for color in COLOR_WORDS:
        if color in message:
            return normalize_color(color)
    return None


def heuristic_extract_filters(message: str) -> dict[str, Any]:
    intent = "unknown"
    if any(token in message for token in ["丢了", "遗失", "找不到", "丢失"]):
        intent = "lost"
    elif any(token in message for token in ["捡到", "拾到", "招领", "捡了"]):
        intent = "found"

    token_keywords = tokenize_text(message)
    feature_phrases = extract_feature_phrases(message)

    category = infer_category(message)
    brand = infer_brand(message)
    color = infer_color(message)
    raw_locations = extract_explicit_locations(message)
    raw_location = "、".join(raw_locations) if raw_locations else infer_precise_location(message)
    normalized_location = normalize_location_group(raw_location) if raw_location else infer_location(message)

    return {
        "intent": intent,
        "category": category,
        "color": color,
        "brand": brand,
        "location": raw_location or normalized_location,
        "raw_location": raw_location,
        "normalized_location": normalized_location,
        "keywords": normalize_keywords(
            [brand, color, raw_location, normalized_location, category, *token_keywords, *feature_phrases]
        )[:10],
        "title_keywords": normalize_keywords([brand, category, *token_keywords[:3]])[:5],
        "feature_text": "、".join(feature_phrases) if feature_phrases else message[:80],
    }


def _coerce_null(value: Any) -> Any:
    if value is None:
        return None
    text = str(value).strip()
    if not text or text.lower() in {"null", "none", "unknown", "未知", "无"}:
        return None
    return text


def _extract_value(patterns: list[str], text: str) -> str | None:
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            value = match.group(1).strip(" ：:，,。；;")
            if value:
                return value
    return None


def parse_chat_extract_response(raw_text: str) -> dict[str, Any]:
    text = raw_text.strip()
    return {
        "intent": _extract_value(
            [
                r"(?:意图|类型|状态)\s*[:：]\s*([^\n]+)",
                r"(丢失|招领|拾到|捡到)",
            ],
            text,
        ),
        "category": _extract_value([r"(?:类别|物品类别)\s*[:：]\s*([^\n]+)"], text),
        "color": _extract_value([r"(?:颜色|色彩)\s*[:：]\s*([^\n]+)"], text),
        "brand": _extract_value([r"(?:品牌)\s*[:：]\s*([^\n]+)"], text),
        "location": _extract_value([r"(?:地点|位置)\s*[:：]\s*([^\n]+)"], text),
        "keywords": _extract_value([r"(?:关键词|关键字)\s*[:：]\s*([^\n]+)"], text),
        "feature_text": _extract_value([r"(?:典型特征|特征摘要|特征)\s*[:：]\s*([^\n]+)"], text),
    }


def _normalize_filter_payload(data: dict[str, Any], source: str, original_message: str) -> dict[str, Any]:
    raw_location = _coerce_null(data.get("location")) or None
    explicit_locations = extract_explicit_locations(original_message)
    precise_location = "、".join(explicit_locations) if explicit_locations else infer_precise_location(original_message)
    if precise_location:
        raw_location = precise_location

    normalized_location = normalize_location_group(raw_location) or infer_location(original_message)
    category = normalize_category(_coerce_null(data.get("category"))) or infer_category(original_message)
    color = normalize_color(_coerce_null(data.get("color"))) or infer_color(original_message)
    brand = normalize_brand(_coerce_null(data.get("brand"))) or infer_brand(original_message)
    keywords = normalize_string_list(_coerce_null(data.get("keywords")))
    feature_text = (_coerce_null(data.get("feature_text")) or "").strip()
    if not feature_text:
        fallback_features = extract_feature_phrases(original_message)
        feature_text = "、".join(fallback_features) if fallback_features else original_message[:80]

    raw_intent = _coerce_null(data.get("intent")) or ""
    if raw_intent in {"丢失", "lost"}:
        intent = "lost"
    elif raw_intent in {"招领", "拾到", "捡到", "found"}:
        intent = "found"
    else:
        intent = heuristic_extract_filters(original_message)["intent"]

    normalized = {
        "source": source,
        "intent": intent,
        "category": category or None,
        "color": color or None,
        "brand": brand or None,
        "location": raw_location or normalized_location,
        "raw_location": raw_location,
        "normalized_location": normalized_location,
        "keywords": normalize_keywords(
            [category, color, brand, raw_location, normalized_location, *keywords, *tokenize_text(original_message)]
        )[:10],
        "title_keywords": normalize_keywords([brand, category, *keywords[:3]])[:5],
        "feature_text": feature_text,
    }
    return normalized


def build_search_chat_prompt(message: str) -> list[dict[str, str]]:
    system_prompt = (
        "你是校园失物招领系统的 AI 助手。"
        "用户会先自然描述丢失或捡到的物品。"
        "你先像正常聊天一样理解这句话，然后顺手把关键线索说出来。"
        "回答尽量简短，自然一点，不要 JSON。"
    )
    user_prompt = f"""
这是用户的话：
{message}

请你直接给出一小段自然中文回答，但尽量把下面这些线索带出来：
- 意图（丢失/招领）
- 类别
- 颜色
- 品牌
- 地点
- 关键词
- 典型特征

你可以自然表达，也可以写成这种轻量格式中的任意一种：
意图：...
类别：...
颜色：...
品牌：...
地点：...
关键词：...
典型特征：...

不要输出 JSON。
"""
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]


def extract_item_search_filters(message: str) -> dict[str, Any]:
    try:
        raw_text = call_ark_chat(
            build_search_chat_prompt(message),
            temperature=0.2,
            max_tokens=220,
        )
        data = parse_chat_extract_response(raw_text)
        source = "ark"
    except Exception as exc:
        print(f"[ARK AI] filter extraction fallback: {exc}")
        data = heuristic_extract_filters(message)
        source = "fallback"
    return _normalize_filter_payload(data, source, message)


def extract_item_search_filters_fast(message: str) -> dict[str, Any]:
    return heuristic_extract_filters(message) | {"source": "local"}


def build_quick_publish_chat_prompt(message: str, item_type: str | None) -> list[dict[str, str]]:
    system_prompt = (
        "你是校园失物招领系统的 AI 助手。"
        "用户会自然描述想发布的失物或招领信息。"
        "你先理解内容，再用简短自然的话把发布表单里会用到的关键信息说出来。"
        "不要 JSON。"
    )
    user_prompt = f"""
这是用户的话：
{message}

当前意图参考：{item_type or "unknown"}

请尽量在回答里带出这些信息：
- 类型（lost/found）
- 标题
- 类别
- 颜色
- 品牌
- 地点
- 关键词
- 典型特征
- 描述

可以自然表达，也可以轻量写成：
类型：...
标题：...
类别：...
颜色：...
品牌：...
地点：...
关键词：...
典型特征：...
描述：...

不要输出 JSON。
"""
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]


def parse_quick_publish_chat_response(raw_text: str) -> dict[str, Any]:
    text = raw_text.strip()
    return {
        "type": _extract_value([r"(?:类型|意图)\s*[:：]\s*([^\n]+)"], text),
        "title": _extract_value([r"(?:标题)\s*[:：]\s*([^\n]+)"], text),
        "category": _extract_value([r"(?:类别|物品类别)\s*[:：]\s*([^\n]+)"], text),
        "color": _extract_value([r"(?:颜色)\s*[:：]\s*([^\n]+)"], text),
        "brand": _extract_value([r"(?:品牌)\s*[:：]\s*([^\n]+)"], text),
        "location": _extract_value([r"(?:地点|位置)\s*[:：]\s*([^\n]+)"], text),
        "keywords": _extract_value([r"(?:关键词|关键字)\s*[:：]\s*([^\n]+)"], text),
        "feature_text": _extract_value([r"(?:典型特征|特征)\s*[:：]\s*([^\n]+)"], text),
        "description": _extract_value([r"(?:描述)\s*[:：]\s*([^\n]+)"], text),
    }


def extract_quick_publish_fields(message: str, item_type: str | None = None) -> dict[str, Any]:
    try:
        raw_text = call_ark_chat(
            build_quick_publish_chat_prompt(message, item_type),
            temperature=0.2,
            max_tokens=260,
        )
        data = parse_quick_publish_chat_response(raw_text)
        source = "ark"
    except Exception as exc:
        print(f"[ARK AI] quick publish fallback: {exc}")
        fallback = heuristic_extract_filters(message)
        inferred_type = item_type or fallback.get("intent") or "unknown"
        title_parts = [fallback.get("brand"), fallback.get("color")]
        if fallback.get("category"):
            title_parts.append(fallback["category"])
        title = "".join([part for part in title_parts if part]) or message[:16]
        description_parts = [message.strip()]
        if fallback.get("location"):
            description_parts.append(f"地点：{fallback['location']}")
        data = {
            "type": inferred_type,
            "title": title,
            "category": fallback.get("category"),
            "color": fallback.get("color"),
            "brand": fallback.get("brand"),
            "location": fallback.get("location"),
            "keywords": "，".join(fallback.get("keywords", [])),
            "feature_text": fallback.get("feature_text", ""),
            "description": "；".join([part for part in description_parts if part]),
        }
        source = "fallback"

    raw_type = _coerce_null(data.get("type")) or item_type or "unknown"
    if raw_type in {"丢失", "lost"}:
        parsed_type = "lost"
    elif raw_type in {"招领", "拾到", "捡到", "found"}:
        parsed_type = "found"
    else:
        parsed_type = item_type or "lost"

    category = normalize_category(_coerce_null(data.get("category"))) or infer_category(message)
    color = normalize_color(_coerce_null(data.get("color"))) or infer_color(message)
    brand = normalize_brand(_coerce_null(data.get("brand"))) or infer_brand(message)
    raw_location = (
        ("、".join(extract_explicit_locations(message)) or infer_precise_location(message))
        or _coerce_null(data.get("location"))
        or None
    )
    normalized_location = normalize_location_group(raw_location) or infer_location(message)
    location = raw_location or normalized_location
    keywords = normalize_keywords(
        [
            category,
            color,
            brand,
            raw_location,
            normalized_location,
            *normalize_string_list(_coerce_null(data.get("keywords"))),
            *tokenize_text(message),
            *extract_feature_phrases(message),
        ]
    )[:10]

    feature_phrases = extract_feature_phrases(message)
    fallback_feature_text = "、".join(feature_phrases) if feature_phrases else message[:80]

    return {
        "source": source,
        "type": parsed_type,
        "title": (_coerce_null(data.get("title")) or message[:20]).strip(),
        "category": category or None,
        "color": color or None,
        "brand": brand or None,
        "location": location or None,
        "raw_location": raw_location,
        "normalized_location": normalized_location,
        "keywords": keywords,
        "feature_text": (_coerce_null(data.get("feature_text")) or "").strip() or fallback_feature_text,
        "description": (_coerce_null(data.get("description")) or message).strip(),
    }


def extract_quick_publish_fields_fast(message: str, item_type: str | None = None) -> dict[str, Any]:
    fallback = heuristic_extract_filters(message)
    inferred_type = item_type or fallback.get("intent") or "lost"
    if inferred_type not in ("lost", "found"):
        inferred_type = "lost"

    title_parts = [fallback.get("brand"), fallback.get("color")]
    if fallback.get("category"):
        title_parts.append(fallback["category"])
    title = "".join([part for part in title_parts if part]) or message[:16]

    return {
        "source": "local",
        "type": inferred_type,
        "title": title,
        "category": fallback.get("category"),
        "color": fallback.get("color"),
        "brand": fallback.get("brand"),
        "location": fallback.get("location"),
        "raw_location": fallback.get("raw_location"),
        "normalized_location": fallback.get("normalized_location"),
        "keywords": fallback.get("keywords", []),
        "feature_text": fallback.get("feature_text", "") or "、".join(extract_feature_phrases(message)),
        "description": message.strip(),
    }
