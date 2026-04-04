# 智能水站管理系统 - 买 N 赠 M 方案优化设计

**文档编号**: 09  
**版本**: v1.0  
**设计日期**: 2026-03-30  
**优先级**: P0 (高优先级)  
**实施策略**: 小改动、大体验、分步实施

---

## 一、需求背景

### 1.1 现状分析

系统已实现基础的买 N 赠 M 功能，但存在以下体验优化空间：

**已有功能** ✅:
- 产品表 `products` 包含 `promo_threshold` (买 N) 和 `promo_gift` (赠 M) 字段
- 优惠配置表 `promotion_config_v2` 支持按模式配置优惠
- 后端已实现买赠计算逻辑 (`discount_strategy.py`)
- 用户端和管理后台已有基础的优惠展示

**待优化点** ⚠️:
1. 优惠展示不够直观，用户难以快速理解优惠力度
2. 缺少"再买 X 件即可享受优惠"的智能提醒
3. 订单结算页缺少优惠明细的清晰展示
4. 管理端缺少优惠效果的统计看板
5. 缺少优惠活动的快速启停控制

### 1.2 优化目标

以**最小改动**实现**最佳体验**：

1. **前端展示优化** - 让用户一眼看懂优惠规则
2. **智能提醒** - 提醒用户差多少件可享受优惠
3. **结算明细** - 清晰展示优惠金额和计算过程
4. **管理便捷** - 快速启停优惠活动，查看效果

---

## 二、设计方案总览

### 2.1 优化范围

| 模块 | 页面 | 改动类型 | 优先级 |
|------|------|----------|--------|
| 用户端 | index.html | UI 优化 + 智能提醒 | P0 |
| 用户端 | user-balance.html | 优惠明细展示 | P0 |
| 管理后台 | admin.html - 产品管理 | 快速启停控制 | P0 |
| 管理后台 | admin.html - 数据看板 | 优惠效果统计 | P1 |
| 后端 API | api_unified.py | 增加优惠计算接口 | P1 |

### 2.2 技术策略

**核心原则**：
- ✅ **不改变现有数据模型** - 复用 promo_threshold 和 promo_gift 字段
- ✅ **不改变核心业务逻辑** - 复用现有买赠计算函数
- ✅ **前端为主，后端为辅** - 90% 的改动在前端展示层
- ✅ **渐进式优化** - 分 3 期实施，每期独立可用

---

## 三、详细设计

### 3.1 用户端优化 - 领水登记页面 (index.html)

#### 3.1.1 产品卡片优惠标签增强

**改动位置**: index.html Line 220-250

**当前实现**:
```html
<div v-if="product.promo_threshold && product.promo_gift" 
     class="text-xs bg-blue-50 text-blue-600 px-2 py-0.5 rounded mt-1 inline-block">
    买{{ product.promo_threshold }}赠{{ product.promo_gift }}
</div>
```

**优化后**:
```html
<!-- 优惠标签 -->
<div v-if="product.promo_threshold && product.promo_gift" 
     class="mt-2 p-2 bg-gradient-to-r from-orange-50 to-red-50 rounded-lg border border-orange-200">
    <div class="flex items-center justify-between">
        <div class="flex items-center">
            <span class="text-lg mr-1">🎁</span>
            <span class="text-sm font-bold text-orange-600">
                买{{ product.promo_threshold }}赠{{ product.promo_gift }}
            </span>
        </div>
        <span class="text-xs bg-orange-500 text-white px-2 py-0.5 rounded-full">
            省￥{{ (product.promo_gift * product.price).toFixed(2) }}
        </span>
    </div>
    <!-- 智能提醒 -->
    <div v-if="cart[product.id] > 0" class="mt-1 text-xs text-orange-700">
        <span v-if="getGiftQuantity(product, cart[product.id]) > 0">
            ✅ 已优惠{{ getGiftQuantity(product, cart[product.id]) }}件
        </span>
        <span v-else>
            再买{{ product.promo_threshold - cart[product.id] }}件享优惠
        </span>
    </div>
</div>
```

**效果说明**:
- 渐变背景色更醒目
- 展示节省金额，直观体现优惠力度
- 根据用户选择的数量，动态显示优惠状态
- 未达优惠门槛时，提醒还需购买多少件

