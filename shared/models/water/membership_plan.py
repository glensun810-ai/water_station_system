"""
会员套餐相关模型
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime
from sqlalchemy.dialects.mysql import DECIMAL, JSON
from datetime import datetime

from models.base import Base


class MembershipPlan(Base):
    """
    会员套餐表
    """

    __tablename__ = "membership_plans"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, comment="套餐名称")
    description = Column(Text, nullable=True, comment="套餐描述")
    price = Column(DECIMAL(10, 2), nullable=False, comment="价格（元）")
    original_price = Column(DECIMAL(10, 2), nullable=True, comment="原价（元）")
    duration_months = Column(Integer, nullable=False, comment="有效期（月）")
    features = Column(JSON, nullable=True, comment="套餐权益")
    icon = Column(String(50), nullable=True, default="👑", comment="套餐图标")
    is_active = Column(Boolean, default=True, comment="是否启用")
    sort_order = Column(Integer, default=0, comment="排序")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
