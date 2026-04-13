"""
空间类型模型
定义系统支持的所有空间类型及其配置规则
"""

from sqlalchemy import Column, Integer, String, Boolean, Float, Text
from sqlalchemy.orm import relationship

from .base import Base, TimestampMixin


class SpaceType(Base, TimestampMixin):
    """空间类型模型"""

    __tablename__ = "space_types"

    id = Column(Integer, primary_key=True, index=True)

    type_code = Column(String(50), unique=True, nullable=False)
    type_name = Column(String(100), nullable=False)
    type_name_en = Column(String(100))
    description = Column(Text)

    min_duration_unit = Column(String(20), nullable=False)
    min_duration_value = Column(Integer, default=1)
    max_duration_value = Column(Integer, default=24)
    advance_booking_days = Column(Integer, default=0)

    min_capacity = Column(Integer, default=1)
    max_capacity = Column(Integer, default=500)

    requires_approval = Column(Boolean, default=False)
    approval_type = Column(String(20))
    approval_deadline_hours = Column(Integer, default=24)

    requires_deposit = Column(Boolean, default=False)
    deposit_percentage = Column(Float, default=0.0)
    deposit_refund_rules = Column(Text)

    standard_facilities = Column(Text)
    optional_addons = Column(Text)

    is_active = Column(Boolean, default=True)
    sort_order = Column(Integer, default=0)

    icon = Column(String(50))
    color_theme = Column(String(20))

    resources = relationship("SpaceResource", back_populates="space_type")

    def __repr__(self):
        return f"<SpaceType(id={self.id}, type_code={self.type_code}, type_name={self.type_name})>"
