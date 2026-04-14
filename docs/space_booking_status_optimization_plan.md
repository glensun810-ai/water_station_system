# 空间服务预约状态值优化完善计划

**编制日期：2026-04-14**  
**问题发现：confirmed与approved状态混淆，需要系统性梳理**

---

## 一、现状分析

### 1.1 状态定义现状

#### 预约状态（BookingStatus）

**定义位置：** `shared/models/space/space_booking.py:24-35`

```python
class BookingStatus(str, enum.Enum):
    pending_approval = "pending_approval"  # 待审批
    approved = "approved"                  # 已通过
    rejected = "rejected"                  # 已拒绝
    deposit_paid = "deposit_paid"          # 已付押金
    confirmed = "confirmed"                # 已确认
    cancelled = "cancelled"                # 已取消
    in_use = "in_use"                      # 使用中
    completed = "completed"                # 已完成
    settled = "settled"                    # 已结算
```

#### 审批状态（ApprovalStatus）

**定义位置：** `shared/models/space/space_approval.py:14-20`

```python
class ApprovalStatus(str, enum.Enum):
    pending = "pending"          # 待审批
    approved = "approved"        # 已通过
    rejected = "rejected"        # 已拒绝
    need_modify = "need_modify"  # 需要修改
```

### 1.2 实际使用的状态值

**数据库查询结果：**
- cancelled
- completed
- confirmed
- rejected

**问题：** 数据库中没有出现 `pending_approval`, `approved`, `in_use`, `settled` 状态，说明：
1. 状态流转未完整实现
2. 测试数据可能未覆盖完整流程

### 1.3 状态业务逻辑梳理

#### 当前实现的流程

| 状态 | 业务含义 | 触发场景 | 允许操作 | 实现状态 |
|-----|---------|---------|---------|---------|
| pending_approval | 待审批 | 创建需审批的预约 | 修改、取消 | ✅ 已实现 |
| approved | 审批通过（中间态） | 管理员审批通过 | 取消、完成 | ⚠️ 混淆 |
| confirmed | 最终确认 | 无需审批直接确认<br>需审批且支付确认 | 取消、完成 | ⚠️ 混淆 |
| rejected | 已拒绝 | 管理员拒绝 | 无 | ✅ 已实现 |
| cancelled | 已取消 | 用户/管理员取消 | 无 | ✅ 已实现 |
| deposit_paid | 已付押金 | 用户支付押金 | 无 | ❌ 未实现 |
| in_use | 使用中 | 用户签到入场 | 完成 | ❌ 未实现 |
| completed | 已完成 | 使用结束/管理员完成 | 无 | ✅ 已实现 |
| settled | 已结算 | 财务结算完成 | 无 | ❌ 未实现 |

#### 状态变化规则

**代码位置：** `apps/api/v2/space_bookings.py`

```
创建预约流程：
  需要审批 → pending_approval (创建SpaceApproval记录)
  无需审批 → confirmed (直接确认)

审批流程：
  pending_approval → approved (审批通过，如需押金等待支付)
  approved → confirmed (支付确认后)
  pending_approval → rejected (审批拒绝)

使用流程：
  confirmed → in_use (用户签到) ❌未实现
  in_use → completed (使用结束) ❌未实现
  
  或直接：
  confirmed → completed (管理员手动完成) ✅已实现

取消流程：
  任意活跃状态 → cancelled (用户/管理员取消)

结算流程：
  completed → settled (财务结算) ❌未实现
```

---

## 二、核心问题诊断

### 2.1 approved 与 confirmed 混淆问题

**问题描述：**

1. **approved（审批通过）** - 应作为中间过渡状态
   - 业务含义：管理员已批准预约申请
   - 后续流程：需等待支付押金（如需要）或其他确认步骤
   - 当前实现：审批通过后直接转为confirmed（如无需押金）

