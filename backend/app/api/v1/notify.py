from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.core.deps import get_db, get_current_user
from backend.app.crud import notification as crud_notif
from backend.app.models.user import User
from backend.app.schemas.notification import NotificationOut, NotificationListOut

router = APIRouter(prefix="/notifications", tags=["通知"])


@router.get("", response_model=NotificationListOut, summary="获取当前用户通知列表")
def list_notifications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    notifications = crud_notif.get_notifications_by_user(db, current_user.id)
    unread = sum(1 for n in notifications if not n.is_read)
    return {"total": len(notifications), "unread": unread, "notifications": notifications}


@router.patch("/{notif_id}/read", response_model=NotificationOut, summary="标记单条通知为已读")
def mark_read(
    notif_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    notif = crud_notif.mark_as_read(db, notif_id, current_user.id)
    if not notif:
        raise HTTPException(status_code=404, detail="通知不存在")
    return notif


@router.patch("/read-all", summary="全部标记为已读")
def mark_all_read(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    count = crud_notif.mark_all_as_read(db, current_user.id)
    return {"message": f"已将 {count} 条通知标记为已读"}
