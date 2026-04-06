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
    Time,
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
    user_type = Column(String(20), default="external")  # internal/external
    office_id = Column(Integer)  # 内部用户关联办公室
    user_name = Column(String(100), nullable=False)
    user_phone = Column(String(20))
    department = Column(String(100))
    booking_date = Column(Date, nullable=False, index=True)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    duration_hours = Column(Float)
    meeting_title = Column(String(200))
    attendees_count = Column(Integer, default=1)
    status = Column(String(20), default=BookingStatus.pending.value)
    total_fee = Column(Float, default=0.0)
    actual_fee = Column(Float, default=0.0)
    payment_status = Column(String(20), default="unpaid")
    payment_method = Column(String(20))
    notes = Column(Text)
    cancelled_at = Column(DateTime)
    cancelled_reason = Column(Text)

    # 关系
    room = relationship("MeetingRoom", back_populates="bookings")
