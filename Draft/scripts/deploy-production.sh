#!/bin/bash
# ============================================================
# 智能水站管理系统 - 生产环境部署脚本
# ============================================================
# 用法: ./deploy-production.sh
# ============================================================

set -e

# ==================== 配置区 ====================
# ⚠️ 部署前请修改以下配置

# 服务器配置
SERVER_HOST="120.76.156.83"
SERVER_USER="root"
DOMAIN="jhw-ai.com"

# 部署路径
DEPLOY_BASE="/var/www/${DOMAIN}"
BACKEND_DIR="${DEPLOY_BASE}/backend"
FRONTEND_DIR="${DEPLOY_BASE}/frontend"
LOG_DIR="/var/log/waterms"
BACKUP_DIR="/backup/waterms"

# Git 配置
GIT_REPO="."  # 本地代码

# ==================== 颜色定义 ====================
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# ==================== 函数定义 ====================
log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[OK]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

check_requirements() {
    log_info "检查系统环境..."
    
    # 检查 Python
    if ! command -v python3 &> /dev/null; then
        log_error "Python3 未安装"
        exit 1
    fi
    
    # 检查 Nginx
    if ! command -v nginx &> /dev/null; then
        log_warning "Nginx 未安装，正在安装..."
        yum install -y nginx 2>/dev/null || apt-get install -y nginx
    fi
    
    log_success "系统环境检查通过"
}

create_directories() {
    log_info "创建目录结构..."
    
    mkdir -p "${DEPLOY_BASE}"
    mkdir -p "${BACKEND_DIR}"
    mkdir -p "${FRONTEND_DIR}/water"
    mkdir -p "${FRONTEND_DIR}/water-admin"
    mkdir -p "${LOG_DIR}"
    mkdir -p "${BACKUP_DIR}/database"
    
    log_success "目录创建完成"
}

backup_database() {
    log_info "备份数据库..."
    
    if [ -f "${BACKEND_DIR}/waterms.db" ]; then
        DATE=$(date +%Y%m%d_%H%M%S)
        cp "${BACKEND_DIR}/waterms.db" "${BACKUP_DIR}/database/waterms_${DATE}.db"
        log_success "数据库已备份: waterms_${DATE}.db"
    else
        log_warning "未找到数据库文件，跳过备份"
    fi
}

