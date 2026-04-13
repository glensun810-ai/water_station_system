"""
折扣规则模型
"""

from sqlalchemy import Column, Integer, String, Boolean, Float, Text, DateTime

from ..base import Base, TimestampMixin


class PricingDiscount(Base, TimestampMixin):
    """折扣规则模型"""

    __tablename__ = "pricing_discounts"

    id = Column(Integer, primary_key=True, index=True)

    discount_name = Column(String(100), nullable=False)
    discount_code = Column(String(50), unique=True)

    discount_type = Column(String(20))

    discount_value = Column(Float)
    discount_unit = Column(String(10))

    conditions = Column(Text)

    effective_from = Column(DateTime)
    effective_to = Column(DateTime)

    is_active = Column(Boolean, default=True)

    def __repr__(self):
        return f"<PricingDiscount(id={self.id}, discount_name={self.discount_name})>"
