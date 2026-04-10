"""
会议室API schemas
Pydantic模型用于API请求和响应验证
"""

from pydantic import BaseModel, field_validator
from typing import Optional
from datetime import datetime, date


class MeetingRoomResponse(BaseModel):
    """会议室响应模型"""

    id: int
    name: str
    location: Optional[str] = None
    capacity: int = 10
    facilities: Optional[str] = None
    price_per_hour: float = 0.0
    member_price_per_hour: float = 0.0
    free_hours_per_month: int = 0
    is_active: bool = True
    requires_approval: bool = False
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class MeetingBookingCreate(BaseModel):
    """会议室预订创建模型"""

    room_id: int
    booking_date: str
    start_time: str
    end_time: str
    duration: Optional[float] = None
    meeting_title: Optional[str] = ""
    attendees_count: Optional[int] = 1
    total_fee: Optional[float] = 0

    @field_validator("room_id")
    def room_id_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError("会议室ID必须大于0")
        return v

    @field_validator("attendees_count")
    def attendees_count_must_be_positive(cls, v):
        if v is not None and v <= 0:
            raise ValueError("参会人数必须大于0")
        return v


class MeetingBookingResponse(BaseModel):
    """会议室预订响应模型"""

    id: int
    booking_no: Optional[str] = None
    room_id: int
    room_name: Optional[str] = None
    user_id: Optional[int] = None
    user_name: Optional[str] = None
    department: Optional[str] = None
    booking_date: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    duration: Optional[float] = None
    meeting_title: Optional[str] = None
    attendees_count: Optional[int] = None
    total_fee: Optional[float] = None
    status: Optional[str] = None
    confirmed_by: Optional[str] = None
    confirmed_at: Optional[datetime] = None
    office_id: Optional[int] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class MeetingBookingUpdate(BaseModel):
    """会议室预订更新模型"""

    meeting_title: Optional[str] = None
    attendees_count: Optional[int] = None
    status: Optional[str] = None
