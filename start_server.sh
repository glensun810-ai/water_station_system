#!/bin/bash
cd /Users/sgl/PycharmProjects/AIchanyejiqun

# 清理进程
pkill -9 -f uvicorn
sleep 2

# 启动服务器
python -m uvicorn apps.main:app --host 127.0.0.1 --port 8008 &

# 等待启动
sleep 5

# 测试API
curl -s "http://127.0.0.1:8008/api/v2/space/types" > /tmp/api_test.json

# 检查结果
if [ -s /tmp/api_test.json ]; then
    echo "✓ API启动成功"
    cat /tmp/api_test.json | python3 -m json.tool | head -20
else
    echo "✗ API启动失败"
    ps aux | grep uvicorn
fi