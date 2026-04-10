#!/bin/bash
# ==========================================
# 回滚脚本
# ==========================================
#
# 功能：
# - 回滚灰度环境部署（恢复之前的灰度版本）
# - 回滚提升操作（恢复生产环境到提升前的状态）
#
# 使用方法：
# ./rollback-canary.sh canary        # 回滚灰度环境
# ./rollback-canary.sh production    # 回滚生产环境（提升后回滚）
# ./rollback-canary.sh --list        # 查看可用备份
# ./rollback-canary.sh --dry-run     # 预演模式
# ==========================================

set -e

# 获取脚本目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 加载配置
source "${SCRIPT_DIR}/config.sh"
source "${SCRIPT_DIR}/config-canary.sh"
source "${SCRIPT_DIR}/deploy-common.sh"

# ==========================================
# 参数解析
# ==========================================

ROLLBACK_TYPE=""
DRY_RUN=false

while [[ $# -gt 0 ]]; do
    case $1 in
        canary)
            ROLLBACK_TYPE="canary"
            shift
            ;;
        production)
            ROLLBACK_TYPE="production"
            shift
            ;;
        --list)
            ROLLBACK_TYPE="list"
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
# 回滚函数
# ==========================================

list_backups() {
    log_header "可用备份列表"
    
    echo -e "${CYAN}=== 灰度环境备份 ===${NC}"
    ssh_exec "
        ls -lh ${SERVER_PROJECT_ROOT}/${BACKEND_DIR}/${CANARY_DB_NAME}.backup* 2>/dev/null || echo '无备份'
    "
    
    echo ""
    echo -e "${CYAN}=== 生产环境备份 ===${NC}"
    ssh_exec "
        ls -lh /var/backups/${DOMAIN}/ | tail -10 || echo '无备份'
    "
}

