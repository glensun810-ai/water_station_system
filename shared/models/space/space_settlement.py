"""
空间结算模型
记录月度结算信息
"""

from sqlalchemy import Column, Integer, String, Float, Text, Boolean, Date, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime, date

from .base import Base, TimestampMixin


class SpaceSettlement(Base, TimestampMixin):
    """空间结算模型"""

    __tablename__ = "space_settlements"

    id = Column(Integer, primary_key=True, index=True)

    settlement_no = Column(String(50), unique=True, nullable=False, index=True)

    settlement_month = Column(String(7), nullable=False, index=True)
    settlement_year = Column(Integer)
    settlement_period_start = Column(Date)
    settlement_period_end = Column(Date)

    booking_ids = Column(Text)
    booking_count = Column(Integer)

    user_id = Column(Integer)
    department = Column(String(100))
    office_id = Column(Integer)
    settlement_scope = Column(String(20))

    total_amount = Column(Float, nullable=False)
    paid_amount = Column(Float, default=0.0)
    pending_amount = Column(Float)
    discount_amount = Column(Float, default=0.0)
    free_quota_used = Column(Float, default=0.0)

    status = Column(String(20), default="pending", index=True)

    applied_at = Column(DateTime)
    applied_by = Column(String(100))

    approved_at = Column(DateTime)
    approved_by = Column(String(100))
    approval_notes = Column(Text)

    processed_at = Column(DateTime)
    processed_by = Column(String(100))
    completed_at = Column(DateTime)

    payment_method = Column(String(20))
    payment_transaction_id = Column(String(100))
    payment_receipt_url = Column(String(200))

    invoice_required = Column(Boolean, default=False)
    invoice_status = Column(String(20))
    invoice_id = Column(Integer)

    notes = Column(Text)

    def __repr__(self):
        return f"<SpaceSettlement(id={self.id}, settlement_no={self.settlement_no}, status={self.status})>"
