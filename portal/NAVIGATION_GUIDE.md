# 面包屑导航规范

## 一、导航层级体系

本系统采用**三层级面包屑导航**，确保用户在任何页面都能清楚地了解自己在系统中的位置。

### 层级结构

```
第1层：首页（固定根节点）
  🏢 AI产业集群空间服务
  URL: /portal/index.html

第2层：管理中心（所有管理功能入口）
  ⚙️ 管理中心
  URL: /portal/index.html
  说明：管理中心在首页内部，所以链接指向首页

第3层：功能模块（具体管理页面）
  各功能模块独立页面
```

### 页面分类与面包屑配置

#### 系统管理模块
- 🏢 **办公室管理** `/portal/admin/offices.html`
  面包屑：`管理中心 > 办公室管理`

- 👥 **用户管理** `/portal/admin/users.html`
  面包屑：`管理中心 > 用户管理`

- 📝 **登录日志** `/portal/admin/login-logs.html`
  面包屑：`管理中心 > 登录日志`

#### 财务管理模块
- 💰 **结算管理** `/portal/admin/settlements.html`
  面包屑：`管理中心 > 结算管理`

#### 会员管理模块
- 👑 **会员套餐管理** `/portal/admin/membership-plans.html`
  面包屑：`管理中心 > 会员套餐管理`

## 二、使用 GlobalHeader 组件

### 基本用法

所有管理后台页面都应该使用 `GlobalHeader` 组件，并传入正确的 `breadcrumbs` 属性。

```html
<!-- 在 head 中引入必要的资源 -->
<link rel="stylesheet" href="../components/GlobalHeader.css">
<script src="../components/GlobalHeader.js"></script>

<!-- 在 Vue app 中注册组件 -->
components: { 'global-header': GlobalHeader }

<!-- 在页面中使用 -->
<global-header :breadcrumbs="breadcrumbs"></global-header>
```

### breadcrumbs 属性格式

```javascript
const breadcrumbs = [
  {
    text: '管理中心',
    icon: '⚙️',
    url: '/portal/index.html'
  },
  {
    text: '办公室管理',
    icon: '🏢',
    url: '/portal/admin/offices.html'
  }
];
```

### 完整示例

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <!-- ... 其他 meta 标签 ... -->
    <link rel="stylesheet" href="../components/GlobalHeader.css">
    <script src="../components/GlobalHeader.js"></script>
</head>
<body>
    <div id="app" v-cloak>
        <!-- 添加面包屑导航 -->
        <global-header 
            :breadcrumbs="[
                {text: '管理中心', icon: '⚙️', url: '/portal/index.html'},
                {text: '办公室管理', icon: '🏢', url: '/portal/admin/offices.html'}
            ]">
        </global-header>
        
        <div class="page-container">
            <!-- 页面内容 -->
        </div>
    </div>
    
    <script>
        createApp({
            components: { 'global-header': GlobalHeader },
            // ... 其他配置 ...
        }).mount('#app');
    </script>
