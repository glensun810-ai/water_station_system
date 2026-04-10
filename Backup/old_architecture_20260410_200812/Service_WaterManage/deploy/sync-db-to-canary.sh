#!/bin/bash
# ==========================================
# 数据库同步脚本：从生产环境同步到灰度环境
# ==========================================
#
# 功能：
# - 从生产环境复制最新数据库到灰度环境
# - 可随时重新同步，不影响生产环境
# - 支持增量同步和完整覆盖
#
# 使用方法：
# ./sync-db-to-canary.sh              # 同步数据库
# ./sync-db-to-canary.sh --force      # 强制覆盖灰度数据库
# ./sync-db-to-canary.sh --dry-run    # 预演模式，不实际执行
# ==========================================

set -e

# 获取脚本目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 加载配置
source "${SCRIPT_DIR}/config-canary.sh"
source "${SCRIPT_DIR}/deploy-common.sh"

# ==========================================
# 参数解析
# ==========================================

FORCE_MODE=false
DRY_RUN=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --force)
            FORCE_MODE=true
            shift
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        *)
            shift
            ;;
    esac
done

# ==========================================
# 同步函数
# ==========================================

sync_database() {
    log_header "同步生产数据库到灰度环境"
    
    if [ "$DRY_RUN" = true ]; then
        log_warn "⚠️  预演模式：不会实际修改文件"
    fi
    
    # 检查生产数据库
    log_info "检查生产数据库..."
    local prod_db_exists=$(ssh_exec_quiet "test -f '${PRODUCTION_PROJECT_ROOT}/${BACKEND_DIR}/${PRODUCTION_DB_NAME}' && echo 'yes' || echo 'no'")
    
    if [ "$prod_db_exists" = "no" ]; then
        log_error "生产数据库不存在: ${PRODUCTION_PROJECT_ROOT}/${BACKEND_DIR}/${PRODUCTION_DB_NAME}"
        exit 1
    fi
    
    # 获取生产数据库信息
    local prod_db_size=$(ssh_exec_quiet "ls -lh '${PRODUCTION_PROJECT_ROOT}/${BACKEND_DIR}/${PRODUCTION_DB_NAME}' | awk '{print \$5}'")
    local prod_db_mtime=$(ssh_exec_quiet "stat -c '%y' '${PRODUCTION_PROJECT_ROOT}/${BACKEND_DIR}/${PRODUCTION_DB_NAME}' | cut -d' ' -f1,2 | cut -d'.' -f1")
    
    log_success "生产数据库信息:"
    log_info "  路径: ${PRODUCTION_PROJECT_ROOT}/${BACKEND_DIR}/${PRODUCTION_DB_NAME}"
    log_info "  大小: $prod_db_size"
    log_info "  最后修改: $prod_db_mtime"
    
    # 检查灰度数据库
    log_info "检查灰度数据库..."
    local canary_db_exists=$(ssh_exec_quiet "test -f '${SERVER_PROJECT_ROOT}/${BACKEND_DIR}/${CANARY_DB_NAME}' && echo 'yes' || echo 'no'")
    
    if [ "$canary_db_exists" = "yes" ]; then
        local canary_db_size=$(ssh_exec_quiet "ls -lh '${SERVER_PROJECT_ROOT}/${BACKEND_DIR}/${CANARY_DB_NAME}' | awk '{print \$5}'")
        local canary_db_mtime=$(ssh_exec_quiet "stat -c '%y' '${SERVER_PROJECT_ROOT}/${BACKEND_DIR}/${CANARY_DB_NAME}' | cut -d' ' -f1,2 | cut -d'.' -f1")
        
        log_info "灰度数据库已存在:"
        log_info "  路径: ${SERVER_PROJECT_ROOT}/${BACKEND_DIR}/${CANARY_DB_NAME}"
        log_info "  大小: $canary_db_size"
        log_info "  最后修改: $canary_db_mtime"
        
        if [ "$FORCE_MODE" = false ]; then
            log_warn "灰度数据库已存在，是否覆盖？"
            if ! confirm "覆盖灰度数据库？"; then
                log_info "取消同步"
                return 0
            fi
        fi
    else
        log_info "灰度数据库不存在，将创建新数据库"
    fi
    
    # 执行同步
    if [ "$DRY_RUN" = false ]; then
        log_info "开始同步..."
        
        # 创建灰度目录
        ensure_dir "${SERVER_PROJECT_ROOT}/${BACKEND_DIR}"
        
        # 备份现有灰度数据库（如果存在）
        if [ "$canary_db_exists" = "yes" ]; then
            local backup_timestamp=$(date +%Y%m%d_%H%M%S)
            ssh_exec "
                echo '备份现有灰度数据库...'
                cp '${SERVER_PROJECT_ROOT}/${BACKEND_DIR}/${CANARY_DB_NAME}' '${SERVER_PROJECT_ROOT}/${BACKEND_DIR}/${CANARY_DB_NAME}.backup_${backup_timestamp}'
                echo '备份完成: ${CANARY_DB_NAME}.backup_${backup_timestamp}'
            "
        fi
        
        # 复制数据库
        ssh_exec "
            echo '复制生产数据库到灰度环境...'
            cp '${PRODUCTION_PROJECT_ROOT}/${BACKEND_DIR}/${PRODUCTION_DB_NAME}' '${SERVER_PROJECT_ROOT}/${BACKEND_DIR}/${CANARY_DB_NAME}'
            chmod 644 '${SERVER_PROJECT_ROOT}/${BACKEND_DIR}/${CANARY_DB_NAME}'
            echo '数据库复制完成'
        "
        
        # 验证同步
        local new_canary_db_size=$(ssh_exec_quiet "ls -lh '${SERVER_PROJECT_ROOT}/${BACKEND_DIR}/${CANARY_DB_NAME}' | awk '{print \$5}'")
        log_success "灰度数据库已更新，大小: $new_canary_db_size"
        
        # 检查数据库完整性
        log_info "验证数据库完整性..."
        ssh_exec "
            cd ${SERVER_PROJECT_ROOT}/${BACKEND_DIR}
            python3 -c \"import sqlite3; conn = sqlite3.connect('${CANARY_DB_NAME}'); print('数据库验证成功，表数量:', len(conn.execute('SELECT name FROM sqlite_master WHERE type=\\\"table\\\"').fetchall())); conn.close()\" || echo '数据库验证失败'
        "
    else
        log_warn "预演模式：以下操作将被执行"
        log_info "1. 备份现有灰度数据库（如果存在）"
        log_info "2. 复制 ${PRODUCTION_PROJECT_ROOT}/${BACKEND_DIR}/${PRODUCTION_DB_NAME}"
        log_info "3. 到 ${SERVER_PROJECT_ROOT}/${BACKEND_DIR}/${CANARY_DB_NAME}"
        log_info "4. 设置文件权限为 644"
    fi
    
    log_success "同步完成"
}

