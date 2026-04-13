"""
用户会员信息模型
"""

from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    Float,
    Text,
    ForeignKey,
    DateTime,
)
from sqlalchemy.orm import relationship
from datetime import datetime

from .base import Base, TimestampMixin


class UserMemberInfo(Base, TimestampMixin):
    """用户会员信息模型"""

    __tablename__ = "user_member_info"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)

    member_level = Column(String(20), default="regular")
    member_since = Column(DateTime)
    member_expire = Column(DateTime)

    discount_rate = Column(Float, default=1.0)

    free_hours_monthly = Column(Integer, default=0)
    priority_booking = Column(Boolean, default=False)
    exclusive_spaces = Column(Text)

    def __repr__(self):
        return f"<UserMemberInfo(id={self.id}, user_id={self.user_id}, member_level={self.member_level})>"
