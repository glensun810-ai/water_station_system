"""
静态文件服务配置
提供前端静态文件访问
"""

import os
from pathlib import Path
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse


def setup_static_files(app):
    """
    配置静态文件服务

    Args:
        app: FastAPI应用实例
    """
    FRONTEND_DIR = Path(__file__).parent.parent / "frontend"

    if FRONTEND_DIR.exists():
        app.mount(
            "/frontend",
            StaticFiles(directory=str(FRONTEND_DIR), html=True),
            name="frontend",
        )
        print(f"✓ 前端目录已挂载: {FRONTEND_DIR}")

        app.mount(
            "/water-admin",
            StaticFiles(directory=str(FRONTEND_DIR), html=True),
            name="water-admin",
        )
        print(f"✓ 水站管理目录已挂载: {FRONTEND_DIR}")

    # 挂载 portal 目录
    PORTAL_DIR = Path(__file__).parent.parent.parent / "portal"
    if PORTAL_DIR.exists():
        app.mount(
            "/portal",
            StaticFiles(directory=str(PORTAL_DIR), html=True),
            name="portal",
        )
        print(f"✓ Portal目录已挂载: {PORTAL_DIR}")
    else:
        print(f"⚠ Portal目录不存在: {PORTAL_DIR}")

    MEETING_FRONTEND_DIR = (
        Path(__file__).parent.parent.parent / "Service_MeetingRoom" / "frontend"
    )

    if MEETING_FRONTEND_DIR.exists():
        app.mount(
            "/meeting-frontend",
            StaticFiles(directory=str(MEETING_FRONTEND_DIR), html=True),
            name="meeting-frontend",
        )
        print(f"✓ 会议室前端目录已挂载: {MEETING_FRONTEND_DIR}")
    else:
        print(f"⚠ 会议室前端目录不存在: {MEETING_FRONTEND_DIR}")

    # 根路径重定向
    @app.get("/")
    async def root():
        """根路径重定向到登录页面"""
        return RedirectResponse(url="/frontend/login.html")

    # 健康检查端点
    @app.get("/health")
    async def health_check():
        """健康检查"""
        return {
            "status": "healthy",
            "service": "Enterprise Service Platform",
            "version": "2.0.0",
        }

    print("\n" + "=" * 50)
    print("企业服务管理平台启动成功！")
    print("=" * 50)
    print("\n访问地址:")
    print("  - 登录页面: http://localhost:8080/frontend/login.html")
    print("  - 水站管理: http://localhost:8080/water-admin/login.html")
    print("  - 管理后台: http://localhost:8080/frontend/admin.html")
    print("  - 预约页面: http://localhost:8080/frontend/index.html")
    print("  - 会议室管理: http://localhost:8080/meeting-frontend/admin.html")
    print("  - API文档:  http://localhost:8080/docs")
    print("  - 健康检查: http://localhost:8080/health")
    print("\n默认管理员:")
    print("  - 用户名: admin")
    print("  - 密码: 见 .env 文件")
    print("=" * 50 + "\n")
