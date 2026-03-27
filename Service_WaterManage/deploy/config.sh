#!/bin/bash
# ==========================================
# 项目部署配置
# 根据不同项目修改此配置即可
# ==========================================

# ==========================================
# 项目基本信息
# ==========================================
PROJECT_NAME="water"
PROJECT_DESC="智能水站管理系统"

# 本地项目根目录（相对于脚本所在目录）
LOCAL_PROJECT_ROOT="$(dirname "$0")/.."

# ==========================================
# 服务器配置
# ==========================================
SERVER_HOST="120.76.156.83"
SERVER_USER="root"
SERVER_PORT=22
# SSH 密码（可选，如果没有配置 SSH 密钥）
SERVER_PASSWORD="sgl@810SGl"

# ==========================================
# 域名配置
# ==========================================
DOMAIN="jhw-ai.com"
HTTPS=true
# SSL 证书路径（服务器上）
SSL_CERT_PATH="/etc/nginx/ssl/jhw-ai.com.pem"
SSL_KEY_PATH="/etc/nginx/ssl/jhw-ai.com.key"

# ==========================================
# 前端路径配置
# ==========================================
FRONTEND_USER_PATH="/water"        # 用户端访问路径，如 /water
FRONTEND_ADMIN_PATH="/water-admin" # 管理后台路径，如 /water-admin

# ==========================================
# 后端配置
# ==========================================
BACKEND_PORT=8000
PYTHON_VERSION="3.8"

# 前端文件到服务器的目录映射
# 格式: "本地文件:服务器目录"
# 本地路径相对于 LOCAL_PROJECT_ROOT
FRONTEND_FILES=(
    "Service_WaterManage/frontend/index.html:/water/index.html"
    "Service_WaterManage/frontend/admin.html:/water-admin/admin.html"
    "Service_WaterManage/frontend/login.html:/water-admin/login.html"
    "Service_WaterManage/frontend/vue.global.js:/water/vue.global.js"
    "Service_WaterManage/frontend/vue.global.js:/water-admin/vue.global.js"
)

# 后端目录
BACKEND_DIR="Service_WaterManage/backend"

# ==========================================
# 高级配置（通常不需要修改）
# ==========================================

# 服务器项目根目录
SERVER_PROJECT_ROOT="/var/www/${DOMAIN}"

# Nginx 配置文件模板
NGINX_TEMPLATE="nginx-template.conf"

# 是否启用自动备份
AUTO_BACKUP=true
BACKUP_RETENTION_DAYS=7

# 部署前检查
PRE_DEPLOY_CHECKS=(
    "check_ssh_connection"
    "check_disk_space"
    "check_nginx"
)
