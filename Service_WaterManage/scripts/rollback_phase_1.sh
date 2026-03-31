#!/bin/bash
# ============================================================
# Phase 1 回滚脚本 - 数据库扩展回滚
# ============================================================
# 用途：回滚 Phase 1 的数据库表扩展操作
# 风险等级：低（仅删除新增字段，不影响现有数据）
# ============================================================

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 配置
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-3306}"
DB_NAME="${DB_NAME:-waterms}"
DB_USER="${DB_USER:-root}"
DB_PASSWORD="${DB_PASSWORD:-}"

# 日志函数
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查参数
if [ "$1" == "--dry-run" ]; then
    DRY_RUN=true
    log_info "运行模式：DRY RUN（仅显示，不执行）"
else
    DRY_RUN=false
fi

# 提示确认
if [ "$DRY_RUN" == "false" ]; then
    log_warn "=========================================="
    log_warn "警告：即将执行数据库回滚操作！"
    log_warn "=========================================="
    log_warn "此操作将删除以下字段："
    log_warn "  - products.service_type"
    log_warn "  - products.resource_config"
    log_warn "  - products.booking_required"
    log_warn "  - products.advance_booking_days"
    log_warn "  - office_pickup.service_type"
    log_warn "  - office_pickup.time_slot"
    log_warn "  - office_pickup.actual_usage"
    echo ""
    read -p "确认继续？(yes/no): " confirm
    
    if [ "$confirm" != "yes" ]; then
        log_info "已取消回滚操作"
        exit 0
    fi
fi

# MySQL 命令函数
run_mysql() {
    local sql="$1"
    if [ "$DRY_RUN" == "true" ]; then
        log_info "[DRY RUN] $sql"
    else
        mysql -h"$DB_HOST" -P"$DB_PORT" -u"$DB_USER" -p"$DB_PASSWORD" "$DB_NAME" -e "$sql"
    fi
}

log_info "开始 Phase 1 回滚..."
echo ""

# Step 1: 备份当前数据（逻辑备份）
log_info "Step 1: 备份新增字段数据（如果需要保留）"
if [ "$DRY_RUN" == "false" ]; then
    BACKUP_FILE="backup_service_extension_$(date +%Y%m%d_%H%M%S).sql"
    mysqldump -h"$DB_HOST" -P"$DB_PORT" -u"$DB_USER" -p"$DB_PASSWORD" \
        --no-create-info \
        --where="service_type IS NOT NULL OR time_slot IS NOT NULL" \
        "$DB_NAME" products office_pickup > "$BACKUP_FILE" 2>/dev/null || true
    log_info "数据已备份到：$BACKUP_FILE"
fi
echo ""

# Step 2: 回滚 products 表
log_info "Step 2: 回滚 products 表扩展"

if [ "$DRY_RUN" == "false" ]; then
    # 先更新数据为默认值（安全做法）
    run_mysql "UPDATE products SET service_type = 'water' WHERE service_type IS NULL;"
    run_mysql "UPDATE products SET resource_config = NULL;"
    run_mysql "UPDATE products SET booking_required = 0;"
    run_mysql "UPDATE products SET advance_booking_days = 0;"
fi

# 删除字段
run_mysql "ALTER TABLE products DROP COLUMN IF EXISTS service_type;"
run_mysql "ALTER TABLE products DROP COLUMN IF EXISTS resource_config;"
run_mysql "ALTER TABLE products DROP COLUMN IF EXISTS booking_required;"
run_mysql "ALTER TABLE products DROP COLUMN IF EXISTS advance_booking_days;"

log_info "products 表回滚完成"
echo ""

# Step 3: 回滚 office_pickup 表
log_info "Step 3: 回滚 office_pickup 表扩展"

if [ "$DRY_RUN" == "false" ]; then
    # 先更新数据为默认值
    run_mysql "UPDATE office_pickup SET service_type = 'water' WHERE service_type IS NULL;"
    run_mysql "UPDATE office_pickup SET time_slot = NULL;"
    run_mysql "UPDATE office_pickup SET actual_usage = NULL;"
fi

# 删除字段
run_mysql "ALTER TABLE office_pickup DROP COLUMN IF EXISTS service_type;"
run_mysql "ALTER TABLE office_pickup DROP COLUMN IF EXISTS time_slot;"
run_mysql "ALTER TABLE office_pickup DROP COLUMN IF EXISTS actual_usage;"

log_info "office_pickup 表回滚完成"
echo ""

# Step 4: 验证回滚
log_info "Step 4: 验证回滚结果"

if [ "$DRY_RUN" == "false" ]; then
    # 检查字段是否已删除
    FIELDS_CHECK=$(mysql -h"$DB_HOST" -P"$DB_PORT" -u"$DB_USER" -p"$DB_PASSWORD" "$DB_NAME" \
        -e "SELECT COUNT(*) FROM information_schema.COLUMNS 
            WHERE TABLE_SCHEMA = '$DB_NAME' 
            AND TABLE_NAME IN ('products', 'office_pickup')
            AND COLUMN_NAME IN ('service_type', 'resource_config', 'booking_required', 
                               'advance_booking_days', 'time_slot', 'actual_usage');" \
        -sN)
    
    if [ "$FIELDS_CHECK" -eq 0 ]; then
        log_info "✅ 回滚成功：所有新增字段已删除"
    else
        log_error "❌ 回滚失败：仍有 $FIELDS_CHECK 个字段未删除"
        exit 1
    fi
fi

echo ""
log_info "=========================================="
log_info "Phase 1 回滚完成！"
log_info "=========================================="
log_info "已删除字段:"
log_info "  ✅ products.service_type"
log_info "  ✅ products.resource_config"
log_info "  ✅ products.booking_required"
log_info "  ✅ products.advance_booking_days"
log_info "  ✅ office_pickup.service_type"
log_info "  ✅ office_pickup.time_slot"
log_info "  ✅ office_pickup.actual_usage"
echo ""
log_warn "注意：请同步回滚代码到 Phase 1 之前的版本"
log_warn "命令：git revert <commit-hash>"
echo ""
