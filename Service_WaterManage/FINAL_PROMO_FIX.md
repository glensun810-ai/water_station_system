# 买 N 赠 M 前端计算错误修复

**日期**: 2026-03-30  
**错误**: `toFixed is not a function`  
**状态**: ✅ 已修复

---

## 错误描述

**现象**: 当用户选择 10 桶再加 1 桶时，页面报错

**错误信息**:
```
Uncaught (in promise) TypeError: this.products.reduce(...).toFixed is not a function
    at Proxy.originalAmount
```

**根因**: 在 `originalAmount` 和 `discountAmount` 计算属性中，在 reduce 的每次迭代中都调用了 `.toFixed(2)`，导致 sum 变成字符串，最后又调用 `.toFixed(2)` 时报错。

---

## 修复内容

### 修复前的错误代码

```javascript
originalAmount() {
    return this.products.reduce((sum, p) => {
        if (!this.cart[p.id]) return sum;
        return (sum + this.cart[p.id] * p.price).toFixed(2);  // ❌ 错误：每次迭代都调用 toFixed
    }, 0).toFixed(2);  // ❌ 错误：此时 sum 已经是字符串
}
```

### 修复后的正确代码

```javascript
originalAmount() {
    const amount = this.products.reduce((sum, p) => {
        if (!this.cart[p.id]) return sum;
        return sum + this.cart[p.id] * p.price;  // ✅ 正确：只累加数字
    }, 0);
    return amount.toFixed(2);  // ✅ 正确：最后才调用 toFixed
}
```

同样的修复也应用到 `discountAmount` 计算属性。

---

## 修复验证

### 测试场景：12L 桶装水（买 10 赠 1，单价 16.8 元）

| 数量 | 原价 | 优惠 | 实付 | 状态 |
|------|------|------|------|------|
| 10 桶 | ¥168.00 | ¥0.00 | ¥168.00 | ✅ |
| 11 桶 | ¥184.80 | ¥16.80 | ¥168.00 | ✅ |
| 12 桶 | ¥201.60 | ¥16.80 | ¥184.80 | ✅ |
| 22 桶 | ¥369.60 | ¥33.60 | ¥336.00 | ✅ |

**所有测试通过！** ✅

---

## 技术要点

### JavaScript reduce 最佳实践

```javascript
// ❌ 错误做法
array.reduce((sum, item) => {
    return (sum + item.value).toFixed(2);  // 返回字符串
}, 0)

// ✅ 正确做法
const total = array.reduce((sum, item) => {
    return sum + item.value;  // 返回数字
}, 0);
return total.toFixed(2);  // 最后格式化
```

### 为什么不能在 reduce 中调用 toFixed？

1. **toFixed 返回字符串**: `(123).toFixed(2)` 返回 `"123.00"`（字符串）
2. **字符串 + 数字 = 字符串**: `"123.00" + 456` 结果是 `"123.00456"`
3. **字符串.toFixed() 报错**: `"123.00".toFixed(2)` 抛出 TypeError

---

## 用户体验

### 修复前 ❌
- 选择 11 桶时报错
- 页面无法继续操作
- 控制台显示红色错误

### 修复后 ✅
- 选择 11 桶正常显示 ¥168.00
- 显示优惠明细：
  - 🎉 已优惠 1 件
  - 原价：¥184.80
  - 优惠：-¥16.80
  - 实付：¥168.00
- 用户清楚看到优惠金额

---

## 变更统计

| 文件 | 修复位置 | 变更行数 |
|------|---------|---------|
| `frontend/index.html` | originalAmount | -4/+5 |
| `frontend/index.html` | discountAmount | -4/+5 |

**总计**: 修改 2 个计算属性，+10 行代码

---

## 验证步骤

1. **清除浏览器缓存**
   - Windows/Linux: `Ctrl + Shift + Delete`
   - Mac: `Cmd + Shift + Delete`

2. **刷新页面**
   - Windows/Linux: `Ctrl + Shift + R`
   - Mac: `Cmd + Shift + R`

3. **测试场景**
   - 选择 12L 桶装水
   - 选择 10 桶 → 显示 ¥168.00 ✅
   - 增加到 11 桶 → 显示 ¥168.00 ✅（不是 ¥184.80）
   - 增加到 12 桶 → 显示 ¥184.80 ✅

---

**修复人员**: AI Development Team  
**状态**: ✅ 已完成并测试通过  
**部署**: 刷新浏览器即可生效

---

*买 N 赠 M 功能已完全修复，前后端计算逻辑一致！* 🎉
