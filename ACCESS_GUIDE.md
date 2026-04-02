# 系统访问指南

## 问题诊断

您遇到的404错误是因为访问路径不正确。

**错误的访问路径：**
```
http://localhost:8080/water-admin/login.html ❌
```

**正确的访问路径：**
```
http://localhost:8080/frontend/login.html ✅
```

---

## 快速修复步骤

### 1. 停止当前服务
```bash
# 按 Ctrl+C 停止正在运行的服务
```

### 2. 使用启动脚本重启
```bash
cd Service_WaterManage
./start.sh
```

### 3. 使用正确的地址访问

**前端页面：**
- 登录页面：http://localhost:8080/frontend/login.html
- 管理后台：http://localhost:8080/frontend/admin.html
- 预约页面：http://localhost:8080/frontend/index.html

**API文档：**
- Swagger UI：http://localhost:8080/docs
- ReDoc：http://localhost:8080/redoc

---

## 完整访问地址列表

### 前端页面

| 页面 | 地址 | 说明 |
|------|------|------|
| 登录 | http://localhost:8080/frontend/login.html | 管理员登录 |
| 管理 | http://localhost:8080/frontend/admin.html | 管理后台 |
| 预约 | http://localhost:8080/frontend/index.html | 用户预约 |
| 服务 | http://localhost:8080/frontend/services.html | 服务列表 |
| 套餐 | http://localhost:8080/frontend/packages.html | 套餐管理 |

### API文档

| 文档 | 地址 | 说明 |
|------|------|------|
| Swagger | http://localhost:8080/docs | 交互式API文档 |
| ReDoc | http://localhost:8080/redoc | 美观的API文档 |

---

## 登录凭据

### 默认管理员账号

**用户名：** admin  
**密码：** 见 `.env` 文件中的 `DEFAULT_ADMIN_PASSWORD`

**⚠️ 重要：**
- 首次登录后请立即修改密码
- 密码要求：至少12位，包含特殊字符和数字

---

## 启动方式

### 方式一：使用启动脚本（推荐）

```bash
cd Service_WaterManage
./start.sh
```

### 方式二：手动启动

```bash
cd Service_WaterManage/backend
python3 main.py
```

**注意：** 默认监听8080端口

---

## 常见问题

### Q1: 404错误怎么办？

**原因：** 访问路径错误

**解决：** 使用正确的路径
- ✅ 正确：`/frontend/login.html`
- ❌ 错误：`/water-admin/login.html`

### Q2: 无法连接到服务器？

**检查：**
1. 服务是否启动成功
2. 端口是否被占用
3. 防火墙设置

**解决：**
```bash
# 检查端口占用
lsof -i :8080

# 更改端口（在main.py最后）
uvicorn.run(app, host="0.0.0.0", port=8081)
```

### Q3: 登录失败？

**检查：**
1. 用户名密码是否正确
2. 数据库是否存在
3. 查看控制台错误信息

**解决：**
```bash
# 检查数据库
ls Service_WaterManage/backend/waterms.db

# 如果不存在，需要初始化
cd Service_WaterManage/backend
python3 -c "from main import *; Base.metadata.create_all(bind=engine)"
```

---

## 下一步

完成登录后，您可以：

1. **修改密码**
   - 进入管理后台
   - 用户管理 → 修改密码

2. **查看功能**
   - 用户管理
   - 产品管理
   - 交易管理
   - 会议室预约

3. **配置系统**
   - 系统设置
   - 权限管理

---

## 技术支持

**问题反馈：**
- 查看日志：`Service_WaterManage/backend/logs/app.log`
- API文档：http://localhost:8080/docs

**相关文档：**
- `FINAL_EXECUTION_REPORT.md` - 完成报告
- `SECURITY_BEST_PRACTICES.md` - 安全指南
- `ARCHITECT_GUIDANCE.md` - 架构指导

---

**更新时间：** 2026年4月2日