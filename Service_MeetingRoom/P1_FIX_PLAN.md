# 会议室管理系统 P1级别修复计划

**修复时间**: 2026-04-01  
**执行人**: 首席架构师  
**优先级**: P1（高）  
**预计工作量**: 3小时

---

## 一、P1修复目标

### 1.1 核心问题

**问题1：calendar.html未集成**
- ❌ portal/index.html中没有calendar.html入口
- ❌ 用户无法从管理平台访问日历视图
- ❌ calendar.html与会议室系统使用不同的API

**问题2：架构重叠**
- ⚠️ calendar.html使用通用预约API
- ⚠️ Service_MeetingRoom使用专用会议室API
- ⚠️ 两套系统数据模型不同

### 1.2 修复目标

1. **集成calendar.html到portal**
2. **统一API调用**
3. **清晰的功能定位**

---

## 二、修复方案

### 方案A：保留并统一（推荐）✅

**优点**：
- ✅ 日历视图和列表视图互补
- ✅ 提升用户体验
- ✅ 不破坏现有功能

**步骤**：
1. 在portal添加calendar.html入口
2. 重构calendar.html调用会议室API
3. 标明为"日历视图"

---

## 三、具体修复步骤

### 步骤1：在portal添加入口

在portal/index.html的会议室卡片中添加链接：
```html
<a href="../Service_WaterManage/frontend/calendar.html" class="btn-secondary">
    日历视图
</a>
```

### 步骤2：重构calendar.html

**修改点**：
1. API端点改为 `/api/meeting/*`
2. 数据加载改为调用会议室API
3. 创建预约使用会议室字段

**核心代码修改**：
```javascript
// 修改前
const API_BASE = 'http://localhost:8000/api';

// 修改后  
const API_BASE = 'http://localhost:8000/api/meeting';

// 加载预约数据
const loadBookings = async () => {
    const response = await fetch(`${API_BASE}/bookings`);
    bookings.value = await response.json();
};

// 创建预约
const createBooking = async () => {
    const response = await fetch(`${API_BASE}/bookings`, {
        method: 'POST',
        body: JSON.stringify({
            room_id: bookingForm.room_id,
            user_type: bookingForm.user_type,
            office_id: bookingForm.office_id,
            ...
        })
    });
};
```

### 步骤3：调整UI文案

- 标题改为"会议室预约日历"
- 添加提示："日历视图 | 列表视图"
- 统一风格

---

## 四、执行检查清单

- [ ] 备份calendar.html
- [ ] 修改portal/index.html添加入口
- [ ] 重构calendar.html调用会议室API
- [ ] 测试日历视图功能
- [ ] 验证创建预约流程
- [ ] 验证数据一致性

---

## 五、风险评估

| 风险 | 概率 | 应对 |
|-----|------|------|
| API调用失败 | 低 | 充分测试 |
| 数据不一致 | 低 | 使用同一API |
| UI样式冲突 | 低 | 统一样式规范 |

---

**预计完成时间**: 2026-04-01 19:00