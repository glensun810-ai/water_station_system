# 灰度环境部署指南

## 部署方式

由于 SSH 服务未启动，需要通过阿里云控制台 VNC/Workbench 执行部署。

## 操作步骤

### 步骤1: 登录阿里云控制台

1. 访问阿里云轻量应用服务器控制台:
   ```
   https://swasnext.console.aliyun.com
   ```

2. 找到服务器实例（IP: 120.76.156.83）

3. 点击"远程连接" → 选择"Workbench远程连接"或"VNC远程连接"

4. 输入密码登录:
   - 控制台密码（第一层）: `sgl@810SGl`
   - 服务器密码（第二层）: `sgl@810jhw`

### 步骤2: 执行一键部署命令

连接成功后，复制并粘贴以下完整命令执行:

```bash
systemctl start sshd nginx && systemctl enable sshd nginx && cd /var/www/jhw-ai.com/backend && source venv/bin/activate && pkill -f uvicorn || true && sleep 2 && nohup python -m uvicorn main:app --host 127.0.0.1 --port 8000 > /var/log/water-api.log 2>&1 & mkdir -p /var/www/canary-jhw-ai.com/{backend,water,water-admin} && cp /var/www/jhw-ai.com/backend/waterms.db /var/www/canary-jhw-ai.com/backend/waterms_canary.db && rsync -av --exclude='*.db' --exclude='*.sqlite' --exclude='__pycache__' --exclude='venv' --exclude='.git' --exclude='*.log' /var/www/jhw-ai.com/backend/ /var/www/canary-jhw-ai.com/backend/ && cd /var/www/canary-jhw-ai.com/backend && sed -i 's/waterms\.db/waterms_canary.db/g' main.py && if [ ! -d venv ]; then python3 -m venv venv && source venv/bin/activate && pip install --upgrade pip -q && pip install -r requirements.txt -q; else source venv/bin/activate; fi && pkill -f "uvicorn.*8001" || true && sleep 2 && nohup python -m uvicorn main:app --host 127.0.0.1 --port 8001 > /var/log/water-canary-api.log 2>&1 & cp -r /var/www/jhw-ai.com/water/* /var/www/canary-jhw-ai.com/water/ && cp -r /var/www/jhw-ai.com/water-admin/* /var/www/canary-jhw-ai.com/water-admin/ && cat > /etc/nginx/conf.d/canary.conf << 'EOF'
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
nginx -s reload && sleep 3 && echo "=== 服务状态 ===" && ss -tlnp | grep -E "8000|8001|80" && echo "=== 后端进程 ===" && ps aux | grep uvicorn | grep -v grep && echo "=== API健康检查 ===" && curl -s http://127.0.0.1:8000/api/health && curl -s http://127.0.0.1:8001/api/health && echo "" && echo "========================================" && echo "部署完成！" && echo "========================================"
```

### 步骤3: 验证部署

部署完成后，通过浏览器访问验证:

**生产环境:**
- 用户端: http://120.76.156.83/water/
- 管理后台: http://120.76.156.83/water-admin/

**灰度环境:**
- 用户端: http://120.76.156.83:8001/water/
- 管理后台: http://120.76.156.83:8001/water-admin/

## 部署说明

### 命令执行内容

1. 启动 SSH 和 Nginx 服务
2. 启动生产环境后端（端口 8000）
3. 创建灰度环境目录
4. 复制生产数据库到灰度环境（waterms_canary.db）
5. 复制后端代码到灰度环境
6. 配置灰度数据库
7. 创建灰度环境虚拟环境并安装依赖
8. 启动灰度后端服务（端口 8001）
9. 复制前端文件
10. 配置 Nginx 灰度站点
11. 验证服务状态

### 注意事项

1. 灰度环境使用独立的数据库副本，不影响生产数据
2. 灰度环境使用端口 8001，与生产环境 8000 完全隔离
3. 测试账号: admin / admin123

---

**生成时间**: 2026-04-04