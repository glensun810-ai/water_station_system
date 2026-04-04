#!/bin/bash
# ============================================
# 数据库恢复脚本 - 紧急数据恢复
# ============================================
# 用途：从备份恢复数据库
# 执行：在服务器上执行
# ⚠️ 警告：此操作会覆盖现有数据库，请谨慎使用
# ============================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[OK]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# 配置
BACKUP_DIR="/backup/waterms/database"
DB_DIR="/var/www/jhw-ai.com/backend"

echo -e "${RED}"
echo "========================================"
echo "  ⚠️  数据库恢复脚本  ⚠️"
echo "========================================"
echo -e "${NC}"
echo "⚠️  警告：此操作将覆盖现有数据库"
echo ""

# 检查备份目录
if [ ! -d "$BACKUP_DIR" ]; then
    log_error "备份目录不存在: $BACKUP_DIR"
    exit 1
fi

# 列出可用备份
log_info "可用的备份文件:"
echo ""
echo "水站管理数据库备份:"
ls -lht "${BACKUP_DIR}/waterms_"*.db 2>/dev/null | head -5 || echo "  无备份文件"
echo ""

echo "会议室管理数据库备份:"
ls -lht "${BACKUP_DIR}/meeting_"*.db 2>/dev/null | head -5 || echo "  无备份文件"
echo ""

# 选择要恢复的备份
read -p "请输入要恢复的水站备份文件名（例如：waterms_20260404_152737.db，输入skip跳过）: " WATER_BACKUP
read -p "请输入要恢复的会议室备份文件名（例如：meeting_20260404_152737.db，输入skip跳过）: " MEETING_BACKUP

if [ "$WATER_BACKUP" = "skip" ] && [ "$MEETING_BACKUP" = "skip" ]; then
    log_info "用户取消恢复操作"
    exit 0
fi

# 确认操作
echo ""
echo -e "${YELLOW}⚠️  即将执行以下恢复操作:${NC}"
[ "$WATER_BACKUP" != "skip" ] && echo "  水站数据库: ${WATER_BACKUP}"
[ "$MEETING_BACKUP" != "skip" ] && echo "  会议室数据库: ${MEETING_BACKUP}"
echo ""
read -p "确认执行恢复？此操作不可逆！(yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    log_info "用户取消恢复操作"
    exit 0
fi

echo ""
log_info "开始数据库恢复..."

# 停止服务
log_warning "停止API服务..."
systemctl stop waterms 2>/dev/null || pkill -f "uvicorn.*main:app" || true
sleep 2

# 恢复水站数据库
if [ "$WATER_BACKUP" != "skip" ]; then
    if [ -f "${BACKUP_DIR}/${WATER_BACKUP}" ]; then
        log_info "恢复水站数据库..."
        
        # 备份当前数据库
        if [ -f "${DB_DIR}/waterms.db" ]; then
            CURRENT_BACKUP="waterms_before_restore_$(date +%Y%m%d_%H%M%S).db"
            cp "${DB_DIR}/waterms.db" "${BACKUP_DIR}/${CURRENT_BACKUP}"
            log_info "当前数据库已备份: ${CURRENT_BACKUP}"
        fi
        
        # 恢复数据库
        cp "${BACKUP_DIR}/${WATER_BACKUP}" "${DB_DIR}/waterms.db"
        
        # 验证MD5
        if [ -f "${BACKUP_DIR}/${WATER_BACKUP}.md5" ]; then
            RESTORED_MD5=$(md5sum "${DB_DIR}/waterms.db" | cut -d' ' -f1)
            ORIGINAL_MD5=$(cut -d' ' -f1 "${BACKUP_DIR}/${WATER_BACKUP}.md5")
            
            if [ "$RESTORED_MD5" = "$ORIGINAL_MD5" ]; then
                log_success "水站数据库恢复成功，MD5校验通过"
            else
                log_error "水站数据库MD5校验失败！"
                log_warning "请检查数据完整性"
            fi
        else
            log_success "水站数据库恢复成功"
        fi
        
        # 验证数据库完整性
        DB_CHECK=$(sqlite3 "${DB_DIR}/waterms.db" "PRAGMA integrity_check;" 2>&1)
        if [ "$DB_CHECK" = "ok" ]; then
            log_success "水站数据库完整性验证通过"
        else
            log_error "水站数据库完整性验证失败: $DB_CHECK"
        fi
    else
        log_error "备份文件不存在: ${BACKUP_DIR}/${WATER_BACKUP}"
    fi
fi

# 恢复会议室数据库
if [ "$MEETING_BACKUP" != "skip" ]; then
    if [ -f "${BACKUP_DIR}/${MEETING_BACKUP}" ]; then
        log_info "恢复会议室数据库..."
        
        # 备份当前数据库
        if [ -f "${DB_DIR}/meeting.db" ]; then
            CURRENT_BACKUP="meeting_before_restore_$(date +%Y%m%d_%H%M%S).db"
            cp "${DB_DIR}/meeting.db" "${BACKUP_DIR}/${CURRENT_BACKUP}"
            log_info "当前数据库已备份: ${CURRENT_BACKUP}"
        fi
        
        # 恢复数据库
        cp "${BACKUP_DIR}/${MEETING_BACKUP}" "${DB_DIR}/meeting.db"
        
        # 验证MD5
        if [ -f "${BACKUP_DIR}/${MEETING_BACKUP}.md5" ]; then
            RESTORED_MD5=$(md5sum "${DB_DIR}/meeting.db" | cut -d' ' -f1)
            ORIGINAL_MD5=$(cut -d' ' -f1 "${BACKUP_DIR}/${MEETING_BACKUP}.md5")
            
            if [ "$RESTORED_MD5" = "$ORIGINAL_MD5" ]; then
                log_success "会议室数据库恢复成功，MD5校验通过"
            else
                log_error "会议室数据库MD5校验失败！"
                log_warning "请检查数据完整性"
            fi
        else
            log_success "会议室数据库恢复成功"
        fi
        
        # 验证数据库完整性
        DB_CHECK=$(sqlite3 "${DB_DIR}/meeting.db" "PRAGMA integrity_check;" 2>&1)
        if [ "$DB_CHECK" = "ok" ]; then
            log_success "会议室数据库完整性验证通过"
        else
            log_error "会议室数据库完整性验证失败: $DB_CHECK"
        fi
    else
        log_error "备份文件不存在: ${BACKUP_DIR}/${MEETING_BACKUP}"
    fi
fi

# 重启服务
log_info "重启API服务..."
systemctl start waterms 2>/dev/null || {
    log_warning "使用nohup启动服务..."
    cd "${DB_DIR}"
    nohup python -m uvicorn main:app --host 127.0.0.1 --port 8000 > /var/log/waterms/waterms.log 2>&1 &
}

sleep 3

# 验证服务
log_info "验证服务状态..."
if curl -s http://127.0.0.1:8000/api/health | grep -q "healthy"; then
    log_success "API服务恢复正常"
else
    log_warning "API服务可能未完全启动，请手动检查"
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  ✅ 数据库恢复完成${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
log_info "建议执行以下操作:"
echo "  1. 测试前端功能是否正常"
echo "  2. 检查数据完整性"
echo "  3. 查看服务日志: tail -f /var/log/waterms/waterms.log"
echo ""