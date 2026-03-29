# 部署安全检查清单

在使用部署脚本前，请务必完成以下安全检查：

## ✅ 部署前检查

### 1. 敏感信息保护

- [ ] `config-sensitive.sh` 已添加到 `.gitignore`
- [ ] `config-sensitive.sh` 未提交到 Git 仓库
- [ ] SSH 私钥文件权限设置为 `600`
- [ ] 阿里云 AccessKey 权限最小化（如需配置安全组）

### 2. 生产数据备份

- [ ] 已确认 `AUTO_BACKUP=true`（默认开启）
- [ ] 已验证备份目录存在且可写
- [ ] 已了解如何从备份恢复数据

### 3. 服务器配置

- [ ] SSH 密钥认证正常工作
- [ ] 服务器 Python 版本符合要求（3.8+）
- [ ] 服务器 Nginx 或 aaPanel 已安装
- [ ] SSL 证书已放置到指定路径

### 4. 网络配置

- [ ] 域名已正确解析到服务器 IP
- [ ] 阿里云安全组已开放 80/443 端口（或配置自动配置）
- [ ] 防火墙规则允许 HTTP/HTTPS 访问

## 🚨 安全警告

### 绝对禁止

1. ❌ **不要**将 `config-sensitive.sh` 提交到 Git
2. ❌ **不要**在代码中硬编码密码或密钥
3. ❌ **不要**在生产环境使用默认密码
4. ❌ **不要**将 SSH 私钥分享给他人
5. ❌ **不要**在生产环境禁用数据保护

### 必须执行

1. ✅ 定期更换 SSH 密钥和密码
2. ✅ 定期更新阿里云 AccessKey
3. ✅ 定期检查服务器访问日志
4. ✅ 定期备份生产数据
5. ✅ 使用强密码和复杂密钥

## 🔐 密钥管理最佳实践

### SSH 密钥

```bash
# 生成新的 SSH 密钥对
ssh-keygen -t rsa -b 4096 -C "your_email@example.com"

# 设置正确的权限
chmod 600 ~/.ssh/jhw-ai-server.pem
chmod 644 ~/.ssh/jhw-ai-server.pem.pub

# 将公钥添加到服务器
ssh-copy-id -i ~/.ssh/jhw-ai-server.pem.pub root@your_server_ip
```

### 阿里云 AccessKey

1. 登录阿里云控制台
2. 进入"访问控制 (RAM)" → "用户"
3. 创建 RAM 用户并分配最小权限
4. 创建 AccessKey 并妥善保管
5. 定期轮换 AccessKey

## 📊 部署日志审计

部署完成后，建议检查：

1. **服务器日志**
   ```bash
   tail -f /var/log/water-api.log
   ```

2. **Nginx 访问日志**
   ```bash
   tail -f /var/log/nginx/access.log
   ```

3. **系统登录日志**
   ```bash
   last
   ```

4. **失败的登录尝试**
   ```bash
   lastb
   ```

## 🆘 紧急处理

### 如果发现数据泄露

1. 立即停止服务
   ```bash
   ./deploy.sh stop
   ```

2. 更改所有密码和密钥

3. 检查服务器日志，确定泄露范围

4. 通知相关人员

5. 从备份恢复数据（如需要）

### 如果部署失败

1. 检查部署日志
   ```bash
   ./deploy.sh logs
   ```

2. 检查服务状态
   ```bash
   ./deploy.sh status
   ```

3. 查看服务器错误信息
   ```bash
   ./deploy.sh shell
   tail -100 /var/log/water-api.log
   ```

4. 从备份恢复（如果需要）
   ```bash
   ls /var/backups/water/
   ```

## 📞 联系方式

如遇安全问题，请立即联系项目负责人。