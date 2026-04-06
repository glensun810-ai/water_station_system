"""
产品相关的Pydantic模型
"""

from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional, List


class ProductBase(BaseModel):
    """产品基础模型"""

    name: str
    specification: Optional[str] = None
    unit: str = "unit"
    price: float
    cost_price: Optional[float] = None
    image_url: Optional[str] = None
    description: Optional[str] = None
    category_id: Optional[int] = None
    barcode: Optional[str] = None
    promo_threshold: int = 10
    promo_gift: int = 1


class ProductCreate(ProductBase):
    """产品创建模型"""

    stock: int = 0
    is_active: int = 1


class ProductUpdate(BaseModel):
    """产品更新模型"""

    name: Optional[str] = None
    specification: Optional[str] = None
    unit: Optional[str] = None
    price: Optional[float] = None
    cost_price: Optional[float] = None
    stock: Optional[int] = None
    image_url: Optional[str] = None
    description: Optional[str] = None
    category_id: Optional[int] = None
    barcode: Optional[str] = None
    promo_threshold: Optional[int] = None
    promo_gift: Optional[int] = None
    is_active: Optional[int] = None


class ProductResponse(ProductBase):
    """产品响应模型"""

    id: int
    stock: int
    is_active: int
    is_protected: int = 0
    category_name: Optional[str] = None
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class CategoryBase(BaseModel):
    """分类基础模型"""

    name: str
    sort_order: int = 0
    is_active: int = 1


class CategoryCreate(CategoryBase):
    """分类创建模型"""

    pass


class CategoryUpdate(BaseModel):
    """分类更新模型"""

    name: Optional[str] = None
    sort_order: Optional[int] = None
    is_active: Optional[int] = None


class CategoryResponse(CategoryBase):
    """分类响应模型"""

    id: int
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class InventoryRecordBase(BaseModel):
    """库存记录基础模型"""

    product_id: int
    type: str  # in/out/adjust/loss
    quantity: int
    note: Optional[str] = None


class InventoryRecordCreate(InventoryRecordBase):
    """库存记录创建模型"""

    pass


class InventoryRecordResponse(InventoryRecordBase):
    """库存记录响应模型"""

    id: int
    before_stock: int
    after_stock: int
    operator_id: Optional[int] = None
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
