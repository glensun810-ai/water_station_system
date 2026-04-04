# 生产环境一键部署指南

## 重要说明
- ✅ 自动备份生产数据库
- ✅ 只更新代码，不覆盖数据
- ✅ 启动所有服务

## 操作步骤

### 步骤1: 登录阿里云控制台

1. 访问: https://swasnext.console.aliyun.com
2. 找到服务器实例（IP: 120.76.156.83）
3. 点击"远程连接" → "Workbench远程连接"
4. 输入密码:
   - 控制台密码: `sgl@810SGl`
   - 服务器密码: `sgl@810jhw`

### 步骤2: 复制并执行一键部署命令

```bash
DATE=$(date +%Y%m%d_%H%M%S) && mkdir -p /backup/waterms/database && cp /var/www/jhw-ai.com/backend/waterms.db /backup/waterms/database/waterms_${DATE}.db && echo "备份完成: waterms_${DATE}.db" && systemctl start sshd nginx && systemctl enable sshd nginx && cd /var/www/jhw-ai.com/backend && source venv/bin/activate && pkill -f uvicorn || true && sleep 2 && nohup python -m uvicorn main:app --host 127.0.0.1 --port 8000 > /var/log/water-api.log 2>&1 & cat > /etc/nginx/conf.d/water.conf << 'EOF'
server {
    listen 80;
    location /water/ { alias /var/www/jhw-ai.com/water/; index index.html; }
    location /water-admin/ { alias /var/www/jhw-ai.com/water-admin/; index admin.html; }
    location /api/ { proxy_pass http://127.0.0.1:8000/api/; }
}
EOF
nginx -s reload && sleep 3 && echo "=== 验证 ===" && curl -s http://127.0.0.1:8000/api/health && echo "" && echo "✅ 部署完成！访问: http://120.76.156.83/water/"
```

## 部署完成后访问地址

| 环境 | 地址 |
|------|------|
| 用户端 | http://120.76.156.83/water/ |
| 管理后台 | http://120.76.156.83/water-admin/ |

测试账号: admin / admin123

---

**生成时间**: 2026-04-04