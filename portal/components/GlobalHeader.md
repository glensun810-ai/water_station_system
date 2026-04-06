# GlobalHeader 全局导航栏组件

## 功能特性

GlobalHeader是一个统一的全局导航栏组件，提供以下功能：

### 1. 面包屑导航
- 自动显示页面层级导航
- 支持动态配置面包屑项
- 点击面包屑可快速返回上级页面

### 2. 用户信息展示
- 显示用户头像和名称
- 显示当前选择的办公室
- 显示用户角色标签（管理员/超管）

### 3. 办公室设置
- 在用户下拉菜单中提供办公室设置功能
- 支持多办公室管理和切换
- 支持添加新办公室
- 实时保存办公室设置到localStorage

### 4. 用户菜单
- 返回首页
- 我的余额
- 修改密码
- 管理后台（仅管理员可见）
- 退出登录

## 使用方法

### 1. 引入组件

在页面头部引入CSS和JS：

```html
<link rel="stylesheet" href="/portal/assets/css/design-system.css">
<link rel="stylesheet" href="/portal/components/GlobalHeader.css">
<script src="/portal/components/GlobalHeader.js"></script>
```

### 2. 注册组件

在Vue应用中注册GlobalHeader组件：

```javascript
const app = createApp({
    components: {
        'global-header': GlobalHeader
    },
    data() {
        return {
            breadcrumbs: []  // 面包屑导航配置
        }
    }
});
```

### 3. 使用组件

在页面模板中使用组件：

```html
<global-header :breadcrumbs="breadcrumbs"></global-header>
```

### 4. 配置面包屑导航

在页面data中配置面包屑导航：

```javascript
data() {
    return {
        breadcrumbs: [
            { 
                text: '水站服务',    // 显示文本
                icon: '💧',        // 图标（可选）
                url: '/water/index.html'  // 链接地址
            }
        ]
    }
}
```

## 示例

### 首页（无面包屑）

首页作为顶级页面，不需要面包屑导航：

```html
<global-header></global-header>
```

### 子页面（带面包屑）

子页面需要配置面包屑导航：

```html
<global-header :breadcrumbs="breadcrumbs"></global-header>
```

```javascript
data() {
    return {
        breadcrumbs: [
            { text: '水站服务', icon: '💧', url: '/water/index.html' }
        ]
    }
}
```

### 多级面包屑

支持多级面包屑导航：

```javascript
breadcrumbs: [
    { text: '水站服务', icon: '💧', url: '/water/index.html' },
    { text: '订单详情', icon: '📄', url: '/water/orders.html' },
    { text: '订单123', url: '/water/order/123.html' }
]
```

## 办公室功能

### 办公室数据结构

办公室数据保存在localStorage中：

```javascript
localStorage.setItem('user_offices', JSON.stringify({
    offices: [
        { id: 1, name: '总部办公室', location: '3层305室', description: '默认办公室' },
        { id: 2, name: '研发办公室', location: '4层410室', description: '研发团队' }
    ],
    selectedOfficeId: 1  // 当前选择的办公室ID
}));
```

### 办公室切换事件

监听办公室切换事件：

```javascript
mounted() {
    // GlobalHeader会触发office-changed事件
    // 可以通过监听localStorage变化来处理
    window.addEventListener('storage', (event) => {
        if (event.key === 'user_offices') {
            // 办公室切换了，重新加载页面数据
            this.loadData();
        }
    });
}
```

## 样式自定义

GlobalHeader使用设计系统的CSS变量，可以通过修改design-system.css来自定义样式：

```css
:root {
    --primary: #2563EB;  /* 主色调 */
    --spacing-md: 12px;  /* 间距 */
    --radius-md: 8px;    /* 圆角 */
    /* 更多变量见 design-system.css */
}
```

## 响应式设计

GlobalHeader支持完整的响应式设计：

- **桌面端**：显示完整的面包屑、用户信息、办公室名称
- **平板端**：紧凑显示，字号稍小
- **移动端**：
  - 面包屑只显示图标，隐藏文本（首页除外）
  - 用户信息只显示头像
  - 办公室名称隐藏
  - 菜单宽度适配

## 最佳实践

1. **统一引入**：所有服务页面都应该使用GlobalHeader，保持统一的用户体验
2. **面包屑配置**：子页面都应该配置面包屑，方便用户导航
3. **办公室设置**：引导用户设置默认办公室，提升使用体验
4. **数据同步**：监听localStorage变化，及时更新页面数据

## 已集成页面

- ✅ 首页 (/portal/index.html)
- ✅ 水站服务 (/water/index.html)
- 待集成：会议室服务、用餐服务等

## 版本信息

- 版本：v1.0
- 创建时间：2026-04-06
- 作者：AI产业集群开发团队