#### 3.1.2 数量选择器增强

**新增计算函数**:
```javascript
/**
 * 计算赠送数量
 */
const getGiftQuantity = (product, quantity) => {
    if (!product.promo_threshold || !product.promo_gift || quantity < product.promo_threshold) return 0;
    
    // 买 N 赠 M：每满 N 件，赠送 M 件
    const cycles = Math.floor(quantity / product.promo_threshold);
    return cycles * product.promo_gift;
};

/**
 * 计算距离下次优惠还差多少件
 */
const getNextGiftProgress = (product, quantity) => {
    if (!product.promo_threshold) return { current: 0, need: 0, percent: 0 };
    
    const remainder = quantity % product.promo_threshold;
    const need = product.promo_threshold - remainder;
    const percent = Math.floor((remainder / product.promo_threshold) * 100);
    
    return {
        current: remainder,
        need: need === product.promo_threshold ? 0 : need,
        percent: percent
    };
};
```

#### 3.1.3 结算弹窗优惠明细

**改动位置**: index.html 结算弹窗

**新增展示**:
```html
<!-- 优惠明细卡片 -->
<div v-if="totalGiftQty > 0" class="mb-4 p-3 bg-green-50 rounded-lg border border-green-200">
    <div class="text-sm font-bold text-green-800 mb-2">
        🎉 优惠明细
    </div>
    <div class="text-xs space-y-1 text-green-700">
        <div class="flex justify-between">
            <span>商品总额：</span>
            <span class="line-through">￥{{ totalAmount }}</span>
        </div>
        <div class="flex justify-between">
            <span>赠送数量：</span>
            <span class="text-green-600 font-bold">-{{ totalGiftQty }}件</span>
        </div>
        <div class="flex justify-between">
            <span>优惠金额：</span>
            <span class="text-red-600 font-bold">-￥{{ totalGiftAmount }}</span>
        </div>
        <div class="border-t border-green-300 mt-1 pt-1 flex justify-between font-bold">
            <span>应付金额：</span>
            <span>￥{{ actualAmount }}</span>
        </div>
    </div>
</div>
```

---

### 3.2 用户端优化 - 我的预付页面 (user-balance.html)

#### 3.2.1 预付订单优惠展示

**改动位置**: user-balance.html 订单列表

**优化内容**:
```html
<!-- 订单卡片 -->
<div class="order-card" v-for="order in prepaidOrders">
    <!-- 订单头部 -->
    <div class="flex justify-between items-center">
        <span class="font-bold">{{ order.product_name }}</span>
        <span v-if="order.gift_qty > 0" class="text-xs bg-red-100 text-red-600 px-2 py-0.5 rounded">
            已赠{{ order.gift_qty }}件
        </span>
    </div>
    
    <!-- 优惠进度条 -->
    <div v-if="order.gift_qty > 0" class="mt-2">
        <div class="text-xs text-gray-600 mb-1">
            累计优惠：{{ order.gift_qty }}件 (价值￥{{ order.gift_qty * order.unit_price }})
        </div>
    </div>
</div>
```

---

### 3.3 管理后台优化 - 产品管理 (admin.html)

#### 3.3.1 产品列表优惠信息增强

**改动位置**: admin.html 产品列表 Line 3070-3100

**当前实现**:
```html
<th>优惠方案</th>
...
<td>买{{ p.promo_threshold }}赠{{ p.promo_gift }}</td>
```

**优化后**:
```html
<th>优惠方案</th>
<th>优惠力度</th>
<th>状态</th>
...
<td>
    <div class="text-sm font-bold text-orange-600">
        买{{ p.promo_threshold }}赠{{ p.promo_gift }}
    </div>
    <div class="text-xs text-gray-500">
        满{{ p.promo_threshold }}件享优惠
    </div>
</td>
<td>
    <div class="text-sm text-green-600">
        约{{ Math.round((p.promo_gift / (p.promo_threshold + p.promo_gift)) * 100) }}% OFF
    </div>
    <div class="text-xs text-gray-500">
        每件省￥{{ (p.promo_gift * p.price / (p.promo_threshold + p.promo_gift)).toFixed(2) }}
    </div>
</td>
<td>
    <!-- 快速启停开关 -->
    <label class="relative inline-flex items-center cursor-pointer">
        <input type="checkbox" 
               :checked="p.promo_threshold > 0"
               @change="toggleProductPromo(p, $event.target.checked)"
               class="sr-only peer">
        <div class="w-9 h-5 bg-gray-300 peer-focus:outline-none peer-focus:ring-2 peer-focus:ring-blue-300 
                    rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white 
                    after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white 
                    after:border-gray-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all 
                    peer-checked:bg-blue-600"></div>
        <span class="ml-2 text-xs">{{ p.promo_threshold > 0 ? '已开启' : '已关闭' }}</span>
    </label>
</td>
```

