from typing import Optional, List

from sqlalchemy.orm import Session

from backend.app.models.notification import Notification


def create_notification(
    db: Session,
    user_id: int,
    type: str,
    content: str,
    related_item_id: Optional[int] = None,
    related_match_id: Optional[int] = None,
) -> Notification:
    notif = Notification(
        user_id=user_id,
        type=type,
        content=content,
        related_item_id=related_item_id,
        related_match_id=related_match_id,
    )
    db.add(notif)
    db.commit()
    db.refresh(notif)
    return notif


def get_notifications_by_user(db: Session, user_id: int) -> List[Notification]:
    return (
        db.query(Notification)
        .filter(Notification.user_id == user_id)
        .order_by(Notification.created_at.desc())
        .all()
    )


def mark_as_read(db: Session, notif_id: int, user_id: int) -> Optional[Notification]:
    notif = db.query(Notification).filter(
        Notification.id == notif_id,
        Notification.user_id == user_id,
    ).first()
    if notif:
        notif.is_read = True
        db.commit()
        db.refresh(notif)
    return notif


def mark_all_as_read(db: Session, user_id: int) -> int:
    count = (
        db.query(Notification)
        .filter(Notification.user_id == user_id, Notification.is_read == False)
        .update({"is_read": True})
    )
    db.commit()
    return count
