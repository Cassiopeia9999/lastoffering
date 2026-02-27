from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.core.deps import get_db, get_current_user
from backend.app.crud import item as crud_item
from backend.app.crud import message as crud_message
from backend.app.crud import notification as crud_notif
from backend.app.models.user import User
from backend.app.schemas.message import MessageCreate, MessageOut, MessageListOut

router = APIRouter(prefix="/items", tags=["留言"])


@router.post("/{item_id}/messages", response_model=MessageOut, status_code=201, summary="对物品留言")
def post_message(
    item_id: int,
    payload: MessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    item = crud_item.get_item_by_id(db, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="物品不存在")

    msg = crud_message.create_message(db, item_id=item_id, sender_id=current_user.id, content=payload.content)

    # 给物品发布者发送留言通知（不给自己发）
    if item.owner_id != current_user.id:
        crud_notif.create_notification(
            db,
            user_id=item.owner_id,
            type="new_message",
            content=f"用户【{current_user.username}】在你的物品【{item.title}】下留言了",
            related_item_id=item_id,
        )

    return msg


@router.get("/{item_id}/messages", response_model=MessageListOut, summary="查看物品留言")
def get_messages(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    item = crud_item.get_item_by_id(db, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="物品不存在")
    messages = crud_message.get_messages_by_item(db, item_id)
    return {"total": len(messages), "messages": messages}
