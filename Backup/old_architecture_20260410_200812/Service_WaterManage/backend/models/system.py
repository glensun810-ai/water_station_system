"""
系统相关模型
包含DeleteLog, Notification等系统模型定义
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime

from models.base import Base


class DeleteLog(Base):
    """删除日志"""

    __tablename__ = "delete_logs"

    id = Column(Integer, primary_key=True, index=True)
    table_name = Column(String(50), nullable=False)
    record_id = Column(Integer, nullable=False)
    record_data = Column(Text)
    deleted_by = Column(Integer, ForeignKey("users.id"))
    deleted_at = Column(DateTime, default=datetime.now)
    reason = Column(String(500))


class Notification(Base):
    """通知"""

    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(200), nullable=False)
    content = Column(Text)
    type = Column(String(50))  # info, warning, error
    is_read = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.now)

    user = relationship("User", back_populates="notifications")
