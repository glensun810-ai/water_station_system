#!/bin/bash
# 清理 Python 缓存并重启后端服务

cd /Users/sgl/PycharmProjects/AIchanyejiqun/Service_WaterManage/backend

echo "=== 清理 Python 缓存 ==="
find . -type d -name "__pycache__" -exec rm -rf {} +
find . -name "*.pyc" -delete

echo "=== 验证文件修改 ==="
grep "Depends(get_db)" api_unified.py | head -5

echo "=== 准备启动服务 ==="
echo "请在 PyCharm 中停止当前运行的服务，然后重新运行 main.py"
