#!/bin/bash
# ============================================
# 一键部署 - 本地到服务器（完整版）
# ============================================

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
NC='\033[0m'

SERVER="root@120.76.156.83"
IP="120.76.156.83"

echo -e "${BLUE}"
echo "╔══════════════════════════════════════════════════════╗"
echo "║   一键部署 - Portal首页+真实数据                     ║"
echo "╚══════════════════════════════════════════════════════╝"
echo -e "${NC}"
echo ""

# 检查本地文件
echo -e "${CYAN}检查本地文件...${NC}"
[ ! -f "deploy_full.sh" ] && echo "❌ deploy_full.sh 不存在" && exit 1
[ ! -d "Service_WaterManage" ] && echo "❌ Service_WaterManage 不存在" && exit 1
[ ! -d "portal" ] && echo "❌ portal 不存在" && exit 1
echo -e "${GREEN}✅ 文件检查通过${NC}"
echo ""

# ========================================
# 1. 上传部署脚本
# ========================================
echo -e "${CYAN}[1/5] 上传部署脚本...${NC}"
scp deploy_full.sh ${SERVER}:/root/ && echo -e "${GREEN}✅ 完成${NC}" || exit 1
echo ""

# ========================================
# 2. 上传数据库备份
# ========================================
echo -e "${CYAN}[2/5] 上传真实数据库...${NC}"
ssh ${SERVER} "mkdir -p /backup/waterms/database"

# 上传备份的数据库
if [ -f "backups/database/waterms_20260404_152737.db" ]; then
    echo "  → 上传水站数据库..."
    scp backups/database/waterms_20260404_152737.db ${SERVER}:/backup/waterms/database/
fi

if [ -f "backups/database/meeting_20260404_152737.db" ]; then
    echo "  → 上传会议室数据库..."
    scp backups/database/meeting_20260404_152737.db ${SERVER}:/backup/waterms/database/
fi

# 上传当前使用的数据库（如果备份不存在）
if [ -f "Service_WaterManage/backend/waterms.db" ]; then
    echo "  → 上传当前水站数据库..."
    scp Service_WaterManage/backend/waterms.db ${SERVER}:/backup/waterms/database/waterms_current.db
fi

if [ -f "Service_MeetingRoom/backend/meeting.db" ]; then
    echo "  → 上传当前会议室数据库..."
    scp Service_MeetingRoom/backend/meeting.db ${SERVER}:/backup/waterms/database/meeting_current.db
fi

echo -e "${GREEN}✅ 数据库上传完成${NC}"
echo ""

# ========================================
# 3. 上传SSL证书
# ========================================
echo -e "${CYAN}[3/5] 上传SSL证书...${NC}"
ssh ${SERVER} "mkdir -p /var/www/jhw-ai.com/ssl"

if [ -f "Draft/docs/SSL/24143096_jhw-ai.com_nginx/jhw-ai.com.pem" ]; then
    scp Draft/docs/SSL/24143096_jhw-ai.com_nginx/*.pem Draft/docs/SSL/24143096_jhw-ai.com_nginx/*.key ${SERVER}:/var/www/jhw-ai.com/ssl/ 2>/dev/null || true
    echo -e "${GREEN}✅ SSL证书已上传${NC}"
else
    echo -e "${YELLOW}⚠️  跳过SSL证书${NC}"
fi
echo ""

# ========================================
# 4. 上传项目代码
# ========================================
echo -e "${CYAN}[4/5] 上传项目代码...${NC}"

# 创建目录
ssh ${SERVER} "mkdir -p /root/project/portal"
ssh ${SERVER} "mkdir -p /root/project/Service_WaterManage/{backend,frontend}"
ssh ${SERVER} "mkdir -p /root/project/Service_MeetingRoom/{backend,frontend}"

# 上传Portal首页
echo "  → 上传Portal首页..."
scp -r portal/* ${SERVER}:/root/project/portal/

# 上传水站后端
echo "  → 上传水站后端代码..."
scp -r Service_WaterManage/backend/* ${SERVER}:/root/project/Service_WaterManage/backend/

# 上传水站前端
echo "  → 上传水站前端代码..."
scp -r Service_WaterManage/frontend/* ${SERVER}:/root/project/Service_WaterManage/frontend/

# 上传会议室后端
if [ -d "Service_MeetingRoom/backend" ]; then
    echo "  → 上传会议室后端代码..."
    scp -r Service_MeetingRoom/backend/* ${SERVER}:/root/project/Service_MeetingRoom/backend/
fi

# 上传会议室前端
if [ -d "Service_MeetingRoom/frontend" ]; then
    echo "  → 上传会议室前端代码..."
    scp -r Service_MeetingRoom/frontend/* ${SERVER}:/root/project/Service_MeetingRoom/frontend/
fi

echo -e "${GREEN}✅ 代码上传完成${NC}"
echo ""

# ========================================
# 5. 执行部署
# ========================================
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}正在服务器上执行部署...${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

ssh ${SERVER} "bash /root/deploy_full.sh"

echo ""
echo -e "${GREEN}"
echo "╔══════════════════════════════════════════════════════╗"
echo "║          ✅ 部署成功！                               ║"
echo "╚══════════════════════════════════════════════════════╝"
echo -e "${NC}"
echo ""
echo -e "${CYAN}【访问地址】${NC}"
echo "  首页(Portal): http://${IP}/"
echo "  水站管理: http://${IP}/water/"
echo "  管理后台: http://${IP}/water-admin/admin.html"
echo "  会议室: http://${IP}/meeting/"
echo ""
echo -e "${CYAN}【测试账号】${NC}"
echo "  用户名: admin"
echo "  密码: admin123"
echo ""
echo -e "${CYAN}【数据已部署】${NC}"
echo "  ✅ 水站管理真实数据"
echo "  ✅ 会议室管理真实数据"
echo ""
echo -e "${YELLOW}【重要提醒】${NC}"
echo "  请立即登录管理后台修改密码！"
echo ""