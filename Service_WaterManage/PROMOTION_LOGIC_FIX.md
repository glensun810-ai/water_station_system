# 预付费充值买赠逻辑修复报告

## 🔴 问题描述

用户反馈：配置"买十赠一"优惠方案时，充值 10 个应该赠送 1 个 (总共 11 个),但实际没有赠送。

---

## ✅ 问题分析

### 错误的计算逻辑 (修复前)

```python
# api_unified.py Line 275-277 (旧代码)
cycle = config.trigger_qty + config.gift_qty  # 10 + 1 = 11
free_quantity = (request.quantity // cycle) * config.gift_qty
```

**举例**: 买 10 赠 1, 充值 10 个
- `cycle = 10 + 1 = 11`
- `free_quantity = (10 // 11) * 1 = 0` ❌ **没有赠送!**

**问题根源**: 
- 旧逻辑理解错误，把"买 N 赠 M"理解为"每满 (N+M) 个才赠送 M 个"
- 实际上应该是"每买 N 个就赠送 M 个"

### 正确的计算逻辑 (修复后)

```python
# api_unified.py Line 275-278 (新代码)
# 买 N 赠 M: 每买 trigger_qty 个，就赠送 gift_qty 个
# 例如：买 10 赠 1，充值 10 个 → 赠送 1 个；充值 20 个 → 赠送 2 个
free_quantity = (request.quantity // config.trigger_qty) * config.gift_qty
```

**举例**: 买 10 赠 1, 充值 10 个
- `free_quantity = (10 // 10) * 1 = 1` ✅ **正确赠送 1 个!**

---

## 📊 测试用例对比

### 场景 1: 买 10 赠 1, 充值 10 个

| 项目 | 旧逻辑 | 新逻辑 | 期望值 |
|------|--------|--------|--------|
| 付费数量 | 10 | 10 | 10 |
| 赠送数量 | 0 ❌ | 1 ✅ | 1 |
| 总数量 | 10 | 11 ✅ | 11 |

### 场景 2: 买 10 赠 1, 充值 20 个

| 项目 | 旧逻辑 | 新逻辑 | 期望值 |
|------|--------|--------|--------|
| 付费数量 | 20 | 20 | 20 |
| 赠送数量 | 1 ❌ | 2 ✅ | 2 |
| 总数量 | 21 | 22 ✅ | 22 |

### 场景 3: 买 10 赠 1, 充值 15 个

| 项目 | 旧逻辑 | 新逻辑 | 期望值 |
|------|--------|--------|--------|
| 付费数量 | 15 | 15 | 15 |
| 赠送数量 | 1 ✅ | 1 ✅ | 1 |
| 总数量 | 16 | 16 ✅ | 16 |
| 说明 | 满足 1 次条件 | 满足 1 次条件 | 正确 |

### 场景 4: 买 5 赠 2, 充值 10 个

| 项目 | 旧逻辑 | 新逻辑 | 期望值 |
|------|--------|--------|--------|
| 付费数量 | 10 | 10 | 10 |
| 赠送数量 | 2 ❌ | 4 ✅ | 4 |
| 总数量 | 12 | 14 ✅ | 14 |
| 说明 | 错误理解 | 满足 2 次买 5 的条件 | 正确 |

---

## 🛠️ 修复内容

### 文件：`backend/api_unified.py` (Line 273-278)

#### 修改前
```python
# 计算赠送数量
free_quantity = 0
if config and config.trigger_qty > 0:
    cycle = config.trigger_qty + config.gift_qty
    free_quantity = (request.quantity // cycle) * config.gift_qty
```

#### 修改后
```python
# 计算赠送数量
free_quantity = 0
if config and config.trigger_qty > 0:
    # 买 N 赠 M: 每买 trigger_qty 个，就赠送 gift_qty 个
    # 例如：买 10 赠 1，充值 10 个 → 赠送 1 个；充值 20 个 → 赠送 2 个
    free_quantity = (request.quantity // config.trigger_qty) * config.gift_qty
```

---

## ✅ 完整的充值流程

### 1. 前端发起充值请求 (admin-unified.html)

```javascript
// Line 590-602
const url = `${API_BASE}/unified/wallet/balance?user_id=${this.topupForm.userId}`;
const res = await fetch(url, {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify({
        product_id: this.topupForm.productId,
        wallet_type: this.topupForm.type,  // 'prepaid'
        quantity: this.topupForm.quantity,  // 10
        note: this.topupForm.note
    })
});
```

### 2. 后端计算赠送数量 (api_unified.py)

