"""
AI产业集群空间服务系统 - 重构版主入口
目标：< 500行，仅保留路由挂载和启动配置
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from pathlib import Path

# 导入配置
from config.database import engine, Base, get_db
from config.settings import settings

# 导入API路由（待提取）
# from api.auth import router as auth_router
# from api.water import router as water_router
# from api.meeting import router as meeting_router

# 创建应用
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

# 注册路由（待添加）
# app.include_router(auth_router)
# app.include_router(water_router)
# app.include_router(meeting_router)

# 挂载静态文件
FRONTEND_DIR = Path(__file__).parent.parent / "frontend"
MEETING_FRONTEND_DIR = (
    Path(__file__).parent.parent.parent / "Service_MeetingRoom" / "frontend"
)
PORTAL_DIR = Path(__file__).parent.parent.parent / "portal"

print(f"\n正在挂载静态文件目录...")
print(f"  FRONTEND_DIR: {FRONTEND_DIR} (exists: {FRONTEND_DIR.exists()})")
print(f"  PORTAL_DIR: {PORTAL_DIR} (exists: {PORTAL_DIR.exists()})")
print(
    f"  MEETING_FRONTEND_DIR: {MEETING_FRONTEND_DIR} (exists: {MEETING_FRONTEND_DIR.exists()})"
)

if FRONTEND_DIR.exists():
    app.mount(
        "/frontend",
        StaticFiles(directory=str(FRONTEND_DIR), html=True),
        name="frontend",
    )
    app.mount(
        "/water-admin",
        StaticFiles(directory=str(FRONTEND_DIR), html=True),
        name="water-admin",
    )
    print(f"✓ 前端目录已挂载")

if MEETING_FRONTEND_DIR.exists():
    app.mount(
        "/meeting-frontend",
        StaticFiles(directory=str(MEETING_FRONTEND_DIR), html=True),
        name="meeting-frontend",
    )
    print(f"✓ 会议室前端目录已挂载")

if PORTAL_DIR.exists():
    app.mount(
        "/portal", StaticFiles(directory=str(PORTAL_DIR), html=True), name="portal"
    )
    print(f"✓ Portal目录已挂载")


# 根路径重定向
@app.get("/")
async def root():
    return RedirectResponse(url="/portal/index.html")


# 健康检查
@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "2.0.0"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=settings.PORT)
