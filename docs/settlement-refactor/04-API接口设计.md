# 水站结算管理模块重构方案 - API接口设计

**文档版本**: v1.0  
**创建日期**: 2026-04-08  
**文档性质**: API接口规范  

---

## 一、API接口架构概览

### 1.1 API版本管理

**策略**: 采用双版本并存策略
- v1: 保留旧API,兼容现有前端
- v2: 新API,实现新业务逻辑

**路由前缀**:
```
/api/v1/*  - 旧API接口(兼容模式)
/api/v2/*  - 新API接口(重构版本)
```

---

### 1.2 API模块划分

| 模块 | 路由前缀 | 说明 | 新增/修改 |
|------|---------|------|----------|
| 领水记录管理 | /api/v2/pickups | 领水记录CRUD | 修改 |
| 结算申请管理 | /api/v2/settlements | 结算申请单管理 | 新增 |
| 结算审核管理 | /api/v2/settlements/review | 结算审核操作 | 新增 |
| 结算确认管理 | /api/v2/settlements/confirm | 收款确认操作 | 新增 |
| 月度结算管理 | /api/v2/monthly-settlements | 月度结算单管理 | 新增 |
| 统计查询 | /api/v2/settlements/stats | 结算统计查询 | 新增 |
| 操作日志 | /api/v2/settlements/logs | 操作日志查询 | 新增 |
| 提醒催款 | /api/v2/settlements/remind | 催款提醒操作 | 新增 |

---

## 二、领水记录管理API (修改)

### 2.1 获取领水记录列表

**接口**: `GET /api/v2/pickups`

**请求参数**:
```python
{
    "office_id": Optional[int],  # 办公室ID筛选
    "status": Optional[str],  # 状态筛选: pending/applied/approved/confirmed/settled
    "start_date": Optional[str],  # 开始日期: YYYY-MM-DD
    "end_date": Optional[str],  # 结束日期: YYYY-MM-DD
    "product_id": Optional[int],  # 产品ID筛选
    "pickup_person": Optional[str],  # 领取人姓名搜索
    "page": int = 1,  # 页码
    "page_size": int = 20,  # 每页数量
    "sort_by": Optional[str],  # 排序字段: pickup_time/total_amount
    "sort_order": Optional[str]  # 排序方向: asc/desc
}
```

**响应格式**:
```python
{
    "success": True,
    "data": {
        "records": [
            {
                "id": 1,
                "office_id": 101,
                "office_name": "A101办公室",
                "office_room_number": "A101",
                "product_id": 1,
                "product_name": "18L桶装水",
                "product_specification": "18L",
                "quantity": 3,
                "unit_price": 15.00,
                "total_amount": 45.00,
                "free_quantity": 0,
                "pickup_person": "张三",
                "pickup_person_id": 201,
                "pickup_time": "2026-04-08 10:30:00",
                "settlement_status": "pending",
                "payment_mode": "credit",
                "settlement_application_id": null,
                "is_disputed": false,
                "note": null,
                "created_at": "2026-04-08 10:30:00",
                "updated_at": "2026-04-08 10:30:00"
            }
        ],
        "pagination": {
            "total": 100,
            "page": 1,
            "page_size": 20,
            "total_pages": 5
        }
    }
}
```

**示例请求**:
```bash
GET /api/v2/pickups?office_id=101&status=pending&page=1&page_size=20
```

---

### 2.2 创建领水记录

**接口**: `POST /api/v2/pickups`

**请求参数**:
```python
{
    "office_id": int,  # 办公室ID(必填)
    "product_id": int,  # 产品ID(必填)
    "quantity": int,  # 数量(必填)
    "pickup_person": str,  # 领取人姓名(必填)
    "pickup_person_id": Optional[int],  # 领取人用户ID
    "pickup_time": Optional[str],  # 领取时间(可选,默认当前时间)
    "payment_mode": Optional[str],  # 付款模式(可选,默认credit)
    "note": Optional[str]  # 备注
}
```

**响应格式**:
```python
{
    "success": True,
    "data": {
        "id": 1,
        "office_id": 101,
        "office_name": "A101办公室",
        "product_name": "18L桶装水",
        "quantity": 3,
        "total_amount": 45.00,
        "settlement_status": "pending",
        "pickup_time": "2026-04-08 10:30:00",
        "created_at": "2026-04-08 10:30:00"
    },
    "message": "领水记录创建成功"
}
```

