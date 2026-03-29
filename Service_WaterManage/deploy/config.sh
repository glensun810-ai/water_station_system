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

# 本地项目根目录（使用 SCRIPT_DIR 如果可用，否则基于当前脚本位置）
if [ -n "$SCRIPT_DIR" ]; then
    LOCAL_PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
else
    LOCAL_PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/.."
fi

# ==========================================
# 服务器基础配置
# ==========================================
SERVER_HOST="120.76.156.83"
SERVER_USER="root"
SERVER_PORT=22

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
    "frontend/index.html:/water/index.html"
    "frontend/admin.html:/water-admin/admin.html"
    "frontend/login.html:/water-admin/login.html"
    "frontend/change-password.html:/water-admin/change-password.html"
    "frontend/vue.global.js:/water/vue.global.js"
    "frontend/vue.global.js:/water-admin/vue.global.js"
)

# 后端目录
BACKEND_DIR="backend"

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

# ==========================================
# 生产数据保护配置（绝对不允许覆盖的文件/目录）
# ==========================================
PROTECTED_PATTERNS=(
    "*.db"           # SQLite 数据库（包含所有业务数据）
    "*.sqlite"       # SQLite 数据库
    "*.sqlite3"     # SQLite 数据库
    "waterms.db"     # 主数据库文件
    "*.log"          # 日志文件
    "uploads/"       # 上传的文件
    "*.env"          # 环境变量文件
)

# 是否启用生产数据保护（强烈建议开启）
PROTECT_PRODUCTION_DATA=true

# 部署前检查
PRE_DEPLOY_CHECKS=(
    "check_ssh_connection"
    "check_disk_space"
    "check_nginx"
    "verify_production_data_exists"
)

# ==========================================
# 敏感信息配置（从外部文件加载）
# ==========================================

# 尝试加载敏感信息配置文件
if [ -f "$(dirname "${BASH_SOURCE[0]}")/config-sensitive.sh" ]; then
    source "$(dirname "${BASH_SOURCE[0]}")/config-sensitive.sh"
fi

# 如果未配置 SSH 密钥或密码，使用默认值
SSH_KEY_PATH="${SSH_KEY_PATH:-$HOME/.ssh/jhw-ai-server.pem}"
SERVER_PASSWORD="${SERVER_PASSWORD:-}"

# ==========================================
# 阿里云安全组配置（可选）
# ==========================================

# 如果需要自动配置安全组，取消注释并填写
# ALIYUN_ACCESS_KEY_ID=""
# ALIYUN_ACCESS_KEY_SECRET=""
# ALIYUN_REGION_ID=""
# ALIYUN_INSTANCE_ID=""