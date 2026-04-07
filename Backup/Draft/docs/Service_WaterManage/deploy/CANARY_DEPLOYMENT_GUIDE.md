# 灰度发布系统使用指南

## 概述

本项目已实现完整的灰度发布系统，允许将最新代码部署到独立的灰度环境进行验证，而不影响生产环境。验证通过后，可将灰度环境提升到生产环境。

## 系统架构

### 环境隔离

**生产环境**
- 前端访问: `jhw-ai.com/water`, `jhw-ai.com/water-admin`
- 后端端口: `8000`
- 数据库: `waterms.db`
- 项目路径: `/var/www/jhw-ai.com`

**灰度环境**
- 前端访问: `canary.jhw-ai.com/water`, `canary.jhw-ai.com/water-admin`
- 后端端口: `8001`
- 数据库: `waterms_canary.db` (生产数据库副本)
- 项目路径: `/var/www/canary-jhw-ai.com`

## 核心脚本

### 1. 灰度部署脚本
```bash
./deploy-canary.sh deploy      # 部署到灰度环境
./deploy-canary.sh status      # 查看灰度环境状态
./deploy-canary.sh logs        # 查看灰度环境日志
./deploy-canary.sh stop        # 停止灰度环境
./deploy-canary.sh shell       # SSH到服务器
./deploy-canary.sh clean       # 清理灰度环境
```

### 2. 数据库同步脚本
```bash
./sync-db-to-canary.sh              # 同步生产数据库到灰度环境
./sync-db-to-canary.sh --force      # 强制覆盖灰度数据库
./sync-db-to-canary.sh --dry-run    # 预演模式
./sync-db-to-canary.sh --compare    # 查看数据库对比
```

### 3. 灰度提升脚本
```bash
./promote-canary.sh           # 提升灰度到生产（需确认）
./promote-canary.sh --dry-run # 预演模式
```

### 4. 回滚脚本
```bash
./rollback-canary.sh canary        # 回滚灰度环境
./rollback-canary.sh production    # 回滚生产环境（提升后回滚）
./rollback-canary.sh --list        # 查看可用备份
```

## 使用流程

### 完整灰度发布流程

```
┌─────────────────┐
│ 1. 部署到灰度环境 │
└─────────────────┘
         ↓
┌─────────────────┐
│ 2. 验证灰度环境  │
└─────────────────┘
         ↓
┌─────────────────┐
│ 3. 提升到生产环境│
└─────────────────┘
         ↓
┌─────────────────┐
│ 4. 验证生产环境  │
└─────────────────┘
```

### 步骤 1: 部署到灰度环境

```bash
cd Service_WaterManage/deploy

# 部署最新代码到灰度环境
./deploy-canary.sh deploy
```

部署过程会：
- 检查环境连接
- 从生产环境复制最新数据库到灰度环境
- 上传最新后端代码
- 上传最新前端代码
- 配置灰度环境的Nginx（子域名 `canary.jhw-ai.com`）
- 启动灰度环境后端服务（端口8001）
- 验证灰度环境部署

### 步骤 2: 验证灰度环境

访问灰度环境进行测试：
- 用户端: `https://canary.jhw-ai.com/water/`
- 管理后台: `https://canary.jhw-ai.com/water-admin/`
- API: `https://canary.jhw-ai.com/api/`

验证要点：
1. 登录功能正常
2. 核心业务流程正常
3. 数据展示正确
4. API响应正常
5. 无明显bug或错误

查看灰度环境状态：
```bash
./deploy-canary.sh status
./deploy-canary.sh logs
```

### 步骤 3: 提升到生产环境（验证通过后）

```bash
# 先预演，了解提升流程
./promote-canary.sh --dry-run

# 实际执行提升
./promote-canary.sh
```

提升过程会：
1. 验证灰度环境正常运行
2. 备份生产环境
3. 停止生产环境服务
4. 切换灰度配置到生产配置
5. 启动生产环境服务
6. 验证生产环境
7. 可选清理灰度环境

### 步骤 4: 验证生产环境

访问生产环境确认：
- 用户端: `https://jhw-ai.com/water/`
- 管理后台: `https://jhw-ai.com/water-admin/`
- API: `https://jhw-ai.com/api/`

如果出现问题，可立即回滚：
```bash
./rollback-canary.sh production
```

## 常见场景

### 场景 1: 重新部署灰度环境

如果灰度环境有问题或需要重新测试：
```bash
# 清理灰度环境
./deploy-canary.sh clean

# 重新部署
./deploy-canary.sh deploy
```

### 场景 2: 同步最新生产数据到灰度

如果需要测试最新生产数据：
```bash
./sync-db-to-canary.sh
```

