#!/bin/bash
# ==========================================
# 灰度提升脚本：将灰度环境提升到生产环境
# ==========================================
#
# 功能：
# - 验证灰度环境正常运行
# - 备份生产环境
# - 停止生产环境服务
# - 切换灰度环境配置为生产环境配置
# - 重启服务
# - 验证生产环境
#
# 使用方法：
# ./promote-canary.sh           # 提升灰度到生产（需确认）
# ./promote-canary.sh --dry-run # 预演模式
# ==========================================

set -e

# 获取脚本目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 加载生产环境配置
source "${SCRIPT_DIR}/config.sh"
# 加载灰度环境配置（用于获取灰度环境信息）
source "${SCRIPT_DIR}/config-canary.sh"
source "${SCRIPT_DIR}/deploy-common.sh"

# ==========================================
# 参数解析
# ==========================================

DRY_RUN=false

while [[ $# -gt 0 ]]; do
    case $1 in
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
# 提升步骤
# ==========================================

verify_canary_before_promote() {
    log_header "步骤 1: 验证灰度环境"
    
    log_info "检查灰度环境服务状态..."
    
    local checks_passed=0
    local checks_total=4
    
    # 检查灰度后端进程
    echo -n "灰度后端进程: "
    local backend_running=$(ssh_exec_quiet "ps aux | grep 'uvicorn.*:${BACKEND_PORT}' | grep -v grep | wc -l")
    if [ "$backend_running" -gt 0 ]; then
        echo -e "${GREEN}OK${NC}"
        ((checks_passed++))
    else
        echo -e "${RED}FAILED${NC}"
    fi
    
    # 检查灰度 API 健康
    echo -n "灰度 API 健康: "
    if ssh_exec_quiet "curl -sf http://127.0.0.1:${BACKEND_PORT}/api/health > /dev/null 2>&1"; then
        echo -e "${GREEN}OK${NC}"
        ((checks_passed++))
    else
        echo -e "${RED}FAILED${NC}"
    fi
    
    # 检查灰度 HTTPS
    echo -n "灰度 HTTPS: "
    if curl -sfI "https://${CANARY_DOMAIN}/api/health" > /dev/null 2>&1; then
        echo -e "${GREEN}OK${NC}"
        ((checks_passed++))
    else
        echo -e "${RED}FAILED${NC}"
    fi
    
    # 检查灰度数据库
    echo -n "灰度数据库: "
    if ssh_exec_quiet "test -f '${SERVER_PROJECT_ROOT}/${BACKEND_DIR}/${CANARY_DB_NAME}'"; then
        echo -e "${GREEN}OK${NC}"
        ((checks_passed++))
    else
        echo -e "${RED}FAILED${NC}"
    fi
    
    echo ""
    if [ $checks_passed -lt $checks_total ]; then
        log_error "灰度环境验证失败 ($checks_passed/$checks_total)"
        log_error "请确保灰度环境正常运行后再提升"
        return 1
    fi
    
    log_success "灰度环境验证通过 ($checks_passed/$checks_total)"
}

backup_production() {
    log_header "步骤 2: 备份生产环境"
    
    if [ "$DRY_RUN" = true ]; then
        log_warn "预演模式：将备份生产环境"
        return 0
    fi
    
    local backup_timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_name="production-before-promote-${backup_timestamp}"
    
    log_info "创建生产环境备份: $backup_name"
    
    ssh_exec "
        # 创建备份目录
        mkdir -p /var/backups/${DOMAIN}
        
        # 备份项目目录
        if [ -d '${PRODUCTION_PROJECT_ROOT}' ]; then
            tar -czf /var/backups/${DOMAIN}/${backup_name}.tar.gz -C /var/www jhw-ai.com 2>/dev/null || true
            echo '项目目录已备份'
        fi
        
        # 备份数据库
        if [ -f '${PRODUCTION_PROJECT_ROOT}/${BACKEND_DIR}/${PRODUCTION_DB_NAME}' ]; then
            cp '${PRODUCTION_PROJECT_ROOT}/${BACKEND_DIR}/${PRODUCTION_DB_NAME}' /var/backups/${DOMAIN}/${backup_name}.db
            echo '数据库已备份'
        fi
    "
    
    log_success "生产环境备份完成"
}

stop_production() {
    log_header "步骤 3: 停止生产环境服务"
    
    if [ "$DRY_RUN" = true ]; then
        log_warn "预演模式：将停止生产环境后端服务（端口 8000）"
        return 0
    fi
    
    log_warn "⚠️  停止生产环境服务..."
    
    ssh_exec "
        # 停止生产环境后端（端口 8000）
        pkill -f 'uvicorn.*:8000' 2>/dev/null || true
        echo '生产环境后端已停止'
        
        sleep 2
        
        # 验证已停止
        if ps aux | grep 'uvicorn.*:8000' | grep -v grep > /dev/null 2>&1; then
            echo 'WARNING: 生产环境后端仍在运行'
            exit 1
        else
            echo '生产环境后端确认已停止'
        fi
    "
    
    log_success "生产环境服务已停止"
}

switch_config() {
    log_header "步骤 4: 切换配置"
    
    if [ "$DRY_RUN" = true ]; then
        log_warn "预演模式：将执行以下切换操作"
        log_info "1. 停止灰度环境后端（端口 ${BACKEND_PORT})"
        log_info "2. 复制灰度环境代码到生产环境"
        log_info "3. 复制灰度数据库到生产数据库"
        log_info "4. 配置生产环境后端使用端口 8000"
        log_info "5. 配置生产环境使用生产数据库"
        return 0
    fi
    
    log_info "切换灰度环境到生产环境配置..."
    
    # 读取生产环境配置（覆盖灰度配置）
    source "${SCRIPT_DIR}/config.sh"
    
    ssh_exec "
        # 停止灰度环境后端
        echo '停止灰度环境后端...'
        pkill -f 'uvicorn.*:${BACKEND_PORT}' 2>/dev/null || true
        sleep 2
        
        # 复制灰度环境代码到生产环境
        echo '复制灰度环境代码到生产环境...'
        rsync -a --exclude='*.db' --exclude='*.sqlite' --exclude='*.sqlite3' --exclude='__pycache__' --exclude='*.log' \
            '${SERVER_PROJECT_ROOT}/${BACKEND_DIR}/' '${PRODUCTION_PROJECT_ROOT}/${BACKEND_DIR}/' 2>/dev/null || true
        
        # 复制灰度数据库到生产数据库（备份后覆盖）
        echo '复制灰度数据库到生产数据库...'
        if [ -f '${SERVER_PROJECT_ROOT}/${BACKEND_DIR}/${CANARY_DB_NAME}' ]; then
            # 备份当前生产数据库（额外备份）
            cp '${PRODUCTION_PROJECT_ROOT}/${BACKEND_DIR}/${PRODUCTION_DB_NAME}' '${PRODUCTION_PROJECT_ROOT}/${BACKEND_DIR}/${PRODUCTION_DB_NAME}.pre_promote' 2>/dev/null || true
            
            # 复制灰度数据库到生产数据库
            cp '${SERVER_PROJECT_ROOT}/${BACKEND_DIR}/${CANARY_DB_NAME}' '${PRODUCTION_PROJECT_ROOT}/${BACKEND_DIR}/${PRODUCTION_DB_NAME}'
            chmod 644 '${PRODUCTION_PROJECT_ROOT}/${BACKEND_DIR}/${PRODUCTION_DB_NAME}'
        fi
        
        # 修改生产环境数据库配置（恢复使用生产数据库）
        echo '修改生产环境数据库配置...'
        cd ${PRODUCTION_PROJECT_ROOT}/${BACKEND_DIR}
        sed -i 's/${CANARY_DB_NAME}/${PRODUCTION_DB_NAME}/g' main.py 2>/dev/null || true
        if [ -f '.env' ]; then
            sed -i 's/${CANARY_DB_NAME}/${PRODUCTION_DB_NAME}/g' .env 2>/dev/null || true
        fi
        
        echo '配置切换完成'
    "
    
    log_success "配置切换完成"
}

start_production() {
    log_header "步骤 5: 启动生产环境服务"
    
    # 重新加载生产环境配置
    source "${SCRIPT_DIR}/config.sh"
    
    if [ "$DRY_RUN" = true ]; then
        log_warn "预演模式：将启动生产环境后端服务（端口 8000）"
        return 0
    fi
    
    log_info "启动生产环境后端..."
    
    ssh_exec "
        cd ${PRODUCTION_PROJECT_ROOT}/${BACKEND_DIR}
        
        source venv/bin/activate
        
        # 启动生产环境后端（端口 8000）
        nohup python -m uvicorn main:app --host 127.0.0.1 --port 8000 > /var/log/water-api.log 2>&1 &
        
        sleep 3
        
        if curl -sf http://127.0.0.1:8000/api/health > /dev/null 2>&1; then
            echo 'BACKEND_STARTED_OK'
        else
            echo 'BACKEND_STARTED_FAILED'
            cat /var/log/water-api.log
        fi
    "
    
    local result=$(ssh_exec_quiet "curl -sf http://127.0.0.1:8000/api/health")
    if [ -n "$result" ]; then
        log_success "生产环境后端启动成功"
    else
        log_error "生产环境后端启动失败"
        return 1
    fi
}

verify_production() {
    log_header "步骤 6: 验证生产环境"
    
    # 重新加载生产环境配置
    source "${SCRIPT_DIR}/config.sh"
    
    local checks_passed=0
    local checks_total=3
    
    echo ""
    log_info "验证生产环境..."
    
    echo -n "生产用户端: "
    if curl -sfI "https://${DOMAIN}${FRONTEND_USER_PATH}/" > /dev/null 2>&1; then
        echo -e "${GREEN}OK${NC}"
        ((checks_passed++))
    else
        echo -e "${RED}FAILED${NC}"
    fi
    
    echo -n "生产管理后台: "
    if curl -sfI "https://${DOMAIN}${FRONTEND_ADMIN_PATH}/" > /dev/null 2>&1; then
        echo -e "${GREEN}OK${NC}"
        ((checks_passed++))
    else
        echo -e "${RED}FAILED${NC}"
    fi
    
    echo -n "生产 API: "
    if curl -sf "https://${DOMAIN}/api/health" > /dev/null 2>&1; then
        echo -e "${GREEN}OK${NC}"
        ((checks_passed++))
    else
        echo -e "${RED}FAILED${NC}"
    fi
    
    echo ""
    if [ $checks_passed -eq $checks_total ]; then
        log_success "生产环境验证通过 ($checks_passed/$checks_total)"
    else
        log_warn "生产环境部分验证失败 ($checks_passed/$checks_total)"
        log_warn "请检查日志并手动验证"
    fi
}

cleanup_canary() {
    log_header "步骤 7: 清理灰度环境（可选）"
    
    if [ "$DRY_RUN" = true ]; then
        log_warn "预演模式：可选择清理灰度环境"
        return 0
    fi
    
    log_info "是否清理灰度环境？"
    log_warn "⚠️  清理将删除灰度环境所有文件"
    
    if confirm "清理灰度环境？"; then
        log_info "清理灰度环境..."
        
        ssh_exec "
            # 停止灰度后端（如果还在运行）
            pkill -f 'uvicorn.*:${BACKEND_PORT}' 2>/dev/null || true
            
            # 删除灰度环境文件
            rm -rf ${SERVER_PROJECT_ROOT}
            
            # 删除灰度 Nginx 配置
            rm -f /etc/nginx/sites-available/${CANARY_DOMAIN}
            rm -f /etc/nginx/sites-enabled/${CANARY_DOMAIN}
            rm -f /etc/aa_nginx/vhost/${CANARY_DOMAIN}.conf
            
            echo '灰度环境已清理'
        "
        
        restart_nginx
        
        log_success "灰度环境已清理"
    else
        log_info "保留灰度环境，可手动清理"
    fi
}

# ==========================================
# 主函数
# ==========================================

show_usage() {
    cat << EOF
用法: $0 [选项]

灰度提升选项:
    无参数          提升灰度环境到生产环境（需确认）
    --dry-run      预演模式，不实际执行
    --help         显示帮助信息

示例:
    $0                      # 提升灰度到生产（需确认）
    $0 --dry-run            # 预演模式

提升流程:
    1. 验证灰度环境正常运行
    2. 备份生产环境
    3. 停止生产环境服务
    4. 切换灰度配置到生产配置
    5. 启动生产环境服务
    6. 验证生产环境
    7. 清理灰度环境（可选）

⚠️  重要提示:
    - 提升操作会影响生产环境
    - 会自动备份生产环境
    - 建议先使用 --dry-run 预演
    - 确保灰度环境已充分验证
EOF
}

main() {
    echo ""
    echo -e "${MAGENTA}╔═══════════════════════════════════════════════════════╗${NC}"
    echo -e "${MAGENTA}║${NC}  ${BOLD}灰度提升脚本${NC}                                      ${MAGENTA}║${NC}"
    echo -e "${MAGENTA}║${NC}  操作：灰度环境 → 生产环境                    ${MAGENTA}║${NC}"
    echo -e "${MAGENTA}║${NC}  灰度域名: ${CANARY_DOMAIN}                       ${MAGENTA}║${NC}"
    echo -e "${MAGENTA}║${NC}  生产域名: ${DOMAIN}                               ${MAGENTA}║${NC}"
    echo -e "${MAGENTA}╚═══════════════════════════════════════════════════════╝${NC}"
    echo ""
    
    if [ "$DRY_RUN" = true ]; then
        log_warn "⚠️  预演模式：不会实际修改生产环境"
    else
        log_warn "⚠️  警告：此操作将影响生产环境！"
        log_warn "建议先使用 --dry-run 预演"
        
        if ! confirm "确认提升灰度环境到生产环境？"; then
            log_info "取消操作"
            exit 0
        fi
    fi
    
    verify_canary_before_promote || exit 1
    backup_production || exit 1
    stop_production || exit 1
    switch_config || exit 1
    start_production || exit 1
    verify_production
    cleanup_canary
    
    echo ""
    if [ "$DRY_RUN" = false ]; then
        log_success "🎉 灰度环境已成功提升到生产环境！"
        echo ""
        echo "访问地址:"
        echo -e "  ${GREEN}生产用户端:${NC}   https://${DOMAIN}${FRONTEND_USER_PATH}/"
        echo -e "  ${GREEN}生产管理后台:${NC} https://${DOMAIN}${FRONTEND_ADMIN_PATH}/"
        echo -e "  ${GREEN}生产 API:${NC}     https://${DOMAIN}/api/"
        echo ""
    else
        log_info "预演完成，使用不带参数的命令实际执行"
    fi
}

# 处理参数
if [[ "$1" == "help" ]] || [[ "$1" == "--help" ]] || [[ "$1" == "-h" ]]; then
    show_usage
else
    main
fi