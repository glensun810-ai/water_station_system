# 一键部署说明

## 🚀 快速部署（3步完成）

### 步骤1: 上传文件到服务器

```bash
# 在本地项目根目录执行以下命令

# 上传部署脚本
scp deploy_all_in_one.sh root@120.76.156.83:/root/

# 上传数据库备份
scp backups/database/*.db backups/database/*.md5 root@120.76.156.83:/backup/waterms/database/

# 上传SSL证书（如需HTTPS）
scp Draft/docs/SSL/24143096_jhw-ai.com_nginx/* root@120.76.156.83:/var/www/jhw-ai.com/ssl/
```

### 步骤2: 登录服务器并执行部署

```bash
# 登录服务器
ssh root@120.76.156.83

# 进入项目目录（假设已上传代码）
cd /path/to/project

# 执行一键部署
bash /root/deploy_all_in_one.sh
```

### 步骤3: 访问系统

部署完成后，访问以下地址：
- 水站管理：http://120.76.156.83/water/
- 管理后台：http://120.76.156.83/water-admin/admin.html

---

## 📋 详细说明

### 前置条件
- 已有服务器访问权限
- 已上传项目代码到服务器
- 已上传数据库备份文件

### 脚本功能
✅ 自动创建所有必要目录
✅ 自动安装系统依赖（Nginx、Python等）
✅ 自动创建Python虚拟环境
✅ 自动安装Python依赖
✅ 自动配置Nginx（支持HTTP/HTTPS）
✅ 自动配置系统服务（systemd）
✅ 自动恢复数据库
✅ 自动启动所有服务
✅ 自动验证部署结果

### 部署后操作
1. 登录管理后台修改密码
2. 生成生产环境密钥
3. 配置域名解析（如未配置）
4. 测试所有功能

---

## ⚠️ 注意事项

1. **确保在项目根目录执行**
2. **确保已上传数据库备份文件**
3. **如需HTTPS，确保已上传SSL证书**
4. **部署完成后立即修改密码**

---

## 🎯 访问链接

部署成功后，可通过以下链接访问：

### HTTP访问（默认）
- 水站管理：http://120.76.156.83/water/
- 水站后台：http://120.76.156.83/water-admin/admin.html
- 会议室：http://120.76.156.83/meeting/
- 会议室后台：http://120.76.156.83/meeting-admin/admin.html

### HTTPS访问（需SSL证书）
- 水站管理：https://jhw-ai.com/water/
- 水站后台：https://jhw-ai.com/water-admin/admin.html

### 测试账号
- 用户名：admin
- 密码：admin123