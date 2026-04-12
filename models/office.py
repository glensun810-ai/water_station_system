"""
办公室相关模型
包含Office模型定义
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
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

    leader_name = Column(String(100), nullable=True)
    leader_phone = Column(String(20), nullable=True, comment="负责人电话")

    primary_admin_id = Column(
        Integer, ForeignKey("users.id"), nullable=True, comment="主要管理员用户ID"
    )

    water_user_count = Column(Integer, default=0)

    is_common = Column(Integer, default=1)

    is_active = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    admin_relations = relationship(
        "OfficeAdminRelation", back_populates="office", lazy="dynamic"
    )