2. **confirmed（最终确认）** - 应作为稳定可执行状态
   - 业务含义：预约已最终确认，可以开始执行
   - 用户期望：看到"已确认"表示预约成功
   - 当前实现：审批通过和直接确认都用此状态

**代码证据：**

`apps/api/v2/space_approvals.py:196-264` 审批通过逻辑：
```python
approval.status = "approved"
if booking:
    booking.status = "approved"  # ← 预约变为approved
    
    if booking.requires_deposit:
        next_action = {"action": "pay_deposit", ...}
    else:
        booking.status = "confirmed"  # ← 如无需押金，立即变为confirmed
        booking.confirmed_at = datetime.now()
```

**问题影响：**

- 用户可能看到"已通过"和"已确认"两个相似状态，容易混淆
- 管理员看到"approved"状态时，不确定是否需要支付确认
- 状态含义不清晰，影响用户体验和运营效率

### 2.2 deposit_paid 状态未真正使用

**定义了但未实现：**
- 枚举中定义了 `deposit_paid` 状态
- 数据库字段有 `payment_status`、`deposit_paid` 等
- 实际流程中：支付后直接进入 `confirmed`，未经过 `deposit_paid` 状态

**缺失流程：**
```
需押金的预约：
approved → deposit_paid (用户支付押金) → confirmed (支付确认)
```

### 2.3 in_use 状态缺失实现

**定义了但未实现：**
- 预约已确认，使用日期到达，应有"使用中"状态
- 签到功能未实现（`checked_in_at` 字段存在但无API）
- 实际管理困难：不清楚预约是否正在使用

### 2.4 settled 状态缺失实现

**定义了但未实现：**
- 预约完成后应有结算流程
- 结算功能部分实现（有结算表但未完整流程）
- 财务管理困难：不清楚哪些预约已结算

### 2.5 状态冲突检测问题

**代码位置：** `apps/api/v2/space_bookings.py:178-188`

当前冲突检测包含的状态：
```python
SpaceBooking.status.in_([
    "pending_approval", 
    "approved", 
    "confirmed", 
    "in_use", 
    "completed"  # ← 包含completed，可能有问题
])
```

**问题：**
- `completed` 状态的预约不应参与冲突检测（已结束使用）
- 应排除的历史状态：`cancelled`, `rejected`, `completed`

---

## 三、优化完善方案

### 3.1 状态语义明确化

#### 方案A：保留双状态体系（推荐）

**优点：**
- approved 和 confirmed 各有清晰职责
- 支持复杂审批+支付流程
- 状态层次分明

**状态定义：**

| 状态 | 层级 | 业务含义 | 后续状态 | 显示文案 |
|-----|------|---------|---------|---------|
| pending_approval | 审批层 | 等待审批 | approved/rejected | "待审批" |
| approved | 审批层 | 审批通过，待支付 | deposit_paid/confirmed | "审批通过，待支付" |
| deposit_paid | 支付层 | 已付押金，待确认 | confirmed | "已付押金，待确认" |
| confirmed | 执行层 | 最终确认可执行 | in_use/cancelled | "已确认" |
| in_use | 执行层 | 正在使用中 | completed | "使用中" |
| completed | 结算层 | 使用完成 | settled | "已完成" |
| settled | 结算层 | 已结算 | - | "已结算" |
| cancelled | 结束层 | 已取消 | - | "已取消" |
| rejected | 结束层 | 已拒绝 | - | "已拒绝" |

**状态流转图：**

