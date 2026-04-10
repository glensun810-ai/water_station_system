#!/bin/bash
# ==========================================
# 智能一键部署脚本
# ==========================================
#
# ⚠️  重要安全警告 ⚠️
# ==========================================
# 此脚本设计为：只更新代码文件，永不覆盖任何生产数据！
#
# 以下数据在任何情况下都受到保护，不会被覆盖：
#   ✓ 领水记录 (water_records)
#   ✓ 结算记录 (settlement_records)  
#   ✓ 库存数据 (inventory)
#   ✓ 办公室数据 (offices)
#   ✓ 用户数据 (users)
#   ✓ 所有 .db / .sqlite 数据库文件
#
# 部署策略：增量更新（rsync），只修改有变化的代码文件
# ==========================================

set -e

# 获取脚本目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 加载配置和函数
source "${SCRIPT_DIR}/config.sh"
source "${SCRIPT_DIR}/deploy-common.sh"

# ==========================================
# 部署步骤函数
# ==========================================

deploy_step_1_check() {
    log_header "步骤 1: 环境检查"
    
    # 检查必要命令
    check_command ssh || exit 1
    check_command scp || exit 1
    check_command curl || exit 1
    
    # 测试服务器连接
    check_ssh_connection || exit 1
    
    # 检查磁盘空间
    check_disk_space
    
    # ==========================================
    # 生产数据保护检查
    # ==========================================
    log_info "生产数据保护检查..."
    if [ "$PROTECT_PRODUCTION_DATA" = true ]; then
        log_success "生产数据保护已启用 (PROTECT_PRODUCTION_DATA=true)"
        
        # 列出受保护的文件模式
        log_info "受保护的数据类型："
        for pattern in "${PROTECTED_PATTERNS[@]}"; do
            log_info "  - $pattern"
        done
    else
        log_warn "⚠️  生产数据保护已禁用 (PROTECT_PRODUCTION_DATA=false)"
        log_warn "⚠️  建议启用以保护生产数据！"
    fi
    
    # 检查本地文件
    log_info "检查本地项目文件..."
    if [ ! -d "${LOCAL_PROJECT_ROOT}/${BACKEND_DIR}" ]; then
        log_error "后端目录不存在: ${LOCAL_PROJECT_ROOT}/${BACKEND_DIR}"
        exit 1
    fi
    
    if [ ! -d "${LOCAL_PROJECT_ROOT}/frontend" ]; then
        log_error "前端目录不存在"
        exit 1
    fi
    
    # 检查本地是否有数据库文件（不应该有）
    if [ -f "${LOCAL_PROJECT_ROOT}/${BACKEND_DIR}/waterms.db" ]; then
        log_warn "⚠️  本地存在数据库文件: ${LOCAL_PROJECT_ROOT}/${BACKEND_DIR}/waterms.db"
        log_warn "⚠️  部署时将排除此文件，不会覆盖服务器数据库"
    fi
    
    log_success "环境检查通过"
}

deploy_step_2_backup() {
    log_header "步骤 2: 安全检查与备份"
    
    # ==========================================
    # 安全检查：确保不覆盖生产数据的警告
    # ==========================================
    log_warn "=============================================="
    log_warn "  重要：生产环境数据保护机制已启用"
    log_warn "  以下数据在任何情况下都不会被覆盖："
    log_warn "    - 数据库文件 (waterms.db)"
    log_warn "    - 领水记录"
    log_warn "    - 结算记录"  
    log_warn "    - 库存数据"
    log_warn "    - 办公室数据"
    log_warn "    - 用户数据"
    log_warn "    - 所有 .db/.sqlite 文件"
    log_warn "=============================================="
    
    if [ "$AUTO_BACKUP" = true ]; then
        log_info "执行增量备份..."
        local backup_name="${PROJECT_NAME}-$(date +%Y%m%d%H%M%S)"
        backup_server "$backup_name"
        log_success "备份完成"
    else
        log_info "跳过备份 (AUTO_BACKUP=false)"
    fi
    
    # 额外验证：确认数据库存在
    log_info "验证生产数据..."
    local db_exists=$(ssh_exec_quiet "test -f '${SERVER_PROJECT_ROOT}/${BACKEND_DIR}/waterms.db' && echo 'yes' || echo 'no'")
    if [ "$db_exists" = "yes" ]; then
        local db_size=$(ssh_exec_quiet "ls -lh '${SERVER_PROJECT_ROOT}/${BACKEND_DIR}/waterms.db' | awk '{print \$5}'")
        log_success "生产数据库存在，大小: $db_size"
    else
        log_warn "未找到生产数据库，将使用新的空数据库"
    fi
}

