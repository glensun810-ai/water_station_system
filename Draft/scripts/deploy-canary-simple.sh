#!/bin/bash
# ==========================================
# 简化版灰度部署脚本 - 本地执行版本
# ==========================================

echo "========================================"
echo "灰度环境部署 - 本地准备版本"
echo "========================================"

# 检查当前目录
if [ ! -d "Service_WaterManage" ]; then
    echo "错误：请在项目根目录执行"
    exit 1
fi

echo "检查本地文件..."
ls -la Service_WaterManage/backend/main.py Service_WaterManage/frontend/index.html 2>/dev/null || {
    echo "错误：项目文件不存在"
    exit 1
}

echo "✅ 本地文件检查通过"

# 显示部署所需信息
echo ""
echo "部署信息："
echo "  服务器IP: 120.76.156.83"
echo "  灰度端口: 8001"
echo "  灰度域名: canary.jhw-ai.com"
echo "  灰度数据库: waterms_canary.db"
echo ""

echo "问题： SSH连接失败，echo "解决方案： 需要通过阿里云控制台VNC手动操作"
echo ""
echo "========================================"
echo "手动部署步骤（通过VNC）"
echo "========================================"
echo ""
echo "步骤1: 通过阿里云控制台VNC连接服务器"
echo "  - 登录: https://ecs.console.aliyun.com"
echo "  - 找到实例: 120.76.156.83"
echo "  - 点击: 远程连接 → VNC远程连接"
echo "  - 密码: sgl@810jhw"
echo ""
echo "步骤2: 在服务器上执行以下命令"
echo ""
cat << 'EOF'
# 启动SSH服务
systemctl start sshd
systemctl enable sshd

# 启动Nginx
systemctl start nginx
systemctl enable nginx

# 启动生产环境后端
cd /var/www/jhw-ai.com/backend
source venv/bin/activate
pkill -f uvicorn
nohup python -m uvicorn main:app --host 127.0.0.1 --port 8000 > /var/log/water-api.log 2>&1 &

# 创建灰度环境目录
mkdir -p /var/www/canary-jhw-ai.com/backend
mkdir -p /var/www/canary-jhw-ai.com/water
mkdir -p /var/www/canary-jhw-ai.com/water-admin

# 复制生产数据库到灰度环境
cp /var/www/jhw-ai.com/backend/waterms.db /var/www/canary-jhw-ai.com/backend/waterms_canary.db

# 复制后端代码到灰度环境
rsync -av --exclude='*.db' --exclude='*.sqlite' --exclude='__pycache__' --exclude='venv' \
    /var/www/jhw-ai.com/backend/ /var/www/canary-jhw-ai.com/backend/

# 修改灰度数据库配置
cd /var/www/canary-jhw-ai.com/backend
sed -i 's/waterms.db/waterms_canary.db/g' main.py

# 启动灰度环境后端
source venv/bin/activate
nohup python -m uvicorn main:app --host 127.0.0.1 --port 8001 > /var/log/water-canary-api.log 2>&1 &

# 复制前端文件
cp /var/www/jhw-ai.com/water/* /var/www/canary-jhw-ai.com/water/
cp /var/www/jhw-ai.com/water-admin/* /var/www/canary-jhw-ai.com/water-admin/

# 配置灰度Nginx
cat > /etc/nginx/conf.d/canary.conf << 'NGINX_EOF'
server {
    listen 8001;
    server_name canary.jhw-ai.com;
    
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
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
    }
}
NGINX_EOF

# 重启Nginx
nginx -t && nginx -s reload

echo ""
echo "✅ 灰度环境部署完成!"
echo ""
echo "访问地址:"
echo "  生产环境: http://120.76.156.83/water/"
echo "  灰度环境: http://120.76.156.83:8001/water/"
echo ""
EOF

echo "========================================"
echo "完成!"
echo "========================================"