**业务逻辑**:
1. 验证办公室ID和产品ID有效性
2. 验证库存充足(产品库存 >= 数量)
3. 计算总金额(含优惠)
4. 自动扣减库存
5. 设置初始状态为`pending`
6. 记录操作日志

---

### 2.3 更新领水记录

**接口**: `PUT /api/v2/pickups/{pickup_id}`

**请求参数**:
```python
{
    "quantity": Optional[int],  # 数量
    "pickup_person": Optional[str],  # 领取人姓名
    "pickup_time": Optional[str],  # 领取时间
    "note": Optional[str]  # 备注
}
```

**响应格式**:
```python
{
    "success": True,
    "data": {
        "id": 1,
        "quantity": 5,
        "total_amount": 75.00,
        "updated_at": "2026-04-08 11:00:00"
    },
    "message": "领水记录更新成功"
}
```

**业务约束**:
- ❌ 已申请结算的记录不允许修改
- ❌ 已结清的记录不允许修改
- ✅ 只有pending状态的记录可以修改

---

### 2.4 删除领水记录(软删除)

**接口**: `DELETE /api/v2/pickups/{pickup_id}`

**响应格式**:
```python
{
    "success": True,
    "data": {
        "id": 1,
        "is_deleted": true,
        "deleted_at": "2026-04-08 11:30:00"
    },
    "message": "领水记录已删除"
}
```

**业务约束**:
- ❌ 已结清的记录不允许删除
- ✅ 只有pending/applied状态的记录可以删除
- ✅ 使用软删除(is_deleted=true)

---

### 2.5 标记争议记录

**接口**: `POST /api/v2/pickups/{pickup_id}/dispute`

**请求参数**:
```python
{
    "dispute_reason": str,  # 争议原因(必填)
    "dispute_evidence": Optional[str],  # 争议证据URL
    "note": Optional[str]  # 备注
}
```

**响应格式**:
```python
{
    "success": True,
    "data": {
        "id": 1,
        "is_disputed": true,
        "dispute_reason": "记录有误,实际未领取",
        "dispute_reported_at": "2026-04-08 12:00:00",
        "settlement_status": "disputed"
    },
    "message": "争议已标记,请等待管理员处理"
}
```

---

## 三、结算申请管理API (新增)

### 3.1 创建结算申请单

**接口**: `POST /api/v2/settlements/apply`

**请求参数**:
```python
{
    "office_id": int,  # 办公室ID(必填)
    "pickup_ids": List[int],  # 领水记录ID列表(必填)
    "note": Optional[str]  # 申请备注
}
```

**响应格式**:
```python
{
    "success": True,
    "data": {
        "id": 101,
        "application_no": "SA-20260408-0001",
        "office_id": 101,
        "office_name": "A101办公室",
        "applicant_id": 201,
        "applicant_name": "张经理",
        "applied_at": "2026-04-08 14:30:00",
        "record_count": 3,
        "total_amount": 135.00,
        "status": "applied",
        "items": [
            {
                "pickup_id": 1,
                "pickup_time": "2026-04-08 10:30:00",
                "product_name": "18L桶装水",
                "quantity": 3,
                "amount": 45.00
            }
        ]
    },
    "message": "结算申请提交成功,请等待管理员审核"
}
```

**业务逻辑**:
1. 验证申请人权限(必须是办公室负责人)
2. 验证所有记录属于同一办公室
3. 验证所有记录状态为`pending`
4. 计算总金额和记录数量
5. 生成申请单编号(SA-YYYYMMDD-NNNN)
6. 创建结算明细关联记录
7. 更新领水记录状态为`applied`
8. 发送审核通知给管理员
9. 记录操作日志

---

### 3.2 获取结算申请单列表

**接口**: `GET /api/v2/settlements`

**请求参数**:
```python
{
    "office_id": Optional[int],  # 办公室ID筛选
    "status": Optional[str],  # 状态筛选: applied/approved/confirmed/settled
    "applicant_id": Optional[int],  #申请人ID筛选
    "start_date": Optional[str],  # 申请开始日期
    "end_date": Optional[str],  # 申请结束日期
    "settlement_period": Optional[str],  # 结算周期筛选
    "page": int = 1,
    "page_size": int = 20
}
```

