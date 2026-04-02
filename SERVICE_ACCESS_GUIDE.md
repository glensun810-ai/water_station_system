# 服务访问地址清单

## 水站管理系统

### 前端页面
- **登录页面：** http://localhost:8000/water-admin/login.html
- **管理后台：** http://localhost:8000/water-admin/admin.html
- **预约页面：** http://localhost:8000/frontend/index.html
- **套餐页面：** http://localhost:8000/frontend/packages.html
- **服务页面：** http://localhost:8000/frontend/services.html
- **预约记录：** http://localhost:8000/frontend/bookings.html

### API端点
- **API文档：** http://localhost:8000/docs
- **健康检查：** http://localhost:8000/health
- **API v2：** http://localhost:8000/v2/*

## 会议室管理系统

### 前端页面
- **管理后台：** http://localhost:8000/meeting-frontend/admin.html
- **预约日历：** http://localhost:8000/meeting-frontend/calendar.html
- **预约页面：** http://localhost:8000/meeting-frontend/index.html

### API端点
- **会议室API：** http://localhost:8000/api/meeting/*
  - GET /api/meeting/rooms - 获取会议室列表
  - POST /api/meeting/rooms - 创建会议室
  - GET /api/meeting/bookings - 获取预约列表
  - POST /api/meeting/bookings - 创建预约

## 默认管理员账号

- **用户名：** admin
- **密码：** 见 .env 文件（由系统自动生成）

## 启动服务

```bash
cd Service_WaterManage/backend
PORT=8000 python3 run.py
```

## 访问地址别名

为了方便访问，以下路径都指向同一位置：

**水站管理：**
- /water-admin/* → Service_WaterManage/frontend/*
- /frontend/* → Service_WaterManage/frontend/*

**会议室管理：**
- /meeting-frontend/* → Service_MeetingRoom/frontend/*

## 端口说明

- **端口 8000：** 主服务端口（推荐使用）
- **端口 8080：** 备用端口（通过环境变量 PORT 指定）

## 注意事项

1. 所有服务共享同一个后端服务（端口8000）
2. 前端页面通过不同路径区分不同服务
3. API v2 提供了现代化的RESTful接口
4. 旧的API接口仍然可用（/api/*）

## 测试命令

```bash
# 测试健康检查
curl http://localhost:8000/health

# 测试水站管理登录页
curl -I http://localhost:8000/water-admin/login.html

# 测试会议室列表
curl http://localhost:8000/api/meeting/rooms
```