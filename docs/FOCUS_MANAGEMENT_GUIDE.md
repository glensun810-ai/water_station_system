# 焦点管理最佳实践指南

## 一、焦点管理原则

### 1.1 核心原则

1. **可见性** - 焦点必须清晰可见
2. **逻辑性** - Tab顺序必须符合逻辑
3. **可预测性** - 焦点移动必须可预测
4. **可控制性** - 用户应能控制焦点

### 1.2 WCAG要求

- **2.4.3 Focus Order (Level A)** - 焦点顺序
- **2.4.7 Focus Visible (Level AA)** - 焦点可见
- **3.2.1 On Focus (Level A)** - 焦点时不改变上下文

---

## 二、焦点样式规范

### 2.1 基础焦点样式

已在 design-system.css 中定义：

```css
/* 默认焦点样式 */
:focus {
    outline: 2px solid var(--primary);
    outline-offset: 2px;
}

/* 仅键盘焦点可见 */
:focus:not(:focus-visible) {
    outline: none;
}

:focus-visible {
    outline: 2px solid var(--primary);
    outline-offset: 2px;
}
```

### 2.2 特定元素焦点样式

```css
/* 按钮焦点 */
.btn:focus-visible {
    outline: 2px solid var(--primary);
    outline-offset: 2px;
    box-shadow: 0 0 0 4px var(--primary-light);
}

/* 链接焦点 */
a:focus-visible {
    outline: 2px solid var(--primary);
    outline-offset: 2px;
    text-decoration: underline;
}

/* 输入框焦点 */
.input:focus-visible,
.select:focus-visible {
    outline: none;
    border-color: var(--primary);
    box-shadow: 0 0 0 3px var(--primary-light);
}

/* 卡片焦点 */
.card-clickable:focus-visible {
    outline: 2px solid var(--primary);
    outline-offset: 2px;
    box-shadow: var(--shadow-md);
}
```

---

## 三、Tab顺序管理

### 3.1 自然Tab顺序

HTML元素的默认Tab顺序：
1. `<a>` 有 href 属性
2. `<button>`
3. `<input>` (非hidden)
4. `<select>`
5. `<textarea>`
6. 带有 `tabindex="0"` 的元素

### 3.2 自定义Tab顺序

```html
<!-- 正确：使用自然顺序 -->
<div>
    <input type="text" placeholder="姓名">
    <input type="email" placeholder="邮箱">
    <button>提交</button>
</div>

<!-- 避免：不合理的tabindex -->
<div>
    <button tabindex="3">提交</button> <!-- 错误 -->
    <input type="text" tabindex="1">姓名</input> <!-- 错误 -->
    <input type="email" tabindex="2">邮箱</input> <!-- 错误 -->
</div>

<!-- 合理使用tabindex -->
<div>
    <button tabindex="0">可聚焦按钮</button>
    <span tabindex="-1">不可通过Tab聚焦</span>
</div>
```

### 3.3 Tabindex使用规则

- **`tabindex="0"`** - 元素可通过Tab聚焦，顺序由DOM位置决定
- **`tabindex="-1"`** - 元素不可通过Tab聚焦，但可通过JavaScript聚焦
- **`tabindex="正数"`** - ⚠️ 避免使用，会破坏自然顺序

---

## 四、模态框焦点管理

### 4.1 打开模态框时

```javascript
// 打开模态框
function openModal() {
    const modal = document.getElementById('modal');
    modal.style.display = 'block';
    
    // 聚焦到第一个可交互元素
    const firstFocusable = modal.querySelector(
        'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );
    if (firstFocusable) {
        firstFocusable.focus();
    }
    
    // 添加焦点陷阱
    document.addEventListener('keydown', trapFocus);
}
```

### 4.2 焦点陷阱（Focus Trap）

```javascript
function trapFocus(event) {
    const modal = document.getElementById('modal');
    const focusableElements = modal.querySelectorAll(
        'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );
    
    const firstFocusable = focusableElements[0];
    const lastFocusable = focusableElements[focusableElements.length - 1];
    
    if (event.key === 'Tab') {
        if (event.shiftKey) {
            // Shift + Tab
            if (document.activeElement === firstFocusable) {
                event.preventDefault();
                lastFocusable.focus();
            }
        } else {
            // Tab
            if (document.activeElement === lastFocusable) {
                event.preventDefault();
                firstFocusable.focus();
            }
        }
    }
    
    // Escape 关闭模态框
    if (event.key === 'Escape') {
        closeModal();
    }
}
```

### 4.3 关闭模态框时

```javascript
function closeModal() {
    const modal = document.getElementById('modal');
    modal.style.display = 'none';
    
    // 移除焦点陷阱
    document.removeEventListener('keydown', trapFocus);
    
    // 恢复焦点到触发元素
    if (triggerElement) {
        triggerElement.focus();
    }
}
```

---

## 五、跳过导航链接

### 5.1 实现方式

```html
<body>
    <!-- 跳过导航链接 -->
    <a href="#main-content" class="skip-link">
        跳到主要内容
    </a>
    
    <!-- 导航 -->
    <nav>
        <ul>
            <li><a href="/">首页</a></li>
            <li><a href="/about">关于</a></li>
        </ul>
    </nav>
    
    <!-- 主内容 -->
    <main id="main-content">
        <h1>页面标题</h1>
        <!-- 内容 -->
    </main>
</body>
```

### 5.2 样式

已在 design-system.css 中定义：

```css
.skip-link {
    position: absolute;
    top: -100px;
    left: 0;
    background: var(--primary);
    color: white;
    padding: var(--spacing-md) var(--spacing-lg);
    z-index: 9999;
    text-decoration: none;
    border-radius: 0 0 var(--radius-md) 0;
    transition: top var(--transition-fast);
}

.skip-link:focus {
    top: 0;
}
```

