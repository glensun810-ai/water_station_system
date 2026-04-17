#!/bin/bash
######################################################################
# AI产业集群空间服务系统 - 生产环境部署脚本
# 
# 目标服务器：120.76.156.83
# 域名：service.jhw-ai.com
# 部署目录：/www/wwwroot/service.jhw-ai.com
# 
# 使用方法：
#   chmod +x deploy-server.sh
#   sudo ./deploy-server.sh
######################################################################

set -e

# 部署配置
DEPLOY_DIR="/www/wwwroot/service.jhw-ai.com"
DOMAIN="service.jhw-ai.com"
API_PORT=8008
BACKUP_DIR="/www/wwwroot/service.jhw-ai.com-backup"
REPO_URL="https://github.com/glensun810-ai/water_station_system.git"
BRANCH="main"

echo "======================================================================"
echo "  AI产业集群空间服务系统 - 生产环境部署"
echo "======================================================================"
echo ""
echo "部署目录: $DEPLOY_DIR"
echo "域名: $DOMAIN"
echo "API端口: $API_PORT"
echo ""

# 检查是否为root用户
if [ "$EUID" -ne 0 ]; then 
    echo "请使用root用户执行此脚本"
    echo "   sudo ./deploy-server.sh"
    exit 1
fi

echo "[步骤1] 检查系统依赖..."
echo ""

# 检查Python3
if ! command -v python3 &> /dev/null; then
    echo "安装Python3..."
    if command -v yum &> /dev/null; then
        yum install -y python3 python3-pip python3-devel
    elif command -v apt-get &> /dev/null; then
        apt-get update
        apt-get install -y python3 python3-pip python3-dev python3-venv
    fi
fi
echo "✓ Python3已安装: $(python3 --version)"

# 检查pip
if ! command -v pip3 &> /dev/null; then
    echo "安装pip3..."
    python3 -m ensurepip --upgrade
fi
echo "✓ pip3已安装: $(pip3 --version)"

# 检查Nginx
if ! command -v nginx &> /dev/null; then
    echo "安装Nginx..."
    if command -v yum &> /dev/null; then
        yum install -y nginx
    elif command -v apt-get &> /dev/null; then
        apt-get install -y nginx
    fi
fi
echo "✓ Nginx已安装"

# 检查git
if ! command -v git &> /dev/null; then
    echo "安装git..."
    if command -v yum &> /dev/null; then
        yum install -y git
    elif command -v apt-get &> /dev/null; then
        apt-get install -y git
    fi
fi
echo "✓ git已安装"

# 检查Node.js（如果前端需要构建）
if ! command -v node &> /dev/null; then
    echo "Node.js未安装，跳过前端构建步骤"
    SKIP_FRONTEND_BUILD=true
else
    echo "✓ Node.js已安装: $(node --version)"
    SKIP_FRONTEND_BUILD=false
fi

echo ""
echo "[步骤2] 创建部署目录..."
echo ""

# 备份旧版本
if [ -d "$DEPLOY_DIR" ]; then
    echo "备份旧版本到 $BACKUP_DIR..."
    rm -rf "$BACKUP_DIR"
    mv "$DEPLOY_DIR" "$BACKUP_DIR"
fi

# 创建部署目录
mkdir -p "$DEPLOY_DIR"
mkdir -p "$DEPLOY_DIR/logs"
mkdir -p "$DEPLOY_DIR/data"

echo "✓ 部署目录创建完成"

echo ""
echo "[步骤3] 克隆代码..."
echo ""

# 从GitHub克隆代码
echo "克隆代码到 $DEPLOY_DIR..."
cd "$DEPLOY_DIR"

git clone "$REPO_URL" . 2>/dev/null || {
    echo "仓库已存在，尝试拉取最新代码..."
    git fetch origin
    git reset --hard origin/$BRANCH
}

# 切换到指定分支
git checkout $BRANCH 2>/dev/null || git checkout -b $BRANCH origin/$BRANCH
git pull origin $BRANCH

echo "✓ 代码克隆完成"
echo "   当前版本: $(git log --oneline -1)"

echo ""
echo "[步骤4] 安装Python依赖..."
echo ""

cd "$DEPLOY_DIR"

# 创建虚拟环境
python3 -m venv .venv
source .venv/bin/activate

# 安装依赖
pip3 install --upgrade pip
pip3 install -r requirements.txt

echo "✓ Python依赖安装完成"

echo ""
echo "[步骤5] 前端构建（如有需要）..."
echo ""

if [ "$SKIP_FRONTEND_BUILD" = false ]; then
    # 检查是否有需要构建的前端项目
    if [ -f "package.json" ]; then
        echo "发现package.json，执行前端构建..."
        npm install
        npm run build
        echo "✓ 前端构建完成"
    else
        echo "未发现需要构建的前端项目，跳过"
    fi
