from datetime import datetime

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float, ForeignKey, Enum
from sqlalchemy.orm import relationship

from backend.app.core.database import Base

ITEM_CATEGORIES = [
    "移动电子设备",  # mobile_device: 手机、平板
    "笔记本电脑",    # laptop
    "耳机",          # headphones
    "充电器/数据线", # charger
    "包类",          # bag: 背包、手提包、钱包
    "书籍",          # book
    "文具",          # stationery
    "证件",          # card: 学生证、身份证、银行卡
    "钥匙",          # keys
    "眼镜",          # glasses
    "饰品",          # accessory
    "水杯",          # bottle
    "雨伞",          # umbrella
    "衣物",          # clothes
    "其他",          # other
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