```
┌─────────────────────────────────────────────────────┐
│                     创建预约                          │
│   ├─ 无需审批 → confirmed (直接确认)                 │
│   ├─ 需审批 → pending_approval                      │
└─────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────┐
│                     审批流程                          │
│   ├─ 通过 → approved                                │
│   │    ├─ 需押金 → 等待支付                         │
│   │    │    ↓                                       │
│   │    │    deposit_paid (用户支付)                 │
│   │    │    ↓                                       │
│   │    │    confirmed (支付确认)                    │
│   │    │                                            │
│   │    ├─ 无需押金 → confirmed (直接确认)           │
│   │                                                 │
│   ├─ 拒绝 → rejected                                │
│   ├─ 要求修改 → pending_approval (用户重新提交)     │
└─────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────┐
│                     使用流程                          │
│   confirmed → in_use (签到入场)                     │
│   in_use → completed (使用结束)                     │
│                                                     │
│   或简化流程：                                       │
│   confirmed → completed (管理员手动完成)             │
└─────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────┐
│                     结算流程                          │
│   completed → settled (财务结算)                    │
└─────────────────────────────────────────────────────┘

任意时刻可取消：
pending_approval/approved/deposit_paid/confirmed → cancelled
```

#### 方案B：合并approved到confirmed

**优点：**
- 状态数量减少，简化管理
- 对用户更直观

**缺点：**
- 无法区分审批通过但未支付的状态
- 复杂流程无法支持

**不建议采用，因为：**
- 会丢失业务细节
- 无法支持押金支付流程

### 3.2 状态显示优化

**前端显示规则：**

```javascript
const statusDisplayMap = {
  pending_approval: {
    text: "待审批",
    color: "warning",
    icon: "⏳",
    description: "您的预约正在等待管理员审批",
    userActions: ["修改", "取消"],
    adminActions: ["审批通过", "审批拒绝", "要求修改"]
  },
  
  approved: {
    text: "审批通过",
    color: "success",
    icon: "✓",
    description: "审批已通过，请完成支付以确认预约",
    userActions: ["支付押金", "取消"],
    adminActions: ["确认支付", "取消"]
  },
  
  deposit_paid: {
    text: "已付押金",
    color: "info",
    icon: "💳",
    description: "已支付押金，等待最终确认",
    userActions: ["确认支付信息", "取消"],
    adminActions: ["核实支付", "确认", "取消"]
  },
  
  confirmed: {
    text: "已确认",
    color: "primary",
    icon: "✅",
    description: "预约已确认，请按时到场使用",
    userActions: ["取消"],
    adminActions: ["签到", "完成", "取消"]
  },
  
  in_use: {
    text: "使用中",
    color: "info",
    icon: "🎯",
    description: "预约正在使用中",
    userActions: [],
    adminActions: ["完成"]
  },
  
  completed: {
    text: "已完成",
    color: "default",
    icon: "📋",
    description: "预约已完成，等待结算",
    userActions: ["评价"],
    adminActions: ["结算"]
  },
  
  settled: {
    text: "已结算",
    color: "default",
    icon: "💰",
    description: "预约已完成结算",
    userActions: ["查看结算详情"],
    adminActions: []
  },
  
  cancelled: {
    text: "已取消",
    color: "danger",
    icon: "✗",
    description: "预约已取消",
    userActions: [],
    adminActions: []
  },
  
  rejected: {
    text: "已拒绝",
    color: "danger",
    icon: "✗",
    description: "预约申请已拒绝",
    userActions: ["查看拒绝原因", "重新预约"],
    adminActions: []
  }
};
```

### 3.3 状态冲突检测优化

**正确规则：**

```python
# 参与冲突检测的状态（活跃预约）
ACTIVE_STATUSES = ["pending_approval", "approved", "deposit_paid", "confirmed", "in_use"]

# 不参与冲突检测的状态（已结束）
FINISHED_STATUSES = ["completed", "settled", "cancelled", "rejected"]

# 可修改的状态
MODIFIABLE_STATUSES = ["pending_approval"]

# 可取消的状态
CANCELABLE_STATUSES = ["pending_approval", "approved", "deposit_paid", "confirmed"]

# 可完成的状态
COMPLETABLE_STATUSES = ["confirmed", "in_use"]
```

---

## 四、实施计划

### 4.1 P0 - 立即修复（本周）

#### 任务1：状态冲突检测修复

