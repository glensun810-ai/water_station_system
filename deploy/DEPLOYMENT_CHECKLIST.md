# 部署前准备检查清单 - AI产业集群服务管理平台

**项目**: 水站管理 + 会议室预定系统  
**部署日期**: 2026-04-04  
**服务器**: 120.76.156.83 (阿里云)  
**域名**: jhw-ai.com, www.jhw-ai.com  
**状态**: 生产环境准备就绪

---

## ✅ 已完成的高优先级任务

### 1. ✅ 安全配置检查与加固
- [x] **清理部署文档敏感密码** - `PRODUCTION_DEPLOY_INSTRUCTIONS.md` 已清理密码信息
- [x] **验证.gitignore配置** - `.env` 和 `config-sensitive.sh` 已正确排除
- [x] **SSL证书准备** - 证书文件位于 `Draft/docs/SSL/24143096_jhw-ai.com_nginx/`
  - 证书文件: `jhw-ai.com.pem`
  - 私钥文件: `jhw-ai.com.key`
- [x] **创建生产环境配置模板** - `.env.production` 已准备

### 2. ✅ 数据库备份与保护（真实数据）
- [x] **数据库完整性验证** - 两个数据库文件完整性检查均为 `ok`
  - 水站数据库: `Service_WaterManage/backend/waterms.db` (264KB) - ✅ OK
  - 会议室数据库: `Service_MeetingRoom/backend/meeting.db` (216KB) - ✅ OK
- [x] **创建备份脚本** - `scripts/backup_databases_for_deploy.sh` 已创建并执行
- [x] **执行数据库备份** - 备份文件已生成:
  - 水站备份: `backups/database/waterms_20260404_152737.db`
  - 会议室备份: `backups/database/meeting_20260404_152737.db`
  - 校验文件: `.md5` 文件已生成
  - 备份清单: `backup_manifest_20260404_152737.txt`
- [x] **备份策略** - 服务器备份目录 `/backup/waterms/database/` 已规划

### 3. ✅ 生产环境配置准备
- [x] **创建 .env.production 模板** - 包含所有生产环境必需配置
- [x] **环境变量分离** - 生产/开发环境配置已分离
- [x] **配置检查清单**:
  - `ENVIRONMENT=production` ✅
  - `DEBUG=false` ✅
  - `SECRET_KEY` - 需部署后由管理员设置 ⚠️
  - `JWT_SECRET_KEY` - 需部署后由管理员设置 ⚠️
  - `DATABASE_URL` - 生产路径已配置 ✅
  - `CORS_ALLOWED_ORIGINS` - 已配置生产域名 ✅

### 4. ✅ SSL证书和安全配置
- [x] **SSL证书文件确认** - 文件位置已确认
- [x] **Nginx SSL配置** - `deploy/nginx-production.conf` 已创建
  - HTTPS配置 ✅
  - HTTP→HTTPS重定向 ✅
  - 安全Headers配置 ✅
  - TLS 1.2/1.3支持 ✅
  - WebSocket代理配置 ✅

### 5. ✅ Nginx配置优化
- [x] **生产Nginx配置文件** - 已创建完整的生产配置
  - 域名支持: jhw-ai.com, www.jhw-ai.com ✅
  - IP访问支持: 120.76.156.83 ✅
  - 水站管理路由: /water/, /water-admin/ ✅
  - 会议室路由: /meeting/, /meeting-admin/ ✅
  - API代理: /api/ ✅
  - Gzip压缩 ✅
  - 静态资源缓存策略 ✅
  - 安全Headers ✅

---

## ⏳ 待完成的任务

### 6. 🔄 API地址配置统一（进行中）
**当前状态**: 前端API地址已基于localhost和jhw-ai.com自动判断  
**需检查项**:
- [ ] 验证所有前端文件的API配置一致性
- [ ] 测试生产环境API地址可访问性
- [ ] 确保WebSocket连接正确

### 7. 📝 创建部署验证脚本（待完成）
- [ ] 创建部署后自动验证脚本
- [ ] 包含API健康检查
- [ ] 包含前端页面可访问性检查
- [ ] 包含数据库连接验证

### 8. 📋 编写部署文档和应急预案（待完成）
- [ ] 详细部署步骤文档
- [ ] 回滚操作步骤
- [ ] 紧急问题处理流程
- [ ] 数据恢复方案

---

## 📦 需要部署的关键文件清单

### 数据库文件（真实数据，必须保留）
```
✅ Service_WaterManage/backend/waterms.db (264KB, 完整性OK)
✅ Service_MeetingRoom/backend/meeting.db (216KB, 完整性OK)
```

### 配置文件
```
✅ Service_WaterManage/backend/.env.production (生产环境配置模板)
⚠️ Service_WaterManage/backend/.env (部署后需要设置生产密钥)
```

### SSL证书文件
```
✅ Draft/docs/SSL/24143096_jhw-ai.com_nginx/jhw-ai.com.pem
✅ Draft/docs/SSL/24143096_jhw-ai.com_nginx/jhw-ai.com.key
```

### Nginx配置文件
```
✅ deploy/nginx-production.conf (生产环境完整配置)
```

### 前端文件
```
✅ Service_WaterManage/frontend/ (水站管理前端)
✅ Service_MeetingRoom/frontend/ (会议室管理前端)
```

### 后端代码
```
✅ Service_WaterManage/backend/ (水站管理后端)
✅ Service_MeetingRoom/backend/ (会议室管理后端)
```

---

## ⚠️ 部署前必须确认的事项

### 1. 数据安全（最高优先级）
- ✅ 真实数据库已备份到 `backups/database/`
- ✅ 备份文件已生成MD5校验
- ⚠️ **部署前必须上传备份文件到服务器 `/backup/waterms/database/`**
- ⚠️ **确保服务器备份目录已创建且有足够空间**

