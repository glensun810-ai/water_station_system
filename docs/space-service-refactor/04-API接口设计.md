# 空间服务预约管理系统 - API接口设计

**版本:** v2.0
**设计日期:** 2026-04-12
**架构师:** API架构专家组

---

## 一、API设计总览

### 1.1 API版本策略

| 版本 | 路由前缀 | 状态 | 说明 |
|------|---------|------|------|
| **v1** | `/api/v1/meeting/*` | 维护模式 | 保留兼容，不再新增功能 |
| **v2** | `/api/v2/space/*` | **主版本** | 全部新功能在此版本 |

### 1.2 API路由结构

```
/api/v2/space/
├── types/              # 空间类型管理
│   ├── GET    /        # 获取空间类型列表
│   ├── GET    /{id}    # 获取空间类型详情
│   ├── POST   /        # 创建空间类型（管理员）
│   ├── PUT    /{id}    # 更新空间类型（管理员）
│   └── DELETE /{id}    # 删除空间类型（管理员）
│
├── resources/          # 空间资源管理
│   ├── GET    /        # 获取空间资源列表
│   ├── GET    /{id}    # 获取空间资源详情
│   ├── POST   /        # 创建空间资源（管理员）
│   ├── PUT    /{id}    # 更新空间资源（管理员）
│   ├── DELETE /{id}    # 删除空间资源（管理员）
│   ├── GET    /{id}/availability     # 查询可用时段
│   ├── GET    /{id}/slots/{date}     # 获取某日可用时段列表
│   └── GET    /{id}/calendar/{month} # 获取月度日历视图
│
├── bookings/           # 预约管理
│   ├── GET    /        # 获取预约列表
│   ├── GET    /{id}    # 获取预约详情
│   ├── POST   /        # 创建预约
│   ├── PUT    /{id}    # 修改预约
│   ├── DELETE /{id}    # 删除预约（软删除）
│   ├── PUT    /{id}/cancel            # 取消预约
│   ├── PUT    /{id}/check-in          # 签到入场
│   ├── PUT    /{id}/complete          # 完成预约
│   ├── POST   /{id}/rate              # 提交评价
│   ├── GET    /my                     # 我的预约列表
│   ├── GET    /my/stats               # 我的预约统计
│   └── GET    /calendar               # 预约日历视图
│
├── approvals/          # 审批管理
│   ├── GET    /        # 获取审批列表
│   ├── GET    /{id}    # 获取审批详情
│   ├── POST   /        # 提交审批申请
│   ├── PUT    /{id}/approve           # 审批通过
│   ├── PUT    /{id}/reject            # 审批拒绝（★修复BUG-001）
│   ├── PUT    /{id}/request-modify    # 要求修改
│   ├── GET    /pending                # 待审批列表
│   ├── GET    /my                     # 我提交的审批
│   └── POST   /batch-approve          # 批量审批
│
├── payments/           # 支付管理
│   ├── GET    /        # 获取支付记录列表
│   ├── GET    /{id}    # 获取支付详情
│   ├── POST   /        # 创建支付记录
│   ├── POST   /{id}/confirm           # 确认支付
│   ├── POST   /{id}/verify            # 审核支付（线下）
│   ├── POST   /{id}/refund            # 申请退款
│   ├── GET    /my                     # 我的支付记录
│   └── GET    /pending                # 待支付列表
│
├── settlements/        # 结算管理
│   ├── GET    /        # 获取结算列表
│   ├── GET    /{id}    # 获取结算详情
│   ├── POST   /        # 创建结算申请
│   ├── PUT    /{id}/approve           # 审批结算
│   ├── PUT    /{id}/confirm           # 确认结算
│   ├── GET    /summary                # 结算汇总
│   ├── GET    /statistics             # 结算统计
│   └── POST   /batch-create           # 批量创建结算
│
├── pricing/            # 定价管理
│   ├── GET    /rules                  # 获取定价规则列表
│   ├── POST   /rules                  # 创建定价规则
│   ├── PUT    /rules/{id}             # 更新定价规则
│   ├── GET    /time-slots             # 获取时段定价列表
│   ├── POST   /time-slots             # 创建时段定价
│   ├── GET    /addons                 # 获取增值服务列表
│   ├── POST   /addons                 # 创建增值服务
│   ├── GET    /discounts              # 获取折扣规则列表
│   ├── POST   /discounts              # 创建折扣规则
│   ├── POST   /calculate              # 计算费用（定价引擎）
│   └── POST   /preview                # 预览费用明细
│
├── notifications/      # 通知管理
│   ├── GET    /        # 获取通知列表
│   ├── GET    /{id}    # 获取通知详情
│   ├── PUT    /{id}/read              # 标记已读
│   ├── POST   /        # 发送通知（管理员）
│   ├── GET    /unread                 # 未读通知列表
│   ├── PUT    /batch-read             # 批量标记已读
│   └── GET    /my                     # 我的通知列表
│
├── statistics/         # 统计分析
│   ├── GET    /overview               # 统计概览
│   ├── GET    /usage                  # 使用率统计
│   ├── GET    /revenue                # 收入统计
│   ├── GET    /trends                 # 预约趋势
│   ├── GET    /by-type                # 按类型统计
│   ├── GET    /by-resource            # 按空间统计
│   ├── GET    /by-user                # 按用户统计
│   ├── GET    /by-department          # 按部门统计
│   ├── GET    /by-time                # 按时段统计
│   ├── POST   /export                 # 导出统计报表
│   └── GET    /dashboard              # Dashboard数据
│
├── calendar/           # 日历集成
│   ├── POST   /sync/outlook           # 同步Outlook日历
│   ├── POST   /sync/gcal              # 同步Google日历
│   ├── GET    /events                 # 获取日历事件
│   ├── DELETE /events/{id}            # 删除日历事件
│   └── POST   /invite                 # 发送日历邀请
│
└── invoices/           # 发票管理
    ├── GET    /        # 获取发票列表
    ├── GET    /{id}    # 获取发票详情
    ├── POST   /        # 申请发票
    ├── PUT    /{id}/issue             # 开具发票
    ├── PUT    /{id}/cancel            # 取消发票
    └── GET    /my                     # 我的发票列表
```

