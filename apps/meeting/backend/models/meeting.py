"""会议室模型"""

from sqlalchemy import Column, Integer, String, Float, Boolean, Text, ForeignKey
from sqlalchemy.orm import relationship

from models.base import Base, TimestampMixin


class MeetingRoom(Base, TimestampMixin):
    """会议室模型"""

    __tablename__ = "meeting_rooms"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    location = Column(String(200))
    capacity = Column(Integer, default=10)
    facilities = Column(Text)  # JSON格式存储设施
    price_per_hour = Column(Float, default=0.0)
    member_price_per_hour = Column(Float, default=0.0)
    free_hours_per_month = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    requires_approval = Column(Boolean, default=False)

    # 关系
    bookings = relationship("MeetingBooking", back_populates="room")
