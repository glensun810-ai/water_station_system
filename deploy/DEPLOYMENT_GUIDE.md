# AI产业集群空间服务系统 - 云服务器部署指南

## 服务器信息

- **公网IP**: 120.76.156.83
- **域名**: jhw-ai.com
- **部署目录**: /var/www/jhw-ai
- **API端口**: 8008（内部）
- **Web端口**: 80（外部）

## 快速部署步骤

### 1. 连接服务器

```bash
# SSH连接到云服务器
ssh root@120.76.156.83

# 或使用域名（需先配置DNS）
ssh root@jhw-ai.com
```

### 2. 上传部署文件

**方法1：从GitHub直接克隆（推荐）**

```bash
# 在服务器上执行
cd /var/www
git clone https://github.com/glensun810-ai/water_station_system.git jhw-ai
cd jhw-ai
git checkout feature/refactor-cleanup
git pull origin feature/refactor-cleanup
```

**方法2：从本地打包上传**

```bash
# 在本地执行（打包代码）
tar -czf jhw-ai.tar.gz \
  --exclude='.git' \
  --exclude='__pycache__' \
  --exclude='*.pyc' \
  --exclude='data/*.db' \
  --exclude='logs' \
  --exclude='.pids' \
  --exclude='Backup' \
  --exclude='.venv' \
  apps/ portal/ space-frontend/ shared/ models/ config/ depends/ utils/ \
  deploy/ requirements.txt run.py start_server.sh

# 上传到服务器
scp jhw-ai.tar.gz root@120.76.156.83:/tmp/

# 在服务器上解压
ssh root@120.76.156.83
cd /var/www
mkdir -p jhw-ai
tar -xzf /tmp/jhw-ai.tar.gz -C jhw-ai
```

### 3. 执行自动部署脚本

```bash
# 在服务器上执行
cd /var/www/jhw-ai
chmod +x deploy/deploy-production.sh
sudo ./deploy/deploy-production.sh
```

### 4. 手动部署（如果自动脚本失败）

#### 4.1 安装系统依赖

```bash
# CentOS/RHEL
yum install -y python3 python3-pip nginx git

# Ubuntu/Debian
apt-get install -y python3 python3-pip nginx git
```

#### 4.2 安装Python依赖

```bash
cd /var/www/jhw-ai
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

#### 4.3 配置Systemd服务

```bash
# 复制服务配置
cp deploy/systemd/jhw-ai.service /etc/systemd/system/

# 启用并启动服务
systemctl daemon-reload
systemctl enable jhw-ai
systemctl start jhw-ai

# 检查状态
systemctl status jhw-ai
```

#### 4.4 配置Nginx

```bash
# 复制Nginx配置
cp deploy/nginx.conf /etc/nginx/conf.d/jhw-ai.conf

# 删除默认配置
rm -f /etc/nginx/sites-enabled/default

# 测试并重启
nginx -t
systemctl restart nginx
```

#### 4.5 配置防火墙

```bash
# CentOS (firewalld)
firewall-cmd --permanent --add-port=80/tcp
firewall-cmd --permanent --add-port=443/tcp
firewall-cmd --reload

# Ubuntu (ufw)
ufw allow 80/tcp
ufw allow 443/tcp
```

## 验证部署

### 1. 检查API服务

```bash
# 健康检查
curl http://127.0.0.1:8008/health

# 应返回：{"status": "healthy", ...}
```

### 2. 检查Nginx代理

```bash
# 通过Nginx访问
curl http://127.0.0.1/health

# 应返回相同结果
```

### 3. 检查外部访问

```bash
# 在本地电脑浏览器访问
http://120.76.156.83/portal/index.html
http://120.76.156.83/health
```

## 域名配置

### 1. DNS解析配置

登录域名服务商（如阿里云、腾讯云），添加DNS解析：

```
类型: A记录
主机记录: @
记录值: 120.76.156.83

类型: A记录
主机记录: www
记录值: 120.76.156.83
```

### 2. 验证DNS解析

```bash
# 在本地执行
ping jhw-ai.com
# 应解析到 120.76.156.83

nslookup jhw-ai.com
```

### 3. 通过域名访问

```
http://jhw-ai.com/portal/index.html
http://jhw-ai.com/health
```

## SSL证书配置（HTTPS）

### 1. 申请SSL证书

**推荐方案：阿里云免费SSL证书**

1. 登录阿里云控制台
2. 产品与服务 → SSL证书（应用安全）
3. 购买证书 → 免费版DV SSL
4. 域名验证（添加DNS记录）
5. 等待审核（通常1-2天）
6. 下载证书（Nginx格式）

### 2. 安装证书

```bash
# 创建证书目录
mkdir -p /var/www/jhw-ai/ssl

# 上传证书文件
scp jhw-ai.com.pem root@120.76.156.83:/var/www/jhw-ai/ssl/
scp jhw-ai.com.key root@120.76.156.83:/var/www/jhw-ai/ssl/

