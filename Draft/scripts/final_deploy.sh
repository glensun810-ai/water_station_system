#!/bin/bash
# 最终版一键部署脚本

set -e
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

SERVER="root@120.76.156.83"
SERVER_IP="120.76.156.83"

echo -e "${BLUE}╔══════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   一键部署 - 终极修复版                              ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════╝${NC}"
echo ""

# 上传部署脚本
echo -e "${CYAN}[1/4] 上传部署脚本...${NC}"
scp deploy_final_v2.sh ${SERVER}:/root/ && echo -e "${GREEN}✅ 完成${NC}" || exit 1
echo ""

# 上传数据库
echo -e "${CYAN}[2/4] 上传数据库...${NC}"
ssh ${SERVER} "mkdir -p /backup/waterms/database"
[ -f "backups/database/waterms_20260404_152737.db" ] && scp backups/database/*.db backups/database/*.md5 ${SERVER}:/backup/waterms/database/ 2>/dev/null || true
echo -e "${GREEN}✅ 完成${NC}"
echo ""

# 上传SSL
echo -e "${CYAN}[3/4] 上传SSL证书...${NC}"
ssh ${SERVER} "mkdir -p /var/www/jhw-ai.com/ssl"
[ -f "Draft/docs/SSL/24143096_jhw-ai.com_nginx/jhw-ai.com.pem" ] && scp Draft/docs/SSL/24143096_jhw-ai.com_nginx/* ${SERVER}:/var/www/jhw-ai.com/ssl/ 2>/dev/null || true
echo -e "${GREEN}✅ 完成${NC}"
echo ""

# 上传代码
echo -e "${CYAN}[4/4] 上传代码...${NC}"
ssh ${SERVER} "mkdir -p /root/project/Service_WaterManage/{backend,frontend} /root/project/Service_MeetingRoom/{backend,frontend}"
scp -r Service_WaterManage/backend/* ${SERVER}:/root/project/Service_WaterManage/backend/
scp -r Service_WaterManage/frontend/* ${SERVER}:/root/project/Service_WaterManage/frontend/
scp -r Service_MeetingRoom/backend/* ${SERVER}:/root/project/Service_MeetingRoom/backend/ 2>/dev/null || true
scp -r Service_MeetingRoom/frontend/* ${SERVER}:/root/project/Service_MeetingRoom/frontend/ 2>/dev/null || true
echo -e "${GREEN}✅ 完成${NC}"
echo ""

# 执行部署
echo -e "${YELLOW}正在服务器上部署...${NC}"
echo ""
ssh ${SERVER} "bash /root/deploy_final_v2.sh"

echo ""
echo -e "${GREEN}✅ 部署完成！${NC}"
echo ""
echo -e "${CYAN}访问地址:${NC}"
echo "  http://${SERVER_IP}/water/"
echo "  http://${SERVER_IP}/water-admin/admin.html"
echo "  http://${SERVER_IP}/meeting/"
echo ""
echo -e "${CYAN}测试账号:${NC} admin / admin123"
echo ""