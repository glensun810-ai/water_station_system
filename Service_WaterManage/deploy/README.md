# 智能一键部署脚本

## 目录结构

```
deploy/
├── config.sh          # 项目配置文件（根据不同项目修改此文件）
├── deploy-common.sh   # 通用函数库
├── deploy.sh         # 主部署脚本
└── README.md         # 使用说明
```

## 快速开始

### 1. 修改配置文件

编辑 `config.sh`，根据您的项目修改以下配置：

```bash
# 项目信息
PROJECT_NAME="water"
PROJECT_DESC="智能水站管理系统"

# 服务器配置
SERVER_HOST="120.76.156.83"
SERVER_USER="root"
SERVER_PORT=22

# 域名配置
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

### 2. 执行部署

```bash
cd deploy
./deploy.sh deploy
```

## 使用命令

| 命令 | 说明 |
|------|------|
| `./deploy.sh deploy` | 执行完整部署 |
| `./deploy.sh status` | 查看服务状态 |
| `./deploy.sh restart` | 重启服务 |
| `./deploy.sh stop` | 停止服务 |
| `./deploy.sh logs` | 查看后端日志 |
| `./deploy.sh shell` | SSH 连接到服务器 |
| `./deploy.sh deploy --skip-backup` | 跳过备份执行部署 |

## 部署流程

1. **环境检查** - 检查 SSH 连接、本地文件
2. **备份** - 自动备份当前部署
3. **上传后端** - 上传并配置 Python 环境
4. **上传前端** - 上传并修改 API 地址
5. **配置 Nginx** - 生成反向代理配置
6. **启动服务** - 启动后端 API
7. **验证** - 检查所有服务是否正常

## 适用项目

此脚本设计为通用型，只需修改 `config.sh` 即可用于其他项目：

- 修改 `PROJECT_NAME` 和 `PROJECT_DESC`
- 修改 `SERVER_HOST` 和 `SERVER_USER`
- 修改 `DOMAIN` 和前端路径
- 修改 `BACKEND_DIR` 指向您的后端目录
- 修改 `FRONTEND_FILES` 配置前端文件映射

## 注意事项

1. 确保服务器 SSH 密钥已配置或使用密码登录
2. 确保域名已解析到服务器 IP
3. 确保 SSL 证书已放置到对应路径
4. 首次部署需要手动配置 Nginx（后续自动）
