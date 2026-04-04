#!/bin/bash
# ============================================
# 智能部署脚本 - 自动检测并适配环境
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
echo "║   AI产业集群服务管理平台 - 智能部署版                ║"
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

# 检查Nginx - 多种方式检测
NGINX_INSTALLED=false

# 方法1: 检查nginx命令
if command -v nginx &> /dev/null; then
    NGINX_INSTALLED=true
    log_success "Nginx 已安装: $(nginx -v 2>&1)"
fi

# 方法2: 检查nginx可执行文件
if [ "$NGINX_INSTALLED" = false ] && [ -f "/usr/sbin/nginx" ]; then
    NGINX_INSTALLED=true
    log_success "Nginx 已安装在 /usr/sbin/nginx"
fi

# 方法3: 检查nginx服务
if [ "$NGINX_INSTALLED" = false ] && systemctl list-unit-files | grep -q nginx.service; then
    NGINX_INSTALLED=true
    log_success "Nginx 服务已存在"
fi

# 如果未安装，尝试安装
if [ "$NGINX_INSTALLED" = false ]; then
    log_warning "Nginx 未安装，正在尝试安装..."
    
    # 获取CentOS版本
    if [ -f /etc/redhat-release ]; then
        CENTOS_VERSION=$(cat /etc/redhat-release | grep -oE '[0-9]+' | head -1)
        log_info "检测到 CentOS 版本: $CENTOS_VERSION"
    else
        CENTOS_VERSION=8
    fi
    
    # 创建nginx仓库配置 - 根据版本选择
    if [ "$CENTOS_VERSION" -ge 8 ]; then
        # CentOS 8 使用 AppStream
        log_info "尝试从 AppStream 安装..."
        yum install -y nginx 2>/dev/null || {
            # 如果失败，尝试使用不同的baseurl
            log_info "AppStream 安装失败，尝试官方源..."
            
            cat > /etc/yum.repos.d/nginx.repo << 'EOF'
[nginx-stable]
name=nginx stable repo
baseurl=http://nginx.org/packages/centos/7/$basearch/
gpgcheck=0
enabled=1
EOF
            
            yum clean all
            yum makecache
            yum install -y nginx
        }
    else
        # CentOS 7
        log_info "使用nginx官方源..."
        cat > /etc/yum.repos.d/nginx.repo << 'EOF'
[nginx-stable]
name=nginx stable repo
baseurl=http://nginx.org/packages/centos/7/$basearch/
gpgcheck=0
enabled=1
EOF
        
        yum clean all
        yum makecache
        yum install -y nginx
    fi
    
    if [ $? -eq 0 ] && [ -f "/usr/sbin/nginx" ]; then
        log_success "Nginx 安装成功"
        NGINX_INSTALLED=true
    else
        log_error "Nginx 安装失败"
        log_info ""
        log_info "请手动安装Nginx后再运行此脚本："
        log_info "  方法1: yum install -y nginx"
        log_info "  方法2: 从源码编译安装"
        log_info "  方法3: 使用Docker运行nginx"
        log_info ""
        log_warning "或者，您可以使用不依赖Nginx的简化部署方式："
        log_info "  bash deploy_simple.sh"
        exit 1
    fi
fi

echo ""

# ========================================
# 步骤2: 创建目录结构
# ========================================
log_step "【步骤2/10】创建目录结构..."

mkdir -p "${DEPLOY_DIR}/backend" \
         "${DEPLOY_DIR}/water" \
         "${DEPLOY_DIR}/water-admin" \
         "${DEPLOY_DIR}/meeting" \
         "${DEPLOY_DIR}/meeting-admin" \
         "${DEPLOY_DIR}/ssl" \
         "${BACKUP_DIR}/database" \
         "${LOG_DIR}" \
         "/etc/nginx/conf.d"

log_success "目录创建完成"
echo ""

# ========================================
# 步骤3: 检查SSL证书
# ========================================
log_step "【步骤3/10】检查SSL证书..."

