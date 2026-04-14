"""
空间预约Schema
"""

from datetime import datetime, date
from typing import Optional, List
from pydantic import BaseModel, field_validator


class SpaceBookingBase(BaseModel):
    """空间预约基础模型"""

    resource_id: int
    booking_date: date
    start_time: str
    end_time: str

    user_name: Optional[str] = None  # 改为可选，由后端自动填充
    user_phone: Optional[str] = None
    user_email: Optional[str] = None
    department: Optional[str] = None
    office_id: Optional[int] = None

    purpose: Optional[str] = None
    title: Optional[str] = None
    attendees_count: int = 1
    attendees_info: Optional[str] = None

    special_requests: Optional[str] = None
    addons_selected: Optional[str] = None

    @field_validator("resource_id")
    def resource_id_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError("空间ID必须大于0")
        return v

    @field_validator("start_time", "end_time")
    def time_format_must_be_valid(cls, v):
        from datetime import datetime as dt

        try:
            dt.strptime(v, "%H:%M")
        except ValueError:
            raise ValueError("时间格式必须为HH:MM")
        return v

    @field_validator("attendees_count")
    def attendees_count_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError("参会人数必须大于0")
        return v


class SpaceBookingCreate(SpaceBookingBase):
    """创建预约"""

    user_type: str = "external"
    type_code: Optional[str] = None

    meal_session: Optional[str] = None
    meal_standard: Optional[str] = None
    guests_count: Optional[int] = None

    content_type: Optional[str] = None
    content_url: Optional[str] = None

    exhibition_type: Optional[str] = None
    exhibition_plan_url: Optional[str] = None

    end_date: Optional[date] = None
    booking_days: int = 1

    class Config:
        extra = "ignore"  # 忽略前端发送的额外字段


class SpaceBookingUpdate(BaseModel):
    """更新预约"""

    title: Optional[str] = None
    attendees_count: Optional[int] = None
    attendees_info: Optional[str] = None
    special_requests: Optional[str] = None
    addons_selected: Optional[str] = None

    start_time: Optional[str] = None
    end_time: Optional[str] = None

    @field_validator("start_time", "end_time")
    def time_format_must_be_valid(cls, v):
        if v is None:
            return v
        from datetime import datetime as dt

        try:
            dt.strptime(v, "%H:%M")
        except ValueError:
            raise ValueError("时间格式必须为HH:MM")
        return v


class SpaceBookingCancel(BaseModel):
    """取消预约"""

    cancel_reason: str
    cancel_type: str = "user_cancel"

    @field_validator("cancel_reason")
    def cancel_reason_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError("取消原因不能为空")
        return v


class SpaceBookingResponse(BaseModel):
    """预约响应模型"""

    id: int
    booking_no: str
    resource_id: int
    resource_name: Optional[str] = None
    type_code: Optional[str] = None
    type_name: Optional[str] = None

    user_id: Optional[int] = None
    user_type: str
    user_name: str
    user_phone: Optional[str] = None
    user_email: Optional[str] = None
    department: Optional[str] = None
    office_id: Optional[int] = None

    booking_date: date
    start_time: str
    end_time: str
    duration: Optional[float] = None
    duration_unit: Optional[str] = None

    purpose: Optional[str] = None
    title: Optional[str] = None
    attendees_count: int = 1
    attendees_info: Optional[str] = None

    special_requests: Optional[str] = None
    addons_selected: Optional[str] = None

    base_fee: float = 0.0
    addon_fee: float = 0.0
    discount_amount: float = 0.0
    total_fee: float = 0.0
    actual_fee: float = 0.0

    requires_deposit: bool = False
    deposit_amount: float = 0.0
    deposit_paid: bool = False

    status: str
    payment_status: str
    settlement_status: str

    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    rejected_reason: Optional[str] = None
    rejected_at: Optional[datetime] = None

    confirmed_at: Optional[datetime] = None

    cancelled_at: Optional[datetime] = None
    cancelled_by: Optional[str] = None
    cancel_reason: Optional[str] = None

    can_modify: bool = True
    can_cancel: bool = True
    cancel_deadline: Optional[datetime] = None

    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class FeeCalculationRequest(BaseModel):
    """费用计算请求"""

    resource_id: int
    type_code: Optional[str] = None
    booking_date: date
    start_time: str
    end_time: str
    duration: Optional[float] = None

    user_id: Optional[int] = None
    user_type: str = "external"
    member_level: str = "regular"

    attendees_count: int = 1
    addons_selected: Optional[List[dict]] = None

    promotion_code: Optional[str] = None

    @field_validator("start_time", "end_time")
    def time_format_must_be_valid(cls, v):
        from datetime import datetime as dt

        try:
            dt.strptime(v, "%H:%M")
        except ValueError:
            raise ValueError("时间格式必须为HH:MM")
        return v


class FeeCalculationResponse(BaseModel):
    """费用计算响应"""

    calculation_detail: dict
    fee_summary: dict
    deposit_info: dict
    payment_methods: List[str]


class BatchOperationRequest(BaseModel):
    """批量操作请求"""

    booking_ids: List[int]
    operation: str
    reason: Optional[str] = None

    @field_validator("booking_ids")
    def booking_ids_must_not_be_empty(cls, v):
        if not v or len(v) == 0:
            raise ValueError("预约ID列表不能为空")
        if len(v) > 100:
            raise ValueError("单次批量操作最多100条记录")
        return v

    @field_validator("operation")
    def operation_must_be_valid(cls, v):
        valid_operations = ["delete", "approve", "cancel", "complete"]
        if v not in valid_operations:
            raise ValueError(f"操作类型必须是: {', '.join(valid_operations)}")
        return v


class BatchOperationResult(BaseModel):
    """批量操作结果"""

    total: int
    success_count: int
    failed_count: int
    success_ids: List[int]
    failed_items: List[dict]
    message: str