**响应格式**:
```python
{
    "success": True,
    "data": {
        "applications": [
            {
                "id": 101,
                "application_no": "SA-20260408-0001",
                "office_id": 101,
                "office_name": "A101办公室",
                "applicant_id": 201,
                "applicant_name": "张经理",
                "applied_at": "2026-04-08 14:30:00",
                "record_count": 3,
                "total_amount": 135.00,
                "status": "applied",
                "reviewer_id": null,
                "reviewer_name": null,
                "reviewed_at": null,
                "confirmer_id": null,
                "confirmer_name": null,
                "confirmed_at": null,
                "payment_method": null,
                "payment_amount": null,
                "receipt_no": null,
                "settlement_period": null,
                "monthly_settlement_id": null
            }
        ],
        "pagination": {
            "total": 50,
            "page": 1,
            "page_size": 20,
            "total_pages": 3
        }
    }
}
```

---

### 3.3 获取结算申请单详情

**接口**: `GET /api/v2/settlements/{application_id}`

**响应格式**:
```python
{
    "success": True,
    "data": {
        "id": 101,
        "application_no": "SA-20260408-0001",
        "office_id": 101,
        "office_name": "A101办公室",
        "office_room_number": "A101",
        "applicant_id": 201,
        "applicant_name": "张经理",
        "applied_at": "2026-04-08 14:30:00",
        "record_count": 3,
        "total_amount": 135.00,
        "status": "applied",
        
        # 审核信息
        "reviewer_id": null,
        "reviewer_name": null,
        "reviewed_at": null,
        "review_status": null,
        "review_note": null,
        
        # 收款信息
        "confirmer_id": null,
        "confirmer_name": null,
        "confirmed_at": null,
        "payment_method": null,
        "payment_amount": null,
        "payment_time": null,
        "payment_evidence": null,
        
        # 差额信息
        "difference_amount": null,
        "difference_status": null,
        "difference_note": null,
        
        # 收据信息
        "receipt_no": null,
        "receipt_generated_at": null,
        
        # 结算明细
        "items": [
            {
                "id": 1,
                "pickup_id": 1,
                "pickup_time": "2026-04-08 10:30:00",
                "product_name": "18L桶装水",
                "product_specification": "18L",
                "quantity": 3,
                "unit_price": 15.00,
                "amount": 45.00,
                "pickup_status": "applied",
                "pickup_person": "张三"
            }
        ],
        
        # 操作日志(最近5条)
        "logs": [
            {
                "id": 1,
                "operation_type": "apply",
                "operator_id": 201,
                "operator_name": "张经理",
                "operated_at": "2026-04-08 14:30:00",
                "note": "提交结算申请"
            }
        ]
    }
}
```

---

### 3.4 取消结算申请

**接口**: `POST /api/v2/settlements/{application_id}/cancel`

**请求参数**:
```python
{
    "reason": str  # 取消原因(必填)
}
```

**响应格式**:
```python
{
    "success": True,
    "data": {
        "id": 101,
        "status": "cancelled",
        "cancelled_at": "2026-04-08 15:00:00",
        "cancelled_reason": "申请人主动取消",
        
        # 关联的领水记录状态回退
        "affected_pickups": [
            {
                "id": 1,
                "old_status": "applied",
                "new_status": "pending"
            }
        ]
    },
    "message": "结算申请已取消,领水记录状态已回退"
}
```

**业务约束**:
- ✅ 只有applied状态(待审核)的申请单可以取消
- ❌ 已审核或已收款的申请单不允许取消
- ✅ 取消后自动回退关联领水记录状态到pending

---

## 四、结算审核管理API (新增)

### 4.1 审核通过结算申请

**接口**: `POST /api/v2/settlements/{application_id}/approve`

**请求参数**:
```python
{
    "note": Optional[str]  # 审核备注
}
```

**响应格式**:
```python
{
    "success": True,
    "data": {
        "id": 101,
        "status": "approved",
        "reviewer_id": 301,
        "reviewer_name": "李会计",
        "reviewed_at": "2026-04-08 15:30:00",
        "review_status": "approved",
        "review_note": "审核通过",
        
        # 关联的领水记录状态更新
        "affected_pickups": [
            {
                "id": 1,
                "old_status": "applied",
                "new_status": "approved"
            }
        ]
    },
    "message": "结算申请审核通过,请等待办公室付款"
}
```

**业务逻辑**:
1. 验证审核人权限(必须是管理员)
2. 验证申请单状态为`applied`
3. 更新申请单状态为`approved`
4. 同步更新关联领水记录状态为`approved`
5. 发送审核结果通知给申请人
6. 记录操作日志

