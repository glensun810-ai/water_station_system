#!/bin/bash
# 快速修复404问题

echo "======================================================================"
echo "  修复404问题 - 重新部署Portal前端"
echo "======================================================================"

# 1. 创建portal目录
mkdir -p /var/www/jhw-ai/portal
mkdir -p /var/www/jhw-ai/portal/assets/css
mkdir -p /var/www/jhw-ai/portal/assets/js
mkdir -p /var/www/jhw-ai/portal/components

# 2. 检查portal文件
if [ ! -f "/var/www/jhw-ai/portal/index.html" ]; then
    echo "❌ Portal首页不存在，正在从项目复制..."
    
    # 检查当前目录是否有portal
    if [ -d "./portal" ]; then
        cp -r portal/* /var/www/jhw-ai/portal/
        echo "✓ Portal文件已复制"
    else
        echo "当前目录没有portal文件，请先克隆项目代码"
        echo "执行: cd /var/www/jhw-ai && git pull origin feature/refactor-cleanup"
        exit 1
    fi
fi

# 3. 设置权限
chmod -R 755 /var/www/jhw-ai/portal/
chown -R root:root /var/www/jhw-ai/portal/

echo "✓ Portal文件权限已设置"

# 4. 验证文件
ls -lh /var/www/jhw-ai/portal/ | head -10

# 5. 测试访问
echo ""
echo "测试Nginx访问..."
curl -I http://127.0.0.1/portal/index.html 2>&1 | head -5

echo ""
echo "======================================================================"
echo "修复完成！请测试访问："
echo "  http://120.76.156.83/portal/index.html"
echo "======================================================================"