"""
预付费相关Pydantic Schemas
"""

from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional


class PrepaidPackageBase(BaseModel):
    name: str
    product_id: int
    price: float
    buy_quantity: int
    gift_quantity: int
    validity_days: int = 90
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    is_active: Optional[int] = None


class PrepaidPackageCreate(PrepaidPackageBase):
    pass


class PrepaidPackageUpdate(BaseModel):
    name: Optional[str] = None
    price: Optional[float] = None
    buy_quantity: Optional[int] = None
    gift_quantity: Optional[int] = None
    validity_days: Optional[int] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    is_active: Optional[int] = None


class PrepaidPackageResponse(PrepaidPackageBase):
    id: int
    product_name: Optional[str] = None
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class PrepaidOrderBase(BaseModel):
    user_id: int
    product_id: int
    total_qty: int
    unit_price: float
    total_amount: float
    discount_amount: float = 0
    payment_method: str = "offline"
    note: Optional[str] = None


class PrepaidOrderCreate(PrepaidOrderBase):
    created_by: int


class PrepaidOrderResponse(PrepaidOrderBase):
    id: int
    used_qty: int
    payment_status: str
    payment_at: Optional[datetime] = None
    confirmed_by: Optional[int] = None
    is_active: int
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class PrepaidPickupBase(BaseModel):
    order_id: int
    pickup_qty: int
    note: Optional[str] = None


class PrepaidPickupCreate(PrepaidPickupBase):
    picked_by: int


class PrepaidPickupResponse(PrepaidPickupBase):
    id: int
    picked_at: Optional[datetime] = None
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class PrepaidBalanceResponse(BaseModel):
    total_qty: int
    used_qty: int
    remaining_qty: int
