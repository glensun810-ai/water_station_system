"""
Enterprise Service Platform - Backend API
企业服务平台 - 统一后端入口

架构说明：
- 本文件仅负责应用初始化和路由挂载
- 所有业务逻辑在 core/, services/, api/ 模块中
- 旧版内联路由已迁移至 api/legacy.py
- 旧版平铺api_*.py文件保持兼容，后续逐步迁移
"""

import sys
import os

# 确保后端目录在 Python 路径中
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from config.settings import settings
from config.database import (
    db_manager,
    get_db,
    SessionLocal,
    MeetingSessionLocal,
    engine,
)
from models.base import Base

# ==================== 应用初始化 ====================

app = FastAPI(
    title=settings.APP_NAME,
    description="AI产业集群空间服务系统 - 水站/会议室/用餐服务统一管理平台",
    version=settings.APP_VERSION,
)

# CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ALLOW_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
)

# 数据库表初始化
Base.metadata.create_all(bind=db_manager.main_engine)

# ==================== 健康检查 ====================
# ⚠️ 健康检查端点必须在静态文件挂载之前定义，否则会被覆盖


@app.get("/health")
def root_health_check():
    """根路径健康检查"""
    from datetime import datetime

    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "timestamp": datetime.now().isoformat(),
    }


@app.get("/api/health")
def api_health_check():
    """API健康检查"""
    from datetime import datetime

    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "timestamp": datetime.now().isoformat(),
    }


