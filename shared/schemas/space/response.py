"""
统一响应Schema
"""

from datetime import datetime
from typing import Optional, Any, Generic, TypeVar
from pydantic import BaseModel

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    """统一API响应格式"""

    code: int = 200
    message: str = "success"
    data: Optional[T] = None
    timestamp: datetime = datetime.now()

    class Config:
        arbitrary_types_allowed = True


class PaginatedResponse(BaseModel, Generic[T]):
    """分页响应"""

    items: list
    total: int
    page: int
    limit: int
    pages: int


class ErrorDetail(BaseModel):
    """错误详情"""

    error_code: str
    error_detail: Optional[str] = None
    error_data: Optional[dict] = None


class ErrorResponse(BaseModel):
    """错误响应"""

    code: int
    message: str
    data: Optional[Any] = None
    error: Optional[ErrorDetail] = None
    timestamp: datetime = datetime.now()


class SuccessResponse(BaseModel):
    """成功响应"""

    code: int = 200
    message: str = "success"
    data: Optional[dict] = None
    timestamp: datetime = datetime.now()
