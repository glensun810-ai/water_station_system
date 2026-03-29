# 智能一键部署脚本

## 📋 目录结构

```
deploy/
├── config.sh                      # 项目配置文件（可提交到 Git）
├── config-sensitive.sh            # 敏感信息配置（⚠️ 不可提交到 Git）
├── config-sensitive.example.sh    # 敏感信息配置模板（可提交到 Git）
├── deploy-common.sh               # 通用函数库
├── deploy.sh                      # 主部署脚本
└── README.md                      # 使用说明（本文件）
```

## ⚙️ 核心配置信息

在使用部署脚本前，您需要准备以下核心信息：

### 1. 服务器认证信息（必选，二选一）

**方式 A：SSH 密钥（推荐）**
- SSH 私钥文件路径（如：`~/.ssh/jhw-ai-server.pem`）
- 服务器 IP 地址
- 服务器用户名（通常为 root）
- SSH 端口（默认为 22）

**方式 B：SSH 密码**
- 服务器密码
- 服务器 IP 地址
- 服务器用户名
- SSH 端口（默认为 22）

### 2. 服务器基础信息（必选）

- **服务器 IP 地址**：如 `120.76.156.83`
- **SSH 用户名**：如 `root`
- **SSH 端口**：默认 `22`

### 3. 域名配置（必选）

- **域名**：如 `jhw-ai.com`
- **SSL 证书路径**（服务器上）：
  - 证书文件：`/etc/nginx/ssl/jhw-ai.com.pem`
  - 私钥文件：`/etc/nginx/ssl/jhw-ai.com.key`

### 4. 项目信息（必选）

- **项目名称**：如 `water`
- **项目描述**：如 `智能水站管理系统`
- **前端访问路径**：
  - 用户端：`/water`
  - 管理后台：`/water-admin`
- **后端端口**：如 `8000`
- **Python 版本**：如 `3.8`

### 5. 阿里云配置（可选，用于自动配置安全组）

如果需要脚本自动配置阿里云安全组规则（开放 80/443 端口），需要提供：

- **AccessKey ID**：阿里云访问密钥 ID
- **AccessKey Secret**：阿里云访问密钥 Secret
- **区域 ID**：如 `cn-shenzhen`
- **实例 ID**：如 `i-wz96rjdknmpn283zucrq`

## 🚀 快速开始

### 1. 首次配置

```bash
# 进入 deploy 目录
cd Service_WaterManage/deploy

# 复制敏感信息配置模板
cp config-sensitive.example.sh config-sensitive.sh

# 编辑敏感信息配置文件
vim config-sensitive.sh
```

在 `config-sensitive.sh` 中填写实际的敏感信息：

```bash
# SSH 密钥路径
SSH_KEY_PATH="$HOME/.ssh/jhw-ai-server.pem"
SERVER_PASSWORD=""

# 阿里云配置（如果需要自动配置安全组）
ALIYUN_ACCESS_KEY_ID="your_access_key_id"
ALIYUN_ACCESS_KEY_SECRET="your_access_key_secret"
ALIYUN_REGION_ID="cn-shenzhen"
ALIYUN_INSTANCE_ID="your_instance_id"
```

### 2. 执行部署

```bash
# 执行完整部署
./deploy.sh deploy
```

## 📖 使用命令

| 命令 | 说明 |
|------|------|
| `./deploy.sh deploy` | 执行完整部署 |
| `./deploy.sh deploy --skip-backup` | 跳过备份执行部署 |
| `./deploy.sh deploy --skip-sg` | 跳过安全组配置 |
| `./deploy.sh status` | 查看服务状态 |
| `./deploy.sh restart` | 重启服务 |
| `./deploy.sh stop` | 停止服务 |
| `./deploy.sh logs` | 查看后端日志 |
| `./deploy.sh shell` | SSH 连接到服务器 |
| `./deploy.sh backup` | 创建手动备份 |
| `./deploy.sh help` | 显示帮助信息 |

## 🔄 部署流程

脚本会自动执行以下步骤：

1. **环境检查** - 检查 SSH 连接、磁盘空间、必要命令
2. **安全检查与备份** - 自动备份当前部署和数据库
3. **上传后端** - 增量更新后端代码（排除所有数据文件）
4. **上传前端** - 上传前端文件并配置 API 地址
5. **配置 Nginx** - 自动生成并应用 Nginx 配置（支持 aaPanel 和标准 Nginx）
6. **配置安全组**（可选）- 自动配置阿里云安全组规则
7. **启动后端服务** - 重启后端 API 服务
8. **验证部署** - 检查所有服务是否正常运行
9. **清理部署文件** - 清理服务器上的临时文件

