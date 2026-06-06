# 余额登记与线下结算改善计划

> 日期：2026-05-26 | 定位：内部登记管理系统 | 资金不经过系统，线下由业主方收取

---

## 一、背景与定位

### 1.1 系统定位

本系统定位为**业主方内部空间/用水服务登记管理工具**：
- 用户预约/使用服务 → 系统记录费用 → 余额账面扣减
- 用户实际付款 → **线下支付给业主方** → 管理员在系统录入充值/确认收款
- 系统收入 → 与业主方单独结算SaaS服务费，与系统内金额无关

### 1.2 当前系统概要

| 模块 | 状态 | 说明 |
|------|------|------|
| UserBalanceAccount 模型 | ✅ 已有 | membership/service/gift 三种余额 + 冻结 + 统计 |
| BalanceTransaction 模型 | ✅ 已有 | 完整流水记录，含前后余额快照 |
| BalanceDeductRecord 模型 | ✅ 已有 | 抵扣记录，区分会员/服务/赠送/现金 |
| 管理员余额调整 API | ✅ 已有 | `/admin/balance/adjust`、`/gift`、accounts/stats/transactions |
| 用户余额查询 API | ✅ 已有 | `/balance/my`、transactions、deduct-records、summary |
| 空间预约余额抵扣 | ✅ 已有 | balance_deduct模式，会员→服务→赠送优先级扣减 |
| 管理员余额管理页面 | ✅ 已有 | 统计+账户列表+调整/赠送弹窗+交易记录 |
| 用户余额页面 | ⚠️ 基础 | portal/balance.html 存在但功能有限 |
| 用水服务余额抵扣 | ❌ 缺失 | 用水服务使用独立SQLite DB + 水票数量体系，未接入统一余额 |
| 用水统一钱包 API | ⚠️ 独立运行 | `apps/water/api_unified.py` 使用独立 `waterms.db`，与主应用DB隔离 |
| 兼容层 | ❌ 存根 | `apps/api/v1/unified_compat.py` 所有余额字段硬编码返回 0 |
| UserSpaceQuota 管理 API | ❌ 缺失 | 模型存在但无CRUD API，免费额度管理不可用 |
| UserMemberInfo 管理 API | ❌ 缺失 | 模型存在(discount_rate/free_hours)，但无管理API |
| User.balance_credit 字段 | ⚠️ 遗留 | `shared/models/water/user.py` 中字段存在但从未被新API更新 |
| 线上支付网关集成 | ✅ 无需 | 无支付宝/微信SDK集成，符合线下定位 |

---

## 二、问题清单

### 2.1 术语合规问题（P0 - 法律风险）

当前系统多处使用金融/支付相关术语，与"内部登记管理"定位不符。

| 当前术语 | 出现位置 | 建议术语 | 优先级 |
|---------|---------|---------|--------|
| "充值" | 全局多处 | "余额登记" / "额度录入" | P0 |
| "支付" | booking.html, payment.html | "确认预约" / "记账确认" | P0 |
| "余额支付" | booking.html | "余额抵扣" / "额度扣减" | P0 |
| "在线支付" | 多处 | "线下结算" | P0 |
| "押金" | space_booking模型 | "预约保证金登记" | P0 |
| "退款" | admin_balance API | "退还登记" / "额度退回" | P0 |
| "结算" | 全局多处 | "使用确认" / "费用确认" | P0 |
| "账单" | credit-notes | "使用明细" / "费用清单" | P0 |
| "微信支付"/"支付宝" | payment.html, membership-plans | "联系管理员线下付款" | P0 |
| "银行转账" | membership-orders | "线下付款" | P1 |

### 2.2 架构层面问题

#### 2.2.1 用水服务使用独立数据库
- **问题**: `apps/water/` 的 `models_unified.py` 使用独立 SQLite 数据库 `waterms.db`，与主应用数据库 `app.db` 物理隔离
- **影响**: `UserBalanceAccount`（在主DB）和 `AccountWallet`（在waterms.db）无法在同一事务中操作
- **需要**: 将用水钱包迁移到主数据库，或至少通过 API 层统一余额视图

#### 2.2.2 兼容层是存根
- **文件**: `apps/api/v1/unified_compat.py`
- **问题**: `get_user_balance` 端点硬编码返回所有余额为 0（`prepaid_remaining: 0, credit_remaining: 0`）
- **需要**: 对接真实的 `UserBalanceAccount` 和 `AccountWallet` 数据

