# 404问题快速修复指南

## 问题诊断

您遇到的问题：
- `http://120.76.156.83` → 301重定向到HTTPS
- `https://jhw-ai.com/portal/index.html` → 403 Forbidden

这说明：
1. ✓ Nginx已运行并配置HTTPS
2. ✓ 域名DNS已解析
3. ❌ 但Portal文件未部署到正确位置

## 立即修复步骤

### 步骤1：SSH连接服务器

```bash
ssh root@120.76.156.83
```

### 步骤2：执行诊断脚本

```bash
cd /var/www/jhw-ai
chmod +x deploy/diagnose.sh
./deploy/diagnose.sh
```

诊断脚本会检查：
- 部署目录是否存在
- Portal文件是否存在
- API服务是否运行
- Nginx配置是否正确
- 文件权限是否正常

### 步骤3：根据诊断结果修复

#### 如果部署目录不存在：

```bash
# 创建部署目录
mkdir -p /var/www/jhw-ai

# 克隆代码
cd /var/www
git clone https://github.com/glensun810-ai/water_station_system.git jhw-ai
cd jhw-ai
git checkout feature/refactor-cleanup

# 执行部署
chmod +x deploy/deploy-production.sh
sudo ./deploy/deploy-production.sh
```

#### 如果Portal文件不存在：

```bash
cd /var/www/jhw-ai
chmod +x deploy/fix-404.sh
./deploy/fix-404.sh
```

#### 如果Nginx配置错误：

```bash
# 更新Nginx配置
cp deploy/nginx.conf /etc/nginx/conf.d/jhw-ai.conf

# 测试配置
nginx -t

# 重启Nginx
systemctl restart nginx
```

#### 如果文件权限问题：

```bash
chmod -R 755 /var/www/jhw-ai/portal/
chmod -R 755 /var/www/jhw-ai/apps/
chmod -R 755 /var/www/jhw-ai/space-frontend/
chmod -R 755 /var/www/jhw-ai/shared/
```

### 步骤4：验证修复

```bash
# 检查文件是否存在
ls -lh /var/www/jhw-ai/portal/index.html

# 测试本地访问
curl -I http://127.0.0.1/portal/index.html

# 测试API服务
curl http://127.0.0.1:8008/health
```

### 步骤5：禁用HTTPS重定向（临时方案）

如果HTTPS配置有问题，可以先禁用重定向：

```bash
# 编辑Nginx配置
vim /etc/nginx/conf.d/jhw-ai.conf

# 暂时注释掉HTTPS重定向
# server {
#     listen 80;
#     return 301 https://$server_name$request_uri;
# }

# 重启Nginx
systemctl restart nginx
```

## 正确的文件结构

部署成功后，应该有以下文件：

```
/var/www/jhw-ai/
├── portal/
│   ├── index.html           ← Portal首页（必需）
│   ├── admin/
│   │   ├── login.html
│   │   ├── users.html
│   │   └── ...
│   ├── assets/
│   │   ├── css/
│   │   └── js/
│   └── components/
├── apps/
│   ├── main.py              ← API服务入口
│   ├── water/
│   └── meeting/
├── space-frontend/
│   └── index.html
├── shared/
│   └── utils/
├── deploy/
│   ├── nginx.conf
│   ├── deploy-production.sh
│   └── diagnose.sh
├── logs/
└── data/
    └── app.db
```

## Nginx正确配置片段

确保 `/etc/nginx/conf.d/jhw-ai.conf` 包含：

```nginx
# HTTP服务器（不要强制HTTPS）
server {
    listen 80;
    server_name jhw-ai.com www.jhw-ai.com 120.76.156.83;
    
    # Portal统一入口
    location /portal/ {
        alias /var/www/jhw-ai/portal/;
        index index.html;
        try_files $uri $uri/ /portal/index.html;
        
        # 静态资源缓存
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2)$ {
            expires 7d;
            add_header Cache-Control "public, immutable";
        }
    }
    
    # API反向代理
    location /api/ {
        proxy_pass http://127.0.0.1:8008/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    # 健康检查
    location /health {
        proxy_pass http://127.0.0.1:8008/health;
    }
}
```

## 常见问题排查

### 问题1：403 Forbidden

原因：文件权限不正确

修复：
```bash
chmod -R 755 /var/www/jhw-ai/
chown -R root:root /var/www/jhw-ai/
```

### 问题2：404 Not Found

原因：文件不存在或路径错误

检查：
```bash
ls -R /var/www/jhw-ai/portal/
cat /etc/nginx/conf.d/jhw-ai.conf | grep "location /portal"
```

### 问题3：502 Bad Gateway

原因：API服务未运行

修复：
```bash
systemctl start jhw-ai
systemctl status jhw-ai
```

### 问题4：Connection Refused

原因：防火墙阻止或服务未启动

检查：
```bash
netstat -tlnp | grep ":80"
firewall-cmd --list-all
```

## 验证部署成功

执行以下测试：

```bash
# 1. 本地文件测试
ls -lh /var/www/jhw-ai/portal/index.html

# 2. API服务测试
curl http://127.0.0.1:8008/health
# 应返回: {"status": "healthy", ...}

# 3. Nginx代理测试
curl http://127.0.0.1/health
# 应返回: {"status": "healthy", ...}

# 4. Portal页面测试
curl -I http://127.0.0.1/portal/index.html
# 应返回: HTTP/1.1 200 OK
```

## 最终访问链接

修复成功后，可访问：

- **HTTP访问**: http://120.76.156.83/portal/index.html
- **域名访问**: http://jhw-ai.com/portal/index.html
- **API文档**: http://jhw-ai.com/docs
- **健康检查**: http://jhw-ai.com/health

---

请先执行诊断脚本，然后根据诊断结果修复。如有问题，请提供诊断输出结果。