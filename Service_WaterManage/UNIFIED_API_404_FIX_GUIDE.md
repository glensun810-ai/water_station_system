# 统一账户模块 404 错误 - 完整修复指南

## 🔴 问题症状

所有 `/api/unified/*` 路径都返回 404 Not Found:
- ❌ `GET /api/unified/user/{id}/balance` → 404
- ❌ `POST /api/unified/wallet/balance` → 404  
- ❌ `GET /api/unified/promotion-config/{id}` → 404
- ❌ `GET /api/auth/me` → CORS 错误 + Failed to load

---

## ✅ 根本原因

**后端服务未重启**,导致新注册的路由器未生效。

虽然代码已经修复:
1. ✅ 已导入路由器：`from api_unified import router as unified_router`
2. ✅ 已注册路由：`app.include_router(unified_router)`

但是**运行中的后端服务仍然使用旧版本的代码**,没有加载新的路由配置。

---

## 🛠️ 完整修复步骤

### 步骤 1: 确认代码已修改

检查 `main.py` 文件包含以下内容:

#### 1.1 导入语句 (Line 17-18)
```python
# 导入统一账户管理模块的路由
from api_unified import router as unified_router
```

#### 1.2 路由注册 (Line 507-508)
```python
# 注册统一账户管理模块的路由
app.include_router(unified_router)
```

### 步骤 2: 完全停止后端服务

#### PyCharm 中操作:
1. 找到运行控制台 (Run 窗口)
2. 点击 **红色停止按钮** ⏹️
3. 等待进程完全退出

#### 或者使用命令行:
```bash
# macOS/Linux
ps aux | grep "uvicorn|python.*main"
kill -9 <PID>

# Windows
taskkill /F /IM python.exe
```

### 步骤 3: 清理 Python 缓存

删除 `__pycache__` 目录，确保重新编译:

```bash
cd /Users/sgl/PycharmProjects/AIchanyejiqun/Service_WaterManage/backend

# macOS/Linux
find . -type d -name "__pycache__" -exec rm -rf {} +
find . -name "*.pyc" -delete

# Windows (PowerShell)
Get-ChildItem -Recurse -Directory -Filter __pycache__ | Remove-Item -Recurse -Force
Get-ChildItem -Recurse -Filter *.pyc | Remove-Item -Force
```

### 步骤 4: 重启后端服务

#### 方式 A: PyCharm 启动
1. 右键点击 `main.py`
2. 选择 **Run 'main'** 或按 `Shift+F10`
3. 观察控制台输出，确保无错误

#### 方式 B: 命令行启动
```bash
cd /Users/sgl/PycharmProjects/AIchanyejiqun/Service_WaterManage/backend
python main.py
```

#### 预期启动日志:
```
INFO:     Started server process [PID]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### 步骤 5: 验证路由已注册

#### 方式 1: 访问 Swagger UI
打开浏览器访问：http://localhost:8000/docs

查找 **"unified-account"** 分组，应该看到以下 API:
- `GET /api/unified/account/{user_id}`
- `POST /api/unified/wallet/balance`
- `GET /api/unified/user/{user_id}/balance`
- `GET /api/unified/promotion-config/{product_id}`
- ...等等

#### 方式 2: 测试健康检查
```bash
curl http://localhost:8000/api/health
```

预期返回:
```json
{"status": "ok", "timestamp": "2026-03-24T..."}
```

#### 方式 3: 测试统一账户 API
```bash
# 获取用户余额
curl http://localhost:8000/api/unified/user/1/balance

# 获取优惠配置
curl http://localhost:8000/api/unified/promotion-config/1
```

### 步骤 6: 刷新前端页面

1. 在浏览器中打开 `admin-unified.html`
2. 按 `Ctrl+Shift+R` (Windows) 或 `Cmd+Shift+R` (Mac) **强制刷新**
3. 清除浏览器缓存 (可选)

---

## 🔍 故障排查

### 问题 1: 服务启动失败

**错误**: `ModuleNotFoundError: No module named 'xxx'`

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

### 问题 3: CORS 错误仍然存在

**错误**: `Access to fetch at '...' from origin '...' has been blocked by CORS policy`

**检查**: 
1. 确认后端已添加 CORS 中间件 (已在 main.py Line 499-505)
2. 确认前端请求的 URL 正确
3. 重启浏览器

### 问题 4: 某些 API 仍返回 404

**可能原因**: 
1. 路由器前缀不匹配
2. 路由路径拼写错误
3. HTTP 方法不正确

**检查清单**:
```python
# api_unified.py Line 22
router = APIRouter(prefix="/api/unified", tags=["unified-account"])

# 例如:
@router.get("/user/{user_id}/balance")  # → GET /api/unified/user/{user_id}/balance
@router.post("/wallet/balance")         # → POST /api/unified/wallet/balance
```

---

## 📊 验证测试

### 测试 1: 充值功能

1. 登录统一账户管理页面
2. 选择一个用户
3. 点击"充值/授信"
4. 填写表单:
   - 类型：预付
   - 产品：选择任一产品
   - 数量：10
5. 点击"确认充值"

**预期结果**:
```json
{
  "message": "预付充值成功：付费 10 个，赠送 1 个，共 11 个",
  "wallet": {
    "id": 1,
    "product_id": 1,
    "wallet_type": "prepaid",
    "paid_qty": 10,
    "free_qty": 1,
    "available_qty": 11,
    "total_amount": 100.0
  }
}
```

### 测试 2: 查询余额

刷新页面后，查看用户列表中的余额列:
- ✅ 付费桶：显示绿色数字
- ✅ 赠送桶：显示橙色数字
- ✅ 信用余额：显示蓝色数字

### 测试 3: 领取功能

1. 选择一个有余额的用户
2. 在操作栏点击"领取"
3. 输入领取数量
4. 提交

**预期结果**: 扣减成功，记录领用明细

---

## 🎯 关键要点总结

### ✅ 必须执行的操作
1. **完全停止**后端服务 (不只是刷新页面)
2. **清理缓存** (`__pycache__` 目录)
3. **重新启动**后端服务
4. **强制刷新**浏览器页面

### ❌ 常见错误
- 只刷新前端页面，不重启后端
- 服务仍在后台运行，没有真正停止
- Python 缓存未清理，使用旧的字节码
- 浏览器缓存未清除

---

## 📞 如需进一步帮助

如果按照以上步骤操作后仍有问题，请提供:

1. **后端启动日志**: 完整的控制台输出
2. **Swagger UI 截图**: 查看是否有 unified 分组
3. **浏览器控制台错误**: 完整的错误信息
4. **网络请求详情**: Request URL、Method、Status Code

---

**修复完成时间**: 2026-03-24  
**关键**: 一定要重启后端服务！🔄
