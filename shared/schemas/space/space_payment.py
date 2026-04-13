"""
空间支付Schema
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, field_validator


class SpacePaymentBase(BaseModel):
    """空间支付基础模型"""

    booking_id: int
    payment_type: str
    amount: float
    payment_method: Optional[str] = None
    payment_channel: Optional[str] = None

    @field_validator("booking_id")
    def booking_id_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError("预约ID必须大于0")
        return v

    @field_validator("amount")
    def amount_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError("支付金额必须大于0")
        return v

    @field_validator("payment_type")
    def payment_type_must_be_valid(cls, v):
        valid_types = ["deposit", "balance", "full", "refund"]
        if v not in valid_types:
            raise ValueError(f"支付类型必须是: {valid_types}")
        return v


class SpacePaymentCreate(SpacePaymentBase):
    """创建支付记录"""

    pass


class SpacePaymentConfirm(BaseModel):
    """确认支付"""

    transaction_id: Optional[str] = None
    receipt_url: Optional[str] = None
    proof_url: Optional[str] = None
    notes: Optional[str] = None


class SpacePaymentVerify(BaseModel):
    """审核支付（线下）"""

    verified_by: str
    verification_notes: Optional[str] = None

    @field_validator("verified_by")
    def verified_by_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError("审核人不能为空")
        return v


class SpacePaymentRefund(BaseModel):
    """申请退款"""

    refund_reason: str
    refund_amount: Optional[float] = None

    @field_validator("refund_reason")
    def refund_reason_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError("退款原因不能为空")
        return v


class SpacePaymentResponse(BaseModel):
    """支付响应模型"""

    id: int
    payment_no: str
    booking_id: int
    booking_no: Optional[str] = None

    user_id: Optional[int] = None
    user_name: Optional[str] = None

    payment_type: str
    payment_purpose: Optional[str] = None

    amount: float
    currency: str = "CNY"

    payment_method: Optional[str] = None
    payment_channel: Optional[str] = None

    status: str

    initiated_at: datetime
    completed_at: Optional[datetime] = None

    transaction_id: Optional[str] = None
    receipt_url: Optional[str] = None

    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
