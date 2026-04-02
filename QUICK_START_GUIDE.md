# 会议室管理模块 - 快速启动指南

## 一、立即启动服务

### 方式1：主应用启动（推荐）

```bash
cd Service_WaterManage/backend
python3 main.py
```

服务启动后访问：
- API文档：http://localhost:8000/docs
- 预约页面：Service_MeetingRoom/frontend/index.html
- 管理员登录：Service_MeetingRoom/frontend/admin_login.html

### 方式2：独立启动（仅会议室模块）

```bash
python3 start_meeting_enhanced.py
```

---

## 二、功能测试

### 测试1：时间段检查API

```bash
curl -X POST http://localhost:8000/api/meeting/flexible/check-time-slot \
  -H 'Content-Type: application/json' \
  -d '{"room_id": 1, "booking_date": "2026-04-02", "start_time": "09:00", "end_time": "12:00"}'
```

预期返回：
```json
{
  "is_available": true,
  "conflict_count": 0,
  "duration_minutes": 180,
  "duration_hours": 3.0,
  "is_valid": true,
  "message": "时间段可用",
  "warnings": []
}
```

### 测试2：管理员登录API

```bash
curl -X POST http://localhost:8000/api/admin/login \
  -H 'Content-Type: application/json' \
  -d '{"username": "admin", "password": "admin123"}'
```

预期返回：
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "expires_in": 7200,
  "user_info": {
    "user_id": 1,
    "username": "admin",
    "role_id": 1,
    "role_name": "超级管理员",
    "permissions": "[\"all\"]"
  }
}
```

### 测试3：获取可用时段

```bash
curl http://localhost:8000/api/meeting/flexible/available-slots/1/2026-04-02
```

### 测试4：快捷时段

```bash
curl http://localhost:8000/api/meeting/flexible/quick-slots
```

---

## 三、前端功能测试

### 测试页面功能

1. **打开预约页面**
   - 直接打开：Service_MeetingRoom/frontend/index.html
   - 或通过portal访问

2. **测试灵活时间段**
   - 选择会议室
   - 点击"上午"快捷按钮 → 自动填充 09:00-12:00
   - 观察实时验证结果（绿色提示）
   - 修改时间 → 再次验证

3. **测试冲突检测**
   - 创建一个预约（如 09:00-12:00）
   - 再次预约相同时间段 → 显示红色冲突警告

4. **测试时长验证**
   - 选择开始 09:00，结束 09:15 → 显示黄色警告（时长不足）
   - 选择开始 07:00，结束 23:00 → 显示黄色警告（超时长）

---

## 四、管理员功能测试

### 登录测试

1. **打开登录页面**
   - Service_MeetingRoom/frontend/admin_login.html

2. **输入账号**
   - 用户名：admin
   - 密码：admin123

3. **登录成功**
   - 自动跳转到管理后台（admin.html）
   - Token保存在localStorage

### API测试（使用Token）

```bash
# 获取当前用户信息
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/admin/me

# 查看操作日志
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/admin/logs

# 查看角色列表
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/admin/roles
```

---

## 五、常见问题

### Q1：API无法访问？

**检查：**
- 确认服务已启动（main.py正在运行）
- 确认路由已注册（main.py包含include_router）
- 确认数据库文件存在（Service_MeetingRoom/backend/meeting.db）

**解决：**
```bash
# 检查数据库
ls Service_MeetingRoom/backend/meeting.db

# 如果不存在，运行迁移
python3 Service_MeetingRoom/migrate_database.py
```

### Q2：时间段验证失败？

**检查：**
- 时间格式是否正确（HH:MM）
- 是否在07:00-22:00范围
- 分钟是否为30分钟间隔
- 开始时间是否早于结束时间

### Q3：管理员登录失败？

**检查：**
- 用户名密码是否正确
- 数据库是否有admin用户
- bcrypt密码是否正确存储

**解决：**
```bash
# 重新初始化管理员
python3 -c "
from Service_MeetingRoom.migrate_database import init_admin_tables
init_admin_tables()
"
```

---

## 六、下一步

1. **修改默认密码**（强烈建议）
   - 登录管理后台
   - 修改admin账号密码

2. **配置生产环境**
   - 设置JWT_SECRET_KEY环境变量
   - 配置HTTPS
   - 启用API限流

3. **功能扩展**
   - 添加时间段可视化
   - 实现批量预约管理
   - 添加通知提醒功能

---

**祝使用愉快！** 🎉