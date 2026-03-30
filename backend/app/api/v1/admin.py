from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.app.core.deps import get_db, get_current_admin
from backend.app.crud import user as crud_user
from backend.app.crud import item as crud_item
from backend.app.models.user import User
from backend.app.models.item import Item
from backend.app.models.match import Match
from backend.app.models.notification import Notification
from backend.app.schemas.admin import AdminUserOut, AdminUserUpdate, AdminItemOut, StatsOverview

router = APIRouter(prefix="/admin", tags=["管理员"])


# ── 用户管理 ──────────────────────────────────────────────

@router.get("/users", response_model=List[AdminUserOut], summary="获取所有用户列表")
def list_users(
    keyword: Optional[str] = Query(None, description="用户名/联系方式关键词"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    query = db.query(User)
    if keyword:
        query = query.filter(
            User.username.contains(keyword) | User.contact.contains(keyword)
        )
    total = query.count()
    users = query.offset((page - 1) * page_size).limit(page_size).all()
    return users


@router.get("/users/{user_id}", response_model=AdminUserOut, summary="获取指定用户详情")
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    user = crud_user.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    return user


@router.delete("/users/{user_id}", status_code=204, summary="删除用户")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    user = crud_user.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    if user.id == current_admin.id:
        raise HTTPException(status_code=400, detail="不能删除自己的账号")
    db.delete(user)
    db.commit()


@router.patch("/users/{user_id}", response_model=AdminUserOut, summary="修改用户（启用/禁用/重置密码/设为管理员）")
def update_user(
    user_id: int,
    payload: AdminUserUpdate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    user = crud_user.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    if user.id == current_admin.id:
        raise HTTPException(status_code=400, detail="不能修改自己的账号状态")

    if payload.is_active is not None:
        user.is_active = payload.is_active
    if payload.is_admin is not None:
        user.is_admin = payload.is_admin
    if payload.new_password:
        from backend.app.core.password import hash_password
        user.password_hash = hash_password(payload.new_password)

    db.commit()
    db.refresh(user)
    return user


# ── 物品内容审核 ──────────────────────────────────────────

@router.get("/items", summary="获取所有物品（含已下架）")
def list_all_items(
    type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    is_deleted: Optional[bool] = Query(None, description="True=已下架 False=正常"),
    keyword: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    query = db.query(Item)
    if type:
        query = query.filter(Item.type == type)
    if status:
        query = query.filter(Item.status == status)
    if is_deleted is not None:
        query = query.filter(Item.is_deleted == is_deleted)
    if keyword:
        query = query.filter(
            Item.title.contains(keyword) | Item.description.contains(keyword)
        )
    total = query.count()
    items = query.order_by(Item.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()

    result = []
    for item in items:
        result.append({
            "id": item.id,
            "type": item.type,
            "title": item.title,
            "category": item.category,
            "status": item.status,
            "is_deleted": item.is_deleted,
            "owner_id": item.owner_id,
            "owner_username": item.owner.username if item.owner else None,
            "created_at": item.created_at,
        })
    return {"total": total, "items": result}


@router.delete("/items/{item_id}", status_code=204, summary="管理员强制下架物品")
def admin_delete_item(
    item_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    item = db.query(Item).filter(Item.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="物品不存在")
    item.is_deleted = True
    db.commit()


@router.patch("/items/{item_id}/restore", summary="管理员恢复已下架物品")
def admin_restore_item(
    item_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    item = db.query(Item).filter(Item.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="物品不存在")
    item.is_deleted = False
    db.commit()
    return {"message": "物品已恢复"}


@router.patch("/items/{item_id}/status", summary="管理员修改物品状态")
def admin_update_item_status(
    item_id: int,
    payload: dict,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    status = payload.get("status")
    if status not in ("pending", "matched", "closed"):
        raise HTTPException(status_code=400, detail="无效状态，可选：pending / matched / closed")
    item = db.query(Item).filter(Item.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="物品不存在")
    item.status = status
    db.commit()
    return {"message": "状态已更新", "status": status}


# ── 系统统计 ──────────────────────────────────────────────

@router.get("/stats", response_model=StatsOverview, summary="系统运行统计概览")
def get_stats(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    total_users = db.query(User).count()
    active_users = db.query(User).filter(User.is_active == True).count()

    total_items = db.query(Item).filter(Item.is_deleted == False).count()
    lost_items = db.query(Item).filter(Item.type == "lost", Item.is_deleted == False).count()
    found_items = db.query(Item).filter(Item.type == "found", Item.is_deleted == False).count()
    matched_items = db.query(Item).filter(Item.status == "matched", Item.is_deleted == False).count()
    pending_items = db.query(Item).filter(Item.status == "pending", Item.is_deleted == False).count()

    total_matches = db.query(Match).count()
    confirmed_matches = db.query(Match).filter(Match.status == "confirmed").count()

    total_notifications = db.query(Notification).count()
    unread_notifications = db.query(Notification).filter(Notification.is_read == False).count()

    return StatsOverview(
        total_users=total_users,
        active_users=active_users,
        total_items=total_items,
        lost_items=lost_items,
        found_items=found_items,
        matched_items=matched_items,
        pending_items=pending_items,
        total_matches=total_matches,
        confirmed_matches=confirmed_matches,
        total_notifications=total_notifications,
        unread_notifications=unread_notifications,
    )


@router.get("/stats/category", summary="各类别物品数量统计")
def get_category_stats(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    from sqlalchemy import func
    rows = (
        db.query(Item.category, func.count(Item.id).label("count"))
        .filter(Item.is_deleted == False, Item.category.isnot(None))
        .group_by(Item.category)
        .order_by(func.count(Item.id).desc())
        .all()
    )
    return {"categories": [{"category": r.category, "count": r.count} for r in rows]}


@router.get("/stats/daily", summary="近30天每日发布量统计")
def get_daily_stats(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    from sqlalchemy import func
    from datetime import datetime, timedelta

    since = datetime.utcnow() - timedelta(days=30)
    rows = (
        db.query(
            func.date(Item.created_at).label("date"),
            Item.type,
            func.count(Item.id).label("count"),
        )
        .filter(Item.created_at >= since, Item.is_deleted == False)
        .group_by(func.date(Item.created_at), Item.type)
        .order_by(func.date(Item.created_at))
        .all()
    )
    return {"daily": [{"date": str(r.date), "type": r.type, "count": r.count} for r in rows]}
