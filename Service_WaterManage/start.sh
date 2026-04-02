#!/bin/bash

# 企业服务管理平台启动脚本

echo "================================"
echo "企业服务管理平台启动中..."
echo "================================"

# 进入后端目录
cd "$(dirname "$0")/backend"

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到 Python3"
    exit 1
fi

# 检查.env文件
if [ ! -f ".env" ]; then
    echo "警告: .env 文件不存在，使用默认配置"
fi

# 使用新的启动脚本
python3 run.py