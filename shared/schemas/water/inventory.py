"""
库存预警相关Pydantic Schemas
"""

from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional


class InventoryAlertConfigBase(BaseModel):
    product_id: int
    threshold: int = 10
    is_active: int = 1


class InventoryAlertConfigCreate(InventoryAlertConfigBase):
    pass


class InventoryAlertConfigUpdate(BaseModel):
    threshold: Optional[int] = None
    is_active: Optional[int] = None


class InventoryAlertConfigResponse(InventoryAlertConfigBase):
    id: int
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