rollback_canary() {
    log_header "回滚灰度环境"
    
    if [ "$DRY_RUN" = true ]; then
        log_warn "预演模式：将回滚灰度环境"
        return 0
    fi
    
    log_warn "⚠️  回滚灰度环境将恢复到之前的版本"
    
    if ! confirm "确认回滚灰度环境？"; then
        log_info "取消回滚"
        return 0
    fi
    
    # 检查灰度数据库备份
    local backup_files=$(ssh_exec_quiet "ls ${SERVER_PROJECT_ROOT}/${BACKEND_DIR}/${CANARY_DB_NAME}.backup* 2>/dev/null | head -1")
    
    if [ -n "$backup_files" ]; then
        log_info "找到灰度数据库备份: $backup_files"
        
        log_info "回滚灰度环境..."
        
        ssh_exec "
            cd ${SERVER_PROJECT_ROOT}/${BACKEND_DIR}
            
            # 停止灰度后端
            pkill -f 'uvicorn.*:${BACKEND_PORT}' 2>/dev/null || true
            sleep 2
            
            # 恢复灰度数据库
            if [ -f '${CANARY_DB_NAME}' ]; then
                echo '备份当前灰度数据库...'
                cp '${CANARY_DB_NAME}' '${CANARY_DB_NAME}.rollback_$(date +%Y%m%d_%H%M%S)'
            fi
            
            # 恢复到最近的备份
            latest_backup=\$(ls -t ${CANARY_DB_NAME}.backup* | head -1)
            if [ -n \"\$latest_backup\" ]; then
                echo '恢复灰度数据库: \$latest_backup'
                cp \"\$latest_backup\" '${CANARY_DB_NAME}'
                chmod 644 '${CANARY_DB_NAME}'
            fi
            
            echo '灰度数据库已回滚'
        "
        
        # 重启灰度后端
        log_info "重启灰度环境后端..."
        
        ssh_exec "
            cd ${SERVER_PROJECT_ROOT}/${BACKEND_DIR}
            
            source venv/bin/activate
            
            nohup python -m uvicorn main:app --host 127.0.0.1 --port ${BACKEND_PORT} > /var/log/${PROJECT_NAME}-api.log 2>&1 &
            
            sleep 3
            
            if curl -sf http://127.0.0.1:${BACKEND_PORT}/api/health > /dev/null 2>&1; then
                echo 'BACKEND_STARTED_OK'
            else
                echo 'BACKEND_STARTED_FAILED'
            fi
        "
        
        local result=$(ssh_exec_quiet "curl -sf http://127.0.0.1:${BACKEND_PORT}/api/health")
        if [ -n "$result" ]; then
            log_success "灰度环境已回滚并重启成功"
        else
            log_error "灰度环境重启失败，请检查日志"
        fi
    else
        log_warn "未找到灰度数据库备份"
        log_info "建议重新部署灰度环境: ./deploy-canary.sh deploy"
    fi
}

rollback_production() {
    log_header "回滚生产环境（提升后回滚）"
    
    if [ "$DRY_RUN" = true ]; log_warn "预演模式：将回滚生产环境到提升前的状态"
        return 0
    fi
    
    log_warn "⚠️  ⚠️  ⚠️  严重警告 ⚠️  ⚠️  ⚠️"
    log_warn "回滚生产环境将影响正在运行的生产服务！"
    log_warn "此操作将恢复到最近的提升前的备份"
    
    if ! confirm "⚠️  确认回滚生产环境？请输入 'yes' 确认"; then
        log_info "取消回滚"
        return 0
    fi
    
    # 查找最近的备份
    log_info "查找生产环境备份..."
    
    local backups=$(ssh_exec_quiet "ls -t /var/backups/${DOMAIN}/production-before-promote-*.tar.gz 2>/dev/null | head -1")
    
    if [ -z "$backups" ]; then
        log_error "未找到提升前的备份"
        log_info "可用备份:"
        ssh_exec "ls -lh /var/backups/${DOMAIN}/"
        return 1
    fi
    
    log_info "找到备份: $backups"
    
    if ! confirm "使用此备份回滚？"; then
        log_info "取消回滚"
        return 0
    fi
    
    log_warn "开始回滚生产环境..."
    
    # 停止生产环境后端
    ssh_exec "
        pkill -f 'uvicorn.*:8000' 2>/dev/null || true
        echo '生产环境后端已停止'
        sleep 2
    "
    
    # 恢复备份
    local backup_file=$(basename "$backups")
    local backup_timestamp=$(echo "$backup_file" | grep -oP '\d{8}_\d{6}')
    
    ssh_exec "
        cd /var/backups/${DOMAIN}
        
        echo '解压备份...'
        tar -xzf ${backup_file} -C /tmp/
        
        echo '恢复生产环境...'
        # 备份当前生产环境
        if [ -d '${PRODUCTION_PROJECT_ROOT}' ]; then
            mv '${PRODUCTION_PROJECT_ROOT}' '${PRODUCTION_PROJECT_ROOT}.rollback_current'
        fi
        
        # 恢复备份
        cp -r /tmp/jhw-ai.com '${PRODUCTION_PROJECT_ROOT}'
        
        # 恢复数据库
        if [ -f '${backup_file%.tar.gz}.db' ]; then
            cp '${backup_file%.tar.gz}.db' '${PRODUCTION_PROJECT_ROOT}/${BACKEND_DIR}/${PRODUCTION_DB_NAME}'
            chmod 644 '${PRODUCTION_PROJECT_ROOT}/${BACKEND_DIR}/${PRODUCTION_DB_NAME}'
        fi
        
        # 清理临时文件
        rm -rf /tmp/jhw-ai.com
        
        echo '生产环境已恢复'
    "
    
    # 重启生产环境后端
    log_info "重启生产环境后端..."
    
    ssh_exec "
        cd ${PRODUCTION_PROJECT_ROOT}/${BACKEND_DIR}
        
        source venv/bin/activate
        
        nohup python -m uvicorn main:app --host 127.0.0.1 --port 8000 > /var/log/water-api.log 2>&1 &
        
        sleep 3
        
        if curl -sf http://127.0.0.1:8000/api/health > /dev/null 2>&1; then
            echo 'BACKEND_STARTED_OK'
        else
            echo 'BACKEND_STARTED_FAILED'
        fi
    "
    
    local result=$(ssh_exec_quiet "curl -sf http://127.0.0.1:8000/api/health")
    if [ -n "$result" ]; then
        log_success "生产环境已回滚并重启成功"
        
        echo ""
        echo "访问地址:"
        echo -e "  ${GREEN}生产用户端:${NC}   https://${DOMAIN}${FRONTEND_USER_PATH}/"
        echo -e "  ${GREEN}生产管理后台:${NC} https://${DOMAIN}${FRONTEND_ADMIN_PATH}/"
        echo -e "  ${GREEN}生产 API:${NC}     https://${DOMAIN}/api/"
    else
        log_error "生产环境重启失败，请检查日志"
        log_error "可手动检查: ssh root@${SERVER_HOST}"
    fi
}

# ==========================================
# 主函数
# ==========================================

show_usage() {
    cat << EOF
用法: $0 <回滚类型> [选项]

回滚类型:
    canary          回滚灰度环境（恢复灰度数据库）
    production      回滚生产环境（提升后回滚到提升前的备份）
    --list         查看可用备份列表

选项:
    --dry-run      预演模式，不实际执行

示例:
    $0 canary                  # 回滚灰度环境
    $0 production              # 回滚生产环境
    $0 --list                  # 查看备份
    $0 canary --dry-run        # 预演回滚灰度

说明:
    - canary 回滚: 恢复灰度数据库到最近的备份
    - production 回滚: 恢复生产环境到提升前的备份
    - 建议先使用 --dry-run 预演
    - production 回滚会影响生产服务，请谨慎操作
EOF
}

main() {
    if [ -z "$ROLLBACK_TYPE" ]; then
        log_error "请指定回滚类型"
        show_usage
        exit 1
    fi
    
    echo ""
    echo -e "${MAGENTA}╔═══════════════════════════════════════════════════════╗${NC}"
    echo -e "${MAGENTA}║${NC}  ${BOLD}回滚脚本${NC}                                          ${MAGENTA}║${NC}"
    echo -e "${MAGENTA}║${NC}  回滚类型: ${ROLLBACK_TYPE}                              ${MAGENTA}║${NC}"
    echo -e "${MAGENTA}╚═══════════════════════════════════════════════════════╝${NC}"
    echo ""
    
    case "$ROLLBACK_TYPE" in
        canary)
            rollback_canary
            ;;
        production)
            rollback_production
            ;;
        list|--list)
            list_backups
            ;;
        *)
            log_error "未知回滚类型: $ROLLBACK_TYPE"
            show_usage
            exit 1
            ;;
    esac
}

main