deploy_step_3_upload_backend() {
    log_header "步骤 3: 上传后端"
    
    # ==========================================
    # 安全警告：禁止覆盖任何生产数据！
    # ==========================================
    log_warn "安全模式：只更新代码文件，不修改任何数据！"
    
    # 创建服务器目录
    ensure_dir "${SERVER_PROJECT_ROOT}"
    ensure_dir "${SERVER_PROJECT_ROOT}/${BACKEND_DIR}"
    
    # 检查服务器上是否存在数据库（生产数据）
    local db_exists=$(ssh_exec_quiet "test -f '${SERVER_PROJECT_ROOT}/${BACKEND_DIR}/waterms.db' && echo 'yes' || echo 'no'")
    if [ "$db_exists" = "yes" ]; then
        log_success "检测到生产数据库: ${SERVER_PROJECT_ROOT}/${BACKEND_DIR}/waterms.db"
        log_info "数据库将保持不变，不会被覆盖"
    fi
    
    # ==========================================
    # 关键：只上传代码文件，永不删除目录
    # 使用 rsync 增量更新，精确排除数据文件
    # ==========================================
    log_info "增量更新后端代码（排除所有数据文件）..."
    
    # 定义需要排除的内容（所有可能的数据文件）
    local exclude_patterns=(
        "*.db"           # SQLite 数据库
        "*.sqlite"      # SQLite 数据库
        "*.sqlite3"     # SQLite 数据库
        "__pycache__"   # Python 缓存
        "*.pyc"         # Python 编译文件
        "*.pyo"         # Python 编译文件
        ".pytest_cache" # 测试缓存
        "venv/"         # 虚拟环境（服务器上已存在）
        "*.log"         # 日志文件
        "uploads/"      # 上传的文件
        "*.env"         # 环境变量文件
        ".git/"         # Git 目录
    )
    
    # 构建 rsync 排除参数
    local rsync_exclude=""
    for pattern in "${exclude_patterns[@]}"; do
        rsync_exclude="${rsync_exclude} --exclude='${pattern}'"
    done
    
    # 检查服务器上是否有 rsync
    local server_has_rsync=$(ssh_exec_quiet "command -v rsync &>/dev/null && echo 'yes' || echo 'no'")
    
    if command -v rsync &>/dev/null && [ "$server_has_rsync" = "yes" ]; then
        # 使用 rsync 增量同步
        if [ -n "$SSH_KEY_PATH" ] && [ -f "$SSH_KEY_PATH" ]; then
            rsync -avz ${rsync_exclude} -e "ssh -i '$SSH_KEY_PATH' -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null" "${LOCAL_PROJECT_ROOT}/${BACKEND_DIR}/" "${SERVER_USER}@${SERVER_HOST}:${SERVER_PROJECT_ROOT}/${BACKEND_DIR}/"
        elif command -v sshpass &>/dev/null && [ -n "$SERVER_PASSWORD" ]; then
            rsync -avz ${rsync_exclude} -e "sshpass -p '$SERVER_PASSWORD' ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null" "${LOCAL_PROJECT_ROOT}/${BACKEND_DIR}/" "${SERVER_USER}@${SERVER_HOST}:${SERVER_PROJECT_ROOT}/${BACKEND_DIR}/"
        else
            rsync -avz ${rsync_exclude} -e "ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null" "${LOCAL_PROJECT_ROOT}/${BACKEND_DIR}/" "${SERVER_USER}@${SERVER_HOST}:${SERVER_PROJECT_ROOT}/${BACKEND_DIR}/"
        fi
    else
        # 如果 rsync 不可用，使用 tar 方式但更安全
        log_warn "rsync 不可用，使用 tar 方式上传"
        
        # 先tar到临时文件，再上传解压
        local temp_tar="/tmp/backend_code_$(date +%Y%m%d_%H%M%S).tar"
        (cd "${LOCAL_PROJECT_ROOT}/${BACKEND_DIR}" && tar --exclude='*.db' --exclude='*.sqlite' --exclude='*.sqlite3' --exclude='__pycache__' --exclude='venv' --exclude='*.log' --exclude='.git' -cf - .) > "$temp_tar"
        
        # 上传到服务器（追加到现有目录）
        scp_upload "$temp_tar" "/tmp/backend_code.tar"
        ssh_exec "cd ${SERVER_PROJECT_ROOT}/${BACKEND_DIR} && tar -xf /tmp/backend_code.tar --overwrite"
        ssh_exec "rm -f /tmp/backend_code.tar"
        rm -f "$temp_tar"
    fi
    
    # 验证数据库仍然存在
    local db_exists_after=$(ssh_exec_quiet "test -f '${SERVER_PROJECT_ROOT}/${BACKEND_DIR}/waterms.db' && echo 'yes' || echo 'no'")
    if [ "$db_exists_after" = "yes" ]; then
        log_success "数据库验证通过：生产数据完好"
    else
        log_error "数据库丢失！请立即检查服务器！"
        return 1
    fi
    
    # 确保虚拟环境存在（如果不存在则创建）
    log_info "检查/安装 Python 依赖..."
    ssh_exec "
        cd ${SERVER_PROJECT_ROOT}/${BACKEND_DIR}
        
        # 如果虚拟环境不存在，则创建
        if [ ! -d 'venv' ]; then
            echo '创建虚拟环境...'
            python${PYTHON_VERSION} -m venv venv 2>/dev/null || python3 -m venv venv 2>/dev/null || python -m venv venv
        fi
        
        # 激活虚拟环境
        source venv/bin/activate
        
        # 升级 pip
        pip install --upgrade pip -q
        
        # 安装依赖
        pip install -r requirements.txt -q
        
        echo 'Dependencies installed'
    "
    
    # 修复已知问题（只修改代码，不影响数据）
    log_info "修复已知问题..."
    ssh_exec "
        cd ${SERVER_PROJECT_ROOT}/${BACKEND_DIR}
        
        # 修复 main.py 前向引用问题
        sed -i 's/-> Optional\[User\]:/-> Optional[\"User\"]:/' main.py 2>/dev/null || true
        
        echo 'Fixes applied'
    "
    
    log_success "后端上传完成（生产数据完好）"
}