---

## 六、动态内容焦点管理

### 6.1 添加新内容时

```javascript
// 添加新内容并聚焦
function addNewItem() {
    const list = document.getElementById('list');
    const newItem = document.createElement('li');
    newItem.innerHTML = `
        <button>新项目</button>
    `;
    list.appendChild(newItem);
    
    // 聚焦到新添加的按钮
    const button = newItem.querySelector('button');
    button.focus();
}
```

### 6.2 删除内容时

```javascript
// 删除项目并移动焦点
function deleteItem(button) {
    const item = button.closest('li');
    const list = item.parentElement;
    const items = Array.from(list.children);
    const index = items.indexOf(item);
    
    item.remove();
    
    // 聚焦到下一个或上一个项目
    const nextItem = items[index + 1] || items[index - 1];
    if (nextItem) {
        const focusable = nextItem.querySelector('button');
        if (focusable) focusable.focus();
    }
}
```

### 6.3 加载内容时

```javascript
// 加载内容并管理焦点
async function loadContent() {
    const container = document.getElementById('content');
    
    // 显示加载状态
    container.innerHTML = `
        <div role="status" aria-live="polite">
            加载中...
        </div>
    `;
    
    // 加载数据
    const data = await fetchData();
    
    // 更新内容
    container.innerHTML = data;
    
    // 聚焦到新内容的标题
    const heading = container.querySelector('h1, h2, h3');
    if (heading) {
        heading.setAttribute('tabindex', '-1');
        heading.focus();
    }
}
```

---

## 七、焦点可见性最佳实践

### 7.1 避免的做法

```css
/* ❌ 错误：移除所有焦点样式 */
*:focus {
    outline: none;
}

/* ❌ 错误：仅用颜色表示焦点 */
button:focus {
    background-color: blue;
}
```

### 7.2 推荐的做法

```css
/* ✅ 正确：保留鼠标点击时的样式 */
*:focus:not(:focus-visible) {
    outline: none;
}

/* ✅ 正确：键盘焦点清晰可见 */
*:focus-visible {
    outline: 2px solid var(--primary);
    outline-offset: 2px;
}

/* ✅ 正确：增强焦点样式 */
button:focus-visible {
    outline: 2px solid var(--primary);
    outline-offset: 2px;
    box-shadow: 0 0 0 4px var(--primary-light);
}
```

---

## 八、测试检查清单

### 8.1 键盘导航测试

- [ ] 所有交互元素可通过Tab访问
- [ ] Tab顺序符合视觉顺序
- [ ] Shift+Tab可以反向导航
- [ ] Enter/Space可以激活按钮和链接
- [ ] Escape可以关闭模态框
- [ ] 箭头键可以导航列表和菜单

### 8.2 焦点可见性测试

- [ ] 所有可聚焦元素有可见的焦点样式
- [ ] 焦点样式对比度足够（至少3:1）
- [ ] 焦点样式不依赖颜色
- [ ] 焦点样式不会被其他样式覆盖

### 8.3 模态框测试

- [ ] 打开模态框时焦点移到模态框
- [ ] Tab键在模态框内循环
- [ ] Escape键可以关闭模态框
- [ ] 关闭模态框时焦点返回触发元素

### 8.4 屏幕阅读器测试

- [ ] 跳过导航链接可用
- [ ] 焦点变化被正确宣布
- [ ] 动态内容变化被宣布
- [ ] 错误提示被正确宣布

---

## 九、Vue.js焦点管理示例

### 9.1 Vue 3 Composition API

```javascript
import { ref, onMounted, nextTick } from 'vue';

export default {
    setup() {
        const modalRef = ref(null);
        const isOpen = ref(false);
        const triggerElement = ref(null);
        
        const openModal = (event) => {
            triggerElement.value = event.target;
            isOpen.value = true;
            
            nextTick(() => {
                // 聚焦到第一个可交互元素
                const focusable = modalRef.value.querySelector(
                    'button, [href], input, select, textarea'
                );
                if (focusable) focusable.focus();
            });
        };
        
        const closeModal = () => {
            isOpen.value = false;
            // 恢复焦点
            if (triggerElement.value) {
                triggerElement.value.focus();
            }
        };
        
        const handleKeydown = (event) => {
            if (event.key === 'Escape') {
                closeModal();
            }
        };
        
        return {
            modalRef,
            isOpen,
            openModal,
            closeModal,
            handleKeydown
        };
    }
};
```

### 9.2 模板示例

```html
<template>
    <div>
        <button @click="openModal">打开模态框</button>
        
        <div 
            v-if="isOpen" 
            ref="modalRef"
            class="modal-overlay"
            role="dialog"
            aria-modal="true"
            @keydown="handleKeydown"
        >
            <div class="modal-content">
                <h2>模态框标题</h2>
                <button @click="closeModal">关闭</button>
            </div>
        </div>
    </div>
</template>
```

---

## 十、常见问题和解决方案

### 问题1: 焦点样式不显示

**原因**: CSS重置或框架覆盖了默认样式

**解决**:
```css
/* 添加 !important 或更高优先级选择器 */
button:focus-visible {
    outline: 2px solid var(--primary) !important;
    outline-offset: 2px !important;
}
```

### 问题2: 模态框外元素可聚焦

**原因**: 缺少焦点陷阱

**解决**: 实现焦点陷阱或使用 aria-hidden="true" 隐藏背景内容

### 问题3: 动态内容焦点丢失

**原因**: 内容更新后焦点未重新设置

**解决**: 使用 Vue的 nextTick 或 setTimeout 确保DOM更新后再聚焦

---

**最后更新**: 2026-04-08  
**标准**: WCAG 2.1 AA  
**状态**: 已实施