#### 2.2.3 User 模型遗留字段
- **文件**: `shared/models/water/user.py`
- **问题**: `balance_credit` 字段（Float）存在但从被新API更新，前后端读取不一致
- **需要**: 废弃或迁移到 `UserBalanceAccount`

### 2.3 管理员余额管理功能完善（P1）

#### 2.3.1 缺少用户搜索器
- **问题**: 调整/赠送弹窗只能输入数字 User ID，管理员不知道用户ID
- **现状**: `balance-manage.html` 只有 `input type=number` 输入 user_id
- **需要**: 带搜索的下拉选择器，支持按姓名/手机号搜索用户

#### 2.3.2 缺少"线下充值确认"专用工作流
- **问题**: 管理员用 `adjust` 接口（设计用于修正错误）和 `gift` 接口（设计用于赠送）来完成充值录入，语义混淆
- **需要**: 专门的 `POST /admin/balance/recharge` 端点，完整记录：充值用户、金额、余额类型、线下支付方式（银行转账/微信/现金）、凭证编号、备注、操作管理员
- **区别**: adjust = 纠错调整（可正可负），gift = 赠送（不关联用户付款），recharge = 线下充值确认（用户已付款给业主方）

#### 2.3.3 缺少批量充值/调整
- **问题**: 只能逐个用户调整，无法批量录入
- **需要**: 批量充值导入（Excel/CSV上传或粘贴解析）

#### 2.3.4 缺少余额过期预警
- **问题**: `membership_expire_date` 字段存在但无任何提醒
- **需要**: 在管理页面标注即将过期的会员余额，自动提醒

### 2.4 用户端功能完善（P1）

#### 2.4.1 用水服务未接入余额抵扣
- **问题**: 空间预约已支持余额抵扣，但用水服务使用独立的水票/办公室账户体系，未接入统一余额
- **文件**: `apps/water/` 下所有API使用 `OfficeAccount`/`OfficeRecharge`/`Transaction` 而非 `UserBalanceAccount`
- **需要**:
  1. 用水订单创建时检查 `UserBalanceAccount` 余额
  2. 用水消费时生成 `BalanceDeductRecord`
  3. 统一用户在空间和水服务的余额视图

#### 2.4.2 用户余额页面功能不完整
- **问题**: `portal/balance.html` 只能查看余额，缺少操作引导
- **需要**:
  - 显示"如何充值"引导（联系管理员、线下付款方式说明）
  - 显示扣除优先级说明（会员余额 → 服务余额 → 赠送余额 → 记账）
  - 显示余额使用明细（按服务类型分类：空间预约/用水）
  - 余额不足提醒

#### 2.4.3 预约页面余额展示优化
- **文件**: `space-frontend/booking.html`
- **问题**: 余额充足/不足/无余额三种状态显示较混乱
- **需要**:
  - 余额充足时：绿色提示"本次预约将使用余额 ¥X.XX"
  - 余额不足时：橙色提示"余额不足，请联系管理员线下充值后预约，或使用记账模式"
  - 外部用户：提示"外部访客请线下支付给管理员"

#### 2.4.4 缺少"我的余额明细"在空间前端
- **问题**: `space-frontend/my-bookings.html` 没有余额入口
- **需要**: 在"我的"页面增加余额卡片入口

### 2.5 记账（Credit）模式完善（P1）

#### 2.5.1 记账额度限制缺失
- **问题**: `credit` 模式无额度上限，任何人都可无限记账
- **需要**: 为每个用户/办公室设置记账额度上限（如每个办公室每月5000元）

#### 2.5.2 记账账单生成缺失
- **问题**: `credit_note_id` 和 `deduct_record_id` 字段存在但 `credit-notes.html` 页面内容很少（仅9处余额相关）
- **需要**: 记账账单自动生成，管理员可查看/导出记账明细

### 2.6 数据报表与分析（P2）

#### 2.6.1 财务统计报表缺失
- **需要**:
  - 管理员：按月份统计充值总额、抵扣总额、记账总额
  - 管理员：按用户统计余额、充值记录、消费记录
  - 管理员：按服务类型统计（空间 vs 用水）消费分布
  - 管理员：导出报表（Excel/CSV）

