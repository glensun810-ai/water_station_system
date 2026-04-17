# AI产业集群部署指南

## 部署信息
- 服务器IP: 120.76.156.83
- 部署目录: /www/wwwroot/service.jhw-ai.com
- 域名: service.jhw-ai.com
- API端口: 8008

## 部署方式

### 方式一：宝塔面板执行（推荐）

1. 登录宝塔面板
2. 点击「终端」或「文件」
3. 上传脚本文件 `deploy/server-auto-deploy.sh`
4. 在终端执行：
```bash
chmod +x /www/wwwroot/server-auto-deploy.sh
sudo /www/wwwroot/server-auto-deploy.sh
```

### 方式二：阿里云控制台远程执行

1. 登录阿里云控制台
2. 找到服务器实例
3. 点击「远程连接」
4. 复制以下命令直接执行：

```bash
# 一键部署命令
cd /tmp && curl -o deploy.sh https://raw.githubusercontent.com/glensun810-ai/water_station_system/main/deploy/server-auto-deploy.sh && chmod +x deploy.sh && sudo ./deploy.sh
```

### 方式三：手动复制脚本执行

1. 登录服务器终端
2. 创建脚本文件：
```bash
cat > /www/wwwroot/deploy.sh << 'EOF'
#!/bin/bash
set -e
DEPLOY_DIR="/www/wwwroot/service.jhw-ai.com"
DOMAIN="service.jhw-ai.com"

echo "====== AI产业集群自动部署 ======"

# 安装依赖
if ! command -v python3 &> /dev/null; then
    yum install -y python3 python3-pip python3-devel nginx git || \
    apt-get update && apt-get install -y python3 python3-pip python3-venv nginx git
fi

# 创建目录并克隆代码
mkdir -p $DEPLOY_DIR && cd $DEPLOY_DIR
mkdir -p logs data

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
cat > /etc/nginx/conf.d/$DOMAIN.conf << 'NGINX'
server {
    listen 80;
    server_name service.jhw-ai.com www.service.jhw-ai.com 120.76.156.83;
    client_max_body_size 50M;
    
    gzip on;
    gzip_types text/plain text/css application/json application/javascript;
    
    location /portal/ {
        alias /www/wwwroot/service.jhw-ai.com/portal/;
        index index.html;
        try_files $uri $uri/ /portal/index.html;
    }
    location = / { return 301 /portal/index.html; }
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
    location /health { proxy_pass http://127.0.0.1:8008/health; }
    location /docs { proxy_pass http://127.0.0.1:8008/docs; }
    location /redoc { proxy_pass http://127.0.0.1:8008/redoc; }
    location ~ /\. { deny all; }
    location ~* ^/(data|logs|\.git|\.venv)/ { deny all; }
}
NGINX

nginx -t && systemctl restart nginx || nginx -t && service nginx restart

echo ""
echo "====== 部署完成 ======"
curl -s http://127.0.0.1:8008/health && echo " - API正常"
curl -s http://127.0.0.1/health && echo " - Nginx正常"
echo ""
echo "访问地址:"
echo "  http://$DOMAIN/portal/index.html"
echo "  http://120.76.156.83/portal/index.html"
EOF

chmod +x /www/wwwroot/deploy.sh
sudo /www/wwwroot/deploy.sh
```

## 验证部署

执行完成后，检查以下地址：

1. 健康检查: http://120.76.156.83/health
2. Portal首页: http://120.76.156.83/portal/index.html
3. API文档: http://120.76.156.83/docs

## 常见问题

### 如果域名无法访问
确认DNS解析是否指向 120.76.156.83

### 如果API服务未启动
检查日志：
```bash
tail -100 /www/wwwroot/service.jhw-ai.com/logs/api.log
```

### 重启服务
```bash
cd /www/wwwroot/service.jhw-ai.com
source .venv/bin/activate
pkill -f "uvicorn apps.main:app"
nohup uvicorn apps.main:app --host 0.0.0.0 --port 8008 > logs/api.log 2>&1 &
```

### 设置systemd服务（推荐）
```bash
cat > /etc/systemd/system/jhw-ai.service << 'EOF'
[Unit]
Description=AI产业集群服务
After=network.target

[Service]
Type=simple
WorkingDirectory=/www/wwwroot/service.jhw-ai.com
ExecStart=/www/wwwroot/service.jhw-ai.com/.venv/bin/uvicorn apps.main:app --host 0.0.0.0 --port 8008
Restart=always

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable jhw-ai
systemctl start jhw-ai
```