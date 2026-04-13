"""
用户空间使用额度模型
"""

from sqlalchemy import Column, Integer, Float, String, ForeignKey
from sqlalchemy.orm import relationship

from .base import Base, TimestampMixin


class UserSpaceQuota(Base, TimestampMixin):
    """用户空间额度模型"""

    __tablename__ = "user_space_quota"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    type_id = Column(Integer, ForeignKey("space_types.id"))

    free_quota_monthly = Column(Float, default=0.0)
    free_quota_used = Column(Float, default=0.0)
    free_quota_remaining = Column(Float)

    quota_month = Column(String(7), index=True)

    def __repr__(self):
        return f"<UserSpaceQuota(id={self.id}, user_id={self.user_id}, quota_month={self.quota_month})>"
