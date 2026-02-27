from datetime import datetime

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship

from backend.app.core.database import Base


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    type = Column(String(32), nullable=False, comment="通知类型：match_found/item_matched/contact_shared/system")
    content = Column(Text, nullable=False)
    related_item_id = Column(Integer, ForeignKey("items.id"), nullable=True)
    related_match_id = Column(Integer, nullable=True, comment="关联匹配记录ID")
    is_read = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", backref="notifications")
    related_item = relationship("Item", backref="notifications")
