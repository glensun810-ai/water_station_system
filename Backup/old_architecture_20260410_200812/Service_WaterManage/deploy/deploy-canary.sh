#!/bin/bash
# ==========================================
# 灰度环境部署脚本
# ==========================================
#
# 功能：
# - 将本地最新代码部署到灰度环境
# - 不影响生产环境
# - 使用生产数据库副本
# - 独立的后端端口和访问路径
#
# 使用方法：
# ./deploy-canary.sh deploy        # 部署到灰度环境
# ./deploy-canary.sh status        # 查看灰度环境状态
# ./deploy-canary.sh logs          # 查看灰度环境日志
# ./deploy-canary.sh stop          # 停止灰度环境
# ./deploy-canary.sh shell         # SSH 到服务器
# ./deploy-canary.sh clean         # 清理灰度环境
# ==========================================

set -e

# 获取脚本目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 加载灰度环境配置
source "${SCRIPT_DIR}/config-canary.sh"

# 加载通用函数
source "${SCRIPT_DIR}/deploy-common.sh"

# ==========================================
# 灰度环境特殊步骤
# ==========================================

sync_production_database() {
    log_header "步骤: 同步生产数据库到灰度环境"
    
    # 检查生产数据库是否存在
    local prod_db_exists=$(ssh_exec_quiet "test -f '${PRODUCTION_PROJECT_ROOT}/${BACKEND_DIR}/${PRODUCTION_DB_NAME}' && echo 'yes' || echo 'no'")
    
    if [ "$prod_db_exists" = "yes" ]; then
        log_info "生产数据库存在，开始同步..."
        
        # 创建灰度环境目录
        ensure_dir "${SERVER_PROJECT_ROOT}/${BACKEND_DIR}"
        
        # 复制生产数据库到灰度环境
        ssh_exec "
            # 备份现有的灰度数据库（如果存在）
            if [ -f '${SERVER_PROJECT_ROOT}/${BACKEND_DIR}/${CANARY_DB_NAME}' ]; then
                echo '备份现有灰度数据库...'
                cp '${SERVER_PROJECT_ROOT}/${BACKEND_DIR}/${CANARY_DB_NAME}' '${SERVER_PROJECT_ROOT}/${BACKEND_DIR}/${CANARY_DB_NAME}.backup'
            fi
            
            # 复制生产数据库到灰度环境
            echo '复制生产数据库到灰度环境...'
            cp '${PRODUCTION_PROJECT_ROOT}/${BACKEND_DIR}/${PRODUCTION_DB_NAME}' '${SERVER_PROJECT_ROOT}/${BACKEND_DIR}/${CANARY_DB_NAME}'
            
            # 设置权限
            chmod 644 '${SERVER_PROJECT_ROOT}/${BACKEND_DIR}/${CANARY_DB_NAME}'
            
            echo '数据库同步完成'
        "
        
        # 验证灰度数据库
        local canary_db_size=$(ssh_exec_quiet "ls -lh '${SERVER_PROJECT_ROOT}/${BACKEND_DIR}/${CANARY_DB_NAME}' | awk '{print \$5}'")
        log_success "灰度数据库已创建，大小: $canary_db_size"
    else
        log_warn "生产数据库不存在，将创建新的空数据库"
    fi
}

verify_canary_database() {
    log_info "验证灰度数据库..."
    
    local db_exists=$(ssh_exec_quiet "test -f '${SERVER_PROJECT_ROOT}/${BACKEND_DIR}/${CANARY_DB_NAME}' && echo 'yes' || echo 'no'")
    
    if [ "$db_exists" = "yes" ]; then
        local db_size=$(ssh_exec_quiet "ls -lh '${SERVER_PROJECT_ROOT}/${BACKEND_DIR}/${CANARY_DB_NAME}' | awk '{print \$5}'")
        log_success "灰度数据库验证通过，大小: $db_size"
        return 0
    else
        log_error "灰度数据库不存在"
        return 1
    fi
}

# ==========================================
# 部署步骤函数
# ==========================================

