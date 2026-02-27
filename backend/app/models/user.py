from sqlalchemy import Column, Integer, String, Boolean
from backend.app.core.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(32), unique=True, index=True, nullable=False)
    password_hash = Column(String(128), nullable=False)
    contact = Column(String(64), nullable=False)
    is_admin = Column(Boolean, default=False)
