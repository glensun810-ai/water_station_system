"""
API v2 使用指南
Enterprise Service Platform - API v2 Documentation
"""

# API v2 使用指南

## 概述

API v2 是企业服务平台的全新API架构，采用现代化的分层设计：
- **清晰的分层架构**：API → Service → Repository → Model
- **统一的错误处理**：标准化的错误响应格式
- **完善的类型注解**：更好的IDE支持和类型安全
- **RESTful设计**：符合REST规范的API设计

## 基础信息

### Base URL
```
http://localhost:8000/v2
```

### 认证方式
使用JWT Bearer Token认证：
```
Authorization: Bearer <your_token>
```

### 通用响应格式

**成功响应：**
```json
{
  "id": 1,
  "name": "示例",
  "created_at": "2026-04-02T10:00:00"
}
```

**错误响应：**
```json
{
  "detail": "错误描述"
}
```

## 认证接口

### 登录
```
POST /v2/auth/login
```

**请求体：**
```json
{
  "name": "用户名",
  "password": "密码"
}
```

**响应：**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 86400,
  "user_id": 1,
  "user_name": "admin",
  "role": "admin"
}
```

### 修改密码
```
POST /v2/auth/change-password
```

**请求头：**
```
Authorization: Bearer <token>
```

**请求体：**
```json
{
  "old_password": "旧密码",
  "new_password": "新密码"
}
```

## 用户接口

### 获取用户列表
```
GET /v2/users?skip=0&limit=100
```

**权限：** 管理员

**响应：**
```json
[
  {
    "id": 1,
    "name": "用户1",
    "department": "技术部",
    "role": "staff",
    "balance_credit": 100.0,
    "is_active": 1,
    "created_at": "2026-04-02T10:00:00"
  }
]
```

### 获取单个用户
```
GET /v2/users/{user_id}
```

**权限：** 管理员或用户本人

### 创建用户
```
POST /v2/users
```

**权限：** 管理员

**请求体：**
```json
{
  "name": "新用户",
  "department": "技术部",
  "role": "staff",
  "password": "初始密码"
}
```

### 更新用户
```
PUT /v2/users/{user_id}
```

**权限：** 管理员

**请求体：**
```json
{
  "department": "新部门",
  "role": "admin"
}
```

### 删除用户
```
DELETE /v2/users/{user_id}
```

**权限：** 管理员

### 停用/激活用户
```
POST /v2/users/{user_id}/deactivate
POST /v2/users/{user_id}/activate
```

**权限：** 管理员

### 重置密码
```
POST /v2/users/{user_id}/reset-password?new_password=新密码
```

**权限：** 管理员

## 产品接口

### 获取产品列表
```
GET /v2/products?skip=0&limit=100
```

**权限：** 无需认证

**响应：**
```json
[
  {
    "id": 1,
    "name": "矿泉水",
    "category_id": 1,
    "price": 100.0,
    "service_type": "water",
    "stock": 50,
    "is_active": 1,
    "created_at": "2026-04-02T10:00:00"
  }
]
```

### 根据分类获取产品
```
GET /v2/products/category/{category_id}
```

### 根据服务类型获取产品
```
GET /v2/products/service-type/{service_type}
```

**service_type 可选值：**
- `water` - 水站
- `dining` - 餐饮
- `meeting` - 会议室

### 搜索产品
```
GET /v2/products/search?keyword=关键词
```

### 获取单个产品
```
GET /v2/products/{product_id}
```

### 创建产品
```
POST /v2/products
```

**权限：** 管理员

**请求体：**
```json
{
  "name": "新产品",
  "category_id": 1,
  "price": 100.0,
  "service_type": "water",
  "description": "产品描述",
  "unit": "桶",
  "stock": 0
}
```

### 更新产品
```
PUT /v2/products/{product_id}
```

**权限：** 管理员

### 删除产品
```
DELETE /v2/products/{product_id}
```

**权限：** 管理员

### 更新库存
```
PUT /v2/products/{product_id}/stock?quantity=100
```

**权限：** 管理员

### 分类接口

**获取所有分类：**
```
GET /v2/products/categories
```

**获取单个分类：**
```
GET /v2/products/categories/{category_id}
```

**创建分类：**
```
POST /v2/products/categories?name=分类名&service_type=water
```

## 交易接口

### 获取交易列表
```
GET /v2/transactions?skip=0&limit=100
```

**权限：** 管理员

### 获取未结算交易
```
GET /v2/transactions/unsettled
```

**权限：** 管理员

### 获取已结算交易
```
GET /v2/transactions/settled
```

**权限：** 管理员

### 获取用户交易
```
GET /v2/transactions/user/{user_id}
```

**权限：** 管理员或用户本人

### 创建交易
```
POST /v2/transactions
```

**请求体：**
```json
{
  "user_id": 1,
  "product_id": 1,
  "quantity": 2,
  "actual_price": 200.0,
  "type": "pickup",
  "note": "备注"
}
```

**type 可选值：**
- `pickup` - 取货
- `reserve` - 预约

### 更新交易
```
PUT /v2/transactions/{transaction_id}
```

**权限：** 管理员

### 删除交易
```
DELETE /v2/transactions/{transaction_id}?delete_reason=原因
```

**权限：** 已认证用户

### 申请结算
```
POST /v2/transactions/{transaction_id}/apply-settlement
```

**权限：** 已认证用户

### 结算交易
```
POST /v2/transactions/{transaction_id}/settle
```

**权限：** 管理员

### 批量结算
```
POST /v2/transactions/batch-settle
```

**权限：** 管理员

**请求体：**
```json
{
  "transaction_ids": [1, 2, 3]
}
```

**响应：**
```json
{
  "success_count": 2,
  "failed_count": 1,
  "failed_details": [
    {
      "transaction_id": 3,
      "reason": "余额不足"
    }
  ]
}
```

## 状态码说明

- `200` - 成功
- `201` - 创建成功
- `204` - 删除成功（无返回内容）
- `400` - 请求参数错误
- `401` - 未认证
- `403` - 无权限
- `404` - 资源不存在
- `500` - 服务器错误

## 最佳实践

### 1. 认证Token管理
- Token有效期为24小时
- 建议在Token过期前刷新
- 将Token存储在安全的地方

### 2. 错误处理
- 始终检查响应状态码
- 解析`detail`字段获取错误信息
- 对常见错误进行适当处理

### 3. 分页查询
- 使用`skip`和`limit`参数进行分页
- 默认`limit=100`，最大建议不超过`1000`

### 4. 性能优化
- 使用批量接口减少请求次数
- 合理使用缓存
- 避免在循环中调用API

## 示例代码

### Python (requests)
```python
import requests

