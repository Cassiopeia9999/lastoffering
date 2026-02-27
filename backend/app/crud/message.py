from typing import List

from sqlalchemy.orm import Session

from backend.app.models.message import Message


def create_message(db: Session, item_id: int, sender_id: int, content: str) -> Message:
    msg = Message(item_id=item_id, sender_id=sender_id, content=content)
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return msg


def get_messages_by_item(db: Session, item_id: int) -> List[Message]:
    return (
        db.query(Message)
        .filter(Message.item_id == item_id)
        .order_by(Message.created_at.asc())
        .all()
    )