#### 3.3.2 快速启停优惠函数

**新增 API**:
```javascript
/**
 * 快速启停产品优惠
 */
const toggleProductPromo = async (product, enable) => {
    try {
        if (enable) {
            // 启用优惠：设置默认买 10 赠 1
            await fetch(`/api/products/${product.id}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    promo_threshold: 10,
                    promo_gift: 1
                })
            });
            showMessage(`${product.name} 优惠已开启 (买 10 赠 1)`);
        } else {
            // 关闭优惠
            await fetch(`/api/products/${product.id}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    promo_threshold: 0,
                    promo_gift: 0
                })
            });
            showMessage(`${product.name} 优惠已关闭`);
        }
        
        // 刷新产品列表
        await loadProducts();
    } catch (error) {
        console.error('切换优惠失败:', error);
        showMessage('操作失败', 'error');
    }
};
```

#### 3.3.3 产品编辑弹窗优化

**改动位置**: admin.html 产品编辑弹窗 Line 2411-2440

**优化内容**:
```html
<!-- 优惠方案设置 -->
<div class="mb-4 p-3 bg-orange-50 rounded-lg border border-orange-200">
    <div class="text-sm font-bold text-orange-800 mb-2">
        🎁 买 N 赠 M 设置
    </div>
    
    <div class="grid grid-cols-2 gap-3">
        <div>
            <label class="text-xs text-gray-600">买 N</label>
            <input type="number" 
                   v-model.number="editingProduct.promo_threshold"
                   class="w-full text-sm border rounded px-2 py-1"
                   placeholder="0">
        </div>
        <div>
            <label class="text-xs text-gray-600">赠 M</label>
            <input type="number" 
                   v-model.number="editingProduct.promo_gift"
                   class="w-full text-sm border rounded px-2 py-1"
                   placeholder="0">
        </div>
    </div>
    
    <!-- 实时预览 -->
    <div v-if="editingProduct.promo_threshold > 0 && editingProduct.promo_gift > 0" 
         class="mt-2 p-2 bg-white rounded text-xs">
        <div class="text-orange-600 font-bold mb-1">优惠预览：</div>
        <div>优惠力度：约{{ Math.round((editingProduct.promo_gift / 
              (editingProduct.promo_threshold + editingProduct.promo_gift)) * 100) }}% OFF</div>
        <div>每件平均：￥{{ (editingProduct.price * editingProduct.promo_threshold / 
              (editingProduct.promo_threshold + editingProduct.promo_gift)).toFixed(2) }}</div>
        <div class="text-green-600">每满{{ editingProduct.promo_threshold }}件赠送{{ editingProduct.promo_gift }}件</div>
    </div>
</div>
```

---

### 3.4 管理后台优化 - 数据看板 (admin.html)

#### 3.4.1 优惠效果统计卡片

**改动位置**: admin.html Dashboard 区域

**新增统计 API**:
```python
@app.get("/api/admin/promotion-stats")
def get_promotion_statistics(
    start_date: str = None,
    end_date: str = None,
    db: Session = Depends(get_db)
):
    """
    获取优惠效果统计数据
    """
    from sqlalchemy import func, sum
    
    # 查询时间段内的交易记录
    query = db.query(
        TransactionV2.product_id,
        Product.name,
        Product.price,
        func.count(TransactionV2.id).label('total_orders'),
        func.sum(TransactionV2.quantity).label('total_qty'),
        func.sum(TransactionV2.free_qty).label('total_gift_qty'),
        func.sum(TransactionV2.total_price).label('total_amount')
    ).join(Product, TransactionV2.product_id == Product.id)
    
    if start_date:
        query = query.filter(TransactionV2.created_at >= start_date)
    if end_date:
        query = query.filter(TransactionV2.created_at <= end_date)
    
    stats = query.group_by(TransactionV2.product_id, Product.name, Product.price).all()
    
    result = []
    for stat in stats:
        result.append({
            'product_id': stat.product_id,
            'product_name': stat.name,
            'unit_price': stat.price,
            'total_orders': stat.total_orders,
            'total_qty': stat.total_qty,
            'total_gift_qty': stat.total_gift_qty or 0,
            'total_amount': stat.total_amount or 0,
            'gift_rate': round((stat.total_gift_qty or 0) / (stat.total_qty or 1) * 100, 2),
            'total_savings': round((stat.total_gift_qty or 0) * stat.price, 2)
        })
    
    return result
```

**前端展示**:
```html
<!-- 优惠效果统计卡片 -->
<div class="bg-white rounded-lg shadow p-4">
    <div class="text-lg font-bold text-gray-800 mb-3">
        🎁 优惠效果统计
    </div>
    
    <!-- 总计卡片 -->
    <div class="grid grid-cols-3 gap-3 mb-4">
        <div class="text-center p-2 bg-orange-50 rounded">
            <div class="text-2xl font-bold text-orange-600">{{ promoStats.totalGiftQty }}</div>
            <div class="text-xs text-gray-600">赠送总量</div>
        </div>
        <div class="text-center p-2 bg-red-50 rounded">
            <div class="text-2xl font-bold text-red-600">￥{{ promoStats.totalSavings }}</div>
            <div class="text-xs text-gray-600">用户节省</div>
        </div>
        <div class="text-center p-2 bg-green-50 rounded">
            <div class="text-2xl font-bold text-green-600">{{ promoStats.avgGiftRate }}%</div>
            <div class="text-xs text-gray-600">平均优惠率</div>
        </div>
    </div>
    
    <!-- 产品排行 -->
    <div class="text-sm font-bold text-gray-700 mb-2">按产品统计</div>
    <div class="space-y-2">
        <div v-for="stat in promoStats.products" :key="stat.product_id"
             class="flex justify-between items-center p-2 bg-gray-50 rounded">
            <div class="text-sm">{{ stat.product_name }}</div>
            <div class="text-xs text-gray-600">
                赠{{ stat.total_gift_qty }}件 
                <span class="text-red-500">省￥{{ stat.total_savings }}</span>
            </div>
        </div>
    </div>
</div>
```

---

### 3.5 后端 API 增强

#### 3.5.1 优惠计算接口

**新增 API**:
```python
@app.get("/api/promotions/calculate")
def calculate_promotion_detail(
    product_id: int,
    quantity: int,
    db: Session = Depends(get_db)
):
    """
    计算优惠详情（前端实时展示用）
    
    返回详细的优惠计算过程和结果
    """
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="产品不存在")
    
    if not product.promo_threshold or product.promo_threshold <= 0:
        return {
            'product_id': product_id,
            'product_name': product.name,
            'unit_price': product.price,
            'quantity': quantity,
            'gift_qty': 0,
            'paid_qty': quantity,
            'total_amount': product.price * quantity,
            'savings': 0,
            'discount_rate': 0,
            'message': '当前无优惠'
        }
    
    # 计算赠送数量
    cycles = quantity // product.promo_threshold
    gift_qty = cycles * product.promo_gift
    
    # 计算金额
    paid_qty = quantity - gift_qty
    total_amount = paid_qty * product.price
    original_amount = quantity * product.price
    savings = original_amount - total_amount
    discount_rate = round((savings / original_amount * 100) if original_amount > 0 else 0, 2)
    
    # 计算距离下次优惠还差多少
    remainder = quantity % product.promo_threshold
    next_gift_need = product.promo_threshold - remainder if remainder > 0 else 0
    
    return {
        'product_id': product_id,
        'product_name': product.name,
        'unit_price': product.price,
        'quantity': quantity,
        'gift_qty': gift_qty,
        'paid_qty': paid_qty,
        'total_amount': total_amount,
        'original_amount': original_amount,
        'savings': savings,
        'discount_rate': discount_rate,
        'message': f'已优惠{gift_qty}件' if gift_qty > 0 else f'再买{next_gift_need}件享优惠',
        'next_gift_progress': {
            'current': remainder,
            'need': next_gift_need,
            'percent': round((remainder / product.promo_threshold) * 100)
        }
    }
```

---

## 四、实施计划

### 4.1 Phase 1 - 用户端体验优化 (2 天)

| 任务 | 文件 | 预计工时 | 优先级 |
|------|------|----------|--------|
| 产品卡片优惠标签增强 | index.html | 2h | P0 |
| 智能提醒函数实现 | index.html | 1h | P0 |
| 结算弹窗优惠明细 | index.html | 2h | P0 |
| 我的预付优惠展示 | user-balance.html | 1h | P1 |
| 自测与调试 | - | 2h | P0 |

**验收标准**:
- ✅ 用户能看到醒目的优惠标签
- ✅ 选择数量时实时显示优惠状态
- ✅ 结算页清晰展示优惠明细

### 4.2 Phase 2 - 管理端优化 (2 天)

| 任务 | 文件 | 预计工时 | 优先级 |
|------|------|----------|--------|
| 产品列表优惠信息增强 | admin.html | 2h | P0 |
| 快速启停开关 | admin.html + API | 2h | P0 |
| 产品编辑弹窗优化 | admin.html | 2h | P1 |
| 自测与调试 | - | 2h | P0 |

**验收标准**:
- ✅ 产品列表清晰展示优惠力度
- ✅ 一键启停优惠功能正常
- ✅ 编辑时实时预览优惠效果

### 4.3 Phase 3 - 数据统计看板 (1 天)

| 任务 | 文件 | 预计工时 | 优先级 |
|------|------|----------|--------|
| 优惠统计 API | api_unified.py | 2h | P1 |
| Dashboard 统计卡片 | admin.html | 2h | P1 |
| 产品排行展示 | admin.html | 1h | P2 |
| 测试与优化 | - | 2h | P1 |

**验收标准**:
- ✅ Dashboard 展示优惠效果统计
- ✅ 数据准确无误

---

## 五、技术细节

### 5.1 复用现有函数

充分利用已有的优惠计算逻辑，避免重复开发：

```javascript
// 复用 discount_strategy.py 中的计算逻辑
// 前端实现相同逻辑用于实时展示
const calculateGift = (quantity, threshold, gift) => {
    return Math.floor(quantity / threshold) * gift;
};

// 后端已有实现 (discount_strategy.py:133-149)
# 买 N 赠 M 计算
cycle = config.trigger_qty + config.gift_qty
free_items = 0
for i in range(quantity):
    position_in_cycle = (historical_count + i + 1) % cycle
    if position_in_cycle == 0:
        free_items += 1
```

### 5.2 样式统一

使用 Tailwind CSS 统一视觉风格：

```html
<!-- 优惠相关样式规范 -->
- 主色调：橙色系 (orange-500, orange-600)
- 背景：渐变 (from-orange-50 to-red-50)
- 边框：orange-200
- 强调色：绿色 (green-600 表示节省)
- 字体：加粗 (font-bold) 突出重点
```

### 5.3 性能优化

- 前端计算使用缓存，避免重复计算
- 列表页使用虚拟滚动（如产品数量过多）
- API 请求增加防抖处理

---

## 六、测试用例

### 6.1 前端功能测试

| 测试场景 | 预期结果 | 优先级 |
|---------|---------|--------|
| 产品卡片显示优惠标签 | 标签醒目，显示买 N 赠 M 和节省金额 | P0 |
| 选择数量未达优惠门槛 | 显示"再买 X 件享优惠" | P0 |
| 选择数量达到优惠门槛 | 显示"✅ 已优惠 X 件" | P0 |
| 结算页展示优惠明细 | 商品总额、赠送数量、优惠金额、应付金额清晰展示 | P0 |
| 管理端快速启停优惠 | 开关响应迅速，状态正确 | P0 |
| 编辑产品实时预览 | 修改买 N 赠 M 数值时，优惠力度实时更新 | P1 |

### 6.2 后端 API 测试

```bash
# 测试优惠计算 API
curl "http://localhost:8000/api/promotions/calculate?product_id=1&quantity=15"

# 预期响应：
{
    "product_name": "桶装水 18L",
    "quantity": 15,
    "gift_qty": 1,
    "paid_qty": 14,
    "total_amount": 210,
    "savings": 15,
    "discount_rate": 6.67,
    "message": "已优惠 1 件"
}
```

### 6.3 边界测试

| 边界情况 | 预期处理 |
|---------|---------|
| 数量 = 0 | 不显示优惠信息 |
| 数量 < 买 N 阈值 | 显示"再买 X 件享优惠" |
| 数量 = 买 N 阈值 | 显示"✅ 已优惠 M 件" |
| 买 N 阈值 = 0 | 不显示优惠标签 |
| 产品无优惠配置 | 正常展示，不显示优惠信息 |

---

## 七、预期效果

### 7.1 用户体验提升

| 指标 | 优化前 | 优化后 | 提升 |
|------|--------|--------|------|
| 优惠理解成本 | 高 | 低 | -70% |
| 优惠信息可见性 | 一般 | 优秀 | +150% |
| 决策效率 | 慢 | 快 | +60% |
| 管理操作便捷性 | 一般 | 优秀 | +80% |

### 7.2 业务价值

1. **提升用户满意度** - 透明的优惠信息减少用户困惑
2. **增加购买量** - 智能提醒促使用户凑单享受优惠
3. **提高管理效率** - 一键启停优惠，无需复杂操作
4. **数据驱动决策** - 优惠效果统计帮助优化促销策略

---

## 八、风险评估

### 8.1 技术风险

| 风险 | 可能性 | 影响 | 应对措施 |
|------|--------|------|---------|
| 前端性能下降 | 低 | 中 | 使用缓存和防抖 |
| 计算逻辑不一致 | 低 | 高 | 前后端使用相同公式 |
| 样式兼容性问题 | 中 | 低 | 充分测试主流浏览器 |

### 8.2 业务风险

| 风险 | 可能性 | 影响 | 应对措施 |
|------|--------|------|---------|
| 优惠配置错误 | 低 | 中 | 增加输入验证和预览 |
| 用户对优惠敏感度降低 | 低 | 低 | 后续可增加限时优惠 |

---

## 九、后续优化建议

### 9.1 短期优化 (1-2 周)

1. **限时买赠活动** - 设置优惠有效期，营造紧迫感
2. **优惠券叠加** - 买赠优惠 + 优惠券双重优惠
3. **消息推送** - 优惠活动开始/结束推送

### 9.2 中期优化 (1-2 月)

1. **阶梯式买赠** - 买得越多送得越多（买 10 赠 1、买 20 赠 3、买 50 赠 8）
2. **组合优惠** - 多种产品组合享受优惠
3. **会员专享优惠** - 不同等级会员不同优惠力度

### 9.3 长期优化 (3-6 月)

1. **AI 智能推荐** - 基于历史数据推荐最优购买量
2. **动态定价** - 根据供需关系自动调整优惠力度
3. **团购优惠** - 多人拼团享受更高优惠

---

## 十、附录

### 10.1 相关文件索引

| 文件 | 路径 | 说明 |
|------|------|------|
| 用户端主页 | frontend/index.html | Line 60-250, 1220-1240 |
| 我的预付 | frontend/user-balance.html | Line 110-240 |
| 管理后台 | frontend/admin.html | Line 2280-2440, 3070-3100 |
| 优惠计算 | backend/discount_strategy.py | Line 98-160 |
| 统一 API | backend/api_unified.py | Line 540-600 |
| 产品模型 | backend/main.py | Line 142-156 |
| 优惠配置 | backend/models_unified.py | Line 162-188 |

### 10.2 关键代码片段

**前端优惠计算函数**:
```javascript
const getGiftQuantity = (product, quantity) => {
    if (!product.promo_threshold || !product.promo_gift || quantity < product.promo_threshold) return 0;
    const cycles = Math.floor(quantity / product.promo_threshold);
    return cycles * product.promo_gift;
};
```

**后端优惠计算 API**:
```python
@app.get("/api/promotions/calculate")
def calculate_promotion_detail(product_id: int, quantity: int, db: Session):
    # 详细实现见 3.5.1 章节
```

---

**文档状态**: ✅ 设计完成，等待评审  
**最后更新**: 2026-03-30  
**负责人**: 产品经理  
**技术负责人**: 待定
