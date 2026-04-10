"""
领水相关Pydantic模型
"""

from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional, List


class OfficePickupCreate(BaseModel):
    """领水创建模型"""

    office_id: int
    product_id: int
    quantity: int
    pickup_person: str


class OfficePickupUpdate(BaseModel):
    """领水更新模型"""

    office_id: Optional[int] = None
    product_id: Optional[int] = None
    quantity: Optional[int] = None
    pickup_person: Optional[str] = None
    settlement_status: Optional[str] = None
    note: Optional[str] = None


class OfficePickupResponse(BaseModel):
    """领水记录响应模型"""

    id: int
    office_id: int
    office_name: str
    office_room_number: Optional[str] = None
    product_id: int
    product_name: str
    product_specification: Optional[str] = None
    quantity: int
    pickup_person: str
    pickup_person_id: Optional[int] = None
    pickup_time: datetime
    unit_price: float
    total_amount: float
    free_qty: int = 0
    discount_desc: Optional[str] = None
    settlement_status: str = "pending"
    payment_mode: str = "credit"
    note: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class SettlementApply(BaseModel):
    """结算申请模型"""

    pickup_ids: List[int]


class SettlementConfirm(BaseModel):
    """结算确认模型"""

    note: Optional[str] = None


class OfficeAccountResponse(BaseModel):
    """办公室账户响应"""

    office_id: int
    office_name: str
    office_room_number: Optional[str] = None
    manager_name: Optional[str] = None
    total_qty: int = 0
    paid_qty: int = 0
    free_qty: int = 0
    remaining_qty: int = 0
    balance_credit: float = 0.0
    status: str = "active"

    model_config = ConfigDict(from_attributes=True)


class UserOfficeResponse(BaseModel):
    """用户办公室响应"""

    office_id: int
    office_name: str
    office_room_number: Optional[str] = None
    manager_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
