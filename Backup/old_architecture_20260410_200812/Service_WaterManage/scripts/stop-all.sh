#!/bin/bash

# 停止所有服务

echo "停止智能水站管理系统..."

# 停止后端
pkill -f "uvicorn main:app" 2>/dev/null
echo "  ✅ 后端已停止"

# 停止前端
pkill -f "http.server 8888" 2>/dev/null
echo "  ✅ 前端已停止"

echo ""
echo "所有服务已停止"