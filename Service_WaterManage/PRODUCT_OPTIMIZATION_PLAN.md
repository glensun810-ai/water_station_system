# 水站管理系统 - 双模式业务优化方案

## 📋 文档信息

| 项目 | 内容 |
|------|------|
| **版本** | v1.0 |
| **创建日期** | 2026-03-24 |
| **文档作者** | 产品经理专家 |
| **状态** | 待实施 |

---

## 🎯 项目背景

### 当前问题

1. **文案不准确**：
   - "待结算" → 应改为 "待支付"（更准确反映用户视角）
   - "已结算" → 应改为 "已支付待确认"（明确状态流转）

2. **业务模式单一**：
   - 目前仅支持"先领用后结算"模式
   - 缺乏"先预定后领取"的预付费模式
   - 无法针对不同模式设置差异化优惠

### 业务需求

作为水站管理方，需要支持两种不同的业务模式，并可针对每种模式设置独立的优惠策略：

| 模式 | 特点 | 适用场景 | 优惠策略 |
|------|------|----------|----------|
| **先用后付** | 领取时不扣库存，后续统一结算 | 短期用水、临时需求 | 标准价格，无买赠优惠 |
| **先付后用** | 先支付预定，按量分批领取 | 长期用水、计划性需求 | 可享受买 N 赠 M 优惠 |

---

## 🏗️ 整体优化方案

### 一、文案优化（Phase 1）

#### 1.1 前端文案修改

| 位置 | 原文案 | 新文案 | 说明 |
|------|--------|--------|------|
| 领水 Tab 状态卡片 | 待结算 | 待支付 | 用户视角更清晰 |
| 领水 Tab 状态卡片 | 已结算 | 已支付待确认 | 明确需要管理员确认 |
| 结算 Tab 标题 | 待结算 | 待支付 | 保持一致 |
| 结算 Tab 状态标签 | 待结算 | 待支付 | 保持一致 |
| 结算 Tab 状态标签 | 已申请待确认 | 已支付待确认 | 保持一致 |
| 记录 Tab 状态标签 | ⏰ 待结算 | ⏰ 待支付 | 保持一致 |
| 记录 Tab 状态标签 | ⏳ 已申请待确认 | ⏳ 已支付待确认 | 保持一致 |

#### 1.2 后端 API 返回文案

- 保持数据结构不变
- 前端根据 `settlement_applied` 字段显示对应文案

---

### 二、双模式业务设计（Phase 2）

#### 2.1 模式定义

```
┌─────────────────────────────────────────────────────────────┐
│                    业务模式对比                              │
├─────────────────┬─────────────────┬─────────────────────────┤
│     维度        │   先用后付模式   │    先付后用模式          │
├─────────────────┼─────────────────┼─────────────────────────┤
│ 流程            │ 领水→结算→支付   │ 支付预定→领水→核销       │
│ 库存扣减        │ 领水时扣减       │ 预定时冻结，领水时扣减    │
│ 支付时点        │ 结算时支付       │ 预定时支付               │
│ 优惠策略        │ 标准价（无买赠）  │ 可配置买 N 赠 M           │
│ 适用产品        │ 所有产品         │ 可配置特定产品           │
│ 退款处理        │ 不支持           │ 支持未使用部分退款       │
└─────────────────┴─────────────────┴─────────────────────────┘
```

#### 2.2 状态机设计

**先用后付模式状态流转：**
```
[未结算] → [待支付] → [已支付待确认] → [已完成]
    ↓           ↓            ↓
  领水      用户申请      管理员确认
```

**先付后用模式状态流转：**
```
[未预定] → [已预定待领取] → [已领取] → [已完成]
    ↓            ↓             ↓
  支付预定      扫码领水      自动核销
```

#### 2.3 数据库扩展设计

##### 2.3.1 新增优惠配置表

```sql
CREATE TABLE promotion_config (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL,
    mode VARCHAR(20) NOT NULL DEFAULT 'pay_later',  -- 'pay_later' 或 'prepay'
    trigger_qty INTEGER NOT NULL DEFAULT 10,        -- 买 N
    gift_qty INTEGER NOT NULL DEFAULT 0,            -- 赠 M
    discount_rate DECIMAL(5,2) DEFAULT 100,         -- 折扣率（百分比）
    is_active INTEGER DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(id)
);
```

##### 2.3.2 扩展 Transaction 表

```sql
ALTER TABLE transactions ADD COLUMN mode VARCHAR(20) DEFAULT 'pay_later';
-- 'pay_later': 先用后付
-- 'prepay': 先付后用

ALTER TABLE transactions ADD COLUMN reserved_qty INTEGER DEFAULT 0;
-- 预定时预留的数量

ALTER TABLE transactions ADD COLUMN used_qty INTEGER DEFAULT 0;
-- 已使用的数量（用于分次领取）

ALTER TABLE transactions ADD COLUMN payment_status VARCHAR(20) DEFAULT 'unpaid';
-- 'unpaid': 未支付
-- 'paid': 已支付
-- 'refunded': 已退款
```

