#!/bin/bash
# ==========================================
# 通用部署函数库
# ==========================================

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
GRAY='\033[0;90m'
NC='\033[0m' # No Color
BOLD='\033[1m'

# ==========================================
# 日志函数
# ==========================================

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo -e "${CYAN}[STEP $1/$2]${NC} $3"
}

log_header() {
    echo ""
    echo -e "${BOLD}========================================${NC}"
    echo -e "${BOLD}  $1${NC}"
    echo -e "${BOLD}========================================${NC}"
}

# ==========================================
# SSH 连接函数
# ==========================================

SSH_OPTS="-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o ConnectTimeout=10"

ssh_exec() {
    local cmd="$1"
    if [ -n "$SSH_KEY_PATH" ] && [ -f "$SSH_KEY_PATH" ]; then
        ssh -i "$SSH_KEY_PATH" -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o ConnectTimeout=10 -p ${SERVER_PORT:-22} ${SERVER_USER}@${SERVER_HOST} "$cmd"
    elif command -v sshpass &>/dev/null && [ -n "$SERVER_PASSWORD" ]; then
        sshpass -p "$SERVER_PASSWORD" ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o ConnectTimeout=10 -p ${SERVER_PORT:-22} ${SERVER_USER}@${SERVER_HOST} "$cmd"
    else
        ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o ConnectTimeout=10 -p ${SERVER_PORT:-22} ${SERVER_USER}@${SERVER_HOST} "$cmd"
    fi
}

ssh_exec_quiet() {
    local cmd="$1"
    if [ -n "$SSH_KEY_PATH" ] && [ -f "$SSH_KEY_PATH" ]; then
        ssh -i "$SSH_KEY_PATH" -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o ConnectTimeout=10 -p ${SERVER_PORT:-22} ${SERVER_USER}@${SERVER_HOST} "$cmd" 2>/dev/null
    elif command -v sshpass &>/dev/null && [ -n "$SERVER_PASSWORD" ]; then
        sshpass -p "$SERVER_PASSWORD" ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o ConnectTimeout=10 -p ${SERVER_PORT:-22} ${SERVER_USER}@${SERVER_HOST} "$cmd" 2>/dev/null
    else
        ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o ConnectTimeout=10 -p ${SERVER_PORT:-22} ${SERVER_USER}@${SERVER_HOST} "$cmd" 2>/dev/null
    fi
}

# ==========================================
# SCP 传输函数
# ==========================================

scp_upload() {
    local local_path="$1"
    local remote_path="$2"
    if [ -n "$SSH_KEY_PATH" ] && [ -f "$SSH_KEY_PATH" ]; then
        scp -i "$SSH_KEY_PATH" -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -P ${SERVER_PORT:-22} "$local_path" "${SERVER_USER}@${SERVER_HOST}:${remote_path}"
    elif command -v sshpass &>/dev/null && [ -n "$SERVER_PASSWORD" ]; then
        sshpass -p "$SERVER_PASSWORD" scp -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -P ${SERVER_PORT:-22} "$local_path" "${SERVER_USER}@${SERVER_HOST}:${remote_path}"
    else
        scp -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -P ${SERVER_PORT:-22} "$local_path" "${SERVER_USER}@${SERVER_HOST}:${remote_path}"
    fi
}

scp_download() {
    local remote_path="$1"
    local local_path="$2"
    if [ -n "$SSH_KEY_PATH" ] && [ -f "$SSH_KEY_PATH" ]; then
        scp -i "$SSH_KEY_PATH" -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -P ${SERVER_PORT:-22} "${SERVER_USER}@${SERVER_HOST}:${remote_path}" "$local_path"
    elif command -v sshpass &>/dev/null && [ -n "$SERVER_PASSWORD" ]; then
        sshpass -p "$SERVER_PASSWORD" scp -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -P ${SERVER_PORT:-22} "${SERVER_USER}@${SERVER_HOST}:${remote_path}" "$local_path"
    else
        scp -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -P ${SERVER_PORT:-22} "${SERVER_USER}@${SERVER_HOST}:${remote_path}" "$local_path"
    fi
}

# ==========================================
# 检查函数
# ==========================================

