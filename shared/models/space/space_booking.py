"""
空间预约模型
记录所有空间预约信息
"""

import enum
from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    Float,
    Text,
    ForeignKey,
    Date,
    DateTime,
)
from sqlalchemy.orm import relationship
from datetime import datetime, date

from .base import Base, TimestampMixin


class BookingStatus(str, enum.Enum):
    """预约状态枚举"""

    pending_approval = "pending_approval"
    approved = "approved"
    rejected = "rejected"
    deposit_paid = "deposit_paid"
    confirmed = "confirmed"
    cancelled = "cancelled"
    in_use = "in_use"
    completed = "completed"
    settled = "settled"


class PaymentStatus(str, enum.Enum):
    """支付状态枚举"""

    unpaid = "unpaid"
    deposit_paid = "deposit_paid"
    balance_pending = "balance_pending"
    fully_paid = "fully_paid"
    refunded = "refunded"


class SettlementStatus(str, enum.Enum):
    """结算状态枚举"""

    unsettled = "unsettled"
    pending = "pending"
    applied = "applied"
    confirmed = "confirmed"
    settled = "settled"


class SpaceBooking(Base, TimestampMixin):
    """空间预约模型"""

    __tablename__ = "space_bookings"

    id = Column(Integer, primary_key=True, index=True)

    booking_no = Column(String(50), unique=True, nullable=False, index=True)

    resource_id = Column(
        Integer, ForeignKey("space_resources.id"), nullable=False, index=True
    )
    resource_name = Column(String(100))
    type_id = Column(Integer)
    type_code = Column(String(50))

    user_id = Column(Integer, index=True)
    user_type = Column(String(20), default="external")
    user_name = Column(String(100), nullable=False)
    user_phone = Column(String(20))
    user_email = Column(String(100))
    department = Column(String(100))
    office_id = Column(Integer)

    booking_date = Column(Date, nullable=False, index=True)
    start_time = Column(String(10), nullable=False)
    end_time = Column(String(10), nullable=False)
    duration = Column(Float)
    duration_unit = Column(String(20))

    end_date = Column(Date)
    booking_days = Column(Integer, default=1)

    meal_session = Column(String(20))
    meal_standard = Column(String(20))
    guests_count = Column(Integer, default=1)

    content_type = Column(String(50))
    content_url = Column(String(200))
    content_approved = Column(Boolean, default=False)
    play_frequency = Column(Integer, default=1)

    exhibition_type = Column(String(50))
    exhibition_plan_url = Column(String(200))

    purpose = Column(String(200))
    title = Column(String(200))
    attendees_count = Column(Integer, default=1)
    attendees_info = Column(Text)

    special_requests = Column(Text)
    addons_selected = Column(Text)

    base_fee = Column(Float, default=0.0)
    addon_fee = Column(Float, default=0.0)
    discount_amount = Column(Float, default=0.0)
    total_fee = Column(Float, default=0.0)
    actual_fee = Column(Float, default=0.0)
    fee_unit = Column(String(20))

    requires_deposit = Column(Boolean, default=False)
    deposit_amount = Column(Float, default=0.0)
    deposit_paid = Column(Boolean, default=False)
    deposit_paid_at = Column(DateTime)
    deposit_payment_method = Column(String(20))
    deposit_refunded = Column(Boolean, default=False)
    deposit_refund_amount = Column(Float)
    deposit_refund_at = Column(DateTime)

    balance_amount = Column(Float, default=0.0)
    balance_paid = Column(Boolean, default=False)
    balance_paid_at = Column(DateTime)
    balance_payment_method = Column(String(20))

    status = Column(String(20), default="pending_approval", index=True)
    payment_status = Column(String(20), default="unpaid")
    settlement_status = Column(String(20), default="unsettled")

    approval_id = Column(Integer)
    approved_by = Column(String(100))
    approved_at = Column(DateTime)
    approval_notes = Column(Text)
    rejected_reason = Column(Text)
    rejected_at = Column(DateTime)

    confirmed_at = Column(DateTime)
    confirmed_by = Column(String(100))

    cancelled_at = Column(DateTime)
    cancelled_by = Column(String(100))
    cancel_reason = Column(String(500))
    cancel_type = Column(String(20))

    checked_in_at = Column(DateTime)
    checked_in_by = Column(String(100))
    started_at = Column(DateTime)
    ended_at = Column(DateTime)
    actual_duration = Column(Float)

    completed_at = Column(DateTime)
    completion_notes = Column(Text)

    rated_at = Column(DateTime)
    rating_score = Column(Float)
    rating_feedback = Column(Text)

    invoice_requested = Column(Boolean, default=False)
    invoice_status = Column(String(20))
    invoice_id = Column(Integer)
    invoice_info = Column(Text)

    settlement_id = Column(Integer)
    settled_at = Column(DateTime)

    can_modify = Column(Boolean, default=True)
    can_cancel = Column(Boolean, default=True)
    cancel_deadline = Column(DateTime)
    modify_deadline = Column(DateTime)

    user_payment_confirmed = Column(Boolean, default=False)
    user_payment_confirmed_at = Column(DateTime)
    admin_payment_verified = Column(Boolean, default=False)
    admin_payment_verified_at = Column(DateTime)
    admin_payment_verified_by = Column(String(100))

    is_deleted = Column(Integer, default=0, index=True)
    deleted_at = Column(DateTime)
    deleted_by = Column(String(100))
    delete_reason = Column(String(500))

    booking_source = Column(String(20))
    booking_channel = Column(String(20))

    calendar_invite_sent = Column(Boolean, default=False)
    calendar_invite_id = Column(String(100))

    resource = relationship("SpaceResource", back_populates="bookings")

    def __repr__(self):
        return f"<SpaceBooking(id={self.id}, booking_no={self.booking_no}, status={self.status})>"
