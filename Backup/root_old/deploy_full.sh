#!/bin/bash
# ============================================
# 完整部署脚本 - 包含Portal首页和真实数据
# ============================================

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
RED='\033[0;31m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[✅ OK]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[⚠️ WARN]${NC} $1"; }
log_error() { echo -e "${RED}[❌ ERROR]${NC} $1"; }
log_step() { echo -e "${CYAN}[STEP]${NC} $1"; }

# 配置
SERVER_IP="120.76.156.83"
DOMAIN="jhw-ai.com"
DEPLOY_DIR="/var/www/${DOMAIN}"
BACKUP_DIR="/backup/waterms"
LOG_DIR="/var/log/waterms"
API_PORT=8000

echo -e "${BLUE}"
echo "╔══════════════════════════════════════════════════════╗"
echo "║   完整部署脚本 - Portal首页+真实数据                 ║"
echo "╚══════════════════════════════════════════════════════╝"
echo -e "${NC}"
echo "部署时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# ========================================
# 步骤1: 创建目录
# ========================================
log_step "【步骤1/10】创建目录结构..."
mkdir -p "${DEPLOY_DIR}/"{backend,portal,water,water-admin,meeting,meeting-admin,ssl}
mkdir -p "${BACKUP_DIR}/database"
mkdir -p "${LOG_DIR}"
log_success "目录创建完成"
echo ""

# ========================================
# 步骤2: 部署Portal首页
# ========================================
log_step "【步骤2/10】部署Portal首页..."