##### 2.3.3 新增预定领取记录表

```sql
CREATE TABLE reservation_pickups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    reservation_id INTEGER NOT NULL,
    pickup_qty INTEGER NOT NULL,
    picked_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    picked_by INTEGER NOT NULL,
    status VARCHAR(20) DEFAULT 'completed',
    FOREIGN KEY (reservation_id) REFERENCES transactions(id),
    FOREIGN KEY (picked_by) REFERENCES users(id)
);
```

#### 2.4 后端 API 扩展

##### 2.4.1 优惠配置 API

```python
# 获取产品优惠配置（按模式）
GET /api/promotions/config?product_id={id}&mode={mode}

# 设置产品优惠配置
POST /api/promotions/config
{
    "product_id": 1,
    "mode": "prepay",          # pay_later 或 prepay
    "trigger_qty": 10,
    "gift_qty": 1,
    "discount_rate": 100,
    "is_active": 1
}

# 批量设置产品优惠
POST /api/promotions/batch
{
    "configs": [
        {"product_id": 1, "mode": "pay_later", "trigger_qty": 10, "gift_qty": 0},
        {"product_id": 1, "mode": "prepay", "trigger_qty": 10, "gift_qty": 1}
    ]
}
```

##### 2.4.2 预定 API

```python
# 创建预定订单
POST /api/reservation/create
{
    "user_id": 1,
    "product_id": 1,
    "quantity": 20,
    "mode": "prepay"
}

# 确认定金/全款支付
POST /api/reservation/pay
{
    "reservation_id": 1,
    "payment_method": "credit"  # 挂账/线下/在线
}

# 领取预定的水
POST /api/reservation/pickup
{
    "reservation_id": 1,
    "pickup_qty": 5
}

# 查询预定余额
GET /api/reservation/{user_id}/balance
```

#### 2.5 前端 UI 扩展

##### 2.5.1 领水页面改造

```
┌────────────────────────────────────────────┐
│  💧 领水                                    │
├────────────────────────────────────────────┤
│  ┌─────────────┬─────────────┐             │
│  │  🔄 先用后付 │  💳 先付后用 │  ← Tab 切换  │
│  └─────────────┴─────────────┘             │
├────────────────────────────────────────────┤
│  快捷操作（根据模式显示不同优惠信息）          │
│  ┌────┐ ┌────┐ ┌────┐ ┌────┐              │
│  │ ×1 │ │ ×2 │ │ ×5 │ │记录│              │
│  └────┘ └────┘ └────┘ └────┘              │
├────────────────────────────────────────────┤
│  状态卡片                                   │
│  ┌──────────┬──────────┬──────────┐        │
│  │ 本月已领 │  待支付   │已支付待确认│       │
│  │   10 桶   │  ¥50.00  │  ¥100.00 │       │
│  └──────────┴──────────┴──────────┘        │
├────────────────────────────────────────────┤
│  产品列表（显示对应模式的优惠）               │
│  ┌────────────────────────────────────┐    │
│  │ 桶装水 18L                          │    │
│  │ 库存：50 桶  |  ¥5.00/桶           │    │
│  │ 🏷️ 先用后付：标准价                │    │
│  │ 🏷️ 先付后用：买 10 赠 1              │    │
│  └────────────────────────────────────┘    │
└────────────────────────────────────────────┘
```

##### 2.5.2 管理后台扩展

**产品管理 Tab 新增优惠配置：**

```
┌─────────────────────────────────────────────┐
│  产品管理 > 优惠配置                          │
├─────────────────────────────────────────────┤
│  产品：桶装水 18L                             │
├─────────────────────────────────────────────┤
│  ┌─────────────────────────────────────┐   │
│  │ 🔄 先用后付模式                       │   │
│  │ ┌────────────┬────────────┐         │   │
│  │ │ 买 N       │ 赠 M        │         │   │
│  │ │ [  10  ]   │ [  0  ]    │  ℹ️标准价│   │
│  │ └────────────┴────────────┘         │   │
│  └─────────────────────────────────────┘   │
│  ┌─────────────────────────────────────┐   │
│  │ 💳 先付后用模式                       │   │
│  │ ┌────────────┬────────────┐         │   │
│  │ │ 买 N       │ 赠 M        │         │   │
│  │ │ [  10  ]   │ [  1  ]    │  ℹ️优惠 │   │
│  │ └────────────┴────────────┘         │   │
│  └─────────────────────────────────────┘   │
└─────────────────────────────────────────────┘
```

---

## 📅 分步骤实施计划

### Phase 1: 文案优化（优先级：高，预计工时：2 小时）

