"""
全局异常处理器 - 空间服务API
确保所有错误返回JSON格式，避免HTML错误页面
"""

from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError
import logging
import traceback
from datetime import datetime

logger = logging.getLogger(__name__)


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    处理请求验证异常（Pydantic验证错误）
    """
    errors = []
    for error in exc.errors():
        errors.append(
            {
                "field": ".".join(str(loc) for loc in error["loc"]),
                "message": error["msg"],
                "type": error["type"],
            }
        )

    logger.warning(
        f"Validation error at {request.url.path}: {len(errors)} errors",
        extra={"errors": errors},
    )

    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "success": False,
            "detail": "请求参数验证失败",
            "errors": errors,
            "timestamp": datetime.now().isoformat(),
        },
    )


async def http_exception_handler(request: Request, exc):
    """
    处理HTTPException（如404、403等）
    """
    logger.warning(
        f"HTTP exception at {request.url.path}: {exc.status_code} - {exc.detail}"
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "detail": exc.detail,
            "timestamp": datetime.now().isoformat(),
        },
    )


async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    """
    处理数据库异常
    """
    logger.error(f"Database error at {request.url.path}: {str(exc)}", exc_info=True)

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "detail": "数据库操作失败，请稍后重试",
            "timestamp": datetime.now().isoformat(),
        },
    )


async def generic_exception_handler(request: Request, exc: Exception):
    """
    处理所有未捕获的异常
    这个处理器是最关键的，确保所有错误都返回JSON而不是HTML
    """
    logger.error(
        f"Unhandled exception at {request.url.path}: {type(exc).__name__} - {str(exc)}",
        exc_info=True,
    )

    error_detail = str(exc)
    if len(error_detail) > 200:
        error_detail = error_detail[:200] + "..."

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "detail": f"服务器内部错误: {error_detail}",
            "error_type": type(exc).__name__,
            "timestamp": datetime.now().isoformat(),
            "path": request.url.path,
        },
    )


def register_exception_handlers(app):
    """
    注册所有异常处理器到FastAPI应用
    """
    from fastapi import HTTPException

    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(SQLAlchemyError, sqlalchemy_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)

    logger.info("Exception handlers registered for space service API")
