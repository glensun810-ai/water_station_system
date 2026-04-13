"""
空间审批Schema
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, field_validator


class SpaceApprovalBase(BaseModel):
    """空间审批基础模型"""

    booking_id: int
    approval_type: str

    approval_content: Optional[str] = None
    attachments: Optional[str] = None

    @field_validator("booking_id")
    def booking_id_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError("预约ID必须大于0")
        return v

    @field_validator("approval_type")
    def approval_type_must_be_valid(cls, v):
        valid_types = [
            "booking_approval",
            "content_approval",
            "cancel_approval",
            "modify_approval",
        ]
        if v not in valid_types:
            raise ValueError(f"审批类型必须是: {valid_types}")
        return v


class SpaceApprovalCreate(SpaceApprovalBase):
    """创建审批申请"""

    pass


class SpaceApprovalApprove(BaseModel):
    """审批通过"""

    approval_notes: Optional[str] = None
    approver_id: Optional[int] = None
    approver_name: Optional[str] = None


class SpaceApprovalReject(BaseModel):
    """审批拒绝"""

    rejection_reason: str
    rejection_detail: Optional[str] = None
    suggest_alternatives: Optional[List[dict]] = None
    allow_resubmit: bool = True
    resubmit_deadline: Optional[datetime] = None

    @field_validator("rejection_reason")
    def rejection_reason_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError("拒绝原因不能为空")
        return v


class SpaceApprovalRequestModify(BaseModel):
    """要求修改"""

    modify_suggestions: str
    resubmit_deadline: Optional[datetime] = None

    @field_validator("modify_suggestions")
    def suggestions_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError("修改建议不能为空")
        return v


class SpaceApprovalResponse(BaseModel):
    """审批响应模型"""

    id: int
    approval_no: str
    booking_id: int
    booking_no: Optional[str] = None

    approval_type: str
    approval_stage: Optional[str] = None

    approval_content: Optional[str] = None
    attachments: Optional[str] = None

    approver_id: Optional[int] = None
    approver_name: Optional[str] = None
    approver_role: Optional[str] = None
    approver_department: Optional[str] = None

    status: str
    result: Optional[str] = None

    submitted_at: datetime
    reviewed_at: Optional[datetime] = None
    approved_at: Optional[datetime] = None
    rejected_at: Optional[datetime] = None

    approval_notes: Optional[str] = None
    rejection_reason: Optional[str] = None
    modify_suggestions: Optional[str] = None

    deadline: Optional[datetime] = None
    is_overdue: bool = False

    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
