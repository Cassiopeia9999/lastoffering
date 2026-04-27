from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, String

from backend.app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(32), unique=True, index=True, nullable=False)
    password_hash = Column(String(128), nullable=False)
    contact = Column(String(64), nullable=False, comment="联系方式")
    is_admin = Column(Boolean, default=False, nullable=False)
    is_superadmin = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False, comment="账号是否启用")

    avatar = Column(String(256), nullable=True, comment="头像图片路径")
    nickname = Column(String(32), nullable=True, comment="昵称")
    real_name = Column(String(32), nullable=True, comment="真实姓名")
    signature = Column(String(128), nullable=True, comment="个性签名")
    college = Column(String(64), nullable=True, comment="学院")
    class_name = Column(String(32), nullable=True, comment="班级")
    email = Column(String(64), nullable=True, comment="邮箱")

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
