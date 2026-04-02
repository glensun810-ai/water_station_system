"""
用户相关模型
"""

from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime

from models.base import Base


class User(Base):
    """用户表"""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)
    department = Column(String, nullable=False)
    role = Column(String, default="staff")
    password_hash = Column(String, nullable=True)
    balance_credit = Column(Float, default=0)
    is_active = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.now)

    transactions = relationship(
        "Transaction", foreign_keys="Transaction.user_id", back_populates="user"
    )
    notifications = relationship("Notification", back_populates="user")