#### 2.6.2 余额变动通知缺失
- **问题**: 管理员调整余额后，用户无任何通知
- **需要**: 余额变动时创建系统通知（已有 `system_notifications` 功能可直接复用）

### 2.7 用户套餐购买与余额关联（P2）

#### 2.7.1 会员套餐购买后未自动充值余额
- **文件**: `portal/membership-plans.html`, `portal/membership-orders.html`
- **问题**: 用户购买会员套餐后，`balance_added` 显示金额但实际是否调用 balance API 不确定
- **需要**: 确认 `admin_membership_order.py` 中是否在确认订单时调用 `UserBalanceAccount` 增加余额

#### 2.7.2 套餐购买引导线下支付
- **问题**: `membership-plans.html` 仍有"微信支付"按钮和二维码图片
- **需要**: 改为"联系我们线下付款"引导，扫码加微信沟通（信息性，非支付功能）

### 2.8 审计与合规（P2）

#### 2.8.1 管理员操作日志不完整
- **问题**: `BalanceTransaction` 有 `admin_id` 字段，但缺少操作IP、操作类型细分
- **需要**: 增强审计日志，记录每次余额操作的IP地址和完整上下文

#### 2.8.2 用户余额对账功能缺失
- **需要**: 用户可查看"我的余额变动时间线"，类似银行流水
- **需要**: 用户可对异常余额变动提出异议（标记/反馈机制）

---

## 三、功能改善清单

### Phase 1: 术语合规整改（P0）— 预计1天

#### 3.1.1 后端 Schema/API 术语修改

**文件**: `shared/schemas/space/space_payment.py`
- `SpacePaymentConfirmOffline` → 已是offline，保持不变
- 确认 API 文档中的描述文字不含"在线支付"

**文件**: `apps/api/v1/admin_balance.py`
- `adjust_balance` endpoint description: "管理员调整用户余额" → "管理员录入/修正额度登记"
- `gift_balance` endpoint description: "赠送余额" → 保持不变（赠送是合理的）
- **新增**: `POST /admin/balance/recharge` — "线下充值确认"专用端点
  ```python
  class RechargeConfirmRequest(BaseModel):
      user_id: int
      amount: float
      balance_type: str = "membership"  # membership/service
      payment_method: str = "offline"   # bank_transfer/wechat/cash
      payment_reference: Optional[str]  # 凭证编号/截图文件名
      notes: Optional[str]
  ```

**文件**: `shared/models/space/space_booking.py`
- `requires_deposit`/`deposit_amount`/`deposit_paid` 字段注释: 添加"预约保证金登记(非金融押金)"
- `payment_status` config: "待支付" → "待确认"

#### 3.1.2 前端术语修改

**文件**: `portal/admin/balance-manage.html`
- 页面标题 "余额管理" → "额度管理"
- "调整余额" → "额度调整"  
- "赠送余额" → "赠送额度"
- 新增 "充值确认" 按钮（调用新的 /recharge 端点）
- "会员余额"/"服务余额"/"赠送余额" → 保持不变（这些是内部分类，可接受）

**文件**: `space-frontend/booking.html`
- "记账模式" → 保持不变（这是合理的记账描述）
- "预付模式" → "线下预付确认"
- "余额抵扣" → "额度扣减"
- "外部访客需线下付费" → 保持不变

**文件**: `portal/membership-plans.html`
- 移除微信支付/支付宝按钮
- 改为 "联系管理员开通" + 显示联系方式（从系统配置读取）

**文件**: `portal/payment.html`
- 移除"微信扫码支付"相关UI
- 改为"线下付款指引"页面

**文件**: `portal/faq.html` / `portal/help.html`
- 更新支付方式描述，移除"线上支付"相关

### Phase 2: 管理员功能完善（P1）— 预计2-3天

#### 3.2.1 用户搜索选择器

**文件**: `portal/admin/balance-manage.html`
- 替换 `adjustForm.user_id` 的 `input type=number` 为搜索下拉组件
- API: `GET /api/v1/admin/users?search=xxx` 或复用现有用户搜索
- 下拉列表显示：姓名、手机号、当前余额

#### 3.2.2 线下充值确认专用页面/弹窗

