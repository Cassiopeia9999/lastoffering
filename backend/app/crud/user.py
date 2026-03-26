from typing import Optional, List

from sqlalchemy.orm import Session

from backend.app.models.user import User
from backend.app.core.password import hash_password, verify_password


def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_username(db: Session, username: str) -> Optional[User]:
    return db.query(User).filter(User.username == username).first()


def get_all_users(db: Session, skip: int = 0, limit: int = 50) -> List[User]:
    return db.query(User).offset(skip).limit(limit).all()


def create_user(db: Session, username: str, password: str, contact: str) -> User:
    user = User(
        username=username,
        password_hash=hash_password(password),
        contact=contact,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def verify_user(db: Session, username: str, password: str) -> Optional[User]:
    user = get_user_by_username(db, username)
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    if not user.is_active:
        return None
    return user


def update_user_contact(db: Session, user: User, contact: str) -> User:
    user.contact = contact
    db.commit()
    db.refresh(user)
    return user


def update_user_password(db: Session, user: User, new_password: str) -> User:
    user.password_hash = hash_password(new_password)
    db.commit()
    db.refresh(user)
    return user


def update_user_profile(db: Session, user: User, data: dict) -> User:
    """更新用户扩展资料（昵称/签名/真实姓名/学院/班级/邮箱/联系方式/密码）"""
    field_map = ["contact", "nickname", "real_name", "signature", "college", "class_name", "email"]
    for field in field_map:
        if field in data and data[field] is not None:
            setattr(user, field, data[field])
    if data.get("password"):
        user.password_hash = hash_password(data["password"])
    db.commit()
    db.refresh(user)
    return user


def update_user_avatar(db: Session, user: User, avatar_path: str) -> User:
    """更新用户头像路径"""
    user.avatar = avatar_path
    db.commit()
    db.refresh(user)
    return user


def set_user_active(db: Session, user_id: int, is_active: bool) -> Optional[User]:
    user = get_user_by_id(db, user_id)
    if not user:
        return None
    user.is_active = is_active
    db.commit()
    db.refresh(user)
    return user


def reset_user_password(db: Session, user_id: int, new_password: str) -> Optional[User]:
    """管理员重置用户密码"""
    user = get_user_by_id(db, user_id)
    if not user:
        return None
    user.password_hash = hash_password(new_password)
    db.commit()
    db.refresh(user)
    return user
