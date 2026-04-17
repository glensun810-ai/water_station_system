#!/bin/bash
######################################################################
# AI产业集群一键部署脚本 - 本地执行版
# 
# 执行方式：
#   1. 在本地运行此脚本，自动将代码上传到服务器并完成部署
#   2. 如果SSH连接失败，脚本会生成服务器端脚本供手动执行
#
# 目标服务器：120.76.156.83
# 域名：service.jhw-ai.com
# 部署目录：/www/wwwroot/service.jhw-ai.com
######################################################################

set -e

# 配置
SERVER_IP="120.76.156.83"
SERVER_USER="root"
DEPLOY_DIR="/www/wwwroot/service.jhw-ai.com"
DOMAIN="service.jhw-ai.com"
API_PORT="8008"
SSH_OPTS="-o StrictHostKeyChecking=no -o ConnectTimeout=10"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo_success() { echo "${GREEN}✓${NC} $1"; }
echo_error() { echo "${RED}✗${NC} $1"; }
echo_info() { echo "${YELLOW}→${NC} $1"; }
echo_step() { echo "\n${GREEN}[步骤 $1]${NC} $2\n"; }

# 检测项目根目录
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
echo "项目目录: $PROJECT_ROOT"

echo "======================================================================"
echo "  AI产业集群空间服务系统 - 一键部署"
echo "======================================================================"
echo ""
echo "目标服务器: $SERVER_IP"
echo "部署目录: $DEPLOY_DIR"
echo "域名: $DOMAIN"
echo ""

# 测试SSH连接
echo_step "1" "测试SSH连接..."
SSH_SUCCESS=false

if ssh $SSH_OPTS $SERVER_USER@$SERVER_IP "echo 'SSH连接成功'" 2>/dev/null; then
    SSH_SUCCESS=true
    echo_success "SSH连接正常"
else
    echo_error "SSH连接失败 - 服务器可能有安全策略限制"
    echo_info "将生成服务器端部署脚本..."
fi

if [ "$SSH_SUCCESS" = true ]; then
    # SSH连接成功，执行远程部署
    echo_step "2" "上传代码到服务器..."
    
    # 创建远程目录
    ssh $SSH_OPTS $SERVER_USER@$SERVER_IP "mkdir -p $DEPLOY_DIR"
    echo_success "远程目录创建完成"
    
    # 使用rsync同步代码（排除不必要的文件）
    echo_info "同步代码文件..."
    rsync -avz --progress \
        --exclude '.git' \
        --exclude '.idea' \
        --exclude '__pycache__' \
        --exclude '*.pyc' \
        --exclude '.venv' \
        --exclude 'node_modules' \
        --exclude 'logs/*' \
        --exclude '.pids' \
        --exclude 'Backup' \
        --exclude 'tests' \
        --exclude '*.db' \
        --exclude 'data/*' \
        --exclude '.DS_Store' \
        --exclude '*.log' \
        $PROJECT_ROOT/ $SERVER_USER@$SERVER_IP:$DEPLOY_DIR/
    
    echo_success "代码上传完成"
    
    echo_step "3" "远程安装Python依赖..."
    
    ssh $SSH_OPTS $SERVER_USER@$SERVER_IP << 'REMOTE_SCRIPT'
cd /www/wwwroot/service.jhw-ai.com

# 检查并安装Python3
if ! command -v python3 &> /dev/null; then
    if command -v yum &> /dev/null; then
        yum install -y python3 python3-pip python3-devel
    elif command -v apt-get &> /dev/null; then
        apt-get update && apt-get install -y python3 python3-pip python3-venv
    fi
fi

# 创建虚拟环境并安装依赖
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

mkdir -p logs data
REMOTE_SCRIPT
    
    echo_success "Python依赖安装完成"
    
    echo_step "4" "配置并启动后端服务..."
    
    ssh $SSH_OPTS $SERVER_USER@$SERVER_IP << 'REMOTE_SCRIPT'
# 停止旧服务
pkill -f "uvicorn apps.main:app" 2>/dev/null || true
sleep 2

cd /www/wwwroot/service.jhw-ai.com

