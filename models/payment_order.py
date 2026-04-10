"""
支付订单相关模型
"""

from sqlalchemy import Column, Integer, String, DateTime, Enum, ForeignKey
from sqlalchemy.dialects.mysql import DECIMAL
from sqlalchemy.orm import relationship
from datetime import datetime

from models.base import Base


class PaymentOrder(Base):
    """
    支付订单表
    """

    __tablename__ = "payment_orders"

    id = Column(Integer, primary_key=True, index=True)
    order_no = Column(String(64), unique=True, nullable=False, comment="订单号")
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="用户ID")
    plan_id = Column(
        Integer, ForeignKey("membership_plans.id"), nullable=False, comment="会员套餐ID"
    )
    amount = Column(DECIMAL(10, 2), nullable=False, comment="订单金额")
    payment_method = Column(Enum("alipay", "wechat"), nullable=True, comment="支付方式")
    status = Column(
        Enum("pending", "paid", "cancelled", "refunded"),
        default="pending",
        comment="订单状态",
    )
    paid_at = Column(DateTime, nullable=True, comment="支付时间")
    trade_no = Column(String(128), nullable=True, comment="第三方交易号")
    cancel_reason = Column(String(500), nullable=True, comment="取消原因")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    user = relationship("User", foreign_keys=[user_id])
    plan = relationship("MembershipPlan", foreign_keys=[plan_id])
