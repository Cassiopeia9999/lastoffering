from typing import List, Optional, Tuple

from sqlalchemy.orm import Session, joinedload

from backend.app.models.item import Item


def create_item(
    db: Session,
    owner_id: int,
    type: str,
    title: str,
    description: Optional[str] = None,
    category: Optional[str] = None,
    color: Optional[str] = None,
    brand: Optional[str] = None,
    keywords: Optional[List[str]] = None,
    feature_text: Optional[str] = None,
    location: Optional[str] = None,
    happen_time=None,
    image_url: Optional[str] = None,
    feature_vector: Optional[str] = None,
) -> Item:
    item = Item(
        owner_id=owner_id,
        type=type,
        title=title,
        description=description,
        category=category,
        color=color,
        brand=brand,
        keywords=keywords or [],
        feature_text=feature_text,
        location=location,
        happen_time=happen_time,
        image_url=image_url,
        feature_vector=feature_vector,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def get_item_by_id(db: Session, item_id: int) -> Optional[Item]:
    return (
        db.query(Item)
        .options(joinedload(Item.owner))
        .filter(Item.id == item_id, Item.is_deleted.is_(False), Item.owner_deleted.is_(False))
        .first()
    )


def get_items(
    db: Session,
    skip: int = 0,
    limit: int = 20,
    type: Optional[str] = None,
    category: Optional[str] = None,
    status: Optional[str] = None,
    keyword: Optional[str] = None,
    exclude_closed: bool = False,
) -> Tuple[List[Item], int]:
    query = db.query(Item).filter(Item.is_deleted.is_(False), Item.owner_deleted.is_(False))
    if type:
        query = query.filter(Item.type == type)
    if category:
        query = query.filter(Item.category == category)
    if status:
        query = query.filter(Item.status == status)
    elif exclude_closed:
        query = query.filter(Item.status != "closed")
    if keyword:
        query = query.filter(Item.title.contains(keyword) | Item.description.contains(keyword))
    total = query.count()
    items = query.order_by(Item.created_at.desc()).offset(skip).limit(limit).all()
    return items, total


def get_items_by_owner(
    db: Session,
    owner_id: int,
    include_deleted: bool = True,
    include_owner_deleted: bool = False,
) -> List[Item]:
    query = db.query(Item).filter(Item.owner_id == owner_id)
    if not include_deleted:
        query = query.filter(Item.is_deleted.is_(False))
    if not include_owner_deleted:
        query = query.filter(Item.owner_deleted.is_(False))
    return query.order_by(Item.created_at.desc()).all()


def update_item(db: Session, item: Item, **kwargs) -> Item:
    for key, value in kwargs.items():
        if value is not None and hasattr(item, key):
            setattr(item, key, value)
    db.commit()
    db.refresh(item)
    return item


def update_item_status(db: Session, item: Item, status: str) -> Item:
    item.status = status
    db.commit()
    db.refresh(item)
    return item


def soft_delete_item(db: Session, item: Item) -> Item:
    item.is_deleted = True
    item.owner_deleted = True
    db.commit()
    db.refresh(item)
    return item


def off_shelf_item(db: Session, item: Item) -> Item:
    item.is_deleted = True
    item.owner_deleted = False
    db.commit()
    db.refresh(item)
    return item


def restore_item(db: Session, item: Item) -> Item:
    item.is_deleted = False
    item.owner_deleted = False
    db.commit()
    db.refresh(item)
    return item


def update_item_feature(db: Session, item: Item, feature_vector: str, category: Optional[str] = None) -> Item:
    item.feature_vector = feature_vector
    if category:
        item.category = category
    db.commit()
    db.refresh(item)
    return item


def get_items_with_features(db: Session, type: Optional[str] = None) -> List[Item]:
    query = db.query(Item).filter(
        Item.is_deleted.is_(False),
        Item.feature_vector.isnot(None),
        Item.status == "pending",
    )
    if type:
        query = query.filter(Item.type == type)
    return query.all()

