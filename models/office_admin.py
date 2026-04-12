"""
办公室管理员关联模型
支持一个用户配置为多个办公室的管理员
"""

from sqlalchemy import Column, Integer, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime

from models.base import Base


class OfficeAdminRelation(Base):
    """
    办公室管理员关联表

    支持一个用户管理多个办公室
    支持一个办公室有多个管理员
    """

    __tablename__ = "office_admin_relations"
    __table_args__ = (
        UniqueConstraint("office_id", "user_id", name="unique_office_admin"),
    )

    id = Column(Integer, primary_key=True, index=True)
    office_id = Column(
        Integer, ForeignKey("office.id"), nullable=False, index=True, comment="办公室ID"
    )
    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        index=True,
        comment="管理员用户ID",
    )
    is_primary = Column(Integer, default=0, comment="是否主要管理员(负责人)")
    role_type = Column(
        Integer, default=1, comment="管理员类型: 1=负责人 2=行政对接人 3=其他"
    )
    created_at = Column(DateTime, default=datetime.now)

    office = relationship("Office", back_populates="admin_relations")
    admin_user = relationship("User", back_populates="managed_offices")
