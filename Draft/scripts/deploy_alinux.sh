#!/bin/bash
# ============================================
# Alibaba Cloud Linux 专用部署脚本
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
echo "║   AI产业集群服务管理平台 - Alibaba Cloud专用版       ║"
echo "╚══════════════════════════════════════════════════════╝"
echo -e "${NC}"
echo "部署时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo "服务器: ${SERVER_IP}"
echo ""

# ========================================
# 步骤1: 环境检查
# ========================================
log_step "【步骤1/10】环境检查..."

# 检查root权限
[ "$EUID" -ne 0 ] && log_error "请使用root用户执行" && exit 1

# 检查Python3
command -v python3 &> /dev/null || { log_error "Python3未安装"; exit 1; }
log_success "Python3: $(python3 --version)"

# 检查pip3
command -v pip3 &> /dev/null || yum install -y python3-pip
log_success "pip3已安装"

# 检查sqlite3
command -v sqlite3 &> /dev/null || yum install -y sqlite
log_success "SQLite3已安装"

# 检查Nginx - 多种检测方式
NGINX_EXISTS=false
if command -v nginx &> /dev/null; then
    NGINX_EXISTS=true
    log_success "Nginx已安装: $(nginx -v 2>&1)"
elif [ -f /usr/sbin/nginx ]; then
    NGINX_EXISTS=true
    log_success "Nginx已安装在/usr/sbin/nginx"
elif rpm -q nginx &> /dev/null; then
    NGINX_EXISTS=true
    log_success "Nginx包已安装"
fi

# 如果nginx未安装，使用dnf安装
if [ "$NGINX_EXISTS" = false ]; then
    log_warning "Nginx未安装，正在安装..."
    
    # 方法1: 直接使用dnf/yum安装（Alibaba Cloud Linux通常已有nginx）
    log_info "尝试从系统仓库安装nginx..."
    
    # 先更新仓库
    dnf clean all
    dnf makecache
    
    # 尝试安装nginx
    if dnf install -y nginx 2>/dev/null; then
        log_success "Nginx安装成功"
        NGINX_EXISTS=true
    else
        # 方法2: 配置nginx官方仓库（针对RHEL 8）
        log_info "配置nginx官方RHEL8仓库..."
        
        cat > /etc/yum.repos.d/nginx.repo << 'EOF'
[nginx-stable]
name=nginx stable repo
baseurl=http://nginx.org/packages/rhel/8/$basearch/
gpgcheck=0
enabled=1
EOF
        
        dnf clean all
        dnf makecache
        
        if dnf install -y nginx; then
            log_success "Nginx安装成功"
            NGINX_EXISTS=true
        else
            # 方法3: 使用EPEL
            log_info "尝试从EPEL安装..."
            dnf install -y epel-release
            dnf install -y nginx
            
            if [ $? -eq 0 ]; then
                log_success "Nginx安装成功"
                NGINX_EXISTS=true
            else
                log_error "Nginx安装失败"
                echo ""
                echo "请手动安装nginx："
                echo "  dnf install -y nginx"
                echo "或"
                echo "  yum install -y nginx"
                exit 1
            fi
        fi
    fi
fi

echo ""

# ========================================
# 步骤2-10: 其余步骤保持不变
# ========================================

log_step "【步骤2/10】创建目录..."
mkdir -p "${DEPLOY_DIR}/"{backend,water,water-admin,meeting,meeting-admin,ssl} \
         "${BACKUP_DIR}/database" "${LOG_DIR}" /etc/nginx/conf.d
log_success "目录创建完成"
echo ""

log_step "【步骤3/10】检查SSL证书..."
if [ -f "${DEPLOY_DIR}/ssl/jhw-ai.com.pem" ]; then
    chmod 644 "${DEPLOY_DIR}/ssl/jhw-ai.com.pem"
    chmod 600 "${DEPLOY_DIR}/ssl/jhw-ai.com.key"
    SSL_ENABLED=true
    log_success "SSL已配置"
else
    SSL_ENABLED=false
    log_warning "使用HTTP"
fi
echo ""

