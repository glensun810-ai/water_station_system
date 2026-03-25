# 统一账户页面刷新报错修复指南

## 🔴 问题症状

在统一账户管理页面刷新后，出现大量错误堆栈:

### 错误 1: JWT 验证异常处理错误
```
AttributeError: module 'jose.jwt' has no attribute 'InvalidTokenError'
```

**原因**: `python-jose` 库的异常类层次结构变化，`jwt.InvalidTokenError` 不存在。

### 错误 2: 数据库字段缺失
```
sqlite3.OperationalError: no such column: account_wallet.paid_qty
```

**原因**: `account_wallet` 表缺少 `paid_qty` 和 `free_qty` 字段。

---

## ✅ 修复方案

### 修复 1: JWT 异常处理

#### 文件：`backend/main.py` (Line 65-76)

**修改前**:
```python
def verify_token(token: str) -> Optional[dict]:
    """验证 JWT Token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError as e:
        import logging
        logging.error(f"Token verification failed: {str(e)}")
        return None
```

**修改后**:
```python
def verify_token(token: str) -> Optional[dict]:
    """验证 JWT Token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except Exception as e:
        # 捕获所有 JWT 验证异常 (包括 ExpiredSignatureError, JWSError 等)
        import logging
        logging.error(f"Token verification failed: {str(e)}")
        return None
```

**说明**: 使用通用的 `Exception` 捕获所有 JWT 相关异常，避免特定异常类不存在的问题。

---

### 修复 2: 数据库字段迁移

#### 方式 A: 使用迁移脚本 (推荐)

1. **执行迁移脚本**:
   ```bash
   cd /Users/sgl/PycharmProjects/AIchanyejiqun/Service_WaterManage/backend
   python migrate_add_fields.py
   ```

2. **预期输出**:
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

#### 方式 B: 手动执行 SQL

如果不想使用脚本，可以直接执行 SQL:

```sql
-- 添加 paid_qty 字段
ALTER TABLE account_wallet ADD COLUMN paid_qty INTEGER DEFAULT 0;

-- 添加 free_qty 字段
ALTER TABLE account_wallet ADD COLUMN free_qty INTEGER DEFAULT 0;
```

---

## 🚀 重启后端服务

### 步骤 1: 停止当前服务

在 PyCharm 中:
- 找到运行控制台 (Run 窗口)
- 点击**红色停止按钮** ⏹️
- 等待进程完全退出

### 步骤 2: 清理 Python 缓存

```bash
cd /Users/sgl/PycharmProjects/AIchanyejiqun/Service_WaterManage/backend
find . -type d -name "__pycache__" -exec rm -rf {} +
find . -name "*.pyc" -delete
```

### 步骤 3: 重新启动服务

**方式 A: PyCharm**
- 右键点击 `main.py`
- 选择 **Run 'main'**
- 观察控制台输出

**方式 B: 命令行**
```bash
cd /Users/sgl/PycharmProjects/AIchanyejiqun/Service_WaterManage/backend
python main.py
```

---

## ✅ 验证启动成功

### 预期输出
```
INFO:     Started server process [PID]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### 测试步骤

1. **访问统一账户管理页面**
   ```
   http://localhost:63342/Service_WaterManage/frontend/admin-unified.html
   ```

2. **刷新页面**
   - 按 `Ctrl+Shift+R` (Windows) 或 `Cmd+Shift+R` (Mac)
   - 强制刷新浏览器缓存

3. **验证功能**
   - ✅ 页面正常加载，无报错
   - ✅ 用户列表显示余额信息
   - ✅ 可以点击"充值/授信"按钮
   - ✅ 可以查看财务报表

---

## 🎯 技术要点

### JWT 异常处理

`python-jose` 库的异常类层次:
```
JWSError
├── JWSSignatureError
│   └── JWSSignatureError
└── JWTError
    └── JWTClaimsError
```

**最佳实践**: 直接捕获 `Exception`,因为:
1. 不同版本的 `python-jose` 异常类可能不同
2. 我们只关心验证是否失败，不关心具体失败原因
3. 简化代码逻辑

### 数据库字段迁移

**为什么需要迁移？**
1. 模型代码 (`models_unified.py`) 添加了新字段
2. 但 SQLite 数据库不会自动更新表结构
3. 需要使用 `ALTER TABLE` 手动添加字段

**SQLite ALTER TABLE 限制**:
- ✅ 可以添加新列
- ❌ 不能删除列 (SQLite 3.35.0+)
- ❌ 不能重命名列 (SQLite 3.25.0+)

---

## 📊 修复统计

- **修改文件**: 2 个
  - `main.py`: 修改 JWT 异常处理
  - `migrate_add_fields.py`: 新建数据库迁移脚本
- **修改行数**: 约 10 行
- **数据库变更**: 添加 2 个字段 (`paid_qty`, `free_qty`)
- **影响范围**: 统一账户管理模块

---

## ⚠️ 重要提醒

### 必须执行的步骤

1. **必须先执行数据库迁移**
   ```bash
   python migrate_add_fields.py
   ```
   
2. **然后重启后端服务**
   - 停止 → 清理缓存 → 重启

3. **最后刷新前端页面**
   - 强制刷新 (`Ctrl+Shift+R`)

### 数据备份建议

在执行数据库迁移前，建议先备份:

```bash
cd /Users/sgl/PycharmProjects/AIchanyejiqun/Service_WaterManage/backend
cp waterms.db waterms_backup_$(date +%Y%m%d_%H%M%S).db
```

---

## 📞 如需进一步帮助

如果按照以上步骤操作后仍有问题，请提供:

1. **后端启动日志**: 完整的控制台输出
2. **数据库迁移输出**: `python migrate_add_fields.py` 的输出
3. **浏览器控制台错误**: 完整的错误信息

---

**修复完成时间**: 2026-03-24  
**状态**: ✅ 代码已修复，等待执行迁移和重启  
**下一步**: 
1. 执行数据库迁移脚本
2. 重启后端服务
3. 刷新前端页面测试
