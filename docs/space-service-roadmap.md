# 空间服务系统 — 当前状态与下一步规划

> 审计日期: 2026-05-26 | 分支: feature/refactor-cleanup

## 当前完成度评估

| 模块 | 完成度 | 说明 |
|------|--------|------|
| 核心预约生命周期 | 95% | 创建→审批→确认→激活→完成→结算，全链路通畅 |
| 多单位差异化预约 | 90% | hour/half_day/session/slot/day/week/month/meal 全部支持 |
| 用户端前端 | 85% | 10页面，9个完整，profile页有3个stub |
| 管理后台 | 90% | 8页面全部功能完整，仅发票按钮为stub |
| 定价与费用计算 | 90% | 三级定价+免费额度+余额抵扣，缺少发票 |
| 结算与对账 | 80% | 双路径结算可用，缺自动化定时任务和PDF报告 |
| 通知系统 | 30% | 仅3个触发点，审批/支付/结算事件均未接入 |
| 统计与分析 | 60% | API完备，前端仅表格，无图表可视化 |
| 代码健康度 | 70% | ~25% SpaceBooking字段未使用，2个model是死代码 |

**总评：核心业务闭环完整，可以支撑日常运营。当前阶段从"功能建设"转向"完善与优化"。**

---

## Phase 4: 财务闭环（优先级最高 — 直接影响合规与收入）

### 4.1 发票管理模块
- 新建 `portal/admin/space/invoices.html` — 发票申请列表 + 开具/寄送管理
- 新建 `space-frontend/invoice-apply.html` — 用户申请开票
- 后端：复用现有 `models/invoice.py`，新增 `GET/POST/PUT /api/v2/space/invoices`
- `SpaceBooking` 已有 `invoice_requested`/`invoice_status`/`invoice_id` 字段，打通即可

### 4.2 定时任务自动化
- 每月1日自动执行 `POST /payment/monthly-settlement` 生成月度账单
- 每月定时重置 `UserSpaceQuota.free_quota_used`（月度免费额度刷新）
- 过期未支付预约自动取消（cron job）

### 4.3 支付确认流程完善
- 管理员 verify payment 时实际调用 `create_notification()` 通知用户
- 支付完成/退款完成触发通知

---

## Phase 5: 运营体验（中优先级 — 提升管理效率与数据可见性）

### 5.1 统计可视化
- `dashboard.html` 加入 Chart.js 图表：近30天预约趋势折线图、资源类型占比饼图
- `statistics.html` 加入：时段热力图、资源利用率柱状图
- 用户端 `index.html` 加入个人使用趋势迷你图

### 5.2 通知系统全覆盖
- 审批通过/驳回 → 通知申请人
- 支付验证通过/失败 → 通知用户
- 结算完成 → 通知用户
- 预约即将开始（提前1小时）→ 提醒通知
- 删除死代码 `shared/models/space/notification.py`（从未使用）

### 5.3 用户端补全
- `profile.html` 3个stub：编辑个人信息、支付记录、帮助中心
- 新增发票申请页（见4.1）

---

## Phase 6: 代码健康与体验优化（低优先级 — 长期维护）

### 6.1 死代码清理
- 删除 `SpaceSettlement` model（`space_settlements` 表从未读写，已被 CreditNote + unified_settlement 替代）
- 删除 `shared/models/space/notification.py`（API 使用 system_notifications 表）
- 清理 `SpaceBooking` 中未使用的字段（`checked_in_*`、`rated_*`、`calendar_invite_*`、`content_*`、`exhibition_*` 等 ~15个字段）

### 6.2 评价与反馈系统
- `SpaceBooking` 已有 `rating_score`/`rating_feedback`/`rated_at` 字段
- 新增 `POST /api/v2/space/bookings/{id}/rate` — 用户完成预约后评价
- 管理后台展示评价数据

### 6.3 日历集成
- 预约确认后生成 iCal 文件供下载
- `SpaceBooking` 已有 `calendar_invite_sent`/`calendar_invite_id` 字段

---

## 建议执行优先级

| 优先级 | 任务 | 理由 |
|--------|------|------|
| **P0** | 发票管理（前后端+打通model） | 直接影响收入合规，用户强需求 |
| **P0** | 月度定时任务（结算+额度刷新） | 当前需手动执行，运营风险 |
| **P1** | 通知系统全覆盖 | 用户体验断层明显，3个触发点太少 |
| **P1** | 统计图表可视化 | 管理员数据决策依赖 |
| **P1** | profile.html 3个stub | 用户端唯一不完整页面 |
| **P2** | 死代码清理 | 降低维护成本 |
| **P2** | 评价系统 | 激活已有字段，获取用户反馈 |
| **P3** | 日历集成 | 锦上添花，提升专业感 |