if [ -f "${DEPLOY_DIR}/ssl/jhw-ai.com.pem" ] && [ -f "${DEPLOY_DIR}/ssl/jhw-ai.com.key" ]; then
    chmod 644 "${DEPLOY_DIR}/ssl/jhw-ai.com.pem"
    chmod 600 "${DEPLOY_DIR}/ssl/jhw-ai.com.key"
    SSL_ENABLED=true
    log_success "SSL证书已配置"
else
    SSL_ENABLED=false
    log_warning "未配置SSL，使用HTTP部署"
fi
echo ""

# ========================================
# 步骤4: 检查数据库备份
# ========================================
log_step "【步骤4/10】检查数据库备份..."

DB_BACKUP_EXISTS=false
if [ -f "${BACKUP_DIR}/database/waterms_20260404_152737.db" ]; then
    DB_BACKUP_EXISTS=true
    log_success "数据库备份已找到"
else
    log_warning "未找到数据库备份，将使用空数据库"
fi
echo ""

# ========================================
# 步骤5: 部署后端代码
# ========================================
log_step "【步骤5/10】部署后端代码..."

CODE_DIRS=(
    "/root/project/Service_WaterManage/backend"
    "Service_WaterManage/backend"
    "./Service_WaterManage/backend"
    "/root/Service_WaterManage/backend"
)

CODE_FOUND=false
for dir in "${CODE_DIRS[@]}"; do
    if [ -d "$dir" ]; then
        log_info "找到代码: $dir"
        cp -r "$dir"/* "${DEPLOY_DIR}/backend/"
        CODE_FOUND=true
        break
    fi
done

if [ "$CODE_FOUND" = false ]; then
    log_error "未找到后端代码"
    exit 1
fi

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

if [ ! -d ".venv" ]; then
    log_info "创建Python虚拟环境..."
    python3 -m venv .venv
fi

log_info "激活虚拟环境并安装依赖..."
source .venv/bin/activate

pip install --upgrade pip -q 2>/dev/null || pip install --upgrade pip
pip install -r requirements.txt -q 2>/dev/null || pip install -r requirements.txt

deactivate
cd - > /dev/null
log_success "Python依赖安装完成"
echo ""

# ========================================
# 步骤7: 部署前端代码
# ========================================
log_step "【步骤7/10】部署前端代码..."

# 水站管理前端
for dir in "/root/project/Service_WaterManage/frontend" "Service_WaterManage/frontend" "./Service_WaterManage/frontend"; do
    if [ -d "$dir" ]; then
        log_info "复制水站前端: $dir"
        cp -r "$dir"/* "${DEPLOY_DIR}/water/"
        
        if [ -f "${DEPLOY_DIR}/water/admin.html" ]; then
            cp "${DEPLOY_DIR}/water/admin.html" "${DEPLOY_DIR}/water-admin/admin.html"
        fi
        break
    fi
done

# 会议室前端
for dir in "/root/project/Service_MeetingRoom/frontend" "Service_MeetingRoom/frontend" "./Service_MeetingRoom/frontend"; do
    if [ -d "$dir" ]; then
        log_info "复制会议室前端: $dir"
        cp -r "$dir"/* "${DEPLOY_DIR}/meeting/"
        
        if [ -f "${DEPLOY_DIR}/meeting/admin.html" ]; then
            cp "${DEPLOY_DIR}/meeting/admin.html" "${DEPLOY_DIR}/meeting-admin/admin.html"
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
    }
    
    location = / {
        return 301 /water/;
    }
}
EOF
fi

log_success "Nginx配置完成"
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

log_info "启动API服务..."
systemctl start waterms
sleep 3

log_info "启动Nginx服务..."
systemctl start nginx 2>/dev/null || systemctl restart nginx
systemctl enable nginx

# 验证服务
if curl -s http://127.0.0.1:${API_PORT}/api/health 2>/dev/null | grep -q "healthy"; then
    log_success "API服务启动成功"
else
    log_warning "API服务可能未完全启动，请检查日志"
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
echo "  API状态: systemctl status waterms"
echo "  API日志: tail -f ${LOG_DIR}/waterms.log"
echo "  Nginx状态: systemctl status nginx"
echo ""
echo -e "${GREEN}部署完成时间: $(date '+%Y-%m-%d %H:%M:%S')${NC}"
echo ""
