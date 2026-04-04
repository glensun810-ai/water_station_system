#!/bin/bash
# ==========================================
# 服务器服务修复脚本 - 在服务器上执行
# ==========================================
# 
# 使用方法：
# 1. 登录阿里云控制台
# 2. 使用远程连接（VNC/Workbench）
# 3. 复制此脚本内容到服务器执行
# ==========================================

echo "========================================"
echo "服务器服务诊断与修复"
echo "========================================"

# 1. 检查SSH服务
echo ""
echo "[1] 检查SSH服务..."
systemctl status sshd || service ssh status

# 如果SSH服务未运行，启动它
if ! systemctl is-active --quiet sshd; then
    echo "启动SSH服务..."
    systemctl start sshd || service ssh start
    systemctl enable sshd || service ssh enable
fi

# 2. 检查防火墙
echo ""
echo "[2] 检查防火墙..."
if command -v firewall-cmd &> /dev/null; then
    firewall-cmd --state
    firewall-cmd --list-ports
    # 开放必要端口
    firewall-cmd --permanent --add-port=22/tcp
    firewall-cmd --permanent --add-port=80/tcp
    firewall-cmd --permanent --add-port=443/tcp
    firewall-cmd --permanent --add-port=8000/tcp
    firewall-cmd --permanent --add-port=8001/tcp
    firewall-cmd --reload
elif command -v ufw &> /dev/null; then
    ufw status
    ufw allow 22/tcp
    ufw allow 80/tcp
    ufw allow 443/tcp
    ufw allow 8000/tcp
    ufw allow 8001/tcp
fi

# 3. 检查Nginx
echo ""
echo "[3] 检查Nginx..."
systemctl status nginx || systemctl status aa_nginx || echo "Nginx未安装或未运行"

# 如果Nginx未运行，启动它
if ! systemctl is-active --quiet nginx && ! systemctl is-active --quiet aa_nginx; then
    echo "启动Nginx..."
    systemctl start nginx || systemctl start aa_nginx || nginx
fi

# 4. 检查后端服务
echo ""
echo "[4] 检查后端服务..."
ps aux | grep uvicorn | grep -v grep
netstat -tlnp | grep 8000 || ss -tlnp | grep 8000

# 5. 检查应用目录
echo ""
echo "[5] 检查应用目录..."
ls -la /var/www/jhw-ai.com/ 2>/dev/null || echo "生产环境目录不存在"
ls -la /var/www/canary-jhw-ai.com/ 2>/dev/null || echo "灰度环境目录不存在（正常）"

# 6. 检查数据库
echo ""
echo "[6] 检查数据库..."
ls -lh /var/www/jhw-ai.com/backend/waterms.db 2>/dev/null || echo "数据库不存在"

# 7. 检查端口监听
echo ""
echo "[7] 检查端口监听..."
netstat -tlnp || ss -tlnp

# 8. 检查系统日志
echo ""
echo "[8] 检查系统日志（最近错误）..."
tail -20 /var/log/messages 2>/dev/null || tail -20 /var/log/syslog 2>/dev/null || journalctl -n 20 --no-pager

echo ""
echo "========================================"
echo "诊断完成！"
echo "========================================"
echo ""
echo "如果SSH服务已启动，请从本地重新尝试连接："
echo "  ssh -i ~/.ssh/jhw-ai-server.pem root@120.76.156.83"
echo ""
echo "如果服务仍未运行，请手动启动："
echo "  systemctl start sshd"
echo "  systemctl start nginx"
echo "  cd /var/www/jhw-ai.com/backend && source venv/bin/activate && uvicorn main:app --port 8000"