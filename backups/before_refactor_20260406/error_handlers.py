"""
全局异常处理器
统一处理所有异常，返回标准格式响应
"""

from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError
import logging
import traceback
from datetime import datetime

from exceptions import AppException

logger = logging.getLogger(__name__)


async def app_exception_handler(request: Request, exc: AppException):
    """
    处理应用异常

    Args:
        request: 请求对象
        exc: 异常实例

    Returns:
        JSON响应
    """
    # 记录异常日志
    logger.warning(
        f"Application exception: {exc.code} - {exc.message}",
        extra={
            "code": exc.code,
            "status_code": exc.status_code,
            "path": request.url.path,
            "method": request.method,
            "details": exc.details,
        },
    )

    # 构建响应
    response_content = {
        "success": False,
        "error": {
            "code": exc.code,
            "message": exc.message,
            "timestamp": datetime.now().isoformat(),
            "path": request.url.path,
            "method": request.method,
        },
    }

    # 添加详细信息（如果有）
    if exc.details:
        response_content["error"]["details"] = exc.details

    return JSONResponse(status_code=exc.status_code, content=response_content)


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    处理请求验证异常

    Args:
        request: 请求对象
        exc: 验证异常

    Returns:
        JSON响应
    """
    # 提取错误信息
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
        f"Validation error: {len(errors)} errors",
        extra={"path": request.url.path, "method": request.method, "errors": errors},
    )

    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "success": False,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "请求参数验证失败",
                "timestamp": datetime.now().isoformat(),
                "path": request.url.path,
                "method": request.method,
                "details": {"errors": errors},
            },
        },
    )


async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    """
    处理数据库异常

    Args:
        request: 请求对象
        exc: 数据库异常

    Returns:
        JSON响应
    """
    # 记录详细错误日志
    logger.error(
        f"Database error: {str(exc)}",
        extra={
            "path": request.url.path,
            "method": request.method,
            "exception_type": type(exc).__name__,
        },
        exc_info=True,
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": {
                "code": "DATABASE_ERROR",
                "message": "数据库操作失败，请稍后重试",
                "timestamp": datetime.now().isoformat(),
                "path": request.url.path,
                "method": request.method,
            },
        },
    )


async def generic_exception_handler(request: Request, exc: Exception):
    """
    处理未捕获的异常

    Args:
        request: 请求对象
        exc: 异常实例

    Returns:
        JSON响应
    """
    # 记录详细错误日志
    logger.error(
        f"Unhandled exception: {str(exc)}",
        extra={
            "path": request.url.path,
            "method": request.method,
            "exception_type": type(exc).__name__,
        },
        exc_info=True,
    )

    # 生产环境不返回详细错误信息
    from config.settings import settings

    if settings.ENVIRONMENT == "production":
        message = "服务器内部错误，请稍后重试"
    else:
        message = f"服务器内部错误: {str(exc)}"

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": {
                "code": "INTERNAL_ERROR",
                "message": message,
                "timestamp": datetime.now().isoformat(),
                "path": request.url.path,
                "method": request.method,
            },
        },
    )


def register_exception_handlers(app):
    """
    注册异常处理器到应用

    Args:
        app: FastAPI应用实例
    """
    from fastapi.exceptions import RequestValidationError
    from sqlalchemy.exc import SQLAlchemyError

    # 注册异常处理器
    app.add_exception_handler(AppException, app_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(SQLAlchemyError, sqlalchemy_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)

    logger.info("Exception handlers registered")