if [ -d "/root/project/portal" ]; then
    cp -r /root/project/portal/* "${DEPLOY_DIR}/portal/"
    log_success "Portal首页已部署"
else
    log_warning "未找到Portal目录"
fi
echo ""

# ========================================
# 步骤3: 部署后端代码和数据库
# ========================================
log_step "【步骤3/10】部署后端代码..."

# 部署后端代码
if [ -d "/root/project/Service_WaterManage/backend" ]; then
    cp -r /root/project/Service_WaterManage/backend/* "${DEPLOY_DIR}/backend/"
    log_success "后端代码已部署"
fi

# 恢复真实数据库
if [ -f "${BACKUP_DIR}/database/waterms_20260404_152737.db" ]; then
    log_info "恢复水站管理数据库..."
    cp "${BACKUP_DIR}/database/waterms_20260404_152737.db" "${DEPLOY_DIR}/backend/waterms.db"
    log_success "水站数据库已恢复 (264KB)"
fi

if [ -f "${BACKUP_DIR}/database/meeting_20260404_152737.db" ]; then
    log_info "恢复会议室管理数据库..."
    cp "${BACKUP_DIR}/database/meeting_20260404_152737.db" "${DEPLOY_DIR}/backend/meeting.db"
    log_success "会议室数据库已恢复 (216KB)"
fi
echo ""

# ========================================
# 步骤4: 安装Python依赖
# ========================================
log_step "【步骤4/10】安装Python依赖..."
cd "${DEPLOY_DIR}/backend"

if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi

source .venv/bin/activate
pip install --upgrade pip -q
pip install -r requirements.txt -q 2>/dev/null || pip install -r requirements.txt
deactivate
cd - > /dev/null
log_success "Python依赖安装完成"
echo ""

# ========================================
# 步骤5: 部署水站管理前端
# ========================================
log_step "【步骤5/10】部署水站管理前端..."

if [ -d "/root/project/Service_WaterManage/frontend" ]; then
    cp -r /root/project/Service_WaterManage/frontend/* "${DEPLOY_DIR}/water/"
    
    if [ -f "${DEPLOY_DIR}/water/admin.html" ]; then
        cp "${DEPLOY_DIR}/water/admin.html" "${DEPLOY_DIR}/water-admin/admin.html"
    fi
    log_success "水站管理前端已部署"
fi
echo ""

# ========================================
# 步骤6: 部署会议室管理前端
# ========================================
log_step "【步骤6/10】部署会议室管理前端..."

if [ -d "/root/project/Service_MeetingRoom/frontend" ]; then
    cp -r /root/project/Service_MeetingRoom/frontend/* "${DEPLOY_DIR}/meeting/"
    
    if [ -f "${DEPLOY_DIR}/meeting/admin.html" ]; then
        cp "${DEPLOY_DIR}/meeting/admin.html" "${DEPLOY_DIR}/meeting-admin/admin.html"
    fi
    log_success "会议室管理前端已部署"
fi
echo ""

# ========================================
# 步骤7: 检查SSL证书
# ========================================
log_step "【步骤7/10】检查SSL证书..."

if [ -f "${DEPLOY_DIR}/ssl/jhw-ai.com.pem" ] && [ -f "${DEPLOY_DIR}/ssl/jhw-ai.com.key" ]; then
    chmod 644 "${DEPLOY_DIR}/ssl/jhw-ai.com.pem"
    chmod 600 "${DEPLOY_DIR}/ssl/jhw-ai.com.key"
    SSL_ENABLED=true
    log_success "SSL证书已配置"
else
    SSL_ENABLED=false
    log_warning "使用HTTP部署"
fi
echo ""

# ========================================
# 步骤8: 配置Nginx
# ========================================
log_step "【步骤8/10】配置Nginx..."

if [ "$SSL_ENABLED" = true ]; then
    cat > /etc/nginx/conf.d/jhw-ai.conf << 'EOF'
# HTTP重定向到HTTPS
server {
    listen 80;
    server_name jhw-ai.com www.jhw-ai.com 120.76.156.83;
    return 301 https://$server_name$request_uri;
}

# HTTPS主服务器
server {
    listen 443 ssl http2;
    server_name jhw-ai.com www.jhw-ai.com;
    
    ssl_certificate /var/www/jhw-ai.com/ssl/jhw-ai.com.pem;
    ssl_certificate_key /var/www/jhw-ai.com/ssl/jhw-ai.com.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    
    # 开启gzip压缩
    gzip on;
    gzip_vary on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml;
    
    # Portal首页 - 默认访问
    location = / {
        root /var/www/jhw-ai.com/portal;
        index index.html;
    }
    
    location /portal/ {
        alias /var/www/jhw-ai.com/portal/;
        index index.html;
    }
    
    # 水站管理
    location /water/ {
        alias /var/www/jhw-ai.com/water/;
        index index.html;
    }
    
    location /water-admin/ {
        alias /var/www/jhw-ai.com/water-admin/;
        index admin.html;
    }
    
    # 会议室管理
    location /meeting/ {
        alias /var/www/jhw-ai.com/meeting/;
        index index.html;
    }
    
    location /meeting-admin/ {
        alias /var/www/jhw-ai.com/meeting-admin/;
        index admin.html;
    }
    
    # API代理
    location /api/ {
        proxy_pass http://127.0.0.1:8000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF
else
    cat > /etc/nginx/conf.d/jhw-ai.conf << 'EOF'
server {
    listen 80;
    server_name jhw-ai.com www.jhw-ai.com 120.76.156.83;
    
    # 开启gzip压缩
    gzip on;
    gzip_vary on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml;
    
    # Portal首页 - 默认访问
    location = / {
        root /var/www/jhw-ai.com/portal;
        index index.html;
    }
    
    location /portal/ {
        alias /var/www/jhw-ai.com/portal/;
        index index.html;
    }
    
    # 水站管理
    location /water/ {
        alias /var/www/jhw-ai.com/water/;
        index index.html;
    }
    
    location /water-admin/ {
        alias /var/www/jhw-ai.com/water-admin/;
        index admin.html;
    }
    
    # 会议室管理
    location /meeting/ {
        alias /var/www/jhw-ai.com/meeting/;
        index index.html;
    }
    
    location /meeting-admin/ {
        alias /var/www/jhw-ai.com/meeting-admin/;
        index admin.html;
    }
    
    # API代理
    location /api/ {
        proxy_pass http://127.0.0.1:8000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
EOF
fi

# 测试nginx配置
if nginx -t 2>/dev/null; then
    log_success "Nginx配置完成"
else
    log_error "Nginx配置错误"
    nginx -t
    exit 1
fi
echo ""

# ========================================
# 步骤9: 配置系统服务
# ========================================
log_step "【步骤9/10】配置系统服务..."

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
log_success "系统服务配置完成"
echo ""

# ========================================
# 步骤10: 启动服务
# ========================================
log_step "【步骤10/10】启动服务..."

# 启动API服务
log_info "启动API服务..."
systemctl start waterms
sleep 3

# 启动Nginx
log_info "启动Nginx服务..."
systemctl start nginx 2>/dev/null || systemctl reload nginx
systemctl enable nginx

# 验证API服务
if curl -s http://127.0.0.1:${API_PORT}/api/health 2>/dev/null | grep -q "healthy"; then
    log_success "API服务启动成功"
else
    log_warning "API服务可能未完全启动"
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
echo "  首页(Portal): http://${SERVER_IP}/"
echo "  水站管理: http://${SERVER_IP}/water/"
echo "  管理后台: http://${SERVER_IP}/water-admin/admin.html"
echo "  会议室: http://${SERVER_IP}/meeting/"
echo ""
echo -e "${CYAN}【测试账号】${NC}"
echo "  用户名: admin"
echo "  密码: admin123"
echo ""
echo -e "${CYAN}【数据库信息】${NC}"
echo "  水站数据库: $(du -h ${DEPLOY_DIR}/backend/waterms.db 2>/dev/null | cut -f1 || echo '未找到')"
echo "  会议室数据库: $(du -h ${DEPLOY_DIR}/backend/meeting.db 2>/dev/null | cut -f1 || echo '未找到')"
echo ""
echo -e "${CYAN}【服务管理】${NC}"
echo "  查看API状态: systemctl status waterms"
echo "  查看API日志: tail -f ${LOG_DIR}/waterms.log"
echo "  重启API服务: systemctl restart waterms"
echo ""
echo -e "${GREEN}部署完成时间: $(date '+%Y-%m-%d %H:%M:%S')${NC}"
echo ""
