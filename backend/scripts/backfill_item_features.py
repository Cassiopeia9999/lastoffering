from backend.app.core.database import SessionLocal
from backend.app.models.item import Item
from backend.app.services.ark_ai import heuristic_extract_filters, normalize_keywords


def build_feature_text(item: Item, keywords: list[str]) -> str | None:
    parts = []
    if item.brand:
        parts.append(item.brand)
    if item.color:
        parts.append(item.color)
    if item.category:
        parts.append(item.category)
    parts.extend([keyword for keyword in keywords if keyword not in parts][:3])
    if not parts:
        return None
    return "、".join(parts)


def backfill_items() -> None:
    db = SessionLocal()
    try:
        items = db.query(Item).order_by(Item.id.asc()).all()
        updated_count = 0

        for item in items:
            source_text = " ".join(
                [value for value in [item.title, item.description, item.location, item.category] if value]
            )
            parsed = heuristic_extract_filters(source_text)

            changed = False

            if not item.category and parsed.get("category"):
                item.category = parsed["category"]
                changed = True
            if not item.color and parsed.get("color"):
                item.color = parsed["color"]
                changed = True
            if not item.brand and parsed.get("brand"):
                item.brand = parsed["brand"]
                changed = True
            if not item.location and parsed.get("location"):
                item.location = parsed["location"]
                changed = True

            merged_keywords = []
            existing_keywords = normalize_keywords(item.keywords)
            for keyword in [*existing_keywords, *(parsed.get("keywords") or [])]:
                if keyword and keyword not in merged_keywords:
                    merged_keywords.append(keyword)
            if merged_keywords and merged_keywords != existing_keywords:
                item.keywords = merged_keywords[:8]
                changed = True

            if not item.feature_text:
                feature_text = build_feature_text(item, merged_keywords)
                if feature_text:
                    item.feature_text = feature_text
                    changed = True

            if changed:
                updated_count += 1
                print(
                    f"[Backfill] item_id={item.id}, title={item.title}, "
                    f"color={item.color}, brand={item.brand}, keywords={item.keywords}, "
                    f"feature_text={item.feature_text}"
                )

        db.commit()
        print(f"[Backfill] updated {updated_count} item(s)")
    finally:
        db.close()


if __name__ == "__main__":
    backfill_items()