# 启动新服务
source .venv/bin/activate
nohup uvicorn apps.main:app --host 0.0.0.0 --port 8008 > logs/api.log 2>&1 &
echo $! > .pids/api.pid

sleep 3

# 检查服务是否启动
if curl -s http://127.0.0.1:8008/health > /dev/null; then
    echo "API服务启动成功"
else
    echo "API服务启动可能需要更多时间，请稍后检查"
fi
REMOTE_SCRIPT
    
    echo_success "后端服务启动完成"
    
    echo_step "5" "配置Nginx反向代理..."
    
    ssh $SSH_OPTS $SERVER_USER@$SERVER_IP << 'REMOTE_SCRIPT'
# 检查Nginx
if ! command -v nginx &> /dev/null; then
    if command -v yum &> /dev/null; then
        yum install -y nginx
    elif command -v apt-get &> /dev/null; then
        apt-get install -y nginx
    fi
fi

# 创建Nginx配置
cat > /etc/nginx/conf.d/service.jhw-ai.com.conf << 'NGINX_CONF'
server {
    listen 80;
    server_name service.jhw-ai.com www.service.jhw-ai.com 120.76.156.83;
    
    client_max_body_size 50M;
    
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml;
    
    location /portal/ {
        alias /www/wwwroot/service.jhw-ai.com/portal/;
        index index.html;
        try_files $uri $uri/ /portal/index.html;
    }
    
    location = / {
        return 301 /portal/index.html;
    }
    
    location /space-frontend/ {
        alias /www/wwwroot/service.jhw-ai.com/space-frontend/;
        index index.html;
    }
    
    location /water/ {
        alias /www/wwwroot/service.jhw-ai.com/apps/water/frontend/;
        index index.html;
    }
    
    location /meeting-frontend/ {
        alias /www/wwwroot/service.jhw-ai.com/apps/meeting/frontend/;
        index index.html;
    }
    
    location /shared/ {
        alias /www/wwwroot/service.jhw-ai.com/shared/;
    }
    
    location /api/ {
        proxy_pass http://127.0.0.1:8008/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
    
    location /health {
        proxy_pass http://127.0.0.1:8008/health;
        access_log off;
    }
    
    location /docs {
        proxy_pass http://127.0.0.1:8008/docs;
    }
    
    location /redoc {
        proxy_pass http://127.0.0.1:8008/redoc;
    }
    
    location ~ /\. {
        deny all;
    }
    
    location ~* ^/(data|logs|\.pids|\.git|\.venv)/ {
        deny all;
    }
}
NGINX_CONF

# 测试并重启Nginx
nginx -t && systemctl restart nginx || nginx -t && service nginx restart

echo "Nginx配置完成"
REMOTE_SCRIPT
    
    echo_success "Nginx配置完成"
    
else
    # SSH连接失败，生成服务器端脚本
    echo_step "2" "生成服务器端部署脚本..."
    
    SERVER_SCRIPT="$PROJECT_ROOT/deploy/server-auto-deploy.sh"
    
    cat > "$SERVER_SCRIPT" << 'SERVERSCRIPT'
#!/bin/bash
# AI产业集群服务器端自动部署脚本
# 请将此脚本上传到服务器后执行

set -e
DEPLOY_DIR="/www/wwwroot/service.jhw-ai.com"
DOMAIN="service.jhw-ai.com"

echo "====== AI产业集群自动部署 ======"

# 安装依赖
if ! command -v python3 &> /dev/null; then
    yum install -y python3 python3-pip python3-devel nginx git || \
    apt-get update && apt-get install -y python3 python3-pip python3-venv nginx git
fi

# 创建目录
mkdir -p $DEPLOY_DIR && cd $DEPLOY_DIR
mkdir -p logs data

# 克隆或更新代码
if [ ! -d ".git" ]; then
    git clone https://github.com/glensun810-ai/water_station_system.git .
else
    git pull
fi

# 安装Python依赖
python3 -m venv .venv && source .venv/bin/activate
pip install --upgrade pip && pip install -r requirements.txt

# 启动服务
pkill -f "uvicorn apps.main:app" 2>/dev/null || true
sleep 2
source .venv/bin/activate
nohup uvicorn apps.main:app --host 0.0.0.0 --port 8008 > logs/api.log 2>&1 &
sleep 3

# 配置Nginx
cat > /etc/nginx/conf.d/$DOMAIN.conf << 'EOF'
server {
    listen 80;
    server_name service.jhw-ai.com www.service.jhw-ai.com 120.76.156.83;
    client_max_body_size 50M;
    
    location /portal/ { alias /www/wwwroot/service.jhw-ai.com/portal/; index index.html; }
    location = / { return 301 /portal/index.html; }
    location /space-frontend/ { alias /www/wwwroot/service.jhw-ai.com/space-frontend/; }
    location /water/ { alias /www/wwwroot/service.jhw-ai.com/apps/water/frontend/; }
    location /meeting-frontend/ { alias /www/wwwroot/service.jhw-ai.com/apps/meeting/frontend/; }
    location /api/ { proxy_pass http://127.0.0.1:8008/api/; proxy_set_header Host $host; }
    location /health { proxy_pass http://127.0.0.1:8008/health; }
    location /docs { proxy_pass http://127.0.0.1:8008/docs; }
}
EOF

nginx -t && systemctl restart nginx || nginx -t && service nginx restart

# 验证部署
echo ""
echo "====== 部署完成 ======"
curl -s http://127.0.0.1:8008/health && echo " - API正常"
curl -s http://127.0.0.1/health && echo " - Nginx正常"
echo ""
echo "访问地址: http://$DOMAIN/portal/index.html"
echo "IP访问: http://120.76.156.83/portal/index.html"
SERVERSCRIPT
    
    chmod +x "$SERVER_SCRIPT"
    
    echo_success "服务器端脚本已生成: $SERVER_SCRIPT"
    echo_info "请将此脚本上传到服务器执行："
    echo ""
    echo "  方式1: 通过宝塔面板上传文件"
    echo "  方式2: 通过FTP上传"
    echo "  方式3: 通过阿里云控制台远程执行"
    echo ""
    echo "  执行命令: chmod +x server-auto-deploy.sh && sudo ./server-auto-deploy.sh"
fi

echo_step "6" "验证部署结果..."

if [ "$SSH_SUCCESS" = true ]; then
    # 测试访问
    echo_info "测试API服务..."
    API_RESULT=$(ssh $SSH_OPTS $SERVER_USER@$SERVER_IP "curl -s http://127.0.0.1:8008/health")
    echo_success "API: $API_RESULT"
    
    echo_info "测试Nginx代理..."
    NGINX_RESULT=$(ssh $SSH_OPTS $SERVER_USER@$SERVER_IP "curl -s http://127.0.0.1/health")
    echo_success "Nginx: $NGINX_RESULT"
    
    echo_info "测试域名访问..."
    DOMAIN_RESULT=$(curl -s --max-time 10 http://$DOMAIN/health 2>/dev/null || echo "域名未解析或无法访问")
    echo "域名访问: $DOMAIN_RESULT"
    
    echo_info "测试IP访问..."
    IP_RESULT=$(curl -s --max-time 10 http://$SERVER_IP/health 2>/dev/null || echo "无法访问")
    echo "IP访问: $IP_RESULT"
fi

echo ""
echo "======================================================================"
echo "  部署结果"
echo "======================================================================"
echo ""
if [ "$SSH_SUCCESS" = true ]; then
    echo_success "部署已完成！"
    echo ""
    echo "访问地址:"
    echo "  http://$DOMAIN/portal/index.html"
    echo "  http://$SERVER_IP/portal/index.html"
    echo ""
else
    echo_info "由于SSH无法连接，请手动执行服务器端脚本"
    echo ""
    echo "脚本位置: $PROJECT_ROOT/deploy/server-auto-deploy.sh"
    echo ""
    echo "上传方式:"
    echo "  1. 宝塔面板: 文件管理 -> 上传"
    echo "  2. 阿里云控制台: 远程连接 -> 执行命令"
    echo "  3. FTP工具: 上传脚本文件"
    echo ""
fi
echo "======================================================================"