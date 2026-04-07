#!/bin/bash
# Alibaba Cloud Linux 一键部署

set -e
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
NC='\033[0m'

SERVER="root@120.76.156.83"
IP="120.76.156.83"

echo -e "${CYAN}╔══════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║   Alibaba Cloud Linux 一键部署                       ║${NC}"
echo -e "${CYAN}╚══════════════════════════════════════════════════════╝${NC}"
echo ""

# 上传脚本
echo -e "${CYAN}[1/4] 上传部署脚本...${NC}"
scp deploy_alinux.sh ${SERVER}:/root/ && echo -e "${GREEN}✅${NC}" || exit 1
echo ""

# 上传数据库
echo -e "${CYAN}[2/4] 上传数据库...${NC}"
ssh ${SERVER} "mkdir -p /backup/waterms/database"
[ -f "backups/database/waterms_20260404_152737.db" ] && scp backups/database/*.db ${SERVER}:/backup/waterms/database/
echo -e "${GREEN}✅${NC}"
echo ""

# 上传SSL
echo -e "${CYAN}[3/4] 上传SSL证书...${NC}"
ssh ${SERVER} "mkdir -p /var/www/jhw-ai.com/ssl"
[ -f "Draft/docs/SSL/24143096_jhw-ai.com_nginx/jhw-ai.com.pem" ] && scp Draft/docs/SSL/24143096_jhw-ai.com_nginx/* ${SERVER}:/var/www/jhw-ai.com/ssl/
echo -e "${GREEN}✅${NC}"
echo ""

# 上传代码
echo -e "${CYAN}[4/4] 上传代码...${NC}"
ssh ${SERVER} "mkdir -p /root/project/Service_WaterManage/{backend,frontend} /root/project/Service_MeetingRoom/{backend,frontend}"
scp -r Service_WaterManage/backend/* ${SERVER}:/root/project/Service_WaterManage/backend/
scp -r Service_WaterManage/frontend/* ${SERVER}:/root/project/Service_WaterManage/frontend/
scp -r Service_MeetingRoom/backend/* ${SERVER}:/root/project/Service_MeetingRoom/backend/ 2>/dev/null || true
scp -r Service_MeetingRoom/frontend/* ${SERVER}:/root/project/Service_MeetingRoom/frontend/
echo -e "${GREEN}✅${NC}"
echo ""

# 执行部署
echo -e "${YELLOW}执行部署...${NC}"
ssh ${SERVER} "bash /root/deploy_alinux.sh"

echo ""
echo -e "${GREEN}✅ 部署完成${NC}"
echo ""
echo -e "${CYAN}访问地址:${NC}"
echo "  http://${IP}/water/"
echo "  http://${IP}/water-admin/admin.html"
echo ""
echo -e "${CYAN}账号: admin / admin123${NC}"