**文件**: `portal/admin/balance-manage.html`
- 新增 "充值确认" 按钮和弹窗
- 表单字段：
  - 用户选择（搜索+自动完成）
  - 充值金额
  - 余额类型（会员/服务）
  - 线下支付方式（银行转账/微信/现金）
  - 支付凭证编号（可选）
  - 备注
  - 过期日期（会员余额可选）
- 调用新 `POST /admin/balance/recharge` 端点

**后端新增**: `apps/api/v1/admin_balance.py`
- `POST /admin/balance/recharge` 端点
  - 增加余额（仅正数）
  - 生成 `TransactionType.MEMBERSHIP_CHARGE` 或 `SERVICE_CHARGE`
  - 记录操作管理员和线下支付信息
  - 发送通知给用户

#### 3.2.3 余额过期预警

**文件**: `portal/admin/balance-manage.html`
- 统计卡片增加"即将过期余额"指标
- 账户列表标注即将过期的记录（黄色/红色标记）
- 可筛选"30天内过期"的账户

#### 3.2.4 批量导入充值

**文件**: `portal/admin/balance-manage.html`
- 新增 "批量录入" 按钮
- 支持粘贴 TSV/CSV 格式：用户ID/手机号,金额,类型,备注
- 预览+确认流程
- 后端: `POST /admin/balance/batch-recharge`

### Phase 3: 架构整合 — 统一数据库 + 消灭存根（P0）— 预计1-2天

#### 3.3.1 用水钱包迁移到主数据库
**文件**: `apps/water/models_unified.py`
- 将 `UserAccount`、`AccountWallet`、`TransactionV2` 等表从 `waterms.db` 迁移到主 `app.db`
- 更新数据库连接配置，统一使用主数据库 engine

#### 3.3.2 兼容层对接真实数据
**文件**: `apps/api/v1/unified_compat.py`
- `get_user_balance` 从硬编码 0 改为读取真实 `UserBalanceAccount` + `AccountWallet`
- 确保前后端数据一致

#### 3.3.3 废弃遗留字段
**文件**: `shared/models/water/user.py`
- `balance_credit` 字段标记为 deprecated
- 所有读取改为从 `UserBalanceAccount` 获取

### Phase 4: 用水服务接入统一余额（P1）— 预计2-3天

#### 3.4.1 用水订单余额抵扣

**文件**: `apps/water/api_unified_order.py` 或对应的订单创建API
- 用水订单创建/确认时：
  - 检查用户 `UserBalanceAccount` 余额
  - 如果有余额，优先抵扣
  - 生成 `BalanceDeductRecord`（order_type="water"）
  - 更新 `UserBalanceAccount`

#### 3.4.2 用水管理后台余额视图

**文件**: `apps/water/frontend/admin.html` 或 `admin-unified.html`
- 用户详情中显示用户统一余额
- 水票/预付费领取时可选择余额抵扣

#### 3.4.3 余额扣除优先级统一

确保用水和空间使用相同的扣除优先级：会员余额 → 服务余额 → 赠送余额 → 记账

### Phase 5: 用户端体验优化（P1）— 预计2天

#### 5.1.1 用户余额页面增强

**文件**: `portal/balance.html`
- 添加充值引导区："如何充值？联系您的管理员进行线下充值"
- 显示扣除优先级说明
- 按服务类型分类显示交易记录（空间预约/用水/会员充值）
- 余额不足预警提示

#### 5.1.2 空间前端余额入口

**文件**: `space-frontend/my-bookings.html`
- 顶部增加余额卡片
- 显示可用余额（区分会员/服务/赠送）

#### 5.1.3 预约页面余额引导优化

**文件**: `space-frontend/booking.html`
- 根据不同用户类型和余额情况显示差异化引导：
  - 内部员工有余额：绿色显示抵扣金额
  - 内部员工余额不足：提示联系管理员充值
  - 外部访客：提示线下支付

### Phase 6: 报表与通知（P2）— 预计2-3天

#### 5.1 财务统计页面

**文件**: 新建 `portal/admin/balance-report.html`
- 月度余额变动统计图
- 按服务类型消费分布
- 用户充值排行
- 导出CSV功能

#### 5.2 余额变动通知

**文件**: `apps/api/v1/admin_balance.py`
- 在 `adjust`/`recharge`/`gift` 操作后调用通知服务
- 通知内容："管理员已为您[充值/调整] ¥XXX 到[会员/服务]余额"
- 通知渠道：系统内通知（已有）+ 可选短信

