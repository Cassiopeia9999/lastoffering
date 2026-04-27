import json
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.types import TypeDecorator

from backend.app.core.database import Base

ITEM_CATEGORIES = [
    "移动电子设备",
    "笔记本电脑",
    "耳机",
    "充电器/数据线",
    "包类",
    "书籍",
    "文具",
    "证件",
    "钥匙",
    "眼镜",
    "饰品",
    "水杯",
    "雨伞",
    "衣物",
    "其他",
]


class JSONListType(TypeDecorator):
    impl = Text
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if isinstance(value, str):
            value = [value]
        elif not isinstance(value, (list, tuple, set)):
            value = [str(value)]
        cleaned = [str(item).strip() for item in value if str(item).strip()]
        return json.dumps(cleaned, ensure_ascii=False)

    def process_result_value(self, value, dialect):
        if not value:
            return []
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
        try:
            parsed = json.loads(value)
        except (TypeError, json.JSONDecodeError):
            parsed = value
        if isinstance(parsed, list):
            return [str(item).strip() for item in parsed if str(item).strip()]
        return [segment.strip() for segment in str(parsed).split(",") if segment.strip()]


class Item(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True)
    type = Column(Enum("lost", "found"), nullable=False, comment="lost=失物 found=招领")
    title = Column(String(100), nullable=False, comment="物品标题")
    description = Column(Text, nullable=True, comment="详细描述")
    category = Column(String(32), nullable=True, comment="物品类别")
    color = Column(String(32), nullable=True, comment="颜色")
    brand = Column(String(64), nullable=True, comment="品牌")
    keywords = Column(JSONListType, nullable=True, comment="关键词列表(JSON)")
    feature_text = Column(Text, nullable=True, comment="典型特征摘要")
    location = Column(String(128), nullable=True, comment="丢失/发现地点")
    happen_time = Column(DateTime, nullable=True, comment="丢失/发现时间")
    image_url = Column(String(256), nullable=True, comment="图片相对路径")
    feature_vector = Column(Text, nullable=True, comment="图像特征向量(JSON字符串)")
    status = Column(
        Enum("pending", "matched", "closed"),
        default="pending",
        nullable=False,
        comment="pending=待处理 matched=已匹配 closed=已完成",
    )
    is_deleted = Column(Boolean, default=False, nullable=False, comment="是否下架")
    owner_deleted = Column(Boolean, default=False, nullable=False, comment="是否被发布者删除")
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    owner = relationship("User", backref="items")