deploy_step_1_check() {
    log_header "步骤 1: 环境检查"
    
    check_command ssh || exit 1
    check_command scp || exit 1
    check_command curl || exit 1
    
    check_ssh_connection || exit 1
    check_disk_space
    
    log_info "检查本地项目文件..."
    if [ ! -d "${LOCAL_PROJECT_ROOT}/${BACKEND_DIR}" ]; then
        log_error "后端目录不存在: ${LOCAL_PROJECT_ROOT}/${BACKEND_DIR}"
        exit 1
    fi
    
    if [ ! -d "${LOCAL_PROJECT_ROOT}/frontend" ]; then
        log_error "前端目录不存在"
        exit 1
    fi
    
    log_success "环境检查通过"
}

deploy_step_2_sync_db() {
    log_header "步骤 2: 同步生产数据库"
    
    sync_production_database
    
    log_success "数据库同步完成"
}

deploy_step_3_upload_backend() {
    log_header "步骤 3: 上传后端到灰度环境"
    
    log_warn "灰度部署：只更新代码，不影响生产数据"
    
    ensure_dir "${SERVER_PROJECT_ROOT}"
    ensure_dir "${SERVER_PROJECT_ROOT}/${BACKEND_DIR}"
    
    log_info "增量更新后端代码..."
    
    local exclude_patterns=(
        "*.db"
        "*.sqlite"
        "*.sqlite3"
        "__pycache__"
        "*.pyc"
        "*.pyo"
        ".pytest_cache"
        "venv/"
        "*.log"
        "uploads/"
        "*.env"
        ".git/"
    )
    
    local rsync_exclude=""
    for pattern in "${exclude_patterns[@]}"; do
        rsync_exclude="${rsync_exclude} --exclude='${pattern}'"
    done
    
    local server_has_rsync=$(ssh_exec_quiet "command -v rsync &>/dev/null && echo 'yes' || echo 'no'")
    
    if command -v rsync &>/dev/null && [ "$server_has_rsync" = "yes" ]; then
        if [ -n "$SSH_KEY_PATH" ] && [ -f "$SSH_KEY_PATH" ]; then
            rsync -avz ${rsync_exclude} -e "ssh -i '$SSH_KEY_PATH' -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null" "${LOCAL_PROJECT_ROOT}/${BACKEND_DIR}/" "${SERVER_USER}@${SERVER_HOST}:${SERVER_PROJECT_ROOT}/${BACKEND_DIR}/"
        elif command -v sshpass &>/dev/null && [ -n "$SERVER_PASSWORD" ]; then
            rsync -avz ${rsync_exclude} -e "sshpass -p '$SERVER_PASSWORD' ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null" "${LOCAL_PROJECT_ROOT}/${BACKEND_DIR}/" "${SERVER_USER}@${SERVER_HOST}:${SERVER_PROJECT_ROOT}/${BACKEND_DIR}/"
        else
            rsync -avz ${rsync_exclude} -e "ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null" "${LOCAL_PROJECT_ROOT}/${BACKEND_DIR}/" "${SERVER_USER}@${SERVER_HOST}:${SERVER_PROJECT_ROOT}/${BACKEND_DIR}/"
        fi
    else
        log_warn "rsync 不可用，使用 tar 方式上传"
        
        local temp_tar="/tmp/backend_canary_$(date +%Y%m%d_%H%M%S).tar"
        (cd "${LOCAL_PROJECT_ROOT}/${BACKEND_DIR}" && tar --exclude='*.db' --exclude='*.sqlite' --exclude='*.sqlite3' --exclude='__pycache__' --exclude='venv' --exclude='*.log' --exclude='.git' -cf - .) > "$temp_tar"
        
        scp_upload "$temp_tar" "/tmp/backend_canary.tar"
        ssh_exec "cd ${SERVER_PROJECT_ROOT}/${BACKEND_DIR} && tar -xf /tmp/backend_canary.tar --overwrite"
        ssh_exec "rm -f /tmp/backend_canary.tar"
        rm -f "$temp_tar"
    fi
    
    verify_canary_database
    
    log_info "检查/安装 Python 依赖..."
    ssh_exec "
        cd ${SERVER_PROJECT_ROOT}/${BACKEND_DIR}
        
        if [ ! -d 'venv' ]; then
            echo '创建虚拟环境...'
            python${PYTHON_VERSION} -m venv venv 2>/dev/null || python3 -m venv venv 2>/dev/null || python -m venv venv
        fi
        
        source venv/bin/activate
        pip install --upgrade pip -q
        pip install -r requirements.txt -q
        
        echo 'Dependencies installed'
    "
    
    log_info "修改数据库配置（使用灰度数据库）..."
    ssh_exec "
        cd ${SERVER_PROJECT_ROOT}/${BACKEND_DIR}
        
        # 修改 main.py 中的数据库文件名（如果硬编码）
        sed -i 's/waterms.db/${CANARY_DB_NAME}/g' main.py 2>/dev/null || true
        
        # 或者创建/修改 .env 文件
        if [ -f '.env' ]; then
            sed -i 's/waterms.db/${CANARY_DB_NAME}/g' .env 2>/dev/null || true
        else
            echo 'DATABASE_URL=${CANARY_DB_NAME}' > .env
        fi
        
        echo 'Database configuration updated'
    "
    
    log_success "后端上传完成"
}

