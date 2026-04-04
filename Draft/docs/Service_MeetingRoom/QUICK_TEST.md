# 会议室服务 - 快速测试指南

## ✅ 服务已启动

会议室服务后端已启动并运行在：`http://localhost:8002`

---

## 🌐 访问方式

### 方式一：直接访问后端服务（推荐）

**用户端页面：**
```
http://localhost:8002/meeting
```
或
```
http://localhost:8002/frontend/index.html
```

**管理端页面：**
```
http://localhost:8002/meeting-admin
```
或
```
http://localhost:8002/admin/admin.html
```

**API 文档：**
```
http://localhost:8002/docs
```

---

## 📋 测试步骤

### 1. 启动后端服务（如果未启动）

```bash
cd /Users/sgl/PycharmProjects/AIchanyejiqun/Service_MeetingRoom/backend
uvicorn main:app --reload --port 8002
```

### 2. 初始化测试数据

访问 Swagger API 文档：`http://localhost:8002/docs`

或者使用以下命令创建测试会议室：

```bash
# 创建小型会议室
curl -X POST "http://localhost:8002/api/meeting/rooms" \
  -H "Content-Type: application/json" \
  -d '{"name":"小型会议室 A","type":"small","capacity":6,"price_per_hour":100,"free_hours_per_month":8}'

# 创建中型会议室
curl -X POST "http://localhost:8002/api/meeting/rooms" \
  -H "Content-Type: application/json" \
  -d '{"name":"中型会议室 B","type":"medium","capacity":12,"price_per_hour":150,"free_hours_per_month":8}'

# 创建大型会议室
curl -X POST "http://localhost:8002/api/meeting/rooms" \
  -H "Content-Type: application/json" \
  -d '{"name":"大型会议室 C","type":"large","capacity":30,"price_per_hour":200,"free_hours_per_month":8}'

# 创建 VIP 会客厅
curl -X POST "http://localhost:8002/api/meeting/rooms" \
  -H "Content-Type: application/json" \
  -d '{"name":"VIP 会客厅","type":"vip","capacity":8,"price_per_hour":200,"free_hours_per_month":4}'
```

### 3. 测试用户端预约流程

1. 打开浏览器访问：`http://localhost:8002/meeting`
2. 选择日期（今天或明天）
3. 选择一个会议室
4. 选择一个可用时间段
5. 填写会议信息（主题、人数等）
6. 点击"确认提交"
7. 查看成功提示

### 4. 测试管理端

1. 打开浏览器访问：`http://localhost:8002/meeting-admin`
2. 查看首页数据统计
3. 切换到"预约记录"标签
4. 查看刚才创建的预约
5. 切换到"会议室管理"标签
6. 可以编辑或删除会议室

---

## 🔧 常见问题

### 问题 1: 页面无法加载

**原因**: 后端服务未启动

**解决**: 
```bash
cd /Users/sgl/PycharmProjects/AIchanyejiqun/Service_MeetingRoom/backend
uvicorn main:app --reload --port 8002
```

### 问题 2: 预约失败

**原因**: 数据库中没有会议室数据

**解决**: 执行步骤 2 的初始化测试数据命令

### 问题 3: 时间冲突错误

**原因**: 同一时段已有预约

**解决**: 选择其他时间段或其他会议室

---

## 📊 API 接口测试

### 获取会议室列表
```bash
curl http://localhost:8002/api/meeting/rooms
```

### 查询可用时间段
```bash
curl "http://localhost:8002/api/meeting/rooms/1/availability?date=2026-04-01"
```

### 创建预约
```bash
curl -X POST "http://localhost:8002/api/meeting/reservations" \
  -H "Content-Type: application/json" \
  -d '{
    "room_id": 1,
    "start_time": "2026-04-01T14:00:00",
    "end_time": "2026-04-01T16:00:00",
    "title": "产品评审会",
    "attendee_count": 8
  }'
```

### 查询我的预约
```bash
curl http://localhost:8002/api/meeting/reservations
```

### 取消预约
```bash
curl -X DELETE "http://localhost:8002/api/meeting/reservations/1"
```

---

## 🎯 功能清单

### 用户端 ✅
- [x] 选择日期
- [x] 选择会议室
- [x] 查询可用时间段
- [x] 填写会议信息
- [x] 自动计算费用
- [x] 创建预约
- [x] 查看我的预约
- [x] 取消预约

### 管理端 ✅
- [x] 数据统计仪表盘
- [x] 预约记录列表
- [x] 预约审核（通过/拒绝）
- [x] 会议室管理（CRUD）
- [x] 启用/停用会议室

---

## 📝 测试报告模板

### 测试用例 1: 创建预约
- **步骤**: 选择日期 → 选择会议室 → 选择时间 → 提交
- **预期**: 预约成功，显示成功提示
- **实际**: ______
- **状态**: ⬜ 通过 ⬜ 失败

### 测试用例 2: 查看预约记录
- **步骤**: 切换到"我的预约"标签
- **预期**: 显示刚才创建的预约
- **实际**: ______
- **状态**: ⬜ 通过 ⬜ 失败

### 测试用例 3: 取消预约
- **步骤**: 在预约记录中点击"取消"按钮
- **预期**: 预约状态变为"已取消"
- **实际**: ______
- **状态**: ⬜ 通过 ⬜ 失败

### 测试用例 4: 管理端查看数据
- **步骤**: 访问管理端首页
- **预期**: 显示预约统计数据
- **实际**: ______
- **状态**: ⬜ 通过 ⬜ 失败

---

## 🚀 下一步

1. ✅ 用户端预约页面 - 已完成
2. ✅ 管理端后台页面 - 已完成  
3. ✅ 后端 API 服务 - 已完成
4. ⏳ 集成到统一门户 - 待办
5. ⏳ 添加通知功能 - 待办

---

**测试时间**: 2026-03-31  
**测试状态**: ✅ 准备就绪