check_command() {
    local cmd="$1"
    if ! command -v $cmd &> /dev/null; then
        log_error "$cmd 未安装，请先安装"
        return 1
    fi
    return 0
}

check_ssh_connection() {
    log_info "检查 SSH 连接..."
    if command -v sshpass &>/dev/null && [ -n "$SERVER_PASSWORD" ]; then
        if sshpass -p "$SERVER_PASSWORD" ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o ConnectTimeout=10 -p ${SERVER_PORT:-22} ${SERVER_USER}@${SERVER_HOST} "echo ok" &>/dev/null; then
            log_success "SSH 连接正常"
            return 0
        else
            log_error "无法连接到服务器 ${SERVER_USER}@${SERVER_HOST}:${SERVER_PORT:-22}"
            return 1
        fi
    else
        if ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o ConnectTimeout=10 -p ${SERVER_PORT:-22} ${SERVER_USER}@${SERVER_HOST} "echo ok" &>/dev/null; then
            log_success "SSH 连接正常"
            return 0
        else
            log_error "无法连接到服务器 ${SERVER_USER}@${SERVER_HOST}:${SERVER_PORT:-22}"
            return 1
        fi
    fi
}

check_disk_space() {
    log_info "检查磁盘空间..."
    local available=$(ssh_exec_quiet "df -h / | tail -1 | awk '{print \$4}'")
    log_info "可用空间: $available"
    return 0
}

check_nginx() {
    log_info "检查 Nginx..."
    if ssh_exec_quiet "which nginx || which aa_nginx" &>/dev/null; then
        log_success "Nginx 已安装"
        return 0
    else
        log_warn "Nginx 未安装"
        return 1
    fi
}

check_server_dir() {
    log_info "检查服务器目录..."
    if ssh_exec_quiet "[ -d /var/www/${DOMAIN} ]" &>/dev/null; then
        log_info "项目目录已存在"
        return 1
    else
        log_info "项目目录不存在，将创建新目录"
        return 0
    fi
}

# ==========================================
# 备份函数
# ==========================================

backup_server() {
    local backup_name="$1"
    local backup_dir="$2"
    
    log_info "创建备份: $backup_name"
    
    ssh_exec "
        # 创建备份目录
        mkdir -p /var/backups/${DOMAIN}
        
        # 备份项目目录
        if [ -d '${SERVER_PROJECT_ROOT}' ]; then
            tar -czf /var/backups/${DOMAIN}/${backup_name}.tar.gz -C /var/www ${DOMAIN} 2>/dev/null || true
            echo '项目目录已备份'
        fi
        
        # 备份数据库
        if [ -f '${SERVER_PROJECT_ROOT}/${BACKEND_DIR}/waterms.db' ]; then
            cp '${SERVER_PROJECT_ROOT}/${BACKEND_DIR}/waterms.db' /var/backups/${DOMAIN}/${backup_name}.db 2>/dev/null || true
            echo '数据库已备份'
        fi
        
        # 清理旧备份
        find /var/backups/${DOMAIN} -name '*.tar.gz' -mtime +${BACKUP_RETENTION_DAYS} -delete 2>/dev/null || true
    "
    
    log_success "备份完成"
}

# ==========================================
# 服务管理函数
# ==========================================

restart_backend() {
    log_info "重启后端服务..."
    
    ssh_exec "
        cd ${SERVER_PROJECT_ROOT}/${BACKEND_DIR}
        
        # 激活虚拟环境
        source venv/bin/activate
        
        # 停止旧进程
        pkill -f 'uvicorn main:app' 2>/dev/null || true
        sleep 2
        
        # 启动新进程
        nohup python -m uvicorn main:app --host 127.0.0.1 --port ${BACKEND_PORT} > /var/log/${PROJECT_NAME}-api.log 2>&1 &
        
        # 等待启动
        sleep 3
        
        # 检查状态
        if curl -sf http://127.0.0.1:${BACKEND_PORT}/api/health > /dev/null 2>&1; then
            echo 'BACKEND_STARTED_OK'
        else
            echo 'BACKEND_STARTED_FAILED'
            cat /var/log/${PROJECT_NAME}-api.log
        fi
    "
    
    local result=$(ssh_exec_quiet "curl -sf http://127.0.0.1:${BACKEND_PORT}/api/health")
    if [ -n "$result" ]; then
        log_success "后端服务启动成功"
        return 0
    else
        log_error "后端服务启动失败"
        return 1
    fi
}

