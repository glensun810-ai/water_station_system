"""会议室审批和支付模型"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from models.base import Base, TimestampMixin


class MeetingApproval(Base, TimestampMixin):
    """会议室审批模型"""

    __tablename__ = "meeting_approvals"

    id = Column(Integer, primary_key=True, index=True)
    approval_no = Column(String(50), unique=True, nullable=False, index=True)
    booking_id = Column(Integer, ForeignKey("meeting_bookings.id"), nullable=False)
    approver_id = Column(Integer)  # 审批人ID
    approver_name = Column(String(100))
    status = Column(String(20), default="pending")  # pending/approved/rejected
    notes = Column(Text)
    approved_at = Column(DateTime)
    rejected_at = Column(DateTime)
    reject_reason = Column(Text)


class MeetingPayment(Base, TimestampMixin):
    """会议室支付模型"""

    __tablename__ = "meeting_payments"

    id = Column(Integer, primary_key=True, index=True)
    payment_no = Column(String(50), unique=True, nullable=False, index=True)
    booking_id = Column(Integer, ForeignKey("meeting_bookings.id"), nullable=False)
    user_id = Column(Integer)  # 用户ID
    user_name = Column(String(100))
    amount = Column(Float, nullable=False)
    payment_method = Column(String(20))  # cash/credit_card/wechat/alipay
    payment_status = Column(String(20), default="unpaid")  # unpaid/paid/refunded
    paid_at = Column(DateTime)
    transaction_id = Column(String(100))
    notes = Column(Text)