deploy_backend() {
    log_info "部署后端代码..."
    
    # 复制后端代码
    cp -r Service_WaterManage/backend/* "${BACKEND_DIR}/"
    
    # 创建虚拟环境
    if [ ! -d "${BACKEND_DIR}/.venv" ]; then
        cd "${BACKEND_DIR}"
        python3 -m venv .venv
        source .venv/bin/activate
        pip install -r requirements.txt
        deactivate
        cd - > /dev/null
    fi
    
    # 设置权限
    chmod -R 755 "${BACKEND_DIR}"
    
    log_success "后端代码部署完成"
}

deploy_frontend() {
    log_info "部署前端代码..."
    
    # 复制前端文件
    if [ -d "Service_WaterManage/frontend" ]; then
        cp -r Service_WaterManage/frontend/* "${FRONTEND_DIR}/water/"
    fi
    
    if [ -d "water-admin" ]; then
        cp -r water-admin/* "${FRONTEND_DIR}/water-admin/"
    fi
    
    # 设置权限
    chmod -R 755 "${FRONTEND_DIR}"
    chown -R nginx:nginx "${FRONTEND_DIR}" 2>/dev/null || chown -R www-data:www-data "${FRONTEND_DIR}" 2>/dev/null || true
    
    log_success "前端代码部署完成"
}

configure_nginx() {
    log_info "配置 Nginx..."
    
    # 备份现有配置
    if [ -f "/etc/nginx/conf.d/waterms.conf" ]; then
        cp "/etc/nginx/conf.d/waterms.conf" "/etc/nginx/conf.d/waterms.conf.bak.$(date +%Y%m%d_%H%M%S)"
    fi
    
    # 写入新配置
    cat > /etc/nginx/conf.d/waterms.conf << 'NGINX_EOF'
server {
    listen 80;
    server_name DOMAIN_PLACEHOLDER www.DOMAIN_PLACEHOLDER SERVER_IP_PLACEHOLDER;
    
    access_log /var/log/nginx/waterms_access.log;
    error_log /var/log/nginx/waterms_error.log;
    
    # Gzip 压缩
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/javascript application/json application/xml;
    
    # 前端静态文件 - 用户端
    location /water/ {
        alias FRONTEND_DIR_PLACEHOLDER/water/;
        index index.html;
        try_files $uri $uri/ /water/index.html;
        
        # 缓存静态资源
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2)$ {
            expires 7d;
            add_header Cache-Control "public, immutable";
        }
    }
    
    # 前端静态文件 - 管理后台
    location /water-admin/ {
        alias FRONTEND_DIR_PLACEHOLDER/water-admin/;
        index admin.html;
        try_files $uri $uri/ /water-admin/admin.html;
    }
    
    # API 反向代理
    location /api/ {
        proxy_pass http://127.0.0.1:8000/api/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket 支持
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
        access_log off;
    }
    
    # 根路径重定向
    location = / {
        return 301 /water/;
    }
}
NGINX_EOF

    # 替换变量
    sed -i "s|DOMAIN_PLACEHOLDER|${DOMAIN}|g" /etc/nginx/conf.d/waterms.conf
    sed -i "s|SERVER_IP_PLACEHOLDER|${SERVER_HOST}|g" /etc/nginx/conf.d/waterms.conf
    sed -i "s|FRONTEND_DIR_PLACEHOLDER|${FRONTEND_DIR}|g" /etc/nginx/conf.d/waterms.conf
    
    # 测试并重载配置
    if nginx -t; then
        nginx -s reload
        log_success "Nginx 配置完成"
    else
        log_error "Nginx 配置有误"
        exit 1
    fi
}

setup_systemd() {
    log_info "配置 systemd 服务..."
    
    cat > /etc/systemd/system/waterms.service << 'SYSTEMD_EOF'
[Unit]
Description=Water Management System API Service
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=BACKEND_DIR_PLACEHOLDER
Environment="PATH=BACKEND_DIR_PLACEHOLDER/.venv/bin"
ExecStart=BACKEND_DIR_PLACEHOLDER/.venv/bin/python -m uvicorn main:app --host 127.0.0.1 --port 8000
Restart=always
RestartSec=5
StandardOutput=append:LOG_DIR_PLACEHOLDER/waterms.log
StandardError=append:LOG_DIR_PLACEHOLDER/waterms-error.log

[Install]
WantedBy=multi-user.target
SYSTEMD_EOF

    # 替换变量
    sed -i "s|BACKEND_DIR_PLACEHOLDER|${BACKEND_DIR}|g" /etc/systemd/system/waterms.service
    sed -i "s|LOG_DIR_PLACEHOLDER|${LOG_DIR}|g" /etc/systemd/system/waterms.service
    
    # 重载 systemd
    systemctl daemon-reload
    systemctl enable waterms
    systemctl restart waterms
    
    log_success "systemd 服务配置完成"
}

verify_deployment() {
    log_info "验证部署..."
    
    sleep 3
    
    # 测试 API
    if curl -s http://127.0.0.1:8000/api/health | grep -q "healthy"; then
        log_success "API 服务正常"
    else
        log_warning "API 服务可能有问题"
    fi
    
    # 测试前端
    if curl -s http://127.0.0.1/water/ | grep -q "html"; then
        log_success "前端访问正常"
    else
        log_warning "前端可能有问题"
    fi
}

show_summary() {
    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}  🎉 部署完成！${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
    echo -e "${BLUE}访问地址:${NC}"
    echo "  用户端:    http://${DOMAIN}/water/"
    echo "  管理后台:  http://${DOMAIN}/water-admin/admin.html"
    echo "  或者IP:    http://${SERVER_HOST}/water/"
    echo ""
    echo -e "${BLUE}服务管理:${NC}"
    echo "  启动: systemctl start waterms"
    echo "  停止: systemctl stop waterms"
    echo "  状态: systemctl status waterms"
    echo "  日志: tail -f ${LOG_DIR}/waterms.log"
    echo ""
    echo -e "${BLUE}测试账号:${NC}"
    echo "  用户名: admin"
    echo "  密码:   Jhw@2026!WaterMS"
    echo ""
    echo -e "${YELLOW}注意事项:${NC}"
    echo "  1. 确保安全组已开放 80 和 443 端口"
    echo "  2. 确保域名已解析到 ${SERVER_HOST}"
    echo "  3. 如需 HTTPS，请配置 SSL 证书"
    echo ""
}

# ==================== 主程序 ====================
main() {
    echo -e "${BLUE}"
    echo "========================================"
    echo "  智能水站管理系统 - 生产环境部署"
    echo "========================================"
    echo -e "${NC}"
    
    check_requirements
    create_directories
    backup_database
    deploy_backend
    deploy_frontend
    configure_nginx
    setup_systemd
    verify_deployment
    show_summary
}

main "$@"