restart_nginx() {
    log_info "重启 Nginx..."
    
    # 尝试多种重启方式
    ssh_exec "
        pkill -HUP aa_nginx 2>/dev/null || 
        nginx -s reload 2>/dev/null || 
        systemctl reload nginx 2>/dev/null ||
        echo 'Nginx reload attempted'
    "
    
    sleep 1
    log_success "Nginx 已重启"
}

# ==========================================
# 健康检查函数
# ==========================================

check_health_endpoint() {
    local url="$1"
    local name="$2"
    local max_attempts=${3:-5}
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if curl -sf "$url" > /dev/null 2>&1; then
            return 0
        fi
        echo -n "."
        sleep 2
        ((attempt++))
    done
    return 1
}

verify_deployment() {
    local checks_passed=0
    local checks_total=3
    
    echo ""
    log_info "验证部署..."
    
    # 检查用户端
    echo -n "用户端: "
    if curl -sfI "https://${DOMAIN}${FRONTEND_USER_PATH}/" > /dev/null 2>&1; then
        echo -e "${GREEN}OK${NC}"
        ((checks_passed++))
    else
        echo -e "${RED}FAILED${NC}"
    fi
    
    # 检查管理后台
    echo -n "管理后台: "
    if curl -sfI "https://${DOMAIN}${FRONTEND_ADMIN_PATH}/" > /dev/null 2>&1; then
        echo -e "${GREEN}OK${NC}"
        ((checks_passed++))
    else
        echo -e "${RED}FAILED${NC}"
    fi
    
    # 检查 API
    echo -n "API 服务: "
    if curl -sf "https://${DOMAIN}/api/health" > /dev/null 2>&1; then
        echo -e "${GREEN}OK${NC}"
        ((checks_passed++))
    else
        echo -e "${RED}FAILED${NC}"
    fi
    
    echo ""
    if [ $checks_passed -eq $checks_total ]; then
        log_success "验证通过 ($checks_passed/$checks_total)"
        return 0
    else
        log_warn "部分验证失败 ($checks_passed/$checks_total)"
        return 1
    fi
}

# ==========================================
# 生产数据保护函数
# ==========================================

verify_production_data_exists() {
    log_info "验证生产数据完整性..."
    
    # 检查数据库文件
    if [ -n "$SERVER_PROJECT_ROOT" ] && [ -n "$BACKEND_DIR" ]; then
        local db_path="${SERVER_PROJECT_ROOT}/${BACKEND_DIR}/waterms.db"
        local db_exists=$(ssh_exec_quiet "test -f '$db_path' && echo 'yes' || echo 'no'")
        
        if [ "$db_exists" = "yes" ]; then
            local db_size=$(ssh_exec_quiet "ls -lh '$db_path' 2>/dev/null | awk '{print \$5}'")
            local db_mtime=$(ssh_exec_quiet "stat -c '%y' '$db_path' 2>/dev/null | cut -d' ' -f1,2 | cut -d'.' -f1")
            log_success "生产数据库存在: $db_path"
            log_info "  大小: $db_size"
            log_info "  修改时间: $db_mtime"
            return 0
        else
            log_warn "未找到生产数据库: $db_path"
            log_warn "将创建新的空数据库"
            return 0
        fi
    else
        log_error "无法验证生产数据：路径配置不正确"
        return 1
    fi
}

# ==========================================
# 阿里云安全组配置函数
# ==========================================