---

### 4.2 审核拒绝结算申请

**接口**: `POST /api/v2/settlements/{application_id}/reject`

**请求参数**:
```python
{
    "reason": str  # 拒绝原因(必填)
}
```

**响应格式**:
```python
{
    "success": True,
    "data": {
        "id": 101,
        "status": "rejected",
        "reviewer_id": 301,
        "reviewer_name": "李会计",
        "reviewed_at": "2026-04-08 15:30:00",
        "review_status": "rejected",
        "review_note": "申请金额计算错误",
        
        # 关联的领水记录状态回退
        "affected_pickups": [
            {
                "id": 1,
                "old_status": "applied",
                "new_status": "pending"
            }
        ]
    },
    "message": "结算申请已拒绝,领水记录状态已回退"
}
```

---

### 4.3 批量审核通过

**接口**: `POST /api/v2/settlements/batch-approve`

**请求参数**:
```python
{
    "application_ids": List[int],  # 申请单ID列表(必填)
    "note": Optional[str]  # 批量审核备注
}
```

**响应格式**:
```python
{
    "success": True,
    "data": {
        "approved_count": 5,
        "failed_count": 0,
        "approved_applications": [101, 102, 103, 104, 105],
        "failed_applications": []
    },
    "message": "批量审核完成: 5条成功, 0条失败"
}
```

---

## 五、结算确认管理API (新增)

### 5.1 确认收款

**接口**: `POST /api/v2/settlements/{application_id}/confirm`

**请求参数**:
```python
{
    "payment_method": str,  # 收款方式: cash/transfer/alipay/wechat/credit
    "payment_amount": float,  # 实际收款金额
    "payment_time": Optional[str],  # 收款时间(可选,默认当前时间)
    "payment_evidence": Optional[str],  # 收款凭证URL
    "note": Optional[str]  # 收款备注
}
```

**响应格式**:
```python
{
    "success": True,
    "data": {
        "id": 101,
        "status": "settled",
        "confirmer_id": 301,
        "confirmer_name": "李会计",
        "confirmed_at": "2026-04-08 16:30:00",
        "payment_method": "transfer",
        "payment_amount": 135.00,
        "payment_time": "2026-04-08 16:00:00",
        "payment_evidence": "https://example.com/evidence/123.jpg",
        
        # 差额信息(如果有)
        "difference_amount": null,
        "difference_status": null,
        
        # 收据信息
        "receipt_no": "RC-20260408-0001",
        "receipt_generated_at": "2026-04-08 16:30:00",
        
        # 关联的领水记录状态更新
        "affected_pickups": [
            {
                "id": 1,
                "old_status": "approved",
                "new_status": "settled"
            }
        ]
    },
    "message": "收款确认成功,已生成收据: RC-20260408-0001"
}
```

**业务逻辑**:
1. 验证确认人权限(必须是管理员)
2. 验证申请单状态为`approved`或`confirmed`
3. 核对收款金额与申请金额
4. 记录差额信息(如果有)
5. 生成收据编号(RC-YYYYMMDD-NNNN)
6. 更新申请单状态为`settled`
7. 同步更新关联领水记录状态为`settled`
8. 发送收款确认通知给申请人
9. 记录操作日志

---

### 5.2 部分收款确认

**接口**: `POST /api/v2/settlements/{application_id}/partial-confirm`

**请求参数**:
```python
{
    "payment_method": str,
    "payment_amount": float,  # 实际收款金额(小于申请金额)
    "payment_time": Optional[str],
    "payment_evidence": Optional[str],
    "difference_status": str,  # pending/waived/installment
    "difference_note": str,  # 差额说明
    "note": Optional[str]
}
```

**响应格式**:
```python
{
    "success": True,
    "data": {
        "id": 101,
        "status": "partially_settled",
        "payment_amount": 700.00,
        "difference_amount": 100.00,
        "difference_status": "pending",
        "difference_note": "办公室称本月预算不足,申请下月补缴",
        
        # 差额处理选项
        "difference_options": [
            {
                "option": "continue_collect",
                "description": "继续追缴,保持待收款状态"
            },
            {
                "option": "waive",
                "description": "作废差额,需审批"
            },
            {
                "option": "installment",
                "description": "分期付款,设置后续收款计划"
            }
        ]
    },
    "message": "部分收款已确认,差额¥100待处理"
}
```