else
    echo "跳过前端构建"
fi

echo ""
echo "[步骤6] 初始化数据库..."
echo ""

# 创建数据库目录
mkdir -p "$DEPLOY_DIR/data"

# 检查数据库是否存在
if [ ! -f "$DEPLOY_DIR/data/app.db" ]; then
    echo "数据库将在首次启动时自动创建..."
fi

echo "✓ 数据库配置完成"

echo ""
echo "[步骤7] 配置Systemd服务..."
echo ""

# 创建systemd服务文件
cat > /etc/systemd/system/jhw-ai.service << 'EOF'
[Unit]
Description=AI产业集群空间服务系统
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/www/wwwroot/service.jhw-ai.com
Environment="PATH=/www/wwwroot/service.jhw-ai.com/.venv/bin"
ExecStart=/www/wwwroot/service.jhw-ai.com/.venv/bin/uvicorn apps.main:app --host 0.0.0.0 --port 8008
Restart=always
RestartSec=10
StandardOutput=append:/www/wwwroot/service.jhw-ai.com/logs/api_service.log
StandardError=append:/www/wwwroot/service.jhw-ai.com/logs/api_error.log

[Install]
WantedBy=multi-user.target
EOF

# 启用服务
systemctl daemon-reload
systemctl enable jhw-ai

echo "✓ Systemd服务配置完成"

echo ""
echo "[步骤8] 配置Nginx..."
echo ""

# 创建Nginx配置文件
cat > /etc/nginx/conf.d/service.jhw-ai.com.conf << 'EOF'
# AI产业集群空间服务系统 Nginx配置
# 域名：service.jhw-ai.com
# IP：120.76.156.83
# API端口：8008

server {
    listen 80;
    server_name service.jhw-ai.com www.service.jhw-ai.com 120.76.156.83;
    
    # 日志配置
    access_log /var/log/nginx/service.jhw-ai.com_access.log;
    error_log /var/log/nginx/service.jhw-ai.com_error.log;
    
    # 客户端请求体大小限制
    client_max_body_size 50M;
    
    # Gzip压缩
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/javascript application/json application/xml;
    
    # Portal统一入口（首页）
    location /portal/ {
        alias /www/wwwroot/service.jhw-ai.com/portal/;
        index index.html;
        try_files $uri $uri/ /portal/index.html;
        
        # 静态资源缓存
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2)$ {
            expires 7d;
            add_header Cache-Control "public, immutable";
        }
    }
    
    # 根路径重定向到Portal首页
    location = / {
        return 301 /portal/index.html;
    }
    
    # Space前端
    location /space-frontend/ {
        alias /www/wwwroot/service.jhw-ai.com/space-frontend/;
        index index.html;
        try_files $uri $uri/ /space-frontend/index.html;
        
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2)$ {
            expires 7d;
            add_header Cache-Control "public, immutable";
        }
    }
    
    # Water前端
    location /water/ {
        alias /www/wwwroot/service.jhw-ai.com/apps/water/frontend/;
        index index.html;
        try_files $uri $uri/ /water/index.html;
        
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2)$ {
            expires 7d;
            add_header Cache-Control "public, immutable";
        }
    }
    
    # Meeting前端
    location /meeting-frontend/ {
        alias /www/wwwroot/service.jhw-ai.com/apps/meeting/frontend/;
        index index.html;
        try_files $uri $uri/ /meeting-frontend/index.html;
        
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2)$ {
            expires 7d;
            add_header Cache-Control "public, immutable";
        }
    }
    
    # Shared静态资源
    location /shared/ {
        alias /www/wwwroot/service.jhw-ai.com/shared/;
        
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2)$ {
            expires 30d;
            add_header Cache-Control "public, immutable";
        }
    }
    
    # API反向代理（统一端口8008）
    location /api/ {
        proxy_pass http://127.0.0.1:8008/api/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket支持
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # 超时配置
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
        
        # 缓冲配置
        proxy_buffering on;
        proxy_buffer_size 4k;
        proxy_buffers 8 4k;
    }
    
    # 健康检查端点
    location /health {
        proxy_pass http://127.0.0.1:8008/health;
        proxy_set_header Host $host;
        access_log off;
    }
    
    # API文档
    location /docs {
        proxy_pass http://127.0.0.1:8008/docs;
        proxy_set_header Host $host;
    }
    
    location /redoc {
        proxy_pass http://127.0.0.1:8008/redoc;
        proxy_set_header Host $host;
    }
    
    # OpenAPI schema
    location /openapi.json {
        proxy_pass http://127.0.0.1:8008/openapi.json;
        proxy_set_header Host $host;
    }
    
    # 禁止访问隐藏文件
    location ~ /\. {
        deny all;
        access_log off;
        log_not_found off;
    }
    
    # 禁止访问敏感目录
    location ~* ^/(data|logs|\.pids|Backup|tests|scripts|\.git|\.venv)/ {
        deny all;
        access_log off;
        log_not_found off;
    }
}
EOF

