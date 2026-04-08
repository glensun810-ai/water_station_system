# ARIA可访问性标签使用指南

## 一、核心原则

### WCAG 2.1 可访问性原则

1. **可感知（Perceivable）** - 信息必须能被用户感知
2. **可操作（Operable）** - 界面组件必须能被操作
3. **可理解（Understandable）** - 信息和操作必须易于理解
4. **健壮性（Robust）** - 内容必须足够健壮以适应各种用户代理

---

## 二、ARIA标签使用规范

### 2.1 页面结构标签

#### 主导航
```html
<nav role="navigation" aria-label="主导航">
    <ul>
        <li><a href="/">首页</a></li>
        <li><a href="/about">关于</a></li>
    </ul>
</nav>
```

#### 主内容区域
```html
<main role="main" aria-label="主要内容">
    <!-- 页面主要内容 -->
</main>
```

#### 侧边栏
```html
<aside role="complementary" aria-label="侧边栏">
    <!-- 侧边栏内容 -->
</aside>
```

#### 页脚
```html
<footer role="contentinfo" aria-label="页脚">
    <!-- 页脚内容 -->
</footer>
```

### 2.2 交互组件标签

#### 按钮
```html
<!-- 普通按钮 -->
<button aria-label="关闭">×</button>

<!-- 带图标的按钮 -->
<button aria-label="搜索">
    <span aria-hidden="true">🔍</span>
</button>

<!-- 切换按钮 -->
<button aria-pressed="false" aria-label="收藏">
    收藏
</button>
```

#### 链接
```html
<!-- 外部链接 -->
<a href="https://example.com" target="_blank" aria-label="访问示例网站（新窗口打开）">
    示例网站
</a>

<!-- 带图标的链接 -->
<a href="/profile" aria-label="用户资料">
    <span aria-hidden="true">👤</span>
    <span>资料</span>
</a>
```

#### 表单元素
```html
<!-- 输入框 -->
<label for="username">用户名</label>
<input type="text" id="username" name="username" 
       aria-required="true"
       aria-describedby="username-hint">
<span id="username-hint">请输入您的用户名</span>

<!-- 错误状态 -->
<input type="text" 
       aria-invalid="true"
       aria-describedby="username-error">
<span id="username-error" role="alert">用户名不能为空</span>

<!-- 选择框 -->
<label for="country">国家</label>
<select id="country" name="country" aria-required="true">
    <option value="">请选择</option>
    <option value="cn">中国</option>
</select>
```

### 2.3 模态框标签

```html
<div class="modal-overlay" 
     role="dialog" 
     aria-modal="true" 
     aria-labelledby="modal-title"
     aria-describedby="modal-desc">
    
    <div class="modal-content">
        <h2 id="modal-title">确认删除</h2>
        <p id="modal-desc">您确定要删除此项目吗？此操作无法撤销。</p>
        
        <button aria-label="关闭对话框">×</button>
        
        <div class="modal-footer">
            <button class="btn btn-secondary">取消</button>
            <button class="btn btn-danger">删除</button>
        </div>
    </div>
</div>
```

### 2.4 列表和表格标签

#### 列表
```html
<ul role="list" aria-label="功能列表">
    <li role="listitem">功能1</li>
    <li role="listitem">功能2</li>
</ul>

<!-- 带数量的列表 -->
<ul role="list" aria-label="购物车商品（3件）">
    <li>商品1</li>
    <li>商品2</li>
    <li>商品3</li>
</ul>
```

#### 表格
```html
<table role="table" aria-label="用户列表">
    <caption>系统用户列表</caption>
    <thead>
        <tr>
            <th scope="col">姓名</th>
            <th scope="col">邮箱</th>
            <th scope="col">角色</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td>张三</td>
            <td>zhangsan@example.com</td>
            <td>管理员</td>
        </tr>
    </tbody>
</table>
```

### 2.5 状态和动态内容标签

