# 智能一键部署脚本 - 核心配置说明

## 🎯 需要您提供的核心信息

### 1. 服务器认证信息（必选，二选一）

#### 方式 A：SSH 密钥（推荐，更安全）

| 配置项 | 说明 | 示例 |
|--------|------|------|
| `SSH_KEY_PATH` | SSH 私钥文件路径 | `~/.ssh/jhw-ai-server.pem` |
| `SERVER_PASSWORD` | SSH 密码（留空） | `""` |

#### 方式 B：SSH 密码（不推荐）

| 配置项 | 说明 | 示例 |
|--------|------|------|
| `SSH_KEY_PATH` | SSH 密钥路径（留空） | `""` |
| `SERVER_PASSWORD` | SSH 密码 | `"your_password"` |

**配置位置**：`deploy/config-sensitive.sh`

```bash
# SSH 密钥认证（推荐）
SSH_KEY_PATH="$HOME/.ssh/jhw-ai-server.pem"
SERVER_PASSWORD=""
```

---

### 2. 服务器基础信息（必选）

这些信息已经在 `deploy/config.sh` 中配置好，如果服务器有变化需要修改：

| 配置项 | 说明 | 当前值 | 示例 |
|--------|------|--------|------|
| `SERVER_HOST` | 服务器 IP 地址 | `120.76.156.83` | `123.45.67.89` |
| `SERVER_USER` | SSH 用户名 | `root` | `root` 或 `ubuntu` |
| `SERVER_PORT` | SSH 端口 | `22` | `22` 或自定义端口 |

**配置位置**：`deploy/config.sh`

---

### 3. 域名和 SSL 配置（必选）

这些信息已经在 `deploy/config.sh` 中配置好：

| 配置项 | 说明 | 当前值 | 示例 |
|--------|------|--------|------|
| `DOMAIN` | 域名 | `jhw-ai.com` | `example.com` |
| `SSL_CERT_PATH` | SSL 证书路径 | `/etc/nginx/ssl/jhw-ai.com.pem` | `/etc/ssl/certs/cert.pem` |
| `SSL_KEY_PATH` | SSL 私钥路径 | `/etc/nginx/ssl/jhw-ai.com.key` | `/etc/ssl/private/key.pem` |

**配置位置**：`deploy/config.sh`

---

### 4. 项目配置（必选）

这些信息已经在 `deploy/config.sh` 中配置好：

| 配置项 | 说明 | 当前值 |
|--------|------|--------|
| `PROJECT_NAME` | 项目名称 | `water` |
| `PROJECT_DESC` | 项目描述 | `智能水站管理系统` |
| `FRONTEND_USER_PATH` | 用户端路径 | `/water` |
| `FRONTEND_ADMIN_PATH` | 管理后台路径 | `/water-admin` |
| `BACKEND_PORT` | 后端端口 | `8000` |
| `PYTHON_VERSION` | Python 版本 | `3.8` |

**配置位置**：`deploy/config.sh`

---

### 5. 阿里云配置（可选）

如果需要脚本自动配置阿里云安全组（开放 80/443 端口），需要提供：

| 配置项 | 说明 | 获取方式 |
|--------|------|----------|
| `ALIYUN_ACCESS_KEY_ID` | 阿里云 AccessKey ID | 阿里云控制台 → AccessKey 管理 |
| `ALIYUN_ACCESS_KEY_SECRET` | 阿里云 AccessKey Secret | 阿里云控制台 → AccessKey 管理 |
| `ALIYUN_REGION_ID` | 区域 ID | 如 `cn-shenzhen` |
| `ALIYUN_INSTANCE_ID` | 实例 ID | 阿里云控制台 → ECS 实例 |

**配置位置**：`deploy/config-sensitive.sh`

```bash
# 阿里云配置（可选）
ALIYUN_ACCESS_KEY_ID="your_access_key_id"
ALIYUN_ACCESS_KEY_SECRET="your_access_key_secret"
ALIYUN_REGION_ID="cn-shenzhen"
ALIYUN_INSTANCE_ID="your_instance_id"
```

---

## 📝 配置步骤

### 步骤 1：首次配置（只需一次）

```bash
# 1. 进入 deploy 目录
cd Service_WaterManage/deploy

# 2. 复制敏感信息配置模板
cp config-sensitive.example.sh config-sensitive.sh

# 3. 编辑配置文件
vim config-sensitive.sh
```

在 `config-sensitive.sh` 中填写实际信息：

```bash
# SSH 密钥路径（必须填写）
SSH_KEY_PATH="$HOME/.ssh/jhw-ai-server.pem"
SERVER_PASSWORD=""

# 阿里云配置（如果需要自动配置安全组）
ALIYUN_ACCESS_KEY_ID="your_access_key_id"
ALIYUN_ACCESS_KEY_SECRET="your_access_key_secret"
ALIYUN_REGION_ID="cn-shenzhen"
ALIYUN_INSTANCE_ID="your_instance_id"
```