# 设置权限
chmod 600 /var/www/jhw-ai/ssl/*.key
chmod 644 /var/www/jhw-ai/ssl/*.pem
```

### 3. 启用HTTPS配置

编辑 `/etc/nginx/conf.d/jhw-ai.conf`，取消HTTPS部分的注释：

```nginx
server {
    listen 443 ssl http2;
    server_name jhw-ai.com www.jhw-ai.com;
    
    ssl_certificate /var/www/jhw-ai/ssl/jhw-ai.com.pem;
    ssl_certificate_key /var/www/jhw-ai/ssl/jhw-ai.com.key;
    
    # ... 其他配置
}

# HTTP重定向到HTTPS
server {
    listen 80;
    server_name jhw-ai.com www.jhw-ai.com;
    return 301 https://$server_name$request_uri;
}
```

### 4. 重启Nginx

```bash
nginx -t
systemctl restart nginx
```

### 5. 验证HTTPS

```
https://jhw-ai.com/portal/index.html
https://jhw-ai.com/health
```

## 服务管理命令

### API服务

```bash
# 启动
systemctl start jhw-ai

# 停止
systemctl stop jhw-ai

# 重启
systemctl restart jhw-ai

# 状态
systemctl status jhw-ai

# 查看日志
tail -f /var/www/jhw-ai/logs/api_service.log
journalctl -u jhw-ai -f
```

### Nginx服务

```bash
# 启动
systemctl start nginx

# 停止
systemctl stop nginx

# 重启
systemctl restart nginx

# 状态
systemctl status nginx

# 测试配置
nginx -t
```

## 常见问题排查

### 1. API服务无法启动

```bash
# 查看详细错误日志
journalctl -u jhw-ai -n 100

# 检查Python依赖
cd /var/www/jhw-ai
source .venv/bin/activate
pip list

# 手动启动测试
python -m uvicorn apps.main:app --host 127.0.0.1 --port 8008
```

### 2. Nginx 502错误

```bash
# 检查API服务是否运行
systemctl status jhw-ai

# 检查端口监听
netstat -tlnp | grep 8008

# 查看Nginx错误日志
tail -f /var/log/nginx/jhw-ai_error.log
```

### 3. 无法访问（连接超时）

```bash
# 检查防火墙
firewall-cmd --list-all  # CentOS
ufw status               # Ubuntu

# 检查端口监听
netstat -tlnp | grep :80
netstat -tlnp | grep :443

# 检查Nginx状态
systemctl status nginx
```

### 4. 数据库错误

```bash
# 检查数据库文件
ls -lh /var/www/jhw-ai/data/

# 查看数据库内容
sqlite3 /var/www/jhw-ai/data/app.db ".tables"

# 备份并重建（如有必要）
cp /var/www/jhw-ai/data/app.db /var/www/jhw-ai/data/app.db.bak
```

## 更新部署

### 快速更新

```bash
cd /var/www/jhw-ai
git pull origin feature/refactor-cleanup
systemctl restart jhw-ai
```

### 完整更新

```bash
# 停止服务
systemctl stop jhw-ai

# 备份数据库
cp /var/www/jhw-ai/data/app.db /var/www/jhw-ai-backup/data/

# 更新代码
cd /var/www/jhw-ai
git pull origin feature/refactor-cleanup

# 更新依赖
source .venv/bin/activate
pip install -r requirements.txt

# 重启服务
systemctl start jhw-ai
```

## 性能优化建议

### 1. 启用Nginx缓存

```nginx
# 在nginx.conf中添加
proxy_cache_path /var/cache/nginx levels=1:2 keys_zone=api_cache:10m max_size=100m;

location /api/ {
    proxy_cache api_cache;
    proxy_cache_valid 200 10m;
    proxy_cache_key $request_uri;
    # ...
}
```

### 2. 优化数据库

```bash
# 定期清理日志
sqlite3 /var/www/jhw-ai/data/app.db "DELETE FROM user_login_logs WHERE login_time < date('now', '-30 days');"
```

### 3. 日志轮转

创建 `/etc/logrotate.d/jhw-ai`:

```
/var/www/jhw-ai/logs/*.log {
    daily
    rotate 30
    compress
    missingok
    notifempty
    create 644 root root
}
```

## 监控与告警

### 1. 健康检查脚本

创建 `/var/www/jhw-ai/scripts/health_check.sh`:

```bash
#!/bin/bash
STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8008/health)
if [ "$STATUS" != "200" ]; then
    echo "API服务异常，状态码: $STATUS"
    systemctl restart jhw-ai
fi
```

### 2. 定时检查

```bash
# 添加cron任务
crontab -e

# 每5分钟检查一次
*/5 * * * * /var/www/jhw-ai/scripts/health_check.sh
```

## 最终访问链接

部署成功后，系统可通过以下链接访问：

- **Portal首页**: http://jhw-ai.com/portal/index.html
- **Portal首页(IP)**: http://120.76.156.83/portal/index.html
- **API文档**: http://jhw-ai.com/docs
- **健康检查**: http://jhw-ai.com/health

配置SSL后：

- **Portal首页**: https://jhw-ai.com/portal/index.html
- **API文档**: https://jhw-ai.com/docs
- **健康检查**: https://jhw-ai.com/health

## 技术支持

如遇部署问题，请查看：

1. 服务日志：`/var/www/jhw-ai/logs/api_service.log`
2. Nginx日志：`/var/log/nginx/jhw-ai_error.log`
3. Systemd日志：`journalctl -u jhw-ai`

---

部署完成后，请在此文档记录部署时间和状态，便于后续维护。