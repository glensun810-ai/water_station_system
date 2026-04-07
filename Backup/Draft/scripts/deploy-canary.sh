#!/bin/bash
# ==========================================
# 灰度环境一键部署脚本
# ==========================================
#
# 使用方法：
# 1. 通过阿里云控制台 VNC 或 Workbench 连接服务器
# 2. 粘贴执行本脚本
#
# 服务器信息：
# - IP: 120.76.156.83
# - 密码: sgl@810jhw
# - 域名: jhw-ai.com
# ==========================================

echo "========================================"
echo "灰度环境一键部署"
echo "========================================"
echo ""

# 1. 启动基础服务
echo "[1/6] 启动基础服务..."
systemctl start sshd nginx
systemctl enable sshd nginx
echo "✅ SSH 和 Nginx 已启动"

# 2. 启动生产环境后端
echo ""
echo "[2/6] 启动生产环境后端..."
cd /var/www/jhw-ai.com/backend
source venv/bin/activate
pkill -f uvicorn || true
nohup python -m uvicorn main:app --host 127.0.0.1 --port 8000 > /var/log/water-api.log 2>&1 &
echo "✅ 生产环境后端已启动（端口 8000）"

# 3. 创建灰度环境目录
echo ""
echo "[3/6] 创建灰度环境..."
mkdir -p /var/www/canary-jhw-ai.com/{backend,water,water-admin}
echo "✅ 灰度环境目录已创建"

# 4. 复制数据库
echo ""
echo "[4/6] 复制生产数据库到灰度环境..."
cp /var/www/jhw-ai.com/backend/waterms.db /var/www/canary-jhw-ai.com/backend/waterms_canary.db
echo "✅ 灰度数据库已创建（waterms_canary.db）"

# 5. 复制后端代码
echo ""
echo "[5/6] 复制后端代码到灰度环境..."
rsync -av --exclude='*.db' --exclude='*.sqlite' --exclude='__pycache__' --exclude='venv' \
    /var/www/jhw-ai.com/backend/ /var/www/canary-jhw-ai.com/backend/

# 修改灰度数据库配置
cd /var/www/canary-jhw-ai.com/backend
sed -i 's/waterms\.db/waterms_canary.db/g' main.py

# 启动灰度后端
source venv/bin/activate
nohup python -m uvicorn main:app --host 127.0.0.1 --port 8001 > /var/log/water-canary-api.log 2>&1 &
echo "✅ 灰度环境后端已启动（端口 8001）"

# 6. 部署前端和配置Nginx
echo ""
echo "[6/6] 部署前端并配置 Nginx..."
cp -r /var/www/jhw-ai.com/water/* /var/www/canary-jhw-ai.com/water/
cp -r /var/www/jhw-ai.com/water-admin/* /var/www/canary-jhw-ai.com/water-admin/

# 配置灰度 Nginx
cat > /etc/nginx/conf.d/canary.conf << 'EOF'
server {
    listen 8001;
    server_name canary.jhw-ai.com 120.76.156.83;
    
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
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF

# 重启 Nginx
nginx -s reload
echo "✅ Nginx 已配置"

# 验证服务
echo ""
echo "========================================"
echo "验证服务状态"
echo "========================================"
sleep 3

echo ""
echo "后端进程："
ps aux | grep uvicorn | grep -v grep

echo ""
echo "端口监听："
netstat -tlnp | grep -E "8000|8001|80"

echo ""
echo "========================================"
echo "✅ 部署完成！"
echo "========================================"
echo ""
echo "🎉 访问地址："
echo ""
echo "【生产环境】"
echo "  用户端：http://120.76.156.83/water/"
echo "  管理后台：http://120.76.156.83/water-admin/"
echo "  API：http://120.76.156.83/api/"
echo ""
echo "【灰度环境】"
echo "  用户端：http://120.76.156.83:8001/water/"
echo "  管理后台：http://120.76.156.83:8001/water-admin/"
echo "  API：http://120.76.156.83:8001/api/"
echo ""
echo "========================================"
echo "部署日志："
echo "  生产环境: /var/log/water-api.log"
echo "  灰度环境: /var/log/water-canary-api.log"
echo "========================================"