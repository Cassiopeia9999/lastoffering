from datetime import datetime

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float, ForeignKey, Enum
from sqlalchemy.orm import relationship

from backend.app.core.database import Base

ITEM_CATEGORIES = [
    "电子产品", "证件", "钥匙", "钱包/包", "书籍/文具",
    "衣物", "眼镜", "雨伞", "水杯/水壶", "运动用品",
    "首饰/饰品", "其他",
]


class Item(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True)
    type = Column(Enum("lost", "found"), nullable=False, comment="lost=失物 found=招领")
    title = Column(String(100), nullable=False, comment="物品标题")
    description = Column(Text, nullable=True, comment="详细描述")
    category = Column(String(32), nullable=True, comment="物品类别（AI识别，可手动改）")
    location = Column(String(128), nullable=True, comment="丢失/发现地点")
    happen_time = Column(DateTime, nullable=True, comment="丢失/发现时间")
    image_url = Column(String(256), nullable=True, comment="图片相对路径")
    feature_vector = Column(Text, nullable=True, comment="特征向量（JSON字符串）")
    status = Column(
        Enum("pending", "matched", "closed"),
        default="pending",
        nullable=False,
        comment="pending=待认领 matched=已匹配 closed=已关闭",
    )
    is_deleted = Column(Boolean, default=False, nullable=False, comment="软删除（下架）")
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    owner = relationship("User", backref="items")
