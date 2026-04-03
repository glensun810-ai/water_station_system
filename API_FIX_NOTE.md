# API端口配置修复说明

## 问题描述
前端页面配置的API端口错误，导致404错误。

## 已修复文件

### 1. index.html ✅
- **修改位置**：第328行
- **修改前**：`http://localhost:8000/api/meeting`
- **修改后**：`http://localhost:8080/api/meeting`

### 2. admin.html ✅
- **修改位置**：第334行
- **修改前**：`http://localhost:8000/api/meeting`
- **修改后**：`http://localhost:8080/api/meeting`

### 3. my_bookings.html ✅
- **配置**：使用相对路径 `/api/meeting`（正确）
- **无需修改**

## 正确的访问方式

### 启动服务（端口8080）
```bash
cd Service_WaterManage/backend
uvicorn main:app --host 0.0.0.0 --port 8080 --reload
```

### 访问前端页面
```
预约页面：http://localhost:8080/frontend/index.html
管理后台：http://localhost:8080/frontend/admin.html
我的预约：http://localhost:8080/frontend/my_bookings.html
```

## 测试API

### 测试会议室API
```bash
curl http://localhost:8080/api/meeting/rooms
```

### 测试预约API
```bash
curl http://localhost:8080/api/meeting/bookings
```

### 测试健康检查
```bash
curl http://localhost:8080/health
```

## 重要提示

⚠️ **所有前端API调用都使用端口8080**

✅ 正确配置：
- 开发环境：`http://localhost:8080/api/meeting`
- 生产环境：`https://jhw-ai.com/api/meeting`

❌ 错误配置：
- ~~`http://localhost:8000/api/meeting`~~

## 下次启动

直接使用启动脚本：
```bash
./start_server.sh
```

然后在浏览器打开：http://localhost:8080/frontend/index.html