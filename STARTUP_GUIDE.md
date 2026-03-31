# AI 产业集群空间服务管理系统 - 启动指南

## 📋 快速启动

### 方法 1：Python 启动（推荐，跨平台）

```bash
# 启动所有服务并自动打开浏览器
cd /Users/sgl/PycharmProjects/AIchanyejiqun
python3 start_all.py

# 启动所有服务但不打开浏览器
python3 start_all.py --no-browser

# 停止所有服务
python3 start_all.py stop
```

### 方法 2：Shell 脚本（Mac/Linux）

```bash
# 启动所有服务
./start_all.sh

# 停止所有服务
./stop_all.sh
```

---

## 🌐 访问地址

### 用户端

| 服务 | 地址 |
|------|------|
| 🏠 统一门户首页 | http://localhost:8080/portal/index.html |
| 💧 水站管理 | http://localhost:8080/Service_WaterManage/frontend/index.html |
| 🏛️ 会议室预定 | http://localhost:8080/Service_MeetingRoom/frontend/index.html |
| 🍽️ 餐厅茶室 | http://localhost:8080/Service_Dining/frontend/index.html |
| 🏢 办公空间 | http://localhost:8080/Service_Office/frontend/index.html |
| 📺 前台大屏 | http://localhost:8080/Service_Screen/frontend/index.html |

### 管理后台

| 服务 | 地址 |
|------|------|
| 水站管理 | http://localhost:8080/Service_WaterManage/frontend/admin.html |
| 会议室管理 | http://localhost:8080/Service_MeetingRoom/frontend/admin.html |
| 餐厅茶室管理 | http://localhost:8080/Service_Dining/frontend/admin.html |
| 前台大屏管理 | http://localhost:8080/Service_Screen/frontend/admin.html |

### 测试账号

```
用户名：admin
密码：admin123
角色：super_admin
```

---

## 🔧 服务说明

| 服务 | 端口 | 说明 |
|------|------|------|
| 水站服务 | 8000 | 水站管理后端 API |
| 统一 API 网关 | 8001 | 其他所有服务的 API |
| 前端静态文件 | 8080 | 前端页面访问 |

---

## 📁 日志文件

启动后，日志文件位于 `logs/` 目录：

```
logs/
├── waterms.log      # 水站服务日志
├── gateway.log      # API 网关日志
└── frontend.log     # 前端服务日志
```

---

## ⚠️ 常见问题

### 1. 端口被占用

如果提示端口被占用，可以：

```bash
# 查看占用端口的进程
lsof -i:8000
lsof -i:8001
lsof -i:8080

# 手动停止
kill -9 <PID>

# 或使用停止脚本
python3 start_all.py stop
```

### 2. 虚拟环境不存在

```bash
# 创建虚拟环境
python3 -m venv .venv

# 安装依赖
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. 前端页面 404

确保通过 8080 端口访问前端页面，而不是直接访问后端服务。

### 4. 浏览器未自动打开

如果启动后浏览器未自动打开，可以手动访问：
```
http://localhost:8080/portal/index.html
```

或使用 `--no-browser` 参数启动：
```bash
python3 start_all.py --no-browser
```

---

## 🛑 停止服务

```bash
# 方法 1：Python
python3 start_all.py stop

# 方法 2：Shell
./stop_all.sh

# 方法 3：手动
kill $(cat .pids/*.pid)
```

---

## 📝 使用说明

1. 启动服务后，浏览器会自动打开统一门户首页
2. 点击相应的服务卡片进入具体功能
3. 首次使用需要登录（admin / admin123）
4. 管理后台用于管理员审核和管理

---

## 💡 高级用法

### 命令行参数

```bash
# 启动并打开浏览器（默认）
python3 start_all.py

# 启动但不打开浏览器
python3 start_all.py --no-browser

# 停止服务
python3 start_all.py stop

# 查看帮助
python3 start_all.py --help
```

---

**版本**: 2.0  
**更新日期**: 2026-03-31  
**新增功能**: 自动打开浏览器
