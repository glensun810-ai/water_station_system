"""
产品相关模型
包含Product和ProductCategory模型定义
"""

from sqlalchemy import Column, Integer, String, Float, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from models.base import Base


class ProductCategory(Base):
    """产品分类表"""

    __tablename__ = "product_categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    sort_order = Column(Integer, default=0)
    is_active = Column(Integer, default=1)
    created_at = Column(String, default=datetime.now)

    # 关系
    products = relationship("Product", back_populates="category")


class Product(Base):
    """产品表"""

    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    specification = Column(String)  # e.g., "18L", "500ml", "4小时"
    unit = Column(String, default="unit")
    price = Column(Float, nullable=False)
    stock = Column(Integer, default=0)
    cost_price = Column(Float, nullable=True)  # 成本价
    image_url = Column(String, nullable=True)  # 产品图片URL
    description = Column(String, nullable=True)  # 产品描述
    category_id = Column(
        Integer, ForeignKey("product_categories.id"), nullable=True
    )  # 分类ID
    barcode = Column(String, nullable=True)  # 产品条码
    promo_threshold = Column(Integer, default=10)  # 买 N
    promo_gift = Column(Integer, default=1)  # 赠 M
    is_active = Column(Integer, default=1)  # 1: 启用/在售，0: 停用/归档
    is_protected = Column(
        Integer, default=0
    )  # 0: 可删除, 1: 受保护(发布后自动保护真实数据)

    # === Phase 1 服务扩展字段 ===
    service_type = Column(
        String(50), default="water"
    )  # 服务类型：water/meeting_room/dining等
    resource_config = Column(Text, nullable=True)  # 资源配置 (JSON)
    booking_required = Column(Integer, default=0)  # 是否需要预约：0-不需要，1-需要
    advance_booking_days = Column(Integer, default=0)  # 可提前预约天数

    # 关系
    category = relationship("ProductCategory", back_populates="products")
    transactions = relationship("Transaction", back_populates="product")
    inventory_records = relationship("InventoryRecord", back_populates="product")
    alert_configs = relationship("InventoryAlertConfig", back_populates="product")
