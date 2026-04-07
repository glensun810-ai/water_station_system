# 会议室管理系统 - 服务重启问题解决方案

**问题**: 前端页面访问API返回404  
**原因**: 后端服务运行的是旧代码，meeting路由未加载  
**解决**: 强制重启后端服务  

---

## 问题现象

```
GET http://localhost:8000/api/meeting/rooms?is_active=true
返回: 404 Not Found
```

## 问题原因

1. 后端服务进程运行的是旧代码
2. 热重载未生效
3. meeting路由未注册到运行中的应用

---

## 解决方案

### 方法1：使用快速启动脚本（推荐）

```bash
cd /Users/sgl/PycharmProjects/AIchanyejiqun
./scripts/start_meeting_system.sh
```

### 方法2：手动重启

```bash
# 1. 查找旧进程
lsof -i :8000 | grep LISTEN

# 2. 杀死旧进程
kill -9 <PID>

# 3. 重新启动
cd Service_WaterManage/backend
python3 -m uvicorn main:app --host 0.0.0.0 --port 8000

# 4. 验证API
curl http://localhost:8000/api/meeting/health
```

---

## 验证清单

API端点验证：

```bash
# 健康检查
curl http://localhost:8000/api/meeting/health
# 应返回: {"status":"ok",...}

# 会议室列表
curl http://localhost:8000/api/meeting/rooms
# 应返回: 5个会议室的JSON数组

# 办公室列表
curl http://localhost:8000/api/meeting/offices
# 应返回: 9个办公室的JSON数组
```

---

## 预防措施

### 1. 每次修改后端代码后

```bash
# 必须重启服务
pkill -f "uvicorn.*main:app"
python3 -m uvicorn main:app --host 0.0.0.0 --port 8000
```

### 2. 使用启动脚本

```bash
# 自动检查并重启
./scripts/start_meeting_system.sh
```

### 3. 添加监控

考虑添加：
- 进程监控（supervisor/systemd）
- 自动重启机制
- 健康检查定时任务

---

## 当前服务状态

**进程ID**: 每次重启后变化  
**端口**: 8000  
**状态**: ✅ 正常  

**API端点**:
- ✅ /api/meeting/health
- ✅ /api/meeting/rooms
- ✅ /api/meeting/offices
- ✅ /api/meeting/bookings

**数据**:
- 会议室: 5个
- 办公室: 9个
- 预约: 2个

---

## 访问地址

**前端页面**:
- Portal: http://localhost:8080/portal/index.html
- 列表视图: http://localhost:8080/Service_MeetingRoom/frontend/index.html
- 日历视图: http://localhost:8080/Service_MeetingRoom/frontend/calendar.html
- 管理后台: http://localhost:8080/Service_MeetingRoom/frontend/admin.html

**后端API**:
- Health: http://localhost:8000/api/meeting/health
- Rooms: http://localhost:8000/api/meeting/rooms
- Offices: http://localhost:8000/api/meeting/offices
- Bookings: http://localhost:8000/api/meeting/bookings

---

**最后更新**: 2026-04-01 22:10  
**状态**: ✅ 问题已解决，系统正常