deploy_step_4_upload_frontend() {
    log_header "步骤 4: 上传前端"
    
    ensure_dir "${SERVER_PROJECT_ROOT}${FRONTEND_USER_PATH}"
    ensure_dir "${SERVER_PROJECT_ROOT}${FRONTEND_ADMIN_PATH}"
    
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
    
    log_info "配置前端 API 地址（灰度环境）..."
    local api_url="https://${CANARY_DOMAIN}/api"
    
    ssh_exec "
        sed -i 's|http://localhost:8000/api|${api_url}|g' ${SERVER_PROJECT_ROOT}${FRONTEND_USER_PATH}/index.html 2>/dev/null || true
        sed -i 's|https://jhw-ai.com/api|${api_url}|g' ${SERVER_PROJECT_ROOT}${FRONTEND_USER_PATH}/index.html 2>/dev/null || true
        
        sed -i 's|http://localhost:8000/api|${api_url}|g' ${SERVER_PROJECT_ROOT}${FRONTEND_ADMIN_PATH}/admin.html 2>/dev/null || true
        sed -i 's|https://jhw-ai.com/api|${api_url}|g' ${SERVER_PROJECT_ROOT}${FRONTEND_ADMIN_PATH}/admin.html 2>/dev/null || true
        
        sed -i 's|http://localhost:8000/api|${api_url}|g' ${SERVER_PROJECT_ROOT}${FRONTEND_ADMIN_PATH}/login.html 2>/dev/null || true
        sed -i 's|https://jhw-ai.com/api|${api_url}|g' ${SERVER_PROJECT_ROOT}${FRONTEND_ADMIN_PATH}/login.html 2>/dev/null || true
        
        sed -i 's|\"admin.html\"|\"/water-admin/admin.html\"|g' ${SERVER_PROJECT_ROOT}${FRONTEND_ADMIN_PATH}/login.html 2>/dev/null || true
        sed -i \"s|'admin.html'|'/water-admin/admin.html'|g\" ${SERVER_PROJECT_ROOT}${FRONTEND_ADMIN_PATH}/login.html 2>/dev/null || true
        
        sed -i 's|\"login.html\"|\"/water-admin/login.html\"|g' ${SERVER_PROJECT_ROOT}${FRONTEND_ADMIN_PATH}/admin.html 2>/dev/null || true
        sed -i \"s|'login.html'|'/water-admin/login.html'|g\" ${SERVER_PROJECT_ROOT}${FRONTEND_ADMIN_PATH}/admin.html 2>/dev/null || true
        
        echo 'Frontend configured'
    "
    
    log_success "前端上传完成"
}

