#!/bin/bash
# 用户认证流程完整测试脚本
# 测试从登录到用户管理页面的完整流程

set -e

API_BASE="http://127.0.0.1:8008"
LOGIN_URL="$API_BASE/api/v1/system/auth/login"
USERS_URL="$API_BASE/api/v1/system/users"
STATS_URL="$API_BASE/api/v1/system/users/stats/overview"

echo "========================================"
echo "  用户认证流程完整测试"
echo "========================================"

echo ""
echo "[1] 测试登录API"
echo "    URL: $LOGIN_URL"
echo "    参数: username=admin, password=admin123"

LOGIN_RESPONSE=$(curl -sX POST "$LOGIN_URL" \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}')

echo ""
echo "登录响应:"
echo "$LOGIN_RESPONSE" | python3 -m json.tool

TOKEN=$(echo "$LOGIN_RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin).get('access_token', ''))")

if [ -z "$TOKEN" ]; then
    echo "❌ 登录失败，无法获取token"
    exit 1
fi

echo ""
echo "✅ Token获取成功: ${TOKEN:0:50}..."

echo ""
echo "[2] 测试用户列表API（带token）"
echo "    URL: $USERS_URL"

USERS_RESPONSE=$(curl -s "$USERS_URL" \
  -H "Authorization: Bearer $TOKEN")

echo ""
echo "用户列表响应:"
echo "$USERS_RESPONSE" | python3 -m json.tool | head -30

if echo "$USERS_RESPONSE" | grep -q "items"; then
    echo ""
    echo "✅ 用户列表获取成功"
else
    echo ""
    echo "❌ 用户列表获取失败"
    echo "$USERS_RESPONSE"
    exit 1
fi

echo ""
echo "[3] 测试用户统计API（带token）"
echo "    URL: $STATS_URL"

STATS_RESPONSE=$(curl -s "$STATS_URL" \
  -H "Authorization: Bearer $TOKEN")

echo ""
echo "统计响应:"
echo "$STATS_RESPONSE" | python3 -m json.tool

if echo "$STATS_RESPONSE" | grep -q "total"; then
    echo ""
    echo "✅ 用户统计获取成功"
else
    echo ""
    echo "❌ 用户统计获取失败"
    exit 1
fi

echo ""
echo "[4] 测试无token访问（应返回401）"
echo "    URL: $USERS_URL"

NO_TOKEN_RESPONSE=$(curl -s "$USERS_URL")

echo ""
echo "无token响应:"
echo "$NO_TOKEN_RESPONSE" | python3 -m json.tool

if echo "$NO_TOKEN_RESPONSE" | grep -q "未登录或登录已过期"; then
    echo ""
    echo "✅ 无token访问正确返回401错误"
else
    echo ""
    echo "❌ 无token访问未正确返回401错误"
    exit 1
fi

echo ""
echo "[5] 测试无效token访问（应返回401）"
INVALID_TOKEN_RESPONSE=$(curl -s "$USERS_URL" \
  -H "Authorization: Bearer invalid_token_12345")

echo ""
echo "无效token响应:"
echo "$INVALID_TOKEN_RESPONSE" | python3 -m json.tool

if echo "$INVALID_TOKEN_RESPONSE" | grep -q "未登录或登录已过期"; then
    echo ""
    echo "✅ 无效token访问正确返回401错误"
else
    echo ""
    echo "❌ 无效token访问未正确返回401错误"
    exit 1
fi

echo ""
echo "[6] 测试登录页面HTML"
LOGIN_PAGE_RESPONSE=$(curl -sI "$API_BASE/portal/admin/login.html")

if echo "$LOGIN_PAGE_RESPONSE" | grep -q "200 OK"; then
    echo "✅ 登录页面可访问"
else
    echo "❌ 登录页面无法访问"
    exit 1
fi

echo ""
echo "[7] 测试用户管理页面HTML"
USERS_PAGE_RESPONSE=$(curl -sI "$API_BASE/portal/admin/users.html")

if echo "$USERS_PAGE_RESPONSE" | grep -q "200 OK"; then
    echo "✅ 用户管理页面可访问"
else
    echo "❌ 用户管理页面无法访问"
    exit 1
fi

echo ""
echo "[8] 测试API配置文件"
API_CONFIG_RESPONSE=$(curl -sI "$API_BASE/shared/utils/api-config.js")

if echo "$API_CONFIG_RESPONSE" | grep -q "200 OK"; then
    echo "✅ API配置文件可访问"
else
    echo "❌ API配置文件无法访问"
    exit 1
fi

echo ""
echo "========================================"
echo "  所有测试通过 ✅"
echo "========================================"
echo ""
echo "测试摘要:"
echo "  - 登录API正常"
echo "  - Token生成正常"
echo "  - 用户API认证正常"
echo "  - 无token访问返回401"
echo "  - 无效token访问返回401"
echo "  - 登录页面可访问"
echo "  - 用户管理页面可访问"
echo "  - API配置文件可访问"
echo ""
echo "请打开浏览器访问: http://127.0.0.1:8008/portal/admin/login.html"
echo "使用以下账号登录:"
echo "  用户名: admin"
echo "  密码: admin123"
echo ""
echo "登录成功后，页面应该跳转到首页或用户管理页面"
echo "用户管理页面应该能够正常显示用户列表"