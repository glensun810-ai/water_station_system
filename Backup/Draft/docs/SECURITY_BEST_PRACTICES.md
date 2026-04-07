# 安全最佳实践指南

**版本：** 1.0.0  
**更新时间：** 2026年4月2日  
**适用范围：** 企业服务管理平台

---

## 一、关键安全问题

### 🔴 高危问题（必须立即修复）

#### 1.1 硬编码默认密码

**位置：**
- `main.py:1004` - 登录验证
- `main.py:1064` - 密码修改
- `api_admin_auth.py:358` - 管理员初始化

**风险：**
- 攻击者可使用默认密码登录
- 适用于所有未修改密码的账户

**修复方案：**

✅ **已完成：**
- 创建密码管理工具 (`utils/password.py`)
- 配置中设置默认密码 (`config/settings.py`)

⚠️ **待执行：**
1. 首次部署时强制修改默认密码
2. 添加密码强度验证
3. 定期提醒用户修改密码

**操作步骤：**
```bash
# 1. 生成强密码
python3 -c "
from utils import generate_random_password
print(generate_random_password(16))
"

# 2. 更新管理员密码
# 登录后台 -> 用户管理 -> 修改密码

# 3. 删除或禁用默认账户
# 生产环境建议创建新管理员账户后禁用admin账户
```

---

#### 1.2 SECRET_KEY配置问题

**问题描述：**
- 开发环境：使用固定默认值（安全）
- 生产环境：每次重启生成新值（❌ 会导致JWT全部失效）

**位置：**
- `main.py:33` - `secrets.token_urlsafe(32)`
- `api_admin_auth.py:22` - 默认值硬编码

**风险：**
- 服务重启后所有用户需重新登录
- JWT Token全部失效
- 可能导致会话劫持

**修复方案：**

✅ **已完成：**
- 创建统一配置 (`config/settings.py`)
- 支持环境变量

⚠️ **待执行：**
```bash
# 1. 生成SECRET_KEY
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# 2. 设置环境变量（生产环境必须）
export SECRET_KEY="your-generated-secret-key-here"
export JWT_SECRET_KEY="your-jwt-secret-key-here"

# 3. 或创建.env文件
cat > Service_WaterManage/backend/.env << EOF
SECRET_KEY=your-generated-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-key-here
ENVIRONMENT=production
EOF

# 4. 验证配置
python3 -c "from config import settings; print('SECRET_KEY:', settings.SECRET_KEY[:10]+'...')"
```

---

### 🟠 中危问题（建议修复）

#### 2.1 SQL注入风险

**位置：**
- `api_meeting.py:273` - 动态SQL拼接

**风险：**
- 攻击者可注入恶意SQL
- 可能导致数据泄露或删除

**修复方案：**

❌ **错误示例：**
```python
f"UPDATE meeting_rooms SET {', '.join(updates)} WHERE id = :room_id"
```

✅ **正确示例：**
```python
query = text("UPDATE meeting_rooms SET name = :name, capacity = :capacity WHERE id = :room_id")
db.execute(query, {"name": name, "capacity": capacity, "room_id": room_id})
```

---

#### 2.2 敏感信息泄露

**位置：**
- `main.py:1058` - 日志中输出密码哈希

**风险：**
- 日志文件可能泄露敏感信息
- 违反安全审计要求

**修复方案：**

❌ **错误示例：**
```python
print(f"Changing password for user: {user.name}, current hash: {user.password_hash[:30]}")
```

✅ **正确示例：**
```python
print(f"Changing password for user: {user.name}")
# 或使用结构化日志
logger.info("Password changed", extra={"user_id": user.id, "username": user.name})
```

---

## 二、密码安全策略

### 2.1 密码强度要求

**当前配置：**
```python
MIN_PASSWORD_LENGTH = 8  # 最小长度
REQUIRE_SPECIAL_CHAR = False  # 是否要求特殊字符
REQUIRE_NUMBER = False  # 是否要求数字
```

**生产环境建议：**
```python
MIN_PASSWORD_LENGTH = 12  # 建议至少12位
REQUIRE_SPECIAL_CHAR = True  # 必须包含特殊字符
REQUIRE_NUMBER = True  # 必须包含数字
```

### 2.2 密码存储

✅ **已实现：**
- 使用bcrypt哈希
- 自动加盐
- 不可逆加密

### 2.3 密码验证流程

```
用户登录
    ↓
检查用户是否存在
    ↓
检查用户是否激活
    ↓
检查密码哈希是否存在
    ├─ 否 → 使用默认密码验证（兼容旧数据）
    └─ 是 → 使用bcrypt验证
```

---

## 三、JWT认证安全

### 3.1 JWT配置

**当前配置：**
```python
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24  # 24小时过期
JWT_EXPIRE_HOURS = 2  # 管理员Token 2小时过期
```

**安全建议：**
- ✅ 使用强密钥（至少32字节）
- ✅ 定期轮换密钥（建议每季度）
- ✅ 短过期时间（已实现）
- ⚠️ 添加刷新Token机制

