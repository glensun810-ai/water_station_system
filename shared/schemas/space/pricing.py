"""
定价相关Schema
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, field_validator


class PricingRuleBase(BaseModel):
    """定价规则基础模型"""

    rule_name: str
    rule_code: Optional[str] = None
    pricing_type: str
    pricing_params: Optional[str] = None
    conditions: Optional[str] = None
    priority: int = 0

    @field_validator("pricing_type")
    def pricing_type_must_be_valid(cls, v):
        valid_types = [
            "base",
            "capacity",
            "member",
            "duration",
            "batch",
            "addon",
            "deposit",
        ]
        if v not in valid_types:
            raise ValueError(f"定价类型必须是: {valid_types}")
        return v


class PricingRuleCreate(PricingRuleBase):
    """创建定价规则"""

    type_id: Optional[int] = None
    resource_id: Optional[int] = None
    effective_from: Optional[datetime] = None
    effective_to: Optional[datetime] = None


class PricingRuleResponse(PricingRuleBase):
    """定价规则响应"""

    id: int
    type_id: Optional[int] = None
    resource_id: Optional[int] = None
    effective_from: Optional[datetime] = None
    effective_to: Optional[datetime] = None
    is_active: bool = True
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PricingAddonBase(BaseModel):
    """增值服务基础模型"""

    addon_name: str
    addon_code: Optional[str] = None
    addon_type: str
    pricing_method: str
    price: float
    description: Optional[str] = None

    @field_validator("addon_type")
    def addon_type_must_be_valid(cls, v):
        valid_types = ["equipment", "service", "food", "setup"]
        if v not in valid_types:
            raise ValueError(f"增值服务类型必须是: {valid_types}")
        return v

    @field_validator("pricing_method")
    def pricing_method_must_be_valid(cls, v):
        valid_methods = ["fixed", "per_hour", "per_person", "per_day"]
        if v not in valid_methods:
            raise ValueError(f"定价方式必须是: {valid_methods}")
        return v

    @field_validator("price")
    def price_must_be_non_negative(cls, v):
        if v < 0:
            raise ValueError("价格不能为负数")
        return v


class PricingAddonResponse(PricingAddonBase):
    """增值服务响应"""

    id: int
    type_id: Optional[int] = None
    is_active: bool = True
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
