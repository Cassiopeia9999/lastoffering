from datetime import datetime
from typing import List

from pydantic import BaseModel, ConfigDict


class MessageCreate(BaseModel):
    content: str


class MessageSenderOut(BaseModel):
    id: int
    username: str

    model_config = ConfigDict(from_attributes=True)


class MessageOut(BaseModel):
    id: int
    item_id: int
    sender_id: int
    sender: MessageSenderOut
    content: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MessageListOut(BaseModel):
    total: int
    messages: List[MessageOut]
