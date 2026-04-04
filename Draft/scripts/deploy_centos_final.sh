#!/bin/bash
# ============================================
# CentOS一键部署脚本 - 最终修复版
# ============================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
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
echo "║   AI产业集群服务管理平台 - CentOS最终版              ║"
echo "╚══════════════════════════════════════════════════════╝"
echo -e "${NC}"
echo "部署时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo "服务器: ${SERVER_IP}"
echo "域名: ${DOMAIN}"
echo ""

# ========================================
# 步骤1: 环境检查与安装
# ========================================
log_step "【步骤1/10】环境检查与安装..."

# 检查是否为root用户
if [ "$EUID" -ne 0 ]; then
    log_error "请使用root用户执行此脚本"
    exit 1
fi

# 检查Python
if ! command -v python3 &> /dev/null; then
    log_error "Python3 未安装"
    exit 1
fi
log_success "Python3 已安装: $(python3 --version)"

# 检查pip3
if ! command -v pip3 &> /dev/null; then
    log_warning "pip3 未安装，正在安装..."
    yum install -y python3-pip
fi
log_success "pip3 已安装"

# 检查sqlite3
if ! command -v sqlite3 &> /dev/null; then
    log_warning "SQLite3 未安装，正在安装..."
    yum install -y sqlite
fi
log_success "SQLite3 已安装"

# 安装Nginx - 使用EPEL仓库
if ! command -v nginx &> /dev/null; then
    log_warning "Nginx 未安装，正在安装..."
    
    # 安装EPEL仓库
    log_info "安装EPEL仓库..."
    yum install -y epel-release
    
    # 安装nginx
    log_info "安装Nginx..."
    yum install -y nginx
    
    if [ $? -eq 0 ]; then
        log_success "Nginx 安装成功"
    else
        log_warning "Nginx 安装失败，尝试使用官方源..."
        
        # 添加nginx官方源
        cat > /etc/yum.repos.d/nginx.repo << 'EOF'
[nginx-stable]
name=nginx stable repo
baseurl=http://nginx.org/packages/centos/$releasever/$basearch/
gpgcheck=1
enabled=1
gpgkey=https://nginx.org/keys/nginx_signing.key
module_hotfixes=true
EOF
        
        yum install -y nginx
        
        if [ $? -eq 0 ]; then
            log_success "Nginx 安装成功"
        else
            log_error "Nginx 安装失败，请手动安装"
            log_info "手动安装命令: yum install -y epel-release && yum install -y nginx"
            exit 1
        fi
    fi
else
    log_success "Nginx 已安装"
fi

echo ""

# ========================================
# 步骤2: 创建目录结构
# ========================================
log_step "【步骤2/10】创建目录结构..."

mkdir -p "${DEPLOY_DIR}/backend"
mkdir -p "${DEPLOY_DIR}/water"
mkdir -p "${DEPLOY_DIR}/water-admin"
mkdir -p "${DEPLOY_DIR}/meeting"
mkdir -p "${DEPLOY_DIR}/meeting-admin"
mkdir -p "${DEPLOY_DIR}/ssl"
mkdir -p "${BACKUP_DIR}/database"
mkdir -p "${LOG_DIR}"
mkdir -p "/etc/nginx/conf.d"

log_success "目录创建完成"
echo ""

# ========================================
# 步骤3: 检查SSL证书
# ========================================
log_step "【步骤3/10】检查SSL证书..."

if [ -f "${DEPLOY_DIR}/ssl/jhw-ai.com.pem" ] && [ -f "${DEPLOY_DIR}/ssl/jhw-ai.com.key" ]; then
    log_success "SSL证书文件已存在"
    chmod 644 "${DEPLOY_DIR}/ssl/jhw-ai.com.pem"
    chmod 600 "${DEPLOY_DIR}/ssl/jhw-ai.com.key"
    SSL_ENABLED=true
else
    log_warning "SSL证书文件不存在，将使用HTTP部署"
    SSL_ENABLED=false
fi
echo ""

