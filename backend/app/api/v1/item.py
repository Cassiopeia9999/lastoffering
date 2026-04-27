import json
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, Query, UploadFile
from sqlalchemy.orm import Session

from backend.app.core.deps import get_current_user, get_db
from backend.app.crud import item as crud_item, message as crud_message
from backend.app.models.item import ITEM_CATEGORIES, Item
from backend.app.models.user import User
from backend.app.schemas.item import ItemListOut, ItemOut, ItemStatusUpdate, ItemUpdate, SimilarItemListOut
from backend.app.services.ai_classifier import classify_image
from backend.app.services.ai_feature import extract_feature, feature_to_str, str_to_feature
from backend.app.services.ai_search import search_similar_items
from backend.app.services.auto_match import run_auto_match
from backend.app.utils.file_utils import save_upload_image

router = APIRouter(prefix="/items", tags=["items"])


def parse_keywords_form(raw_keywords: Optional[str]) -> list[str]:
    if not raw_keywords:
        return []
    try:
        data = json.loads(raw_keywords)
        if isinstance(data, list):
            return [str(item).strip() for item in data if str(item).strip()]
    except json.JSONDecodeError:
        pass
    return [segment.strip() for segment in raw_keywords.split(",") if segment.strip()]


def parse_happen_time(raw_happen_time: Optional[str]) -> Optional[datetime]:
    if not raw_happen_time:
        return None
    try:
        from dateutil import parser

        return parser.isoparse(raw_happen_time)
    except Exception:
        try:
            return datetime.fromisoformat(raw_happen_time.replace("Z", "+00:00"))
        except Exception as exc:
            raise HTTPException(status_code=400, detail=f"happen_time format invalid: {raw_happen_time}") from exc


