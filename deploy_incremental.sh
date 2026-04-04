#!/bin/bash
# ============================================
# 增量更新部署脚本 - 保护数据库（无rsync版本）
# ============================================

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
RED='\033[0;31m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[✅]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[⚠️]${NC} $1"; }
log_error() { echo -e "${RED}[❌]${NC} $1"; }
log_step() { echo -e "${CYAN}[STEP]${NC} $1"; }

DEPLOY_DIR="/var/www/jhw-ai.com"
BACKUP_DIR="/backup/waterms"
LOG_DIR="/var/log/waterms"
DATE=$(date +%Y%m%d_%H%M%S)

echo -e "${BLUE}"
echo "╔══════════════════════════════════════════════════════╗"
echo "║   增量更新部署 - 保护数据库安全                       ║"
echo "╚══════════════════════════════════════════════════════╝"
echo -e "${NC}"
echo "更新时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# ========================================
# 步骤1: 备份服务器数据库（安全措施）
# ========================================
log_step "【步骤1/6】备份服务器数据库..."

mkdir -p "${BACKUP_DIR}/database"

if [ -f "${DEPLOY_DIR}/backend/waterms.db" ]; then
    cp "${DEPLOY_DIR}/backend/waterms.db" "${BACKUP_DIR}/database/waterms_backup_${DATE}.db"
    log_success "水站数据库已备份"
fi

if [ -f "${DEPLOY_DIR}/backend/meeting.db" ]; then
    cp "${DEPLOY_DIR}/backend/meeting.db" "${BACKUP_DIR}/database/meeting_backup_${DATE}.db"
    log_success "会议室数据库已备份"
fi
echo ""

# ========================================
# 步骤2: 更新Portal首页
# ========================================
log_step "【步骤2/6】更新Portal首页..."

if [ -d "/root/project/portal" ]; then
    cp -r /root/project/portal/* "${DEPLOY_DIR}/portal/"
    log_success "Portal首页已更新"
fi
echo ""

# ========================================
# 步骤3: 更新后端代码（保护数据库）
# ========================================
log_step "【步骤3/6】更新后端代码（保护数据库）..."

if [ -d "/root/project/Service_WaterManage/backend" ]; then
    # 临时保存数据库文件
    TEMP_DIR="/tmp/db_backup_${DATE}"
    mkdir -p "$TEMP_DIR"
    
    if [ -f "${DEPLOY_DIR}/backend/waterms.db" ]; then
        cp "${DEPLOY_DIR}/backend/waterms.db" "${TEMP_DIR}/"
        log_info "临时保存水站数据库"
    fi
    
    if [ -f "${DEPLOY_DIR}/backend/meeting.db" ]; then
        cp "${DEPLOY_DIR}/backend/meeting.db" "${TEMP_DIR}/"
        log_info "临时保存会议室数据库"
    fi
    
    # 删除旧的Python文件（保留数据库和虚拟环境）
    cd "${DEPLOY_DIR}/backend"
    find . -maxdepth 1 -type f \( -name "*.py" -o -name "*.txt" -o -name "*.json" -o -name "*.md" \) -delete
    find . -maxdepth 1 -type d ! -name "." ! -name ".venv" ! -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    
    # 复制新代码（排除数据库文件）
    cd /root/project/Service_WaterManage/backend
    for item in *.py *.txt *.json *.md; do
        [ -f "$item" ] && cp "$item" "${DEPLOY_DIR}/backend/"
    done
    
    # 复制子目录（排除数据库文件）
    for dir in api config models routers utils; do
        if [ -d "$dir" ]; then
            mkdir -p "${DEPLOY_DIR}/backend/$dir"
            cp -r $dir/* "${DEPLOY_DIR}/backend/$dir/"
        fi
    done
    
    # 恢复数据库文件
    if [ -f "${TEMP_DIR}/waterms.db" ]; then
        cp "${TEMP_DIR}/waterms.db" "${DEPLOY_DIR}/backend/waterms.db"
        log_success "水站数据库已恢复（未覆盖）"
    fi
    
    if [ -f "${TEMP_DIR}/meeting.db" ]; then
        cp "${TEMP_DIR}/meeting.db" "${DEPLOY_DIR}/backend/meeting.db"
        log_success "会议室数据库已恢复（未覆盖）"
    fi
    
    # 清理临时文件
    rm -rf "$TEMP_DIR"
    
    log_success "后端代码已更新"
fi
echo ""

# ========================================
# 步骤4: 更新前端代码
# ========================================
log_step "【步骤4/6】更新前端代码..."

if [ -d "/root/project/Service_WaterManage/frontend" ]; then
    cp -r /root/project/Service_WaterManage/frontend/* "${DEPLOY_DIR}/water/"
    
    if [ -f "${DEPLOY_DIR}/water/admin.html" ]; then
        cp "${DEPLOY_DIR}/water/admin.html" "${DEPLOY_DIR}/water-admin/admin.html"
    fi
    log_success "水站前端已更新"
fi

if [ -d "/root/project/Service_MeetingRoom/frontend" ]; then
    cp -r /root/project/Service_MeetingRoom/frontend/* "${DEPLOY_DIR}/meeting/"
    
    if [ -f "${DEPLOY_DIR}/meeting/admin.html" ]; then
        cp "${DEPLOY_DIR}/meeting/admin.html" "${DEPLOY_DIR}/meeting-admin/admin.html"
    fi
    log_success "会议室前端已更新"
fi
echo ""

# ========================================
# 步骤5: 更新Python依赖
# ========================================
log_step "【步骤5/6】检查Python依赖..."

cd "${DEPLOY_DIR}/backend"

if [ -d ".venv" ]; then
    source .venv/bin/activate
    
    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt -q 2>/dev/null || pip install -r requirements.txt
        log_success "Python依赖已更新"
    fi
    
    deactivate
fi

cd - > /dev/null
echo ""

# ========================================
# 步骤6: 重启服务
# ========================================
log_step "【步骤6/6】重启服务..."

systemctl restart waterms
sleep 2
systemctl reload nginx

if curl -s http://127.0.0.1:8000/api/health 2>/dev/null | grep -q "healthy"; then
    log_success "API服务重启成功"
else
    log_warning "API服务可能未完全启动"
fi

echo ""

# ========================================
# 完成
# ========================================
echo -e "${GREEN}"
echo "╔══════════════════════════════════════════════════════╗"
echo "║          ✅ 增量更新完成！                            ║"
echo "╚══════════════════════════════════════════════════════╝"
echo -e "${NC}"
echo ""
echo -e "${CYAN}【更新内容】${NC}"
echo "  ✅ Portal首页"
echo "  ✅ 后端代码"
echo "  ✅ 前端代码"
echo "  ✅ Python依赖"
echo ""
echo -e "${CYAN}【数据保护】${NC}"
echo "  ✅ 水站数据库：未被覆盖"
echo "  ✅ 会议室数据库：未被覆盖"
echo "  ✅ 备份位置：${BACKUP_DIR}/database/"
echo ""
echo -e "${CYAN}【访问地址】${NC}"
echo "  首页: http://120.76.156.83/"
echo "  水站: http://120.76.156.83/water/"
echo "  会议室: http://120.76.156.83/meeting/"
echo ""
