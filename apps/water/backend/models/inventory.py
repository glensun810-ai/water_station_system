"""
库存相关模型
包含InventoryRecord和InventoryAlertConfig模型定义
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from models.base import Base


class InventoryRecord(Base):
    """库存流水记录"""

    __tablename__ = "inventory_records"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    type = Column(String(20), nullable=False)  # in/out/adjust/loss
    quantity = Column(Integer, nullable=False)
    before_stock = Column(Integer, nullable=False)
    after_stock = Column(Integer, nullable=False)
    reference_type = Column(String(50))
    reference_id = Column(Integer)
    operator_id = Column(Integer)
    note = Column(String(500))
    created_at = Column(DateTime, default=datetime.now)

    product = relationship("Product", back_populates="inventory_records")


class InventoryAlertConfig(Base):
    """库存预警配置（按产品单独设置）"""

    __tablename__ = "inventory_alert_configs"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    warning_threshold = Column(Integer, default=10)
    critical_threshold = Column(Integer, default=5)
    is_active = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime)

    product = relationship("Product", back_populates="alert_configs")
