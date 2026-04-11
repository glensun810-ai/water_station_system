# API 路径规范文档

## 问题根因分析

### 问题描述
用户管理页面 `portal/admin/users.html` 出现 404 错误：
- `GET http://127.0.0.1:8008/api/v1/users` 404 Not Found
- `GET http://127.0.0.1:8008/api/v1/users/stats/overview` 404 Not Found

### 根本原因
架构重构后，API 路径发生了变化，但前端页面未同步更新：

**旧架构（Service_WaterManage/backend/）：**
```python
# api_user_management.py
router = APIRouter(prefix="/api/users")
# 路由路径：/api/users, /api/users/stats/overview
```

**新架构（apps/api/v1/）：**
```python
# system.py
router = APIRouter(prefix="/system")  # + v1_router.prefix="/api/v1"
# 路由路径：/api/v1/system/users, /api/v1/system/users/stats/overview（需添加）
```

**前端调用（未更新）：**
```javascript
// portal/admin/users.html
fetch(`${API_BASE}/users`)  // 错误：尝试访问 /api/v1/users
```

## API 路径设计规范

### 1. 统一 API 基础路径
所有 API 必须遵循统一的版本化路径：
- **基础路径**: `/api/v1`
- **服务前缀**: 根据模块功能添加适当的前缀

### 2. 服务模块路由前缀规范

| 模块 | Router Prefix | API 路径示例 | 说明 |
|------|--------------|-------------|------|
| **系统服务** | `/system` | `/api/v1/system/users` | 用户、认证、办公室管理 |
| **水站服务** | `/water` | `/api/v1/water/products` | 水站产品、领水记录 |
| **会议室服务** | `/meeting` | `/api/v1/meeting/rooms` | 会议室、预约管理 |
| **产品管理** | `/products` | `/api/v1/products` | 产品列表 |
| **办公室管理** | `/offices` | `/api/v1/offices` | 办公室详细信息（独立路由） |

**注意**: `system` 模块包含基础的系统管理功能（用户、认证），而 `offices` 模块提供更详细的办公室管理功能。两个模块有部分重叠，但各有侧重。

### 3. 前端 API 配置规范

#### 必须使用统一配置文件
所有前端页面必须引入并使用 `/shared/utils/api-config.js`：

```html
<script src="/shared/utils/api-config.js"></script>
```

#### 使用 buildApiUrl 函数
不要直接拼接 API 路径，使用统一的工具函数：

```javascript
// ❌ 错误方式
const API_BASE = `${window.location.protocol}//${window.location.hostname}:${window.location.port}/api/v1`;
fetch(`${API_BASE}/users`);

// ✅ 正确方式
fetch(window.buildApiUrl('/system/users'));
fetch(window.buildApiUrl('/system/users/stats/overview'));
```

#### 使用 API_CONFIG 常量
对于常用的 API 路径，使用预定义的常量：

```javascript
// ✅ 使用预定义常量
fetch(window.buildApiUrl(window.API_CONFIG.SYSTEM.USERS));
fetch(window.buildApiUrl(window.API_CONFIG.WATER.PRODUCTS));
fetch(window.buildApiUrl(window.API_CONFIG.MEETING.ROOMS));
```

### 4. Router 注册顺序规范

在 `apps/main.py` 中，router 注册顺序很重要：

```python
# 正确的注册顺序（避免路由冲突）
v1_router.include_router(system_router, tags=["系统服务"])
v1_router.include_router(water_router, tags=["水站服务"])
v1_router.include_router(meeting_router, tags=["会议室服务"])
v1_router.include_router(products_router, tags=["产品管理"])
v1_router.include_router(offices_router, tags=["办公室管理"])
```

**原则**: 
- 基础服务（system）优先注册
- 特定服务后注册
- 避免路由重叠导致的冲突

### 5. API 路径迁移检查清单

当进行架构重构或 API 迁移时，必须完成以下检查：

#### 后端检查：
- [ ] 确认所有 router 的 prefix 正确设置
- [ ] 确认所有路由端点（@router.get/post/put/delete）路径正确
- [ ] 确认路由注册顺序正确（在 main.py 中）
- [ ] 确认没有遗漏关键路由（对比旧架构）
- [ ] 测试所有 API 端点可访问

#### 前端检查：
- [ ] 引入 `/shared/utils/api-config.js`
- [ ] 移除自定义的 `const API_BASE = ...` 定义
- [ ] 使用 `window.buildApiUrl()` 替代所有字符串拼接
- [ ] 更新 API_CONFIG 常量（如有新模块）
- [ ] 测试所有 API 调用正常工作

#### 文档检查：
- [ ] 更新 API 路径规范文档
- [ ] 更新 API_CONFIG 配置文件注释
- [ ] 记录路由变更历史

### 6. 常见错误与解决方案

#### 错误 1: 404 Not Found
**原因**: API 路径不匹配
**解决**: 
1. 检查 router prefix 是否正确
2. 使用 buildApiUrl 构建 API 路径
3. 查看 API 文档（/docs）确认实际路径

#### 错误 2: 路由冲突
**原因**: 两个 router 定义了相同路径
**解决**:
1. 检查 router 注册顺序
2. 避免在不同模块中定义完全相同的路径
3. 使用不同的 prefix 区分

#### 错误 3: API_BASE 未定义
**原因**: 未引入 api-config.js
**解决**: 在 HTML head 中添加：
```html
<script src="/shared/utils/api-config.js"></script>
```

### 7. 路由路径命名规范

#### RESTful 风格：
```
GET    /system/users              # 获取用户列表
GET    /system/users/{id}         # 获取单个用户
POST   /system/users              # 创建用户
PUT    /system/users/{id}         # 更新用户
DELETE /system/users/{id}         # 删除用户

