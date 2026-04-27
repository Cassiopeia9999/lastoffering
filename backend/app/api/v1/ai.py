from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.app.core.deps import get_current_user, get_db
from backend.app.models.item import Item
from backend.app.models.user import User
from backend.app.schemas.item import ItemOut
from backend.app.services.ark_ai import (
    extract_item_search_filters,
    extract_item_search_filters_fast,
    extract_quick_publish_fields,
    extract_quick_publish_fields_fast,
)
from backend.app.services.local_nlp import BM25Document, bm25_score, normalize_bm25_scores, tokenize_text
from backend.app.services.semantic_rules import (
    normalize_brand,
    normalize_category,
    normalize_color,
    normalize_keywords,
    normalize_location,
    normalize_text,
    same_brand_family,
    semantic_contains,
)

router = APIRouter()


class AssistantSearchRequest(BaseModel):
    message: str = Field(..., min_length=2, max_length=300)
    limit: int = Field(default=5, ge=1, le=10)
    fast_only: bool = Field(default=False)


class QuickPublishParseRequest(BaseModel):
    message: str = Field(..., min_length=2, max_length=400)
    type: Optional[str] = Field(default=None)
    fast_only: bool = Field(default=False)


def split_terms(value: str | None) -> list[str]:
    if not value:
        return []
    return [segment.strip() for segment in value.replace("/", "、").split("、") if segment.strip()]


def keyword_score(query_keywords: list[str], item: Item) -> tuple[float, list[str]]:
    query_terms = normalize_keywords(query_keywords)
    if not query_terms:
        return 0.0, []

    searchable_values = [
        item.title,
        item.description,
        item.feature_text,
        item.location,
        item.category,
        item.color,
        item.brand,
        *(item.keywords or []),
    ]
    normalized_texts = [normalize_text(value) for value in searchable_values if normalize_text(value)]

    matched: list[str] = []
    for keyword in query_terms:
        normalized_keyword = normalize_text(keyword)
        if any(normalized_keyword in text for text in normalized_texts):
            matched.append(keyword)
            continue

        related_values = {
            value
            for value in [
                normalize_category(keyword),
                normalize_color(keyword),
                normalize_brand(keyword),
                normalize_location(keyword),
            ]
            if value
        }
        if any(normalize_text(value) in normalized_texts for value in related_values):
            matched.append(keyword)

    if not matched:
        return 0.0, []
    return len(matched) / len(query_terms), matched


def location_score(filters: dict, item: Item) -> tuple[float, str | None]:
    raw_locations = split_terms(filters.get("raw_location"))
    normalized_locations = split_terms(filters.get("normalized_location"))

    if raw_locations:
        item_candidates = [item.location, item.description, item.title]
        for raw_location in raw_locations:
            raw_text = normalize_text(raw_location)
            if any(raw_text in normalize_text(value) for value in item_candidates if normalize_text(value)):
                return 0.2, f"具体地点命中：{raw_location}"

    for normalized_location in normalized_locations or split_terms(filters.get("location")):
        matched, canonical = semantic_contains(
            normalized_location,
            [item.location, item.description, item.title],
            "location",
        )
        if matched:
            return 0.14, f"地点范围相关：{canonical or normalized_location}"

    return 0.0, None


def build_item_search_text(item: Item) -> str:
    return " ".join(
        [
            item.title or "",
            item.description or "",
            item.feature_text or "",
            item.location or "",
            item.category or "",
            item.color or "",
            item.brand or "",
            " ".join(item.keywords or []),
        ]
    ).strip()


def build_query_tokens(filters: dict) -> list[str]:
    return tokenize_text(
        " ".join(
            [
                filters.get("category") or "",
                filters.get("color") or "",
                filters.get("brand") or "",
                filters.get("raw_location") or "",
                filters.get("normalized_location") or "",
                filters.get("feature_text") or "",
                " ".join(filters.get("keywords") or []),
            ]
        )
    )


