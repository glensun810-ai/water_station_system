#!/bin/bash
# ============================================
# 本地执行 - 最终版（本地→服务器）
# ============================================

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

SERVER="root@120.76.156.83"
SERVER_IP="120.76.156.83"
DOMAIN="jhw-ai.com"

echo -e "${BLUE}"
echo "╔══════════════════════════════════════════════════════╗"
echo "║   自动部署 - 最终修复版                              ║"
echo "╚══════════════════════════════════════════════════════╝"
echo -e "${NC}"
echo ""

# 步骤1: 上传部署脚本
echo -e "${CYAN}[1/4] 上传部署脚本...${NC}"
scp deploy_centos_final.sh ${SERVER}:/root/
echo -e "${GREEN}✅ 部署脚本上传完成${NC}"
echo ""

# 步骤2: 上传数据库备份
echo -e "${CYAN}[2/4] 上传数据库备份...${NC}"
ssh ${SERVER} "mkdir -p /backup/waterms/database"
if [ -f "backups/database/waterms_20260404_152737.db" ]; then
    scp backups/database/*.db backups/database/*.md5 ${SERVER}:/backup/waterms/database/ 2>/dev/null || true
    echo -e "${GREEN}✅ 数据库备份上传完成${NC}"
else
    echo -e "${YELLOW}⚠️  跳过数据库备份${NC}"
fi
echo ""

# 步骤3: 上传SSL证书
echo -e "${CYAN}[3/4] 上传SSL证书...${NC}"
ssh ${SERVER} "mkdir -p /var/www/${DOMAIN}/ssl"
if [ -f "Draft/docs/SSL/24143096_jhw-ai.com_nginx/jhw-ai.com.pem" ]; then
    scp Draft/docs/SSL/24143096_jhw-ai.com_nginx/* ${SERVER}:/var/www/${DOMAIN}/ssl/
    echo -e "${GREEN}✅ SSL证书上传完成${NC}"
else
    echo -e "${YELLOW}⚠️  跳过SSL证书${NC}"
fi
echo ""

# 步骤4: 上传项目代码
echo -e "${CYAN}[4/4] 上传项目代码...${NC}"
ssh ${SERVER} "mkdir -p /root/project/Service_WaterManage/{backend,frontend}"
ssh ${SERVER} "mkdir -p /root/project/Service_MeetingRoom/{backend,frontend}"

echo "  上传水站后端..."
scp -r Service_WaterManage/backend/* ${SERVER}:/root/project/Service_WaterManage/backend/

echo "  上传水站前端..."
scp -r Service_WaterManage/frontend/* ${SERVER}:/root/project/Service_WaterManage/frontend/

echo "  上传会议室后端..."
scp -r Service_MeetingRoom/backend/* ${SERVER}:/root/project/Service_MeetingRoom/backend/ 2>/dev/null || true

echo "  上传会议室前端..."
scp -r Service_MeetingRoom/frontend/* ${SERVER}:/root/project/Service_MeetingRoom/frontend/

echo -e "${GREEN}✅ 项目代码上传完成${NC}"
echo ""

# 执行远程部署
echo -e "${YELLOW}========================================${NC}"
echo -e "${YELLOW}正在服务器上执行部署...${NC}"
echo -e "${YELLOW}========================================${NC}"
echo ""

ssh ${SERVER} "bash /root/deploy_centos_final.sh"

echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║          ✅ 部署成功！                               ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${CYAN}【访问链接】${NC}"
echo "  水站管理: http://${SERVER_IP}/water/"
echo "  管理后台: http://${SERVER_IP}/water-admin/admin.html"
echo "  会议室: http://${SERVER_IP}/meeting/"
echo ""
echo -e "${CYAN}【测试账号】${NC}"
echo "  用户名: admin"
echo "  密码: admin123"
echo ""