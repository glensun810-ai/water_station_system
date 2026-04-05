# 公共组件库使用指南

**版本**: v1.0  
**创建时间**: 2026-04-05  
**用途**: AI产业集群空间服务系统统一组件库

---

## 一、组件库概述

本组件库旨在统一水站管理和会议室预定系统的前端UI组件，减少代码冗余，提高开发效率。

### 目录结构

```
portal/
├── assets/
│   └── css/
│       └── design-system.css       # 统一设计系统样式
├── components/
│   ├── common/                      # 通用组件
│   │   ├── OfficeSelector.vue      # 办公室选择
│   │   ├── StatsCard.vue           # 统计卡片
│   │   ├── ConfirmDialog.vue       # 确认对话框
│   │   ├── FilterButton.vue        # 筛选按钮
│   │   └── DatePicker.vue          # 日期选择器
│   └── business/                    # 业务组件
│       └── OrderList.vue           # 订单列表
└── docs/
    └── README.md                    # 本文档
```

---

## 二、快速开始

### 2.1 引入设计系统样式

在HTML文件头部引入设计系统样式：

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>页面标题</title>
    <!-- 引入设计系统样式 -->
    <link rel="stylesheet" href="../assets/css/design-system.css">
    <!-- 引入Vue 3 -->
    <script src="https://unpkg.com/vue@3/dist/vue.global.js"></script>
</head>
<body>
    <!-- 页面内容 -->
</body>
</html>
```

### 2.2 引入组件

在Vue应用中引入组件：

```javascript
const { createApp } = Vue;

// 引入组件
import OfficeSelector from '../components/common/OfficeSelector.js';
import StatsCard from '../components/common/StatsCard.js';
import ConfirmDialog from '../components/common/ConfirmDialog.js';

const app = createApp({
    // 应用配置
});

// 注册组件
app.component('OfficeSelector', OfficeSelector);
app.component('StatsCard', StatsCard);
app.component('ConfirmDialog', ConfirmDialog);

app.mount('#app');
```

---

## 三、组件详细文档

### 3.1 OfficeSelector - 办公室选择组件

**用途**: 统一的办公室选择界面，用于水站领水和会议室预定。

**示例代码**:

```html
<template>
  <div>
    <OfficeSelector
      v-model="selectedOffice"
      :exclude-inactive="true"
      :show-leader="true"
      :columns="2"
      @change="handleOfficeChange"
    />
  </div>
</template>

<script>
export default {
  data() {
    return {
      selectedOffice: null
    }
  },
  methods: {
    handleOfficeChange(office) {
      console.log('选中的办公室:', office);
      // 处理办公室选择逻辑
    }
  }
}
</script>
```

**Props参数**:

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| modelValue | Object | null | 当前选中的办公室对象（支持v-model） |
| excludeInactive | Boolean | true | 是否排除不活跃办公室 |
| apiUrl | String | '/api/offices' | 自定义API地址 |
| showLeader | Boolean | true | 是否显示负责人 |
| columns | Number | 2 | 每行显示列数（移动端自动调整为1） |

**Events事件**:

| 事件名 | 参数 | 说明 |
|--------|------|------|
| update:modelValue | office: Object | v-model更新事件 |
| change | office: Object | 办公室选择变化时触发 |
| load | offices: Array | 办公室列表加载完成时触发 |

---

### 3.2 StatsCard - 统计卡片组件

**用途**: Dashboard统计卡片，显示关键数据指标。

**示例代码**:

```html
<template>
  <div class="grid grid-cols-4 gap-md">
    <StatsCard
      title="今日预约"
      :value="23"
      icon="📅"
      color="primary"
      :trend="10"
      trend-label="较昨日"
      clickable
      @click="handleCardClick"
    />
    
    <StatsCard
      title="待审批"
      :value="5"
      icon="⏳"
      color="warning"
    />
    
    <StatsCard
      title="总收入"
      :value="1234.56"
      icon="💰"
      color="success"
      subtitle="本月累计"
    />
  </div>
