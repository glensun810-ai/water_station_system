"""
系统服务数据模式
"""

from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class UserResponse(BaseModel):
    id: int
    username: str
    name: Optional[str] = None
    department: Optional[str] = None
    role: str
    phone: Optional[str] = None
    email: Optional[str] = None
    company: Optional[str] = None
    is_active: int
    created_at: Optional[datetime] = None
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True


class OfficeResponse(BaseModel):
    id: int
    name: str
    room_number: Optional[str] = None
    leader_name: Optional[str] = None
    manager_name: Optional[str] = None
    contact_info: Optional[str] = None
    is_active: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AuthResponse(BaseModel):
    access_token: str
    token_type: str
    user_info: dict