| 步骤 | 任务 | 文件 | 详细说明 |
|------|------|------|----------|
| 1.1 | 代码备份 | - | 备份 frontend/index.html 和 backend/main.py |
| 1.2 | 修改领水 Tab 状态卡片 | frontend/index.html | 待结算→待支付，已结算→已支付待确认 |
| 1.3 | 修改结算 Tab 标题和标签 | frontend/index.html | 统一文案 |
| 1.4 | 修改记录 Tab 状态标签 | frontend/index.html | 统一文案 |
| 1.5 | 验证修改 | 浏览器测试 | 检查所有界面文案 |

### Phase 2: 双模式核心功能（优先级：中，预计工时：2 天）

| 步骤 | 任务 | 文件 | 详细说明 |
|------|------|------|----------|
| 2.1 | 数据库迁移 | backend/migrate.py | 创建 promotion_config 表，扩展 transactions 表 |
| 2.2 | 后端模型扩展 | backend/main.py | 新增 PromotionConfig 模型 |
| 2.3 | 优惠计算逻辑 | backend/main.py | 根据模式计算优惠价格 |
| 2.4 | 优惠配置 API | backend/main.py | CRUD API |
| 2.5 | 管理后台 UI | frontend/admin.html | 产品优惠配置界面 |
| 2.6 | 领水模式切换 | frontend/index.html | Tab 切换 UI |
| 2.7 | 预定流程 API | backend/main.py | 预定/领取/核销 API |
| 2.8 | 预定流程 UI | frontend/index.html | 预定界面 |

### Phase 3: 测试与优化（优先级：中，预计工时：1 天）

| 步骤 | 任务 | 说明 |
|------|------|------|
| 3.1 | 单元测试 | 测试优惠计算逻辑 |
| 3.2 | 集成测试 | 测试完整流程 |
| 3.3 | 性能测试 | 并发场景测试 |
| 3.4 | 用户验收测试 | 实际用户测试 |

---

## 🔒 风险控制

### 数据兼容性

1. **向后兼容**：
   - 现有 transaction 记录默认 `mode='pay_later'`
   - 现有产品自动创建默认优惠配置

2. **数据迁移**：
   - 迁移脚本需要可回滚
   - 迁移前完整备份数据库

### Bug 预防

1. **代码审查**：
   - 所有修改需要双人审查
   - 关键逻辑添加单元测试

2. **灰度发布**：
   - 先在小范围测试
   - 确认无问题后全量发布

---

## 📊 成功指标

| 指标 | 目标值 | 测量方式 |
|------|--------|----------|
| 文案准确率 | 100% | 人工检查 |
| 功能完整性 | 100% | 测试用例覆盖 |
| Bug 数量 | 0 严重 Bug | 测试报告 |
| 用户满意度 | >90% | 用户反馈 |

---

## 📝 附录

### A. 数据库迁移 SQL

```sql
-- 1. 创建优惠配置表
CREATE TABLE IF NOT EXISTS promotion_config (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL,
    mode VARCHAR(20) NOT NULL DEFAULT 'pay_later',
    trigger_qty INTEGER NOT NULL DEFAULT 10,
    gift_qty INTEGER NOT NULL DEFAULT 0,
    discount_rate DECIMAL(5,2) DEFAULT 100,
    is_active INTEGER DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(id)
);

-- 2. 扩展 transactions 表
ALTER TABLE transactions ADD COLUMN mode VARCHAR(20) DEFAULT 'pay_later';
ALTER TABLE transactions ADD COLUMN reserved_qty INTEGER DEFAULT 0;
ALTER TABLE transactions ADD COLUMN used_qty INTEGER DEFAULT 0;
ALTER TABLE transactions ADD COLUMN payment_status VARCHAR(20) DEFAULT 'unpaid';

-- 3. 创建预定领取记录表
CREATE TABLE IF NOT EXISTS reservation_pickups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    reservation_id INTEGER NOT NULL,
    pickup_qty INTEGER NOT NULL,
    picked_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    picked_by INTEGER NOT NULL,
    status VARCHAR(20) DEFAULT 'completed',
    FOREIGN KEY (reservation_id) REFERENCES transactions(id),
    FOREIGN KEY (picked_by) REFERENCES users(id)
);

-- 4. 初始化现有产品的优惠配置
INSERT INTO promotion_config (product_id, mode, trigger_qty, gift_qty)
SELECT id, 'pay_later', promo_threshold, promo_gift FROM products;

INSERT INTO promotion_config (product_id, mode, trigger_qty, gift_qty)
SELECT id, 'prepay', promo_threshold, promo_gift FROM products;
```

### B. API 变更清单

| 变更类型 | API 路径 | 说明 |
|----------|----------|------|
| 新增 | GET /api/promotions/config | 获取优惠配置 |
| 新增 | POST /api/promotions/config | 设置优惠配置 |
| 新增 | POST /api/reservation/create | 创建预定 |
| 新增 | POST /api/reservation/pay | 支付预定 |
| 新增 | POST /api/reservation/pickup | 领取预定 |
| 修改 | GET /api/user/{user_id}/status | 新增预定余额字段 |
| 修改 | POST /api/record | 支持 mode 参数 |

---

**文档结束**