</template>
```

**Props参数**:

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| title | String | - | 统计标题（必填） |
| value | Number/String | 0 | 统计数值 |
| subtitle | String | '' | 副标题 |
| icon | String | '📊' | 图标（emoji或class名） |
| iconType | String | 'emoji' | 图标类型（'emoji' 或 'class'） |
| color | String | 'primary' | 颜色主题（primary/success/warning/danger/info） |
| trend | Number | undefined | 趋势值（正数上升，负数下降） |
| trendLabel | String | '较昨日' | 趋势标签 |
| clickable | Boolean | false | 是否可点击 |
| loading | Boolean | false | 加载状态 |

---

### 3.3 ConfirmDialog - 确认对话框组件

**用途**: 统一的确认对话框，用于删除、取消等操作确认。

**示例代码**:

```html
<template>
  <div>
    <button @click="showDialog = true">删除</button>
    
    <ConfirmDialog
      v-model="showDialog"
      title="确认删除"
      message="删除后无法恢复，是否继续？"
      type="danger"
      confirm-text="删除"
      @confirm="handleConfirm"
      @cancel="handleCancel"
    />
  </div>
</template>

<script>
export default {
  data() {
    return {
      showDialog: false
    }
  },
  methods: {
    async handleConfirm() {
      // 执行删除操作
      await this.deleteItem();
      this.showDialog = false;
    },
    handleCancel() {
      console.log('取消删除');
    }
  }
}
</script>
```

**Props参数**:

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| modelValue | Boolean | false | 是否显示对话框（支持v-model） |
| title | String | '确认操作' | 对话框标题 |
| message | String | - | 对话框消息 |
| type | String | 'info' | 对话框类型（info/warning/danger） |
| confirmText | String | '确认' | 确认按钮文字 |
| cancelText | String | '取消' | 取消按钮文字 |
| inputLabel | String | '' | 输入框标签（可选，设置后显示输入框） |
| inputPlaceholder | String | '' | 输入框占位符 |
| loading | Boolean | false | 确认按钮加载状态 |

---

### 3.4 FilterButton - 筛选按钮组件

**用途**: Tab切换和状态筛选按钮。

**示例代码**:

```html
<template>
  <!-- Segment类型 -->
  <FilterButton
    v-model="activeFilter"
    :options="filterOptions"
    type="segment"
    @change="handleFilterChange"
  />
  
  <!-- Tab类型 -->
  <FilterButton
    v-model="activeTab"
    :options="tabOptions"
    type="tab"
  />
  
  <!-- Card类型 -->
  <FilterButton
    v-model="statusFilter"
    :options="statusOptions"
    type="card"
    :show-count="true"
  />
</template>

<script>
export default {
  data() {
    return {
      activeFilter: 'pending',
      filterOptions: [
        { label: '待确认', value: 'pending', count: 5 },
        { label: '已确认', value: 'confirmed', count: 10 },
        { label: '已取消', value: 'cancelled', count: 2 }
      ]
    }
  },
  methods: {
    handleFilterChange(value, option) {
      console.log('筛选变化:', value, option);
    }
  }
}
</script>
```

**Props参数**:

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| modelValue | String/Number | - | 当前选中的值（必填） |
| options | Array | - | 选项数组（必填） |
| type | String | 'segment' | 按钮类型（segment/tab/card） |
| showCount | Boolean | false | 是否显示数量徽章 |
| disabled | Boolean | false | 是否禁用 |

**options数组格式**:

```javascript
[
  {
    label: '待确认',  // 显示文字
    value: 'pending', // 选项值
    count: 5,         // 数量（可选）
    icon: '⏳'        // 图标（可选）
  }
]
```

---

### 3.5 DatePicker - 日期选择器组件

**用途**: 统一的日期选择器，支持快捷日期选择。

**示例代码**:

```html
<template>
  <!-- 基础日期选择 -->
  <DatePicker
    v-model="selectedDate"
    placeholder="选择日期"
    @change="handleDateChange"
  />
  
  <!-- 带快捷选择的日期选择器 -->
  <DatePicker
    v-model="selectedDate"
    :show-quick-select="true"
    @change="handleDateChange"
  />
</template>
```

**Props参数**:

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| modelValue | String/Date | '' | 选中的日期（支持v-model） |
| placeholder | String | '选择日期' | 占位符文字 |
| minDate | String/Date | null | 最小日期 |
| maxDate | String/Date | null | 最大日期 |
| disabled | Boolean | false | 是否禁用 |
| clearable | Boolean | true | 是否可清空 |
| showQuickSelect | Boolean | false | 是否显示快捷选择 |

---

### 3.6 OrderList - 订单列表组件

**用途**: 统一的订单列表查询，支持水站领水记录和会议室预约记录。

**示例代码**:

```html
<template>
  <OrderList
    :api-url="'/api/user/office-pickups'"
    :type="'water'"
    :tabs="orderTabs"
    :show-search="true"
    :show-status-filter="true"
    @item-click="handleItemClick"
    @load="handleLoad"
  />
