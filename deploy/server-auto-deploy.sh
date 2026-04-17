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
