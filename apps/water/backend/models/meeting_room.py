"""
会议室模型
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean
from datetime import datetime
from models.base import Base


class MeetingRoom(Base):
    """会议室表"""

    __tablename__ = "meeting_rooms"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    location = Column(String(100))
    capacity = Column(Integer, default=10)
    facilities = Column(Text)
    price_per_hour = Column(Float, default=0.0)
    member_price_per_hour = Column(Float, default=0.0)
    free_hours_per_month = Column(Integer, default=0)
    is_active = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class MeetingBooking(Base):
    """会议室预订表"""

    __tablename__ = "meeting_bookings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    booking_no = Column(String(50), unique=True)
    room_id = Column(Integer, nullable=False)
    room_name = Column(String(100))
    user_id = Column(Integer)
    user_name = Column(String(100))
    user_phone = Column(String(20))
    department = Column(String(100))
    booking_date = Column(DateTime, nullable=False)
    start_time = Column(String(10), nullable=False)
    end_time = Column(String(10), nullable=False)
    duration = Column(Float, default=1.0)
    meeting_title = Column(String(200))
    attendees_count = Column(Integer, default=1)
    total_fee = Column(Float, default=0.0)
    status = Column(String(20), default="pending")
    cancel_reason = Column(String(500))
    user_type = Column(String(20), default="external")
    office_id = Column(Integer)
    can_modify = Column(Boolean, default=True)
    can_cancel = Column(Boolean, default=True)
    cancel_deadline = Column(String(20))
    reviewer_id = Column(Integer)
    reviewed_at = Column(DateTime)
    payment_status = Column(String(20), default="unpaid")
    payment_mode = Column(String(20), default="credit")
    payment_amount = Column(Float, default=0.0)
    payment_method = Column(String(50))
    payment_time = Column(DateTime)
    payment_evidence = Column(Text)
    payment_remark = Column(Text)
    confirmed_by = Column(String(100))
    confirmed_at = Column(DateTime)
    is_free = Column(Integer, default=0)
    free_hours_used = Column(Float, default=0.0)
    actual_fee = Column(Float, default=0.0)
    discount_amount = Column(Float, default=0.0)
    settlement_batch_id = Column(Integer)
    is_deleted = Column(Integer, default=0)
    deleted_at = Column(DateTime)
    deleted_by = Column(String(100))
    delete_reason = Column(String(500))
    cancel_detail = Column(Text)
    cancelled_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class MeetingRoomStatistics(Base):
    """会议室统计表"""

    __tablename__ = "meeting_room_statistics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    room_id = Column(Integer, nullable=False)
    room_name = Column(String(100))
    total_bookings = Column(Integer, default=0)
    total_hours = Column(Float, default=0.0)
    total_revenue = Column(Float, default=0.0)
    utilization_rate = Column(Float, default=0.0)
    month = Column(String(7))
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