```python
# Line 267-278
# 获取优惠配置
config = db.query(PromotionConfigV2).filter(
    PromotionConfigV2.product_id == request.product_id,
    PromotionConfigV2.mode == 'prepaid',
    PromotionConfigV2.is_active == 1
).first()

# 计算赠送数量 (已修复)
free_quantity = (request.quantity // config.trigger_qty) * config.gift_qty
# 例如：买 10 赠 1, 充值 10 个 → free_quantity = (10 // 10) * 1 = 1
```

### 3. 保存到数据库 (account_service.py)

```python
# Line 119-128
wallet = self.get_or_create_wallet(user_id, product_id, 'prepaid')

# 更新余额
wallet.paid_qty += paid_quantity      # 付费数量 +10
wallet.free_qty += free_quantity      # 赠送数量 +1
wallet.available_qty = wallet.paid_qty + wallet.free_qty  # 总数量 = 11

self.db.commit()
```

### 4. 返回充值结果 (api_unified.py)

```python
# Line 288-303
message = f"预付充值成功：付费{result['paid_qty']}个"
if free_quantity > 0:
    message += f"，赠送{free_quantity}个"
message += "，共" + str(result['total_qty']) + "个"

# 示例输出：
# "预付充值成功：付费 10 个，赠送 1 个，共 11 个"
```

---

## 🎯 验证步骤

### 步骤 1: 重启后端服务

```bash
cd /Users/sgl/PycharmProjects/AIchanyejiqun/Service_WaterManage/backend
# 停止当前服务
# 清理缓存
find . -type d -name "__pycache__" -exec rm -rf {} +
# 重启服务
python main.py
```

### 步骤 2: 配置优惠方案

1. 打开统一账户管理页面
2. 进入"优惠配置"Tab
3. 为某个产品配置"买 10 赠 1"
   - 模式：预付 (prepaid)
   - 触发数量：10
   - 赠送数量：1
   - 启用状态：是

### 步骤 3: 测试充值

1. 进入"充值/授信"Tab
2. 选择一个用户
3. 选择产品
4. 类型选择"预付充值"
5. 输入数量：**10**
6. 点击"确认充值"

### 预期结果

- ✅ 提示消息："预付充值成功：付费 10 个，赠送 1 个，共 11 个"
- ✅ 用户余额显示：
  - 付费桶：10
  - 赠送桶：1
  - 总余额：11

---

## 📝 技术要点

### 语义理解

**"买 N 赠 M"的正确理解**:
- ✅ 每购买 N 个商品，就赠送 M 个
- ✅ 充值 N 个 → 获得 N+M 个
- ✅ 充值 2N 个 → 获得 2N+2M 个
- ❌ ~~每满 (N+M) 个才赠送 M 个~~ (这是旧逻辑的错误理解)

### 数学公式

```
赠送数量 = (充值数量 // 触发数量) × 赠送数量

例如：买 10 赠 1
- 充值 10 个：赠送 = (10 // 10) × 1 = 1 个
- 充值 20 个：赠送 = (20 // 10) × 1 = 2 个
- 充值 15 个：赠送 = (15 // 10) × 1 = 1 个 (不满 10 的部分不赠送)
```

---

## ⚠️ 注意事项

### 边界情况

1. **充值数量不足触发条件**
   - 买 10 赠 1, 充值 9 个 → 赠送 0 个 ✅
   
2. **充值数量是倍数的情况**
   - 买 10 赠 1, 充值 30 个 → 赠送 3 个 ✅

3. **多次充值累计**
   - 第 1 次充值 10 个 → 赠送 1 个，总 11 个
   - 第 2 次充值 5 个 → 赠送 0 个，总 16 个
   - 第 3 次充值 5 个 → 赠送 0 个，总 21 个
   - 累计充值 20 个，累计赠送 1 个 ✅

---

## 📊 修复统计

- **修改文件**: 1 个 (`api_unified.py`)
- **修改行数**: 3 行 (Line 275-278)
- **影响范围**: 预付费充值模块的买赠计算
- **测试覆盖**: 4 个典型场景

---

## 🚀 后续建议

### 功能增强

1. **前端显示预计赠送数量**
   - 在充值表单中实时显示"预计赠送：X 个"
   - 让用户清楚知道充值能获得的总数

2. **充值历史记录**
   - 记录每次充值的付费数量和赠送数量
   - 方便用户和对账查询

3. **优惠活动配置**
   - 支持时间段优惠 (如：活动期间买 10 赠 2)
   - 支持阶梯优惠 (如：充 100 以上送 15 个)

---

**修复完成时间**: 2026-03-24  
**状态**: ✅ 代码已修复，等待重启验证  
**下一步**: 
1. 重启后端服务
2. 配置买 10 赠 1 优惠
3. 测试充值 10 个，验证是否赠送 1 个
