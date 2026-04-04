#!/bin/bash
# ==========================================
# 生产环境一键部署脚本 - 服务器端执行
# ==========================================
# ⚠️ 重要：此脚本会先备份生产数据，然后只更新代码
# 数据库文件不会被覆盖
# ==========================================

set -e

echo "========================================"
echo "生产环境一键部署"
echo "========================================"

# 配置
PROD_DIR="/var/www/jhw-ai.com"
BACKUP_DIR="/backup/waterms"
DATE=$(date +%Y%m%d_%H%M%S)

# ==========================================
# 步骤1: 备份生产数据
# ==========================================
echo "[步骤1] 备份生产数据库..."
mkdir -p ${BACKUP_DIR}/{database,code,config,logs}

if [ -f "${PROD_DIR}/backend/waterms.db" ]; then
    cp ${PROD_DIR}/backend/waterms.db ${BACKUP_DIR}/database/waterms_${DATE}.db
    DB_SIZE=$(ls -lh ${PROD_DIR}/backend/waterms.db | awk '{print $5}')
    echo "✅ 数据库备份完成: waterms_${DATE}.db (${DB_SIZE})"
else
    echo "⚠️ 数据库文件不存在，跳过备份"
fi

# 备份当前代码配置
if [ -f "${PROD_DIR}/backend/.env" ]; then
    cp ${PROD_DIR}/backend/.env ${BACKUP_DIR}/config/.env_${DATE}
fi

echo "备份目录: ${BACKUP_DIR}"

# ==========================================
# 步骤2: 启动基础服务
# ==========================================
echo "[步骤2] 启动基础服务..."
systemctl start sshd nginx
systemctl enable sshd nginx
echo "✅ SSH 和 Nginx 已启动"

# ==========================================
# 步骤3: 停止后端服务
# ==========================================
echo "[步骤3] 停止现有后端服务..."
pkill -f "uvicorn.*:8000" || true
pkill -f "uvicorn.*:8001" || true
sleep 2
echo "✅ 后端服务已停止"

# ==========================================
# 步骤4: 同步最新代码（不覆盖数据库）
# ==========================================
echo "[步骤4] 更新后端代码（保护数据库）..."
cd ${PROD_DIR}/backend

# 记录数据库大小用于验证
DB_BEFORE=$(ls -lh waterms.db 2>/dev/null | awk '{print $5}' || echo "N/A")
echo "数据库当前大小: ${DB_BEFORE}"

# 创建临时目录存放新代码
mkdir -p /tmp/backend_update

# 如果本地有上传的代码包，使用它
# 否则使用 git 拉取最新代码（如果有 git）
if [ -f "/tmp/backend_latest.tar" ]; then
    echo "使用上传的代码包..."
    cd /tmp/backend_update
    tar -xf /tmp/backend_latest.tar
else
    echo "使用服务器现有代码..."
    # 从灰度环境复制最新代码（如果灰度环境已部署）
    if [ -d "/var/www/canary-jhw-ai.com/backend" ]; then
        echo "从灰度环境复制最新代码..."
        rsync -av --exclude='*.db' --exclude='*.sqlite' --exclude='__pycache__' --exclude='venv' --exclude='.git' --exclude='*.log' \
            /var/www/canary-jhw-ai.com/backend/ ${PROD_DIR}/backend/
    else
        echo "使用当前生产环境代码..."
    fi
fi

# 验证数据库未被覆盖
DB_AFTER=$(ls -lh ${PROD_DIR}/backend/waterms.db 2>/dev/null | awk '{print $5}' || echo "N/A")
if [ "$DB_BEFORE" != "N/A" ] && [ "$DB_BEFORE" = "$DB_AFTER" ]; then
    echo "✅ 数据库验证通过，未被覆盖"
else
    echo "⚠️ 数据库大小变化: ${DB_BEFORE} -> ${DB_AFTER}"
fi

# ==========================================
# 步骤5: 安装/更新依赖
# ==========================================
echo "[步骤5] 检查并更新依赖..."
cd ${PROD_DIR}/backend

if [ ! -d "venv" ]; then
    echo "创建虚拟环境..."
    python3 -m venv venv
fi

source venv/bin/activate
pip install --upgrade pip -q

if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt -q
    echo "✅ 依赖已更新"
fi

# ==========================================
# 步骤6: 启动生产环境后端
# ==========================================
echo "[步骤6] 启动生产环境后端（端口8000）..."
cd ${PROD_DIR}/backend
source venv/bin/activate

nohup python -m uvicorn main:app --host 127.0.0.1 --port 8000 > /var/log/water-api.log 2>&1 &
sleep 3

# 检查是否启动成功
if curl -sf http://127.0.0.1:8000/api/health > /dev/null 2>&1; then
    echo "✅ 后端服务启动成功"
else
    echo "⚠️ 后端服务启动可能有问题，查看日志:"
    tail -20 /var/log/water-api.log
fi

# ==========================================
# 步骤7: 配置 Nginx
# ==========================================
echo "[步骤7] 配置 Nginx..."

cat > /etc/nginx/conf.d/water.conf << 'EOF'
server {
    listen 80;
    server_name jhw-ai.com 120.76.156.83;
    
    location /water/ {
        alias /var/www/jhw-ai.com/water/;
        index index.html;
        try_files $uri $uri/ /water/index.html;
    }
    
    location /water-admin/ {
        alias /var/www/jhw-ai.com/water-admin/;
        index admin.html;
        try_files $uri $uri/ /water-admin/admin.html;
    }
    
    location /api/ {
        proxy_pass http://127.0.0.1:8000/api/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    location / {
        return 301 /water/;
    }
}
EOF

nginx -t && nginx -s reload
echo "✅ Nginx 配置完成"

# ==========================================
# 步骤8: 验证部署
# ==========================================
echo "[步骤8] 验证部署..."

sleep 5

echo "端口监听状态:"
ss -tlnp | grep -E "8000|80"

echo "后端进程状态:"
ps aux | grep uvicorn | grep -v grep

echo "API 健康检查:"
curl -s http://127.0.0.1:8000/api/health

echo ""
echo "========================================"
echo "✅ 生产环境部署完成!"
echo "========================================"
echo ""
echo "访问地址:"
echo "  用户端: http://120.76.156.83/water/"
echo "  管理后台: http://120.76.156.83/water-admin/"
echo ""
echo "备份位置: ${BACKUP_DIR}/database/waterms_${DATE}.db"
echo ""
echo "测试账号: admin / admin123"
echo ""