---

### 5.3 作废差额

**接口**: `POST /api/v2/settlements/{application_id}/waive-difference`

**请求参数**:
```python
{
    "reason": str  # 作废原因(必填)
}
```

**响应格式**:
```python
{
    "success": True,
    "data": {
        "id": 101,
        "status": "settled",
        "difference_amount": 100.00,
        "difference_status": "waived",
        "difference_note": "管理员批准作废差额",
        "settled_at": "2026-04-08 17:00:00"
    },
    "message": "差额已作废,结算单已完成"
}
```

**业务约束**:
- ✅ 需要超级管理员审批权限
- ✅ 只能作废partially_settled状态的差额

---

### 5.4 批量确认收款

**接口**: `POST /api/v2/settlements/batch-confirm`

**请求参数**:
```python
{
    "application_ids": List[int],
    "payment_method": str,  # 统一收款方式
    "note": Optional[str]
}
```

**响应格式**:
```python
{
    "success": True,
    "data": {
        "confirmed_count": 5,
        "failed_count": 0,
        "confirmed_applications": [
            {
                "id": 101,
                "receipt_no": "RC-20260408-0001",
                "amount": 135.00
            }
        ],
        "failed_applications": [],
        "total_amount": 675.00
    },
    "message": "批量收款确认完成: 5条成功, 0条失败, 总金额¥675.00"
}
```

---

## 六、月度结算管理API (新增)

### 6.1 创建月度结算单

**接口**: `POST /api/v2/monthly-settlements`

**请求参数**:
```python
{
    "settlement_period": str,  # 结算周期: YYYY-MM(如: 2026-04)
    "auto_generate": Optional[bool],  # 是否自动生成(可选)
    "note": Optional[str]
}
```

**响应格式**:
```python
{
    "success": True,
    "data": {
        "id": 201,
        "settlement_no": "MS-202604-0001",
        "settlement_period": "2026-04",
        "settlement_year": 2026,
        "settlement_month": 4,
        "start_date": "2026-04-01",
        "end_date": "2026-04-30",
        "office_count": 5,
        "record_count": 120,
        "total_amount": 1800.00,
        "status": "draft",
        
        # 办公室明细
        "office_details": [
            {
                "office_id": 101,
                "office_name": "A101办公室",
                "record_count": 23,
                "amount": 856.00,
                "status": "pending"
            }
        ],
        
        "created_at": "2026-04-30 18:00:00",
        "created_by_id": 301,
        "created_type": "manual"
    },
    "message": "月度结算单创建成功"
}
```

---

### 6.2 审核月度结算单

**接口**: `POST /api/v2/monthly-settlements/{settlement_id}/approve`

**响应格式**:
```python
{
    "success": True,
    "data": {
        "id": 201,
        "status": "pending_payment",
        
        # 生成的结算申请单
        "generated_applications": [
            {
                "application_id": 101,
                "office_id": 101,
                "amount": 856.00,
                "application_no": "SA-20260430-0001"
            }
        ]
    },
    "message": "月度结算单审核通过,已生成5个结算申请单"
}
```

---

### 6.3 获取月度结算单列表

**接口**: `GET /api/v2/monthly-settlements`

**请求参数**:
```python
{
    "settlement_period": Optional[str],
    "status": Optional[str],
    "year": Optional[int],
    "month": Optional[int],
    "page": int = 1,
    "page_size": int = 20
}
```

---

### 6.4 获取月度结算单详情

**接口**: `GET /api/v2/monthly-settlements/{settlement_id}`

---

## 七、统计查询API (新增)

### 7.1 获取全局结算统计

**接口**: `GET /api/v2/settlements/stats/global`

**请求参数**:
```python
{
    "start_date": Optional[str],
    "end_date": Optional[str],
    "settlement_period": Optional[str]
}
```

**响应格式**:
```python
{
    "success": True,
    "data": {
        # 记录数量统计
        "total_record_count": 238,
        "pending_record_count": 28,
        "applied_record_count": 15,
        "approved_record_count": 20,
        "settled_record_count": 175,
        
        # 金额统计
        "total_amount": 8560.00,
        "pending_amount": 980.00,
        "applied_amount": 520.00,
        "approved_amount": 700.00,
        "settled_amount": 7360.00,
        
        # 办公室统计
        "total_office_count": 45,
        "pending_office_count": 8,
        "applied_office_count": 5,
        "approved_office_count": 3,
        "fully_settled_office_count": 29,
        
        # 逾期统计
        "overdue_7days_count": 5,
        "overdue_7days_amount": 180.00,
        "overdue_15days_count": 2,
        "overdue_15days_amount": 85.00,
        "overdue_30days_count": 0,
        "overdue_30days_amount": 0
    }
}
```

