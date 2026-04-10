# AI产业集群空间服务系统 API 设计规范

**版本：** v1.0  
**最后更新：** 2026年4月9日  
**适用范围：** 所有后端服务API开发

## 1. 基本原则

### 1.1 RESTful 设计原则
- 使用HTTP方法语义：GET（查询）、POST（创建）、PUT（更新）、DELETE（删除）
- 资源命名使用复数名词：`/users`, `/products`, `/offices`
- 路径层级不超过3层：`/api/v1/water/products/{id}`

### 1.2 版本控制
- 所有API必须包含版本号：`/api/v1/...`
- 版本升级策略：向后兼容，v1 → v2 需要完整重写
- 版本支持周期：至少维护2个版本

### 1.3 统一路由结构
```
/api/v1/
├── water/          # 水站服务
├── meeting/        # 会议室服务
├── unified/        # 统一账户服务
└── system/         # 系统管理服务
```

## 2. 请求/响应规范

### 2.1 统一响应格式
```json
{
  "code": 200,
  "data": {},
  "message": "success",
  "timestamp": "2026-04-09T10:00:00Z"
}
```

**字段说明：**
- `code`: HTTP状态码（200成功，4xx用户错误，5xx系统错误）
- `data`: 业务数据（成功时返回，错误时为null）
- `message`: 人类可读的消息（成功时"success"，错误时具体错误信息）
- `timestamp`: ISO8601格式时间戳

### 2.2 错误响应格式
```json
{
  "code": 400,
  "data": null,
  "message": "用户名不能为空",
  "timestamp": "2026-04-09T10:00:00Z",
  "error_id": "VALIDATION_ERROR_001"
}
```

### 2.3 错误码体系
| HTTP状态码 | 错误类型 | 说明 |
|------------|----------|------|
| 400 | BAD_REQUEST | 客户端请求参数错误 |
| 401 | UNAUTHORIZED | 认证失败或未认证 |
| 403 | FORBIDDEN | 权限不足 |
| 404 | NOT_FOUND | 资源不存在 |
| 409 | CONFLICT | 资源冲突（如重复创建） |
| 422 | UNPROCESSABLE_ENTITY | 业务逻辑验证失败 |
| 500 | INTERNAL_SERVER_ERROR | 服务器内部错误 |
| 503 | SERVICE_UNAVAILABLE | 服务暂时不可用 |

## 3. 认证与授权

### 3.1 认证方式
- **Header认证**：`Authorization: Bearer <access_token>`
- **Token获取**：POST `/api/v1/auth/login`
- **Token刷新**：POST `/api/v1/auth/refresh`

### 3.2 权限控制
- **角色体系**：
  - `super_admin`: 超级管理员（系统最高权限）
  - `admin`: 系统管理员（全局管理权限）
  - `office_admin`: 办公室管理员（特定办公室管理权限）
  - `user`: 普通用户（服务使用权限）

- **权限注解**：
  ```python
  # FastAPI权限装饰器示例
  @router.get("/users")
  @require_roles(["super_admin", "admin"])
  async def get_users():
      pass
  
  @router.post("/water/pickup")
  @require_roles(["user", "office_admin", "admin", "super_admin"])
  async def create_pickup():
      pass
  ```

## 4. 数据格式规范

### 4.1 日期时间格式
- **ISO8601标准**：`2026-04-09T10:00:00Z`
- **时区处理**：所有时间存储为UTC，前端根据用户时区显示
- **日期范围**：查询参数使用 `date_from`, `date_to`

### 4.2 数值格式
- **货币金额**：使用decimal类型，保留2位小数
- **整数ID**：使用int类型，从1开始自增
- **百分比**：使用0-100的整数，不使用小数

### 4.3 字符串格式
- **长度限制**：明确指定最大长度
- **字符集**：UTF-8编码，支持中文
- **特殊字符**：输入需进行XSS过滤

## 5. 分页与排序

### 5.1 分页参数
```http
GET /api/v1/users?page=1&limit=20
```
- `page`: 页码（从1开始，默认1）
- `limit`: 每页数量（默认20，最大100）

### 5.2 排序参数
```http
GET /api/v1/users?sort=-created_at,name
```
- `sort`: 排序字段，多个字段用逗号分隔
- `-field`: 降序排列
- `field`: 升序排列（默认）

