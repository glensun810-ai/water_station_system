# 最新启动程序说明

## 🎯 最新的一键启动程序

**文件位置**: `/Users/sgl/PycharmProjects/AIchanyejiqun/run.py`

**创建时间**: 2026年4月10日

**架构**: 新架构统一启动程序（单端口、统一API）

---

## 启动方式

### 方式1：一键启动（推荐）

使用统一的启动脚本：

```bash
cd /Users/sgl/PycharmProjects/AIchanyejiqun

# 启动并自动打开浏览器
python run.py

# 启动但不打开浏览器
python run.py --no-browser

# 使用指定端口
python run.py --port 8000

# 查看服务状态
python run.py status

# 停止服务
python run.py stop
```

**特点**：
- ✅ 自动清理残留进程
- ✅ 自动选择可用端口（默认8008，可自定义）
- ✅ 自动打开浏览器访问Portal
- ✅ 统一使用 `apps.main:app` 作为API入口
- ✅ 单端口提供所有服务

---

### 方式2：Shell脚本启动

使用旧的启动脚本（已废弃，不建议使用）：

```bash
cd /Users/sgl/PycharmProjects/AIchanyejiqun
./start.sh
```

**注意**: start.sh 会调用 run.py，所以本质上是一样的。

---

### 方式3：直接使用uvicorn（开发调试用）

直接启动API服务：

```bash
cd /Users/sgl/PycharmProjects/AIchanyejiqun

# 使用默认端口8000（当前运行状态）
python -m uvicorn apps.main:app --host 0.0.0.0 --port 8000 --reload

# 使用新架构默认端口8008
python -m uvicorn apps.main:app --host 0.0.0.0 --port 8008 --reload
```

---

## 重要说明

### ⚠️ 端口差异

- **新架构默认端口**: 8008（run.py设计）
- **当前实际端口**: 8000（当前服务器运行端口）

**解决方案**：

如果需要使用8008端口（新架构默认），请：

```bash
# 1. 停止当前8000端口的服务
python run.py stop

# 2. 使用默认端口8008启动
python run.py
```

或者继续使用8000端口：

```bash
python run.py --port 8000
```

---

## 正确的API入口

### ✅ 必须使用

**文件**: `apps/main.py`
**启动命令**: `uvicorn apps.main:app`

### ❌ 不要使用（已废弃/旧架构）

以下入口文件已废弃或属于旧架构，**不要再使用**：

- ❌ `apps/water/backend/main.py`（旧水站后端）
- ❌ `apps/water/main.py`（旧水站入口）
- ❌ `apps/meeting/backend/main.py`（旧会议室后端）
- ❌ `apps/meeting/main.py`（旧会议室入口）

**原因**: 这些旧入口会导致路由冲突、Schema缺失等问题。

---

## 完整的启动流程

### 1. 确认项目目录
```bash
cd /Users/sgl/PycharmProjects/AIchanyejiqun
```

### 2. 检查是否有残留进程
```bash
lsof -i :8000 | grep LISTEN
lsof -i :8008 | grep LISTEN
```

### 3. 清理残留进程（如果有）
```bash
lsof -i :8000 | grep LISTEN | awk '{print $2}' | xargs kill -9
lsof -i :8008 | grep LISTEN | awk '{print $2}' | xargs kill -9
```

### 4. 使用最新启动程序
```bash
# 方式A: 使用run.py（推荐）
python run.py --port 8000

# 方式B: 直接使用uvicorn（开发调试）
python -m uvicorn apps.main:app --host 0.0.0.0 --port 8000 --reload
```

### 5. 验证服务启动
```bash
# 检查服务状态
python run.py status

# 或手动检查
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/api/v1/products
```

---

## Portal访问地址

根据使用的端口：

**端口8000（当前）**:
- Portal主页: http://127.0.0.1:8000/portal/index.html
- 产品管理: http://127.0.0.1:8000/portal/admin/water/products.html
- 用户管理: http://127.0.0.1:8000/portal/admin/users.html
- 办公室管理: http://127.0.0.1:8000/portal/admin/offices.html
- API文档: http://127.0.0.1:8000/docs

**端口8008（新架构默认）**:
- Portal主页: http://127.0.0.1:8008/portal/index.html
- 产品管理: http://127.0.0.1:8008/portal/admin/water/products.html
- 用户管理: http://127.0.0.1:8008/portal/admin/users.html
- 办公室管理: http://127.0.0.1:8008/portal/admin/offices.html
- API文档: http://127.0.0.1:8008/docs

---

## 总结

| 启动文件 | 状态 | 说明 | 推荐 |
|---------|------|------|------|
| `run.py` | ✅ 最新 | 新架构统一启动程序 | ⭐⭐⭐⭐⭐ |
| `start.sh` | ✅ 可用 | 调用run.py | ⭐⭐⭐ |
| `apps/main.py` | ✅ 正确 | API入口文件（配合uvicorn） | ⭐⭐⭐⭐ |
| `apps/water/backend/main.py` | ❌ 废弃 | 旧架构，不要使用 | ❌ |
| `apps/water/main.py` | ❌ 废弃 | 旧架构，不要使用 | ❌ |

**最佳实践**: 使用 `python run.py --port 8000` 启动服务

生成时间: 2026-04-11