### 3.2 Token验证流程

```
请求携带Token
    ↓
验证Token格式
    ↓
解码Token
    ↓
验证签名
    ↓
检查过期时间
    ↓
提取用户信息
```

---

## 四、数据库安全

### 4.1 连接安全

✅ **已实现：**
- 连接池管理
- 健康检查 (pool_pre_ping)
- 自动重连

### 4.2 查询安全

✅ **已实现：**
- 参数化查询
- ORM防注入

⚠️ **待优化：**
- 删除动态SQL拼接
- 添加查询日志

### 4.3 数据备份

**建议：**
```bash
# 自动备份脚本
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backup/db"
DB_FILE="Service_WaterManage/backend/waterms.db"

# 创建备份
cp $DB_FILE $BACKUP_DIR/waterms_$DATE.db

# 保留最近7天备份
find $BACKUP_DIR -name "waterms_*.db" -mtime +7 -delete
```

---

## 五、访问控制

### 5.1 用户角色

| 角色 | 权限 | 说明 |
|------|------|------|
| staff | 普通员工 | 查看个人信息、创建交易 |
| admin | 管理员 | 用户管理、产品管理、交易管理 |
| super_admin | 超级管理员 | 所有权限 + 系统配置 |

### 5.2 权限验证

**当前实现：**
- API级别验证
- 角色检查
- 数据隔离（部分）

**待优化：**
- 资源级别权限控制
- 操作日志记录
- 敏感操作二次验证

---

## 六、生产环境检查清单

### 部署前检查

- [ ] 修改默认管理员密码
- [ ] 设置SECRET_KEY环境变量
- [ ] 设置JWT_SECRET_KEY环境变量
- [ ] 禁用DEBUG模式
- [ ] 配置HTTPS
- [ ] 设置CORS白名单
- [ ] 配置日志
- [ ] 设置数据库备份
- [ ] 配置防火墙规则
- [ ] 安全部署.env文件（chmod 600）

### 运行时监控

- [ ] 监控登录失败次数
- [ ] 监控异常请求
- [ ] 定期审计操作日志
- [ ] 监控数据库访问
- [ ] 定期检查权限配置

---

## 七、安全事件响应

### 7.1 发现安全事件

**立即行动：**
1. 隔离受影响系统
2. 保存日志和证据
3. 通知安全团队
4. 评估影响范围

### 7.2 密码泄露

**处理流程：**
1. 强制重置所有用户密码
2. 生成新的SECRET_KEY
3. 撤销所有JWT Token
4. 通知用户修改密码

### 7.3 数据泄露

**处理流程：**
1. 停止服务
2. 备份当前数据
3. 分析泄露原因
4. 修复安全漏洞
5. 通知相关方

---

## 八、安全加固建议

### 8.1 立即实施

1. **修改默认密码** ✅
   ```bash
   # 登录后台修改
   ```

2. **配置环境变量** ✅
   ```bash
   export SECRET_KEY="$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')"
   export JWT_SECRET_KEY="$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')"
   ```

3. **启用HTTPS**
   ```nginx
   server {
       listen 443 ssl;
       ssl_certificate /path/to/cert.pem;
       ssl_certificate_key /path/to/key.pem;
   }
   ```

### 8.2 短期实施

1. **添加API限流**
   - 防止暴力破解
   - 防止DDoS攻击

2. **添加操作审计**
   - 记录所有敏感操作
   - 保留操作日志

3. **添加IP白名单**
   - 管理后台IP限制
   - 敏感操作IP限制

### 8.3 长期实施

1. **实施WAF**
   - Web应用防火墙
   - 入侵检测系统

2. **安全培训**
   - 定期安全意识培训
   - 代码安全审查

3. **渗透测试**
   - 定期安全测试
   - 漏洞扫描

---

## 九、安全配置示例

### 9.1 生产环境配置

```bash
# .env 文件（生产环境）
ENVIRONMENT=production
DEBUG=false

# 安全配置（必须设置！）
SECRET_KEY=your-secret-key-at-least-32-characters-long
JWT_SECRET_KEY=your-jwt-secret-key-at-least-32-characters-long

# 密码策略
MIN_PASSWORD_LENGTH=12
REQUIRE_SPECIAL_CHAR=true
REQUIRE_NUMBER=true

# 数据库配置
DATABASE_URL=sqlite:///./data/waterms.db
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=40

# 日志配置
LOG_LEVEL=WARNING
LOG_FILE=/var/log/waterms/app.log
```

### 9.2 Nginx配置

```nginx
server {
    listen 80;
    server_name example.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name example.com;

    ssl_certificate /etc/letsencrypt/live/example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/example.com/privkey.pem;

    # 安全头
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

---

## 十、联系方式

**安全问题报告：**
- 邮箱：security@example.com
- 电话：xxx-xxxx-xxxx

**紧急联系：**
- 技术负责人：xxx
- 安全负责人：xxx

---

**文档版本历史：**
- v1.0.0 (2026-04-02) - 初始版本