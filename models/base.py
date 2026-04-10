"""
统一基础模型
所有SQLAlchemy模型继承自此Base
"""

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, DateTime
from datetime import datetime

Base = declarative_base()


class TimestampMixin:
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.now, onupdate=datetime.now, nullable=False
    )


class SoftDeleteMixin:
    is_deleted = Column(DateTime, nullable=True)
    deleted_at = Column(DateTime, nullable=True)
    deleted_by = Column(DateTime, nullable=True)
    delete_reason = Column(DateTime, nullable=True)
