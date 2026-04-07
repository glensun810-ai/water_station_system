#!/bin/bash
# ==========================================
# 灰度环境完整部署脚本 - 服务器端执行
# ==========================================
# 此脚本通过阿里云控制台 VNC/Workbench 执行
# 将本地最新代码部署到灰度环境（端口8001）
# ==========================================

set -e

echo "========================================"
echo "灰度环境部署脚本 - 服务器端"
echo "========================================"

# 配置
CANARY_PORT=8001
CANARY_DIR="/var/www/canary-jhw-ai.com"
PROD_DIR="/var/www/jhw-ai.com"
CANARY_DB="waterms_canary.db"
PROD_DB="waterms.db"

echo "[步骤1] 启动基础服务..."
systemctl start sshd nginx
systemctl enable sshd nginx

echo "[步骤2] 启动生产环境后端（端口8000）..."
cd ${PROD_DIR}/backend
if [ -d "venv" ]; then
    source venv/bin/activate
    pkill -f "uvicorn.*:8000" || true
    sleep 2
    nohup python -m uvicorn main:app --host 127.0.0.1 --port 8000 > /var/log/water-api.log 2>&1 &
    echo "生产环境后端已启动"
fi

echo "[步骤3] 创建灰度环境目录..."
mkdir -p ${CANARY_DIR}/backend
mkdir -p ${CANARY_DIR}/water
mkdir -p ${CANARY_DIR}/water-admin

echo "[步骤4] 复制生产数据库到灰度环境..."
if [ -f "${PROD_DIR}/backend/${PROD_DB}" ]; then
    cp ${PROD_DIR}/backend/${PROD_DB} ${CANARY_DIR}/backend/${CANARY_DB}
    echo "数据库已复制: ${CANARY_DB}"
else
    echo "警告: 生产数据库不存在"
fi

echo "[步骤5] 复制后端代码到灰度环境..."
rsync -av --exclude='*.db' --exclude='*.sqlite' --exclude='__pycache__' --exclude='venv' --exclude='.git' --exclude='*.log' \
    ${PROD_DIR}/backend/ ${CANARY_DIR}/backend/

echo "[步骤6] 配置灰度数据库..."
cd ${CANARY_DIR}/backend
sed -i "s/${PROD_DB}/${CANARY_DB}/g" main.py 2>/dev/null || true
if [ -f ".env" ]; then
    sed -i "s/${PROD_DB}/${CANARY_DB}/g" .env
else
    echo "DATABASE_URL=${CANARY_DB}" > .env
fi

echo "[步骤7] 创建灰度环境虚拟环境..."
if [ ! -d "${CANARY_DIR}/backend/venv" ]; then
    cd ${CANARY_DIR}/backend
    python3 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip -q
    pip install -r requirements.txt -q
    echo "依赖已安装"
else
    echo "虚拟环境已存在，使用现有环境"
fi

echo "[步骤8] 启动灰度环境后端（端口8001）..."
cd ${CANARY_DIR}/backend
source venv/bin/activate
pkill -f "uvicorn.*:8001" || true
sleep 2
nohup python -m uvicorn main:app --host 127.0.0.1 --port ${CANARY_PORT} > /var/log/water-canary-api.log 2>&1 &
sleep 3
echo "灰度后端已启动"

echo "[步骤9] 复制前端文件..."
cp -r ${PROD_DIR}/water/* ${CANARY_DIR}/water/ 2>/dev/null || true
cp -r ${PROD_DIR}/water-admin/* ${CANARY_DIR}/water-admin/ 2>/dev/null || true

echo "[步骤10] 配置灰度 Nginx..."
cat > /etc/nginx/conf.d/canary.conf << 'EOF'
server {
    listen 8001;
    server_name canary.jhw-ai.com;
    
    location /water/ {
        alias /var/www/canary-jhw-ai.com/water/;
        index index.html;
        try_files $uri $uri/ /water/index.html;
    }
    
    location /water-admin/ {
        alias /var/www/canary-jhw-ai.com/water-admin/;
        index admin.html;
        try_files $uri $uri/ /water-admin/admin.html;
    }
    
    location /api/ {
        proxy_pass http://127.0.0.1:8001/api/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
    
    location / {
        return 301 /water/;
    }
}
EOF

echo "[步骤11] 重载 Nginx..."
nginx -t && nginx -s reload

echo "[步骤12] 验证服务..."
sleep 5

echo "检查端口监听:"
ss -tlnp | grep -E "8000|8001|80"

echo "检查后端进程:"
ps aux | grep uvicorn | grep -v grep

echo "检查 API 健康状态:"
curl -s http://127.0.0.1:8000/api/health | head -c 100
curl -s http://127.0.0.1:8001/api/health | head -c 100

echo ""
echo "========================================"
echo "✅ 灰度环境部署完成!"
echo "========================================"
echo ""
echo "访问地址:"
echo "  生产环境用户端: http://120.76.156.83/water/"
echo "  生产环境管理后台: http://120.76.156.83/water-admin/"
echo ""
echo "  灰度环境用户端: http://120.76.156.83:8001/water/"
echo "  灰度环境管理后台: http://120.76.156.83:8001/water-admin/"
echo ""