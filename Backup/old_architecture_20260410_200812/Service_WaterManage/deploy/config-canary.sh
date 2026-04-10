#!/bin/bash
# ==========================================
# 灰度环境部署配置
# ==========================================
#
# 灰度环境特性：
# - 独立的部署路径和端口
# - 独立的数据库（生产数据库副本）
# - 不影响生产环境
# - 可随时删除或重建
# ==========================================

# ==========================================
# 项目基本信息
# ==========================================
PROJECT_NAME="water-canary"
PROJECT_DESC="智能水站管理系统 - 灰度环境"

# 本地项目根目录
if [ -n "$SCRIPT_DIR" ]; then
    LOCAL_PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
else
    LOCAL_PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/.."
fi

# ==========================================
# 服务器基础配置（与生产环境相同）
# ==========================================
SERVER_HOST="120.76.156.83"
SERVER_USER="root"
SERVER_PORT=22

# ==========================================
# 域名配置 - 灰度环境使用子域名
# ==========================================
# 方案 1: 子域名方式（推荐）
CANARY_DOMAIN="canary.jhw-ai.com"
DOMAIN="${CANARY_DOMAIN}"

# 方案 2: 路径方式（备选）
# CANARY_PATH="/canary"
# DOMAIN="jhw-ai.com"

HTTPS=true
# SSL 证书路径（与生产环境相同，或使用通配符证书）
SSL_CERT_PATH="/etc/nginx/ssl/jhw-ai.com.pem"
SSL_KEY_PATH="/etc/nginx/ssl/jhw-ai.com.key"

# ==========================================
# 前端路径配置 - 与生产环境相同
# ==========================================
FRONTEND_USER_PATH="/water"
FRONTEND_ADMIN_PATH="/water-admin"

# ==========================================
# 后端配置 - 使用不同端口
# ==========================================
BACKEND_PORT=8001  # 生产环境是 8000，灰度使用 8001
PYTHON_VERSION="3.8"

# 前端文件映射（与生产环境相同）
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
# 灰度环境专属配置
# ==========================================

# 灰度环境项目根目录（独立路径）
SERVER_PROJECT_ROOT="/var/www/canary-${DOMAIN}"

# 灰度数据库文件名（从生产数据库复制）
CANARY_DB_NAME="waterms_canary.db"
PRODUCTION_DB_NAME="waterms.db"

# 生产环境路径（用于同步数据库）
PRODUCTION_PROJECT_ROOT="/var/www/jhw-ai.com"

# ==========================================
# 高级配置
# ==========================================

# 是否启用自动备份
AUTO_BACKUP=true
BACKUP_RETENTION_DAYS=7

# ==========================================
# 生产数据保护配置（灰度环境也需要保护）
# ==========================================
PROTECTED_PATTERNS=(
    "*.db"
    "*.sqlite"
    "*.sqlite3"
    "waterms_canary.db"
    "*.log"
    "uploads/"
    "*.env"
)

PROTECT_PRODUCTION_DATA=true

# 部署前检查
PRE_DEPLOY_CHECKS=(
    "check_ssh_connection"
    "check_disk_space"
    "check_nginx"
)

# ==========================================
# 敏感信息配置（从外部文件加载）
# ==========================================
if [ -f "$(dirname "${BASH_SOURCE[0]}")/config-sensitive.sh" ]; then
    source "$(dirname "${BASH_SOURCE[0]}")/config-sensitive.sh"
fi

SSH_KEY_PATH="${SSH_KEY_PATH:-$HOME/.ssh/jhw-ai-server.pem}"
SERVER_PASSWORD="${SERVER_PASSWORD:-}"

# ==========================================
# 阿里云安全组配置（可选）
# ==========================================
# ALIYUN_ACCESS_KEY_ID=""
# ALIYUN_ACCESS_KEY_SECRET=""
# ALIYUN_REGION_ID=""
# ALIYUN_INSTANCE_ID=""