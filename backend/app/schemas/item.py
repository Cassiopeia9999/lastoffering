from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, ConfigDict

from backend.app.models.item import ITEM_CATEGORIES


class ItemCreate(BaseModel):
    type: str
    title: str
    description: Optional[str] = None
    category: Optional[str] = None       # 为空时由 AI 自动识别
    location: Optional[str] = None
    happen_time: Optional[datetime] = None


class ItemUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    location: Optional[str] = None
    happen_time: Optional[datetime] = None


class ItemStatusUpdate(BaseModel):
    status: str


class ItemOwnerOut(BaseModel):
    id: int
    username: str

    model_config = ConfigDict(from_attributes=True)


class ItemOut(BaseModel):
    id: int
    type: str
    title: str
    description: Optional[str]
    category: Optional[str]
    location: Optional[str]
    happen_time: Optional[datetime]
    image_url: Optional[str]
    status: str
    is_deleted: bool
    owner_id: int
    owner: Optional[ItemOwnerOut]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ItemListOut(BaseModel):
    total: int
    items: List[ItemOut]
