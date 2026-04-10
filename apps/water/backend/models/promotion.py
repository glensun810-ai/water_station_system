"""
优惠促销模型
"""

from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime

from models.base import Base


class Promotion(Base):
    """优惠促销表"""

    __tablename__ = "promotions"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    trigger_qty = Column(Integer, nullable=False)
    gift_qty = Column(Integer, nullable=False)
    description = Column(String)
    is_active = Column(Integer, default=1)

    product = relationship("Product")


class PromotionConfig(Base):
    """优惠配置表 - 支持按模式配置不同优惠"""

    __tablename__ = "promotion_config"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    mode = Column(String(20), nullable=False, default="pay_later")
    trigger_qty = Column(Integer, nullable=False, default=10)
    gift_qty = Column(Integer, nullable=False, default=0)
    discount_rate = Column(Float, nullable=False, default=100.0)
    is_active = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    product = relationship("Product")