---

## 二、通用规范

### 2.1 请求规范

#### 认证方式

```http
Authorization: Bearer <JWT_TOKEN>
```

#### 请求头

```http
Content-Type: application/json
Accept: application/json
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
X-Request-ID: uuid-12345678  # 可选，用于追踪请求
```

#### 分页参数

```http
GET /api/v2/space/bookings?page=1&limit=20
```

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| page | int | 1 | 页码（从1开始） |
| limit | int | 20 | 每页数量（最大100） |

#### 排序参数

```http
GET /api/v2/space/bookings?sort=-created_at,status
```

| 参数 | 说明 |
|------|------|
| -field | 降序排列 |
| field | 升序排列（默认） |

#### 过滤参数

```http
GET /api/v2/space/bookings?type_code=meeting_room&status=confirmed&date_from=2026-04-01&date_to=2026-04-30
```

### 2.2 响应规范

#### 成功响应

```json
{
  "code": 200,
  "message": "success",
  "data": {
    ...
  },
  "timestamp": "2026-04-12T10:00:00Z"
}
```

#### 分页响应

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "items": [...],
    "total": 100,
    "page": 1,
    "limit": 20,
    "pages": 5
  },
  "timestamp": "2026-04-12T10:00:00Z"
}
```

#### 错误响应

```json
{
  "code": 400,
  "message": "预约时间冲突",
  "data": null,
  "error": {
    "error_code": "BOOKING_TIME_CONFLICT",
    "error_detail": "会议室A在14:00-16:00已被预约",
    "conflicting_booking_id": 123
  },
  "timestamp": "2026-04-12T10:00:00Z"
}
```

### 2.3 错误码体系

| HTTP状态码 | 错误码 | 说明 |
|-----------|--------|------|
| 400 | VALIDATION_ERROR | 参数验证失败 |
| 400 | BOOKING_TIME_CONFLICT | 预约时间冲突 |
| 400 | BOOKING_STATUS_INVALID | 预约状态不允许此操作 |
| 400 | CAPACITY_EXCEEDED | 容量超限 |
| 401 | UNAUTHORIZED | 未认证或认证过期 |
| 401 | TOKEN_INVALID | Token无效 |
| 401 | TOKEN_EXPIRED | Token过期 |
| 403 | PERMISSION_DENIED | 权限不足 |
| 403 | RESOURCE_NOT_ALLOWED | 无权限访问该资源 |
| 404 | RESOURCE_NOT_FOUND | 资源不存在 |
| 404 | BOOKING_NOT_FOUND | 预约不存在 |
| 409 | DUPLICATE_BOOKING | 重复预约 |
| 422 | BUSINESS_RULE_VIOLATION | 业务规则违规 |
| 500 | INTERNAL_ERROR | 服务器内部错误 |
| 503 | SERVICE_UNAVAILABLE | 服务暂时不可用 |

---

## 三、核心API详细设计

### 3.1 空间类型管理API

#### 获取空间类型列表

```http
GET /api/v2/space/types
```

**请求参数:**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| is_active | boolean | 否 | 过滤激活状态 |

**响应示例:**

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "items": [
      {
        "id": 1,
        "type_code": "meeting_room",
        "type_name": "会议室",
        "type_name_en": "Meeting Room",
        "description": "小型团队协作空间",
        "min_duration_unit": "hour",
        "min_duration_value": 1,
        "max_duration_value": 8,
        "advance_booking_days": 0,
        "min_capacity": 2,
        "max_capacity": 20,
        "requires_approval": false,
        "requires_deposit": false,
        "standard_facilities": ["投影仪", "白板", "音响", "网络", "空调"],
        "is_active": true,
        "icon": "🏢",
        "color_theme": "#3B82F6"
      },
      {
        "id": 2,
        "type_code": "venue",
        "type_name": "会场/多功能厅",
        ...
      }
    ],
    "total": 5
  }
}
```

