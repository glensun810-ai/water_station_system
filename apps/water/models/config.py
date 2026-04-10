"""
系统配置相关模型
包含SystemConfig模型定义
"""

from sqlalchemy import Column, Integer, String, DateTime, Text
from datetime import datetime

from models.base import Base


class SystemConfig(Base):
    """
    系统配置表 - 存储全局配置如收款二维码等
    """

    __tablename__ = "system_config"

    id = Column(Integer, primary_key=True, index=True)
    config_key = Column(String(100), unique=True, nullable=False)
    config_value = Column(Text, nullable=True)
    description = Column(String(500), nullable=True)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
