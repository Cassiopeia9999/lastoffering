from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.core.deps import get_db, get_current_user
from backend.app.crud import item as crud_item
from backend.app.crud import match as crud_match
from backend.app.crud import notification as crud_notif
from backend.app.models.user import User
from backend.app.models.match import Match
from backend.app.schemas.match import MatchCreate, MatchOut

router = APIRouter(prefix="/matches", tags=["匹配"])


@router.get("/item/{item_id}", response_model=Optional[MatchOut], summary="获取物品相关的匹配信息")
def get_match_by_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取物品相关的所有有效匹配记录（pending/confirmed/completed）"""
    from sqlalchemy import or_
    match = (
        db.query(Match)
        .filter(
            or_(Match.lost_item_id == item_id, Match.found_item_id == item_id),
            Match.status.in_(["pending", "confirmed", "completed"])
        )
        .order_by(Match.created_at.desc())
        .first()
    )
    return match


@router.post("", response_model=MatchOut, status_code=201, summary="点击【疑似遗失】创建匹配")
def create_match(
    payload: MatchCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    lost_item = crud_item.get_item_by_id(db, payload.lost_item_id)
    found_item = crud_item.get_item_by_id(db, payload.found_item_id)

    if not lost_item or not found_item:
        raise HTTPException(status_code=404, detail="物品不存在")
    if lost_item.type != "lost" or found_item.type != "found":
        raise HTTPException(status_code=400, detail="lost_item_id 必须是失物，found_item_id 必须是招领")

    match = crud_match.create_match(db, payload.lost_item_id, payload.found_item_id)

    # 通知失物发布者 → 点击跳到招领页（让他去确认/拒绝）
    crud_notif.create_notification(
        db,
        user_id=lost_item.owner_id,
        type="match_found",
        content=f"你的失物【{lost_item.title}】可能已被找到，请查看招领信息【{found_item.title}】",
        related_item_id=found_item.id,
        related_match_id=match.id,
    )
    # 通知招领发布者 → 点击跳到自己的招领页（让他来确认/拒绝）
    crud_notif.create_notification(
        db,
        user_id=found_item.owner_id,
        type="match_found",
        content=f"有用户认为你招领的【{found_item.title}】可能是他的失物【{lost_item.title}】，请确认是否匹配",
        related_item_id=found_item.id,
        related_match_id=match.id,
    )

    return match


@router.patch("/{match_id}/confirm", response_model=MatchOut, summary="确认匹配（交换联系方式）")
def confirm_match(
    match_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    match = crud_match.get_match_by_id(db, match_id)
    if not match:
        raise HTTPException(status_code=404, detail="匹配记录不存在")

    lost_item = crud_item.get_item_by_id(db, match.lost_item_id)
    found_item = crud_item.get_item_by_id(db, match.found_item_id)

    # 只有招领物品的发布者才能确认匹配（他持有物品，需要他来核实）
    if current_user.id != found_item.owner_id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="只有招领信息发布者可以确认匹配")

    crud_match.update_match_status(db, match, "confirmed")
    crud_item.update_item_status(db, lost_item, "matched")
    crud_item.update_item_status(db, found_item, "matched")

    # 给双方发送包含联系方式的通知
    lost_owner = lost_item.owner
    found_owner = found_item.owner

    crud_notif.create_notification(
        db,
        user_id=lost_item.owner_id,
        type="contact_shared",
        content=f"匹配已确认！拾得者【{found_owner.nickname or found_owner.username}】的联系方式：{found_owner.contact or '未填写'}",
        related_item_id=found_item.id,
        related_match_id=match_id,
    )
    crud_notif.create_notification(
        db,
        user_id=found_item.owner_id,
        type="contact_shared",
        content=f"匹配已确认！失物主人【{lost_owner.nickname or lost_owner.username}】的联系方式：{lost_owner.contact or '未填写'}",
        related_item_id=lost_item.id,
        related_match_id=match_id,
    )

    return match


@router.patch("/{match_id}/reject", response_model=MatchOut, summary="拒绝匹配")
def reject_match(
    match_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    match = crud_match.get_match_by_id(db, match_id)
    if not match:
        raise HTTPException(status_code=404, detail="匹配记录不存在")

    lost_item = crud_item.get_item_by_id(db, match.lost_item_id)
    found_item = crud_item.get_item_by_id(db, match.found_item_id)

    # 只有招领物品的发布者才能拒绝匹配
    if current_user.id != found_item.owner_id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="只有招领信息发布者可以拒绝匹配")

    crud_match.update_match_status(db, match, "rejected")
    return match


@router.patch("/{match_id}/complete", response_model=MatchOut, summary="完成认领（双方确认物品已交接）")
def complete_match(
    match_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    双方确认物品已交接完成，物品状态变为 closed（已关闭/已完成）
    需要双方各自确认一次
    """
    match = crud_match.get_match_by_id(db, match_id)
    if not match:
        raise HTTPException(status_code=404, detail="匹配记录不存在")
    if match.status != "confirmed":
        raise HTTPException(status_code=400, detail="匹配未确认，无法完成认领")

    lost_item = crud_item.get_item_by_id(db, match.lost_item_id)
    found_item = crud_item.get_item_by_id(db, match.found_item_id)

    if current_user.id not in (lost_item.owner_id, found_item.owner_id):
        raise HTTPException(status_code=403, detail="无权限操作")

    # 记录哪一方确认完成
    if current_user.id == lost_item.owner_id:
        match.lost_owner_confirmed = True
    else:
        match.found_owner_confirmed = True

    db.commit()
    db.refresh(match)

    # 双方都确认后，标记为完成
    if match.lost_owner_confirmed and match.found_owner_confirmed:
        crud_match.update_match_status(db, match, "completed")
        crud_item.update_item_status(db, lost_item, "closed")
        crud_item.update_item_status(db, found_item, "closed")

        # 发送完成通知
        crud_notif.create_notification(
            db,
            user_id=lost_item.owner_id,
            type="match_completed",
            content=f"恭喜！你的失物【{lost_item.title}】已完成认领",
            related_match_id=match_id,
        )
        crud_notif.create_notification(
            db,
            user_id=found_item.owner_id,
            type="match_completed",
            content=f"感谢！你招领的【{found_item.title}】已成功归还",
            related_match_id=match_id,
        )

    return match
