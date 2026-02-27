from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, ConfigDict


class NotificationOut(BaseModel):
    id: int
    type: str
    content: str
    related_item_id: Optional[int]
    related_match_id: Optional[int]
    is_read: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class NotificationListOut(BaseModel):
    total: int
    unread: int
    notifications: List[NotificationOut]
