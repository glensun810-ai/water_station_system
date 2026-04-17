#!/bin/bash
######################################################################
# AI产业集群空间服务系统 - 生产环境部署脚本
# 
# 目标服务器：120.76.156.83
# 域名：jhw-ai.com
# 部署目录：/var/www/jhw-ai
# 
# 使用方法：
#   1. 将此脚本和代码上传到服务器
#   2. chmod +x deploy-production.sh
#   3. sudo ./deploy-production.sh
######################################################################

set -e  # 遇到错误立即退出

# 部署配置
DEPLOY_DIR="/var/www/jhw-ai"
DOMAIN="jhw-ai.com"
API_PORT=8008
BACKUP_DIR="/var/www/jhw-ai-backup"

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
    echo "❌ 请使用root用户执行此脚本"
    echo "   sudo ./deploy-production.sh"
    exit 1
fi

echo "[步骤1] 检查系统依赖..."
echo ""

# 检查Python3
if ! command -v python3 &> /dev/null; then
    echo "安装Python3..."
    yum install -y python3 python3-pip || apt-get install -y python3 python3-pip
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
    yum install -y nginx || apt-get install -y nginx
fi
echo "✓ Nginx已安装"

# 检查git
if ! command -v git &> /dev/null; then
    echo "安装git..."
    yum install -y git || apt-get install -y git
fi
echo "✓ git已安装"

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

# 克隆仓库（根据实际情况调整）
git clone https://github.com/glensun810-ai/water_station_system.git . || {
    echo "❌ 克隆失败，请检查："
    echo "   1. GitHub仓库是否可访问"
    echo "   2. 是否有正确的访问权限"
    exit 1
}

# 切换到最新版本
git checkout feature/refactor-cleanup
git pull origin feature/refactor-cleanup

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
echo "[步骤5] 初始化数据库..."
echo ""

# 创建数据库目录
mkdir -p "$DEPLOY_DIR/data"

# 检查数据库是否存在
if [ ! -f "$DEPLOY_DIR/data/app.db" ]; then
    echo "创建数据库..."
    # 数据库会在首次启动时自动创建
fi

echo "✓ 数据库配置完成"

echo ""
echo "[步骤6] 配置Systemd服务..."
echo ""

# 复制服务配置文件
cp deploy/systemd/jhw-ai.service /etc/systemd/system/

# 启用服务
systemctl daemon-reload
systemctl enable jhw-ai

echo "✓ Systemd服务配置完成"

echo ""
echo "[步骤7] 配置Nginx..."
echo ""

# 复制Nginx配置
cp deploy/nginx.conf /etc/nginx/conf.d/jhw-ai.conf

# 删除默认配置（如果存在）
rm -f /etc/nginx/sites-enabled/default
rm -f /etc/nginx/conf.d/default.conf

# 测试Nginx配置
nginx -t || {
    echo "❌ Nginx配置错误，请检查配置文件"
    exit 1
}

echo "✓ Nginx配置完成"

echo ""
echo "[步骤8] 启动服务..."
echo ""

# 启动API服务
systemctl start jhw-ai || {
    echo "❌ API服务启动失败，请检查日志"
    systemctl status jhw-ai
    exit 1
}

# 等待服务启动
sleep 5

# 检查服务状态
systemctl status jhw-ai --no-pager || {
    echo "❌ API服务运行异常"
    journalctl -u jhw-ai -n 50
    exit 1
}

echo "✓ API服务已启动"

# 启动Nginx
systemctl restart nginx || {
    echo "❌ Nginx启动失败"
    systemctl status nginx
    exit 1
}

echo "✓ Nginx已启动"

echo ""
echo "[步骤9] 健康检查..."
echo ""

# 检查API服务
sleep 3
API_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8008/health)
if [ "$API_STATUS" = "200" ]; then
    echo "✓ API服务健康检查通过"
else
    echo "❌ API服务健康检查失败 (状态码: $API_STATUS)"
    echo "   请检查日志: tail -100 $DEPLOY_DIR/logs/api_service.log"
fi

# 检查Nginx
NGINX_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1/health)
if [ "$NGINX_STATUS" = "200" ]; then
    echo "✓ Nginx代理配置正确"
else
    echo "⚠ Nginx代理可能需要调整 (状态码: $NGINX_STATUS)"
fi

echo ""
echo "[步骤10] 配置防火墙..."
echo ""

# 检查firewalld或ufw
if command -v firewall-cmd &> /dev/null; then
    echo "配置firewalld..."
    firewall-cmd --permanent --add-port=80/tcp
    firewall-cmd --permanent --add-port=443/tcp
    firewall-cmd --reload
    echo "✓ firewalld配置完成"
elif command -v ufw &> /dev/null; then
    echo "配置ufw..."
    ufw allow 80/tcp
    ufw allow 443/tcp
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
echo "  1. 申请SSL证书（推荐使用阿里云免费证书）"
echo "  2. 配置HTTPS（参考 deploy/nginx.conf 中的HTTPS配置）"
echo "  3. 设置域名DNS解析到 120.76.156.83"
echo ""
echo "======================================================================"