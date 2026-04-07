#!/bin/bash
# ==========================================
# 一键部署脚本 - 本地执行
# ==========================================
# 
# 使用方法：bash deploy-simple.sh
# ==========================================

SERVER="120.76.156.83"
PASSWORD="sgl@810jhw"

echo "========================================"
echo "灰度环境一键部署"
echo "========================================"
echo ""
echo "服务器: $SERVER"
echo "密码: $PASSWORD"
echo ""

# 尝试多种SSH连接方式
echo "[1/3] 尝试连接服务器..."

# 方式1: 标准SSH
if sshpass -p "$PASSWORD" ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o ConnectTimeout=5 root@$SERVER "echo '连接成功'" 2>/dev/null; then
    echo "✅ SSH连接成功"
    CONNECT_OK=true
else
    echo "❌ SSH连接失败"
    echo ""
    echo "========================================"
    echo "需要手动操作"
    echo "========================================"
    echo ""
    echo "请按照以下步骤操作（只需2分钟）："
    echo ""
    echo "步骤1: 打开阿里云控制台"
    echo "  https://ecs.console.aliyun.com"
    echo ""
    echo "步骤2: 找到服务器实例（IP: $SERVER）"
    echo ""
    echo "步骤3: 点击'远程连接' → 'VNC远程连接'"
    echo ""
    echo "步骤4: 输入密码: $PASSWORD"
    echo ""
    echo "步骤5: 在VNC中粘贴执行以下命令（全选复制）："
    echo ""
    cat << 'VNC_COMMAND'
systemctl start sshd nginx
cd /var/www/jhw-ai.com/backend
source venv/bin/activate
pkill -f uvicorn || true
nohup python -m uvicorn main:app --host 127.0.0.1 --port 8000 > /var/log/water-api.log 2>&1 &
mkdir -p /var/www/canary-jhw-ai.com/{backend,water,water-admin}
cp /var/www/jhw-ai.com/backend/waterms.db /var/www/canary-jhw-ai.com/backend/waterms_canary.db
rsync -a --exclude='*.db' --exclude='*.sqlite' --exclude='__pycache__' --exclude='venv' /var/www/jhw-ai.com/backend/ /var/www/canary-jhw-ai.com/backend/
cd /var/www/canary-jhw-ai.com/backend
sed -i 's/waterms\.db/waterms_canary.db/g' main.py
source venv/bin/activate
nohup python -m uvicorn main:app --host 127.0.0.1 --port 8001 > /var/log/water-canary-api.log 2>&1 &
cp -r /var/www/jhw-ai.com/water/* /var/www/canary-jhw-ai.com/water/
cp -r /var/www/jhw-ai.com/water-admin/* /var/www/canary-jhw-ai.com/water-admin/
cat > /etc/nginx/conf.d/canary.conf << 'EOF'
server {
    listen 8001;
    location /water/ {
        alias /var/www/canary-jhw-ai.com/water/;
        index index.html;
    }
    location /water-admin/ {
        alias /var/www/canary-jhw-ai.com/water-admin/;
        index admin.html;
    }
    location /api/ {
        proxy_pass http://127.0.0.1:8001/api/;
    }
}
EOF
nginx -s reload
echo ""
echo "✅ 部署完成！"
echo ""
echo "访问地址："
echo "  生产: http://120.76.156.83/water/"
echo "  灰度: http://120.76.156.83:8001/water/"
VNC_COMMAND
    echo ""
    exit 1
fi

# 如果SSH连接成功，执行部署
if [ "$CONNECT_OK" = true ]; then
    echo ""
    echo "[2/3] 开始部署..."
    
    # 部署脚本
    sshpass -p "$PASSWORD" ssh root@$SERVER << 'REMOTE_SCRIPT'
# 启动基础服务
systemctl start sshd nginx
systemctl enable sshd nginx

# 启动生产环境
cd /var/www/jhw-ai.com/backend
source venv/bin/activate
pkill -f uvicorn || true
nohup python -m uvicorn main:app --host 127.0.0.1 --port 8000 > /var/log/water-api.log 2>&1 &

# 创建灰度环境
mkdir -p /var/www/canary-jhw-ai.com/{backend,water,water-admin}
cp /var/www/jhw-ai.com/backend/waterms.db /var/www/canary-jhw-ai.com/backend/waterms_canary.db
rsync -a --exclude='*.db' --exclude='*.sqlite' --exclude='__pycache__' --exclude='venv' \
    /var/www/jhw-ai.com/backend/ /var/www/canary-jhw-ai.com/backend/

# 配置灰度环境
cd /var/www/canary-jhw-ai.com/backend
sed -i 's/waterms\.db/waterms_canary.db/g' main.py
source venv/bin/activate
nohup python -m uvicorn main:app --host 127.0.0.1 --port 8001 > /var/log/water-canary-api.log 2>&1 &

# 复制前端
cp -r /var/www/jhw-ai.com/water/* /var/www/canary-jhw-ai.com/water/
cp -r /var/www/jhw-ai.com/water-admin/* /var/www/canary-jhw-ai.com/water-admin/

# 配置Nginx
cat > /etc/nginx/conf.d/canary.conf << 'EOF'
server {
    listen 8001;
    location /water/ {
        alias /var/www/canary-jhw-ai.com/water/;
        index index.html;
    }
    location /water-admin/ {
        alias /var/www/canary-jhw-ai.com/water-admin/;
        index admin.html;
    }
    location /api/ {
        proxy_pass http://127.0.0.1:8001/api/;
    }
}
EOF

nginx -s reload
echo "✅ 部署完成"
REMOTE_SCRIPT

    echo ""
    echo "[3/3] 验证部署..."
    
    # 验证服务
    sleep 3
    curl -s http://$SERVER/api/health > /dev/null && echo "✅ 生产环境正常" || echo "⚠️  生产环境异常"
    curl -s http://$SERVER:8001/api/health > /dev/null && echo "✅ 灰度环境正常" || echo "⚠️  灰度环境异常"
    
    echo ""
    echo "========================================"
    echo "✅ 部署完成！"
    echo "========================================"
    echo ""
    echo "访问地址："
    echo "  生产用户端: http://$SERVER/water/"
    echo "  生产管理后台: http://$SERVER/water-admin/"
    echo "  灰度用户端: http://$SERVER:8001/water/"
    echo "  灰度管理后台: http://$SERVER:8001/water-admin/"
fi