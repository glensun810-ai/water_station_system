#!/bin/bash
# ============================================
# 一键部署脚本 - 最终优化版
# ============================================

set -e

# 颜色定义
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

# 配置
SERVER_IP="120.76.156.83"
DOMAIN="jhw-ai.com"
DEPLOY_DIR="/var/www/${DOMAIN}"
BACKUP_DIR="/backup/waterms"
LOG_DIR="/var/log/waterms"
API_PORT=8000

echo -e "${BLUE}"
echo "╔══════════════════════════════════════════════════════╗"
echo "║   一键部署脚本 - 最终优化版                          ║"
echo "╚══════════════════════════════════════════════════════╝"
echo -e "${NC}"

# ========================================
# 步骤1: 创建目录
# ========================================
echo -e "${CYAN}[步骤1/8] 创建目录...${NC}"
mkdir -p "${DEPLOY_DIR}/"{backend,water,water-admin,meeting,meeting-admin,ssl}
mkdir -p "${BACKUP_DIR}/database" "${LOG_DIR}"
echo -e "${GREEN}✅ 完成${NC}"
echo ""

# ========================================
# 步骤2: 检查数据库备份
# ========================================
echo -e "${CYAN}[步骤2/8] 检查数据库...${NC}"
if [ -f "${BACKUP_DIR}/database/waterms_20260404_152737.db" ]; then
    echo -e "${GREEN}✅ 数据库备份已找到${NC}"
else
    echo -e "${YELLOW}⚠️  未找到数据库备份${NC}"
fi
echo ""

# ========================================
# 步骤3: 部署后端代码
# ========================================
echo -e "${CYAN}[步骤3/8] 部署后端代码...${NC}"

