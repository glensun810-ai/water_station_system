#!/usr/bin/env python3
"""
企业服务管理平台 - 启动脚本
提供简化的启动方式和静态文件服务配置
"""

import sys
import os

backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_dir)

from main import app

from static_config import setup_static_files

setup_static_files(app)

from api_new.users import router as users_router
from api_new.products import router as products_router
from api_new.transactions import router as transactions_router
from api_new.auth import router as auth_router

app.include_router(users_router)
app.include_router(products_router)
app.include_router(transactions_router)
app.include_router(auth_router)

if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", 8080))

    uvicorn.run(app, host="0.0.0.0", port=port)