---

### 7.2 获取办公室结算统计

**接口**: `GET /api/v2/settlements/stats/offices`

**请求参数**:
```python
{
    "start_date": Optional[str],
    "end_date": Optional[str],
    "office_id": Optional[int]
}
```

**响应格式**:
```python
{
    "success": True,
    "data": {
        "offices": [
            {
                "office_id": 101,
                "office_name": "A101办公室",
                "office_room_number": "A101",
                
                # 记录统计
                "total_record_count": 23,
                "pending_record_count": 0,
                "applied_record_count": 0,
                "settled_record_count": 23,
                
                # 金额统计
                "total_amount": 856.00,
                "pending_amount": 0,
                "settled_amount": 856.00,
                
                # 状态判断
                "has_pending": false,
                "has_applied": false,
                "is_fully_settled": true,
                
                # 最近领水时间
                "latest_pickup_time": "2026-04-07 16:20:00",
                
                # 最近结算时间
                "latest_settlement_time": "2026-04-09 10:30:00"
            }
        ]
    }
}
```

---

### 7.3 获取月度结算趋势

**接口**: `GET /api/v2/settlements/stats/trend`

**请求参数**:
```python
{
    "start_period": str,  # 开始周期: 2026-01
    "end_period": str  # 结束周期: 2026-04
}
```

**响应格式**:
```python
{
    "success": True,
    "data": {
        "trend": [
            {
                "period": "2026-01",
                "record_count": 180,
                "settled_amount": 6500.00,
                "pending_amount": 500.00,
                "office_count": 40
            },
            {
                "period": "2026-02",
                "record_count": 200,
                "settled_amount": 7200.00,
                "pending_amount": 600.00,
                "office_count": 42
            }
        ]
    }
}
```

---

## 八、提醒催款API (新增)

### 8.1 发送催款提醒

**接口**: `POST /api/v2/settlements/remind`

**请求参数**:
```python
{
    "office_ids": List[int],  # 办公室ID列表(可选)
    "pickup_ids": List[int],  # 领水记录ID列表(可选)
    "reminder_type": str,  # 提醒类型: friendly/formal/urgent
    "note": Optional[str]
}
```

**响应格式**:
```python
{
    "success": True,
    "data": {
        "reminded_count": 5,
        "failed_count": 0,
        "reminded_offices": [
            {
                "office_id": 101,
                "office_name": "A101办公室",
                "pending_amount": 280.00,
                "overdue_days": 8,
                "reminder_sent_at": "2026-04-08 18:00:00"
            }
        ]
    },
    "message": "催款提醒已发送给5个办公室"
}
```

---

### 8.2 获取催款提醒历史

**接口**: `GET /api/v2/settlements/remind/history`

**请求参数**:
```python
{
    "office_id": Optional[int],
    "start_date": Optional[str],
    "end_date": Optional[str],
    "page": int = 1,
    "page_size": int = 20
}
```

---

## 九、操作日志API (新增)

### 9.1 获取操作日志

**接口**: `GET /api/v2/settlements/logs`

**请求参数**:
```python
{
    "operation_type": Optional[str],  # 操作类型筛选
    "target_type": Optional[str],  # 目标类型筛选
    "target_id": Optional[int],  # 目标ID筛选
    "operator_id": Optional[int],  # 操作人ID筛选
    "start_date": Optional[str],
    "end_date": Optional[str],
    "page": int = 1,
    "page_size": int = 20
}
```

**响应格式**:
```python
{
    "success": True,
    "data": {
        "logs": [
            {
                "id": 1,
                "operation_type": "apply",
                "operation_status": "success",
                "target_type": "application",
                "target_id": 101,
                "old_status": null,
                "new_status": "applied",
                "operator_id": 201,
                "operator_name": "张经理",
                "operator_role": "office_manager",
                "operation_detail": {
                    "pickup_ids": [1, 2, 3],
                    "total_amount": 135.00
                },
                "note": "提交结算申请",
                "operated_at": "2026-04-08 14:30:00",
                "ip_address": "192.168.1.100",
                "device_info": "Chrome 120.0"
            }
        ],
        "pagination": {
            "total": 100,
            "page": 1,
            "page_size": 20,
            "total_pages": 5
        }
    }
}
```

