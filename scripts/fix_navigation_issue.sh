#!/bin/bash

echo "=========================================="
echo "点击空间服务跳转登录页问题 - 自动修复脚本"
echo "=========================================="
echo ""

echo "步骤1: 重启服务器（确保最新代码生效）"
killall uvicorn 2>/dev/null
sleep 2
cd /Users/sgl/PycharmProjects/AIchanyejiqun
python3 -m uvicorn apps.main:app --host 127.0.0.1 --port 8008 > /tmp/server_restart.log 2>&1 &
sleep 3
echo "✅ 服务器已重启"

echo ""
echo "步骤2: 验证服务器运行"
health=$(curl -s http://127.0.0.1:8008/health)
if [[ "$health" == *"healthy"* ]]; then
    echo "✅ 服务器运行正常"
else
    echo "❌ 服务器启动失败"
    exit 1
fi

echo ""
echo "步骤3: 验证登录功能"
login_response=$(curl -s -X POST http://127.0.0.1:8008/api/v1/system/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}')

if [[ "$login_response" == *"access_token"* ]]; then
    echo "✅ 登录功能正常"
else
    echo "❌ 登录功能异常"
    echo "响应: $login_response"
    exit 1
fi

echo ""
echo "=========================================="
echo "✅ 服务器已重启，代码已生效"
echo "=========================================="
echo ""
echo "⚠️  重要提示：您还需要执行以下操作："
echo ""
echo "1. 清除浏览器缓存"
echo "   Windows/Linux: Ctrl+Shift+Delete"
echo "   Mac: Cmd+Shift+Delete"
echo ""
echo "2. 清除localStorage"
echo "   打开开发者工具（F12）"
echo "   Application -> Local Storage -> http://127.0.0.1:8008"
echo "   右键 -> Clear"
echo ""
echo "3. 强制刷新页面"
echo "   Windows/Linux: Ctrl+F5"
echo "   Mac: Cmd+Shift+R"
echo ""
echo "4. 重新登录"
echo "   用户名: admin"
echo "   密码: admin123"
echo ""
echo "5. 点击'空间服务-预约'"
echo "   应该跳转到: http://127.0.0.1:8008/space-frontend/index.html"
echo "   无需重新登录 ✅"
echo ""
echo "=========================================="

# 创建验证脚本
echo "创建localStorage验证脚本..."
cat > /tmp/verify_localStorage.js << 'EOF'
console.log('=== localStorage验证 ===');
console.log('token:', localStorage.getItem('token') ? '存在' : '不存在');
const userInfo = JSON.parse(localStorage.getItem('userInfo') || '{}');
console.log('userInfo:', userInfo);
console.log('userInfo.id:', userInfo.id);  // 应该是1，不是null
console.log('');
if (userInfo.id) {
    console.log('✅ userInfo.id存在，应该可以正常访问');
} else {
    console.log('❌ userInfo.id为null，需要重新登录');
}
EOF

echo "验证脚本已创建: /tmp/verify_localStorage.js"
echo "在浏览器控制台执行此脚本验证localStorage"