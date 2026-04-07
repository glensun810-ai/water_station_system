# 操作按钮对齐规范

## 问题背景
用户反馈管理页面中的操作按钮（确认、编辑、删除等）在不同行中没有对齐，影响UI美观。

## 解决方案

### 1. 统一的CSS样式系统

在 `portal/assets/css/design-system.css` 中新增了操作按钮容器样式：

```css
/* 操作按钮容器 - 确保按钮对齐 */
.action-buttons {
    display: grid;
    gap: var(--spacing-xs);
}

/* 2列布局：编辑+删除 */
.action-buttons-2 {
    grid-template-columns: repeat(2, 1fr);
    min-width: 120px;
}

/* 3列布局：充值+编辑+删除 */
.action-buttons-3 {
    grid-template-columns: repeat(3, 1fr);
    min-width: 180px;
}

/* 4列布局：确认+提醒+编辑+删除 */
.action-buttons-4 {
    grid-template-columns: repeat(4, 1fr);
    min-width: 240px;
}

/* 自适应布局：根据内容自动调整 */
.action-buttons-auto {
    grid-template-columns: repeat(auto-fit, minmax(60px, 1fr));
}
```

### 2. 核心技术要点

#### 使用CSS Grid代替Flexbox
- **优势**: Grid布局可以确保每个单元格固定宽度，不会因为内容或按钮数量变化而错位
- **实现**: 使用 `grid-template-columns: repeat(N, 1fr)` 创建N列等宽布局

#### 按钮条件显示的占位处理
当某些按钮根据条件不显示时，使用 `v-show` 配合 `visibility: hidden` 而不是 `v-if`：

```html
<!-- 推荐：保留占位 -->
<button v-show="condition" class="btn">确认</button>

<!-- 不推荐：移除DOM元素 -->
<button v-if="condition" class="btn">确认</button>
```

### 3. 已修改的页面

| 页面 | 原布局 | 新布局 | 修改内容 |
|------|--------|--------|----------|
| `portal/admin/water/pickups.html` | flex | grid (4列) | 确认、提醒、编辑、删除按钮对齐 |
| `portal/admin/water/accounts.html` | flex | grid (3列) | 充值、编辑、删除按钮对齐 |
| `portal/admin/meeting/rooms.html` | flex | grid (2列) | 编辑、删除按钮对齐 |
| `portal/admin/meeting/bookings.html` | flex | grid (自适应) | 确认、取消、查看等按钮自适应 |
| `portal/admin/meeting/approvals.html` | flex | grid (2列) | 通过、拒绝按钮对齐 |

### 4. 使用规范

#### 基本用法
```html
<div class="action-buttons action-buttons-3">
    <button class="btn btn-secondary btn-sm">充值</button>
    <button class="btn btn-secondary btn-sm">编辑</button>
    <button class="btn btn-danger btn-sm">删除</button>
</div>
```

#### 条件按钮
```html
<div class="action-buttons action-buttons-4">
    <!-- 使用 v-show 保留占位 -->
    <button v-show="status === 'pending'" class="btn btn-primary btn-sm">确认</button>
    <button v-show="status === 'unpaid'" class="btn btn-secondary btn-sm">提醒</button>
    <button class="btn btn-secondary btn-sm">编辑</button>
    <button class="btn btn-danger btn-sm">删除</button>
</div>
```

#### 自适应布局
```html
<div class="action-buttons action-buttons-auto">
    <button class="btn btn-success btn-sm">通过</button>
    <button class="btn btn-secondary btn-sm">编辑</button>
    <button class="btn btn-danger btn-sm">删除</button>
</div>
```

### 5. 响应式设计

#### PC端 (>768px)
- 按钮并排显示，使用grid布局确保对齐
- 每个按钮固定宽度，文字居中

#### 移动端 (≤768px)
- 按钮仍然保持grid布局
- 按钮宽度自适应容器
- 确保触摸友好（最小高度36px）

### 6. 测试页面

访问 `http://127.0.0.1:8001/portal/test-action-buttons.html` 查看各种场景的效果演示。

### 7. 注意事项

1. **统一使用design-system.css**: 所有新页面应引用统一的设计系统
2. **选择合适的布局类**:
   - 2个按钮 → `action-buttons-2`
   - 3个按钮 → `action-buttons-3`
   - 4个按钮 → `action-buttons-4`
   - 数量不固定 → `action-buttons-auto`
3. **避免内联样式**: 不要使用style="display: flex"等内联样式覆盖
4. **保持一致性**: 同一项目中相同场景使用相同的按钮数量和顺序

### 8. 视觉效果对比

#### 修改前
```
| ID | 名称   | 操作                    |
|----|--------|-------------------------|
| 1  | 项目A  | [确认] [编辑] [删除]    |  ← 按钮宽度不一致
| 2  | 项目B  | [编辑] [删除]           |  ← 缺少确认按钮，错位
| 3  | 项目C  | [确认] [提醒] [编辑] [删除] | ← 4个按钮，更乱
```

#### 修改后
```
| ID | 名称   | 操作                           |
|----|--------|--------------------------------|
| 1  | 项目A  | [确认] [提醒] [编辑] [删除]    |  ← 所有按钮对齐
| 2  | 项目B  | [    ] [    ] [编辑] [删除]    |  ← 占位保留，对齐
| 3  | 项目C  | [确认] [提醒] [编辑] [删除]    |  ← 对齐
```

### 9. 后续优化建议

1. **按钮图标化**: 考虑使用图标代替文字，节省空间
2. **下拉菜单**: 当操作超过4个时，建议使用"更多"下拉菜单
3. **响应式隐藏**: 在极小屏幕上，可以考虑隐藏次要操作按钮
4. **动画效果**: 为按钮添加微交互动画，提升用户体验

---

**更新日期**: 2026-04-08
**版本**: v1.0
**维护者**: AI产业集群空间服务开发团队