BASE_URL = "http://localhost:8000/v2"

# 登录
response = requests.post(f"{BASE_URL}/auth/login", json={
    "name": "admin",
    "password": "admin123"
})
token = response.json()["access_token"]

# 获取用户列表
headers = {"Authorization": f"Bearer {token}"}
response = requests.get(f"{BASE_URL}/users", headers=headers)
users = response.json()
```

### JavaScript (fetch)
```javascript
const BASE_URL = "http://localhost:8000/v2";

// 登录
const loginResponse = await fetch(`${BASE_URL}/auth/login`, {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({name: 'admin', password: 'admin123'})
});
const {access_token} = await loginResponse.json();

// 获取用户列表
const usersResponse = await fetch(`${BASE_URL}/users`, {
  headers: {'Authorization': `Bearer ${access_token}`}
});
const users = await usersResponse.json();
```

## 迁移指南

### 从 /api/ 迁移到 /v2/

**主要变化：**
1. URL前缀从`/api/`改为`/v2/`
2. 认证方式保持不变（JWT Bearer Token）
3. 响应格式更加标准化
4. 错误处理更加统一

**兼容性：**
- 旧的`/api/`接口继续可用
- 建议新功能使用`/v2/`接口
- 可以逐步迁移现有功能

**迁移步骤：**
1. 更新API基础URL
2. 测试新接口功能
3. 逐步替换旧接口调用
4. 移除旧接口依赖

## 技术支持

如有问题，请联系技术团队或查看：
- Swagger文档：http://localhost:8000/docs
- 架构文档：`ARCHITECTURE_PROGRESS_AND_PLAN.md`
- 完成报告：`P2_PHASE2_COMPLETION_REPORT.md`