### 步骤 2：验证配置

```bash
# 测试 SSH 连接
./deploy.sh shell

# 如果能成功登录到服务器，说明配置正确
```

### 步骤 3：执行部署

```bash
# 完整部署（推荐）
./deploy.sh deploy

# 快速部署（跳过备份）
./deploy.sh deploy --skip-backup

# 跳过安全组配置
./deploy.sh deploy --skip-sg
```

---

## 🔍 配置文件说明

### config.sh（可提交到 Git）

此文件包含项目的公开配置信息，可以安全地提交到 Git：

```bash
# 项目信息
PROJECT_NAME="water"
PROJECT_DESC="智能水站管理系统"

# 服务器信息
SERVER_HOST="120.76.156.83"
SERVER_USER="root"
SERVER_PORT=22

# 域名信息
DOMAIN="jhw-ai.com"
SSL_CERT_PATH="/etc/nginx/ssl/jhw-ai.com.pem"
SSL_KEY_PATH="/etc/nginx/ssl/jhw-ai.com.key"

# 前端路径
FRONTEND_USER_PATH="/water"
FRONTEND_ADMIN_PATH="/water-admin"

# 后端配置
BACKEND_PORT=8000
PYTHON_VERSION="3.8"
```

### config-sensitive.sh（不可提交到 Git）

此文件包含敏感信息，**绝对不能**提交到 Git：

```bash
# SSH 认证信息
SSH_KEY_PATH="$HOME/.ssh/jhw-ai-server.pem"
SERVER_PASSWORD=""

# 阿里云配置
ALIYUN_ACCESS_KEY_ID="your_access_key_id"
ALIYUN_ACCESS_KEY_SECRET="your_access_key_secret"
ALIYUN_REGION_ID="cn-shenzhen"
ALIYUN_INSTANCE_ID="your_instance_id"
```

**重要**：
- `config-sensitive.sh` 已添加到 `.gitignore`
- 永远不要提交此文件到 Git
- 如果不小心提交，立即撤销并更改所有密钥

---

## 🚀 使用流程

### 日常部署流程

```bash
# 1. 更新代码后，进入 deploy 目录
cd Service_WaterManage/deploy

# 2. 执行部署
./deploy.sh deploy

# 3. 部署完成后，验证访问
# 用户端: https://jhw-ai.com/water/
# 管理后台: https://jhw-ai.com/water-admin/
```

### 查看服务状态

```bash
./deploy.sh status
```

### 重启服务

```bash
./deploy.sh restart
```

### 查看日志

```bash
./deploy.sh logs
```

### SSH 连接到服务器

```bash
./deploy.sh shell
```

---

## ⚠️ 安全注意事项

### 1. SSH 密钥安全

```bash
# 确保 SSH 私钥权限正确
chmod 600 ~/.ssh/jhw-ai-server.pem
```

### 2. 阿里云 AccessKey 权限

如果使用阿里云自动配置安全组，建议：

- 创建专用的 RAM 用户
- 只授予 ECS 只读和安全组管理权限
- 定期轮换 AccessKey

### 3. Git 安全

```bash
# 确认 config-sensitive.sh 在 .gitignore 中
cat .gitignore | grep config-sensitive.sh

# 检查是否有敏感文件被提交
git log --all --full-history -- '*config-sensitive.sh'
```

### 4. 定期更换密钥

建议每 3-6 个月更换：
- SSH 密钥
- 阿里云 AccessKey
- 服务器密码

---

## 🆘 常见问题

### Q1: 如何生成新的 SSH 密钥？

```bash
# 生成新的 SSH 密钥对
ssh-keygen -t rsa -b 4096 -C "your_email@example.com"

# 将公钥添加到服务器
ssh-copy-id -i ~/.ssh/jhw-ai-server.pem.pub root@120.76.156.83
```

### Q2: 如何获取阿里云 AccessKey？

1. 登录阿里云控制台
2. 点击右上角头像 → AccessKey 管理
3. 创建 AccessKey
4. 妥善保管 AccessKey ID 和 Secret

### Q3: 部署失败怎么办？

```bash
# 查看部署日志
./deploy.sh logs

# 查看服务状态
./deploy.sh status

# 手动连接服务器排查
./deploy.sh shell
```

### Q4: 如何回滚到上一个版本？

```bash
# 查看备份列表
./deploy.sh shell
ls /var/backups/water/

# 从备份恢复（需要手动操作）
```

---

## 📚 相关文档

- [README.md](./README.md) - 完整使用文档
- [QUICKSTART.md](./QUICKSTART.md) - 快速开始指南
- [SECURITY_CHECKLIST.md](./SECURITY_CHECKLIST.md) - 安全检查清单