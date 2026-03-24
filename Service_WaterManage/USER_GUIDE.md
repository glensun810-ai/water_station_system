# 水站管理系统 - 双模式功能使用指南

## 🎯 功能概述

系统现已支持两种业务模式：

| 模式 | 特点 | 优惠 | 适用场景 |
|------|------|------|----------|
| **🔄 先用后付** | 领取后统一结算 | 标准价格 | 临时用水、短期需求 |
| **💳 先付后用** | 先支付后领取 | 买 N 赠 M | 长期用水、计划性需求 |

---

## 📱 用户端使用

### 1. 选择模式

打开领水页面，在顶部选择模式：

```
┌─────────────────────────────────────┐
│  🔄 先用后付    │  💳 先付后用      │
└─────────────────────────────────────┘
```

### 2. 领取水

**快捷领取：**
- 点击"桶装水 ×1"或"桶装水 ×2"快速领取
- 系统会根据选择的模式计算价格

**选择规格领取：**
1. 浏览产品列表
2. 使用 +/- 选择数量
3. 点击"确认领取"

### 3. 查看优惠

**先用后付模式：**
```
桶装水 18L
💰 先用后付：标准价格
预计支付：¥16.80
```

**先付后用模式：**
```
桶装水 18L
✨ 先付后用：买 10 赠 1
预计支付：¥15.40 (含优惠)
```

### 4. 查看状态

状态卡片显示：
```
┌──────────┬──────────┬──────────────┐
│ 本月已领 │  待支付   │ 已支付待确认 │
│   10 桶   │ ¥50.00   │   ¥100.00    │
└──────────┴──────────┴──────────────┘
```

---

## 💼 管理端使用

### 1. 配置优惠策略

**API 方式配置：**

```bash
# 设置产品 3 的先付后用优惠（买 10 赠 1）
curl -X POST http://localhost:8000/api/promotions/config \
  -H "Content-Type: application/json" \
  -d '{
    "product_id": 3,
    "mode": "prepay",
    "trigger_qty": 10,
    "gift_qty": 1,
    "is_active": 1
  }'

# 设置产品 3 的先用后付优惠（标准价格）
curl -X POST http://localhost:8000/api/promotions/config \
  -H "Content-Type: application/json" \
  -d '{
    "product_id": 3,
    "mode": "pay_later",
    "trigger_qty": 10,
    "gift_qty": 0,
    "is_active": 1
  }'
```

**批量配置：**

```bash
curl -X POST http://localhost:8000/api/promotions/batch \
  -H "Content-Type: application/json" \
  -d '{
    "configs": [
      {"product_id": 3, "mode": "pay_later", "trigger_qty": 10, "gift_qty": 0},
      {"product_id": 3, "mode": "prepay", "trigger_qty": 10, "gift_qty": 1},
      {"product_id": 4, "mode": "pay_later", "trigger_qty": 10, "gift_qty": 0},
      {"product_id": 4, "mode": "prepay", "trigger_qty": 5, "gift_qty": 1}
    ]
  }'
```

### 2. 查询优惠配置

```bash
# 查询所有优惠配置
curl http://localhost:8000/api/promotions/config

# 查询指定产品的优惠配置
curl http://localhost:8000/api/promotions/config/3
```

### 3. 预定功能（需登录）

**创建预定订单：**
```bash
curl -X POST http://localhost:8000/api/reservation/create \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "product_id": 3,
    "pickup_qty": 20
  }'
```

**查询预定余额：**
```bash
curl http://localhost:8000/api/reservation/{user_id}/balance
```

**领取预定：**
```bash
curl -X POST http://localhost:8000/api/reservation/pickup \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "reservation_id": 1,
    "pickup_qty": 5
  }'
```

---

## 🔍 常见问题

### Q1: 两种模式有什么区别？
- **先用后付**：先领取，后续统一结算，标准价格
- **先付后用**：先支付预定，然后分次领取，享受优惠价格

### Q2: 如何切换模式？
在领水页面顶部，点击模式切换按钮即可。

### Q3: 先付后用如何享受优惠？
选择"先付后用"模式后，系统自动应用买 N 赠 M 优惠。
例如：买 10 赠 1，领取 12 桶时，只需支付 11 桶的费用。

### Q4: 预定后如何领取？
预定后，在领水页面选择相应数量领取即可。
（完整功能开发中）

### Q5: 如何管理优惠配置？
目前通过 API 配置，管理后台界面开发中。

---

## 📞 技术支持

遇到问题请查看：
- `IMPLEMENTATION_REPORT.md` - 实施报告
- `PRODUCT_OPTIMIZATION_PLAN.md` - 产品优化方案

---

**最后更新**: 2026-03-24
