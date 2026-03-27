#!/bin/bash
# ==========================================
# 智能一键部署脚本
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
    
    # 检查本地文件
    log_info "检查本地项目文件..."
    if [ ! -d "${LOCAL_PROJECT_ROOT}/${BACKEND_DIR}" ]; then
        log_error "后端目录不存在: ${LOCAL_PROJECT_ROOT}/${BACKEND_DIR}"
        exit 1
    fi
    
    if [ ! -d "${LOCAL_PROJECT_ROOT}/Service_WaterManage/frontend" ]; then
        log_error "前端目录不存在"
        exit 1
    fi
    
    log_success "环境检查通过"
}

deploy_step_2_backup() {
    if [ "$AUTO_BACKUP" = true ]; then
        log_header "步骤 2: 备份"
        local backup_name="${PROJECT_NAME}-$(date +%Y%m%d%H%M%S)"
        backup_server "$backup_name"
    else
        log_info "跳过备份 (AUTO_BACKUP=false)"
    fi
}

deploy_step_3_upload_backend() {
    log_header "步骤 3: 上传后端"
    
    log_info "上传后端目录..."
    
    # 创建服务器目录
    ensure_dir "${SERVER_PROJECT_ROOT}"
    
    # 删除旧的后端目录（如果存在）
    ssh_exec "rm -rf ${SERVER_PROJECT_ROOT}/${BACKEND_DIR}"
    
    # 上传新的后端目录
    scp_upload -r "${LOCAL_PROJECT_ROOT}/${BACKEND_DIR}" "${SERVER_PROJECT_ROOT}/"
    
    # 创建虚拟环境并安装依赖
    log_info "安装 Python 依赖..."
    ssh_exec "
        cd ${SERVER_PROJECT_ROOT}/${BACKEND_DIR}
        
        # 创建虚拟环境
        python${PYTHON_VERSION} -m venv venv 2>/dev/null || python3 -m venv venv 2>/dev/null || python -m venv venv
        
        # 激活虚拟环境
        source venv/bin/activate
        
        # 升级 pip
        pip install --upgrade pip -q
        
        # 安装依赖
        pip install -r requirements.txt -q
        
        echo 'Dependencies installed'
    "
    
    # 修复已知问题
    log_info "修复已知问题..."
    ssh_exec "
        cd ${SERVER_PROJECT_ROOT}/${BACKEND_DIR}
        
        # 修复 main.py 前向引用问题
        sed -i 's/-> Optional\[User\]:/-> Optional[\"User\"]:/' main.py 2>/dev/null || true
        
        echo 'Fixes applied'
    "
    
    log_success "后端上传完成"
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
    
    # 创建 Nginx 配置
    log_info "生成 Nginx 配置..."
    
    ssh_exec "cat > /etc/nginx/sites-available/${DOMAIN}-https << 'NGINX_EOF'
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

    # 启用配置
    ssh_exec "
        mkdir -p /etc/nginx/sites-enabled
        ln -sf /etc/nginx/sites-available/${DOMAIN}-https /etc/nginx/sites-enabled/
    "
    
    # 重启 Nginx
    restart_nginx
    
    log_success "Nginx 配置完成"
}

deploy_step_6_start_backend() {
    log_header "步骤 6: 启动后端服务"
    
    restart_backend
    
    log_success "后端服务启动完成"
}

deploy_step_7_verify() {
    log_header "步骤 7: 验证部署"
    
    verify_deployment
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
    ssh $SSH_OPTS -p ${SERVER_PORT:-22} ${SERVER_USER}@${SERVER_HOST}
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
    help            显示帮助信息

示例:
    $0 deploy           # 执行完整部署
    $0 status          # 查看状态
    $0 restart         # 重启服务
    $0 shell           # SSH 到服务器

EOF
}

main() {
    local command="${1:-deploy}"
    
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
            if [ "$2" = "--skip-backup" ]; then
                log_warn "跳过备份..."
                AUTO_BACKUP=false
            fi
            
            deploy_step_1_check
            deploy_step_2_backup
            deploy_step_3_upload_backend
            deploy_step_4_upload_frontend
            deploy_step_5_configure_nginx
            deploy_step_6_start_backend
            deploy_step_7_verify
            
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
