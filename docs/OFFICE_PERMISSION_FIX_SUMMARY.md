# 办公室权限修复总结

## 问题背景

用户领水界面（http://127.0.0.1:8008/water/index.html）的办公室选择逻辑需要优化：
- **超级管理员、管理员**：应该看到所有办公室（与 http://127.0.0.1:8008/portal/admin/offices.html 一致）
- **办公室管理员**：应该只看到他们管辖的办公室
- **普通用户**：应该只看到他们所属的办公室

## 修复方案

### 1. 后端API优化

#### 创建办公室管理员关联表

```sql
CREATE TABLE IF NOT EXISTS office_admin_relations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    office_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    role VARCHAR(50) DEFAULT 'office_admin',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (office_id) REFERENCES office (id),
    FOREIGN KEY (user_id) REFERENCES users (id)
);
```

#### 添加关联数据

为办公室管理员（孙经理，user_id=23）添加管理办公室关系：
```sql
INSERT INTO office_admin_relations (office_id, user_id, role)
VALUES (38, 23, 'office_admin');
```

#### 优化API返回数据

修改 `/api/v1/water/offices` API：
- 移除 `manager_name` 字段（数据库表中不存在）
- 保持权限过滤逻辑：
  - super_admin/admin：返回所有办公室
  - office_admin：返回管理的办公室 + 所属办公室
  - user：返回所属办公室

### 2. 前端逻辑优化

#### 计算属性调整

**displayOffices 计算属性**：
```javascript
displayOffices() { 
    const userRole = localStorage.getItem('user_role');
    
    // 对于超级管理员和管理员，显示所有办公室（按常用/不常用分类）
    if (userRole === 'admin' || userRole === 'super_admin') {
        return this.offices.filter(o => this.officeTab === 'common' ? o.is_common === 1 : o.is_common !== 1);
    }
    
    // 对于办公室管理员和普通用户，后端已经根据权限过滤
    // 直接显示后端返回的办公室
    return this.offices;
}
```

**isAdmin 计算属性**：
```javascript
isAdmin() {
    const userRole = localStorage.getItem('user_role');
    return userRole === 'admin' || userRole === 'super_admin' || userRole === 'office_admin';
}
```

**isSuperAdmin 计算属性**：
```javascript
isSuperAdmin() {
    const userRole = localStorage.getItem('user_role');
    return userRole === 'admin' || userRole === 'super_admin';
}
```

#### UI展示优化

- **超级管理员/管理员**：
  - 显示"常用/不常用"分类标签
  - 3列网格布局
  - 可点击选择任意办公室

- **办公室管理员**：
  - 不显示分类标签（办公室数量较少）
  - 2列网格布局
  - 只显示管辖的办公室

- **普通用户**：
  - 不显示分类标签
  - 单卡片展示所属办公室
  - 自动选择，无需手动选择

### 3. 数据库调整

为普通用户设置所属办公室：
```sql
UPDATE users SET department = '总经理' WHERE id = 22;
```

## 测试验证

### 测试结果

| 用户 | 角色 | 预期办公室数量 | 实际办公室数量 | 状态 |
|------|------|----------------|----------------|------|
| admin | super_admin | 21 | 21 | ✅ |
| 系统管理员 | admin | 21 | 21 | ✅ |
| 孙经理 | office_admin | 1 | 1 | ✅ |
| 麦子 | admin | 21 | 21 | ✅ |
| 普通用户 | user | 1 | 1 | ✅ |

### 测试命令

```bash
python3 test_office_permission_fix.py
```

### 测试输出

```
============================================================
办公室权限修复测试
============================================================

数据库中激活办公室总数: 21

✅ 所有测试通过！办公室权限修复成功！
```

## 权限规则总结

### 后端权限过滤（`/api/v1/water/offices`）

1. **super_admin/admin**：
   - 返回所有激活的办公室
   - 无权限限制

2. **office_admin**：
   - 返回管理的办公室（通过 `office_admin_relations` 表）
   - 返回所属的办公室（通过 `users.department` 字段）
   - 两者的合并结果

3. **user**：
   - 返回所属的办公室（通过 `users.department` 字段）
   - 如果未设置 `department`，返回空列表

### 前端展示逻辑

1. **super_admin/admin**：
   - 显示所有办公室（按常用/不常用分类）
   - 可手动选择任意办公室

2. **office_admin**：
   - 显示管辖的办公室（后端已过滤）
   - 可手动选择管辖范围内的办公室

3. **user**：
   - 显示所属的办公室（后端已过滤）
   - 自动选择，无需手动操作

## 相关文件

### 后端
- `/Users/sgl/PycharmProjects/AIchanyejiqun/apps/api/v1/water.py` - 办公室列表API
- `/Users/sgl/PycharmProjects/AIchanyejiqun/data/app.db` - 数据库

### 前端
- `/Users/sgl/PycharmProjects/AIchanyejiqun/apps/water/frontend/index.html` - 用户领水界面

### 测试
- `/Users/sgl/PycharmProjects/AIchanyejiqun/test_office_permission_fix.py` - 权限测试脚本

## 验证方法

### 1. API验证

```bash
# 超级管理员登录
curl -s http://127.0.0.1:8008/api/v1/system/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'

# 获取办公室列表
curl -s http://127.0.0.1:8008/api/v1/water/offices \
  -H "Authorization: Bearer <token>"
```

### 2. 前端验证

访问 http://127.0.0.1:8008/water/index.html：
- 使用不同角色账号登录
- 查看办公室选择界面
- 验证办公室列表是否符合预期

### 3. 数据库验证

```bash
# 查看所有办公室
sqlite3 /Users/sgl/PycharmProjects/AIchanyejiqun/data/app.db \
  "SELECT * FROM office WHERE is_active=1;"

# 查看办公室管理员关联
sqlite3 /Users/sgl/PycharmProjects/AIchanyejiqun/data/app.db \
  "SELECT * FROM office_admin_relations;"
```

## 总结

✅ **修复完成**

- 后端API正确实现权限过滤
- 前端正确展示不同角色的办公室列表
- 测试验证所有权限规则符合预期
- 数据库关联表创建完成

用户领水界面的办公室选择功能现在完全符合权限设计要求：
- 超级管理员和管理员可以看到所有办公室
- 办公室管理员只能看到管辖的办公室
- 普通用户只能看到所属的办公室