"""会议室预约模型"""

from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Boolean,
    Text,
    ForeignKey,
    Date,
    DateTime,
    Enum,
)
from sqlalchemy.orm import relationship
from datetime import date, time, datetime
import enum

from models.base import Base, TimestampMixin


class BookingStatus(str, enum.Enum):
    """预约状态"""

    pending = "pending"
    confirmed = "confirmed"
    completed = "completed"
    cancelled = "cancelled"
    rejected = "rejected"


class MeetingBooking(Base, TimestampMixin):
    """会议室预约模型"""

    __tablename__ = "meeting_bookings"

    id = Column(Integer, primary_key=True, index=True)
    booking_no = Column(String(50), unique=True, nullable=False, index=True)
    room_id = Column(Integer, ForeignKey("meeting_rooms.id"), nullable=False)
    room_name = Column(String(100))
    user_id = Column(Integer)
    user_type = Column(String(20), default="external")  # internal/external
    office_id = Column(Integer)  # 内部用户关联办公室
    user_name = Column(String(100), nullable=False)
    user_phone = Column(String(20))
    department = Column(String(100))
    booking_date = Column(Date, nullable=False, index=True)
    start_time = Column(String(10), nullable=False)
    end_time = Column(String(10), nullable=False)
    duration = Column(Float)  # 注意：实际列名是 duration
    meeting_title = Column(String(200))
    attendees_count = Column(Integer, default=1)
    status = Column(String(20), default=BookingStatus.pending.value)
    total_fee = Column(Float, default=0.0)
    actual_fee = Column(Float, default=0.0)
    payment_status = Column(String(20), default="unpaid")
    payment_method = Column(String(50))
    cancel_reason = Column(String(500))
    cancelled_at = Column(DateTime)
    can_modify = Column(Boolean, default=True)
    can_cancel = Column(Boolean, default=True)
    cancel_deadline = Column(String(20))
    is_free = Column(Integer, default=0)
    free_hours_used = Column(Float, default=0)
    discount_amount = Column(Float, default=0)
    payment_mode = Column(String(20))
    payment_amount = Column(Float, default=0)
    payment_time = Column(DateTime)
    payment_evidence = Column(Text)
    payment_remark = Column(Text)
    confirmed_by = Column(String(100))
    confirmed_at = Column(DateTime)
    reviewer_id = Column(Integer)
    reviewed_at = Column(DateTime)
    settlement_batch_id = Column(Integer)
    is_deleted = Column(Integer, default=0)
    deleted_at = Column(DateTime)
    deleted_by = Column(String(100))
    delete_reason = Column(String(500))
    cancel_detail = Column(Text)

    # 关系
    room = relationship("MeetingRoom", back_populates="bookings")
