# GitHub Actions 自动部署指南

## 功能说明

- ✅ 手动触发部署（默认关闭自动部署）
- ✅ 从GitHub拉取最新代码
- ✅ 自动备份服务器旧文件
- ✅ 替换新文件并重载Nginx
- ✅ 部署失败时显示错误信息
- ✅ 部署成功验证

## 使用方法

### 1. 配置 GitHub Secrets

在 GitHub 仓库设置中添加以下 Secrets：

| Secret 名称 | 说明 | 示例值 |
|-------------|------|--------|
| `SSH_PRIVATE_KEY` | 服务器SSH私钥 | `-----BEGIN OPENSSH PRIVATE KEY-----...` |
| `SERVER_HOST` | 服务器IP地址 | `120.76.156.83` |
| `SERVER_USER` | SSH用户名 | `root` |
| `DOMAIN` | 域名 | `jhw-ai.com` |

### 2. 生成 Deploy Key

```bash
# 登录服务器
ssh root@120.76.156.83

# 创建SSH目录
mkdir -p ~/.ssh
chmod 700 ~/.ssh

# 生成deploy key（直接回车，不要设密码）
ssh-keygen -t ed25519 -f ~/.ssh/server_deploy -N ""

# 查看公钥
cat ~/.ssh/server_deploy.pub
```

### 3. 添加 Deploy Key 到 GitHub

1. 打开 GitHub 仓库: https://github.com/glensun810-ai/water_station_system
2. 进入 **Settings** → **Deploy keys** → **Add deploy key**
3. Title: `Server Deploy Key`
4. Key: 粘贴上一步的公钥
5. 勾选 **Allow write access**（如需要）
6. 点击 **Add key**

### 4. 配置 SSH 连接

```bash
# 配置SSH使用deploy key
cat >> ~/.ssh/config << 'EOF'
Host github.com
    HostName github.com
    User git
    IdentityFile ~/.ssh/server_deploy
    StrictHostKeyChecking no
EOF

chmod 600 ~/.ssh/config

# 添加GitHub host key
ssh-keyscan github.com >> ~/.ssh/known_hosts 2>/dev/null

# 测试连接
ssh -T git@github.com
```

成功会显示: `Hi glensun810-ai/water_station_system! You've successfully authenticated...`

### 5. 配置服务器 Git

```bash
# 进入项目目录
cd /var/www/jhw-ai.com

# 初始化git（如果没有）
git init

# 添加GitHub远程仓库
git remote add origin git@github.com:glensun810-ai/water_station_system.git

# 或者如果已经关联了远程仓库，检查一下
git remote -v
```

### 3. 手动触发部署

1. 打开 GitHub 仓库页面
2. 点击 `Actions` 标签
3. 选择 `Deploy to Production` 工作流
4. 点击 `Run workflow` 按钮
5. 等待部署完成

## 部署流程

```
1. 拉取最新代码 (git fetch + reset)
2. 备份当前文件到 /var/backup/jhw-ai.com/
3. 替换新文件
4. 设置文件权限
5. 重载 Nginx
6. 验证部署结果
```

## 备份位置

- 前端: `/var/backup/jhw-ai.com/water_YYYYMMDD_HHMMSS.tar.gz`
- 管理后台: `/var/backup/jhw-ai.com/admin_YYYYMMDD_HHMMSS.tar.gz`

## 故障恢复

如果部署失败，可手动恢复：

```bash
# 登录服务器
ssh root@120.76.156.83

# 查看备份
ls -la /var/backup/jhw-ai.com/

# 恢复文件
cd /var/www/jhw-ai.com
tar -xzf /var/backup/jhw-ai.com/water_20260327_120000.tar.gz

# 重载Nginx
aa_nginx -s reload
```
