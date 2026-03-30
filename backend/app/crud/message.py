from typing import List

from sqlalchemy.orm import Session, joinedload

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
        .options(joinedload(Message.sender))
        .filter(Message.item_id == item_id)
        .order_by(Message.created_at.asc())
        .all()
    )


def get_message_by_id(db: Session, msg_id: int) -> Message | None:
    return db.query(Message).filter(Message.id == msg_id).first()


def delete_message(db: Session, msg: Message) -> None:
    db.delete(msg)
    db.commit()
