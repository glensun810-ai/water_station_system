"""
空间支付模型
记录支付交易详情
"""

import enum
from sqlalchemy import Column, Integer, String, Float, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime

from .base import Base, TimestampMixin


class PaymentType(str, enum.Enum):
    """支付类型枚举"""

    deposit = "deposit"
    balance = "balance"
    full = "full"
    refund = "refund"


class SpacePayment(Base, TimestampMixin):
    """空间支付模型"""

    __tablename__ = "space_payments"

    id = Column(Integer, primary_key=True, index=True)

    payment_no = Column(String(50), unique=True, nullable=False, index=True)

    booking_id = Column(
        Integer, ForeignKey("space_bookings.id"), nullable=False, index=True
    )
    booking_no = Column(String(50))

    user_id = Column(Integer)
    user_name = Column(String(100))

    payment_type = Column(String(20), nullable=False)
    payment_purpose = Column(String(50))

    amount = Column(Float, nullable=False)
    currency = Column(String(10), default="CNY")

    payment_method = Column(String(20))
    payment_channel = Column(String(20))

    status = Column(String(20), default="pending", index=True)

    initiated_at = Column(DateTime, default=datetime.now)
    processed_at = Column(DateTime)
    completed_at = Column(DateTime)
    failed_at = Column(DateTime)
    refunded_at = Column(DateTime)

    transaction_id = Column(String(100))
    receipt_no = Column(String(50))
    receipt_url = Column(String(200))
    proof_url = Column(String(200))

    notes = Column(Text)
    failure_reason = Column(Text)
    refund_reason = Column(Text)

    refund_amount = Column(Float)
    refund_status = Column(String(20))
    refund_transaction_id = Column(String(100))

    verified_by = Column(String(100))
    verified_at = Column(DateTime)
    verification_notes = Column(Text)

    booking = relationship("SpaceBooking", backref="payments")

    def __repr__(self):
        return f"<SpacePayment(id={self.id}, payment_no={self.payment_no}, status={self.status})>"
