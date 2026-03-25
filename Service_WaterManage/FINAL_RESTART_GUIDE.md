# 统一账户页面 500 错误 - 完整修复与重启指南

## 🔴 当前问题症状

1. **CORS 错误**: `No 'Access-Control-Allow-Origin' header`
2. **500 Internal Server Error**: 所有 API 请求都返回 500
3. **认证失败**: `/api/auth/me` 返回 500 错误

**根本原因**: 
- JWT 验证异常处理已修复，但后端服务可能还在使用旧代码
- 或者数据库字段迁移还未执行

---

## ✅ 完整修复步骤

### 步骤 1: 执行数据库迁移 (必须!)

```bash
cd /Users/sgl/PycharmProjects/AIchanyejiqun/Service_WaterManage/backend
python migrate_add_fields.py
```

**预期输出**:
```
当前 account_wallet 表的字段:
  - id
  - user_id
  - product_id
  - wallet_type
  - available_qty
  - locked_qty
  - total_consumed

添加 paid_qty 字段...
✅ paid_qty 字段添加成功
添加 free_qty 字段...
✅ free_qty 字段添加成功

✅ 数据库迁移完成!
📁 数据库文件：waterms.db
```

---

### 步骤 2: 完全停止后端服务

#### PyCharm 中操作:
1. 找到运行控制台 (Run 窗口)
2. 点击**红色停止按钮** ⏹️
3. **重要**: 等待 3-5 秒，确保进程完全退出
4. 如果还有进程在运行，继续点击停止按钮

#### 命令行方式 (可选):
```bash
# 查找并杀死 Python 进程
ps aux | grep "python.*main"
kill -9 <PID>
```

---

### 步骤 3: 清理所有缓存

```bash
cd /Users/sgl/PycharmProjects/AIchanyejiqun/Service_WaterManage/backend

# 清理 Python 字节码缓存
find . -type d -name "__pycache__" -exec rm -rf {} +
find . -name "*.pyc" -delete

# 清理 PyCharm 缓存 (可选)
rm -rf .idea/caches
```

---

### 步骤 4: 重新启动后端服务

#### 方式 A: PyCharm (推荐)

1. 右键点击 `main.py`
2. 选择 **Run 'main'**
3. 观察控制台输出

**预期启动日志**:
```
INFO:     Started server process [PID]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

#### 方式 B: 命令行

```bash
cd /Users/sgl/PycharmProjects/AIchanyejiqun/Service_WaterManage/backend
python main.py
```

---

### 步骤 5: 验证后端服务正常

#### 测试 1: 健康检查
```bash
curl http://localhost:8000/api/health
```

**预期返回**:
```json
{
  "status": "ok",
  "timestamp": "2026-03-24T..."
}
```

#### 测试 2: Swagger UI
打开浏览器访问：http://localhost:8000/docs

**验证要点**:
- ✅ 页面正常加载
- ✅ 看到 **"unified-account"** 分组
- ✅ 所有 API 端点都显示出来

#### 测试 3: 直接测试 API
在 Swagger UI 中:
1. 找到 `GET /api/unified/user/{user_id}/balance`
2. 点击 "Try it out"
3. 输入 `user_id: 1`
4. 点击 "Execute"
5. 应该返回 JSON 数据，不是 500 错误

---

### 步骤 6: 刷新前端页面

1. **清除浏览器缓存**:
   - Chrome/Edge: `Ctrl+Shift+Delete` (Windows) 或 `Cmd+Shift+Delete` (Mac)
   - 勾选"缓存的图片和文件"
   - 点击"清除数据"

2. **强制刷新页面**:
   - 打开统一账户管理页面
   - 按 `Ctrl+Shift+R` (Windows) 或 `Cmd+Shift+R` (Mac)

3. **验证功能**:
   - ✅ 页面正常加载，无报错
   - ✅ 用户列表显示余额信息
   - ✅ 可以点击"充值/授信"按钮
   - ✅ 可以查看财务报表

---

## 🔍 故障排查

### 问题 1: 后端启动失败

**错误**: `ImportError`, `ModuleNotFoundError`

**解决**:
```bash
cd /Users/sgl/PycharmProjects/AIchanyejiqun/Service_WaterManage/backend
pip install -r requirements.txt
```

### 问题 2: 端口被占用

**错误**: `Address already in use: port 8000`

**解决**:
```bash
# macOS/Linux
lsof -i :8000
kill -9 <PID>

# Windows
netstat -ano | findstr :8000
taskkill /F /PID <PID>
```

### 问题 3: 数据库迁移失败

**错误**: `duplicate column name: paid_qty`

**解决**: 字段已存在，可以直接跳过或忽略此错误。

### 问题 4: CORS 仍然报错

**检查**:
1. 确认后端已启动 CORS 中间件
2. 确认前端请求的 URL 是 `http://localhost:8000`
3. 尝试清除浏览器缓存并重启浏览器

---

## 📊 关键检查清单

在刷新前端页面之前，请确认:

- [ ] ✅ 已执行数据库迁移脚本 (`python migrate_add_fields.py`)
- [ ] ✅ 已完全停止后端服务 (等待 3-5 秒)
- [ ] ✅ 已清理 Python 缓存 (`__pycache__` 目录)
- [ ] ✅ 已重启后端服务
- [ ] ✅ 后端启动成功 (看到 "Uvicorn running" 消息)
- [ ] ✅ 测试健康检查 API 返回正常
- [ ] ✅ Swagger UI 能正常访问

---

## 🎯 技术说明

### 为什么会出现 500 错误？

1. **JWT 验证失败**: 之前的代码使用 `jwt.InvalidTokenError`,但这个类不存在
2. **数据库字段缺失**: `account_wallet` 表缺少 `paid_qty` 字段
3. **缓存问题**: Python 使用了旧的字节码文件

### CORS 错误的真相

CORS 错误通常是**结果**而不是**原因**:
- 当后端返回 500 错误时，响应头中没有 CORS 相关的 header
- 浏览器看到没有 `Access-Control-Allow-Origin` header,就报 CORS 错误
- **真正的問題是后端返回了 500 错误**

### 正确的启动顺序

```
1. 执行数据库迁移
   ↓
2. 停止旧的后端服务
   ↓
3. 清理缓存
   ↓
4. 启动新的后端服务
   ↓
5. 验证后端正常
   ↓
6. 最后刷新前端页面
```

---

## ⚠️ 常见错误操作

### ❌ 错误 1: 不执行数据库迁移就直接重启
**结果**: 仍然报 `no such column: paid_qty` 错误

### ❌ 错误 2: 不清理缓存就重启
**结果**: Python 继续使用旧的字节码，修复不生效

### ❌ 错误 3: 后端还没启动好就刷新前端
**结果**: 前端请求失败，报网络错误

### ❌ 错误 4: 只刷新前端页面
**结果**: 问题依旧，因为问题在后端

---

## 📞 如需进一步帮助

如果按照以上步骤操作后仍有问题，请提供:

1. **后端启动日志**: 完整的控制台输出 (从启动到报错的全部内容)
2. **数据库迁移输出**: `python migrate_add_fields.py` 的完整输出
3. **Swagger UI 测试结果**: 访问 http://localhost:8000/docs 的截图
4. **浏览器控制台错误**: 完整的错误信息和网络请求详情

---

**文档创建时间**: 2026-03-24  
**适用场景**: 统一账户页面刷新后出现大量 500 错误  
**核心要点**: 先修复后端 → 再刷新前端
