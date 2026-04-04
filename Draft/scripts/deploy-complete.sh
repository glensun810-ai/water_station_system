#!/bin/bash
# 完整部署脚本 - 智能水站管理系统
# 在服务器上直接执行: bash deploy-complete.sh

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  智能水站管理系统 - 完整部署${NC}"
echo -e "${BLUE}========================================${NC}"

# 1. 检查并安装必要软件
echo -e "\n${YELLOW}[1/8] 检查系统环境...${NC}"
if ! command -v nginx &> /dev/null; then
    echo -e "${RED}Nginx未安装，正在安装...${NC}"
    yum install -y nginx || apt-get install -y nginx
fi

# 启动必要服务
echo "启动SSH和Nginx服务..."
systemctl start sshd 2>/dev/null || true
systemctl enable sshd 2>/dev/null || true
systemctl start nginx 2>/dev/null || true
systemctl enable nginx 2>/dev/null || true

# 2. 创建目录结构
echo -e "\n${YELLOW}[2/8] 创建目录结构...${NC}"
mkdir -p /var/www/jhw-ai.com/{water,water-admin}
mkdir -p /var/log
mkdir -p /backup/waterms/database

# 3. 备份数据库（如果存在）
echo -e "\n${YELLOW}[3/8] 备份数据库...${NC}"
if [ -f "/var/www/jhw-ai.com/backend/waterms.db" ]; then
    DATE=$(date +%Y%m%d_%H%M%S)
    cp /var/www/jhw-ai.com/backend/waterms.db /backup/waterms/database/waterms_${DATE}.db
    echo -e "${GREEN}✓ 数据库已备份: waterms_${DATE}.db${NC}"
fi

# 4. 查找后端代码位置
echo -e "\n${YELLOW}[4/8] 定位代码目录...${NC}"
BACKEND_DIR=""
if [ -f "./waterms.db" ] || [ -f "./main.py" ]; then
    BACKEND_DIR=$(pwd)
    echo -e "${GREEN}✓ 找到后端代码: $BACKEND_DIR${NC}"
elif [ -d "/var/www/jhw-ai.com/backend" ]; then
    BACKEND_DIR="/var/www/jhw-ai.com/backend"
    echo -e "${GREEN}✓ 找到后端代码: $BACKEND_DIR${NC}"
else
    echo -e "${RED}✗ 未找到后端代码，请确认代码位置${NC}"
    echo "当前目录: $(pwd)"
    echo "目录内容:"
    ls -la
    exit 1
fi

# 5. 复制前端文件
echo -e "\n${YELLOW}[5/8] 部署前端文件...${NC}"
FRONTEND_DIR=""
# 查找frontend目录
for dir in "../frontend" "./frontend" "/var/www/jhw-ai.com/frontend"; do
    if [ -d "$dir" ]; then
        FRONTEND_DIR="$dir"
        break
    fi
done

if [ -z "$FRONTEND_DIR" ]; then
    echo -e "${RED}✗ 未找到frontend目录${NC}"
    echo "请检查代码是否完整拉取"
    exit 1
fi