configure_aliyun_security_group() {
    log_info "配置阿里云安全组..."
    
    # 检查是否配置了阿里云凭证
    if [ -z "$ALIYUN_ACCESS_KEY_ID" ] || [ -z "$ALIYUN_ACCESS_KEY_SECRET" ]; then
        log_warn "未配置阿里云凭证，跳过安全组配置"
        log_info "如需自动配置安全组，请在 config.sh 中设置以下变量："
        log_info "  ALIYUN_ACCESS_KEY_ID"
        log_info "  ALIYUN_ACCESS_KEY_SECRET"
        log_info "  ALIYUN_REGION_ID"
        log_info "  ALIYUN_INSTANCE_ID"
        return 0
    fi
    
    # 在服务器上安装和配置 aliyun CLI
    ssh_exec "
        # 检查 aliyun CLI 是否已安装
        if ! command -v aliyun &>/dev/null; then
            echo '安装 aliyun CLI...'
            curl -L 'https://aliyuncli.alicdn.com/aliyun-cli-linux-latest-amd64.tgz' -o /tmp/aliyun-cli.tgz
            tar -xzf /tmp/aliyun-cli.tgz -C /tmp
            mv /tmp/aliyun /usr/local/bin/aliyun
            chmod +x /usr/local/bin/aliyun
            rm -f /tmp/aliyun-cli.tgz
        fi
        
        # 配置 aliyun CLI
        /usr/local/bin/aliyun configure set --profile default --mode AK \\
            --access-key-id ${ALIYUN_ACCESS_KEY_ID} \\
            --access-key-secret ${ALIYUN_ACCESS_KEY_SECRET} \\
            --region ${ALIYUN_REGION_ID}
    "
    
    # 获取实例的安全组 ID
    log_info "获取实例安全组 ID..."
    local sg_id=$(ssh_exec "
        /usr/local/bin/aliyun ecs DescribeInstances --RegionId ${ALIYUN_REGION_ID} --InstanceIds '${ALIYUN_INSTANCE_ID}' \\
        | grep -oP '\"SecurityGroupId\": \"\\K[^\"]+' | head -1
    " 2>/dev/null)
    
    if [ -z "$sg_id" ]; then
        log_error "无法获取安全组 ID"
        return 1
    fi
    
    log_success "安全组 ID: $sg_id"
    
    # 添加安全组规则
    log_info "添加安全组规则..."
    
    # 添加端口 80 规则
    ssh_exec "
        /usr/local/bin/aliyun ecs AuthorizeSecurityGroup --RegionId ${ALIYUN_REGION_ID} \\
            --SecurityGroupId '${sg_id}' \\
            --IpProtocol tcp \\
            --PortRange '80/80' \\
            --SourceCidrIp '0.0.0.0/0' \\
            --Description 'Water management system - HTTP'
    " 2>/dev/null && log_success "已添加端口 80 规则" || log_warn "端口 80 规则可能已存在"
    
    # 添加端口 443 规则
    ssh_exec "
        /usr/local/bin/aliyun ecs AuthorizeSecurityGroup --RegionId ${ALIYUN_REGION_ID} \\
            --SecurityGroupId '${sg_id}' \\
            --IpProtocol tcp \\
            --PortRange '443/443' \\
            --SourceCidrIp '0.0.0.0/0' \\
            --Description 'Water management system - HTTPS'
    " 2>/dev/null && log_success "已添加端口 443 规则" || log_warn "端口 443 规则可能已存在"
    
    log_success "安全组配置完成"
}

# ==========================================
# 清理函数
# ==========================================

cleanup_deployment_artifacts() {
    log_info "清理部署文件..."
    
    ssh_exec "
        # 清理服务器根目录的临时文件
        rm -rf /root/main.py
        rm -rf /root/qwen3.5.py
        rm -rf /root/test_*.py
        rm -rf /root/waterms.db
        rm -rf /root/.git
        rm -rf /root/.github
        rm -rf /root/.idea
        
        echo '清理完成'
    "
    
    log_success "清理完成"
}

# ==========================================
# 用户交互函数
# ==========================================

confirm() {
    local prompt="${1:-确认执行?}"
    read -p "$prompt [y/n]: " choice
    case "$choice" in
        y|Y|yes|Yes|YES) return 0 ;;
        *) return 1 ;;
    esac
}

select_option() {
    local prompt="$1"
    shift
    local options=("$@")
    
    echo "$prompt"
    select choice in "${options[@]}"; do
        if [ -n "$choice" ]; then
            echo "$choice"
            return 0
        fi
    done
}

# ==========================================
# 文件处理函数
# ==========================================

ensure_dir() {
    local dir="$1"
    ssh_exec "mkdir -p '$dir'"
}

replace_in_file() {
    local file="$1"
    local pattern="$2"
    local replacement="$3"
    ssh_exec "sed -i 's|$pattern|$replacement|g' '$file'"
}