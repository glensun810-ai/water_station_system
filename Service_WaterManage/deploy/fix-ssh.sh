#!/bin/bash
# ==========================================
# SSH服务修复脚本 - 在服务器上执行
# ==========================================
# 
# 问题诊断：SSH端口开放但连接被重置
# 可能原因：
# 1. sshd配置错误
# 2. TCP Wrappers限制
# 3. fail2ban封禁
# 4. 连接数限制
# ==========================================

echo "========================================"
echo "SSH服务诊断与修复"
echo "========================================"

# 备份配置
echo ""
echo "[1] 备份SSH配置..."
cp /etc/ssh/sshd_config /etc/ssh/sshd_config.backup.$(date +%Y%m%d_%H%M%S) 2>/dev/null

# 检查SSH服务状态
echo ""
echo "[2] 检查SSH服务状态..."
systemctl status sshd 2>/dev/null || service ssh status 2>/dev/null

# 检查SSH监听端口
echo ""
echo "[3] 检查SSH监听..."
netstat -tlnp | grep :22 || ss -tlnp | grep :22

# 检查配置文件
echo ""
echo "[4] 检查SSH配置文件..."
grep -E "^Port|^PermitRootLogin|^PasswordAuthentication|^PubkeyAuthentication" /etc/ssh/sshd_config

# 检查TCP Wrappers
echo ""
echo "[5] 检查TCP Wrappers..."
if [ -f /etc/hosts.deny ]; then
    echo "hosts.deny内容："
    cat /etc/hosts.deny | grep -v "^#" | grep -v "^$"
fi
if [ -f /etc/hosts.allow ]; then
    echo "hosts.allow内容："
    cat /etc/hosts.allow | grep -v "^#" | grep -v "^$"
fi

# 检查fail2ban
echo ""
echo "[6] 检查fail2ban..."
if command -v fail2ban-client &> /dev/null; then
    fail2ban-client status sshd 2>/dev/null || echo "fail2ban未封禁SSH"
else
    echo "fail2ban未安装"
fi

# 检查SELinux
echo ""
echo "[7] 检查SELinux..."
if command -v getenforce &> /dev/null; then
    getenforce
fi

# 检查系统日志
echo ""
echo "[8] 检查SSH日志（最近错误）..."
tail -30 /var/log/secure 2>/dev/null || tail -30 /var/log/auth.log 2>/dev/null

echo ""
echo "========================================"
echo "开始修复..."
echo "========================================"

# 修复1: 确保基本配置正确
echo ""
echo "[修复1] 修正SSH配置..."
cat > /etc/ssh/sshd_config.d/99-fix.conf << 'EOF'
Port 22
PermitRootLogin yes
PasswordAuthentication yes
PubkeyAuthentication yes
UsePAM yes
X11Forwarding no
PrintMotd no
AcceptEnv LANG LC_*
Subsystem sftp /usr/lib/openssh/sftp-server
MaxStartups 10:30:100
MaxSessions 10
LoginGraceTime 60
ClientAliveInterval 300
ClientAliveCountMax 2
EOF

# 修复2: 清理TCP Wrappers限制
echo ""
echo "[修复2] 清理TCP Wrappers..."
echo "" > /etc/hosts.deny
echo "sshd: ALL" >> /etc/hosts.allow

# 修复3: 重启SSH服务
echo ""
echo "[修复3] 重启SSH服务..."
systemctl restart sshd 2>/dev/null || service ssh restart 2>/dev/null

# 修复4: 检查防火墙
echo ""
echo "[修复4] 配置防火墙..."
if command -v firewall-cmd &> /dev/null; then
    firewall-cmd --permanent --add-service=ssh
    firewall-cmd --permanent --add-port=22/tcp
    firewall-cmd --reload
    echo "已开放SSH端口(firewalld)"
elif command -v ufw &> /dev/null; then
    ufw allow 22/tcp
    echo "已开放SSH端口(ufw)"
elif command -v iptables &> /dev/null; then
    iptables -I INPUT -p tcp --dport 22 -j ACCEPT
    service iptables save 2>/dev/null
    echo "已开放SSH端口(iptables)"
fi

# 修复5: 清理fail2ban封禁（如果有）
echo ""
echo "[修复5] 清理fail2ban封禁..."
if command -v fail2ban-client &> /dev/null; then
    fail2ban-client set sshd unbanip --all 2>/dev/null
    echo "已清理fail2ban封禁"
fi

# 验证修复
echo ""
echo "========================================"
echo "验证修复结果"
echo "========================================"
systemctl status sshd --no-pager 2>/dev/null || service ssh status
netstat -tlnp | grep :22 || ss -tlnp | grep :22

echo ""
echo "========================================"
echo "修复完成！"
echo "========================================"
echo ""
echo "请从本地测试SSH连接："
echo "  ssh -i ~/.ssh/jhw-ai-server.pem root@120.76.156.83"
echo ""
echo "如果仍无法连接，请检查："
echo "1. 本地SSH密钥权限: chmod 600 ~/.ssh/jhw-ai-server.pem"
echo "2. 尝试使用密码登录: ssh -o PreferredAuthentications=password root@120.76.156.83"
echo "3. 查看详细日志: tail -f /var/log/secure"
echo "========================================"