### 场景 3: 灰度环境测试失败

如果灰度环境测试失败：
- 修复本地代码
- 清理灰度环境: `./deploy-canary.sh clean`
- 重新部署: `./deploy-canary.sh deploy`
- 或回滚灰度环境: `./rollback-canary.sh canary`

### 场景 4: 生产环境提升后有问题

如果提升后生产环境有问题：
```bash
# 查看可用备份
./rollback-canary.sh --list

# 回滚生产环境
./rollback-canary.sh production
```

## 安全特性

### 数据隔离
- 灰度环境使用独立的数据库副本
- 不影响生产数据库
- 灰度环境可随时清理重建

### 自动备份
- 提升前自动备份生产环境
- 数据库操作前自动备份
- 支持快速回滚

### 增量更新
- 使用rsync增量同步代码
- 只更新有变化的文件
- 排除所有数据文件

### 验证机制
- 多重健康检查
- 自动验证部署结果
- 支持预演模式

## 注意事项

### 1. DNS配置

灰度环境使用子域名 `canary.jhw-ai.com`，需要：
- 在DNS服务商配置子域名解析到服务器IP
- 或使用通配符域名 `*.jhw-ai.com`
- SSL证书支持子域名（通配符证书）

### 2. SSL证书

灰度环境需要SSL证书支持：
- 使用通配符证书（推荐）：`*.jhw-ai.com`
- 或为灰度子域名单独申请证书

### 3. 服务器资源

灰度环境需要额外资源：
- 端口8001（或修改配置使用其他端口）
- 独立的项目目录空间
- 数据库副本存储空间

### 4. 首次使用

首次使用灰度发布系统前：
1. 确认服务器可达且SSH连接正常
2. 确认DNS已配置灰度子域名
3. 确认SSL证书支持灰度域名
4. 确认服务器有足够资源

## 故障排查

### 网络连接问题

```bash
# 测试服务器连通性
ping 120.76.156.83

# 测试SSH连接
ssh -i ~/.ssh/jhw-ai-server.pem root@120.76.156.83

# 或使用密码
sshpass -p 'your_password' ssh root@120.76.156.83
```

### 服务状态检查

```bash
# 查看灰度环境状态
./deploy-canary.sh status

# 查看灰度环境日志
./deploy-canary.sh logs

# SSH到服务器查看
./deploy-canary.sh shell
```

### 数据库问题

```bash
# 查看数据库对比
./sync-db-to-canary.sh --compare

# 重新同步数据库
./sync-db-to-canary.sh --force
```

### 回滚操作

```bash
# 回滚灰度环境
./rollback-canary.sh canary

# 回滚生产环境（紧急情况）
./rollback-canary.sh production

# 查看可用备份
./rollback-canary.sh --list
```

## 配置文件

### config-canary.sh
灰度环境配置，包括：
- 灰度域名和端口
- 项目路径
- 数据库文件名
- 其他环境参数

### config-sensitive.sh
敏感信息配置，包括：
- SSH密钥路径
- 服务器密码
- 阿里云凭证（可选）

## 最佳实践

1. **始终预演**: 执行重要操作前使用 `--dry-run` 预演
2. **充分验证**: 灰度环境充分测试后再提升
3. **保留备份**: 定期清理旧备份，但保留最近的几个备份
4. **监控日志**: 部署后监控日志，及时发现问题
5. **快速回滚**: 遇到问题立即回滚，不要尝试在线修复

## 扩展功能

### 自定义灰度域名

修改 `config-canary.sh`:
```bash
CANARY_DOMAIN="your-canary-domain.com"
```

### 自定义灰度端口

修改 `config-canary.sh`:
```bash
BACKEND_PORT=8002  # 修改为其他端口
```

### 使用路径方式（而非子域名）

修改 `config-canary.sh`:
```bash
# 注释掉子域名方式
# CANARY_DOMAIN="canary.jhw-ai.com"

# 使用路径方式
CANARY_PATH="/canary"
DOMAIN="jhw-ai.com"
```

然后需要修改Nginx配置使用路径而非子域名。

## 总结

灰度发布系统提供了安全、可靠的部署流程，允许在不影响生产环境的情况下测试新代码。通过严格的隔离、自动备份和快速回滚机制，确保部署安全可控。

核心流程：
1. 部署到灰度环境 → 2. 验证灰度环境 → 3. 提升到生产环境 → 4. 验证生产环境

关键特性：
- ✅ 环境完全隔离
- ✅ 数据独立安全
- ✅ 自动备份保护
- ✅ 快速回滚支持
- ✅ 预演模式验证
- ✅ 多重健康检查