# 查找代码
if [ -d "/root/project/Service_WaterManage/backend" ]; then
    cp -r /root/project/Service_WaterManage/backend/* "${DEPLOY_DIR}/backend/"
    echo -e "${GREEN}✅ 后端代码已复制${NC}"
else
    echo -e "${YELLOW}⚠️  未找到后端代码${NC}"
fi

# 恢复数据库
if [ -f "${BACKUP_DIR}/database/waterms_20260404_152737.db" ]; then
    cp "${BACKUP_DIR}/database/waterms_20260404_152737.db" "${DEPLOY_DIR}/backend/waterms.db"
    [ -f "${BACKUP_DIR}/database/meeting_20260404_152737.db" ] && \
        cp "${BACKUP_DIR}/database/meeting_20260404_152737.db" "${DEPLOY_DIR}/backend/meeting.db"
    echo -e "${GREEN}✅ 数据库已恢复${NC}"
fi
echo ""

# ========================================
# 步骤4: 安装Python依赖
# ========================================
echo -e "${CYAN}[步骤4/8] 安装Python依赖...${NC}"
cd "${DEPLOY_DIR}/backend"

[ ! -d .venv ] && python3 -m venv .venv

source .venv/bin/activate
pip install --upgrade pip -q
pip install -r requirements.txt -q 2>/dev/null || pip install -r requirements.txt
deactivate

cd - > /dev/null
echo -e "${GREEN}✅ Python依赖已安装${NC}"
echo ""

# ========================================
# 步骤5: 部署前端代码
# ========================================
echo -e "${CYAN}[步骤5/8] 部署前端代码...${NC}"

# 水站前端
if [ -d "/root/project/Service_WaterManage/frontend" ]; then
    cp -r /root/project/Service_WaterManage/frontend/* "${DEPLOY_DIR}/water/"
    [ -f "${DEPLOY_DIR}/water/admin.html" ] && \
        cp "${DEPLOY_DIR}/water/admin.html" "${DEPLOY_DIR}/water-admin/admin.html"
    echo -e "${GREEN}✅ 水站前端已部署${NC}"
fi

# 会议室前端
if [ -d "/root/project/Service_MeetingRoom/frontend" ]; then
    cp -r /root/project/Service_MeetingRoom/frontend/* "${DEPLOY_DIR}/meeting/"
    [ -f "${DEPLOY_DIR}/meeting/admin.html" ] && \
        cp "${DEPLOY_DIR}/meeting/admin.html" "${DEPLOY_DIR}/meeting-admin/admin.html"
    echo -e "${GREEN}✅ 会议室前端已部署${NC}"
fi
echo ""

# ========================================
# 步骤6: 配置Nginx
# ========================================
echo -e "${CYAN}[步骤6/8] 配置Nginx...${NC}"

# 检查SSL证书
if [ -f "${DEPLOY_DIR}/ssl/jhw-ai.com.pem" ] && [ -f "${DEPLOY_DIR}/ssl/jhw-ai.com.key" ]; then
    chmod 644 "${DEPLOY_DIR}/ssl/jhw-ai.com.pem"
    chmod 600 "${DEPLOY_DIR}/ssl/jhw-ai.com.key"
    SSL_ENABLED=true
    echo -e "${GREEN}✅ SSL证书已配置${NC}"
else
    SSL_ENABLED=false
    echo -e "${YELLOW}⚠️  未配置SSL，使用HTTP${NC}"
fi

# 生成Nginx配置
if [ "$SSL_ENABLED" = true ]; then
    cat > /etc/nginx/conf.d/jhw-ai.conf << 'EOF'
server {
    listen 80;
    server_name jhw-ai.com www.jhw-ai.com 120.76.156.83;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name jhw-ai.com www.jhw-ai.com;
    
    ssl_certificate /var/www/jhw-ai.com/ssl/jhw-ai.com.pem;
    ssl_certificate_key /var/www/jhw-ai.com/ssl/jhw-ai.com.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    
    gzip on;
    gzip_vary on;
    gzip_types text/plain text/css application/json application/javascript text/xml;
    
    location /water/ {
        alias /var/www/jhw-ai.com/water/;
        index index.html;
    }
    
    location /water-admin/ {
        alias /var/www/jhw-ai.com/water-admin/;
        index admin.html;
    }
    
    location /meeting/ {
        alias /var/www/jhw-ai.com/meeting/;
        index index.html;
    }
    
    location /meeting-admin/ {
        alias /var/www/jhw-ai.com/meeting-admin/;
        index admin.html;
    }
    
    location /api/ {
        proxy_pass http://127.0.0.1:8000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
    
    location = / {
        return 301 /water/;
    }
}
EOF
else
    cat > /etc/nginx/conf.d/jhw-ai.conf << 'EOF'
server {
    listen 80;
    server_name jhw-ai.com www.jhw-ai.com 120.76.156.83;
    
    gzip on;
    gzip_vary on;
    gzip_types text/plain text/css application/json application/javascript text/xml;
    
    location /water/ {
        alias /var/www/jhw-ai.com/water/;
        index index.html;
    }
    
    location /water-admin/ {
        alias /var/www/jhw-ai.com/water-admin/;
        index admin.html;
    }
    
    location /meeting/ {
        alias /var/www/jhw-ai.com/meeting/;
        index index.html;
    }
    
    location /meeting-admin/ {
        alias /var/www/jhw-ai.com/meeting-admin/;
        index admin.html;
    }
    
    location /api/ {
        proxy_pass http://127.0.0.1:8000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
    
    location = / {
        return 301 /water/;
    }
}
EOF
fi

nginx -t && echo -e "${GREEN}✅ Nginx配置完成${NC}"
echo ""

# ========================================
# 步骤7: 配置系统服务
# ========================================
echo -e "${CYAN}[步骤7/8] 配置系统服务...${NC}"

cat > /etc/systemd/system/waterms.service << EOF
[Unit]
Description=Water Management System API
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=${DEPLOY_DIR}/backend
ExecStart=${DEPLOY_DIR}/backend/.venv/bin/python -m uvicorn main:app --host 127.0.0.1 --port ${API_PORT}
Restart=always
RestartSec=5
StandardOutput=append:${LOG_DIR}/waterms.log
StandardError=append:${LOG_DIR}/waterms-error.log

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable waterms
echo -e "${GREEN}✅ 系统服务已配置${NC}"
echo ""

# ========================================
# 步骤8: 启动服务
# ========================================
echo -e "${CYAN}[步骤8/8] 启动服务...${NC}"

# 启动API服务
systemctl start waterms
sleep 3

# 启动/重载Nginx
systemctl start nginx 2>/dev/null || systemctl reload nginx

# 验证服务
if curl -s http://127.0.0.1:${API_PORT}/api/health 2>/dev/null | grep -q "healthy"; then
    echo -e "${GREEN}✅ API服务启动成功${NC}"
else
    echo -e "${YELLOW}⚠️  API服务可能未完全启动${NC}"
fi

echo ""

# ========================================
# 部署完成
# ========================================
echo -e "${GREEN}"
echo "╔══════════════════════════════════════════════════════╗"
echo "║          ✅ 部署完成！                               ║"
echo "╚══════════════════════════════════════════════════════╝"
echo -e "${NC}"
echo ""
echo -e "${CYAN}【访问地址】${NC}"
echo "  水站管理: http://${SERVER_IP}/water/"
echo "  管理后台: http://${SERVER_IP}/water-admin/admin.html"
echo "  会议室: http://${SERVER_IP}/meeting/"
echo ""
echo -e "${CYAN}【测试账号】${NC}"
echo "  用户名: admin"
echo "  密码: admin123"
echo ""
echo -e "${CYAN}【服务管理】${NC}"
echo "  查看API状态: systemctl status waterms"
echo "  查看API日志: tail -f ${LOG_DIR}/waterms.log"
echo "  重启API服务: systemctl restart waterms"
echo ""
