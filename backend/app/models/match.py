from datetime import datetime

from sqlalchemy import Column, Integer, Float, DateTime, Enum, ForeignKey
from sqlalchemy.orm import relationship

from backend.app.core.database import Base


class Match(Base):
    __tablename__ = "matches"

    id = Column(Integer, primary_key=True, index=True)
    lost_item_id = Column(Integer, ForeignKey("items.id"), nullable=False)
    found_item_id = Column(Integer, ForeignKey("items.id"), nullable=False)
    similarity = Column(Float, nullable=True, comment="余弦相似度（0~1）")
    status = Column(
        Enum("pending", "confirmed", "rejected"),
        default="pending",
        nullable=False,
        comment="pending=待确认 confirmed=已确认 rejected=已拒绝",
    )
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    lost_item = relationship("Item", foreign_keys=[lost_item_id], backref="lost_matches")
    found_item = relationship("Item", foreign_keys=[found_item_id], backref="found_matches")