#### 加载状态
```html
<!-- 加载中 -->
<div role="status" aria-live="polite" aria-label="加载中">
    <div class="spinner" aria-hidden="true"></div>
    <span>加载中，请稍候...</span>
</div>

<!-- 进度条 -->
<div role="progressbar" 
     aria-valuenow="60" 
     aria-valuemin="0" 
     aria-valuemax="100"
     aria-label="上传进度">
    <div style="width: 60%"></div>
</div>
```

#### 提示和通知
```html
<!-- 即时通知 -->
<div role="alert" aria-live="assertive">
    操作成功完成
</div>

<!-- 状态更新 -->
<div role="status" aria-live="polite">
    已保存更改
</div>

<!-- 错误提示 -->
<div role="alert" aria-live="assertive">
    <strong>错误：</strong>网络连接失败
</div>
```

### 2.6 隐藏内容

#### 从视觉和辅助技术中隐藏
```html
<div style="display: none;" aria-hidden="true">
    完全隐藏的内容
</div>
```

#### 仅从视觉隐藏（屏幕阅读器可见）
```html
<span class="sr-only">仅屏幕阅读器可见的内容</span>
```

#### 仅从辅助技术隐藏
```html
<div aria-hidden="true">
    视觉可见但屏幕阅读器忽略的内容
</div>
```

---

## 三、实际应用示例

### 3.1 首页（index.html）

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>首页 - AI产业集群空间服务</title>
</head>
<body>
    <!-- 跳过导航链接 -->
    <a href="#main-content" class="skip-link">跳到主要内容</a>
    
    <!-- 头部导航 -->
    <header role="banner">
        <nav role="navigation" aria-label="主导航">
            <ul>
                <li><a href="/" aria-current="page">首页</a></li>
                <li><a href="/services">服务</a></li>
                <li><a href="/about">关于</a></li>
            </ul>
        </nav>
    </header>
    
    <!-- 主内容 -->
    <main id="main-content" role="main" aria-label="主要内容">
        <h1>欢迎来到AI产业集群空间服务</h1>
        
        <!-- 服务卡片 -->
        <section aria-labelledby="services-heading">
            <h2 id="services-heading">我们的服务</h2>
            <ul role="list">
                <li>
                    <article aria-labelledby="service-1">
                        <h3 id="service-1">水站服务</h3>
                        <p>饮用水订购与管理</p>
                        <a href="/water" aria-label="了解更多水站服务">
                            了解更多
                        </a>
                    </article>
                </li>
            </ul>
        </section>
    </main>
    
    <!-- 页脚 -->
    <footer role="contentinfo" aria-label="页脚">
        <p>&copy; 2026 AI产业集群空间服务</p>
    </footer>
</body>
</html>
```

### 3.2 管理后台页面

```html
<div id="app">
    <!-- GlobalHeader 组件 -->
    <header role="banner">
        <nav role="navigation" aria-label="面包屑导航">
            <ol>
                <li><a href="/">首页</a></li>
                <li><a href="/admin">管理中心</a></li>
                <li aria-current="page">用户管理</li>
            </ol>
        </nav>
    </header>
    
    <!-- 主内容 -->
    <main role="main" aria-label="用户管理">
        <!-- 加载状态 -->
        <div v-if="loading" role="status" aria-live="polite">
            <div class="spinner" aria-hidden="true"></div>
            <span>加载中...</span>
        </div>
        
        <!-- 错误状态 -->
        <div v-if="error" role="alert" aria-live="assertive">
            <strong>错误：</strong>{{ error }}
        </div>
        
        <!-- 用户列表 -->
        <table role="table" aria-label="用户列表">
            <thead>
                <tr>
                    <th scope="col">姓名</th>
                    <th scope="col">邮箱</th>
                    <th scope="col">操作</th>
                </tr>
            </thead>
            <tbody>
                <tr v-for="user in users" :key="user.id">
                    <td>{{ user.name }}</td>
                    <td>{{ user.email }}</td>
                    <td>
                        <button :aria-label="'编辑用户 ' + user.name">
                            编辑
                        </button>
                    </td>
                </tr>
            </tbody>
        </table>
    </main>
    
    <!-- 模态框 -->
    <div v-if="showModal" 
         class="modal-overlay"
         role="dialog"
         aria-modal="true"
         aria-labelledby="modal-title">
        <div class="modal-content">
            <h2 id="modal-title">编辑用户</h2>
            <!-- 表单内容 -->
        </div>
    </div>