@app.get("/api/ready")
def readiness_check():
    """就绪检查并初始化必要表"""
    from sqlalchemy import text

    try:
        with db_manager.main_engine.connect() as conn:
            conn.execute(text("SELECT 1"))

        # 初始化登录日志表
        try:
            with db_manager.main_engine.begin() as conn:
                conn.execute(
                    text("""
                    CREATE TABLE IF NOT EXISTS user_login_logs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        username VARCHAR(100),
                        role VARCHAR(50),
                        login_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        ip_address VARCHAR(50),
                        user_agent TEXT,
                        device_type VARCHAR(50),
                        browser VARCHAR(100),
                        os VARCHAR(100),
                        login_method VARCHAR(20) DEFAULT 'password',
                        status VARCHAR(20) NOT NULL,
                        failure_reason VARCHAR(255),
                        logout_time TIMESTAMP,
                        session_duration INTEGER,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                )
        except:
            pass

        return {"status": "ready", "database": "connected"}
    except Exception as e:
        return {"status": "not_ready", "database": "error", "detail": str(e)}


# ==================== 静态文件服务 ====================
# ⚠️ 重要：静态文件挂载顺序很重要
# 1. Portal首页挂载到/portal路径
# 2. 其他静态文件挂载到子路径


# Portal首页（挂载到/portal路径）
portal_dir = os.path.join(backend_dir, "..", "..", "portal")
if os.path.exists(portal_dir):
    print(f"✓ 挂载Portal目录: {portal_dir}")
    app.mount("/portal", StaticFiles(directory=portal_dir, html=True), name="portal")
else:
    print(f"⚠️ Portal目录不存在: {portal_dir}")

# 水站前端（挂载到/water路径）
frontend_dir = os.path.join(backend_dir, "..", "..", "Service_WaterManage", "frontend")
if os.path.exists(frontend_dir):
    print(f"✓ 挂载水站前端目录: {frontend_dir}")
    app.mount(
        "/water",
        StaticFiles(directory=frontend_dir, html=True),
        name="water-frontend",
    )
else:
    print(f"⚠️ 水站前端目录不存在: {frontend_dir}")

# 会议室前端（挂载到/meeting-frontend路径）
meeting_frontend_dir = os.path.join(
    backend_dir, "..", "..", "Service_MeetingRoom", "frontend"
)
if os.path.exists(meeting_frontend_dir):
    print(f"✓ 挂载会议室前端目录: {meeting_frontend_dir}")
    app.mount(
        "/meeting-frontend",
        StaticFiles(directory=meeting_frontend_dir, html=True),
        name="meeting-frontend",
    )
else:
    print(f"⚠️ 会议室前端目录不存在: {meeting_frontend_dir}")


# 根路径重定向到Portal首页
@app.get("/")
def root_redirect():
    """根路径重定向到Portal首页"""
    from fastapi.responses import RedirectResponse

    return RedirectResponse(url="/portal/index.html")


# ==================== 静态文件服务 ====================
# ⚠️ 重要：静态文件必须在路由挂载之前挂载，否则路由会覆盖静态文件

# ==================== 核心域路由 ====================

from core.user.api import router as core_user_router
from core.office.api import router as core_office_router
from core.settlement.api import router as core_settlement_router
from api_user_auth import router as user_auth_router

app.include_router(core_user_router)
app.include_router(core_office_router)
app.include_router(core_settlement_router)
app.include_router(user_auth_router)

# ==================== 服务域路由 ====================

# 注意：services/下的文件与根目录api_*.py存在重复
# 当前策略：优先使用根目录api_*.py（已验证可用），services/暂不挂载
# 后续迁移完成后再切换

# from services.water.packages import router as water_packages_router
# from services.water.services import router as water_services_router
# from services.meeting.api import router as meeting_router
# from services.meeting.payment import router as meeting_payment_router
# from services.meeting.approval import router as meeting_approval_router
# from services.dining.api import router as dining_router

# app.include_router(water_packages_router)
# app.include_router(water_services_router)
# app.include_router(meeting_router)
# app.include_router(meeting_payment_router)
# app.include_router(meeting_approval_router)
# app.include_router(dining_router)

# ==================== 旧版平铺API路由（保持向后兼容） ====================
# 这些文件已包含完整的路由定义，暂时保持不变
# 后续逐步迁移到 core/ 和 services/ 目录

from api_office import router as legacy_office_router
from api_unified import router as legacy_unified_router
from api_unified_settlement import router as legacy_unified_settlement_router
from api_unified_order import router as legacy_unified_order_router
from api_meeting import router as legacy_meeting_router
from api_meeting_payment import router as legacy_meeting_payment_router
from api_meeting_approval import router as legacy_meeting_approval_router
from api_flexible_booking import router as legacy_flexible_router
from api_admin_auth import router as legacy_admin_router
from api_packages import router as legacy_packages_router
from api_coupon import router as legacy_coupon_router
from api_services import router as legacy_services_router
from api_dining import router as legacy_dining_router
from api_migration import router as legacy_migration_router
from api_dashboard_water import router as water_dashboard_router
from api_dashboard_meeting import router as meeting_dashboard_router
from api_user_management import router as user_management_router
from api_settlement_management import router as settlement_management_router
from api_office_admin import router as office_admin_router
from api_login_logs import router as login_logs_router
from api_membership_plan import router as membership_plan_router
from api_payment import router as payment_router
from api_refund import router as refund_router
from api_invoice import router as invoice_router

app.include_router(legacy_office_router)
app.include_router(legacy_unified_router)
app.include_router(legacy_unified_settlement_router)
app.include_router(legacy_unified_order_router)
app.include_router(legacy_meeting_router)
app.include_router(legacy_meeting_payment_router)
app.include_router(legacy_meeting_approval_router)
app.include_router(legacy_flexible_router)
app.include_router(legacy_admin_router)
app.include_router(legacy_packages_router)
app.include_router(legacy_coupon_router)
app.include_router(legacy_services_router)
app.include_router(legacy_dining_router)
app.include_router(legacy_migration_router)

# Dashboard统计路由
app.include_router(water_dashboard_router)
app.include_router(meeting_dashboard_router)

# 系统管理路由
app.include_router(user_management_router)
app.include_router(settlement_management_router)
app.include_router(office_admin_router)
app.include_router(login_logs_router)

# 会员支付路由
app.include_router(membership_plan_router)
app.include_router(payment_router)
app.include_router(refund_router)
app.include_router(invoice_router)

# ==================== 健康检查 ====================


@app.get("/health")
def root_health_check():
    """根路径健康检查"""
    from datetime import datetime

    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "timestamp": datetime.now().isoformat(),
    }


@app.get("/api/health")
def api_health_check():
    from datetime import datetime

    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "timestamp": datetime.now().isoformat(),
    }


@app.get("/api/ready")
def readiness_check():
    from sqlalchemy import text

    try:
        with db_manager.main_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"status": "ready", "database": "connected"}
    except Exception as e:
        return {"status": "not_ready", "database": "error", "detail": str(e)}


# ==================== Portal 聚合API ====================


@app.get("/api/unified/user/{user_id}/balance")
def get_unified_user_balance(user_id: int):
    """获取用户统一余额信息（Portal首页使用）"""
    from config.database import get_db
    from models.user import User
    from models.prepaid import PrepaidOrder
    from sqlalchemy.orm import Session
    from fastapi import HTTPException

    db_gen = get_db()
    db: Session = next(db_gen)
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")

        prepaid_orders = (
            db.query(PrepaidOrder)
            .filter(
                PrepaidOrder.user_id == user_id,
                PrepaidOrder.payment_status == "paid",
                PrepaidOrder.is_active == 1,
            )
            .all()
        )

        balance_prepaid = sum(
            (order.total_qty - order.used_qty) * order.unit_price
            for order in prepaid_orders
        )

        return {
            "user_id": user_id,
            "balance_credit": user.balance_credit or 0,
            "balance_prepaid": balance_prepaid,
            "total_balance": (user.balance_credit or 0) + balance_prepaid,
        }
    finally:
        db.close()


@app.get("/api/meeting/user/{user_id}/free-hours")
def get_meeting_user_free_hours(user_id: int):
    """获取用户会议室免费时长（Portal首页使用）"""
    from datetime import date
    from sqlalchemy import func, and_

    try:
        from services.meeting.api import (
            MeetingSessionLocal,
            MeetingBooking,
        )

        meeting_db = MeetingSessionLocal()
        try:
            today = date.today()
            month_start = date(today.year, today.month, 1)
            month_end = (
                date(today.year, today.month + 1, 1)
                if today.month < 12
                else date(today.year + 1, 1, 1)
            )

            used_free_hours = (
                meeting_db.query(func.sum(MeetingBooking.duration_hours))
                .filter(
                    and_(
                        MeetingBooking.user_id == user_id,
                        MeetingBooking.booking_date >= month_start,
                        MeetingBooking.booking_date < month_end,
                        MeetingBooking.status.in_(["confirmed", "completed"]),
                    )
                )
                .scalar()
                or 0
            )

            total_free_hours = 5
            remaining_hours = max(0, total_free_hours - float(used_free_hours))

            return {
                "user_id": user_id,
                "total_free_hours": total_free_hours,
                "used_free_hours": float(used_free_hours),
                "free_hours": remaining_hours,
                "month": f"{today.year}-{today.month:02d}",
            }
        finally:
            meeting_db.close()
    except Exception as e:
        return {
            "user_id": user_id,
            "total_free_hours": 5,
            "used_free_hours": 0,
            "free_hours": 5,
            "month": f"{date.today().year}-{date.today().month:02d}",
            "error": str(e),
        }


# ==================== 向后兼容导出 ====================
# 以下导出供旧版 api_*.py 文件使用（from main import xxx）
# 后续迁移完成后删除

from config.settings import settings as _settings
from models.product import Product
from models.pickup import OfficePickup
from models.inventory import InventoryRecord
from models.user import User

SECRET_KEY = _settings.SECRET_KEY
ALGORITHM = _settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = _settings.ACCESS_TOKEN_EXPIRE_HOURS * 60
SQLALCHEMY_DATABASE_URL = _settings.DATABASE_URL


# ==================== 启动服务 ====================
if __name__ == "__main__":
    import uvicorn
    import os

    # 从环境变量获取端口，默认使用配置中的端口
    port = int(os.getenv("PORT", settings.PORT))

    print("\n" + "=" * 60)
    print("企业服务平台启动成功！")
    print("=" * 60)
    print("\n访问地址:")
    print(f"  - Portal首页: http://localhost:{port}/portal/index.html")
    print(f"  - 水站管理: http://localhost:{port}/water-admin/index.html")
    print(f"  - 管理后台: http://localhost:{port}/portal/admin/login.html")
    print(f"  - API文档: http://localhost:{port}/docs")
    print("=" * 60 + "\n")

    uvicorn.run(app, host="0.0.0.0", port=port)
