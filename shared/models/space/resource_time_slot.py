"""
资源可用时段模型
定义每个空间资源的可预订时段配置
"""

from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey
from sqlalchemy.orm import relationship

from .base import Base, TimestampMixin


class ResourceTimeSlot(Base, TimestampMixin):
    """资源可用时段"""

    __tablename__ = "resource_time_slots"

    id = Column(Integer, primary_key=True, index=True)
    resource_id = Column(Integer, ForeignKey("space_resources.id"), nullable=False, index=True)

    slot_key = Column(String(50), nullable=False)
    slot_name = Column(String(50))

    slot_type = Column(String(20), nullable=False, default="fixed_time")
    start_time = Column(String(10))
    end_time = Column(String(10))

    duration_value = Column(Float, default=1)
    duration_unit = Column(String(20), default="hour")

    max_bookings_per_slot = Column(Integer, default=1)
    applicable_days = Column(String(50))
    price_override = Column(Float)

    is_active = Column(Boolean, default=True)
    sort_order = Column(Integer, default=0)

    resource = relationship("SpaceResource", back_populates="time_slots")

    def __repr__(self):
        return f"<ResourceTimeSlot(id={self.id}, slot_key={self.slot_key}, resource_id={self.resource_id})>"
