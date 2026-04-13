"""
通知模型
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from datetime import datetime

from .base import Base, TimestampMixin


class Notification(Base, TimestampMixin):
    """通知模型"""

    __tablename__ = "space_notifications"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)

    booking_id = Column(Integer, ForeignKey("space_bookings.id"))

    recipient_id = Column(Integer, index=True)
    recipient_email = Column(String(100))
    recipient_phone = Column(String(20))

    notification_type = Column(String(50), nullable=False)
    notification_category = Column(String(20))

    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)

    channels = Column(String(50))

    status = Column(String(20), default="pending", index=True)

    scheduled_at = Column(DateTime)
    sent_at = Column(DateTime)
    read_at = Column(DateTime)

    delivery_status = Column(Text)
    error_message = Column(Text)

    related_data = Column(Text)

    def __repr__(self):
        return f"<Notification(id={self.id}, type={self.notification_type}, status={self.status})>"