show_db_comparison() {
    log_header "数据库对比"
    
    echo -e "${CYAN}生产环境数据库:${NC}"
    ssh_exec "
        ls -lh ${PRODUCTION_PROJECT_ROOT}/${BACKEND_DIR}/${PRODUCTION_DB_NAME} 2>/dev/null || echo '不存在'
    "
    
    echo ""
    echo -e "${CYAN}灰度环境数据库:${NC}"
    ssh_exec "
        ls -lh ${SERVER_PROJECT_ROOT}/${BACKEND_DIR}/${CANARY_DB_NAME} 2>/dev/null || echo '不存在'
    "
    
    echo ""
    echo -e "${CYAN}灰度数据库备份:${NC}"
    ssh_exec "
        ls -lh ${SERVER_PROJECT_ROOT}/${BACKEND_DIR}/${CANARY_DB_NAME}.backup* 2>/dev/null || echo '无备份'
    "
}

# ==========================================
# 主函数
# ==========================================

show_usage() {
    cat << EOF
用法: $0 [选项]

数据库同步选项:
    无参数          同步生产数据库到灰度环境（需确认）
    --force        强制覆盖灰度数据库，无需确认
    --dry-run      预演模式，不实际执行
    --compare      查看数据库对比信息
    --help         显示帮助信息

示例:
    $0                      # 同步数据库（需确认）
    $0 --force              # 强制覆盖
    $0 --dry-run            # 预演模式
    $0 --compare            # 查看数据库对比

说明:
    - 同步操作不影响生产数据库
    - 灰度数据库使用独立文件，不影响生产环境
    - 每次同步前会自动备份现有灰度数据库
EOF
}

main() {
    local mode="${1:-sync}"
    
    echo ""
    echo -e "${MAGENTA}╔═══════════════════════════════════════════════════════╗${NC}"
    echo -e "${MAGENTA}║${NC}  ${BOLD}数据库同步脚本${NC}                                  ${MAGENTA}║${NC}"
    echo -e "${MAGENTA}║${NC}  生产数据库: ${PRODUCTION_DB_NAME}                       ${MAGENTA}║${NC}"
    echo -e "${MAGENTA}║${NC}  灰度数据库: ${CANARY_DB_NAME}                         ${MAGENTA}║${NC}"
    echo -e "${MAGENTA}╚═══════════════════════════════════════════════════════╝${NC}"
    echo ""
    
    case "$mode" in
        sync|--sync)
            sync_database
            ;;
        --compare)
            show_db_comparison
            ;;
        help|--help|-h)
            show_usage
            ;;
        *)
            if [ "$mode" = "--force" ] || [ "$mode" = "--dry-run" ]; then
                sync_database
            else
                log_error "未知参数: $mode"
                show_usage
                exit 1
            fi
            ;;
    esac
}

# 处理参数
if [ $# -eq 0 ]; then
    main "sync"
else
    main "$@"
fi