#!/bin/bash
# Portal页面API测试脚本

echo "================================================"
echo "Portal页面API测试"
echo "================================================"

BASE_URL="http://127.0.0.1:8008"

echo ""
echo "1. 测试健康检查"
curl -s "$BASE_URL/health" | python3 -m json.tool

echo ""
echo "2. 测试水站产品列表（公开API）"
curl -s "$BASE_URL/api/v1/water/products" | python3 -m json.tool | head -10

echo ""
echo "3. 测试系统办公室列表（需要认证）"
echo "状态码: $(curl -s -o /dev/null -w "%{http_code}" $BASE_URL/api/v1/system/offices)"

echo ""
echo "4. 测试水站统计API（需要认证）"
echo "状态码: $(curl -s -o /dev/null -w "%{http_code}" $BASE_URL/api/v1/water/stats/today)"

echo ""
echo "5. 测试会议室统计API（需要认证）"
echo "状态码: $(curl -s -o /dev/null -w "%{http_code}" $BASE_URL/api/v1/meeting/stats/today)"

echo ""
echo "================================================"
echo "测试结果说明："
echo "- 200: API正常工作"
echo "- 401: API存在，需要认证"
echo "- 404: API不存在（问题）"
echo "================================================"