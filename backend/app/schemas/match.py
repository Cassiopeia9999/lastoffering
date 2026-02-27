from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict

from backend.app.schemas.item import ItemOut


class MatchCreate(BaseModel):
    lost_item_id: int
    found_item_id: int


class MatchOut(BaseModel):
    id: int
    lost_item_id: int
    found_item_id: int
    similarity: Optional[float]
    status: str
    created_at: datetime
    lost_item: Optional[ItemOut] = None
    found_item: Optional[ItemOut] = None

    model_config = ConfigDict(from_attributes=True)
