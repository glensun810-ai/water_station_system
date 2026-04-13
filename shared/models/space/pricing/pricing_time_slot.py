"""
时段定价模型
"""

from sqlalchemy import Column, Integer, String, Boolean, Float, ForeignKey

from ..base import Base, TimestampMixin


class PricingTimeSlot(Base, TimestampMixin):
    """时段定价模型"""

    __tablename__ = "pricing_time_slots"

    id = Column(Integer, primary_key=True, index=True)

    type_id = Column(Integer, ForeignKey("space_types.id"))

    slot_name = Column(String(50), nullable=False)
    slot_type = Column(String(20))

    start_time = Column(String(10))
    end_time = Column(String(10))

    price_multiplier = Column(Float, default=1.0)

    applicable_days = Column(String(50))

    is_active = Column(Boolean, default=True)

    def __repr__(self):
        return f"<PricingTimeSlot(id={self.id}, slot_name={self.slot_name})>"
