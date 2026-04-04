#!/bin/bash
# 最终一键部署脚本

set -e
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

SERVER="root@120.76.156.83"
SERVER_IP="120.76.156.83"

echo -e "${BLUE}"
echo "╔══════════════════════════════════════════════════════╗"
echo "║   最终一键部署脚本                                   ║"
echo "╚══════════════════════════════════════════════════════╝"
echo -e "${NC}"
echo ""

# 1. 上传脚本
echo -e "${CYAN}[1/4] 上传部署脚本...${NC}"
scp deploy_smart_v3.sh ${SERVER}:/root/ && echo -e "${GREEN}✅ 完成${NC}" || exit 1
echo ""

# 2. 上传数据库
echo -e "${CYAN}[2/4] 上传数据库备份...${NC}"
ssh ${SERVER} "mkdir -p /backup/waterms/database"
[ -f "backups/database/waterms_20260404_152737.db" ] && {
    scp backups/database/*.db backups/database/*.md5 ${SERVER}:/backup/waterms/database/ 2>/dev/null || true
    echo -e "${GREEN}✅ 完成${NC}"
} || echo -e "${YELLOW}⚠️  跳过${NC}"
echo ""

# 3. 上传SSL
echo -e "${CYAN}[3/4] 上传SSL证书...${NC}"
ssh ${SERVER} "mkdir -p /var/www/jhw-ai.com/ssl"
[ -f "Draft/docs/SSL/24143096_jhw-ai.com_nginx/jhw-ai.com.pem" ] && {
    scp Draft/docs/SSL/24143096_jhw-ai.com_nginx/* ${SERVER}:/var/www/jhw-ai.com/ssl/ 2>/dev/null || true
    echo -e "${GREEN}✅ 完成${NC}"
} || echo -e "${YELLOW}⚠️  跳过${NC}"
echo ""

# 4. 上传代码
echo -e "${CYAN}[4/4] 上传项目代码...${NC}"
ssh ${SERVER} "mkdir -p /root/project/Service_WaterManage/{backend,frontend}"
ssh ${SERVER} "mkdir -p /root/project/Service_MeetingRoom/{backend,frontend}"

echo "  → 水站后端"
scp -r Service_WaterManage/backend/* ${SERVER}:/root/project/Service_WaterManage/backend/

echo "  → 水站前端"
scp -r Service_WaterManage/frontend/* ${SERVER}:/root/project/Service_WaterManage/frontend/

echo "  → 会议室后端"
scp -r Service_MeetingRoom/backend/* ${SERVER}:/root/project/Service_MeetingRoom/backend/ 2>/dev/null || true

echo "  → 会议室前端"
scp -r Service_MeetingRoom/frontend/* ${SERVER}:/root/project/Service_MeetingRoom/frontend/

echo -e "${GREEN}✅ 完成${NC}"
echo ""

# 执行部署
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}正在服务器上执行部署...${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

ssh ${SERVER} "bash /root/deploy_smart_v3.sh"

echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║          ✅ 部署成功！                               ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${CYAN}访问链接:${NC}"
echo "  水站: http://${SERVER_IP}/water/"
echo "  后台: http://${SERVER_IP}/water-admin/admin.html"
echo "  会议室: http://${SERVER_IP}/meeting/"
echo ""
echo -e "${CYAN}账号: admin / admin123${NC}"
echo ""