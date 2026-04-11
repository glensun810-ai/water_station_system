#!/bin/bash
# Water前端页面访问测试

echo "========================================"
echo "Water前端页面访问测试"
echo "========================================"

BASE_URL="http://127.0.0.1:8008"

pages=(
    "/water/index.html"
    "/water/login.html"
    "/water/admin.html"
    "/water/admin-users.html"
    "/water/admin-settlements.html"
    "/water/bookings.html"
    "/water/user-balance.html"
    "/water/change-password.html"
)

echo ""
echo "测试页面访问状态："
echo ""

for page in "${pages[@]}"; do
    status=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL$page")
    
    if [ "$status" == "200" ]; then
        echo "✓ $page → $status"
    else
        echo "✗ $page → $status"
    fi
done

echo ""
echo "========================================"
echo "测试总结："
echo "- 200: 页面正常访问"
echo "- 404: 页面不存在"
echo "- 500: 服务器错误"
echo "========================================"

echo ""
echo "正确的访问路径："
echo "1. 水站首页: http://127.0.0.1:8008/water/index.html"
echo "2. 水站登录: http://127.0.0.1:8008/water/login.html"
echo "3. 水站管理后台: http://127.0.0.1:8008/water/admin.html"
echo "4. Portal水站: http://127.0.0.1:8008/portal/water/index.html"
echo ""