</template>

<script>
export default {
  data() {
    return {
      orderTabs: [
        { label: '我的订单', value: 'mine' },
        { label: '全部订单', value: 'all' }
      ]
    }
  },
  methods: {
    handleItemClick(order) {
      console.log('点击订单:', order);
    },
    handleLoad(orders) {
      console.log('加载订单:', orders.length);
    }
  }
}
</script>
```

**Props参数**:

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| apiUrl | String | - | API地址（必填） |
| type | String | 'water' | 订单类型（water/meeting） |
| tabs | Array | [] | Tab配置 |
| statusOptions | Array | [...] | 状态选项 |
| showSearch | Boolean | true | 是否显示搜索框 |
| showStatusFilter | Boolean | true | 是否显示状态筛选 |

---

## 四、设计系统样式类

### 4.1 颜色系统

```css
/* 主色 */
--primary: #2563EB;
--primary-hover: #1D4ED8;
--primary-light: #DBEAFE;

/* 功能色 */
--success: #10B981;
--warning: #F59E0B;
--danger: #EF4444;
--info: #3B82F6;
```

### 4.2 间距系统

```css
--spacing-xs: 4px;
--spacing-sm: 8px;
--spacing-md: 12px;
--spacing-lg: 16px;
--spacing-xl: 24px;
--spacing-2xl: 32px;
```

### 4.3 常用工具类

```html
<!-- Flex布局 -->
<div class="flex items-center justify-between gap-md">
  <span>左侧内容</span>
  <span>右侧内容</span>
</div>

<!-- Grid布局 -->
<div class="grid grid-cols-2 gap-lg">
  <div>卡片1</div>
  <div>卡片2</div>
</div>

<!-- 文字截断 -->
<p class="truncate">这是一段很长的文字，会被截断显示</p>

<!-- 隐藏滚动条 -->
<div class="scrollbar-hide">内容区域</div>
```

---

## 五、最佳实践

### 5.1 组件组合使用

```html
<template>
  <div class="dashboard">
    <!-- 统计卡片区域 -->
    <div class="grid grid-cols-4 gap-lg mb-xl">
      <StatsCard title="今日预约" :value="23" icon="📅" color="primary" />
      <StatsCard title="待审批" :value="5" icon="⏳" color="warning" />
      <StatsCard title="已完成" :value="45" icon="✅" color="success" />
      <StatsCard title="总收入" :value="1234.56" icon="💰" color="info" />
    </div>
    
    <!-- 筛选区域 -->
    <div class="filter-section mb-lg">
      <FilterButton
        v-model="statusFilter"
        :options="statusOptions"
        type="segment"
      />
    </div>
    
    <!-- 列表区域 -->
    <OrderList
      :api-url="apiUrl"
      :type="'meeting'"
      @item-click="handleItemClick"
    />
  </div>
</template>
```

### 5.2 移动端适配

所有组件均已适配移动端，只需引入设计系统样式即可自动生效：

```html
<!-- 移动端会自动适配 -->
<meta name="viewport" content="width=device-width, initial-scale=1.0">

<!-- 组件会自动调整布局 -->
<OfficeSelector :columns="2" /> <!-- 移动端自动变为1列 -->
```

---

## 六、注意事项

1. **样式引入**: 确保先引入`design-system.css`再使用组件
2. **Vue版本**: 所有组件基于Vue 3开发，请使用Vue 3.x版本
3. **API接口**: 组件依赖后端API，请确保API接口返回正确的数据格式
4. **移动端测试**: 开发完成后请在移动设备上测试组件表现

---

## 七、更新日志

### v1.0 (2026-04-05)
- ✅ 创建统一设计系统样式
- ✅ 开发OfficeSelector组件
- ✅ 开发StatsCard组件
- ✅ 开发ConfirmDialog组件
- ✅ 开发FilterButton组件
- ✅ 开发DatePicker组件
- ✅ 开发OrderList组件
- ✅ 编写组件使用文档

---

**维护者**: AI产业集群空间服务系统开发团队  
**联系方式**: 项目GitHub仓库