# ========================================
# 步骤4: 检查数据库备份
# ========================================
log_step "【步骤4/10】检查数据库备份..."

if [ -f "${BACKUP_DIR}/database/waterms_20260404_152737.db" ]; then
    log_success "数据库备份文件已存在"
    DB_BACKUP_EXISTS=true
else
    log_warning "数据库备份文件不存在，将使用空数据库"
    DB_BACKUP_EXISTS=false
fi
echo ""

# ========================================
# 步骤5: 部署后端代码
# ========================================
log_step "【步骤5/10】部署后端代码..."

# 查找代码目录
CODE_FOUND=false
CODE_DIRS=(
    "/root/project/Service_WaterManage/backend"
    "Service_WaterManage/backend"
    "./Service_WaterManage/backend"
    "/root/Service_WaterManage/backend"
)

for dir in "${CODE_DIRS[@]}"; do
    if [ -d "$dir" ]; then
        log_info "找到代码目录: $dir"
        cp -r "$dir"/* "${DEPLOY_DIR}/backend/"
        CODE_FOUND=true
        break
    fi
done

if [ "$CODE_FOUND" = false ]; then
    log_error "未找到后端代码目录"
    log_info "请检查以下位置："
    for dir in "${CODE_DIRS[@]}"; do
        log_info "  - $dir"
    done
    exit 1
fi

# 恢复数据库
if [ "$DB_BACKUP_EXISTS" = true ]; then
    log_info "恢复数据库..."
    cp "${BACKUP_DIR}/database/waterms_20260404_152737.db" "${DEPLOY_DIR}/backend/waterms.db"
    
    if [ -f "${BACKUP_DIR}/database/meeting_20260404_152737.db" ]; then
        cp "${BACKUP_DIR}/database/meeting_20260404_152737.db" "${DEPLOY_DIR}/backend/meeting.db"
    fi
    log_success "数据库恢复完成"
fi

log_success "后端代码部署完成"
echo ""

# ========================================
# 步骤6: 安装Python依赖
# ========================================
log_step "【步骤6/10】安装Python依赖..."

cd "${DEPLOY_DIR}/backend"

# 创建虚拟环境
if [ ! -d ".venv" ]; then
    log_info "创建Python虚拟环境..."
    python3 -m venv .venv
fi

# 激活虚拟环境并安装依赖
source .venv/bin/activate

if [ -f "requirements.txt" ]; then
    log_info "安装Python依赖包..."
    pip install --upgrade pip -q 2>/dev/null || pip install --upgrade pip
    pip install -r requirements.txt -q 2>/dev/null || pip install -r requirements.txt
    log_success "Python依赖安装完成"
else
    log_error "requirements.txt 不存在"
    exit 1
fi

deactivate
cd - > /dev/null
echo ""

# ========================================
# 步骤7: 部署前端代码
# ========================================
log_step "【步骤7/10】部署前端代码..."

# 查找前端代码
FRONTEND_DIRS=(
    "/root/project/Service_WaterManage/frontend"
    "Service_WaterManage/frontend"
    "./Service_WaterManage/frontend"
    "/root/Service_WaterManage/frontend"
)

for dir in "${FRONTEND_DIRS[@]}"; do
    if [ -d "$dir" ]; then
        log_info "从 $dir 复制前端代码..."
        cp -r "$dir"/* "${DEPLOY_DIR}/water/"
        
        if [ -f "${DEPLOY_DIR}/water/admin.html" ]; then
            mkdir -p "${DEPLOY_DIR}/water-admin"
            cp "${DEPLOY_DIR}/water/admin.html" "${DEPLOY_DIR}/water-admin/admin.html"
            log_success "水站管理后台部署完成"
        fi
        break
    fi
done

# 会议室前端
MEETING_DIRS=(
    "/root/project/Service_MeetingRoom/frontend"
    "Service_MeetingRoom/frontend"
    "./Service_MeetingRoom/frontend"
    "/root/Service_MeetingRoom/frontend"
)

for dir in "${MEETING_DIRS[@]}"; do
    if [ -d "$dir" ]; then
        log_info "从 $dir 复制会议室前端..."
        cp -r "$dir"/* "${DEPLOY_DIR}/meeting/"
        
        if [ -f "${DEPLOY_DIR}/meeting/admin.html" ]; then
            mkdir -p "${DEPLOY_DIR}/meeting-admin"
            cp "${DEPLOY_DIR}/meeting/admin.html" "${DEPLOY_DIR}/meeting-admin/admin.html"
            log_success "会议室管理后台部署完成"
        fi
        break
    fi
done

log_success "前端代码部署完成"
echo ""

# ========================================
# 步骤8: 配置Nginx
# ========================================
log_step "【步骤8/10】配置Nginx..."

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
    ssl_ciphers HIGH:!aNULL:!MD5;
    
    gzip on;
    gzip_vary on;
    gzip_types text/plain text/css application/json application/javascript text/xml;
    
    location /water/ {
        alias /var/www/jhw-ai.com/water/;
        index index.html;
        try_files $uri $uri/ /water/index.html;
    }
    
    location /water-admin/ {
        alias /var/www/jhw-ai.com/water-admin/;
        index admin.html;
        try_files $uri $uri/ /water-admin/admin.html;
    }
    
    location /meeting/ {
        alias /var/www/jhw-ai.com/meeting/;
        index index.html;
        try_files $uri $uri/ /meeting/index.html;
    }
    
    location /meeting-admin/ {
        alias /var/www/jhw-ai.com/meeting-admin/;
        index admin.html;
        try_files $uri $uri/ /meeting-admin/admin.html;
    }
    
    location /api/ {
        proxy_pass http://127.0.0.1:8000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
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
        try_files $uri $uri/ /water/index.html;
    }
    
    location /water-admin/ {
        alias /var/www/jhw-ai.com/water-admin/;
        index admin.html;
        try_files $uri $uri/ /water-admin/admin.html;
    }
    
    location /meeting/ {
        alias /var/www/jhw-ai.com/meeting/;
        index index.html;
        try_files $uri $uri/ /meeting/index.html;
    }
    
    location /meeting-admin/ {
        alias /var/www/jhw-ai.com/meeting-admin/;
        index admin.html;
        try_files $uri $uri/ /meeting-admin/admin.html;
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

# 测试并重载Nginx
if nginx -t 2>/dev/null; then
    log_success "Nginx配置验证通过"
else
    log_error "Nginx配置验证失败"
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
Environment="PATH=${DEPLOY_DIR}/backend/.venv/bin"
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

log_info "启动API服务..."
systemctl start waterms
sleep 3

log_info "启动Nginx服务..."
systemctl start nginx
systemctl enable nginx

# 验证API服务
log_info "验证API服务..."
if curl -s http://127.0.0.1:${API_PORT}/api/health 2>/dev/null | grep -q "healthy"; then
    log_success "API服务启动成功"
else
    log_warning "API服务可能未完全启动"
    log_info "查看日志: tail -f ${LOG_DIR}/waterms.log"
fi

# 重载Nginx
nginx -s reload 2>/dev/null || systemctl reload nginx

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
echo "  水站管理（用户端）: http://${SERVER_IP}/water/"
echo "  水站管理（管理后台）: http://${SERVER_IP}/water-admin/admin.html"
echo "  会议室预定（用户端）: http://${SERVER_IP}/meeting/"
echo "  会议室预定（管理后台）: http://${SERVER_IP}/meeting-admin/admin.html"
echo ""
echo -e "${CYAN}【测试账号】${NC}"
echo "  用户名: admin"
echo "  密码: admin123"
echo ""
echo -e "${CYAN}【服务管理】${NC}"
echo "  启动: systemctl start waterms"
echo "  停止: systemctl stop waterms"
echo "  状态: systemctl status waterms"
echo "  日志: tail -f ${LOG_DIR}/waterms.log"
echo ""
echo -e "${GREEN}部署完成时间: $(date '+%Y-%m-%d %H:%M:%S')${NC}"
echo ""
