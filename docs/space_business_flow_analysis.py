"""
空间预约管理模块业务流程完整性分析报告
=============================================
编制：首席产品经理
日期：2026-04-13

一、问题诊断
-------------

### 1. 发现的核心问题

**问题描述：Dashboard显示3个待审批，Approvals页面显示0条记录**

**根本原因：**
1. 数据来源不一致
   - Dashboard统计：`SpaceBooking.status='pending_approval'`
   - Approvals查询：`SpaceApproval.status='pending'`

2. 历史数据缺陷
   - 测试数据直接插入数据库，未经过API流程
   - 预约记录没有对应的审批记录

3. 业务逻辑矛盾
   - 会议室（requires_approval=0）预约状态却是pending_approval

### 2. 修复措施

已执行 `tools/fix_approvals_sync.py` 修复脚本：
- 为需要审批的预约创建审批记录：2条
- 修复会议室预约状态为confirmed：1条
- 数据已同步：pending_approval预约=2条，pending审批=2条


二、业务流程梳理
-----------------

### 1. 空间类型配置流程

| 空间类型 | type_code | requires_approval | 审批类型 | 押金要求 |
|---------|-----------|------------------|---------|---------|
| 会议室 | meeting_room | ❌ 否 | - | ❌ 无 |
| 会场 | auditorium | ✅ 是 | manager_approval | ✅ 30% |
| 大堂大屏 | lobby_screen | ✅ 是 | content_review | ❌ 无 |
| 大堂展位 | lobby_booth | ✅ 是 | plan_approval | ✅ 20% |
| VIP餐厅 | vip_dining | ❌ 否 | - | ❌ 无 |

**流程说明：**
- 会议室/VIP餐厅：用户预约后直接进入confirmed状态
- 会场/大屏/展位：用户预约后进入pending_approval状态，需审批

### 2. 用户预约流程

```
用户发起预约
    ↓
检查空间类型
    ↓
┌─────────────────────────────────────┐
│ requires_approval?                   │
│   ├─ No → confirmed状态 (直接确认)  │
│   ├─ Yes → pending_approval状态     │
│          ↓                          │
│          创建SpaceApproval记录       │
│          (status='pending')          │
└─────────────────────────────────────┘
```

**当前实现状态：**
✅ 创建预约API (POST /api/v2/space/bookings)
   - 正确判断requires_approval
   - pending_approval状态时创建审批记录
   - 计算费用、押金

⚠️ 待优化：
   - 押金支付流程未完整实现
   - 预约时间冲突检测可优化

### 3. 审批流程

```
管理员查看审批列表 (GET /api/v2/space/approvals)
    ↓
选择待审批记录 (status='pending')
    ↓
┌─────────────────────────────────────┐
│ 审批决策                             │
│   ├─ 通过 → approved状态             │
│   │        ↓                        │
│   │        预约状态 → approved       │
│   │        如需押金 → pending_payment│
│   │        否则 → confirmed          │
│   │                                  │
│   ├─ 拒绝 → rejected状态             │
│   │        ↓                        │
│   │        预约状态 → rejected       │
│   │        填写拒绝原因              │
│   │        推荐备选方案              │
│   │                                  │
│   ├─ 要求修改 → need_modify状态      │
│   │           ↓                     │
│   │           用户修改后重新提交     │
└─────────────────────────────────────┘
```

**当前实现状态：**
✅ 审批列表API (GET /api/v2/space/approvals)
✅ 审批通过API (PUT /api/v2/space/approvals/{id}/approve)
✅ 审批拒绝API (PUT /api/v2/space/approvals/{id}/reject)
   - 支持拒绝原因
   - 支持详细说明
   - 支持备选方案推荐
✅ 要求修改API (PUT /api/v2/space/approvals/{id}/request-modify)
✅ 批量审批API (POST /api/v2/space/approvals/batch-approve)

⚠️ 待优化：
   - 审批通知机制未完整实现
   - 审批超期处理未实现

### 4. 支付流程

```
审批通过
    ↓
检查requires_deposit
    ↓
┌─────────────────────────────────────┐
│ 需要押金？                           │
│   ├─ Yes → pending_payment状态      │
│   │        ↓                        │
│   │        用户支付押金              │
│   │        ↓                        │
│   │        payment_status='deposit_paid'│
│   │        ↓                        │
│   │        用户确认支付信息          │
│   │        (user_payment_confirmed) │
│   │        ↓                        │
│   │        管理员核实支付            │
│   │        (admin_payment_verified) │
│   │        ↓                        │
│   │        confirmed状态             │
│   │                                  │
│   ├─ No → 直接confirmed状态          │
└─────────────────────────────────────┘
```

**当前实现状态：**
⚠️ 部分实现
   - 数据模型已支持：payment_status, deposit_amount, user_payment_confirmed, admin_payment_verified
   - 支付确认流程未完整实现
   - 支付接口未对接

### 5. 使用流程

```
预约confirmed
    ↓
预约日期到达
    ↓
用户签到/入场
    ↓
┌─────────────────────────────────────┐
│ 使用中 (in_use)                      │
│   ↓                                  │
│ 使用结束                              │
│   ↓                                  │
│ 完成状态 (completed)                  │
└─────────────────────────────────────┘
```

**当前实现状态：**
⚠️ 部分实现
   - 状态模型支持：in_use, completed
   - 签到流程未实现
   - 自动完成机制未实现

### 6. 取消流程

```
用户/管理员取消预约
    ↓
检查预约状态
    ↓
┌─────────────────────────────────────┐
│ 状态判断                             │
│   ├─ pending_approval → cancelled    │
│   │   (无退款)                       │
│   │                                  │
│   ├─ confirmed/approved              │
│   │   ↓                              │
│   │   检查取消时间                    │
│   │   ↓                              │
│   │   ┌─────────────────────────┐   │
│   │   │ 退款规则                  │   │
│   │   │  ├─ 提前7天：全额退款     │   │
│   │   │  ├─ 提前3天：50%退款      │   │
│   │   │  ├─ 3天内：不退款         │   │
│   │   └─────────────────────────┘   │
│   │   ↓                              │
│   │   cancelled状态                   │
│   │   refunded状态(如退款)            │
└─────────────────────────────────────┘
```

**当前实现状态：**
✅ 取消API实现
⚠️ 退款规则未完整实现

### 7. 结算流程

```
预约completed
    ↓
等待结算周期
    ↓
生成结算单
    ↓
┌─────────────────────────────────────┐
│ 结算处理                             │
│   ├─ 计算最终费用                    │
│   ├─ 扣除押金(如有)                  │
│   ├─ 生成结算单                      │
│   ├─ settled状态                     │
└─────────────────────────────────────┘
```

**当前实现状态：**
⚠️ 部分实现
   - 数据模型支持：SpaceSettlement表
   - 自动结算机制未实现


三、数据一致性保障
-----------------

### 1. 核心数据表关系

```
SpaceType (空间类型)
    ↓ 1:N
SpaceResource (空间资源)
    ↓ 1:N
SpaceBooking (预约记录)
    ↓ 1:1
SpaceApproval (审批记录) ──→ 审批通过/拒绝影响预约状态
    ↓ 1:N
SpacePayment (支付记录)
    ↓ 1:1
SpaceSettlement (结算记录)
```

### 2. 状态同步规则

| 操作 | SpaceBooking状态变化 | SpaceApproval状态变化 |
|-----|---------------------|---------------------|
| 创建预约(需审批) | pending_approval | pending |
| 创建预约(无需审批) | confirmed | - |
| 审批通过 | approved → confirmed | approved |
| 审批拒绝 | rejected | rejected |
| 取消预约 | cancelled | cancelled |
| 完成使用 | completed | - |

### 3. 当前数据同步检查命令

```bash
# 检查数据一致性
sqlite3 data/app.db "
SELECT
    (SELECT COUNT(*) FROM space_bookings WHERE status='pending_approval') as pending_bookings,
    (SELECT COUNT(*) FROM space_approvals WHERE status='pending') as pending_approvals
"

# 结果应一致：pending_bookings = pending_approvals
```


四、页面功能完整性
------------------

### 1. 用户端页面

| 页面 | 路径 | 实现状态 | 功能 |
|-----|------|---------|------|
| 预约首页 | /portal/space/index.html | ✅ | 空间列表、预约入口 |
| 预约申请 | /portal/space/booking.html | ✅ | 创建预约申请 |
| 我的预约 | /portal/space/my-bookings.html | ✅ | 查看个人预约 |
| 预约详情 | /portal/space/booking-detail.html | ⚠️ | 预约详情(部分实现) |

### 2. 管理端页面

| 页面 | 路径 | 实现状态 | 功能 |
|-----|------|---------|------|
| Dashboard | /portal/admin/space/dashboard.html | ✅ | 统计概览、快捷入口 |
| 审批中心 | /portal/admin/space/approvals.html | ✅ | 审批列表、审批操作 |
| 预约管理 | /portal/admin/space/bookings.html | ✅ | 预约列表、状态管理 |
| 资源配置 | /portal/admin/space/resources.html | ✅ | 空间资源管理 |
| 统计分析 | /portal/admin/space/statistics.html | ✅ | 使用统计、收入报表 |

### 3. API接口完整性

| API | 方法 | 路径 | 实现状态 |
|-----|------|------|---------|
| 预约列表 | GET | /api/v2/space/bookings | ✅ |
| 创建预约 | POST | /api/v2/space/bookings | ✅ |
| 预约详情 | GET | /api/v2/space/bookings/{id} | ✅ |
| 修改预约 | PUT | /api/v2/space/bookings/{id} | ✅ |
| 取消预约 | PUT | /api/v2/space/bookings/{id}/cancel | ✅ |
| 完成预约 | PUT | /api/v2/space/bookings/{id}/complete | ✅ |
| 审批列表 | GET | /api/v2/space/approvals | ✅ |
| 审批通过 | PUT | /api/v2/space/approvals/{id}/approve | ✅ |
| 审批拒绝 | PUT | /api/v2/space/approvals/{id}/reject | ✅ |
| 要求修改 | PUT | /api/v2/space/approvals/{id}/request-modify | ✅ |
| 批量审批 | POST | /api/v2/space/approvals/batch-approve | ✅ |
| Dashboard统计 | GET | /api/v2/space/statistics/dashboard | ✅ |
| 资源列表 | GET | /api/v2/space/resources | ✅ |
| 类型列表 | GET | /api/v2/space/types | ⚠️ |


五、待完善功能清单
-----------------

### P0 - 核心流程(必须完善)

1. **支付流程完整实现**
   - 押金支付接口
   - 支付确认流程
   - 支付状态同步

2. **通知机制**
   - 审批结果通知(邮件/短信/app)
   - 预约状态变更通知
   - 使用提醒通知

3. **数据一致性校验**
   - 定时任务检查booking与approval状态同步
   - 异常数据自动修复

### P1 - 重要功能(建议完善)

4. **签到/入场流程**
   - 签到API
   - 签到记录表
   - 实时使用状态

5. **自动完成机制**
   - 使用结束自动完成
   - 定时任务检测

6. **退款流程**
   - 退款规则执行
   - 退款记录
   - 押金退还

7. **结算自动化**
   - 定时生成结算单
   - 批量结算
   - 结算对账

### P2 - 增强功能(可选)

8. **审批超期处理**
   - 超期提醒
   - 自动通过/拒绝规则

9. **预约日历视图**
   - 日历展示预约
   - 资源占用可视化

10. **报表导出**
    - 预约记录导出
    - 收入报表导出
    - 使用率报表


六、结论与建议
--------------

### 当前系统状态

**总体评估：核心流程已实现 70%**

✅ 已完成：
- 基础数据模型设计完整
- 预约创建流程完整
- 审批流程完整
- 基础页面功能完整
- 数据修复机制可用

⚠️ 待完善：
- 支付流程（关键缺失）
- 通知机制（影响用户体验）
- 签到流程（影响实际运营）
- 结算流程（影响财务处理）

### 立即行动建议

1. **执行数据修复**
   - 运行 `tools/fix_approvals_sync.py`
   - 定期检查数据一致性

2. **完善支付流程**
   - 实现押金支付API
   - 完善支付确认流程

3. **实现通知机制**
   - 接入邮件/短信服务
   - 实现事件通知队列

4. **优化Dashboard统计**
   - 统一数据来源
   - 增加数据校验

### 下一步工作优先级

P0 (本周)：
- 支付流程实现
- 通知机制接入

P1 (下周)：
- 签到流程实现
- 结算自动化

P2 (后续)：
- 报表导出
- 日历视图
- 超期处理

"""

# 导出报告
with open(
    "/Users/sgl/PycharmProjects/AIchanyejiqun/docs/space_business_flow_analysis.md", "w"
) as f:
    f.write(__DOC__)

print("业务流程分析报告已生成: docs/space_business_flow_analysis.md")