</div>
```

---

## 四、检查清单

### 4.1 页面级检查

- [ ] 所有页面都有唯一的 `<title>`
- [ ] 页面语言正确设置（`lang="zh-CN"`）
- [ ] 包含跳过导航链接（skip link）
- [ ] 页面结构清晰（header, nav, main, footer）
- [ ] 标题层级正确（h1 > h2 > h3）

### 4.2 交互组件检查

- [ ] 所有链接有描述性文本或 aria-label
- [ ] 所有按钮有可识别的文本或 aria-label
- [ ] 表单元素有关联的 label
- [ ] 必填字段标记为 aria-required
- [ ] 错误消息使用 role="alert"

### 4.3 图片和媒体检查

- [ ] 所有图片有 alt 属性
- [ ] 装饰性图片使用 alt="" 或 aria-hidden="true"
- [ ] 复杂图片有长描述
- [ ] 视频有字幕和描述

### 4.4 动态内容检查

- [ ] 加载状态有 role="status"
- [ ] 错误提示有 role="alert"
- [ ] 动态更新使用 aria-live
- [ ] 进度条有正确的 ARIA 属性

### 4.5 键盘可访问性检查

- [ ] 所有交互元素可通过键盘访问
- [ ] Tab 顺序逻辑合理
- [ ] 焦点可见
- [ ] 模态框焦点陷阱正确

---

## 五、测试工具

### 5.1 自动化测试工具

1. **Lighthouse** - Chrome DevTools
2. **axe DevTools** - 浏览器扩展
3. **WAVE** - Web Accessibility Evaluation Tool
4. **Pa11y** - 命令行工具

### 5.2 手动测试

1. **键盘导航测试**
   - 使用 Tab 键遍历所有交互元素
   - 使用 Enter/Space 激活按钮和链接
   - 使用 Escape 关闭模态框

2. **屏幕阅读器测试**
   - macOS: VoiceOver
   - Windows: NVDA
   - iOS: VoiceOver
   - Android: TalkBack

3. **缩放测试**
   - 200% 缩放测试
   - 文字放大测试

---

## 六、常见错误和修复

### 错误1: 缺少alt属性
```html
<!-- 错误 -->
<img src="logo.png">

<!-- 正确 -->
<img src="logo.png" alt="AI产业集群空间服务logo">
```

### 错误2: 空链接
```html
<!-- 错误 -->
<a href="#"></a>

<!-- 正确 -->
<a href="#" aria-label="返回顶部">返回顶部</a>
```

### 错误3: 没有label的表单
```html
<!-- 错误 -->
<input type="text" placeholder="搜索">

<!-- 正确 -->
<label for="search" class="sr-only">搜索</label>
<input type="text" id="search" placeholder="搜索">
```

### 错误4: 仅用颜色表示状态
```html
<!-- 错误 -->
<span style="color: red;">错误</span>

<!-- 正确 -->
<span role="alert" style="color: var(--danger);">
    <span aria-hidden="true">⚠️</span>
    错误
</span>
```

---

## 七、优先级建议

### 高优先级（立即修复）

1. 主要导航和内容区域的 ARIA 标签
2. 表单元素的可访问性
3. 错误提示和通知的可访问性
4. 模态框的可访问性

### 中优先级（近期优化）

1. 加载状态的完善
2. 列表和表格的优化
3. 图标按钮的可访问性

### 低优先级（后续提升）

1. 跳过导航链接
2. 高级 ARIA 属性
3. 动画和过渡的可访问性

---

**最后更新**: 2026-04-08  
**标准**: WCAG 2.1 AA  
**状态**: 待实施