</body>
</html>
```

## 三、设计原则

### 1. 层级完整性原则
面包屑必须反映用户真实的导航路径，不得缺失中间层级。

❌ **错误示例**：
```
AI产业集群空间服务 > 办公室管理
（缺少"管理中心"层级）
```

✅ **正确示例**：
```
AI产业集群空间服务 > ⚙️ 管理中心 > 🏢 办公室管理
```

### 2. 一致性原则
同类页面的面包屑结构必须保持一致。

| 页面类型 | 面包屑层级 |
|---------|-----------|
| 系统管理页面 | 首页 > 管理中心 > 功能名 |
| 服务管理页面 | 首页 > 管理中心 > 功能名 |
| 子功能页面 | 首页 > 管理中心 > 功能 > 子功能 |

### 3. 可点击性原则
- 所有面包屑项（除了当前页）都应该是可点击的链接
- 点击后应跳转到对应的页面
- 当前页的面包屑项应该有视觉区分（高亮或不可点击）

### 4. 图标一致性
每个功能模块应该使用固定的图标：

| 功能模块 | 图标 | 说明 |
|---------|-----|------|
| 首页 | 🏢 | 固定，所有页面根节点 |
| 管理中心 | ⚙️ | 固定，第2层级 |
| 办公室管理 | 🏢 | 功能图标 |
| 用户管理 | 👥 | 功能图标 |
| 结算管理 | 💰 | 功能图标 |
| 会员套餐 | 👑 | 功能图标 |
| 登录日志 | 📝 | 功能图标 |
| 水站管理 | 💧 | 服务图标 |
| 会议室管理 | 📅 | 服务图标 |

## 四、特殊情况处理

### 1. 多级子页面

如果一个功能有子页面（如详情页、编辑页），面包屑应该包含父功能：

```javascript
// 示例：办公室详情页
breadcrumbs = [
  {text: '管理中心', icon: '⚙️', url: '/portal/index.html'},
  {text: '办公室管理', icon: '🏢', url: '/portal/admin/offices.html'},
  {text: '办公室详情', icon: '📋', url: '/portal/admin/offices-detail.html'}
]
```

### 2. 非管理页面

用户前端页面（如个人中心、订单页）不需要"管理中心"层级：

```javascript
// 示例：个人中心
breadcrumbs = [
  {text: '个人中心', icon: '👤', url: '/portal/membership.html'}
]
```

### 3. 无面包屑页面

某些页面可能不需要面包屑（如登录页、注册页），可以不传入 breadcrumbs：

```html
<!-- 不传 breadcrumbs，只显示根链接 -->
<global-header></global-header>
```

## 五、最佳实践检查清单

在开发新页面时，请确认以下几点：

- [ ] 是否引入了 GlobalHeader.css 和 GlobalHeader.js？
- [ ] 是否在 Vue components 中注册了 'global-header'？
- [ ] 是否传入了正确的 breadcrumbs 属性？
- [ ] breadcrumbs 是否包含完整的层级（首页 + 管理中心 + 功能名）？
- [ ] 每个面包屑项是否都有正确的 text、icon、url？
- [ ] icon 是否与功能模块的图标规范一致？
- [ ] url 是否指向正确的页面路径？
- [ ] 是否在移动端测试了面包屑的显示效果？

## 六、已修复页面列表

以下页面已按照本规范完成面包屑导航修复：

| 页面 | 修复内容 | 状态 |
|------|---------|-----|
| offices.html | 添加"管理中心"层级 | ✅ |
| users.html | 添加 GlobalHeader 和面包屑 | ✅ |
| settlements.html | 添加"管理中心"层级 | ✅ |
| login-logs.html | 添加完整面包屑 | ✅ |
| membership-plans.html | 修正层级名称 | ✅ |

## 七、用户体验提升

### 修复前后对比

**修复前：**
```
🏢 AI产业集群空间服务 > 🏢 办公室管理
用户不知道这是管理功能，缺少上下文
```

**修复后：**
```
🏢 AI产业集群空间服务 > ⚙️ 管理中心 > 🏢 办公室管理
清晰的层级结构，用户了解当前位置
```

### 用户获益

1. **清晰的定位感** - 用户知道自己在系统的哪个位置
2. **快速导航** - 可以通过面包屑快速返回上级
3. **一致体验** - 所有页面导航体验统一
4. **减少困惑** - 不再有导航层级缺失导致的迷失感

## 八、维护指南

### 新增页面

1. 确定页面属于哪个层级（管理页面或用户页面）
2. 根据规范配置面包屑
3. 使用正确的图标和链接
4. 测试面包屑的显示和导航功能

### 修改页面

1. 检查当前面包屑是否符合规范
2. 如果不符合，按照规范修正
3. 更新 NAVIGATION_GUIDE.md 文档

### 定期检查

建议每季度检查所有页面的面包屑导航是否仍然符合规范，特别是在进行大规模重构后。

---

**最后更新时间**: 2026-04-08  
**维护负责人**: 系统架构师团队  
**版本**: v1.0