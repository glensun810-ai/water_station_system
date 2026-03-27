#!/bin/bash
# ==========================================
# SSH 密钥配置脚本
# 自动配置 SSH 免密登录
# ==========================================

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/config.sh"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

SSH_DIR="$HOME/.ssh"
PRIVATE_KEY="$SSH_DIR/id_rsa"
PUBLIC_KEY="${PRIVATE_KEY}.pub"

check_ssh_key_auth() {
    ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o ConnectTimeout=5 -p ${SERVER_PORT:-22} ${SERVER_USER}@${SERVER_HOST} "echo ok" &>/dev/null
}

setup_ssh_dir() {
    mkdir -p "$SSH_DIR"
    chmod 700 "$SSH_DIR"
    log_success "SSH 目录已创建: $SSH_DIR"
}

generate_keypair() {
    log_info "生成 SSH 密钥对..."
    ssh-keygen -t rsa -b 4096 -f "$PRIVATE_KEY" -N "" -C "${SERVER_USER}@${SERVER_HOST}"
    log_success "密钥对已生成"
}

import_private_key() {
    log_info "请粘贴您的私钥内容（以 -----BEGIN OPENSSH PRIVATE KEY----- 开头）"
    log_info "粘贴完成后按 Ctrl+D 完成输入"
    log_info "如果不需要导入直接密钥，请按 Ctrl+C 退出"
    echo ""
    
    local key_content
    key_content=$(cat)
    
    if [ -z "$key_content" ]; then
        log_error "未输入任何内容"
        exit 1
    fi
    
    if [[ ! "$key_content" == *"BEGIN"* ]] || [[ ! "$key_content" == *"END"* ]]; then
        log_error "私钥格式不正确，请确保包含完整的 BEGIN 和 END 标记"
        exit 1
    fi
    
    echo "$key_content" > "$PRIVATE_KEY"
    chmod 600 "$PRIVATE_KEY"
    log_success "私钥已保存到: $PRIVATE_KEY"
}

add_public_key_to_server() {
    log_info "将公钥添加到服务器..."
    
    if [ ! -f "$PUBLIC_KEY" ]; then
        log_error "公钥文件不存在: $PUBLIC_KEY"
        exit 1
    fi
    
    local public_key_content
    public_key_content=$(cat "$PUBLIC_KEY")
    
    ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o ConnectTimeout=10 \
        -p ${SERVER_PORT:-22} ${SERVER_USER}@${SERVER_HOST} "
        mkdir -p ~/.ssh
        chmod 700 ~/.ssh
        touch ~/.ssh/authorized_keys
        chmod 600 ~/.ssh/authorized_keys
        
        if grep -qF '$public_key_content' ~/.ssh/authorized_keys 2>/dev/null; then
            echo '公钥已存在，跳过添加'
        else
            echo '$public_key_content' >> ~/.ssh/authorized_keys
            echo '公钥已添加到 authorized_keys'
        fi
    "
    
    log_success "公钥已添加到服务器"
}

verify_connection() {
    log_info "验证 SSH 免密登录..."
    
    if check_ssh_key_auth; then
        log_success "SSH 免密登录配置成功！"
        return 0
    else
        log_error "SSH 免密登录验证失败"
        log_info "请检查:"
        log_info "  1. 私钥内容是否正确"
        log_info "  2. 服务器上的 authorized_keys 是否包含正确的公钥"
        return 1
    fi
}

main() {
    echo ""
    echo "========================================"
    echo "  SSH 密钥免密登录配置"
    echo "========================================"
    echo ""
    log_info "目标服务器: ${SERVER_USER}@${SERVER_HOST}:${SERVER_PORT:-22}"
    echo ""
    
    if check_ssh_key_auth; then
        log_success "SSH 免密登录已配置成功，无需重复配置"
        exit 0
    fi
    
    log_warn "当前无法使用 SSH 密钥免密登录"
    echo ""
    
    setup_ssh_dir
    
    if [ -f "$PRIVATE_KEY" ]; then
        log_info "发现已有私钥: $PRIVATE_KEY"
        read -p "是否使用现有密钥? [y/n]: " use_existing
        if [[ ! "$use_existing" =~ ^[Yy]$ ]]; then
            log_info "将重新生成密钥对..."
            rm -f "$PRIVATE_KEY" "$PUBLIC_KEY"
            generate_keypair
        fi
    else
        read -p "请选择密钥来源: [1] 生成新密钥对  [2] 导入已有私钥: " choice
        case "$choice" in
            1)
                generate_keypair
                ;;
            2)
                import_private_key
                ;;
            *)
                log_error "无效选择"
                exit 1
                ;;
        esac
    fi
    
    add_public_key_to_server
    
    echo ""
    verify_connection
    
    echo ""
    log_success "配置完成！现在可以使用部署脚本了"
}

main "$@"
