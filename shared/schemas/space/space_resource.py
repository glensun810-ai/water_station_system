"""
空间资源Schema
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, field_validator


class SpaceResourceBase(BaseModel):
    """空间资源基础模型"""

    type_id: int
    name: str
    name_en: Optional[str] = None
    location: Optional[str] = None
    floor: Optional[str] = None
    building: Optional[str] = None

    capacity: int = 10
    capacity_level: Optional[str] = None

    facilities: Optional[str] = None
    facilities_status: Optional[str] = None

    base_price: float = 0.0
    price_unit: Optional[str] = None
    member_price: float = 0.0
    vip_price: float = 0.0

    peak_time_price: Optional[float] = None
    off_peak_price: Optional[float] = None

    free_hours_per_month: int = 0

    meal_standard_price: Optional[float] = None
    meal_vip_price: Optional[float] = None
    meal_luxury_price: Optional[float] = None

    booth_size: Optional[str] = None
    booth_position: Optional[str] = None

    venue_level: Optional[str] = None
    setup_time_hours: int = 2
    setup_fee_per_hour: Optional[float] = None

    photos: Optional[str] = None
    description: Optional[str] = None

    is_active: bool = True
    is_available: bool = True
    maintenance_status: str = "normal"
    maintenance_note: Optional[str] = None

    office_id: Optional[int] = None

    @field_validator("name")
    def name_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError("空间名称不能为空")
        return v

    @field_validator("capacity")
    def capacity_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError("容纳人数必须大于0")
        return v

    @field_validator("base_price")
    def price_must_be_non_negative(cls, v):
        if v < 0:
            raise ValueError("基础价格不能为负数")
        return v


class SpaceResourceCreate(SpaceResourceBase):
    """创建空间资源"""

    pass


class SpaceResourceUpdate(BaseModel):
    """更新空间资源"""

    name: Optional[str] = None
    name_en: Optional[str] = None
    location: Optional[str] = None
    floor: Optional[str] = None
    building: Optional[str] = None

    capacity: Optional[int] = None
    capacity_level: Optional[str] = None

    facilities: Optional[str] = None
    facilities_status: Optional[str] = None

    base_price: Optional[float] = None
    price_unit: Optional[str] = None
    member_price: Optional[float] = None
    vip_price: Optional[float] = None

    peak_time_price: Optional[float] = None
    off_peak_price: Optional[float] = None

    free_hours_per_month: Optional[int] = None

    meal_standard_price: Optional[float] = None
    meal_vip_price: Optional[float] = None
    meal_luxury_price: Optional[float] = None

    booth_size: Optional[str] = None
    booth_position: Optional[str] = None

    venue_level: Optional[str] = None
    setup_time_hours: Optional[int] = None
    setup_fee_per_hour: Optional[float] = None

    photos: Optional[str] = None
    description: Optional[str] = None

    is_active: Optional[bool] = None
    is_available: Optional[bool] = None
    maintenance_status: Optional[str] = None
    maintenance_note: Optional[str] = None

    office_id: Optional[int] = None


class SpaceResourceResponse(SpaceResourceBase):
    """空间资源响应模型"""

    id: int
    type_code: Optional[str] = None
    type_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SpaceAvailabilityResponse(BaseModel):
    """空间可用时段响应"""

    resource_id: int
    resource_name: str
    date: str
    operating_hours: dict
    booked_slots: List[dict]
    available_slots: List[dict]
    total_available_hours: float