# 删除默认配置（如果存在）
rm -f /etc/nginx/sites-enabled/default
rm -f /etc/nginx/conf.d/default.conf

# 测试Nginx配置
nginx -t || {
    echo "Nginx配置错误，请检查配置文件"
    exit 1
}

echo "✓ Nginx配置完成"

echo ""
echo "[步骤9] 启动服务..."
echo ""

# 启动API服务
systemctl start jhw-ai || {
    echo "API服务启动失败，请检查日志"
    systemctl status jhw-ai
    exit 1
}

# 等待服务启动
sleep 5

# 检查服务状态
systemctl status jhw-ai --no-pager || {
    echo "API服务运行异常"
    journalctl -u jhw-ai -n 50
    exit 1
}

echo "✓ API服务已启动"

# 启动Nginx
systemctl restart nginx || {
    echo "Nginx启动失败"
    systemctl status nginx
    exit 1
}

echo "✓ Nginx已启动"

echo ""
echo "[步骤10] 健康检查..."
echo ""

# 检查API服务
sleep 3
API_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8008/health)
if [ "$API_STATUS" = "200" ]; then
    echo "✓ API服务健康检查通过 (状态码: 200)"
else
    echo "⚠ API服务健康检查异常 (状态码: $API_STATUS)"
    echo "   请检查日志: tail -100 $DEPLOY_DIR/logs/api_service.log"
fi

# 检查Nginx
NGINX_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1/health)
if [ "$NGINX_STATUS" = "200" ]; then
    echo "✓ Nginx代理配置正确 (状态码: 200)"
else
    echo "⚠ Nginx代理可能需要调整 (状态码: $NGINX_STATUS)"
fi

# 测试域名访问
echo ""
echo "测试域名访问..."
DOMAIN_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://$DOMAIN/health --connect-timeout 5 || echo "000")
if [ "$DOMAIN_STATUS" = "200" ]; then
    echo "✓ 域名访问正常: http://$DOMAIN/health (状态码: 200)"
else
    echo "⚠ 域名访问异常 (状态码: $DOMAIN_STATUS)"
    echo "   请确认DNS解析已正确指向此服务器"
fi

# 测试IP访问
IP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://120.76.156.83/health --connect-timeout 5 || echo "000")
if [ "$IP_STATUS" = "200" ]; then
    echo "✓ IP访问正常: http://120.76.156.83/health (状态码: 200)"
else
    echo "⚠ IP访问异常 (状态码: $IP_STATUS)"
fi

echo ""
echo "[步骤11] 配置防火墙..."
echo ""

# 检查firewalld或ufw
if command -v firewall-cmd &> /dev/null; then
    echo "配置firewalld..."
    firewall-cmd --permanent --add-port=80/tcp
    firewall-cmd --permanent --add-port=443/tcp
    firewall-cmd --permanent --add-port=8008/tcp
    firewall-cmd --reload
    echo "✓ firewalld配置完成"
elif command -v ufw &> /dev/null; then
    echo "配置ufw..."
    ufw allow 80/tcp
    ufw allow 443/tcp
    ufw allow 8008/tcp
    echo "✓ ufw配置完成"
fi

echo ""
echo "======================================================================"
echo "  🎉 部署完成！"
echo "======================================================================"
echo ""
echo "访问地址："
echo "  🌐 Portal首页:    http://$DOMAIN/portal/index.html"
echo "  🌐 IP访问:        http://120.76.156.83/portal/index.html"
echo "  📊 API文档:       http://$DOMAIN/docs"
echo "  📊 健康检查:      http://$DOMAIN/health"
echo ""
echo "管理命令："
echo "  启动服务:   systemctl start jhw-ai"
echo "  停止服务:   systemctl stop jhw-ai"
echo "  重启服务:   systemctl restart jhw-ai"
echo "  查看状态:   systemctl status jhw-ai"
echo "  查看日志:   tail -f $DEPLOY_DIR/logs/api_service.log"
echo ""
echo "后续配置："
echo "  1. 确认DNS解析: $DOMAIN -> 120.76.156.83"
echo "  2. 申请SSL证书（推荐使用Let's Encrypt或阿里云免费证书）"
echo "  3. 配置HTTPS（参考Nginx配置中的HTTPS部分）"
echo ""
echo "======================================================================"