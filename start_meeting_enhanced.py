#!/usr/bin/env python3
"""
会议室管理模块优化 - 快速启动脚本
用于快速测试新功能
"""

import sys
import os

# 添加项目路径
sys.path.insert(0, "/Users/sgl/PycharmProjects/AIchanyejiqun")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# 导入新模块路由
from Service_MeetingRoom.modules.flexible_booking.api_flexible_booking import (
    router as flexible_router,
)
from Service_MeetingRoom.modules.admin_auth.api_admin_auth import router as admin_router

# 导入现有路由
from Service_WaterManage.backend.api_meeting import router as meeting_router

# 创建FastAPI应用
app = FastAPI(
    title="会议室管理系统 - 优化版",
    description="会议室管理模块优化计划实现",
    version="1.0.0",
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(meeting_router)
app.include_router(flexible_router)
app.include_router(admin_router)


@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "会议室管理系统 - 优化版",
        "version": "1.0.0",
        "features": ["灵活时间段选择", "管理员权限验证", "会议室管理", "预约管理"],
        "docs": "/docs",
        "admin_login": {"username": "admin", "password": "admin123"},
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "modules": {"flexible_booking": "✓", "admin_auth": "✓", "meeting": "✓"},
    }


if __name__ == "__main__":
    print("=" * 70)
    print("会议室管理系统 - 优化版启动")
    print("=" * 70)
    print("\n新功能模块：")
    print("  1. 灵活时间段选择 - 支持自定义时间段、冲突检测")
    print("  2. 管理员权限验证 - JWT认证、角色权限、操作日志")
    print("\n默认管理员账号：")
    print("  用户名: admin")
    print("  密码: admin123")
    print("\nAPI文档：")
    print("  Swagger UI: http://localhost:8000/docs")
    print("  ReDoc: http://localhost:8000/redoc")
    print("\n测试命令：")
    print("  # 检查时间段可用性")
    print(
        "  curl -X POST http://localhost:8000/api/meeting/flexible/check-time-slot \\"
    )
    print("    -H 'Content-Type: application/json' \\")
    print(
        '    -d \'{"room_id": 1, "booking_date": "2026-04-02", "start_time": "09:00", "end_time": "12:00"}\''
    )
    print("\n  # 管理员登录")
    print("  curl -X POST http://localhost:8000/api/admin/login \\")
    print("    -H 'Content-Type: application/json' \\")
    print('    -d \'{"username": "admin", "password": "admin123"}\'')
    print("\n" + "=" * 70)

    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
