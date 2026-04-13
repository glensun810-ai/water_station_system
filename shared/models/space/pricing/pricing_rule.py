"""
定价规则模型
"""

from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    Float,
    Text,
    ForeignKey,
    DateTime,
)
from datetime import datetime

from ..base import Base, TimestampMixin


class PricingRule(Base, TimestampMixin):
    """定价规则模型"""

    __tablename__ = "pricing_rules"

    id = Column(Integer, primary_key=True, index=True)

    type_id = Column(Integer, ForeignKey("space_types.id"))

    resource_id = Column(Integer, ForeignKey("space_resources.id"))

    rule_name = Column(String(100), nullable=False)
    rule_code = Column(String(50), unique=True)

    pricing_type = Column(String(20))

    pricing_params = Column(Text)

    conditions = Column(Text)

    priority = Column(Integer, default=0)

    effective_from = Column(DateTime)
    effective_to = Column(DateTime)

    is_active = Column(Boolean, default=True)

    def __repr__(self):
        return f"<PricingRule(id={self.id}, rule_name={self.rule_name})>"