@router.post("", response_model=ItemOut, status_code=201, summary="Create a lost/found item")
async def create_item(
    background_tasks: BackgroundTasks,
    type: str = Form(...),
    title: str = Form(...),
    description: Optional[str] = Form(None),
    category: Optional[str] = Form(None),
    color: Optional[str] = Form(None),
    brand: Optional[str] = Form(None),
    keywords: Optional[str] = Form(None),
    feature_text: Optional[str] = Form(None),
    location: Optional[str] = Form(None),
    happen_time: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if type not in ("lost", "found"):
        raise HTTPException(status_code=400, detail="type must be lost or found")
    if category and category not in ITEM_CATEGORIES:
        raise HTTPException(status_code=400, detail=f"invalid category: {category}")

    image_url = None
    ai_category = None
    feature_str = None

    if image and image.filename:
        image_url = save_upload_image(image)
        ai_category_result, _ = classify_image(image_url)
        ai_category = ai_category_result
        feature_vec = extract_feature(image_url)
        if feature_vec is not None:
            feature_str = feature_to_str(feature_vec)

    item = crud_item.create_item(
        db=db,
        owner_id=current_user.id,
        type=type,
        title=title,
        description=description,
        category=category or ai_category,
        color=color,
        brand=brand,
        keywords=parse_keywords_form(keywords),
        feature_text=feature_text,
        location=location,
        happen_time=parse_happen_time(happen_time),
        image_url=image_url,
        feature_vector=feature_str,
    )

    if feature_str:
        background_tasks.add_task(run_auto_match, item.id, item.type)

    return item


@router.get("", response_model=ItemListOut, summary="List items")
def list_items(
    type: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    keyword: Optional[str] = Query(None),
    exclude_closed: bool = Query(False),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    del current_user
    skip = (page - 1) * page_size
    items, total = crud_item.get_items(
        db,
        skip=skip,
        limit=page_size,
        type=type,
        category=category,
        status=status,
        keyword=keyword,
        exclude_closed=exclude_closed,
    )
    return {"total": total, "items": items}


@router.get("/categories", summary="Get item categories")
def get_categories():
    return {"categories": ITEM_CATEGORIES}


@router.get("/my", response_model=ItemListOut, summary="Get current user's items")
def my_items(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    items = crud_item.get_items_by_owner(db, current_user.id, include_deleted=True, include_owner_deleted=False)
    return {"total": len(items), "items": items}


@router.get("/{item_id}", response_model=ItemOut, summary="Get item detail")
def get_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    del current_user
    item = crud_item.get_item_by_id(db, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="item not found")
    return item


@router.get("/{item_id}/similar", response_model=SimilarItemListOut, summary="Get similar items")
def get_similar_items(
    item_id: int,
    limit: int = Query(4, ge=1, le=12),
    threshold: float = Query(0.35, ge=0.0, le=1.0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    del current_user
    item = crud_item.get_item_by_id(db, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="item not found")

    target_type = "found" if item.type == "lost" else "lost"
    if not item.feature_vector:
        return {"total": 0, "target_type": target_type, "items": []}

    query_feature = str_to_feature(item.feature_vector)
    if query_feature is None:
        return {"total": 0, "target_type": target_type, "items": []}

    similar_items = search_similar_items(
        db=db,
        query_feature=query_feature,
        search_type=target_type,
        top_k=limit,
        threshold=threshold,
        exclude_item_id=item.id,
    )
    return {
        "total": len(similar_items),
        "target_type": target_type,
        "items": [{"item": similar_item, "similarity": similarity} for similar_item, similarity in similar_items],
    }


@router.put("/{item_id}", response_model=ItemOut, summary="Update item")
def update_item(
    item_id: int,
    payload: ItemUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    item = crud_item.get_item_by_id(db, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="item not found")
    if item.owner_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="permission denied")
    if payload.category and payload.category not in ITEM_CATEGORIES:
        raise HTTPException(status_code=400, detail=f"invalid category: {payload.category}")

    updated = crud_item.update_item(
        db,
        item,
        title=payload.title,
        description=payload.description,
        category=payload.category,
        color=payload.color,
        brand=payload.brand,
        keywords=payload.keywords,
        feature_text=payload.feature_text,
        location=payload.location,
        happen_time=payload.happen_time,
    )
    return updated


@router.patch("/{item_id}/status", response_model=ItemOut, summary="Update item status")
def update_status(
    item_id: int,
    payload: ItemStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    item = crud_item.get_item_by_id(db, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="item not found")
    if item.owner_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="permission denied")
    if payload.status not in ("pending", "matched", "closed"):
        raise HTTPException(status_code=400, detail="invalid status")
    return crud_item.update_item_status(db, item, payload.status)


@router.delete("/{item_id}", status_code=204, summary="Delete item")
def delete_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    item = db.query(Item).filter(Item.id == item_id, Item.owner_deleted.is_(False)).first()
    if not item:
        raise HTTPException(status_code=404, detail="item not found")
    if item.owner_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="permission denied")
    crud_item.soft_delete_item(db, item)


@router.post("/{item_id}/off-shelf", status_code=200, summary="Off shelf item")
def off_shelf_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    item = db.query(Item).filter(Item.id == item_id, Item.owner_deleted.is_(False)).first()
    if not item:
        raise HTTPException(status_code=404, detail="item not found")
    if item.owner_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="permission denied")
    crud_item.off_shelf_item(db, item)
    return {"message": "item off shelf"}


@router.post("/{item_id}/restore", summary="Restore item")
def restore_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    item = db.query(Item).filter(Item.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="item not found")
    if item.owner_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="permission denied")
    if not item.is_deleted:
        raise HTTPException(status_code=400, detail="item is not deleted")
    if item.owner_deleted and not current_user.is_admin:
        raise HTTPException(status_code=400, detail="item was deleted and cannot be restored by owner")

    crud_item.restore_item(db, item)
    return {"message": "item restored"}


@router.post("/{item_id}/close", summary="Close item")
def close_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    item = crud_item.get_item_by_id(db, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="item not found")
    if item.owner_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="permission denied")
    if item.status == "closed":
        raise HTTPException(status_code=400, detail="item already closed")

    crud_item.update_item_status(db, item, "closed")
    return {"message": "item closed"}


@router.delete("/{item_id}/messages/{msg_id}", status_code=204, summary="Delete message")
def delete_message(
    item_id: int,
    msg_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    msg = crud_message.get_message_by_id(db, msg_id)
    if not msg or msg.item_id != item_id:
        raise HTTPException(status_code=404, detail="message not found")

    item = crud_item.get_item_by_id(db, item_id)
    if msg.sender_id != current_user.id and item.owner_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="permission denied")

    crud_message.delete_message(db, msg)