---

### 3.2 空间资源管理API

#### 获取空间资源列表

```http
GET /api/v2/space/resources?type_code=meeting_room&is_active=true&page=1&limit=20
```

**请求参数:**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| type_code | string | 否 | 空间类型代码过滤 |
| type_id | int | 否 | 空间类型ID过滤 |
| is_active | boolean | 否 | 激活状态过滤 |
| is_available | boolean | 否 | 可预约状态过滤 |
| capacity_gte | int | 否 | 容量大于等于 |
| capacity_lte | int | 否 | 容量小于等于 |
| location | string | 否 | 位置关键词搜索 |
| q | string | 否 | 名称关键词搜索 |

**响应示例:**

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "items": [
      {
        "id": 1,
        "type_id": 1,
        "type_code": "meeting_room",
        "type_name": "会议室",
        "name": "会议室A",
        "location": "3楼301室",
        "floor": "3",
        "building": "主楼",
        "capacity": 10,
        "capacity_level": "small",
        "facilities": ["投影仪", "白板", "音响", "网络", "空调"],
        "base_price": 50.0,
        "member_price": 40.0,
        "price_unit": "hour",
        "free_hours_per_month": 2,
        "is_active": true,
        "is_available": true,
        "photos": ["url1", "url2"],
        "description": "适合小型会议和讨论"
      }
    ],
    "total": 15,
    "page": 1,
    "limit": 20,
    "pages": 1
  }
}
```

#### 查询空间可用时段

```http
GET /api/v2/space/resources/{id}/availability?date=2026-04-15
```

**响应示例:**

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "resource_id": 1,
    "resource_name": "会议室A",
    "date": "2026-04-15",
    "operating_hours": {
      "start": "08:00",
      "end": "22:00"
    },
    "booked_slots": [
      {
        "start_time": "09:00",
        "end_time": "11:00",
        "booking_id": 123,
        "booking_title": "产品评审会议"
      },
      {
        "start_time": "14:00",
        "end_time": "16:00",
        "booking_id": 124,
        "booking_title": "客户洽谈"
      }
    ],
    "available_slots": [
      {
        "start_time": "08:00",
        "end_time": "09:00",
        "duration": 1
      },
      {
        "start_time": "11:00",
        "end_time": "14:00",
        "duration": 3
      },
      {
        "start_time": "16:00",
        "end_time": "22:00",
        "duration": 6
      }
    ],
    "total_available_hours": 10
  }
}
```

---

### 3.3 预约管理API

#### 创建预约（核心API）

```http
POST /api/v2/space/bookings
Authorization: Bearer <token>
Content-Type: application/json
```

**请求体（会议室预约）:**

```json
{
  "resource_id": 1,
  "booking_date": "2026-04-15",
  "start_time": "14:00",
  "end_time": "16:00",
  "purpose": "项目讨论",
  "title": "产品迭代讨论会",
  "attendees_count": 8,
  "attendees_info": [
    {"name": "张三", "email": "zhangsan@example.com"},
    {"name": "李四", "email": "lisi@example.com"}
  ],
  "special_requests": {
    "need_projector": true,
    "need_refreshments": true
  },
  "addons_selected": [
    {"addon_code": "refreshment", "quantity": 8}
  ],
  "user_notes": "需要准备演示文稿"
}
```

**请求体（会场预约）:**