def score_item(filters: dict, item: Item, bm25_value: float = 0.0) -> tuple[float, list[str]]:
    score = 0.0
    reasons: list[str] = []

    matched, canonical = semantic_contains(
        filters.get("category"),
        [item.category, item.title, item.description],
        "category",
    )
    if matched:
        score += 0.26
        reasons.append(f"类别相关：{canonical or item.category or item.title}")

    matched, canonical = semantic_contains(
        filters.get("color"),
        [item.color, item.description, item.feature_text, item.title],
        "color",
    )
    if matched:
        score += 0.18
        reasons.append(f"颜色相关：{canonical or filters.get('color')}")

    matched, canonical = semantic_contains(
        filters.get("brand"),
        [item.brand, item.description, item.title, item.feature_text],
        "brand",
    )
    if matched:
        score += 0.18
        reasons.append(f"品牌相关：{canonical or filters.get('brand')}")
    elif same_brand_family(filters.get("brand"), item.brand):
        score += 0.12
        reasons.append(f"品牌家族相关：{filters.get('brand')} / {item.brand}")

    location_weight, location_reason = location_score(filters, item)
    if location_weight:
        score += location_weight
        reasons.append(location_reason)

    title_keywords = normalize_keywords(filters.get("title_keywords") or [])
    title_match = [
        keyword
        for keyword in title_keywords
        if normalize_text(keyword) in normalize_text(item.title)
    ]
    if title_match:
        score += min(0.18, 0.09 * len(title_match))
        reasons.append(f"标题命中：{'、'.join(title_match[:2])}")

    query_keywords = filters.get("keywords") or []
    overlap_score, matched_keywords = keyword_score(query_keywords, item)
    if overlap_score > 0:
        score += min(0.24, overlap_score * 0.24)
        reasons.append(f"关键词命中：{'、'.join(matched_keywords[:3])}")

    feature_text = filters.get("feature_text")
    if feature_text:
        probe = feature_text[:24]
        if normalize_text(probe) and any(
            normalize_text(probe) in normalize_text(value)
            for value in [item.feature_text, item.description, item.title]
            if normalize_text(value)
        ):
            score += 0.10
            reasons.append("典型特征接近")

    if bm25_value > 0:
        score += min(0.22, bm25_value * 0.22)
        reasons.append(f"文本召回相关：{round(bm25_value * 100)}%")

    return round(score, 4), reasons


def target_type_from_intent(intent: str) -> Optional[str]:
    if intent == "lost":
        return "found"
    if intent == "found":
        return "lost"
    return None


def build_reply(filters: dict, matches: list[dict]) -> str:
    fragments = []
    if filters.get("category"):
        fragments.append(filters["category"])
    if filters.get("color"):
        fragments.append(filters["color"])
    if filters.get("brand"):
        fragments.append(filters["brand"])
    if filters.get("raw_location"):
        fragments.append(filters["raw_location"])
    elif filters.get("normalized_location"):
        fragments.append(filters["normalized_location"])

    summary = "、".join(fragments) if fragments else "你描述的物品"
    if not matches:
        return f"我先按“{summary}”的线索检索过了，暂时没有找到高相关记录。你可以补充颜色、地点、品牌或典型特征后再试。"
    return f"我先按“{summary}”的线索帮你筛出了 {len(matches)} 条较相关记录，你可以优先查看前几条。"


@router.post("/assistant/search", summary="智能寻物")
def assistant_search(
    payload: AssistantSearchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    print(f"[AI Search] received message: {payload.message}")
    del current_user

    filters = (
        extract_item_search_filters_fast(payload.message)
        if payload.fast_only
        else extract_item_search_filters(payload.message)
    )
    print(f"[AI Search] parsed filters: {filters}")

    target_type = target_type_from_intent(filters["intent"])
    query = db.query(Item).filter(
        Item.is_deleted.is_(False),
        Item.status != "closed",
    )
    if target_type:
        query = query.filter(Item.type == target_type)

    candidates = query.order_by(Item.created_at.desc()).limit(120).all()
    query_tokens = build_query_tokens(filters)
    documents = [
        BM25Document(raw_text=build_item_search_text(item), tokens=tokenize_text(build_item_search_text(item)))
        for item in candidates
    ]
    bm25_values = normalize_bm25_scores(
        [bm25_score(query_tokens, documents, index) for index in range(len(documents))]
    )

    scored_matches = []
    for index, item in enumerate(candidates):
        score, reasons = score_item(filters, item, bm25_values[index] if index < len(bm25_values) else 0.0)
        if score >= 0.18:
            scored_matches.append({"item": item, "score": score, "reasons": reasons})

    scored_matches.sort(key=lambda record: record["score"], reverse=True)
    top_matches = scored_matches[: payload.limit]
    print(f"[AI Search] matched {len(top_matches)} item(s)")

    return {
        "mode": "fast" if payload.fast_only else "full",
        "filters": filters,
        "reply": build_reply(filters, top_matches),
        "items": [
            {
                "item": ItemOut.model_validate(match["item"]).model_dump(mode="json"),
                "score": match["score"],
                "reasons": match["reasons"],
            }
            for match in top_matches
        ],
    }


@router.post("/quick-publish/parse", summary="快速发布字段解析")
def quick_publish_parse(
    payload: QuickPublishParseRequest,
    current_user: User = Depends(get_current_user),
):
    print(f"[Quick Publish] received message: {payload.message}")
    del current_user

    parsed = (
        extract_quick_publish_fields_fast(payload.message, payload.type)
        if payload.fast_only
        else extract_quick_publish_fields(payload.message, payload.type)
    )
    print(f"[Quick Publish] parsed result: {parsed}")
    return {
        "mode": "fast" if payload.fast_only else "full",
        **parsed,
    }
