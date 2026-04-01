#!/bin/bash

# 智能水站管理系统 - 一键启动脚本

echo "======================================"
echo "智能水站管理系统 - 启动中..."
echo "======================================"

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# 停止已有服务
echo ""
echo "停止已有服务..."
pkill -f "uvicorn main:app" 2>/dev/null
pkill -f "python.*http.server.*8888" 2>/dev/null
sleep 1

# 启动后端 API 服务
echo ""
echo "启动后端 API 服务..."
cd "$PROJECT_ROOT/backend"
nohup python3 -m uvicorn main:app --host 127.0.0.1 --port 8000 > /tmp/water-api.log 2>&1 &
BACKEND_PID=$!
echo "  后端 PID: $BACKEND_PID"
sleep 2

# 检查后端是否启动成功
if curl -s http://localhost:8000/api/health > /dev/null 2>&1; then
    echo "  ✅ 后端 API 启动成功"
else
    echo "  ❌ 后端 API 启动失败"
    exit 1
fi

# 启动前端服务
echo ""
echo "启动前端服务..."
cd "$PROJECT_ROOT/frontend"
nohup python3 -m http.server 8888 > /tmp/water-frontend.log 2>&1 &
FRONTEND_PID=$!
echo "  前端 PID: $FRONTEND_PID"
sleep 1

# 检查前端是否启动成功
if curl -s http://localhost:8888/ > /dev/null 2>&1; then
    echo "  ✅ 前端服务启动成功"
else
    echo "  ❌ 前端服务启动失败"
    exit 1
fi

echo ""
echo "======================================"
echo "✅ 系统启动成功！"
echo "======================================"
echo ""
echo "访问地址:"
echo "  - 管理后台: http://localhost:8888/admin.html"
echo "  - 用户端:   http://localhost:8888/index.html"
echo "  - 服务预约: http://localhost:8888/bookings.html"
echo "  - 预约日历: http://localhost:8888/calendar.html"
echo ""
echo "API 地址:"
echo "  - 健康检查: http://localhost:8000/api/health"
echo "  - 产品列表: http://localhost:8000/api/products"
echo ""
echo "停止服务:"
echo "  pkill -f 'uvicorn main:app'"
echo "  pkill -f 'http.server 8888'"
echo ""
echo "日志文件:"
echo "  - 后端日志: /tmp/water-api.log"
echo "  - 前端日志: /tmp/water-frontend.log"
echo ""