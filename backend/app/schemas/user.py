from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class UserRegister(BaseModel):
    username: str
    password: str
    contact: str


class UserLogin(BaseModel):
    username: str
    password: str


class UserUpdate(BaseModel):
    contact: Optional[str] = None
    password: Optional[str] = None
    nickname: Optional[str] = None
    real_name: Optional[str] = None
    signature: Optional[str] = None
    college: Optional[str] = None
    class_name: Optional[str] = None
    email: Optional[str] = None


class UserOut(BaseModel):
    id: int
    username: str
    contact: str
    is_admin: bool
    is_active: bool
    avatar: Optional[str] = None
    nickname: Optional[str] = None
    real_name: Optional[str] = None
    signature: Optional[str] = None
    college: Optional[str] = None
    class_name: Optional[str] = None
    email: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

    model_config = ConfigDict(from_attributes=True)


class AdminUserOut(UserOut):
    """管理员视角下的用户信息（含完整字段）"""
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
