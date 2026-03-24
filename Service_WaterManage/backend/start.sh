#!/bin/bash
# 智能水站管理系统 - 启动脚本

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "🚰 智能水站管理系统 - 启动中..."

# 获取端口（默认 8000）
PORT=${PORT:-8000}

# 检查并清理端口
echo "📌 检查端口 $PORT ..."
PID=$(lsof -ti:$PORT 2>/dev/null)

if [ ! -z "$PID" ]; then
    echo -e "${YELLOW}⚠️  端口 $PORT 被占用 (PID: $PID)，正在清理...${NC}"
    kill -9 $PID 2>/dev/null
    sleep 2
    
    # 验证是否清理成功
    PID=$(lsof -ti:$PORT 2>/dev/null)
    if [ ! -z "$PID" ]; then
        echo -e "${RED}✗ 无法清理端口 $PORT，请手动处理${NC}"
        exit 1
    fi
fi

echo -e "${GREEN}✓ 端口 $PORT 可用${NC}"

# 启动服务
echo "🚀 启动后端服务..."
cd "$(dirname "$0")"
python main.py
