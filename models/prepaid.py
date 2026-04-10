"""
预付费相关模型
包含PrepaidPackage, PrepaidOrder, PrepaidPickup模型定义
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship
from datetime import datetime

from models.base import Base


class PrepaidPackage(Base):
    """预付套餐"""

    __tablename__ = "prepaid_packages"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    product_id = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)
    buy_quantity = Column(Integer, nullable=False)
    gift_quantity = Column(Integer, nullable=False)
    validity_days = Column(Integer, default=90)
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    is_active = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.now)


class PrepaidOrder(Base):
    """预付订单表"""

    __tablename__ = "prepaid_orders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    total_qty = Column(Integer, nullable=False)
    used_qty = Column(Integer, default=0)
    unit_price = Column(Float, nullable=False)
    total_amount = Column(Float, nullable=False)
    discount_amount = Column(Float, default=0)
    payment_status = Column(String, default="unpaid")  # unpaid, paid, refunded
    payment_method = Column(String, default="offline")  # offline, online, credit
    payment_at = Column(DateTime, nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    confirmed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    note = Column(String, nullable=True)
    is_active = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    user = relationship("User", foreign_keys=[user_id])
    product = relationship("Product")
    creator = relationship("User", foreign_keys=[created_by])
    pickups = relationship("PrepaidPickup", back_populates="order")


class PrepaidPickup(Base):
    """预付领取记录表"""

    __tablename__ = "prepaid_pickups"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("prepaid_orders.id"), nullable=False)
    pickup_qty = Column(Integer, nullable=False)
    picked_at = Column(DateTime, default=datetime.now)
    picked_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    note = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.now)

    order = relationship("PrepaidOrder", back_populates="pickups")
    picker = relationship("User", foreign_keys=[picked_by])