log_step "【步骤4/10】检查数据库..."
[ -f "${BACKUP_DIR}/database/waterms_20260404_152737.db" ] && log_success "数据库备份存在" || log_warning "无备份"
echo ""

log_step "【步骤5/10】部署后端..."
for dir in /root/project/Service_WaterManage/backend Service_WaterManage/backend ./Service_WaterManage/backend; do
    [ -d "$dir" ] && cp -r "$dir"/* "${DEPLOY_DIR}/backend/" && log_success "后端代码已部署" && break
done

[ -f "${BACKUP_DIR}/database/waterms_20260404_152737.db" ] && cp "${BACKUP_DIR}/database/waterms_20260404_152737.db" "${DEPLOY_DIR}/backend/waterms.db"
[ -f "${BACKUP_DIR}/database/meeting_20260404_152737.db" ] && cp "${BACKUP_DIR}/database/meeting_20260404_152737.db" "${DEPLOY_DIR}/backend/meeting.db"
echo ""

log_step "【步骤6/10】安装Python依赖..."
cd "${DEPLOY_DIR}/backend"
[ ! -d .venv ] && python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip -q
pip install -r requirements.txt -q 2>/dev/null || pip install -r requirements.txt
deactivate
cd - > /dev/null
log_success "依赖安装完成"
echo ""

log_step "【步骤7/10】部署前端..."
[ -d /root/project/Service_WaterManage/frontend ] && cp -r /root/project/Service_WaterManage/frontend/* "${DEPLOY_DIR}/water/"
[ -d /root/project/Service_MeetingRoom/frontend ] && cp -r /root/project/Service_MeetingRoom/frontend/* "${DEPLOY_DIR}/meeting/"
[ -f "${DEPLOY_DIR}/water/admin.html" ] && cp "${DEPLOY_DIR}/water/admin.html" "${DEPLOY_DIR}/water-admin/admin.html"
[ -f "${DEPLOY_DIR}/meeting/admin.html" ] && cp "${DEPLOY_DIR}/meeting/admin.html" "${DEPLOY_DIR}/meeting-admin/admin.html"
log_success "前端部署完成"
echo ""

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
    
    location /water/ { alias /var/www/jhw-ai.com/water/; index index.html; }
    location /water-admin/ { alias /var/www/jhw-ai.com/water-admin/; index admin.html; }
    location /meeting/ { alias /var/www/jhw-ai.com/meeting/; index index.html; }
    location /meeting-admin/ { alias /var/www/jhw-ai.com/meeting-admin/; index admin.html; }
    location /api/ { proxy_pass http://127.0.0.1:8000/api/; proxy_set_header Host $host; }
    location = / { return 301 /water/; }
}
EOF
else
    cat > /etc/nginx/conf.d/jhw-ai.conf << 'EOF'
server {
    listen 80;
    server_name jhw-ai.com www.jhw-ai.com 120.76.156.83;
    
    location /water/ { alias /var/www/jhw-ai.com/water/; index index.html; }
    location /water-admin/ { alias /var/www/jhw-ai.com/water-admin/; index admin.html; }
    location /meeting/ { alias /var/www/jhw-ai.com/meeting/; index index.html; }
    location /meeting-admin/ { alias /var/www/jhw-ai.com/meeting-admin/; index admin.html; }
    location /api/ { proxy_pass http://127.0.0.1:8000/api/; proxy_set_header Host $host; }
    location = / { return 301 /water/; }
}
EOF
fi

nginx -t && log_success "Nginx配置完成"
echo ""

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
log_success "服务配置完成"
echo ""

log_step "【步骤10/10】启动服务..."
systemctl start waterms
sleep 3
systemctl start nginx
systemctl enable nginx

curl -s http://127.0.0.1:${API_PORT}/api/health | grep -q healthy && log_success "服务启动成功" || log_warning "请检查日志"

echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║          ✅ 部署完成！                               ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${CYAN}访问地址:${NC}"
echo "  水站: http://${SERVER_IP}/water/"
echo "  后台: http://${SERVER_IP}/water-admin/admin.html"
echo "  会议室: http://${SERVER_IP}/meeting/"
echo ""
echo -e "${CYAN}账号: admin / admin123${NC}"
echo ""
