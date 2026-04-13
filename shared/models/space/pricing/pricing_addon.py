"""
增值服务定价模型
"""

from sqlalchemy import Column, Integer, String, Boolean, Float, Text, ForeignKey

from ..base import Base, TimestampMixin


class PricingAddon(Base, TimestampMixin):
    """增值服务定价模型"""

    __tablename__ = "pricing_addons"

    id = Column(Integer, primary_key=True, index=True)

    addon_name = Column(String(100), nullable=False)
    addon_code = Column(String(50), unique=True)

    type_id = Column(Integer, ForeignKey("space_types.id"))

    addon_type = Column(String(20))

    pricing_method = Column(String(20))
    price = Column(Float, nullable=False)

    description = Column(Text)

    is_active = Column(Boolean, default=True)

    def __repr__(self):
        return f"<PricingAddon(id={self.id}, addon_name={self.addon_name})>"
