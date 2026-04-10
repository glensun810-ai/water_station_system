"""
统一日志系统
提供结构化日志、请求追踪、日志轮转等功能
"""

import logging
import logging.config
from logging.handlers import RotatingFileHandler
import os
import json
from datetime import datetime
from typing import Any, Dict
import uuid
from functools import wraps
import time

from config.settings import settings


class StructuredFormatter(logging.Formatter):
    """结构化日志格式化器"""

    def format(self, record: logging.LogRecord) -> str:
        """格式化日志记录"""
        # 基础信息
        log_data = {
            "timestamp": datetime.now().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # 添加额外信息
        if hasattr(record, "extra"):
            log_data["extra"] = record.extra

        # 添加异常信息
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # 添加请求ID（如果有）
        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id

        # 添加用户信息（如果有）
        if hasattr(record, "user_id"):
            log_data["user_id"] = record.user_id

        return json.dumps(log_data, ensure_ascii=False)


class RequestFormatter(logging.Formatter):
    """请求日志格式化器"""

    def format(self, record: logging.LogRecord) -> str:
        """格式化请求日志"""
        # 基础格式
        base_format = "[%(asctime)s] %(levelname)s in %(module)s: %(message)s"

        # 添加请求ID
        if hasattr(record, "request_id"):
            base_format = f"[{record.request_id}] " + base_format

        self._style._fmt = base_format
        return super().format(record)


def setup_logging():
    """配置日志系统"""

    # 创建日志目录
    log_dir = os.path.dirname(settings.LOG_FILE)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # 日志配置
    config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "()": StructuredFormatter,
            },
            "request": {
                "()": RequestFormatter,
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
            "simple": {
                "format": "[%(asctime)s] %(levelname)s - %(name)s - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": settings.LOG_LEVEL,
                "formatter": "simple",
                "stream": "ext://sys.stdout",
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "DEBUG",
                "formatter": "default",
                "filename": settings.LOG_FILE,
                "maxBytes": settings.LOG_MAX_BYTES,
                "backupCount": settings.LOG_BACKUP_COUNT,
                "encoding": "utf-8",
            },
            "error_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "ERROR",
                "formatter": "default",
                "filename": settings.LOG_FILE.replace(".log", "_error.log"),
                "maxBytes": settings.LOG_MAX_BYTES,
                "backupCount": settings.LOG_BACKUP_COUNT,
                "encoding": "utf-8",
            },
        },
        "loggers": {
            "app": {
                "level": "DEBUG",
                "handlers": ["console", "file", "error_file"],
                "propagate": False,
            },
            "api": {
                "level": "DEBUG",
                "handlers": ["console", "file"],
                "propagate": False,
            },
            "services": {
                "level": "DEBUG",
                "handlers": ["console", "file"],
                "propagate": False,
            },
            "sqlalchemy.engine": {
                "level": "WARNING",
                "handlers": ["console"],
                "propagate": False,
            },
        },
        "root": {
            "level": settings.LOG_LEVEL,
            "handlers": ["console", "file"],
        },
    }

    logging.config.dictConfig(config)

    return logging.getLogger("app")


# 获取日志器
def get_logger(name: str = "app") -> logging.Logger:
    """
    获取日志器

    Args:
        name: 日志器名称

    Returns:
        Logger实例
    """
    return logging.getLogger(name)


# 请求ID生成
def generate_request_id() -> str:
    """生成请求ID"""
    return str(uuid.uuid4())[:8]


# 请求日志中间件
class RequestLoggingMiddleware:
    """请求日志中间件"""

    def __init__(self, app):
        self.app = app
        self.logger = get_logger("api")

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # 生成请求ID
        request_id = generate_request_id()

        # 记录请求开始
        start_time = time.time()

        # 提取请求信息
        method = scope["method"]
        path = scope["path"]
        query_string = scope.get("query_string", b"").decode()

        self.logger.info(
            f"Request started: {method} {path}",
            extra={
                "request_id": request_id,
                "method": method,
                "path": path,
                "query_string": query_string,
            },
        )

        # 处理请求
        try:
            await self.app(scope, receive, send)

            # 记录请求完成
            duration = time.time() - start_time
            self.logger.info(
                f"Request completed: {method} {path}",
                extra={
                    "request_id": request_id,
                    "method": method,
                    "path": path,
                    "duration_ms": round(duration * 1000, 2),
                },
            )
        except Exception as e:
            # 记录请求失败
            duration = time.time() - start_time
            self.logger.error(
                f"Request failed: {method} {path}",
                extra={
                    "request_id": request_id,
                    "method": method,
                    "path": path,
                    "duration_ms": round(duration * 1000, 2),
                    "error": str(e),
                },
                exc_info=True,
            )
            raise


# 装饰器：记录函数执行
def log_execution(logger_name: str = "app"):
    """
    记录函数执行的装饰器

    Args:
        logger_name: 日志器名称
    """

    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            logger = get_logger(logger_name)
            func_name = func.__name__

            logger.debug(f"Executing: {func_name}")
            start_time = time.time()

            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                logger.debug(
                    f"Completed: {func_name}",
                    extra={"duration_ms": round(duration * 1000, 2)},
                )
                return result
            except Exception as e:
                duration = time.time() - start_time
                logger.error(
                    f"Failed: {func_name}",
                    extra={"duration_ms": round(duration * 1000, 2), "error": str(e)},
                    exc_info=True,
                )
                raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            logger = get_logger(logger_name)
            func_name = func.__name__

            logger.debug(f"Executing: {func_name}")
            start_time = time.time()

            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                logger.debug(
                    f"Completed: {func_name}",
                    extra={"duration_ms": round(duration * 1000, 2)},
                )
                return result
            except Exception as e:
                duration = time.time() - start_time
                logger.error(
                    f"Failed: {func_name}",
                    extra={"duration_ms": round(duration * 1000, 2), "error": str(e)},
                    exc_info=True,
                )
                raise

        import asyncio

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


# 初始化日志
logger = setup_logging()
