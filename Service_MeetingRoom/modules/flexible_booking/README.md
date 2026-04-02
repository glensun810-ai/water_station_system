# 灵活时间段选择模块使用指南

## 概述

本模块是会议室管理模块优化计划（阶段一P0）的第一个核心功能，实现了灵活的时间段选择、冲突检测和时长验证。

## 快速开始

### 1. 安装依赖

```bash
# 已安装项目基础依赖
pip install fastapi sqlalchemy pydantic
```

### 2. 注册路由

在 `Service_WaterManage/backend/main.py` 中添加：

```python
from Service_MeetingRoom.modules.flexible_booking.api_flexible_booking import router as flexible_router

app.include_router(flexible_router)
```

### 3. 启动服务

```bash
cd Service_WaterManage/backend
python main.py
```

## API接口文档

### 1. 检查时间段可用性

**接口**：`POST /api/meeting/flexible/check-time-slot`

**功能**：验证时间段格式、计算时长、检查冲突

**请求示例**：

```json
{
  "room_id": 1,
  "booking_date": "2026-04-02",
  "start_time": "09:00",
  "end_time": "12:00"
}
```

**响应示例（可用）**：

```json
{
  "is_available": true,
  "conflict_count": 0,
  "duration_minutes": 180,
  "duration_hours": 3.0,
  "is_valid": true,
  "message": "时间段可用",
  "warnings": []
}
```

**响应示例（冲突）**：

```json
{
  "is_available": false,
  "conflict_count": 1,
  "duration_minutes": 180,
  "duration_hours": 3.0,
  "is_valid": true,
  "message": "时间段冲突：已有1个预约",
  "warnings": ["该时间段已有1个预约冲突"]
}
```

**响应示例（时长无效）**：

```json
{
  "is_available": false,
  "duration_minutes": 15,
  "duration_hours": 0.25,
  "is_valid": false,
  "message": "预约时长不能少于30分钟",
  "warnings": ["预约时长不能少于30分钟"]
}
```

### 2. 获取可用时段列表

**接口**：`GET /api/meeting/flexible/available-slots/{room_id}/{booking_date}`

**功能**：查询某会议室某天的所有可用时段（30分钟粒度）

**请求示例**：

```
GET /api/meeting/flexible/available-slots/1/2026-04-02
```

**响应示例**：

```json
{
  "room_id": 1,
  "booking_date": "2026-04-02",
  "available_slots": [
    {"time": "07:00", "end_time": "07:30", "is_available": true, "duration": 30},
    {"time": "07:30", "end_time": "08:00", "is_available": true, "duration": 30},
    {"time": "08:00", "end_time": "08:30", "is_available": true, "duration": 30},
    // ... 更多时段
    {"time": "09:00", "end_time": "09:30", "is_available": false, "duration": 30},  // 已占用
    // ...
  ],
  "booked_slots": [
    ["09:00", "10:30"],
    ["14:00", "16:00"]
  ],
  "total_slots": 30,
  "available_count": 26
}
```

### 3. 获取快捷时段选项

**接口**：`GET /api/meeting/flexible/quick-slots`

**功能**：提供常用时间段快捷选项

**响应示例**：

```json
{
  "quick_slots": [
    {"label": "上午（09:00-12:00）", "start": "09:00", "end": "12:00"},
    {"label": "下午（14:00-18:00）", "start": "14:00", "end": "18:00"},
    {"label": "晚上（19:00-21:00）", "start": "19:00", "end": "21:00"}
  ],
  "message": "快捷时段选项，用户可快速选择常用时间段"
}
```

## 前端集成示例

### Vue.js 3 组件示例