deploy_step_5_configure_nginx() {
    log_header "步骤 5: 配置 Nginx（灰度子域名）"
    
    local nginx_type=$(ssh_exec_quiet "which aa_nginx && echo 'aa_nginx' || (which nginx && echo 'nginx' || echo 'not_found')")
    
    if [ "$nginx_type" = "not_found" ]; then
        log_warn "未检测到 Nginx，将使用标准配置"
        nginx_type="nginx"
    fi
    
    log_info "生成灰度环境 Nginx 配置..."
    
    # 使用子域名配置（推荐）
    if [ "$nginx_type" = "aa_nginx" ]; then
        ssh_exec "cat > /etc/aa_nginx/vhost/${CANARY_DOMAIN}.conf << 'NGINX_EOF'
server {
    listen 80;
    server_name ${CANARY_DOMAIN};
    return 301 https://\$server_name\$request_uri;
}

server {
    listen 443 ssl;
    server_name ${CANARY_DOMAIN};

    ssl_certificate ${SSL_CERT_PATH};
    ssl_certificate_key ${SSL_KEY_PATH};

    ssl_session_timeout 1d;
    ssl_session_cache shared:SSL:50m;
    ssl_session_tickets off;

    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305;
    ssl_prefer_server_ciphers off;

    location ${FRONTEND_USER_PATH}/ {
        alias ${SERVER_PROJECT_ROOT}${FRONTEND_USER_PATH}/;
        index index.html;
        try_files \$uri \$uri/ ${FRONTEND_USER_PATH}/index.html;
    }

    location ${FRONTEND_ADMIN_PATH}/ {
        alias ${SERVER_PROJECT_ROOT}${FRONTEND_ADMIN_PATH}/;
        index admin.html;
        try_files \$uri \$uri/ ${FRONTEND_ADMIN_PATH}/admin.html;
    }

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

    location / {
        return 301 https://${CANARY_DOMAIN}${FRONTEND_USER_PATH}/;
    }
}
NGINX_EOF"
    else
        ssh_exec "cat > /etc/nginx/sites-available/${CANARY_DOMAIN} << 'NGINX_EOF'
server {
    listen 80;
    server_name ${CANARY_DOMAIN};
    return 301 https://\$server_name\$request_uri;
}

server {
    listen 443 ssl;
    server_name ${CANARY_DOMAIN};

    ssl_certificate ${SSL_CERT_PATH};
    ssl_certificate_key ${SSL_KEY_PATH};

    ssl_session_timeout 1d;
    ssl_session_cache shared:SSL:50m;
    ssl_session_tickets off;

    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305;
    ssl_prefer_server_ciphers off;

    location ${FRONTEND_USER_PATH}/ {
        alias ${SERVER_PROJECT_ROOT}${FRONTEND_USER_PATH}/;
        index index.html;
        try_files \$uri \$uri/ ${FRONTEND_USER_PATH}/index.html;
    }

    location ${FRONTEND_ADMIN_PATH}/ {
        alias ${SERVER_PROJECT_ROOT}${FRONTEND_ADMIN_PATH}/;
        index admin.html;
        try_files \$uri \$uri/ ${FRONTEND_ADMIN_PATH}/admin.html;
    }

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

    location / {
        return 301 https://${CANARY_DOMAIN}${FRONTEND_USER_PATH}/;
    }
}
NGINX_EOF"

        ssh_exec "
            mkdir -p /etc/nginx/sites-enabled
            ln -sf /etc/nginx/sites-available/${CANARY_DOMAIN} /etc/nginx/sites-enabled/
        "
    fi
    
    restart_nginx
    
    log_success "Nginx 配置完成"
}

deploy_step_6_start_backend() {
    log_header "步骤 6: 启动灰度环境后端服务"
    
    log_info "启动灰度环境后端（端口 ${BACKEND_PORT})..."
    
    ssh_exec "
        cd ${SERVER_PROJECT_ROOT}/${BACKEND_DIR}
        
        source venv/bin/activate
        
        # 停止灰度环境旧进程
        pkill -f 'uvicorn.*:${BACKEND_PORT}' 2>/dev/null || true
        sleep 2
        
        # 启动灰度环境新进程
        nohup python -m uvicorn main:app --host 127.0.0.1 --port ${BACKEND_PORT} > /var/log/${PROJECT_NAME}-api.log 2>&1 &
        
        sleep 3
        
        if curl -sf http://127.0.0.1:${BACKEND_PORT}/api/health > /dev/null 2>&1; then
            echo 'BACKEND_STARTED_OK'
        else
            echo 'BACKEND_STARTED_FAILED'
            cat /var/log/${PROJECT_NAME}-api.log
        fi
    "
    
    local result=$(ssh_exec_quiet "curl -sf http://127.0.0.1:${BACKEND_PORT}/api/health")
    if [ -n "$result" ]; then
        log_success "灰度环境后端服务启动成功"
    else
        log_error "灰度环境后端服务启动失败"
        return 1
    fi
}

