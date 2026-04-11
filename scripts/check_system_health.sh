#!/bin/bash

echo "=========================================="
echo "Portal系统健康检查"
echo "=========================================="
echo ""
echo "检查时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# 检查服务器状态
echo "=== 服务器状态 ==="
if lsof -i :8000 | grep -q LISTEN; then
    echo "✅ 服务器运行在端口8000"
    pid=$(lsof -i :8000 | grep LISTEN | awk '{print $2}' | head -1)
    echo "   进程PID: $pid"
else
    echo "❌ 服务器未运行"
    echo ""
    echo "启动命令:"
    echo "  python -m uvicorn apps.main:app --host 0.0.0.0 --port 8000 --reload"
    exit 1
fi

echo ""

# 检查健康状态
echo "=== API健康检查 ==="
health=$(curl -s http://127.0.0.1:8000/health)
if [ $? -eq 0 ]; then
    echo "✅ API健康状态正常"
    echo "   响应: $health"
else
    echo "❌ API健康检查失败"
    exit 1
fi

echo ""

# 检查核心API
echo "=== 核心API检查 ==="

apis=(
    "api/v1/products"
    "api/v1/admin/product-categories"
    "api/v1/offices"
)

all_ok=true
for api in "${apis[@]}"; do
    status=$(curl -s -o /dev/null -w "%{http_code}" "http://127.0.0.1:8000/$api")
    if [ "$status" = "200" ]; then
        echo "✅ $api: OK"
    else
        echo "❌ $api: $status"
        all_ok=false
    fi
done

echo ""

# 检查Portal页面
echo "=== Portal页面检查 ==="

pages=(
    "portal/index.html"
    "portal/admin/water/products.html"
    "portal/admin/offices.html"
    "portal/admin/users.html"
)

for page in "${pages[@]}"; do
    status=$(curl -s -o /dev/null -w "%{http_code}" "http://127.0.0.1:8000/$page")
    if [ "$status" = "200" ]; then
        echo "✅ $page: OK"
    else
        echo "❌ $page: $status"
        all_ok=false
    fi
done

echo ""

if [ "$all_ok" = true ]; then
    echo "=========================================="
    echo "✅ 系统健康状态：优秀"
    echo "=========================================="
    echo ""
    echo "Portal访问地址:"
    echo "  http://127.0.0.1:8000/portal/index.html"
    echo ""
    exit 0
else
    echo "=========================================="
    echo "⚠️  系统健康状态：发现问题"
    echo "=========================================="
    exit 1
fi

