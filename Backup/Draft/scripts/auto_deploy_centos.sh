#!/bin/bash
# ============================================
# 本地执行 - 自动上传并部署（CentOS版）
# ============================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[✅ OK]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[⚠️ WARN]${NC} $1"; }
log_error() { echo -e "${RED}[❌ ERROR]${NC} $1"; }

# 配置
SERVER="root@120.76.156.83"
SERVER_IP="120.76.156.83"
DOMAIN="jhw-ai.com"
PROJECT_DIR=$(pwd)

echo -e "${BLUE}"
echo "╔══════════════════════════════════════════════════════╗"
echo "║   自动部署 - CentOS版本（本地执行）                  ║"
echo "╚══════════════════════════════════════════════════════╝"
echo -e "${NC}"
echo ""

# 检查必要的文件
log_info "检查本地文件..."
if [ ! -f "deploy_centos.sh" ]; then
    log_error "deploy_centos.sh 不存在"
    exit 1
fi

log_success "文件检查完成"
echo ""

# ========================================
# 步骤1: 上传部署脚本
# ========================================
log_info "【步骤1/4】上传部署脚本到服务器..."
scp deploy_centos.sh ${SERVER}:/root/
log_success "部署脚本上传完成"
echo ""

# ========================================
# 步骤2: 上传数据库备份
# ========================================
log_info "【步骤2/4】上传数据库备份文件..."
ssh ${SERVER} "mkdir -p /backup/waterms/database"

if [ -f "backups/database/waterms_20260404_152737.db" ]; then
    scp backups/database/*.db backups/database/*.md5 ${SERVER}:/backup/waterms/database/ 2>/dev/null || true
    log_success "数据库备份上传完成"
else
    log_warning "跳过数据库备份上传"
fi
echo ""

# ========================================
# 步骤3: 上传SSL证书
# ========================================
log_info "【步骤3/4】上传SSL证书..."
ssh ${SERVER} "mkdir -p /var/www/${DOMAIN}/ssl"

if [ -f "Draft/docs/SSL/24143096_jhw-ai.com_nginx/jhw-ai.com.pem" ]; then
    scp Draft/docs/SSL/24143096_jhw-ai.com_nginx/* ${SERVER}:/var/www/${DOMAIN}/ssl/
    log_success "SSL证书上传完成"
else
    log_warning "跳过SSL证书上传"
fi
echo ""

# ========================================
# 步骤4: 上传项目代码
# ========================================
log_info "【步骤4/4】上传项目代码（这可能需要几分钟）..."
ssh ${SERVER} "mkdir -p /root/project"

# 上传后端代码
log_info "上传水站管理后端..."
ssh ${SERVER} "mkdir -p /root/project/Service_WaterManage/backend"
scp -r Service_WaterManage/backend/* ${SERVER}:/root/project/Service_WaterManage/backend/

log_info "上传水站管理前端..."
ssh ${SERVER} "mkdir -p /root/project/Service_WaterManage/frontend"
scp -r Service_WaterManage/frontend/* ${SERVER}:/root/project/Service_WaterManage/frontend/

log_info "上传会议室管理后端..."
ssh ${SERVER} "mkdir -p /root/project/Service_MeetingRoom/backend"
scp -r Service_MeetingRoom/backend/* ${SERVER}:/root/project/Service_MeetingRoom/backend/ 2>/dev/null || true

log_info "上传会议室管理前端..."
ssh ${SERVER} "mkdir -p /root/project/Service_MeetingRoom/frontend"
scp -r Service_MeetingRoom/frontend/* ${SERVER}:/root/project/Service_MeetingRoom/frontend/

log_success "项目代码上传完成"
echo ""

# ========================================
# 执行远程部署
# ========================================
log_info "执行远程部署脚本..."
echo ""
echo -e "${YELLOW}========================================${NC}"
echo -e "${YELLOW}正在服务器上执行部署，请稍候...${NC}"
echo -e "${YELLOW}========================================${NC}"
echo ""

ssh ${SERVER} "cd /root/project && bash /root/deploy_centos.sh"

echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║          ✅ 自动部署完成！                           ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════╝${NC}"
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
echo -e "${YELLOW}【重要提醒】${NC}"
echo "  请立即登录管理后台修改密码！"
echo ""