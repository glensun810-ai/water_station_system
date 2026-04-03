#!/bin/bash

# 企业服务管理平台启动脚本

cd "$(dirname "$0")/Service_WaterManage/backend"

echo "正在启动企业服务管理平台..."
echo "API端口: 8080"
echo "前端访问: http://localhost:8080/frontend/"
echo ""

# 启动服务
uvicorn main:app --host 0.0.0.0 --port 8080 --reload