```json
{
  "resource_id": 5,
  "type_code": "venue",
  "booking_date": "2026-04-20",
  "end_date": "2026-04-20",
  "start_time": "09:00",
  "end_time": "18:00",
  "duration_unit": "full_day",
  "purpose": "年会",
  "title": "2026年度总结大会",
  "attendees_count": 200,
  "event_plan_url": "https://example.com/event-plan.pdf",
  "addons_selected": [
    {"addon_code": "tea_break", "quantity": 200, "unit_price": 50},
    {"addon_code": "led_screen", "quantity": 1, "unit_price": 1000},
    {"addon_code": "live_stream", "quantity": 1, "unit_price": 2000}
  ]
}
```

**请求体（VIP餐厅预约）:**

```json
{
  "resource_id": 10,
  "type_code": "vip_dining",
  "booking_date": "2026-04-15",
  "meal_session": "lunch",
  "start_time": "11:30",
  "end_time": "14:00",
  "meal_standard": "vip",
  "guests_count": 10,
  "purpose": "VIP客户接待",
  "title": "合作签约午餐会",
  "special_requests": {
    "vegetarian_needed": true,
    "birthday_cake": true,
    "birthday_person": "王总"
  }
}
```

**响应示例:**

```json
{
  "code": 201,
  "message": "预约创建成功",
  "data": {
    "id": 125,
    "booking_no": "SB20260415001",
    "resource_id": 1,
    "resource_name": "会议室A",
    "type_code": "meeting_room",
    "type_name": "会议室",
    "user_id": 10,
    "user_name": "张三",
    "user_type": "internal",
    "department": "产品部",
    "booking_date": "2026-04-15",
    "start_time": "14:00",
    "end_time": "16:00",
    "duration": 2,
    "duration_unit": "hour",
    "title": "产品迭代讨论会",
    "attendees_count": 8,
    "status": "confirmed",
    "payment_status": "unpaid",
    "base_fee": 100.0,
    "addon_fee": 0.0,
    "discount_amount": 20.0,
    "total_fee": 80.0,
    "requires_deposit": false,
    "can_modify": true,
    "can_cancel": true,
    "cancel_deadline": "2026-04-14T23:59:59Z",
    "created_at": "2026-04-12T10:00:00Z",
    "confirmation_sent": true,
    "calendar_invite_sent": true
  }
}
```

#### 取消预约

```http
PUT /api/v2/space/bookings/{id}/cancel
Authorization: Bearer <token>
Content-Type: application/json
```

**请求体:**

```json
{
  "cancel_reason": "会议取消，议题已解决",
  "cancel_type": "user_cancel"
}
```

**响应示例:**

```json
{
  "code": 200,
  "message": "预约已取消",
  "data": {
    "id": 125,
    "booking_no": "SB20260415001",
    "status": "cancelled",
    "cancelled_at": "2026-04-13T09:00:00Z",
    "cancelled_by": "张三",
    "cancel_reason": "会议取消，议题已解决",
    "deposit_refund": {
      "refundable": false,
      "refund_amount": 0,
      "reason": "无需定金"
    }
  }
}
```

---

### 3.4 审批管理API

#### 审批通过

```http
PUT /api/v2/space/approvals/{id}/approve
Authorization: Bearer <admin_token>
Content-Type: application/json
```

**请求体:**

```json
{
  "approval_notes": "活动方案可行，同意举办",
  "approver_id": 5,
  "approver_name": "行政主管"
}
```

**响应示例:**

```json
{
  "code": 200,
  "message": "审批通过",
  "data": {
    "id": 50,
    "approval_no": "SA20260412001",
    "booking_id": 125,
    "status": "approved",
    "approved_at": "2026-04-12T11:00:00Z",
    "approved_by": "行政主管",
    "approval_notes": "活动方案可行，同意举办",
    "next_action": {
      "action": "pay_deposit",
      "amount": 897.5,
      "deadline": "2026-04-14T23:59:59Z"
    },
    "notification_sent": true
  }
}
```

#### 审批拒绝（★修复BUG-001）

```http
PUT /api/v2/space/approvals/{id}/reject
Authorization: Bearer <admin_token>
Content-Type: application/json
```

**请求体:**

```json
{
  "rejection_reason": "活动方案存在安全隐患，需补充安全预案",
  "rejection_detail": "1. 未提供消防通道示意图\n2. 未标注紧急疏散路线\n3. 缺少现场安全负责人信息",
  "suggest_alternatives": [
    {
      "resource_id": 6,
      "resource_name": "会场B",
      "available_dates": ["2026-04-21", "2026-04-22"]
    }
  ],
  "allow_resubmit": true,
  "resubmit_deadline": "2026-04-15T23:59:59Z"
}
```

