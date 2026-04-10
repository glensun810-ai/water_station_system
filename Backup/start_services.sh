#!/bin/bash

# AI产业集群空间服务系统 - 启动脚本（Linux/Mac）
# 功能：自动检查端口、启动服务、打开浏览器

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "============================================================"
echo "AI产业集群空间服务系统 - 启动器"
echo "============================================================"
echo ""

# 检查Python是否安装
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ 错误: 未找到Python3，请先安装Python3${NC}"
    exit 1
fi

# 检查Python版本
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo -e "${GREEN}✅ Python版本: ${PYTHON_VERSION}${NC}"

# 检查依赖
echo ""
echo "检查依赖..."
if ! python3 -c "import fastapi" 2>/dev/null; then
    echo -e "${YELLOW}⚠️ 正在安装依赖...${NC}"
    pip install -r requirements.txt
fi

# 运行启动脚本
echo ""
echo "正在启动服务..."
python3 start_services.py

if [ $? -ne 0 ]; then
    echo ""
    echo -e "${RED}❌ 服务启动失败${NC}"
    exit 1
fi