### 5.3 分页响应格式
```json
{
  "code": 200,
  "data": {
    "items": [...],
    "total": 100,
    "page": 1,
    "limit": 20,
    "pages": 5
  },
  "message": "success"
}
```

## 6. 搜索与过滤

### 6.1 通用搜索
```http
GET /api/v1/users?q=zhang
```
- `q`: 全局搜索关键词

### 6.2 字段过滤
```http
GET /api/v1/users?role=admin&status=active
```
- 直接使用字段名作为查询参数
- 支持多值：`?status=active,inactive`

### 6.3 范围查询
```http
GET /api/v1/users?age_gte=18&age_lte=65
```
- `_gte`: 大于等于
- `_lte`: 小于等于
- `_gt`: 大于
- `_lt`: 小于

## 7. API文档规范

### 7.1 OpenAPI/Swagger
- 所有API必须提供OpenAPI 3.0文档
- 使用FastAPI自动生成功能
- 包含完整的请求/响应示例

### 7.2 文档结构
```python
@router.post("/water/pickup", 
    summary="创建领水记录",
    description="用户创建水站领水记录，支持预付和信用模式",
    response_description="成功创建领水记录的详细信息",
    responses={
        201: {"description": "成功创建"},
        400: {"description": "参数验证失败"},
        401: {"description": "未认证"},
        403: {"description": "权限不足"}
    }
)
async def create_pickup(pickup: PickupCreate):
    pass
```

## 8. 性能要求

### 8.1 响应时间
- **P95响应时间**：≤ 1秒
- **P99响应时间**：≤ 2秒
- **超时设置**：客户端30秒，服务间调用10秒

### 8.2 负载能力
- **并发用户**：≥ 1000
- **QPS**：≥ 500
- **CPU使用率**：≤ 80%

### 8.3 缓存策略
- **热点数据**：Redis缓存，TTL 5分钟
- **静态数据**：内存缓存，应用启动时加载
- **缓存失效**：写操作后立即失效

## 9. 安全要求

### 9.1 输入验证
- **参数验证**：使用Pydantic模型
- **SQL注入防护**：使用ORM，禁止原生SQL
- **XSS防护**：前端转义，后端过滤

### 9.2 输出安全
- **敏感信息过滤**：密码、token等不返回
- **权限校验**：每次请求都进行权限验证
- **审计日志**：关键操作记录完整日志

### 9.3 速率限制
- **用户级别**：100次/分钟
- **IP级别**：1000次/小时
- **API级别**：按业务重要性配置

## 10. 监控与日志

### 10.1 日志格式
```json
{
  "timestamp": "2026-04-09T10:00:00Z",
  "level": "INFO",
  "service": "water",
  "trace_id": "abc123",
  "span_id": "def456",
  "message": "User created pickup record",
  "user_id": 123,
  "pickup_id": 456
}
```

### 10.2 监控指标
- **请求量**：每秒请求数
- **错误率**：错误请求占比
- **响应时间**：P50/P95/P99
- **资源使用**：CPU/内存/磁盘

### 10.3 告警规则
- **错误率 > 5%**：立即告警
- **P95响应时间 > 2s**：立即告警  
- **服务不可用**：立即告警
- **磁盘使用 > 80%**：预警告警

## 附录A：API端点示例

### A.1 用户管理
```
GET    /api/v1/users              # 获取用户列表
POST   /api/v1/users              # 创建用户
GET    /api/v1/users/{id}         # 获取用户详情
PUT    /api/v1/users/{id}         # 更新用户
DELETE /api/v1/users/{id}         # 删除用户
```

### A.2 水站服务
```
GET    /api/v1/water/products     # 获取产品列表
GET    /api/v1/water/balance      # 获取用户余额
POST   /api/v1/water/pickup       # 创建领水记录
GET    /api/v1/water/pickups      # 获取领水记录
POST   /api/v1/water/settlement   # 申请结算
```

### A.3 会议室服务
```
GET    /api/v1/meeting/rooms      # 获取会议室列表
POST   /api/v1/meeting/bookings   # 创建预约
GET    /api/v1/meeting/bookings   # 获取预约列表
PUT    /api/v1/meeting/bookings/{id}/approve  # 审批预约
```

---
**版本历史：**
- v1.0 (2026-04-09): 初始版本，定义基础API规范