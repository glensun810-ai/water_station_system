#!/bin/bash
# ============================================
# 增量部署 - 本地到服务器（不使用rsync）
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
echo "║   增量部署 - 更新代码，保护数据库                     ║"
echo "╚══════════════════════════════════════════════════════╝"
echo -e "${NC}"
echo ""

# 检查本地文件
echo -e "${CYAN}检查本地文件...${NC}"
[ ! -f "deploy_incremental.sh" ] && echo "❌ deploy_incremental.sh 不存在" && exit 1
[ ! -d "Service_WaterManage" ] && echo "❌ Service_WaterManage 不存在" && exit 1
echo -e "${GREEN}✅ 文件检查通过${NC}"
echo ""

# ========================================
# 1. 上传部署脚本
# ========================================
echo -e "${CYAN}[1/3] 上传部署脚本...${NC}"
scp deploy_incremental.sh ${SERVER}:/root/ && echo -e "${GREEN}✅ 完成${NC}" || exit 1
echo ""

# ========================================
# 2. 上传代码（排除数据库）
# ========================================
echo -e "${CYAN}[2/3] 上传最新代码...${NC}"

# 创建目录
ssh ${SERVER} "mkdir -p /root/project/portal"
ssh ${SERVER} "mkdir -p /root/project/Service_WaterManage/{backend,frontend}"
ssh ${SERVER} "mkdir -p /root/project/Service_MeetingRoom/{backend,frontend}"

# 上传Portal首页
echo "  → 上传Portal首页..."
scp -r portal/* ${SERVER}:/root/project/portal/

# 上传水站后端（使用tar打包，排除数据库）
echo "  → 上传水站后端代码..."
cd Service_WaterManage/backend
tar --exclude='*.db' --exclude='*.db-journal' --exclude='.venv' --exclude='__pycache__' \
    -czf /tmp/water_backend.tar.gz .
scp /tmp/water_backend.tar.gz ${SERVER}:/tmp/
ssh ${SERVER} "cd /root/project/Service_WaterManage/backend && tar -xzf /tmp/water_backend.tar.gz && rm /tmp/water_backend.tar.gz"
cd - > /dev/null

# 上传水站前端
echo "  → 上传水站前端代码..."
scp -r Service_WaterManage/frontend/* ${SERVER}:/root/project/Service_WaterManage/frontend/

# 上传会议室后端
if [ -d "Service_MeetingRoom/backend" ]; then
    echo "  → 上传会议室后端代码..."
    cd Service_MeetingRoom/backend
    tar --exclude='*.db' --exclude='*.db-journal' --exclude='.venv' --exclude='__pycache__' \
        -czf /tmp/meeting_backend.tar.gz .
    scp /tmp/meeting_backend.tar.gz ${SERVER}:/tmp/
    ssh ${SERVER} "cd /root/project/Service_MeetingRoom/backend && tar -xzf /tmp/meeting_backend.tar.gz && rm /tmp/meeting_backend.tar.gz"
    cd - > /dev/null
fi

# 上传会议室前端
if [ -d "Service_MeetingRoom/frontend" ]; then
    echo "  → 上传会议室前端代码..."
    scp -r Service_MeetingRoom/frontend/* ${SERVER}:/root/project/Service_MeetingRoom/frontend/
fi

echo -e "${GREEN}✅ 代码上传完成${NC}"
echo ""

# ========================================
# 3. 执行部署
# ========================================
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}正在服务器上执行增量更新...${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

ssh ${SERVER} "bash /root/deploy_incremental.sh"

echo ""
echo -e "${GREEN}"
echo "╔══════════════════════════════════════════════════════╗"
echo "║          ✅ 增量更新完成！                            ║"
echo "╚══════════════════════════════════════════════════════╝"
echo -e "${NC}"
echo ""
echo -e "${CYAN}【访问地址】${NC}"
echo "  首页(Portal): http://${IP}/"
echo "  水站管理: http://${IP}/water/"
echo "  会议室: http://${IP}/meeting/"
echo ""
echo -e "${CYAN}【数据安全】${NC}"
echo "  ✅ 服务器数据库未被覆盖"
echo "  ✅ 数据库已自动备份"
echo ""