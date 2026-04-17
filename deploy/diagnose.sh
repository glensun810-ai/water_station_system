#!/bin/bash
# 云服务器部署诊断脚本

echo "======================================================================"
echo "  AI产业集群系统 - 云服务器部署诊断"
echo "======================================================================"
echo ""

# 1. 检查部署目录
echo "[检查1] 验证部署目录是否存在..."
if [ -d "/var/www/jhw-ai" ]; then
    echo "✓ 部署目录存在: /var/www/jhw-ai"
    ls -lh /var/www/jhw-ai/ | head -20
else
    echo "❌ 部署目录不存在: /var/www/jhw-ai"
    echo "   需要先执行部署脚本"
    exit 1
fi

echo ""

# 2. 检查portal目录
echo "[检查2] 验证portal前端目录..."
if [ -d "/var/www/jhw-ai/portal" ]; then
    echo "✓ Portal目录存在"
    ls -lh /var/www/jhw-ai/portal/ | head -10
    if [ -f "/var/www/jhw-ai/portal/index.html" ]; then
        echo "✓ Portal首页文件存在: index.html"
    else
        echo "❌ Portal首页文件不存在: index.html"
    fi
else
    echo "❌ Portal目录不存在"
fi

echo ""

# 3. 检查API服务状态
echo "[检查3] 验证API服务状态..."
if systemctl is-active --quiet jhw-ai; then
    echo "✓ API服务运行中"
    systemctl status jhw-ai --no-pager | head -10
else
    echo "❌ API服务未运行"
    systemctl status jhw-ai --no-pager || echo "服务不存在"
fi

echo ""

# 4. 检查端口监听
echo "[检查4] 验证端口监听..."
if netstat -tlnp | grep -q ":8008"; then
    echo "✓ API端口8008已监听"
    netstat -tlnp | grep ":8008"
else
    echo "❌ API端口8008未监听"
fi

if netstat -tlnp | grep -q ":80"; then
    echo "✓ HTTP端口80已监听 (Nginx)"
    netstat -tlnp | grep ":80"
else
    echo "❌ HTTP端口80未监听"
fi

if netstat -tlnp | grep -q ":443"; then
    echo "✓ HTTPS端口443已监听 (Nginx)"
    netstat -tlnp | grep ":443"
else
    echo "⚠ HTTPS端口443未监听"
fi

echo ""

# 5. 检查Nginx配置
echo "[检查5] 验证Nginx配置..."
if [ -f "/etc/nginx/conf.d/jhw-ai.conf" ]; then
    echo "✓ Nginx配置文件存在"
    echo "配置内容:"
    cat /etc/nginx/conf.d/jhw-ai.conf | grep -E "location|alias|root" | head -20
else
    echo "❌ Nginx配置文件不存在"
    ls -lh /etc/nginx/conf.d/ || ls -lh /etc/nginx/sites-enabled/
fi

echo ""

# 6. 测试API服务
echo "[检查6] 测试API服务..."
API_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8008/health 2>/dev/null)
if [ "$API_RESPONSE" = "200" ]; then
    echo "✓ API服务健康检查通过 (状态码: 200)"
    curl -s http://127.0.0.1:8008/health | head -5
else
    echo "❌ API服务健康检查失败 (状态码: $API_RESPONSE)"
fi

echo ""

# 7. 检查文件权限
echo "[检查7] 验证文件权限..."
if [ -d "/var/www/jhw-ai/portal" ]; then
    ls -ld /var/www/jhw-ai/portal
    ls -l /var/www/jhw-ai/portal/index.html 2>/dev/null || echo "index.html不存在"
fi

echo ""
echo "======================================================================"
echo "  诊断完成"
echo "======================================================================"
echo ""
echo "如果发现问题，请检查以下常见原因："
echo "1. 部署脚本未执行 → 执行: sudo ./deploy/deploy-production.sh"
echo "2. Portal文件不存在 → 检查: ls -R /var/www/jhw-ai/portal/"
echo "3. Nginx路径配置错误 → 检查: cat /etc/nginx/conf.d/jhw-ai.conf"
echo "4. 文件权限问题 → 修复: chmod -R 755 /var/www/jhw-ai/portal/"
echo ""