echo "复制前端文件到 /var/www/jhw-ai.com/water/ ..."
cp -r "$FRONTEND_DIR"/* /var/www/jhw-ai.com/water/
echo "复制前端文件到 /var/www/jhw-ai.com/water-admin/ ..."
cp -r "$FRONTEND_DIR"/* /var/www/jhw-ai.com/water-admin/

# 设置权限
chmod -R 755 /var/www/jhw-ai.com/water
chmod -R 755 /var/www/jhw-ai.com/water-admin
chown -R nginx:nginx /var/www/jhw-ai.com/ 2>/dev/null || chown -R www-data:www-data /var/www/jhw-ai.com/ 2>/dev/null || true

echo -e "${GREEN}✓ 前端文件部署完成${NC}"

# 6. 配置Nginx
echo -e "\n${YELLOW}[6/8] 配置Nginx...${NC}"

# 备份现有配置
if [ -f "/etc/nginx/conf.d/water.conf" ]; then
    cp /etc/nginx/conf.d/water.conf /etc/nginx/conf.d/water.conf.bak.$(date +%Y%m%d_%H%M%S)
fi

cat > /etc/nginx/conf.d/water.conf << 'EOF'
server {
    listen 80;
    server_name jhw-ai.com www.jhw-ai.com 120.76.156.83;
    
    # 访问日志
    access_log /var/log/nginx/water_access.log;
    error_log /var/log/nginx/water_error.log;
    
    # 前端静态文件 - 用户端
    location /water/ {
        alias /var/www/jhw-ai.com/water/;
        index index.html;
        try_files $uri $uri/ /water/index.html;
    }
    
    # 前端静态文件 - 管理后台
    location /water-admin/ {
        alias /var/www/jhw-ai.com/water-admin/;
        index admin.html;
        try_files $uri $uri/ /water-admin/admin.html;
    }
    
    # API反向代理
    location /api/ {
        proxy_pass http://127.0.0.1:8000/api/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-Host $host;
        proxy_set_header X-Forwarded-Port $server_port;
        
        # WebSocket支持
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # 超时配置
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # 健康检查
    location /health {
        proxy_pass http://127.0.0.1:8000/api/health;
        proxy_set_header Host $host;
    }
    
    # 根路径重定向
    location = / {
        return 301 /water/;
    }
}
EOF

# 测试Nginx配置
if nginx -t; then
    echo -e "${GREEN}✓ Nginx配置测试通过${NC}"
    nginx -s reload
    echo -e "${GREEN}✓ Nginx配置已重载${NC}"
else
    echo -e "${RED}✗ Nginx配置有误，请检查${NC}"
    exit 1
fi

# 7. 启动后端服务
echo -e "\n${YELLOW}[7/8] 启动后端服务...${NC}"
cd "$BACKEND_DIR"

# 检查Python虚拟环境
if [ -d "venv" ]; then
    echo "激活虚拟环境..."
    source venv/bin/activate
elif [ -d ".venv" ]; then
    echo "激活虚拟环境..."
    source .venv/bin/activate
fi

# 停止旧服务
echo "停止旧的后端服务..."
pkill -f "uvicorn.*8000" || true
sleep 2

# 启动新服务
echo "启动后端服务..."
nohup python -m uvicorn main:app --host 127.0.0.1 --port 8000 > /var/log/water-api.log 2>&1 &
BACKEND_PID=$!
echo $BACKEND_PID > /tmp/water-backend.pid

sleep 3

# 验证后端服务
if curl -s http://127.0.0.1:8000/api/health > /dev/null; then
    echo -e "${GREEN}✓ 后端服务启动成功 (PID: $BACKEND_PID)${NC}"
else
    echo -e "${RED}✗ 后端服务启动失败，查看日志:${NC}"
    tail -20 /var/log/water-api.log
    exit 1
fi

# 8. 最终验证
echo -e "\n${YELLOW}[8/8] 验证部署...${NC}"
echo ""

# 测试API
echo "测试API健康检查..."
if curl -s http://127.0.0.1:8000/api/health | grep -q "ok\|healthy\|success"; then
    echo -e "${GREEN}✓ API服务正常${NC}"
else
    echo -e "${YELLOW}⚠ API返回异常，但服务已启动${NC}"
fi

# 测试前端
echo "测试前端访问..."
if curl -s http://127.0.0.1/water/ | grep -q "html"; then
    echo -e "${GREEN}✓ 用户端前端正常${NC}"
else
    echo -e "${YELLOW}⚠ 用户端前端可能有问题${NC}"
fi

if curl -s http://127.0.0.1/water-admin/ | grep -q "html"; then
    echo -e "${GREEN}✓ 管理后台前端正常${NC}"
else
    echo -e "${YELLOW}⚠ 管理后台前端可能有问题${NC}"
fi

# 检查防火墙
echo ""
echo "检查防火墙..."
if command -v firewall-cmd &> /dev/null; then
    firewall-cmd --state &>/dev/null && {
        firewall-cmd --permanent --add-port=80/tcp 2>/dev/null || true
        firewall-cmd --permanent --add-port=443/tcp 2>/dev/null || true
        firewall-cmd --reload 2>/dev/null || true
        echo -e "${GREEN}✓ 防火墙已配置${NC}"
    }
fi

# 完成提示
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  🎉 部署完成！${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${BLUE}访问地址:${NC}"
echo "  用户端:    http://jhw-ai.com/water/"
echo "  管理后台:  http://jhw-ai.com/water-admin/admin.html"
echo "  或者IP:    http://120.76.156.83/water/"
echo ""
echo -e "${BLUE}测试账号:${NC}"
echo "  用户名: admin"
echo "  密码:   admin123"
echo ""
echo -e "${BLUE}日志位置:${NC}"
echo "  后端日志: /var/log/water-api.log"
echo "  Nginx日志: /var/log/nginx/water_access.log"
echo ""
echo -e "${YELLOW}注意事项:${NC}"
echo "  1. 确保阿里云安全组已开放 80 和 443 端口"
echo "  2. 确保域名 jhw-ai.com 已解析到 120.76.156.83"
echo "  3. 如需HTTPS，请配置SSL证书"
echo ""