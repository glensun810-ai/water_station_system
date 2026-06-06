"""
空间类型Schema
"""

import json
from datetime import datetime
from typing import Optional, List, Any
from pydantic import BaseModel, field_validator


class SpaceTypeBase(BaseModel):
    """空间类型基础模型"""

    type_code: str
    type_name: str
    type_name_en: Optional[str] = None
    description: Optional[str] = None

    min_duration_unit: str
    min_duration_value: int = 1
    max_duration_value: int = 24
    advance_booking_days: int = 0

    auto_approval_max_amount: float = 0.0
    free_quota_applicable_units: Optional[List[str]] = ["hour"]

    min_capacity: int = 1
    max_capacity: int = 500

    requires_approval: bool = False
    approval_type: Optional[str] = None
    approval_deadline_hours: int = 24

    requires_deposit: bool = False
    deposit_percentage: float = 0.0
    deposit_refund_rules: Optional[str] = None

    standard_facilities: Optional[str] = None
    optional_addons: Optional[str] = None

    supported_duration_units: Optional[List[str]] = ["hour"]
    time_slot_preset: Optional[Any] = None

    is_active: bool = True
    sort_order: int = 0

    icon: Optional[str] = None
    color_theme: Optional[str] = None

    @field_validator("type_code", "type_name")
    def must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError("字段不能为空")
        return v

    @field_validator("deposit_percentage")
    def must_be_between_0_and_1(cls, v):
        if v < 0 or v > 1:
            raise ValueError("定金比例必须在0-1之间")
        return v

    @field_validator("supported_duration_units", "time_slot_preset", mode="before")
    def parse_json_string_to_list(cls, v):
        """将数据库或前端传来的 JSON 字符串自动解析为列表/字典"""
        if v is None:
            return None
        if isinstance(v, str):
            try:
                return json.loads(v)
            except (json.JSONDecodeError, TypeError):
                return v
        return v


class SpaceTypeCreate(SpaceTypeBase):
    """创建空间类型"""

    pass


class SpaceTypeUpdate(BaseModel):
    """更新空间类型"""

    type_name: Optional[str] = None
    type_name_en: Optional[str] = None
    description: Optional[str] = None

    min_duration_unit: Optional[str] = None
    min_duration_value: Optional[int] = None
    max_duration_value: Optional[int] = None
    advance_booking_days: Optional[int] = None

    auto_approval_max_amount: Optional[float] = None
    free_quota_applicable_units: Optional[List[str]] = None

    min_capacity: Optional[int] = None
    max_capacity: Optional[int] = None

    requires_approval: Optional[bool] = None
    approval_type: Optional[str] = None
    approval_deadline_hours: Optional[int] = None

    requires_deposit: Optional[bool] = None
    deposit_percentage: Optional[float] = None
    deposit_refund_rules: Optional[str] = None

    standard_facilities: Optional[str] = None
    optional_addons: Optional[str] = None

    supported_duration_units: Optional[List[str]] = None
    time_slot_preset: Optional[Any] = None

    is_active: Optional[bool] = None
    sort_order: Optional[int] = None

    icon: Optional[str] = None
    color_theme: Optional[str] = None

    @field_validator("supported_duration_units", "time_slot_preset", mode="before")
    def parse_json_string_to_list(cls, v):
        if v is None:
            return None
        if isinstance(v, str):
            try:
                return json.loads(v)
            except (json.JSONDecodeError, TypeError):
                return v
        return v


class SpaceTypeResponse(SpaceTypeBase):
    """空间类型响应模型"""

    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