deploy_step_7_verify() {
    log_header "步骤 7: 验证灰度环境部署"
    
    local checks_passed=0
    local checks_total=3
    
    echo ""
    log_info "验证灰度环境..."
    
    echo -n "灰度用户端: "
    if curl -sfI "https://${CANARY_DOMAIN}${FRONTEND_USER_PATH}/" > /dev/null 2>&1; then
        echo -e "${GREEN}OK${NC}"
        ((checks_passed++))
    else
        echo -e "${RED}FAILED${NC}"
    fi
    
    echo -n "灰度管理后台: "
    if curl -sfI "https://${CANARY_DOMAIN}${FRONTEND_ADMIN_PATH}/" > /dev/null 2>&1; then
        echo -e "${GREEN}OK${NC}"
        ((checks_passed++))
    else
        echo -e "${RED}FAILED${NC}"
    fi
    
    echo -n "灰度 API 服务: "
    if curl -sf "https://${CANARY_DOMAIN}/api/health" > /dev/null 2>&1; then
        echo -e "${GREEN}OK${NC}"
        ((checks_passed++))
    else
        echo -e "${RED}FAILED${NC}"
    fi
    
    echo ""
    if [ $checks_passed -eq $checks_total ]; then
        log_success "灰度环境验证通过 ($checks_passed/$checks_total)"
    else
        log_warn "灰度环境部分验证失败 ($checks_passed/$checks_total)"
    fi
}

# ==========================================
# 快捷命令
# ==========================================

cmd_status() {
    log_info "检查灰度环境状态..."
    
    echo -e "${CYAN}=== 灰度环境 Nginx ===${NC}"
    ssh_exec "ss -tlnp | grep -E '80|443' || netstat -tlnp | grep -E '80|443'"
    
    echo -e "${CYAN}=== 灰度环境后端进程（端口 ${BACKEND_PORT}) ===${NC}"
    ssh_exec "ps aux | grep uvicorn | grep ':${BACKEND_PORT}' | grep -v grep"
    
    echo -e "${CYAN}=== 灰度环境 API 健康检查 ===${NC}"
    ssh_exec "curl -s http://127.0.0.1:${BACKEND_PORT}/api/health"
    
    echo -e "${CYAN}=== 灰度环境 HTTPS 检查 ===${NC}"
    curl -sI "https://${CANARY_DOMAIN}/api/health" | head -3
    
    echo -e "${CYAN}=== 灰度数据库 ===${NC}"
    ssh_exec "ls -lh ${SERVER_PROJECT_ROOT}/${BACKEND_DIR}/${CANARY_DB_NAME}"
}

cmd_logs() {
    log_info "查看灰度环境后端日志..."
    ssh_exec "tail -50 /var/log/${PROJECT_NAME}-api.log"
}

cmd_stop() {
    log_info "停止灰度环境服务..."
    ssh_exec "pkill -f 'uvicorn.*:${BACKEND_PORT}' || true"
    log_success "灰度环境服务已停止"
}

cmd_clean() {
    log_warn "⚠️  清理灰度环境将删除所有灰度数据！"
    if confirm "确认清理灰度环境吗？"; then
        log_info "停止服务..."
        ssh_exec "pkill -f 'uvicorn.*:${BACKEND_PORT}' || true"
        
        log_info "删除灰度环境文件..."
        ssh_exec "rm -rf ${SERVER_PROJECT_ROOT}"
        
        log_info "删除灰度 Nginx 配置..."
        ssh_exec "
            rm -f /etc/nginx/sites-available/${CANARY_DOMAIN}
            rm -f /etc/nginx/sites-enabled/${CANARY_DOMAIN}
            rm -f /etc/aa_nginx/vhost/${CANARY_DOMAIN}.conf
        "
        
        restart_nginx
        
        log_success "灰度环境已清理"
    else
        log_info "取消清理"
    fi
}