**文件：** `apps/api/v2/space_bookings.py`

**修改点：**
- Line 183-184: 创建预约冲突检测
- Line 317-318: 修改预约冲突检测

**修改内容：**
```python
# 原代码（错误）
SpaceBooking.status.in_([
    "pending_approval", "approved", "confirmed", "in_use", "completed"
])

# 新代码（正确）
SpaceBooking.status.in_([
    "pending_approval", "approved", "deposit_paid", "confirmed", "in_use"
])
# 排除completed，因为已完成的预约不应冲突
```

#### 任务2：状态显示优化

**文件：** 
- `portal/admin/space/bookings.html`
- `space-frontend/calendar.html`

**修改内容：**
- 为approved状态增加特殊显示："审批通过，待支付"
- 为deposit_paid状态增加显示（如适用）
- 优化状态颜色和图标

#### 任务3：API完善

**新增API：**
```python
# 签到API
@router.put("/{booking_id}/check-in")
async def check_in_booking(booking_id: int, db: Session, user: User):
    """用户签到入场"""
    booking = db.query(SpaceBooking).filter(SpaceBooking.id == booking_id).first()
    if not booking:
        raise HTTPException(404, "预约不存在")
    if booking.status != "confirmed":
        raise HTTPException(400, "只能签到已确认的预约")
    if booking.booking_date != date.today():
        raise HTTPException(400, "只能在预约日期签到")
    
    booking.status = "in_use"
    booking.checked_in_at = datetime.now()
    booking.checked_in_by = user.name
    db.commit()
    return ApiResponse(message="签到成功")

# 支付确认API
@router.put("/{booking_id}/confirm-payment")
async def confirm_payment(booking_id: int, payment_data: dict, db: Session, user: User):
    """确认支付"""
    booking = db.query(SpaceBooking).filter(SpaceBooking.id == booking_id).first()
    if booking.status != "deposit_paid":
        raise HTTPException(400, "只能确认已付押金的预约")
    
    booking.status = "confirmed"
    booking.user_payment_confirmed = True
    booking.user_payment_confirmed_at = datetime.now()
    db.commit()
    return ApiResponse(message="支付已确认")
```

### 4.2 P1 - 重要完善（下周）

#### 任务4：支付流程完整实现

**实现内容：**
- 用户支付押金API
- 支付状态变更逻辑：approved → deposit_paid → confirmed
- 支付确认流程

#### 任务5：签到流程实现

**实现内容：**
- 签到API（见任务3）
- 签到记录表
- 自动状态变更：confirmed → in_use

#### 任务6：自动完成机制

**实现内容：**
- 定时任务：检测已过期预约，自动完成
- 使用结束时间检测
- 状态变更：in_use → completed

### 4.3 P2 - 增强完善（后续）

#### 任务7：结算流程实现

**实现内容：**
- 结算API
- 状态变更：completed → settled
- 结算单生成

#### 任务8：数据迁移

**迁移脚本：**
```python
# tools/migrate_booking_status.py

# 1. 修复approved状态的预约
for booking in db.query(SpaceBooking).filter(SpaceBooking.status == "approved"):
    if booking.requires_deposit and not booking.deposit_paid:
        # 需押金但未支付，保持approved状态
        continue
    else:
        # 无需押金或已支付，转为confirmed
        booking.status = "confirmed"
        booking.confirmed_at = booking.approved_at or datetime.now()
        booking.confirmed_by = booking.approved_by or "system"

# 2. 为pending_approval预约创建审批记录（如缺失）
for booking in db.query(SpaceBooking).filter(SpaceBooking.status == "pending_approval"):
    approval = db.query(SpaceApproval).filter(SpaceApproval.booking_id == booking.id).first()
    if not approval:
        approval = SpaceApproval(
            booking_id=booking.id,
            status="pending",
            approval_type="booking_approval",
            submitted_at=booking.created_at
        )
        db.add(approval)

db.commit()
```

