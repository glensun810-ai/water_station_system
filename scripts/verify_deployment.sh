#!/bin/bash
# ============================================
# 生产环境部署后验证脚本
# ============================================
# 用途：部署完成后自动验证所有服务和功能
# 执行：在服务器上执行此脚本
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
log_test() { echo -e "${CYAN}[TEST]${NC} $1"; }

# 配置
SERVER_IP="120.76.156.83"
DOMAIN="jhw-ai.com"
API_PORT=8000
LOG_FILE="/var/log/waterms/deploy_verification.log"

# 验证结果统计
PASS_COUNT=0
FAIL_COUNT=0
WARN_COUNT=0

echo -e "${BLUE}"
echo "========================================"
echo "  生产环境部署验证"
echo "========================================"
echo -e "${NC}"
echo "验证时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo "服务器: ${SERVER_IP}"
echo "域名: ${DOMAIN}"
echo ""

# 创建日志文件
mkdir -p /var/log/waterms
exec > >(tee -a "$LOG_FILE") 2>&1

# ========================================
# 1. 系统服务检查
# ========================================
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}【1】系统服务检查${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# 检查 Nginx
log_test "检查 Nginx 服务..."
if systemctl is-active --quiet nginx; then
    log_success "Nginx 服务运行正常"
    PASS_COUNT=$((PASS_COUNT + 1))
else
    log_error "Nginx 服务未运行"
    FAIL_COUNT=$((FAIL_COUNT + 1))
fi

# 检查 WaterMS API服务
log_test "检查 WaterMS API 服务..."
if systemctl is-active --quiet waterms; then
    log_success "WaterMS API 服务运行正常"
    PASS_COUNT=$((PASS_COUNT + 1))
else
    if pgrep -f "uvicorn.*main:app" > /dev/null; then
        log_warning "WaterMS API 进程运行中（非systemd管理）"
        WARN_COUNT=$((WARN_COUNT + 1))
    else
        log_error "WaterMS API 服务未运行"
        FAIL_COUNT=$((FAIL_COUNT + 1))
    fi
fi

# 检查端口监听
log_test "检查 API 端口 ${API_PORT}..."
if netstat -tuln | grep -q ":${API_PORT} "; then
    log_success "API 端口 ${API_PORT} 正在监听"
    PASS_COUNT=$((PASS_COUNT + 1))
else
    log_error "API 端口 ${API_PORT} 未监听"
    FAIL_COUNT=$((FAIL_COUNT + 1))
fi

echo ""

# ========================================
# 2. API健康检查
# ========================================
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}【2】API健康检查${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# API内部健康检查
log_test "API 内部健康检查 (localhost)..."
API_RESPONSE=$(curl -s -w "\n%{http_code}" http://127.0.0.1:${API_PORT}/api/health)
API_BODY=$(echo "$API_RESPONSE" | head -n -1)
API_STATUS=$(echo "$API_RESPONSE" | tail -n 1)

if [ "$API_STATUS" = "200" ]; then
    log_success "API 响应正常 (HTTP 200)"
    log_info "响应内容: $API_BODY"
    PASS_COUNT=$((PASS_COUNT + 1))
else
    log_error "API 响应异常 (HTTP $API_STATUS)"
    log_error "响应内容: $API_BODY"
    FAIL_COUNT=$((FAIL_COUNT + 1))
fi

# API外部健康检查（通过Nginx）
log_test "API 外部健康检查 (Nginx代理)..."
API_NGINX_RESPONSE=$(curl -s -w "\n%{http_code}" http://${SERVER_IP}/api/health)
API_NGINX_BODY=$(echo "$API_NGINX_RESPONSE" | head -n -1)
API_NGINX_STATUS=$(echo "$API_NGINX_RESPONSE" | tail -n 1)

if [ "$API_NGINX_STATUS" = "200" ]; then
    log_success "API 通过Nginx访问正常 (HTTP 200)"
    PASS_COUNT=$((PASS_COUNT + 1))
else
    log_error "API 通过Nginx访问异常 (HTTP $API_NGINX_STATUS)"
    FAIL_COUNT=$((FAIL_COUNT + 1))
fi

# HTTPS API健康检查
log_test "HTTPS API 健康检查..."
HTTPS_RESPONSE=$(curl -s -k -w "\n%{http_code}" https://${DOMAIN}/api/health 2>&1)
HTTPS_BODY=$(echo "$HTTPS_RESPONSE" | head -n -1)
HTTPS_STATUS=$(echo "$HTTPS_RESPONSE" | tail -n 1)

if [ "$HTTPS_STATUS" = "200" ]; then
    log_success "HTTPS API 访问正常 (HTTP 200)"
    PASS_COUNT=$((PASS_COUNT + 1))
else
    log_warning "HTTPS API 访问失败 (HTTP $HTTPS_STATUS) - 可能SSL未配置"
    log_info "响应: $HTTPS_BODY"
    WARN_COUNT=$((WARN_COUNT + 1))
fi

echo ""

# ========================================
# 3. 前端页面检查
# ========================================
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}【3】前端页面可访问性检查${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# 检查前端文件存在性
FRONTEND_BASE="/var/www/${DOMAIN}"

log_test "检查水站管理前端文件..."
if [ -f "${FRONTEND_BASE}/water/index.html" ]; then
    log_success "水站用户端前端文件存在"
    PASS_COUNT=$((PASS_COUNT + 1))
else
    log_error "水站用户端前端文件缺失"
    FAIL_COUNT=$((FAIL_COUNT + 1))
fi

if [ -f "${FRONTEND_BASE}/water-admin/admin.html" ]; then
    log_success "水站管理后台前端文件存在"
    PASS_COUNT=$((PASS_COUNT + 1))
else
    log_error "水站管理后台前端文件缺失"
    FAIL_COUNT=$((FAIL_COUNT + 1))
fi

log_test "检查会议室管理前端文件..."
if [ -f "${FRONTEND_BASE}/meeting/index.html" ]; then
    log_success "会议室用户端前端文件存在"
    PASS_COUNT=$((PASS_COUNT + 1))
else
    log_warning "会议室用户端前端文件缺失 - 可能未部署"
    WARN_COUNT=$((WARN_COUNT + 1))
fi

if [ -f "${FRONTEND_BASE}/meeting-admin/admin.html" ]; then
    log_success "会议室管理后台前端文件存在"
    PASS_COUNT=$((PASS_COUNT + 1))
else
    log_warning "会议室管理后台前端文件缺失 - 可能未部署"
    WARN_COUNT=$((WARN_COUNT + 1))
fi

# 前端页面访问检查
log_test "检查水站用户端页面访问..."
WATER_PAGE=$(curl -s -w "\n%{http_code}" http://${SERVER_IP}/water/)
WATER_STATUS=$(echo "$WATER_PAGE" | tail -n 1)

if [ "$WATER_STATUS" = "200" ]; then
    log_success "水站用户端页面可访问 (HTTP 200)"
    PASS_COUNT=$((PASS_COUNT + 1))
else
    log_error "水站用户端页面无法访问 (HTTP $WATER_STATUS)"
    FAIL_COUNT=$((FAIL_COUNT + 1))
fi

log_test "检查水站管理后台页面访问..."
ADMIN_PAGE=$(curl -s -w "\n%{http_code}" http://${SERVER_IP}/water-admin/admin.html)
ADMIN_STATUS=$(echo "$ADMIN_PAGE" | tail -n 1)

if [ "$ADMIN_STATUS" = "200" ]; then
    log_success "水站管理后台页面可访问 (HTTP 200)"
    PASS_COUNT=$((PASS_COUNT + 1))
else
    log_error "水站管理后台页面无法访问 (HTTP $ADMIN_STATUS)"
    FAIL_COUNT=$((FAIL_COUNT + 1))
fi

echo ""

# ========================================
# 4. 数据库检查
# ========================================
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}【4】数据库检查${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

BACKEND_DIR="${FRONTEND_BASE}/backend"

log_test "检查水站数据库文件..."
if [ -f "${BACKEND_DIR}/waterms.db" ]; then
    DB_SIZE=$(du -h "${BACKEND_DIR}/waterms.db" | cut -f1)
    log_success "水站数据库文件存在 (大小: ${DB_SIZE})"
    
    # 数据库完整性检查
    DB_CHECK=$(sqlite3 "${BACKEND_DIR}/waterms.db" "PRAGMA integrity_check;" 2>&1)
    if [ "$DB_CHECK" = "ok" ]; then
        log_success "水站数据库完整性验证通过"
        PASS_COUNT=$((PASS_COUNT + 2))
    else
        log_error "水站数据库完整性验证失败: $DB_CHECK"
        FAIL_COUNT=$((FAIL_COUNT + 1))
    fi
else
    log_error "水站数据库文件不存在"
    FAIL_COUNT=$((FAIL_COUNT + 1))
fi

log_test "检查会议室数据库文件..."
if [ -f "${BACKEND_DIR}/meeting.db" ]; then
    MEETING_DB_SIZE=$(du -h "${BACKEND_DIR}/meeting.db" | cut -f1)
    log_success "会议室数据库文件存在 (大小: ${MEETING_DB_SIZE})"
    
    # 数据库完整性检查
    MEETING_DB_CHECK=$(sqlite3 "${BACKEND_DIR}/meeting.db" "PRAGMA integrity_check;" 2>&1)
    if [ "$MEETING_DB_CHECK" = "ok" ]; then
        log_success "会议室数据库完整性验证通过"
        PASS_COUNT=$((PASS_COUNT + 2))
    else
        log_error "会议室数据库完整性验证失败: $MEETING_DB_CHECK"
        FAIL_COUNT=$((FAIL_COUNT + 1))
    fi
else
    log_warning "会议室数据库文件不存在 - 可能未部署"
    WARN_COUNT=$((WARN_COUNT + 1))
fi

echo ""

# ========================================
# 5. SSL证书检查
# ========================================
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}【5】SSL证书检查${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

SSL_DIR="${FRONTEND_BASE}/ssl"

log_test "检查SSL证书文件..."
if [ -f "${SSL_DIR}/jhw-ai.com.pem" ]; then
    log_success "SSL证书文件存在"
    
    # 检查证书有效期
    CERT_EXPIRE=$(openssl x509 -enddate -noout -in "${SSL_DIR}/jhw-ai.com.pem" 2>&1 | cut -d= -f2)
    log_info "证书过期时间: $CERT_EXPIRE"
    
    # 检查证书权限
    CERT_PERM=$(stat -c "%a" "${SSL_DIR}/jhw-ai.com.pem" 2>/dev/null || stat -f "%Lp" "${SSL_DIR}/jhw-ai.com.pem")
    if [ "$CERT_PERM" = "644" ] || [ "$CERT_PERM" = "600" ]; then
        log_success "SSL证书文件权限正确 ($CERT_PERM)"
        PASS_COUNT=$((PASS_COUNT + 2))
    else
        log_warning "SSL证书文件权限不标准 ($CERT_PERM)"
        WARN_COUNT=$((WARN_COUNT + 1))
    fi
else
    log_warning "SSL证书文件不存在 - HTTPS将无法使用"
    WARN_COUNT=$((WARN_COUNT + 1))
fi

log_test "检查SSL私钥文件..."
if [ -f "${SSL_DIR}/jhw-ai.com.key" ]; then
    log_success "SSL私钥文件存在"
    
    KEY_PERM=$(stat -c "%a" "${SSL_DIR}/jhw-ai.com.key" 2>/dev/null || stat -f "%Lp" "${SSL_DIR}/jhw-ai.com.key")
    if [ "$KEY_PERM" = "600" ]; then
        log_success "SSL私钥文件权限安全 ($KEY_PERM)"
        PASS_COUNT=$((PASS_COUNT + 1))
    else
        log_warning "SSL私钥文件权限不安全 ($KEY_PERM) - 建议设置为600"
        WARN_COUNT=$((WARN_COUNT + 1))
    fi
else
    log_warning "SSL私钥文件不存在 - HTTPS将无法使用"
    WARN_COUNT=$((WARN_COUNT + 1))
fi

echo ""

# ========================================
# 6. 文件权限和目录检查
# ========================================
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}【6】文件权限和目录检查${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

log_test "检查应用目录..."
if [ -d "${FRONTEND_BASE}" ]; then
    log_success "应用目录存在: ${FRONTEND_BASE}"
    PASS_COUNT=$((PASS_COUNT + 1))
else
    log_error "应用目录不存在"
    FAIL_COUNT=$((FAIL_COUNT + 1))
fi

log_test "检查备份目录..."
if [ -d "/backup/waterms/database" ]; then
    BACKUP_COUNT=$(ls -1 /backup/waterms/database/*.db 2>/dev/null | wc -l)
    log_success "备份目录存在，备份文件数: ${BACKUP_COUNT}"
    PASS_COUNT=$((PASS_COUNT + 1))
else
    log_warning "备份目录不存在 - 数据安全风险"
    WARN_COUNT=$((WARN_COUNT + 1))
fi

log_test "检查日志目录..."
if [ -d "/var/log/waterms" ]; then
    log_success "日志目录存在"
    PASS_COUNT=$((PASS_COUNT + 1))
else
    log_warning "日志目录不存在"
    WARN_COUNT=$((WARN_COUNT + 1))
fi

echo ""

# ========================================
# 7. Nginx配置检查
# ========================================
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}【7】Nginx配置检查${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

log_test "检查Nginx配置语法..."
NGINX_TEST=$(nginx -t 2>&1)
if echo "$NGINX_TEST" | grep -q "syntax is ok"; then
    log_success "Nginx配置语法正确"
    PASS_COUNT=$((PASS_COUNT + 1))
else
    log_error "Nginx配置语法错误"
    log_error "$NGINX_TEST"
    FAIL_COUNT=$((FAIL_COUNT + 1))
fi

log_test "检查Nginx配置文件..."
if [ -f "/etc/nginx/conf.d/jhw-ai.conf" ] || [ -f "/etc/nginx/conf.d/water.conf" ]; then
    log_success "Nginx站点配置文件存在"
    PASS_COUNT=$((PASS_COUNT + 1))
else
    log_warning "Nginx站点配置文件可能缺失"
    WARN_COUNT=$((WARN_COUNT + 1))
fi

echo ""

# ========================================
# 验证结果汇总
# ========================================
echo -e "${BLUE}"
echo "========================================"
echo "  验证结果汇总"
echo "========================================"
echo -e "${NC}"

TOTAL_TESTS=$((PASS_COUNT + FAIL_COUNT + WARN_COUNT))

echo -e "${GREEN}✅ 通过: ${PASS_COUNT}${NC}"
echo -e "${RED}❌ 失败: ${FAIL_COUNT}${NC}"
echo -e "${YELLOW}⚠️ 警告: ${WARN_COUNT}${NC}"
echo "总计检查项: ${TOTAL_TESTS}"
echo ""

if [ $FAIL_COUNT -eq 0 ]; then
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}✅ 所有核心验证通过！部署成功！${NC}"
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    
    if [ $WARN_COUNT -gt 0 ]; then
        echo -e "${YELLOW}提示：有 ${WARN_COUNT} 个警告项，建议检查处理${NC}"
    fi
    
    echo ""
    echo -e "${BLUE}访问地址:${NC}"
    echo "  HTTP:  http://${SERVER_IP}/water/"
    echo "  HTTPS: https://${DOMAIN}/water/ (需SSL配置)"
    echo ""
    echo -e "${BLUE}管理后台:${NC}"
    echo "  HTTP:  http://${SERVER_IP}/water-admin/admin.html"
    echo ""
    
    exit 0
else
    echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${RED}❌ 验证失败！请检查并修复上述错误${NC}"
    echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    
    echo ""
    echo -e "${YELLOW}建议操作:${NC}"
    echo "  1. 检查服务状态: systemctl status nginx waterms"
    echo "  2. 查看日志: tail -f /var/log/waterms/*.log"
    echo "  3. 检查端口: netstat -tuln | grep ${API_PORT}"
    echo ""
    
    exit 1
fi