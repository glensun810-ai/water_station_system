#!/bin/bash
# ============================================================
# Phase 2 回滚脚本 - API 扩展回滚
# ============================================================
# 用途：回滚 Phase 2 的新增 API
# 风险等级：低（仅删除新增代码）
# ============================================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

# 检查参数
if [ "$1" == "--dry-run" ]; then
    DRY_RUN=true
    log_info "运行模式：DRY RUN（仅显示，不执行）"
else
    DRY_RUN=false
fi

log_warn "=========================================="
log_warn "Phase 2 回滚 - API 扩展回滚"
log_warn "=========================================="
log_warn "此操作将删除以下新增 API:"
log_warn "  - GET  /api/services/config"
log_warn "  - GET  /api/services/types"
log_warn "  - POST /api/services/check-availability"
log_warn "  - POST /api/services/book"
echo ""

if [ "$DRY_RUN" == "false" ]; then
    read -p "确认继续？(yes/no): " confirm
    if [ "$confirm" != "yes" ]; then
        log_info "已取消回滚操作"
        exit 0
    fi
fi

log_info "开始 Phase 2 回滚..."
echo ""

# Step 1: 删除 API 文件
log_info "Step 1: 删除 API 文件"
if [ "$DRY_RUN" == "false" ]; then
    rm -f backend/api_services.py
    log_info "已删除 backend/api_services.py"
else
    log_info "[DRY RUN] rm backend/api_services.py"
fi
echo ""

# Step 2: 从 main.py 移除 router 引用
log_info "Step 2: 从 main.py 移除 services router"
if [ "$DRY_RUN" == "false" ]; then
    # 备份 main.py
    cp backend/main.py backend/main.py.backup_phase2
    
    # 删除 router 导入和注册
    sed -i.bak '/from backend.api_services import router as services_router/d' backend/main.py
    sed -i.bak '/app.include_router(services_router)/d' backend/main.py
    
    # 清理备份文件
    rm -f backend/main.py.bak
    
    log_info "已从 main.py 移除 services router"
else
    log_info "[DRY RUN] 从 main.py 删除 services router 引用"
fi
echo ""

# Step 3: 验证回滚
log_info "Step 3: 验证回滚结果"
if [ "$DRY_RUN" == "false" ]; then
    if [ ! -f "backend/api_services.py" ]; then
        log_info "✅ API 文件已删除"
    else
        log_error "❌ API 文件未删除"
        exit 1
    fi
    
    if ! grep -q "services_router" backend/main.py; then
        log_info "✅ main.py 已清理"
    else
        log_error "❌ main.py 仍有 services_router 引用"
        exit 1
    fi
fi

echo ""
log_info "=========================================="
log_info "Phase 2 回滚完成！"
log_info "=========================================="
log_info "已删除/恢复:"
log_info "  ✅ backend/api_services.py"
log_info "  ✅ main.py 中的 router 引用"
echo ""
log_warn "注意：请重启服务以应用回滚"
log_warn "命令：pkill -f uvicorn && ./start_all.sh"
echo ""
