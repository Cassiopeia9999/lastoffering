from datetime import datetime
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, UploadFile, File, Form, Query
from sqlalchemy.orm import Session

from backend.app.core.deps import get_db, get_current_user
from backend.app.crud import item as crud_item, message as crud_message
from backend.app.models.user import User
from backend.app.models.item import ITEM_CATEGORIES
from backend.app.schemas.item import ItemOut, ItemListOut, ItemUpdate, ItemStatusUpdate
from backend.app.utils.file_utils import save_upload_image
from backend.app.services.ai_classifier import classify_image
from backend.app.services.ai_feature import extract_feature, feature_to_str
from backend.app.services.auto_match import run_auto_match

router = APIRouter(prefix="/items", tags=["物品"])


@router.post("", response_model=ItemOut, status_code=201, summary="发布失物/招领信息")
async def create_item(
    background_tasks: BackgroundTasks,
    type: str = Form(..., description="lost=失物 / found=招领"),
    title: str = Form(...),
    description: Optional[str] = Form(None),
    category: Optional[str] = Form(None),
    location: Optional[str] = Form(None),
    happen_time: Optional[str] = Form(None, description="格式：2024-01-01T12:00:00"),
    image: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if type not in ("lost", "found"):
        raise HTTPException(status_code=400, detail="type 只能是 lost 或 found")
    if category and category not in ITEM_CATEGORIES:
        raise HTTPException(status_code=400, detail=f"无效的类别，可选：{ITEM_CATEGORIES}")

    image_url = None
    ai_category = None
    feature_str = None

    if image and image.filename:
        image_url = save_upload_image(image)

        # AI 自动识别类别（用户未手动指定时使用 AI 结果）
        ai_category_result, _ = classify_image(image_url)
        ai_category = ai_category_result

        # 提取特征向量并序列化存库
        feature_vec = extract_feature(image_url)
        if feature_vec:
            feature_str = feature_to_str(feature_vec)

    # 用户手动指定类别优先，否则使用 AI 识别结果
    final_category = category if category else ai_category

    parsed_time = None
    if happen_time:
        try:
            # 尝试多种格式解析
            from dateutil import parser
            parsed_time = parser.isoparse(happen_time)
        except Exception:
            try:
                parsed_time = datetime.fromisoformat(happen_time.replace('Z', '+00:00'))
            except Exception:
                raise HTTPException(status_code=400, detail=f"happen_time 格式错误: {happen_time}")

    item = crud_item.create_item(
        db=db,
        owner_id=current_user.id,
        type=type,
        title=title,
        description=description,
        category=final_category,
        location=location,
        happen_time=parsed_time,
        image_url=image_url,
        feature_vector=feature_str,
    )

    # 有图片才触发后台自动匹配（无特征向量无法检索）
    if feature_str:
        background_tasks.add_task(run_auto_match, item.id, item.type)

    return item


@router.get("", response_model=ItemListOut, summary="查询物品列表（支持筛选/关键词搜索）")
def list_items(
    type: Optional[str] = Query(None, description="lost / found"),
    category: Optional[str] = Query(None),
    status: Optional[str] = Query(None, description="pending / matched / closed"),
    keyword: Optional[str] = Query(None, description="标题或描述关键词"),
    exclude_closed: bool = Query(False, description="是否排除已完成的物品"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    skip = (page - 1) * page_size
    items, total = crud_item.get_items(
        db, skip=skip, limit=page_size,
        type=type, category=category, status=status, keyword=keyword,
        exclude_closed=exclude_closed,
    )
    return {"total": total, "items": items}


@router.get("/categories", summary="获取所有物品类别")
def get_categories():
    return {"categories": ITEM_CATEGORIES}


@router.get("/my", response_model=ItemListOut, summary="我发布的物品")
def my_items(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    items = crud_item.get_items_by_owner(db, current_user.id)
    return {"total": len(items), "items": items}


@router.get("/{item_id}", response_model=ItemOut, summary="物品详情")
def get_item(item_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    item = crud_item.get_item_by_id(db, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="物品不存在或已下架")
    return item


@router.put("/{item_id}", response_model=ItemOut, summary="编辑物品信息")
def update_item(
    item_id: int,
    payload: ItemUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    item = crud_item.get_item_by_id(db, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="物品不存在")
    if item.owner_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="无权限修改此物品")
    if payload.category and payload.category not in ITEM_CATEGORIES:
        raise HTTPException(status_code=400, detail=f"无效的类别，可选：{ITEM_CATEGORIES}")

    updated = crud_item.update_item(
        db, item,
        title=payload.title,
        description=payload.description,
        category=payload.category,
        location=payload.location,
        happen_time=payload.happen_time,
    )
    return updated


@router.patch("/{item_id}/status", response_model=ItemOut, summary="更新物品状态")
def update_status(
    item_id: int,
    payload: ItemStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    item = crud_item.get_item_by_id(db, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="物品不存在")
    if item.owner_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="无权限操作")
    if payload.status not in ("pending", "matched", "closed"):
        raise HTTPException(status_code=400, detail="无效的状态值")
    return crud_item.update_item_status(db, item, payload.status)


@router.delete("/{item_id}", status_code=204, summary="下架物品")
def delete_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """下架物品（软删除），物品发布者可以下架"""
    item = crud_item.get_item_by_id(db, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="物品不存在")
    if item.owner_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="无权限操作")
    crud_item.soft_delete_item(db, item)


@router.post("/{item_id}/restore", summary="重新上架物品")
def restore_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """重新上架已下架的物品，只有物品发布者可以操作"""
    # 需要查询包含已下架的物品
    from backend.app.models.item import Item
    item = db.query(Item).filter(Item.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="物品不存在")
    if item.owner_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="无权限操作")
    if not item.is_deleted:
        raise HTTPException(status_code=400, detail="物品未下架，无需重新上架")

    crud_item.restore_item(db, item)
    return {"message": "物品已重新上架"}


@router.post("/{item_id}/close", summary="手动标记物品为已完成（不可逆）")
def close_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """手动将物品标记为已完成，状态变为 closed，不可重新上架"""
    item = crud_item.get_item_by_id(db, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="物品不存在")
    if item.owner_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="无权限操作")
    if item.status == "closed":
        raise HTTPException(status_code=400, detail="物品已是完成状态")
    crud_item.update_item_status(db, item, "closed")
    return {"message": "已标记为完成"}


@router.delete("/{item_id}/messages/{msg_id}", status_code=204, summary="删除留言")
def delete_message(
    item_id: int,
    msg_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """删除留言，只有留言发送者或物品发布者可以删除"""
    msg = crud_message.get_message_by_id(db, msg_id)
    if not msg or msg.item_id != item_id:
        raise HTTPException(status_code=404, detail="留言不存在")
    
    # 检查权限：留言发送者或物品发布者可以删除
    item = crud_item.get_item_by_id(db, item_id)
    if msg.sender_id != current_user.id and item.owner_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="无权限删除此留言")
    
    crud_message.delete_message(db, msg)