**响应示例:**

```json
{
  "code": 200,
  "message": "审批已拒绝，申请人将收到通知",
  "data": {
    "id": 50,
    "approval_no": "SA20260412001",
    "booking_id": 125,
    "status": "rejected",
    "rejected_at": "2026-04-12T11:00:00Z",
    "rejected_by": "行政主管",
    "rejection_reason": "活动方案存在安全隐患，需补充安全预案",
    "rejection_detail": "1. 未提供消防通道示意图\n2. 未标注紧急疏散路线\n3. 缺少现场安全负责人信息",
    "suggest_alternatives": [...],
    "allow_resubmit": true,
    "booking_status": "rejected",
    "notification_sent": true,
    "notification_channels": ["email", "sms", "app_push"]
  }
}
```

---

### 3.5 定价引擎API

#### 计算费用

```http
POST /api/v2/space/pricing/calculate
Content-Type: application/json
```

**请求体:**

```json
{
  "resource_id": 1,
  "type_code": "meeting_room",
  "booking_date": "2026-04-15",
  "start_time": "14:00",
  "end_time": "16:00",
  "duration": 2,
  "user_id": 10,
  "user_type": "internal",
  "member_level": "vip",
  "addons_selected": [
    {"addon_code": "refreshment", "quantity": 8}
  ],
  "promotion_code": "NEW2026"
}
```

**响应示例:**

```json
{
  "code": 200,
  "message": "费用计算成功",
  "data": {
    "calculation_detail": {
      "base_fee": {
        "price_per_unit": 50.0,
        "units": 2,
        "subtotal": 100.0
      },
      "time_slot_adjustment": {
        "slot_type": "normal",
        "multiplier": 1.0,
        "adjustment": 0
      },
      "member_discount": {
        "member_level": "vip",
        "discount_rate": 0.8,
        "discount_amount": 20.0
      },
      "duration_discount": {
        "duration": 2,
        "discount_rate": 1.0,
        "discount_amount": 0
      },
      "free_quota": {
        "available": 2,
        "used": 1.5,
        "remaining": 0.5,
        "applied": 0,
        "reason": "本次预约时长超过剩余免费额度"
      },
      "addon_fee": {
        "items": [
          {
            "addon_code": "refreshment",
            "addon_name": "茶歇服务",
            "quantity": 8,
            "unit_price": 20.0,
            "subtotal": 160.0
          }
        ],
        "subtotal": 160.0
      },
      "promotion_discount": {
        "promotion_code": "NEW2026",
        "discount_rate": 0.9,
        "discount_amount": 24.0
      }
    },
    "fee_summary": {
      "base_fee": 100.0,
      "addon_fee": 160.0,
      "subtotal": 260.0,
      "discount_total": 44.0,
      "final_fee": 216.0
    },
    "deposit_info": {
      "requires_deposit": false,
      "deposit_amount": 0
    },
    "payment_methods": ["wechat", "alipay", "internal_account"]
  }
}
```

---

### 3.6 通知服务API

#### 发送预约确认通知

```http
POST /api/v2/space/notifications
Authorization: Bearer <admin_token>
Content-Type: application/json
```

**请求体:**

```json
{
  "booking_id": 125,
  "notification_type": "booking_confirmed",
  "recipient_id": 10,
  "channels": ["email", "sms", "app_push"],
  "template_data": {
    "booking_no": "SB20260415001",
    "resource_name": "会议室A",
    "booking_date": "2026-04-15",
    "start_time": "14:00",
    "end_time": "16:00",
    "location": "3楼301室"
  },
  "scheduled_at": "2026-04-12T10:00:00Z"
}
```

**响应示例:**

```json
{
  "code": 200,
  "message": "通知发送成功",
  "data": {
    "notification_id": 1001,
    "status": "sent",
    "delivery_status": {
      "email": {
        "status": "sent",
        "sent_at": "2026-04-12T10:00:01Z"
      },
      "sms": {
        "status": "sent",
        "sent_at": "2026-04-12T10:00:02Z"
      },
      "app_push": {
        "status": "delivered",
        "sent_at": "2026-04-12T10:00:00Z",
        "delivered_at": "2026-04-12T10:00:03Z"
      }
    }
  }
}
```

---

### 3.7 统计分析API

