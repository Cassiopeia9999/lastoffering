from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


def normalize_keywords(value) -> List[str]:
    if value is None:
        return []
    if isinstance(value, str):
        parts = value.split(",")
    else:
        parts = value
    return [str(item).strip() for item in parts if str(item).strip()]


class ItemCreate(BaseModel):
    type: str
    title: str
    description: Optional[str] = None
    category: Optional[str] = None
    color: Optional[str] = None
    brand: Optional[str] = None
    keywords: List[str] = Field(default_factory=list)
    feature_text: Optional[str] = None
    location: Optional[str] = None
    happen_time: Optional[datetime] = None

    @field_validator("keywords", mode="before")
    @classmethod
    def validate_keywords(cls, value):
        return normalize_keywords(value)


class ItemUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    color: Optional[str] = None
    brand: Optional[str] = None
    keywords: Optional[List[str]] = None
    feature_text: Optional[str] = None
    location: Optional[str] = None
    happen_time: Optional[datetime] = None

    @field_validator("keywords", mode="before")
    @classmethod
    def validate_keywords(cls, value):
        if value is None:
            return None
        return normalize_keywords(value)


class ItemStatusUpdate(BaseModel):
    status: str


class ItemOwnerOut(BaseModel):
    id: int
    username: str
    nickname: str | None = None
    avatar: str | None = None
    contact: str | None = None

    model_config = ConfigDict(from_attributes=True)


class ItemOut(BaseModel):
    id: int
    type: str
    title: str
    description: Optional[str]
    category: Optional[str]
    color: Optional[str]
    brand: Optional[str]
    keywords: List[str] = Field(default_factory=list)
    feature_text: Optional[str]
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


class SimilarItemOut(BaseModel):
    item: ItemOut
    similarity: float


class SimilarItemListOut(BaseModel):
    total: int
    target_type: str
    items: List[SimilarItemOut]