---

## 五、测试验证计划

### 5.1 状态流转测试

**测试场景：**

1. **无需审批的预约**
   ```
   创建 → confirmed（直接确认） → completed
   ```

2. **需审批无押金的预约**
   ```
   创建 → pending_approval → approved → confirmed → completed
   ```

3. **需审批有押金的预约**
   ```
   创建 → pending_approval → approved → deposit_paid → confirmed → in_use → completed → settled
   ```

4. **取消流程**
   ```
   各活跃状态 → cancelled（测试退款逻辑）
   ```

5. **拒绝流程**
   ```
   pending_approval → rejected
   ```

### 5.2 冲突检测测试

**测试用例：**

1. 相同时间段创建预约 → 应拒绝（冲突）
2. completed状态的旧预约，新预约使用相同时间 → 应允许（不冲突）
3. cancelled状态的预约，新预约使用相同时间 → 应允许（不冲突）

### 5.3 状态一致性测试

**验证规则：**

```sql
-- pending_approval预约必须有审批记录
SELECT COUNT(*) FROM space_bookings b
WHERE b.status = 'pending_approval'
AND NOT EXISTS (
    SELECT 1 FROM space_approvals a 
    WHERE a.booking_id = b.id AND a.status = 'pending'
);

-- approved预约必须有审批通过记录
SELECT COUNT(*) FROM space_bookings b
WHERE b.status = 'approved'
AND NOT EXISTS (
    SELECT 1 FROM space_approvals a 
    WHERE a.booking_id = b.id AND a.status = 'approved'
);

-- 结果应为0（表示数据一致）
```

---

## 六、文档更新计划

### 6.1 API文档更新

**文件：** `docs/api/space_booking_api.md`

**更新内容：**
- 状态定义说明
- 状态流转规则
- 各状态允许的操作

### 6.2 用户手册更新

**文件：** `docs/user_guide/space_booking_guide.md`

**更新内容：**
- 用户看到的状态含义
- 各状态下的可操作项
- 流程说明（审批、支付、签到）

### 6.3 运维手册更新

**文件：** `docs/ops_guide/space_booking_ops.md`

**更新内容：**
- 状态管理规则
- 异常状态处理
- 数据一致性检查

---

## 七、总结

### 7.1 核心问题总结

1. **approved vs confirmed 混淆**
   - approved应作为审批通过的中间状态
   - confirmed应作为最终确认的稳定状态
   - 需明确各自职责，不应混用

2. **状态定义但未实现**
   - deposit_paid：支付流程缺失
   - in_use：签到流程缺失
   - settled：结算流程缺失

3. **冲突检测包含completed**
   - completed预约不应参与冲突检测
   - 会阻止新预约使用已结束的时间段

### 7.2 优化收益

**业务收益：**
- 状态语义清晰，提升用户体验
- 支持完整业务流程（审批→支付→使用→结算）
- 状态管理规范，提升运营效率

**技术收益：**
- 数据一致性提升
- 状态流转可控
- 易于维护和扩展

**风险控制：**
- 避免状态冲突导致预约混乱
- 支付流程规范，降低财务风险
- 结算流程完整，提升财务管理

### 7.3 实施优先级

| 优先级 | 任务 | 预计工时 | 完成时间 |
|--------|------|---------|---------|
| P0 | 冲突检测修复 | 2小时 | 本周二 |
| P0 | 状态显示优化 | 4小时 | 本周三 |
| P0 | API完善（签到/支付确认） | 8小时 | 本周五 |
| P1 | 支付流程实现 | 16小时 | 下周三 |
| P1 | 签到流程实现 | 8小时 | 下周五 |
| P1 | 自动完成机制 | 8小时 | 下周五 |
| P2 | 结算流程实现 | 16小时 | 后续 |
| P2 | 数据迁移 | 4小时 | 后续 |

---

**建议：立即启动P0任务，本周内完成核心修复。**