"""
AI产业集群空间服务 - 用餐服务
独立用餐服务
"""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from config.settings import settings
from config.database import engine
from models.base import Base

# 创建应用
app = FastAPI(
    title=settings.APP_NAME,
    description="用餐服务 - AI产业集群空间服务系统",
    version=settings.APP_VERSION,
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

# 注册路由
from api.dining import router as dining_router

app.include_router(dining_router)

# 挂载静态文件
frontend_dir = Path(__file__).parent.parent / "frontend"
if frontend_dir.exists():
    app.mount(
        "/",
        StaticFiles(directory=str(frontend_dir), html=True),
        name="frontend",
    )


# 根路径
@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
    }


if __name__ == "__main__":
    import uvicorn

    # 从环境变量获取端口，默认使用配置中的端口
    port = int(os.getenv("PORT", settings.PORT))
    uvicorn.run(app, host=settings.HOST, port=port)