#### 获取统计概览

```http
GET /api/v2/space/statistics/overview?date_from=2026-04-01&date_to=2026-04-30
Authorization: Bearer <admin_token>
```

**响应示例:**

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "period": {
      "from": "2026-04-01",
      "to": "2026-04-30"
    },
    "summary": {
      "total_bookings": 150,
      "total_hours": 320,
      "total_revenue": 15000.0,
      "average_booking_duration": 2.1,
      "booking_success_rate": 85.0,
      "cancellation_rate": 12.0,
      "space_utilization_rate": 72.5
    },
    "by_type": [
      {
        "type_code": "meeting_room",
        "type_name": "会议室",
        "booking_count": 120,
        "hours": 240,
        "revenue": 6000.0,
        "utilization": 80.0
      },
      {
        "type_code": "venue",
        "type_name": "会场",
        "booking_count": 10,
        "hours": 80,
        "revenue": 5000.0,
        "utilization": 60.0
      }
    ],
    "by_status": {
      "pending_approval": 5,
      "approved": 20,
      "confirmed": 100,
      "completed": 25,
      "cancelled": 18,
      "rejected": 2
    },
    "trends": {
      "daily": [...],
      "weekly": [...],
      "monthly": [...]
    }
  }
}
```

#### 导出统计报表

```http
POST /api/v2/space/statistics/export
Authorization: Bearer <admin_token>
Content-Type: application/json
```

**请求体:**

```json
{
  "report_type": "monthly_usage",
  "period": {
    "from": "2026-04-01",
    "to": "2026-04-30"
  },
  "format": "pdf",
  "include_details": true,
  "language": "zh-CN"
}
```

**响应示例:**

```json
{
  "code": 200,
  "message": "报表生成成功",
  "data": {
    "report_id": 100,
    "report_url": "https://example.com/reports/usage_202604.pdf",
    "generated_at": "2026-04-30T10:00:00Z",
    "expires_at": "2026-05-30T10:00:00Z"
  }
}
```

---

## 四、API权限矩阵

| API路径 | 方法 | 权限要求 | 说明 |
|---------|------|---------|------|
| `/types` | GET | 无需认证 | 公开信息 |
| `/types` | POST | admin/super_admin | 管理员可创建类型 |
| `/resources` | GET | 无需认证 | 公开信息 |
| `/resources` | POST | admin/space_manager | 管理员可创建空间 |
| `/resources/{id}/availability` | GET | 无需认证 | 公开信息 |
| `/bookings` | GET | 登录用户 | 查看自己的预约 |
| `/bookings` | POST | 登录用户 | 创建预约 |
| `/bookings/{id}` | GET | 预约人或管理员 | 查看预约详情 |
| `/bookings/{id}` | PUT | 预约人或管理员 | 修改预约 |
| `/bookings/{id}/cancel` | PUT | 预约人或管理员 | 取消预约 |
| `/approvals` | GET | admin/space_manager | 查看审批列表 |
| `/approvals/{id}/approve` | PUT | admin/space_manager | 审批通过 |
| `/approvals/{id}/reject` | PUT | admin/space_manager | 审批拒绝 |
| `/payments` | GET | admin/finance_staff | 查看支付记录 |
| `/payments/{id}/confirm` | POST | admin/finance_staff | 确认支付 |
| `/settlements` | GET | admin/finance_staff | 查看结算列表 |
| `/statistics/*` | GET | admin/space_manager | 查看统计 |
| `/pricing/*` | GET/POST | admin/super_admin | 定价管理 |

---

## 五、API版本兼容策略

### 5.1 v1 API兼容映射

| v1路由 | v2路由 | 兼容性说明 |
|--------|--------|-----------|
| `/api/v1/meeting/rooms` | `/api/v2/space/resources?type_code=meeting_room` | 内部转发 |
| `/api/v1/meeting/bookings` | `/api/v2/space/bookings` | 内部转发 |
| `/api/v1/meeting/bookings/{id}/approve` | `/api/v2/space/approvals/{id}/approve` | 内部转发 |
| `/api/v1/meeting/stats/today` | `/api/v2/space/statistics/dashboard` | 内部转发 |

### 5.2 兼容期策略

- **兼容期:** 3个月（2026-04-12 至 2026-07-12）
- **兼容期内:** v1 API正常响应，日志记录使用情况
- **兼容期后:** v1 API返回410 Gone，提示迁移到v2

---

**文档状态:** 已完成
**下一步:** 前端设计方案文档