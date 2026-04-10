"""
通知和促销相关Pydantic Schemas
"""

from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional


class NotificationBase(BaseModel):
    user_id: Optional[int] = None
    title: str
    content: str
    type: str = "info"


class NotificationCreate(NotificationBase):
    pass


class NotificationResponse(NotificationBase):
    id: int
    is_read: int
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class PromotionConfigBase(BaseModel):
    product_id: int
    mode: str = "pay_later"
    trigger_qty: int = 10
    gift_qty: int = 0
    discount_rate: float = 100.0
    is_active: int = 1


class PromotionConfigCreate(PromotionConfigBase):
    pass


class PromotionConfigResponse(PromotionConfigBase):
    id: int
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