### Phase 7: 记账额度与账单（P2）— 预计2天

#### 6.1 记账额度管理

**文件**: `shared/models/space/` 新建或扩展现有模型
- 为办公室/用户配置记账额度上限
- 预约时检查是否超出额度
- 管理员可调整额度

#### 6.2 记账账单生成

**文件**: `portal/admin/space/credit-notes.html`
- 按月份/办公室生成记账汇总
- 列表 + 详情 + 导出

---

## 四、文件修改总清单

| 优先级 | 文件 | 操作 | 说明 |
|--------|------|------|------|
| P0 | `shared/schemas/space/space_payment.py` | 修改 | API文档描述术语修正 |
| P0 | `shared/models/space/space_booking.py` | 修改 | 字段注释修正 |
| P0 | `portal/admin/balance-manage.html` | 修改 | 术语修正 + 新增充值确认弹窗 |
| P0 | `space-frontend/booking.html` | 修改 | 术语修正 + 余额引导优化 |
| P0 | `portal/membership-plans.html` | 修改 | 移除线上支付UI |
| P0 | `portal/payment.html` | 修改 | 改为线下付款指引 |
| P0 | `portal/faq.html` | 修改 | 更新支付方式描述 |
| P0 | `portal/help.html` | 修改 | 更新支付方式描述 |
| P1 | `apps/api/v1/admin_balance.py` | 新增端点 | `POST /recharge` + `POST /batch-recharge` |
| P1 | `apps/api/v1/admin_balance.py` | 新增端点 | `GET /users/search` 用户搜索 |
| P1 | `portal/admin/balance-manage.html` | 修改 | 用户搜索选择器 + 批量导入 |
| P1 | `apps/water/api_unified_order.py` | 修改 | 接入UserBalanceAccount余额抵扣 |
| P1 | `apps/water/services/transaction_service.py` | 修改 | 生成BalanceDeductRecord |
| P1 | `portal/balance.html` | 修改 | 完整余额管理体验 |
| P1 | `space-frontend/my-bookings.html` | 修改 | 增加余额卡片 |
| P2 | `portal/admin/balance-report.html` | **新建** | 财务统计报表 |
| P2 | `portal/admin/space/credit-notes.html` | 修改 | 记账账单功能 |
| P2 | `shared/services/space/booking_status_service.py` | 修改 | 余额变动通知触发 |

---

## 五、数据库变更

### 5.1 新增字段

**BalanceTransaction 表**:
```sql
ALTER TABLE balance_transactions ADD COLUMN payment_method VARCHAR(20);
ALTER TABLE balance_transactions ADD COLUMN payment_reference VARCHAR(100);
ALTER TABLE balance_transactions ADD COLUMN operator_ip VARCHAR(45);
```

### 5.2 新增表

**credit_limit 表**（记账额度配置）:
```sql
CREATE TABLE credit_limits (
    id INTEGER PRIMARY KEY,
    user_id INTEGER,
    office_id INTEGER,
    monthly_limit DECIMAL(10,2),
    current_used DECIMAL(10,2),
    limit_month VARCHAR(7),
    created_at DATETIME,
    updated_at DATETIME
);
```

---

## 六、实施优先级与预估工期

| Phase | 内容 | 优先级 | 预估工期 | 累计 |
|-------|------|--------|---------|------|
| Phase 1 | 术语合规整改 | P0 | 1天 | 1天 |
| Phase 2 | 管理员功能完善 | P1 | 2-3天 | 4天 |
| Phase 3 | 架构整合 — 统一DB+消灭存根 | P0 | 1-2天 | 6天 |
| Phase 4 | 用水服务接入统一余额 | P1 | 2-3天 | 9天 |
| Phase 5 | 用户端体验优化 | P1 | 2天 | 11天 |
| Phase 6 | 报表与通知 | P2 | 2-3天 | 14天 |
| Phase 7 | 记账额度与账单 | P2 | 2天 | 16天 |

---

## 七、免责声明

本文档中的法律合规分析仅供参考，不构成正式法律意见。涉及合规的具体决策，建议咨询专业律师。系统的术语调整和功能改善旨在降低合规风险，不能完全消除所有潜在法律风险。
