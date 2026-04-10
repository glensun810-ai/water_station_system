"""
退款记录相关模型
"""

from sqlalchemy import Column, Integer, String, DateTime, Enum, ForeignKey
from sqlalchemy.dialects.mysql import DECIMAL
from sqlalchemy.orm import relationship
from datetime import datetime

from models.base import Base


class RefundRecord(Base):
    """
    退款记录表
    """

    __tablename__ = "refund_records"

    id = Column(Integer, primary_key=True, index=True)
    refund_no = Column(String(64), unique=True, nullable=False, comment="退款单号")
    order_id = Column(
        Integer, ForeignKey("payment_orders.id"), nullable=False, comment="订单ID"
    )
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="用户ID")
    original_amount = Column(DECIMAL(10, 2), nullable=False, comment="原订单金额")
    refund_amount = Column(DECIMAL(10, 2), nullable=False, comment="退款金额")
    used_days = Column(Integer, nullable=True, comment="已使用天数")
    reason = Column(String(500), nullable=True, comment="退款原因")
    status = Column(
        Enum("pending", "success", "failed"), default="pending", comment="退款状态"
    )
    refund_at = Column(DateTime, nullable=True, comment="退款时间")
    refund_trade_no = Column(String(128), nullable=True, comment="第三方退款交易号")
    reject_reason = Column(String(500), nullable=True, comment="拒绝原因")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    order = relationship("PaymentOrder", foreign_keys=[order_id])
    user = relationship("User", foreign_keys=[user_id])