deploy_step_4_upload_frontend() {
    log_header "步骤 4: 上传前端"
    
    # 创建前端目录
    ensure_dir "${SERVER_PROJECT_ROOT}${FRONTEND_USER_PATH}"
    ensure_dir "${SERVER_PROJECT_ROOT}${FRONTEND_ADMIN_PATH}"
    
    # 上传前端文件
    log_info "上传前端文件..."
    
    for item in "${FRONTEND_FILES[@]}"; do
        local local_path="${item%%:*}"
        local remote_path="${item##*:}"
        local full_local_path="${LOCAL_PROJECT_ROOT}/${local_path}"
        
        if [ -f "$full_local_path" ]; then
            log_info "上传: $local_path -> $remote_path"
            scp_upload "$full_local_path" "${SERVER_PROJECT_ROOT}${remote_path}"
        else
            log_warn "文件不存在: $full_local_path"
        fi
    done
    
    # 修改前端 API 地址
    log_info "配置前端 API 地址..."
    local api_url="https://${DOMAIN}/api"
    
    ssh_exec "
        # 修改 index.html API 地址
        sed -i 's|http://localhost:8000/api|${api_url}|g' ${SERVER_PROJECT_ROOT}${FRONTEND_USER_PATH}/index.html 2>/dev/null || true
        sed -i 's|https://jhw-ai.com/api|${api_url}|g' ${SERVER_PROJECT_ROOT}${FRONTEND_USER_PATH}/index.html 2>/dev/null || true
        
        # 修改 admin.html API 地址
        sed -i 's|http://localhost:8000/api|${api_url}|g' ${SERVER_PROJECT_ROOT}${FRONTEND_ADMIN_PATH}/admin.html 2>/dev/null || true
        sed -i 's|https://jhw-ai.com/api|${api_url}|g' ${SERVER_PROJECT_ROOT}${FRONTEND_ADMIN_PATH}/admin.html 2>/dev/null || true
        
        # 修改 login.html API 地址
        sed -i 's|http://localhost:8000/api|${api_url}|g' ${SERVER_PROJECT_ROOT}${FRONTEND_ADMIN_PATH}/login.html 2>/dev/null || true
        sed -i 's|https://jhw-ai.com/api|${api_url}|g' ${SERVER_PROJECT_ROOT}${FRONTEND_ADMIN_PATH}/login.html 2>/dev/null || true
        
        # 修复跳转路径
        sed -i 's|\"admin.html\"|\"/water-admin/admin.html\"|g' ${SERVER_PROJECT_ROOT}${FRONTEND_ADMIN_PATH}/login.html 2>/dev/null || true
        sed -i \"s|'admin.html'|'/water-admin/admin.html'|g\" ${SERVER_PROJECT_ROOT}${FRONTEND_ADMIN_PATH}/login.html 2>/dev/null || true
        
        sed -i 's|\"login.html\"|\"/water-admin/login.html\"|g' ${SERVER_PROJECT_ROOT}${FRONTEND_ADMIN_PATH}/admin.html 2>/dev/null || true
        sed -i \"s|'login.html'|'/water-admin/login.html'|g\" ${SERVER_PROJECT_ROOT}${FRONTEND_ADMIN_PATH}/admin.html 2>/dev/null || true
        
        echo 'Frontend configured'
    "
    
    log_success "前端上传完成"
}