cmd_shell() {
    log_info "连接到服务器..."
    if [ -n "$SSH_KEY_PATH" ] && [ -f "$SSH_KEY_PATH" ]; then
        ssh -i "$SSH_KEY_PATH" $SSH_OPTS -p ${SERVER_PORT:-22} ${SERVER_USER}@${SERVER_HOST}
    else
        ssh $SSH_OPTS -p ${SERVER_PORT:-22} ${SERVER_USER}@${SERVER_HOST}
    fi
}

# ==========================================
# 主函数
# ==========================================

show_usage() {
    cat << EOF
用法: $0 <命令> [选项]

灰度环境部署命令:
    deploy          部署到灰度环境
    status          查看灰度环境状态
    logs            查看灰度环境日志
    stop            停止灰度环境服务
    shell           SSH 连接到服务器
    clean           清理灰度环境（⚠️  会删除所有灰度数据）
    help            显示帮助信息

示例:
    $0 deploy                  # 部署到灰度环境
    $0 status                  # 查看灰度环境状态
    $0 logs                    # 查看灰度环境日志
    $0 clean                   # 清理灰度环境

访问地址:
    灰度用户端:   https://${CANARY_DOMAIN}${FRONTEND_USER_PATH}/
    灰度管理后台: https://${CANARY_DOMAIN}${FRONTEND_ADMIN_PATH}/
    灰度 API:     https://${CANARY_DOMAIN}/api/

注意:
    - 灰度环境使用生产数据库副本
    - 灰度环境不影响生产环境
    - 验证通过后可使用 promote-canary.sh 提升到生产环境
EOF
}

main() {
    local command="${1:-deploy}"
    
    shift
    
    echo ""
    echo -e "${MAGENTA}╔═══════════════════════════════════════════════════════╗${NC}"
    echo -e "${MAGENTA}║${NC}  ${BOLD}灰度环境部署脚本${NC}                              ${MAGENTA}║${NC}"
    echo -e "${MAGENTA}║${NC}  项目: ${PROJECT_DESC}                   ${MAGENTA}║${NC}"
    echo -e "${MAGENTA}║${NC}  服务器: ${SERVER_HOST}                           ${MAGENTA}║${NC}"
    echo -e "${MAGENTA}║${NC}  灰度域名: ${CANARY_DOMAIN}                       ${MAGENTA}║${NC}"
    echo -e "${MAGENTA}║${NC}  灰度端口: ${BACKEND_PORT}                            ${MAGENTA}║${NC}"
    echo -e "${MAGENTA}╚═══════════════════════════════════════════════════════╝${NC}"
    echo ""
    
    case "$command" in
        deploy)
            deploy_step_1_check
            deploy_step_2_sync_db
            deploy_step_3_upload_backend
            deploy_step_4_upload_frontend
            deploy_step_5_configure_nginx
            deploy_step_6_start_backend
            deploy_step_7_verify
            
            echo ""
            log_success "🎉 灰度环境部署完成！"
            echo ""
            echo "访问地址:"
            echo -e "  ${GREEN}灰度用户端:${NC}   https://${CANARY_DOMAIN}${FRONTEND_USER_PATH}/"
            echo -e "  ${GREEN}灰度管理后台:${NC} https://${CANARY_DOMAIN}${FRONTEND_ADMIN_PATH}/"
            echo -e "  ${GREEN}灰度 API:${NC}     https://${CANARY_DOMAIN}/api/"
            echo ""
            echo "验证步骤:"
            echo "1. 访问灰度环境验证功能"
            echo "2. 测试主要业务流程"
            echo "3. 确认无问题后使用 ./promote-canary.sh 提升到生产环境"
            echo ""
            ;;
        status)
            cmd_status
            ;;
        logs)
            cmd_logs
            ;;
        stop)
            cmd_stop
            ;;
        shell)
            cmd_shell
            ;;
        clean)
            cmd_clean
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

main "$@"