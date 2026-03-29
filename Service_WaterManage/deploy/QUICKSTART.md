# 快速开始指南

## 📦 一键部署（推荐）

如果您已经配置好所有信息，只需执行：

```bash
cd Service_WaterManage/deploy
./deploy.sh deploy
```

## 🔧 首次使用配置

### 步骤 1: 配置敏感信息

```bash
cd Service_WaterManage/deploy
cp config-sensitive.example.sh config-sensitive.sh
vim config-sensitive.sh
```

填写以下信息：

```bash
# SSH 密钥路径
SSH_KEY_PATH="$HOME/.ssh/jhw-ai-server.pem"
SERVER_PASSWORD=""

# 阿里云配置（可选，用于自动配置安全组）
ALIYUN_ACCESS_KEY_ID="your_access_key_id"
ALIYUN_ACCESS_KEY_SECRET="your_access_key_secret"
ALIYUN_REGION_ID="cn-shenzhen"
ALIYUN_INSTANCE_ID="your_instance_id"
```

### 步骤 2: 验证配置

```bash
# 测试 SSH 连接
./deploy.sh shell

# 查看配置
cat config.sh
cat config-sensitive.sh
```

### 步骤 3: 执行部署

```bash
# 完整部署（包含备份）
./deploy.sh deploy

# 跳过备份的快速部署
./deploy.sh deploy --skip-backup

# 跳过安全组配置
./deploy.sh deploy --skip-sg
```

## 🎯 常用命令

```bash
# 查看服务状态
./deploy.sh status

# 重启服务
./deploy.sh restart

# 查看日志
./deploy.sh logs

# SSH 连接到服务器
./deploy.sh shell

# 创建手动备份
./deploy.sh backup

# 停止服务
./deploy.sh stop
```

## ✅ 部署验证

部署完成后，访问以下地址验证：

- **用户端**: https://jhw-ai.com/water/
- **管理后台**: https://jhw-ai.com/water-admin/
- **API**: https://jhw-ai.com/api/health

## 🆘 遇到问题？

### 1. SSH 连接失败

检查 SSH 密钥权限：
```bash
chmod 600 ~/.ssh/jhw-ai-server.pem
```

### 2. 无法访问网站

检查安全组配置：
```bash
# 查看服务状态
./deploy.sh status

# 手动配置安全组（如果自动配置失败）
```

### 3. 部署失败

查看日志：
```bash
./deploy.sh logs
```

### 4. 回滚到上一个版本

```bash
# 查看备份列表
./deploy.sh shell
ls /var/backups/water/

# 从备份恢复（需要手动操作）
```

## 📚 更多信息

- 详细文档: [README.md](./README.md)
- 安全检查清单: [SECURITY_CHECKLIST.md](./SECURITY_CHECKLIST.md)

## ⚠️ 安全提醒

- 永远不要将 `config-sensitive.sh` 提交到 Git
- 定期更换 SSH 密钥和密码
- 定期备份生产数据
- 使用强密码