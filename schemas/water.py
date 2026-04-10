"""
水站服务数据模式
"""

from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class OfficePickupCreate(BaseModel):
    office_id: int
    product_id: int
    quantity: int
    pickup_person: Optional[str] = None
    pickup_time: Optional[str] = None


class OfficePickupResponse(BaseModel):
    id: int
    office_id: int
    office_name: str
    product_id: int
    product_name: str
    product_specification: Optional[str] = None
    quantity: int
    pickup_person: Optional[str] = None
    pickup_person_id: Optional[int] = None
    pickup_time: Optional[datetime] = None
    settlement_status: str
    total_amount: float
    free_qty: int = 0

    class Config:
        from_attributes = True