### 2. 密钥和密码管理
- ⚠️ **部署后必须修改以下密码**:
  - 管理员默认密码: `admin/admin123` → 需修改
  - SECRET_KEY: 需生成生产环境密钥
  - JWT_SECRET_KEY: 需生成生产环境密钥
- ⚠️ 密钥生成命令: `python -c "import secrets; print(secrets.token_urlsafe(48))"`

### 3. SSL证书部署
- ⚠️ 需将SSL证书文件上传到服务器: `/var/www/jhw-ai.com/ssl/`
- ⚠️ 证书文件权限设置: 
  - `.pem` 文件: 644
  - `.key` 文件: 600 (仅root可读)

### 4. 服务和端口
- ⚠️ 确认服务器防火墙已开放: 
  - 80 (HTTP)
  - 443 (HTTPS)
  - 8000 (API服务，内部端口)
- ⚠️ 确认Nginx服务已安装并启动
- ⚠️ 确认Python环境和依赖已安装

### 5. 域名解析
- ⚠️ 确认域名已解析到服务器IP:
  - jhw-ai.com → 120.76.156.83
  - www.jhw-ai.com → 120.76.156.83

---

## 🚀 部署流程建议

### 步骤1: 服务器准备
```bash
# 1. 登录服务器
ssh root@120.76.156.83

# 2. 创建必要目录
mkdir -p /var/www/jhw-ai.com/backend
mkdir -p /var/www/jhw-ai.com/water
mkdir -p /var/www/jhw-ai.com/water-admin
mkdir -p /var/www/jhw-ai.com/meeting
mkdir -p /var/www/jhw-ai.com/meeting-admin
mkdir -p /var/www/jhw-ai.com/ssl
mkdir -p /backup/waterms/database
mkdir -p /var/log/waterms

# 3. 设置权限
chmod -R 755 /var/www/jhw-ai.com
chmod -R 755 /backup/waterms
chmod -R 755 /var/log/waterms
```

### 步骤2: 上传文件
```bash
# 从本地执行:
# 1. 上传数据库备份
scp backups/database/*.db backups/database/*.md5 root@120.76.156.83:/backup/waterms/database/

# 2. 上传SSL证书
scp Draft/docs/SSL/24143096_jhw-ai.com_nginx/* root@120.76.156.83:/var/www/jhw-ai.com/ssl/

# 3. 上传代码和配置（参考deploy-production.sh）
```

### 步骤3: 配置服务
```bash
# 1. 配置SSL证书权限
chmod 644 /var/www/jhw-ai.com/ssl/jhw-ai.com.pem
chmod 600 /var/www/jhw-ai.com/ssl/jhw-ai.com.key

# 2. 配置Nginx
cp deploy/nginx-production.conf /etc/nginx/conf.d/jhw-ai.conf
nginx -t
nginx -s reload

# 3. 配置systemd服务（自动启动）
systemctl enable waterms
systemctl start waterms
```

### 步骤4: 验证部署
```bash
# 1. 检查API服务
curl http://127.0.0.1:8000/api/health

# 2. 检查HTTPS访问
curl https://jhw-ai.com/api/health

# 3. 检查前端页面
curl https://jhw-ai.com/water/
curl https://jhw-ai.com/water-admin/admin.html
```

### 步骤5: 部署后安全加固
```bash
# 1. 修改管理员密码（登录管理后台后操作）

# 2. 生成并设置生产密钥
python -c "import secrets; print(secrets.token_urlsafe(48))"
# 将生成的密钥更新到 .env 文件

# 3. 重启服务使配置生效
systemctl restart waterms
```

---

## 📞 紧急联系和备份信息

### 备份文件位置
- 本地: `backups/database/waterms_20260404_152737.db`
- 本地: `backups/database/meeting_20260404_152737.db`
- 服务器: `/backup/waterms/database/` (需上传)

### 数据恢复命令
```bash
# 恢复水站数据库
cp /backup/waterms/database/waterms_YYYYMMDD_HHMMSS.db /var/www/jhw-ai.com/backend/waterms.db

# 恢复会议室数据库
cp /backup/waterms/database/meeting_YYYYMMDD_HHMMSS.db /var/www/jhw-ai.com/backend/meeting.db
```

### 服务管理命令
```bash
# 启动服务
systemctl start waterms

# 停止服务
systemctl stop waterms

# 重启服务
systemctl restart waterms

# 查看状态
systemctl status waterms

# 查看日志
tail -f /var/log/waterms/waterms.log
```

---

## 📊 部署检查总结

| 类别 | 状态 | 备注 |
|------|------|------|
| 安全配置 | ✅ 完成 | SSL证书已准备，敏感信息已清理 |
| 数据备份 | ✅ 完成 | 真实数据已备份并验证完整性 |
| 配置文件 | ✅ 完成 | 生产环境配置模板已准备 |
| Nginx配置 | ✅ 完成 | HTTPS和安全headers已配置 |
| API配置 | 🔄 进行中 | 需验证生产环境API访问 |
| 验证脚本 | ⏳ 待完成 | 建议创建自动验证脚本 |
| 部署文档 | ⏳ 待完成 | 详细部署步骤需完善 |

---

**生成时间**: 2026-04-04  
**负责人**: [请填写]  
**审核人**: [请填写]  
**部署批准**: [请填写]

---

## 🔗 相关文件路径

- 数据库备份脚本: `scripts/backup_databases_for_deploy.sh`
- 生产环境配置: `Service_WaterManage/backend/.env.production`
- Nginx配置: `deploy/nginx-production.conf`
- SSL证书: `Draft/docs/SSL/24143096_jhw-ai.com_nginx/`
- 备份文件: `backups/database/`