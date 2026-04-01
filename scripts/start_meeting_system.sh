#!/bin/bash
# 会议室管理系统 - 快速启动脚本
# 确保所有服务正确启动

echo "🚀 启动会议室管理系统..."

# 进入后端目录
cd "$(dirname "$0")/../Service_WaterManage/backend"

# 检查是否有旧进程
OLD_PID=$(lsof -ti:8000)
if [ ! -z "$OLD_PID" ]; then
    echo "⚠️  发现旧进程 (PID: $OLD_PID)，正在关闭..."
    kill -9 $OLD_PID
    sleep 2
fi

# 启动后端服务
echo "🔧 启动后端服务..."
nohup python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 > ../../logs/backend.log 2>&1 &
BACKEND_PID=$!

# 等待服务启动
echo "⏳ 等待服务启动..."
sleep 5

# 验证服务状态
echo "🔍 验证服务状态..."
if curl -s http://localhost:8000/api/health > /dev/null; then
    echo "✅ 主服务正常"
else
    echo "❌ 主服务启动失败"
    exit 1
fi

if curl -s http://localhost:8000/api/meeting/health > /dev/null; then
    echo "✅ 会议室服务正常"
else
    echo "❌ 会议室服务启动失败"
    exit 1
fi

# 显示访问地址
echo ""
echo "✅ 系统启动成功！"
echo ""
echo "📍 访问地址:"
echo "  - Portal:        http://localhost:8080/portal/index.html"
echo "  - 列表视图:      http://localhost:8080/Service_MeetingRoom/frontend/index.html"
echo "  - 日历视图:      http://localhost:8080/Service_WaterManage/frontend/calendar.html"
echo "  - 管理后台:      http://localhost:8080/Service_MeetingRoom/frontend/admin.html"
echo ""
echo "📊 后端API:"
echo "  - Health:        http://localhost:8000/api/meeting/health"
echo "  - Rooms:         http://localhost:8000/api/meeting/rooms"
echo "  - Offices:       http://localhost:8000/api/meeting/offices"
echo "  - Bookings:      http://localhost:8000/api/meeting/bookings"
echo ""
echo "📝 后端进程 PID: $BACKEND_PID"
echo "📝 日志文件: logs/backend.log"
echo ""
echo "使用 'kill $BACKEND_PID' 停止服务"