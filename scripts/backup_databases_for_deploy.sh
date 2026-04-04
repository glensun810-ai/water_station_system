#!/bin/bash
# ============================================
# 真实数据库备份脚本 - 部署前安全备份
# ============================================
# 用途：在部署前备份真实的生产数据
# 执行时间：部署前必须执行
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
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKUP_DIR="${PROJECT_ROOT}/backups/database"
DATE=$(date +%Y%m%d_%H%M%S)

# 真实数据库文件
WATER_DB="${PROJECT_ROOT}/Service_WaterManage/backend/waterms.db"
MEETING_DB="${PROJECT_ROOT}/Service_MeetingRoom/backend/meeting.db"

echo -e "${BLUE}"
echo "========================================"
echo "  真实数据库备份 - 部署前准备"
echo "========================================"
echo -e "${NC}"

# 创建备份目录
mkdir -p "${BACKUP_DIR}"
log_info "备份目录: ${BACKUP_DIR}"

# 备份水站管理数据库
if [ -f "${WATER_DB}" ]; then
    log_info "备份水站管理数据库..."
    DB_SIZE=$(du -h "${WATER_DB}" | cut -f1)
    log_info "数据库大小: ${DB_SIZE}"
    
    BACKUP_FILE="${BACKUP_DIR}/waterms_${DATE}.db"
    cp "${WATER_DB}" "${BACKUP_FILE}"
    
    # 验证备份
    if [ -f "${BACKUP_FILE}" ]; then
        BACKUP_SIZE=$(du -h "${BACKUP_FILE}" | cut -f1)
        log_success "水站数据库备份完成: ${BACKUP_FILE} (${BACKUP_SIZE})"
        
        # 创建校验文件（macOS使用md5，Linux使用md5sum）
        if command -v md5sum &> /dev/null; then
            md5sum "${BACKUP_FILE}" > "${BACKUP_FILE}.md5"
        else
            md5 "${BACKUP_FILE}" > "${BACKUP_FILE}.md5"
        fi
        log_success "校验文件已生成: ${BACKUP_FILE}.md5"
    else
        log_error "水站数据库备份失败"
        exit 1
    fi
else
    log_warning "水站管理数据库文件不存在: ${WATER_DB}"
fi

# 备份会议室管理数据库
if [ -f "${MEETING_DB}" ]; then
    log_info "备份会议室管理数据库..."
    DB_SIZE=$(du -h "${MEETING_DB}" | cut -f1)
    log_info "数据库大小: ${DB_SIZE}"
    
    BACKUP_FILE="${BACKUP_DIR}/meeting_${DATE}.db"
    cp "${MEETING_DB}" "${BACKUP_FILE}"
    
    # 验证备份
    if [ -f "${BACKUP_FILE}" ]; then
        BACKUP_SIZE=$(du -h "${BACKUP_FILE}" | cut -f1)
        log_success "会议室数据库备份完成: ${BACKUP_FILE} (${BACKUP_SIZE})"
        
        # 创建校验文件（macOS使用md5，Linux使用md5sum）
        if command -v md5sum &> /dev/null; then
            md5sum "${BACKUP_FILE}" > "${BACKUP_FILE}.md5"
        else
            md5 "${BACKUP_FILE}" > "${BACKUP_FILE}.md5"
        fi
        log_success "校验文件已生成: ${BACKUP_FILE}.md5"
    else
        log_error "会议室数据库备份失败"
        exit 1
    fi
else
    log_warning "会议室管理数据库文件不存在: ${MEETING_DB}"
fi

# 生成备份清单
MANIFEST_FILE="${BACKUP_DIR}/backup_manifest_${DATE}.txt"
log_info "生成备份清单..."

cat > "${MANIFEST_FILE}" << EOF
========================================
数据库备份清单
========================================
备份时间: ${DATE}
备份目录: ${BACKUP_DIR}

水站管理数据库:
  源文件: ${WATER_DB}
  备份文件: waterms_${DATE}.db
  大小: $(du -h "${BACKUP_DIR}/waterms_${DATE}.db" 2>/dev/null | cut -f1 || echo "不存在")
  MD5: $(cat "${BACKUP_DIR}/waterms_${DATE}.db.md5" 2>/dev/null || echo "不存在")

会议室管理数据库:
  源文件: ${MEETING_DB}
  备份文件: meeting_${DATE}.db
  大小: $(du -h "${BACKUP_DIR}/meeting_${DATE}.db" 2>/dev/null | cut -f1 || echo "不存在")
  MD5: $(cat "${BACKUP_DIR}/meeting_${DATE}.db.md5" 2>/dev/null || echo "不存在")

========================================
注意事项:
1. 请妥善保管备份文件
2. 部署前请验证备份完整性
3. 部署后请保留备份文件至少30天
========================================
EOF

log_success "备份清单已生成: ${MANIFEST_FILE}"

# 显示备份文件列表
echo ""
log_info "当前备份文件列表:"
ls -lh "${BACKUP_DIR}" | tail -10

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  ✅ 数据库备份完成！${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${BLUE}备份文件位置:${NC}"
echo "  ${BACKUP_DIR}"
echo ""
echo -e "${BLUE}下一步操作:${NC}"
echo "  1. 验证备份文件完整性"
echo "  2. 将备份文件上传到服务器 /backup/waterms/database/"
echo "  3. 开始部署流程"
echo ""
echo -e "${YELLOW}重要提醒:${NC}"
echo "  请确保备份文件已安全保存后再开始部署！"
echo ""