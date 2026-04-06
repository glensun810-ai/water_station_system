"""
用户相关的Pydantic模型
"""

from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional


class UserBase(BaseModel):
    """用户基础模型"""

    name: str
    department: str
    role: str = "staff"


class UserCreate(UserBase):
    """用户创建模型"""

    password: str
    balance_credit: float = 0.0
    is_active: int = 1


class UserUpdate(BaseModel):
    """用户更新模型"""

    name: Optional[str] = None
    department: Optional[str] = None
    role: Optional[str] = None
    balance_credit: Optional[float] = None
    is_active: Optional[int] = None


class UserResponse(UserBase):
    """用户响应模型"""

    id: int
    balance_credit: float
    is_active: int
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class UserLogin(BaseModel):
    """用户登录模型"""

    name: str
    password: str


class TokenResponse(BaseModel):
    """Token响应模型"""

    access_token: str
    token_type: str = "bearer"
    user: Optional[UserResponse] = None


class PasswordChange(BaseModel):
    """密码修改模型"""

    old_password: str
    new_password: str
