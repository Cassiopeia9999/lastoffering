from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class AdminUserOut(BaseModel):
    id: int
    username: str
    contact: str
    is_admin: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AdminUserUpdate(BaseModel):
    is_active: Optional[bool] = None
    is_admin: Optional[bool] = None
    new_password: Optional[str] = None


class AdminItemOut(BaseModel):
    id: int
    type: str
    title: str
    category: Optional[str]
    status: str
    is_deleted: bool
    owner_id: int
    owner_username: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class StatsOverview(BaseModel):
    total_users: int
    active_users: int
    total_items: int
    lost_items: int
    found_items: int
    matched_items: int
    pending_items: int
    total_matches: int
    confirmed_matches: int
    total_notifications: int
    unread_notifications: int
