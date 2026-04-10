# AI产业集群空间服务系统 - 启动指南

**更新时间**: 2026-04-10  
**架构版本**: 新架构（统一API网关）

---

## 🚀 快速启动

### 方法1：一键启动（推荐）

```bash
python run.py
```

此命令会：
- 启动API服务（端口8008）
- 自动打开浏览器访问Portal首页
- 显示服务地址和使用说明

### 方法2：不打开浏览器

```bash
python run.py --no-browser
```

### 方法3：指定端口

```bash
python run.py --port 9000
```

---

## 📋 常用命令

### 查看服务状态

```bash
python run.py status
```

显示：
- 服务运行状态（PID、健康状态）
- 数据统计（产品、用户、办公室、会议室）

### 停止服务

```bash
python run.py stop
```

---

## 🏢 访问地址

### 用户端
- **Portal首页**: http://127.0.0.1:8008/portal/index.html
- **水站服务**: http://127.0.0.1:8008/portal/water/index.html
- **会议室预约**: http://127.0.0.1:8008/meeting-frontend/index.html

### 管理端
- **管理后台首页**: http://127.0.0.1:8008/portal/admin/index.html
- **水站管理**: http://127.0.0.1:8008/portal/admin/water/dashboard.html
- **会议室管理**: http://127.0.0.1:8008/portal/admin/meeting/rooms.html
- **用户管理**: http://127.0.0.1:8008/portal/admin/users.html
- **办公室管理**: http://127.0.0.1:8008/portal/admin/offices.html

### 开发者
- **API文档**: http://127.0.0.1:8008/docs
- **健康检查**: http://127.0.0.1:8008/health

---

## 🔐 登录信息

### 管理员账号
- 用户名：`admin`
- 密码：`123456`
- 角色：超级管理员

### 其他账号
- 系统管理员（admin）
- 办公室管理员（office_admin）
- 普通用户（user）

---

## 📊 新架构特点

### 统一化设计
- ✅ **单端口访问** - 所有服务统一在8008端口
- ✅ **统一API网关** - `/api/v1/{service}/{resource}`
- ✅ **统一数据库** - SQLite数据一致性保证
- ✅ **统一前端入口** - Portal集成所有服务

### 模块化架构
- ✅ **水站服务** - 领水、结算、产品管理
- ✅ **会议室服务** - 预约、审批、会议室管理
- ✅ **系统管理** - 用户、办公室、权限管理

### 标准化设计
- ✅ **API规范** - RESTful API，版本控制
- ✅ **认证授权** - JWT Bearer Token
- ✅ **前端组件** - Vue 3，共享组件库

---

## 🆚 与旧架构对比

### 旧架构（已废弃）
```
端口8000 → 水站服务
端口8001 → 会议室服务
端口8007 → 餐厅服务
端口8008 → 预约服务
```

### 新架构（当前）
```
端口8008 → 统一API网关
           ├─ 水站服务
           ├─ 会议室服务
           └─ 系统管理
```

---

## 📁 项目结构

### 核心目录
```
run.py              # 统一启动程序
apps/               # 应用服务模块
  ├── main.py       # API网关入口
  ├── water/        # 水站服务
  ├── meeting/      # 会议室服务
  └── system/       # 系统管理
config/             # 配置中心
models/             # 数据模型
portal/             # 前端页面
shared/             # 共享资源
data/               # 数据存储
logs/               # 日志文件
```

---

## 🛠️ 开发辅助

### 数据恢复
```bash
python restore_data.py           # 恢复历史数据
python reimport_meeting_data.py  # 重新导入会议室数据
```

### 系统验证
```bash
python verify_system_health.py   # 系统健康检查
python system_validator.py       # 系统完整性验证
```

---

## 📝 日志文件

### 日志位置
- API服务日志：`logs/api_service.log`
- 启动程序日志：实时输出到终端

### PID文件
- 服务PID：`.pids/api_service.pid`

---

## ❓ 常见问题

### Q1: 端口被占用怎么办？
**A**: 启动程序会自动检测端口可用性：
- 如果8008端口被占用，会自动查找备用端口
- 或使用 `python run.py --port 9000` 指定端口

### Q2: 服务启动失败？
**A**: 检查以下项：
- 数据库文件：`data/app.db` 是否存在
- 日志文件：查看 `logs/api_service.log`
- Python版本：需要3.8+

### Q3: 浏览器无法访问？
**A**: 确认：
- 服务是否正常运行：`python run.py status`
- 使用正确端口：8008（不是8000）
- URL正确：`http://127.0.0.1:8008/portal/index.html`

### Q4: 登录失败？
**A**: 确认：
- 用户名：`admin`
- 密码：`123456`
- 服务已启动且健康

---

## 📞 技术支持

### 文档
- 架构文档：`docs/`
- API文档：`http://127.0.0.1:8008/docs`

### 验证报告
- 架构梳理报告：`docs/架构梳理报告_20260410.md`
- 最终验收报告：`docs/最终验收报告_20260410.md`

---

## 🎯 启动流程

```
python run.py
    ↓
停止旧服务
    ↓
启动API服务（8008端口）
    ↓
等待服务就绪
    ↓
打开浏览器
    ↓
显示使用说明
    ↓
服务运行（等待Ctrl+C）
```

---

## 🎉 享受新架构带来的便利！

- 单端口统一访问
- 模块化服务架构
- 标准化API规范
- 前端集成入口

**一键启动，简单高效！**