```html
<template>
  <div class="time-picker">
    <!-- 时间选择器 -->
    <div class="time-inputs">
      <label>开始时间</label>
      <input type="time" v-model="booking.start_time" min="07:00" max="22:00" step="1800">
      
      <label>结束时间</label>
      <input type="time" v-model="booking.end_time" min="07:00" max="22:00" step="1800">
    </div>
    
    <!-- 快捷时段按钮 -->
    <div class="quick-slots">
      <button v-for="slot in quickSlots" 
              :key="slot.label"
              @click="selectQuickSlot(slot)">
        {{ slot.label }}
      </button>
    </div>
    
    <!-- 时间段验证结果 -->
    <div v-if="validationResult" class="validation-result">
      <p :class="{ 'text-success': validationResult.is_available, 'text-danger': !validationResult.is_available }">
        {{ validationResult.message }}
      </p>
      <p>时长：{{ validationResult.duration_hours }}小时</p>
      <div v-if="validationResult.warnings.length">
        <p v-for="warning in validationResult.warnings" :key="warning">{{ warning }}</p>
      </div>
    </div>
    
    <!-- 可用时段可视化 -->
    <div class="available-slots">
      <div v-for="slot in availableSlots" 
           :key="slot.time"
           :class="{ 'available': slot.is_available, 'booked': !slot.is_available }"
           @click="selectSlot(slot)">
        {{ slot.time }}
      </div>
    </div>
  </div>
</template>

<script>
import { ref, watch } from 'vue'
import axios from 'axios'

export default {
  props: ['roomId', 'bookingDate'],
  setup(props) {
    const booking = ref({
      start_time: '09:00',
      end_time: '12:00'
    })
    
    const validationResult = ref(null)
    const availableSlots = ref([])
    const quickSlots = ref([])
    
    // 监听时间变化，实时验证
    watch([() => booking.value.start_time, () => booking.value.end_time], async () => {
      if (booking.value.start_time && booking.value.end_time) {
        await checkTimeSlot()
      }
    })
    
    // 检查时间段可用性
    const checkTimeSlot = async () => {
      try {
        const response = await axios.post('/api/meeting/flexible/check-time-slot', {
          room_id: props.roomId,
          booking_date: props.bookingDate,
          start_time: booking.value.start_time,
          end_time: booking.value.end_time
        })
        validationResult.value = response.data
      } catch (error) {
        console.error('检查时间段失败:', error)
      }
    }
    
    // 加载可用时段
    const loadAvailableSlots = async () => {
      try {
        const response = await axios.get(
          `/api/meeting/flexible/available-slots/${props.roomId}/${props.bookingDate}`
        )
        availableSlots.value = response.data.available_slots
      } catch (error) {
        console.error('加载可用时段失败:', error)
      }
    }
    
    // 加载快捷时段
    const loadQuickSlots = async () => {
      try {
        const response = await axios.get('/api/meeting/flexible/quick-slots')
        quickSlots.value = response.data.quick_slots
      } catch (error) {
        console.error('加载快捷时段失败:', error)
      }
    }
    
    // 选择快捷时段
    const selectQuickSlot = (slot) => {
      booking.value.start_time = slot.start
      booking.value.end_time = slot.end
    }
    
    // 选择时段
    const selectSlot = (slot) => {
      if (slot.is_available) {
        booking.value.start_time = slot.time
        booking.value.end_time = slot.end_time
      }
    }
    
    // 初始化
    loadAvailableSlots()
    loadQuickSlots()
    
    return {
      booking,
      validationResult,
      availableSlots,
      quickSlots,
      selectQuickSlot,
      selectSlot
    }
  }
}
</script>

<style scoped>
.time-picker {
  max-width: 600px;
  margin: 20px auto;
}

.time-inputs {
  display: flex;
  gap: 20px;
  margin-bottom: 20px;
}

.quick-slots button {
  margin: 5px;
  padding: 10px 20px;
}

.available-slots {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(60px, 1fr));
  gap: 5px;
  margin-top: 20px;
}

.available-slots div {
  padding: 10px;
  text-align: center;
  cursor: pointer;
  border-radius: 4px;
}

.available {
  background-color: #d4edda;
  border: 1px solid #28a745;
}

.booked {
  background-color: #f8d7da;
  border: 1px solid #dc3545;
}

.text-success {
  color: #28a745;
}

.text-danger {
  color: #dc3545;
}
</style>
```

## 单元测试

### 运行测试

```bash
python -m pytest tests/test_flexible_booking.py -v
```

### 测试覆盖率报告

```bash
python -m pytest tests/test_flexible_booking.py --cov=Service_MeetingRoom.modules.flexible_booking --cov-report=html
```

### 测试结果

✅ **24个单元测试全部通过**

| 测试类别 | 测试数 | 状态 |
|---------|--------|------|
| 时间计算功能 | 4 | ✅ 通过 |
| 时长约束验证 | 5 | ✅ 通过 |
| 时间段检查模型 | 4 | ✅ 通过 |
| 时间段验证响应 | 3 | ✅ 通过 |
| 时间冲突检测逻辑 | 8 | ✅ 通过 |

## 安全特性

✅ **SQL注入防护**：所有查询使用参数化（text() + 参数绑定）

✅ **输入验证**：Pydantic模型验证时间格式和范围

✅ **范围约束**：强制时间范围07:00-22:00，时长30分钟-8小时

✅ **格式校验**：正则表达式验证HH:MM格式，分钟必须是30的整数倍

## 性能优化

- 模块级别的数据库连接池（避免重复创建）
- 参数化查询（提高查询效率）
- 索引建议：`meeting_bookings(room_id, booking_date, start_time)`

## 常见问题

### Q1: 为什么分钟必须是30的整数倍？

A: 为了简化时间段管理和冲突检测，采用30分钟作为最小时间单位。这是会议室预约系统的常见做法。

### Q2: 时间冲突检测的范围是什么？

A: 检测范围包括：
- 开始时间重叠
- 结束时间重叠
- 完全包含
- 部分重叠

### Q3: 已取消的预约会占用时间段吗？

A: 不会。只有状态为 `pending`（待确认）或 `confirmed`（已确认）的预约才会产生冲突。

### Q4: 如何处理跨天预约？

A: 当前版本不支持跨天预约。每个预约必须在同一天的07:00-22:00范围内。

## 下一步

- 集成到现有预约流程
- 添加"我的预约"功能
- 实现预约详情页和二维码
- 开发管理员权限验证

---

**版本**：1.0.0  
**更新时间**：2026年4月2日  
**遵循标准**：AIteem.md协作机制