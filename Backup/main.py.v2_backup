"""
AI产业集群空间服务系统 - V2版本（模块化架构）
整合所有模块化API，保持向后兼容
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from pathlib import Path

# 导入配置
from config.database import engine, Base, get_db
from config.settings import settings

# 导入现有API模块
from api_meeting import router as meeting_router
from api_meeting_payment import router as meeting_payment_router
from api_meeting_approval import router as meeting_approval_router
from api_packages import router as packages_router
# from api_dining import router as dining_router  # 如有需要

# 导入原始main.py中的核心功能（暂时保留内联）
from main import app as original_app

# 创建新应用
app = FastAPI(
    title="AI产业集群空间服务",
    description="水站管理、会议室预约、用餐服务",
    version="2.0.0"
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ALLOW_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
)

# 创建数据库表
Base.metadata.create_all(bind=engine)

# 注册模块化API路由
app.include_router(meeting_router, prefix="/api")
app.include_router(meeting_payment_router, prefix="/api")
app.include_router(meeting_approval_router, prefix="/api")
app.include_router(packages_router, prefix="/api")

# 从原始app复制所有路由（临时方案）
for route in original_app.routes:
    if route.path not in [r.path for r in app.routes]:
        app.routes.append(route)

# 挂载静态文件
FRONTEND_DIR = Path(__file__).parent.parent / "frontend"
MEETING_FRONTEND_DIR = (
    Path(__file__).parent.parent.parent / "Service_MeetingRoom" / "frontend"
)
PORTAL_DIR = Path(__file__).parent.parent.parent / "portal"

if FRONTEND_DIR.exists():
    app.mount("/frontend", StaticFiles(directory=str(FRONTEND_DIR), html=True))
    app.mount("/water-admin", StaticFiles(directory=str(FRONTEND_DIR), html=True))

if MEETING_FRONTEND_DIR.exists():
    app.mount("/meeting-frontend", StaticFiles(directory=str(MEETING_FRONTEND_DIR), html=True))

if PORTAL_DIR.exists():
    app.mount("/portal", StaticFiles(directory=str(PORTAL_DIR), html=True))

# 根路径重定向
@app.get("/")
async def root():
    return RedirectResponse(url="/portal/index.html")

@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "2.0.0"}

if __name__ == "__main__":
    import uvicorn
    print("\n" + "="*50)
    print("企业服务管理平台启动成功！(V2模块化架构)")
    print("="*50)
    print("\n访问地址:")
    print("  - Portal首页: http://localhost:8000/")
    print("  - 水站管理: http://localhost:8000/water-admin/index.html")
    print("  - 会议室管理: http://localhost:8000/meeting-frontend/index.html")
    print("  - 管理后台: http://localhost:8000/portal/admin/login.html")
    print("="*50 + "\n")
    uvicorn.run(app, host="0.0.0.0", port=settings.PORT)
