"""
AI产业集群空间服务系统主API路由
统一暴露所有服务的API端点 following API design specification
"""

from fastapi import FastAPI, APIRouter, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler
from utils.rate_limiter import limiter
import os
import logging

# Import the unified v1 API routes
from apps.api.v1.water import router as water_router
from apps.api.v1.meeting import router as meeting_router
from apps.api.v1.system import router as system_router
from apps.api.v1.products import router as products_router
from apps.api.v1.products import category_router as product_categories_router
from apps.api.v1.offices import router as offices_router
from apps.api.v1.accounts import router as accounts_router
from apps.api.v1.membership import router as membership_router
from apps.api.v1.membership import admin_router as admin_membership_router
from apps.api.v1.membership_order import router as membership_order_router
from apps.api.v1.user_balance import router as user_balance_router
from apps.api.v1.admin_membership_order import router as admin_membership_order_router
from apps.api.v1.admin_balance import router as admin_balance_router
from apps.water.api_user_auth import router as user_auth_router

# Import the unified v2 API routes (Space Service)
from apps.api.v2.space_types import router as space_types_router
from apps.api.v2.space_resources import router as space_resources_router
from apps.api.v2.space_bookings import router as space_bookings_router
from apps.api.v2.space_approvals import router as space_approvals_router
from apps.api.v2.space_payments import router as space_payments_router
from apps.api.v2.space_statistics import router as space_statistics_router
from apps.api.v2.unified_settlement import router as unified_settlement_router
from apps.api.v2.space_payment_settlement import (
    router as space_payment_settlement_router,
)

from apps.water.api_login_logs import router as login_logs_router
from apps.api.v1.upload import router as upload_router

from apps.error_handlers import register_exception_handlers
from utils.logger import RequestLoggingMiddleware

# 导入space模型以确保表被创建
from shared.models.space import *

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create main application
app = FastAPI(
    title="AI产业集群空间服务系统 API",
    description="统一的办公空间服务平台API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Register exception handlers FIRST - ensure all errors return JSON
register_exception_handlers(app)
logger.info("Exception handlers registered successfully")

# Configure CORS
from config.settings import settings

cors_origins = settings.CORS_ALLOW_ORIGINS
cors_credentials = settings.CORS_ALLOW_CREDENTIALS

if settings.ENVIRONMENT == "production":
    if "*" in cors_origins and cors_credentials:
        raise ValueError(
            "生产环境不允许 allow_origins=['*'] 与 allow_credentials=True 同时使用"
        )

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=cors_credentials,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
)

# Register request logging middleware
app.add_middleware(RequestLoggingMiddleware)
logger.info("Request logging middleware registered")

# Create v1 version router
v1_router = APIRouter(prefix="/api/v1")

# Register all service routes to v1 version with proper prefixes
v1_router.include_router(water_router, tags=["水站服务"])
v1_router.include_router(meeting_router, tags=["会议室服务"])
v1_router.include_router(system_router, tags=["系统服务"])
v1_router.include_router(products_router, tags=["产品管理"])
v1_router.include_router(product_categories_router, tags=["产品分类"])
v1_router.include_router(offices_router, tags=["办公室管理"])
v1_router.include_router(accounts_router, tags=["办公室账户管理"])
v1_router.include_router(membership_router, tags=["会员套餐"])
v1_router.include_router(admin_membership_router, tags=["管理员-会员套餐管理"])
v1_router.include_router(membership_order_router, tags=["会员订单"])
v1_router.include_router(user_balance_router, tags=["用户余额"])
v1_router.include_router(admin_membership_order_router, tags=["管理员-会员订单"])
v1_router.include_router(admin_balance_router, tags=["管理员-余额管理"])
v1_router.include_router(login_logs_router, tags=["系统日志"])
v1_router.include_router(user_auth_router, tags=["用户认证"])
v1_router.include_router(upload_router, tags=["文件上传"])

# Create v2 version router (Space Service - 新架构)
v2_router = APIRouter(prefix="/api/v2")

# Register space service routes to v2 version
v2_router.include_router(space_types_router)
v2_router.include_router(space_resources_router)
v2_router.include_router(space_bookings_router)
v2_router.include_router(space_approvals_router)
v2_router.include_router(space_payments_router)
v2_router.include_router(space_statistics_router)
v2_router.include_router(unified_settlement_router)
v2_router.include_router(space_payment_settlement_router)

# Add routers to main app
app.include_router(v1_router)
app.include_router(v2_router)

# Mount static files for portal and shared resources
portal_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "portal")
shared_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "shared")
water_frontend_dir = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "apps", "water", "frontend"
)
meeting_frontend_dir = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "apps", "meeting", "frontend"
)

if os.path.exists(portal_dir):
    app.mount("/portal", StaticFiles(directory=portal_dir, html=True), name="portal")

if os.path.exists(shared_dir):
    app.mount("/shared", StaticFiles(directory=shared_dir), name="shared")

# Mount uploaded files directory
uploads_dir = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "data", "uploads", "images"
)
os.makedirs(uploads_dir, exist_ok=True)
app.mount("/data/uploads/images", StaticFiles(directory=uploads_dir), name="uploads")

if os.path.exists(water_frontend_dir):
    app.mount(
        "/water",
        StaticFiles(directory=water_frontend_dir, html=True),
        name="water",
    )

if os.path.exists(meeting_frontend_dir):
    app.mount(
        "/meeting-frontend",
        StaticFiles(directory=meeting_frontend_dir, html=True),
        name="meeting-frontend",
    )

# Mount space frontend (新空间服务前端)
space_frontend_dir = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "space-frontend"
)

if os.path.exists(space_frontend_dir):
    app.mount(
        "/space-frontend",
        StaticFiles(directory=space_frontend_dir, html=True),
        name="space-frontend",
    )


@app.get("/")
async def root():
    return {"message": "AI产业集群空间服务系统 API v1.0"}


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    from datetime import datetime

    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
    }


if __name__ == "__main__":
    import uvicorn
    from datetime import datetime

    uvicorn.run(app, host="0.0.0.0", port=8000)
