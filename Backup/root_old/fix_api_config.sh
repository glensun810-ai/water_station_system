#!/bin/bash
# ============================================
# 修复所有前端页面的API配置
# ============================================

GREEN='\033[0;32m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${BLUE}"
echo "╔══════════════════════════════════════════════════════╗"
echo "║   修复前端页面API配置                                 ║"
echo "╚══════════════════════════════════════════════════════╝"
echo -e "${NC}"
echo ""

# 复制统一配置文件到各个前端目录
echo -e "${CYAN}[1/3] 复制统一API配置文件...${NC}"

cp api-config.js Service_WaterManage/frontend/
cp api-config.js Service_MeetingRoom/frontend/

echo -e "${GREEN}✅ 配置文件已复制${NC}"
echo ""

# 修复水站管理前端
echo -e "${CYAN}[2/3] 修复水站管理前端API配置...${NC}"

# 修复index.html
sed -i.bak 's|const isLocalhost = window.location.hostname === '\''localhost'\'' || window.location.hostname === '\''127.0.0.1'\'';|const isLocalhost = window.location.hostname === '\''localhost'\'' || window.location.hostname === '\''127.0.0.1'\'' || /^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$/.test(window.location.hostname);|g' Service_WaterManage/frontend/index.html

sed -i.bak 's|const API_BASE = localStorage.getItem('\''API_BASE'\'') || (isLocalhost ? '\''http://localhost:8000/api'\'' : '\''https://jhw-ai.com/api'\'');|const API_BASE = `${window.location.protocol}//${window.location.hostname}/api`;|g' Service_WaterManage/frontend/index.html

# 修复admin.html
sed -i.bak 's|const isLocalhost = window.location.hostname === '\''localhost'\'' || window.location.hostname === '\''127.0.0.1'\'' || window.location.protocol === '\''file:'\'';|const isLocalhost = window.location.hostname === '\''localhost'\'' || window.location.hostname === '\''127.0.0.1'\'' || /^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$/.test(window.location.hostname);|g' Service_WaterManage/frontend/admin.html

sed -i.bak 's|const API_BASE = localStorage.getItem('\''API_BASE'\'') || (isLocalhost ? '\''http://localhost:8000/api'\'' : '\''https://jhw-ai.com/api'\'');|const API_BASE = `${window.location.protocol}//${window.location.hostname}/api`;|g' Service_WaterManage/frontend/admin.html

echo -e "${GREEN}✅ 水站管理前端已修复${NC}"
echo ""

# 修复会议室管理前端
echo -e "${CYAN}[3/3] 修复会议室管理前端API配置...${NC}"

# 修复index.html
sed -i.bak 's|const API_BASE = localStorage.getItem('\''API_BASE'\'') ||.*|const API_BASE = `${window.location.protocol}//${window.location.hostname}/api/meeting`;|g' Service_MeetingRoom/frontend/index.html

sed -i.bak 's|const WATER_API_BASE =.*|const WATER_API_BASE = `${window.location.protocol}//${window.location.hostname}/api`;|g' Service_MeetingRoom/frontend/index.html

# 修复admin.html
sed -i.bak 's|const API_BASE = '\''http://localhost:8000/api/meeting'\'';|const API_BASE = `${window.location.protocol}//${window.location.hostname}/api/meeting`;|g' Service_MeetingRoom/frontend/admin.html

sed -i.bak 's|const WATER_API_BASE = '\''http://localhost:8000/api'\'';|const WATER_API_BASE = `${window.location.protocol}//${window.location.hostname}/api`;|g' Service_MeetingRoom/frontend/admin.html

echo -e "${GREEN}✅ 会议室管理前端已修复${NC}"
echo ""

# 清理备份文件
rm -f Service_WaterManage/frontend/*.bak
rm -f Service_MeetingRoom/frontend/*.bak

echo -e "${GREEN}"
echo "╔══════════════════════════════════════════════════════╗"
echo "║          ✅ API配置修复完成！                         ║"
echo "╚══════════════════════════════════════════════════════╝"
echo -e "${NC}"
echo ""
echo -e "${CYAN}【修复内容】${NC}"
echo "  ✅ 水站管理用户端 - index.html"
echo "  ✅ 水站管理后台 - admin.html"
echo "  ✅ 会议室用户端 - index.html"
echo "  ✅ 会议室管理后台 - admin.html"
echo ""
echo -e "${CYAN}【支持访问方式】${NC}"
echo "  ✅ IP访问: http://120.76.156.83/water/"
echo "  ✅ HTTP域名: http://jhw-ai.com/meeting/"
echo "  ✅ HTTPS域名: https://jhw-ai.com/water/"
echo ""
echo -e "${CYAN}【下一步】${NC}"
echo "  执行增量部署: ./update.sh"
echo ""