GET    /system/users/stats/overview  # 用户统计（特殊端点）
POST   /system/users/batch           # 批量操作
```

#### 嵌套资源：
```
GET    /offices/{office_id}/users     # 获取办公室的用户
GET    /meeting/rooms/{room_id}/bookings  # 获取会议室的预约
```

### 8. 验证与测试

#### 后端验证：
```bash
# 查看所有注册的路由
python3 -c "from apps.main import app; print([r.path for r in app.routes])"

# 查看 router 的路由
python3 -c "from apps.api.v1.system import router; print([r.path for r in router.routes])"

# 测试 API 端点
curl http://127.0.0.1:8008/api/v1/system/users
curl http://127.0.0.1:8008/api/v1/system/users/stats/overview
```

#### 前端验证：
```javascript
// 在浏览器 console 中测试
console.log(window.API_CONFIG.BASE_URL);
console.log(window.buildApiUrl('/system/users'));
fetch(window.buildApiUrl('/system/users/stats/overview')).then(r => r.json()).then(console.log);
```

## 本次修复记录

### 已修复问题：
1. **users.html**: 
   - 引入 `/shared/utils/api-config.js`
   - 移除自定义 API_BASE 定义
   - 使用 buildApiUrl('/system/users') 替代所有 API 调用
   - API 调用路径：`/api/v1/users` → `/api/v1/system/users`

2. **system.py**: 
   - 添加缺失的 `/users/stats/overview` 路由
   - 添加缺失的 `POST /users`（创建用户）路由
   - 添加缺失的 `/users/batch`（批量更新）路由
   - 添加缺失的 `/users/batch-delete`（批量删除）路由

### 其他页面检查：
- **offices.html**: 使用 `/api/v1/offices`，路由正确（对应 offices.py）
- **其他页面**: 大部分使用自定义 API_BASE，建议逐步迁移到 buildApiUrl

### 后续建议：
1. 逐步迁移所有页面使用统一的 api-config.js
2. 在 CI/CD 中添加 API 路径一致性检查
3. 定期审查 API_CONFIG 配置文件的完整性
4. 新页面开发时强制使用统一配置

## 附录：API_CONFIG 配置文件

`/shared/utils/api-config.js` 内容：

```javascript
const API_CONFIG = {
    BASE_URL: window.location.origin + '/api/v1',
    
    WATER: {
        PRODUCTS: '/water/products',
        BALANCE: '/water/balance',
        PICKUPS: '/water/pickups',
        SETTLEMENTS: '/water/settlements',
        TRANSACTIONS: '/water/transactions'
    },
    
    MEETING: {
        ROOMS: '/meeting/rooms',
        BOOKINGS: '/meeting/bookings',
        APPROVALS: '/meeting/approvals'
    },
    
    SYSTEM: {
        USERS: '/system/users',
        OFFICES: '/system/offices',
        AUTH: '/system/auth'
    }
};

function buildApiUrl(endpoint) {
    return API_CONFIG.BASE_URL + endpoint;
}

window.API_CONFIG = API_CONFIG;
window.buildApiUrl = buildApiUrl;
```

---
**文档版本**: v1.0  
**创建日期**: 2026-04-11  
**适用项目**: AI产业集群空间服务系统  
**维护责任**: 后端开发团队