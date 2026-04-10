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

    # 负责人信息（可以是外部人员，不一定在系统中）
    leader_name = Column(String(100), nullable=True)
    leader_phone = Column(String(20), nullable=True, comment="负责人电话")

    # 主要管理员（系统用户，默认办公室管理员）
    primary_admin_id = Column(Integer, nullable=True, comment="主要管理员用户ID")

    # 配置人数
    water_user_count = Column(Integer, default=0)

    # 常用标记
    is_common = Column(Integer, default=1)

    # 审计字段
    is_active = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
