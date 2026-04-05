"""
办公室相关模型
包含Office模型定义
"""

from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime

from models.base import Base


class Office(Base):
    """
    办公室信息表

    存储办公室基本信息，用于办公室账户管理
    """

    __tablename__ = "office"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    room_number = Column(String(50), nullable=True)
    description = Column(String(500), nullable=True)

    # 负责人信息
    leader_name = Column(String(100), nullable=True)

    # 配置人数
    water_user_count = Column(Integer, default=0)

    # 常用标记
    is_common = Column(Integer, default=1)  # 1: 常用，0: 不常用

    # 超级管理员关联
    super_admin_id = Column(Integer, nullable=True)

    # 审计字段
    is_active = Column(Integer, default=1)  # 1: 启用，0: 禁用
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
