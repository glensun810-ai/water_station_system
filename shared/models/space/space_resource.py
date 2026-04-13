"""
空间资源模型
管理具体的空间资源实例
"""

from sqlalchemy import Column, Integer, String, Boolean, Float, Text, ForeignKey
from sqlalchemy.orm import relationship

from .base import Base, TimestampMixin


class SpaceResource(Base, TimestampMixin):
    """空间资源模型"""

    __tablename__ = "space_resources"

    id = Column(Integer, primary_key=True, index=True)

    type_id = Column(Integer, ForeignKey("space_types.id"), nullable=False, index=True)

    name = Column(String(100), nullable=False)
    name_en = Column(String(100))
    location = Column(String(200))
    floor = Column(String(20))
    building = Column(String(100))

    capacity = Column(Integer, default=10)
    capacity_level = Column(String(20))

    facilities = Column(Text)
    facilities_status = Column(Text)

    base_price = Column(Float, default=0.0)
    price_unit = Column(String(20))
    member_price = Column(Float, default=0.0)
    vip_price = Column(Float, default=0.0)

    peak_time_price = Column(Float)
    off_peak_price = Column(Float)

    free_hours_per_month = Column(Integer, default=0)

    meal_standard_price = Column(Float)
    meal_vip_price = Column(Float)
    meal_luxury_price = Column(Float)

    booth_size = Column(String(20))
    booth_position = Column(String(20))

    venue_level = Column(String(20))
    setup_time_hours = Column(Integer, default=2)
    setup_fee_per_hour = Column(Float)

    photos = Column(Text)
    description = Column(Text)

    is_active = Column(Boolean, default=True, index=True)
    is_available = Column(Boolean, default=True)
    maintenance_status = Column(String(20), default="normal")
    maintenance_note = Column(Text)

    office_id = Column(Integer)

    space_type = relationship("SpaceType", back_populates="resources")
    bookings = relationship("SpaceBooking", back_populates="resource")

    def __repr__(self):
        return (
            f"<SpaceResource(id={self.id}, name={self.name}, type_id={self.type_id})>"
        )
