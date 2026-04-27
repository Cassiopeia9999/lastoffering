from typing import List, Tuple

from sqlalchemy.orm import Session

from backend.app.core.database import SessionLocal
from backend.app.crud import item as crud_item
from backend.app.crud import notification as crud_notif
from backend.app.models.item import Item
from backend.app.services.ai_feature import str_to_feature
from backend.app.services.ai_search import search_similar_items
from backend.app.services.semantic_rules import (
    normalize_brand,
    normalize_color,
    normalize_keywords,
    normalize_location,
    semantic_contains,
    semantic_keyword_overlap,
    same_brand_family,
)

AUTO_MATCH_CANDIDATE_THRESHOLD = 0.35
AUTO_MATCH_FINAL_THRESHOLD = 0.55
AUTO_MATCH_TOP_K = 5
AUTO_MATCH_CANDIDATE_POOL = 12

# Keep image similarity dominant, then let text/attribute signals refine ranking.
IMAGE_WEIGHT = 0.52
KEYWORD_WEIGHT = 0.20
COLOR_WEIGHT = 0.08
BRAND_WEIGHT = 0.10
LOCATION_WEIGHT = 0.10


def exact_semantic_score(source: str | None, target: str | None, field_type: str) -> float:
    if field_type == "color":
        left = normalize_color(source)
        right = normalize_color(target)
    elif field_type == "brand":
        left = normalize_brand(source)
        right = normalize_brand(target)
    elif field_type == "location":
        left = normalize_location(source)
        right = normalize_location(target)
    else:
        left = source
        right = target

    if not left or not right:
        return 0.0
    return 1.0 if left == right else 0.0


def brand_score(source: str | None, target: str | None) -> tuple[float, str | None]:
    left = normalize_brand(source)
    right = normalize_brand(target)
    if not left or not right:
        return 0.0, None
    if left == right:
        return 1.0, f"品牌一致：{left}"
    if same_brand_family(left, right):
        return 0.7, f"品牌家族接近：{left} / {right}"
    return 0.0, None


def location_score(source_item: Item, target_item: Item) -> tuple[float, str | None]:
    left = normalize_location(source_item.location)
    right = normalize_location(target_item.location)
    if left and right and left == right:
        return 1.0, f"地点范围一致：{left}"

    matched, canonical = semantic_contains(
        source_item.location,
        [target_item.location, target_item.description, target_item.title],
        "location",
    )
    if matched:
        return 0.7, f"地点语义接近：{canonical or source_item.location}"
    return 0.0, None


def build_match_reasons(
    source_item: Item,
    target_item: Item,
    image_score: float,
    keyword_score: float,
    shared_keywords: list[str],
    brand_reason: str | None,
    location_reason: str | None,
) -> List[str]:
    reasons = [f"图像相似度：{image_score:.0%}"]
    if exact_semantic_score(source_item.color, target_item.color, "color"):
        reasons.append(f"颜色一致：{normalize_color(source_item.color)}")
    if brand_reason:
        reasons.append(brand_reason)
    if location_reason:
        reasons.append(location_reason)
    if keyword_score > 0 and shared_keywords:
        reasons.append(f"关键词重合：{'、'.join(shared_keywords[:3])}")
    return reasons


def hybrid_match_score(source_item: Item, target_item: Item, image_score: float) -> Tuple[float, List[str]]:
    keyword_score, shared_keywords = semantic_keyword_overlap(
        normalize_keywords(source_item.keywords or []),
        normalize_keywords(target_item.keywords or []),
    )
    color_score = exact_semantic_score(source_item.color, target_item.color, "color")
    scored_brand, brand_reason = brand_score(source_item.brand, target_item.brand)
    scored_location, location_reason = location_score(source_item, target_item)

    score = (
        image_score * IMAGE_WEIGHT
        + keyword_score * KEYWORD_WEIGHT
        + color_score * COLOR_WEIGHT
        + scored_brand * BRAND_WEIGHT
        + scored_location * LOCATION_WEIGHT
    )
    reasons = build_match_reasons(
        source_item,
        target_item,
        image_score,
        keyword_score,
        shared_keywords,
        brand_reason,
        location_reason,
    )
    return round(score, 4), reasons


def run_auto_match(item_id: int, item_type: str) -> None:
    db: Session = SessionLocal()
    try:
        _do_match(db, item_id, item_type)
    except Exception as exc:
        print(f"[AutoMatch] item_id={item_id} failed: {exc}")
    finally:
        db.close()


def _do_match(db: Session, item_id: int, item_type: str) -> None:
    new_item = crud_item.get_item_by_id(db, item_id)
    if not new_item or not new_item.feature_vector:
        print(f"[AutoMatch] item_id={item_id} has no feature vector, skipped")
        return

    query_vec = str_to_feature(new_item.feature_vector)
    if query_vec is None:
        print(f"[AutoMatch] item_id={item_id} feature vector parse failed")
        return

    search_type = "lost" if item_type == "found" else "found"
    raw_results = search_similar_items(
        db=db,
        query_feature=query_vec.tolist(),
        search_type=search_type,
        top_k=AUTO_MATCH_CANDIDATE_POOL,
        threshold=AUTO_MATCH_CANDIDATE_THRESHOLD,
        exclude_item_id=item_id,
    )

    rescored_results = []
    for matched_item, image_score in raw_results:
        final_score, reasons = hybrid_match_score(new_item, matched_item, image_score)
        if final_score >= AUTO_MATCH_FINAL_THRESHOLD:
            rescored_results.append((matched_item, final_score, image_score, reasons))

    rescored_results.sort(key=lambda item: item[1], reverse=True)
    rescored_results = rescored_results[:AUTO_MATCH_TOP_K]

    if not rescored_results:
        print(f"[AutoMatch] item_id={item_id} no candidates passed final threshold")
        return

    print(f"[AutoMatch] item_id={item_id} matched {len(rescored_results)} candidate(s)")

    for matched_item, final_score, image_score, reasons in rescored_results:
        reason_text = "；".join(reasons)

        if item_type == "found":
            crud_notif.create_notification(
                db,
                user_id=matched_item.owner_id,
                type="match_found",
                content=(
                    f"系统发现一条疑似与你失物相关的招领信息。\n"
                    f"招领物品：{new_item.title}\n"
                    f"综合匹配分：{final_score:.0%}\n"
                    f"匹配依据：{reason_text}\n"
                    f"请前往详情页查看是否为你的失物。"
                ),
                related_item_id=new_item.id,
            )
        else:
            crud_notif.create_notification(
                db,
                user_id=matched_item.owner_id,
                type="match_found",
                content=(
                    f"系统发现一条疑似与你招领物品相关的失物信息。\n"
                    f"失物：{new_item.title}\n"
                    f"综合匹配分：{final_score:.0%}\n"
                    f"匹配依据：{reason_text}\n"
                    f"请前往详情页查看是否为同一物品。"
                ),
                related_item_id=new_item.id,
            )
            crud_notif.create_notification(
                db,
                user_id=new_item.owner_id,
                type="match_found",
                content=(
                    f"系统发现一条可能与你失物“{new_item.title}”相关的招领信息。\n"
                    f"招领物品：{matched_item.title}\n"
                    f"综合匹配分：{final_score:.0%}\n"
                    f"匹配依据：{reason_text}\n"
                    f"请前往详情页确认。"
                ),
                related_item_id=matched_item.id,
            )

        print(
            f"[AutoMatch] notify user_id={matched_item.owner_id}, "
            f"final={final_score:.4f}, image={image_score:.4f}"
        )