## 🛡️ 安全特性

### 生产数据保护

脚本设计了严格的生产数据保护机制，以下数据在任何情况下都不会被覆盖：

- ✓ 数据库文件（`*.db`, `*.sqlite`, `*.sqlite3`）
- ✓ 领水记录、结算记录、库存数据
- ✓ 办公室数据、用户数据
- ✓ 日志文件（`*.log`）
- ✓ 上传的文件（`uploads/`）
- ✓ 环境变量文件（`*.env`）

### 部署策略

- **增量更新**：使用 rsync 只同步有变化的文件
- **精确排除**：严格排除所有可能的数据文件
- **自动备份**：部署前自动备份生产数据
- **多重验证**：部署前后验证数据库完整性

### Git 安全性

为了防止敏感信息泄露，脚本采用了以下措施：

1. **分离配置**：
   - `config.sh` - 包含非敏感配置，可以提交到 Git
   - `config-sensitive.sh` - 包含敏感信息，**不可提交到 Git**

2. **配置模板**：
   - `config-sensitive.example.sh` - 提供配置示例，可以提交到 Git

3. **Git 忽略**：
   - 确保 `config-sensitive.sh` 已添加到 `.gitignore`

## 🔧 配置文件说明

### config.sh（可提交到 Git）

此文件包含项目的公开配置信息：

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

此文件包含敏感信息：

```bash
# SSH 认证信息
SSH_KEY_PATH="$HOME/.ssh/jhw-ai-server.pem"
SERVER_PASSWORD=""

# 阿里云配置（可选）
ALIYUN_ACCESS_KEY_ID="your_access_key_id"
ALIYUN_ACCESS_KEY_SECRET="your_access_key_secret"
ALIYUN_REGION_ID="cn-shenzhen"
ALIYUN_INSTANCE_ID="your_instance_id"
```

## 🌍 适用项目

此脚本设计为通用型，可用于其他项目的部署：

1. 修改 `config.sh` 中的项目信息
2. 修改 `FRONTEND_FILES` 配置前端文件映射
3. 修改 `BACKEND_DIR` 指向后端目录
4. 复制并配置 `config-sensitive.sh`

## ⚠️ 注意事项

1. **SSH 密钥权限**：确保 SSH 私钥文件权限为 `600`
   ```bash
   chmod 600 ~/.ssh/jhw-ai-server.pem
   ```

2. **首次部署**：首次部署前需确保：
   - 服务器已安装 Python 3.8+
   - 服务器已安装 Nginx 或 aaPanel
   - SSL 证书已放置到指定路径
   - 域名已解析到服务器 IP

3. **安全组配置**：
   - 如果无法自动配置安全组，需要手动在阿里云控制台配置
   - 需要开放端口：80（HTTP）、443（HTTPS）

4. **Git 安全**：
   - 确保 `config-sensitive.sh` 已添加到 `.gitignore`
   - 永远不要将 `config-sensitive.sh` 提交到 Git
   - 定期更换 SSH 密钥和阿里云 AccessKey

## 📝 常见问题

### Q1: 部署后无法访问网站？

**A:** 检查以下几点：
1. 安全组是否开放 80/443 端口
2. 域名是否正确解析到服务器 IP
3. Nginx 是否正常运行：`./deploy.sh status`
4. 查看后端日志：`./deploy.sh logs`

### Q2: 如何回滚到上一个版本？

**A:** 部署前会自动备份，可以通过以下方式回滚：
1. 登录服务器查看备份：`ls /var/backups/water/`
2. 解压备份文件恢复
3. 或使用 `./deploy.sh backup` 创建当前版本的备份

### Q3: 脚本会覆盖生产数据吗？

**A:** **绝对不会！** 脚本设计了严格的数据保护机制：
- 排除所有数据库文件（`*.db`, `*.sqlite`, `*.sqlite3`）
- 部署前自动备份数据库
- 部署前后验证数据库完整性

### Q4: 如何修改服务器密码？

**A:** 只需修改 `config-sensitive.sh` 文件：
```bash
SSH_KEY_PATH=""
SERVER_PASSWORD="new_password"
```

### Q5: 如何配置多个项目？

**A:** 复制整个 deploy 目录，为每个项目修改配置即可。

## 📞 支持

如有问题或建议，请联系项目负责人。