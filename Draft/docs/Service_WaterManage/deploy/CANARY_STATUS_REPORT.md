# 灰度环境部署状态报告

## ⚠️ 严重问题：服务器不可达

### 当前状态
- **服务器IP**: 120.76.156.83
- **域名**: jhw-ai.com
- **SSH端口**: 22
- **状态**: ❌ 完全不可达

### 测试结果
1. **Ping测试**: 100% 丢包
   ```
   PING 120.76.156.83: Request timeout
   ```

2. **SSH连接**: Connection timed out
   ```
   ssh: connect to host 120.76.156.83 port 22: Operation timed out
   ```

3. **HTTPS访问**: Failed to connect
   ```
   curl: Failed to connect to jhw-ai.com port 443
   ```

4. **DNS解析**: 正常（IP正确）
   ```
   jhw-ai.com -> 120.76.156.83
   ```

### 可能原因

1. **服务器已停止或宕机**
   - 需在云服务商控制台检查服务器状态
   - 阿里云控制台: https://ecs.console.aliyun.com

2. **防火墙完全阻断**
   - 安全组规则可能被修改
   - 端口22、80、443可能全部关闭

3. **网络故障**
   - 服务器网络配置问题
   - ISP或路由问题

4. **IP地址变更**
   - 服务器可能被重新分配IP
   - DNS解析可能还未更新

## 🔧 解决方案

### 方案 1: 检查服务器状态（推荐）

1. **登录阿里云控制台**
   - 访问: https://ecs.console.aliyun.com
   - 查找实例ID或IP: 120.76.156.83

2. **检查实例状态**
   - 确认实例是否运行中
   - 查看监控数据（CPU、网络、磁盘）
   - 检查是否有异常告警

3. **检查安全组规则**
   - 确认端口22（SSH）是否开放
   - 确认端口80、443（HTTP/HTTPS）是否开放
   - 来源：0.0.0.0/0（允许所有IP访问）

4. **重启服务器（如果已停止）**
   - 在控制台启动实例
   - 等待2-3分钟启动完成

### 方案 2: 通过阿里云控制台连接

如果SSH不可用，可通过控制台远程连接：

1. 登录阿里云ECS控制台
2. 找到对应实例
3. 点击"远程连接"
4. 使用VNC或Workbench连接
5. 检查服务器内部状态

### 方案 3: 更新IP地址

如果服务器IP已变更：

1. 在控制台查看新的公网IP
2. 更新配置文件:
   ```bash
   vim Service_WaterManage/deploy/config.sh
   # 修改 SERVER_HOST="新IP地址"
   ```
3. 更新DNS解析（在域名服务商控制台）

### 方案 4: 联系服务商

如果以上方案都无法解决：
- 联系阿里云技术支持
- 提供实例ID和问题描述
- 请求协助排查网络问题

## ✅ 服务器恢复后的操作

### 步骤 1: 确认连接恢复
```bash
# 测试SSH连接
ssh -i ~/.ssh/jhw-ai-server.pem root@120.76.156.83

# 或使用密码
sshpass -p 'your_password' ssh root@120.76.156.83
```

### 步骤 2: 配置DNS子域名
需要在域名服务商配置灰度子域名：

```
类型: A记录
主机记录: canary
记录值: 120.76.156.83
TTL: 600
```

### 步骤 3: 配置SSL证书
灰度环境需要SSL证书支持：

**推荐方案**: 使用通配符证书
```
*.jhw-ai.com
```

**备选方案**: 为子域名单独申请证书
```
canary.jhw-ai.com
```

### 步骤 4: 执行灰度部署
```bash
cd Service_WaterManage/deploy

# 部署到灰度环境
./deploy-canary.sh deploy
```

### 步骤 5: 访问灰度环境
部署成功后访问：
- **灰度用户端**: https://canary.jhw-ai.com/water/
- **灰度管理后台**: https://canary.jhw-ai.com/water-admin/
- **灰度API**: https://canary.jhw-ai.com/api/

### 步骤 6: 验证测试
在灰度环境测试：
1. 登录功能
2. 核心业务流程
3. 数据展示和操作
4. API响应
5. 无明显bug

### 步骤 7: 提升到生产（验证通过后）
```bash
./promote-canary.sh
```

## 📊 系统架构（部署后）

### 生产环境
- 前端: https://jhw-ai.com/water/
- 管理后台: https://jhw-ai.com/water-admin/
- API: https://jhw-ai.com/api/
- 后端端口: 8000
- 数据库: waterms.db

### 灰度环境
- 前端: https://canary.jhw-ai.com/water/
- 管理后台: https://canary.jhw-ai.com/water-admin/
- API: https://canary.jhw-ai.com/api/
- 后端端口: 8001
- 数据库: waterms_canary.db

## 🚨 紧急联系

如果服务器问题无法解决，请：
1. 立即联系服务器管理员
2. 登录云服务商控制台检查
3. 考虑切换到备用服务器
4. 联系技术支持团队

## 📝 需要的信息

为了协助排查，请提供：
- 阿里云实例ID
- 服务器购买/开通时间
- 最后正常运行时间
- 是否有其他管理员访问权限
- 是否有控制台访问权限

---

**当前状态**: 🔴 无法部署 - 服务器完全不可达

**优先级**: 🚨 最高 - 需立即解决服务器连接问题

**下一步**: 请先解决服务器可达性问题，然后执行部署