---

## 十、错误处理机制

### 10.1 错误响应格式

**标准错误响应**:
```python
{
    "success": False,
    "error": {
        "code": "SETTLEMENT_001",
        "message": "结算申请失败",
        "detail": "领水记录ID 1 已经在其他结算申请单中",
        "timestamp": "2026-04-08 14:30:00",
        "path": "/api/v2/settlements/apply"
    }
}
```

---

### 10.2 错误代码定义

| 错误代码 | 错误说明 | HTTP状态码 |
|---------|---------|-----------|
| SETTLEMENT_001 | 结算申请失败 | 400 |
| SETTLEMENT_002 | 结算审核失败 | 400 |
| SETTLEMENT_003 | 结算确认失败 | 400 |
| SETTLEMENT_004 | 权限不足 | 403 |
| SETTLEMENT_005 | 记录不存在 | 404 |
| SETTLEMENT_006 | 状态不可修改 | 400 |
| SETTLEMENT_007 | 参数验证失败 | 400 |
| SETTLEMENT_008 | 金额计算错误 | 400 |
| SETTLEMENT_009 | 库存不足 | 400 |
| SETTLEMENT_010 | 数据库操作失败 | 500 |

---

### 10.3 异常处理示例

```python
from fastapi import HTTPException, status

class SettlementException(Exception):
    """结算业务异常"""
    def __init__(self, code, message, detail=None):
        self.code = code
        self.message = message
        self.detail = detail
        self.timestamp = datetime.now()
        super().__init__(self.message)

# 使用示例
async def apply_settlement(request: SettlementApplyRequest):
    try:
        # 业务逻辑
        if not validate_permission(user):
            raise SettlementException(
                code="SETTLEMENT_004",
                message="权限不足",
                detail="只有办公室负责人可以申请结算"
            )
        
        # ...
        
    except SettlementException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "success": False,
                "error": {
                    "code": e.code,
                    "message": e.message,
                    "detail": e.detail,
                    "timestamp": str(e.timestamp),
                    "path": request.path
                }
            }
        )
```

---

## 十一、API测试用例

### 11.1 正常流程测试

**测试场景**: 完整结算流程

```python
# 1. 创建领水记录
POST /api/v2/pickups
{
    "office_id": 101,
    "product_id": 1,
    "quantity": 3,
    "pickup_person": "张三"
}
# 响应: {"id": 1, "settlement_status": "pending"}

# 2. 申请结算
POST /api/v2/settlements/apply
{
    "office_id": 101,
    "pickup_ids": [1]
}
# 响应: {"id": 101, "application_no": "SA-20260408-0001", "status": "applied"}

# 3. 审核通过
POST /api/v2/settlements/101/approve
{}
# 响应: {"status": "approved"}

# 4. 确认收款
POST /api/v2/settlements/101/confirm
{
    "payment_method": "transfer",
    "payment_amount": 45.00
}
# 响应: {"status": "settled", "receipt_no": "RC-20260408-0001"}

# 5. 查询结果
GET /api/v2/settlements/101
# 响应: {"status": "settled", "items": [{"pickup_status": "settled"}]}
```

---

### 11.2 异常流程测试

**测试场景**: 权限验证

```python
# 普通用户尝试申请结算
POST /api/v2/settlements/apply
Headers: {"Authorization": "Bearer user_token"}
{
    "office_id": 101,
    "pickup_ids": [1]
}
# 响应: 
{
    "success": False,
    "error": {
        "code": "SETTLEMENT_004",
        "message": "权限不足",
        "detail": "只有办公室负责人可以申请结算"
    }
}
```

---

## 十二、总结

本API接口设计方案实现了：

### ✅ 完整的接口规范
- 清晰的接口路由设计
- 规范的请求响应格式
- 明确的错误处理机制

### ✅ 业务逻辑完整性
- 结算申请→审核→确认完整流程
- 批量操作支持
- 异常情况处理

### ✅ 数据准确性保证
- 状态一致性校验
- 金额计算验证
- 权限验证机制

### ✅ 版本兼容性
- v1版本保留兼容
- v2版本实现新功能
- 平滑迁移支持

---

**下一步**: 基于本API接口设计,编写前端交互设计文档(05-前端交互设计.md)。