deploy_step_5_configure_nginx() {
    log_header "步骤 5: 配置 Nginx"
    
    # 检测 Nginx 类型
    local nginx_type=$(ssh_exec_quiet "which aa_nginx && echo 'aa_nginx' || (which nginx && echo 'nginx' || echo 'not_found')")
    
    if [ "$nginx_type" = "aa_nginx" ]; then
        log_info "检测到 aaPanel Nginx"
    elif [ "$nginx_type" = "nginx" ]; then
        log_info "检测到标准 Nginx"
    else
        log_warn "未检测到 Nginx，将使用标准配置"
        nginx_type="nginx"
    fi
    
    # 创建 Nginx 配置
    log_info "生成 Nginx 配置..."
    
    if [ "$nginx_type" = "aa_nginx" ]; then
        # aaPanel Nginx 配置
        ssh_exec "cat > /etc/aa_nginx/vhost/${DOMAIN}.conf << 'NGINX_EOF'
server {
    listen 80;
    server_name ${DOMAIN};
    return 301 https://\$server_name\$request_uri;
}

server {
    listen 443 ssl;
    server_name ${DOMAIN};

    ssl_certificate ${SSL_CERT_PATH};
    ssl_certificate_key ${SSL_KEY_PATH};

    ssl_session_timeout 1d;
    ssl_session_cache shared:SSL:50m;
    ssl_session_tickets off;

    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305;
    ssl_prefer_server_ciphers off;

    # 前端静态文件 - 用户端
    location ${FRONTEND_USER_PATH}/ {
        alias ${SERVER_PROJECT_ROOT}${FRONTEND_USER_PATH}/;
        index index.html;
        try_files \$uri \$uri/ ${FRONTEND_USER_PATH}/index.html;
    }

    # 前端静态文件 - 管理后台
    location ${FRONTEND_ADMIN_PATH}/ {
        alias ${SERVER_PROJECT_ROOT}${FRONTEND_ADMIN_PATH}/;
        index admin.html;
        try_files \$uri \$uri/ ${FRONTEND_ADMIN_PATH}/admin.html;
    }

    # API 反向代理
    location /api/ {
        proxy_pass http://127.0.0.1:${BACKEND_PORT}/api/;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection \"upgrade\";
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # 默认重定向
    location / {
        return 301 https://${DOMAIN}${FRONTEND_USER_PATH}/;
    }
}
NGINX_EOF"
    else
        # 标准 Nginx 配置
        ssh_exec "cat > /etc/nginx/sites-available/${DOMAIN} << 'NGINX_EOF'
server {
    listen 80;
    server_name ${DOMAIN};
    return 301 https://\$server_name\$request_uri;
}

server {
    listen 443 ssl;
    server_name ${DOMAIN};

    ssl_certificate ${SSL_CERT_PATH};
    ssl_certificate_key ${SSL_KEY_PATH};

    ssl_session_timeout 1d;
    ssl_session_cache shared:SSL:50m;
    ssl_session_tickets off;

    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305;
    ssl_prefer_server_ciphers off;

    # 前端静态文件 - 用户端
    location ${FRONTEND_USER_PATH}/ {
        alias ${SERVER_PROJECT_ROOT}${FRONTEND_USER_PATH}/;
        index index.html;
        try_files \$uri \$uri/ ${FRONTEND_USER_PATH}/index.html;
    }

    # 前端静态文件 - 管理后台
    location ${FRONTEND_ADMIN_PATH}/ {
        alias ${SERVER_PROJECT_ROOT}${FRONTEND_ADMIN_PATH}/;
        index admin.html;
        try_files \$uri \$uri/ ${FRONTEND_ADMIN_PATH}/admin.html;
    }

    # API 反向代理
    location /api/ {
        proxy_pass http://127.0.0.1:${BACKEND_PORT}/api/;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection \"upgrade\";
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # 默认重定向
    location / {
        return 301 https://${DOMAIN}${FRONTEND_USER_PATH}/;
    }
}
NGINX_EOF"

        # 启用配置（标准 Nginx）
        ssh_exec "
            mkdir -p /etc/nginx/sites-enabled
            ln -sf /etc/nginx/sites-available/${DOMAIN} /etc/nginx/sites-enabled/
        "
    fi
    
    # 重启 Nginx
    restart_nginx
    
    log_success "Nginx 配置完成"
}

deploy_step_6_configure_security_group() {
    log_header "步骤 6: 配置安全组（可选）"
    
    # 尝试配置阿里云安全组
    configure_aliyun_security_group
    
    log_success "安全组配置步骤完成"
}

deploy_step_7_start_backend() {
    log_header "步骤 7: 启动后端服务"
    
    restart_backend
    
    log_success "后端服务启动完成"
}

deploy_step_8_verify() {
    log_header "步骤 8: 验证部署"
    
    verify_deployment
}

deploy_step_9_cleanup() {
    log_header "步骤 9: 清理部署文件"
    
    # 清理服务器上的临时文件
    cleanup_deployment_artifacts
    
    log_success "清理完成"
}

# ==========================================
# 快捷命令
# ==========================================

cmd_status() {
    log_info "检查服务状态..."
    
    echo -e "${CYAN}=== Nginx ===${NC}"
    ssh_exec "ss -tlnp | grep -E '80|443' || netstat -tlnp | grep -E '80|443'"
    
    echo -e "${CYAN}=== 后端进程 ===${NC}"
    ssh_exec "ps aux | grep uvicorn | grep -v grep"
    
    echo -e "${CYAN}=== API 健康检查 ===${NC}"
    ssh_exec "curl -s http://127.0.0.1:${BACKEND_PORT}/api/health"
    
    echo -e "${CYAN}=== HTTPS 检查 ===${NC}"
    curl -sI "https://${DOMAIN}/api/health" | head -3
}

cmd_restart() {
    log_info "重启服务..."
    restart_backend
    restart_nginx
    verify_deployment
}

cmd_stop() {
    log_info "停止服务..."
    ssh_exec "pkill -f 'uvicorn main:app' || true"
    log_success "服务已停止"
}

cmd_logs() {
    log_info "查看后端日志..."
    ssh_exec "tail -50 /var/log/${PROJECT_NAME}-api.log"
}

cmd_shell() {
    log_info "连接到服务器..."
    if [ -n "$SSH_KEY_PATH" ] && [ -f "$SSH_KEY_PATH" ]; then
        ssh -i "$SSH_KEY_PATH" $SSH_OPTS -p ${SERVER_PORT:-22} ${SERVER_USER}@${SERVER_HOST}
    else
        ssh $SSH_OPTS -p ${SERVER_PORT:-22} ${SERVER_USER}@${SERVER_HOST}
    fi
}

cmd_backup() {
    log_info "创建手动备份..."
    local backup_name="${PROJECT_NAME}-manual-$(date +%Y%m%d%H%M%S)"
    backup_server "$backup_name"
    log_success "备份完成: $backup_name"
}

# ==========================================
# 主函数
# ==========================================

show_usage() {
    cat << EOF
用法: $0 <命令> [选项]

命令:
    deploy          执行完整部署流程
    status          查看服务状态
    restart         重启服务
    stop            停止服务
    logs            查看后端日志
    shell           SSH 连接到服务器
    backup          创建手动备份
    help            显示帮助信息

选项:
    --skip-backup   跳过备份执行部署
    --skip-sg       跳过安全组配置

示例:
    $0 deploy                  # 执行完整部署
    $0 deploy --skip-backup    # 跳过备份执行部署
    $0 status                  # 查看状态
    $0 restart                 # 重启服务
    $0 shell                   # SSH 到服务器
    $0 backup                  # 创建备份

EOF
}

main() {
    local command="${1:-deploy}"
    local skip_backup=false
    local skip_sg=false
    
    # 解析选项
    shift
    while [[ $# -gt 0 ]]; do
        case $1 in
            --skip-backup)
                skip_backup=true
                shift
                ;;
            --skip-sg)
                skip_sg=true
                shift
                ;;
            *)
                shift
                ;;
        esac
    done
    
    # 显示欢迎信息
    echo ""
    echo -e "${MAGENTA}╔═══════════════════════════════════════════════════════╗${NC}"
    echo -e "${MAGENTA}║${NC}  ${BOLD}智能一键部署脚本${NC}                              ${MAGENTA}║${NC}"
    echo -e "${MAGENTA}║${NC}  项目: ${PROJECT_DESC}                   ${MAGENTA}║${NC}"
    echo -e "${MAGENTA}║${NC}  服务器: ${SERVER_HOST}                           ${MAGENTA}║${NC}"
    echo -e "${MAGENTA}║${NC}  域名: ${DOMAIN}                               ${MAGENTA}║${NC}"
    echo -e "${MAGENTA}╚═══════════════════════════════════════════════════════╝${NC}"
    echo ""
    
    case "$command" in
        deploy)
            # 执行完整部署
            if [ "$skip_backup" = true ]; then
                log_warn "跳过备份..."
                AUTO_BACKUP=false
            fi
            
            deploy_step_1_check
            deploy_step_2_backup
            deploy_step_3_upload_backend
            deploy_step_4_upload_frontend
            deploy_step_5_configure_nginx
            
            if [ "$skip_sg" = false ]; then
                deploy_step_6_configure_security_group
            else
                log_info "跳过安全组配置 (--skip-sg)"
            fi
            
            deploy_step_7_start_backend
            deploy_step_8_verify
            deploy_step_9_cleanup
            
            echo ""
            log_success "🎉 部署完成！"
            echo ""
            echo "访问地址:"
            echo -e "  ${GREEN}用户端:${NC}   https://${DOMAIN}${FRONTEND_USER_PATH}/"
            echo -e "  ${GREEN}管理后台:${NC} https://${DOMAIN}${FRONTEND_ADMIN_PATH}/"
            echo -e "  ${GREEN}API:${NC}      https://${DOMAIN}/api/"
            echo ""
            ;;
        status)
            cmd_status
            ;;
        restart)
            cmd_restart
            ;;
        stop)
            cmd_stop
            ;;
        logs)
            cmd_logs
            ;;
        shell)
            cmd_shell
            ;;
        backup)
            cmd_backup
            ;;
        help|--help|-h)
            show_usage
            ;;
        *)
            log_error "未知命令: $command"
            show_usage
            exit 1
            ;;
    esac
}

# 运行主函数
main "$@"