"""
空间服务基础模型
"""

from datetime import datetime
from sqlalchemy import Column, DateTime

# 使用统一的Base（从models.base导入）
from models.base import Base


class TimestampMixin:
    """时间戳混入类"""

    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.now, onupdate=datetime.now, nullable=False
    )
