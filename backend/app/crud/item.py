from typing import Optional, List, Tuple

from sqlalchemy.orm import Session

from backend.app.models.item import Item


def create_item(
    db: Session,
    owner_id: int,
    type: str,
    title: str,
    description: Optional[str] = None,
    category: Optional[str] = None,
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
    return db.query(Item).filter(Item.id == item_id, Item.is_deleted == False).first()


def get_items(
    db: Session,
    skip: int = 0,
    limit: int = 20,
    type: Optional[str] = None,
    category: Optional[str] = None,
    status: Optional[str] = None,
    keyword: Optional[str] = None,
) -> Tuple[List[Item], int]:
    query = db.query(Item).filter(Item.is_deleted == False)
    if type:
        query = query.filter(Item.type == type)
    if category:
        query = query.filter(Item.category == category)
    if status:
        query = query.filter(Item.status == status)
    if keyword:
        query = query.filter(
            Item.title.contains(keyword) | Item.description.contains(keyword)
        )
    total = query.count()
    items = query.order_by(Item.created_at.desc()).offset(skip).limit(limit).all()
    return items, total


def get_items_by_owner(db: Session, owner_id: int) -> List[Item]:
    return (
        db.query(Item)
        .filter(Item.owner_id == owner_id, Item.is_deleted == False)
        .order_by(Item.created_at.desc())
        .all()
    )


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
    """获取所有有特征向量的物品，用于相似度检索"""
    query = db.query(Item).filter(
        Item.is_deleted == False,
        Item.feature_vector.isnot(None),
        Item.status == "pending",
    )
    if type:
        query = query.filter(Item.type == type)
    return query.all()
