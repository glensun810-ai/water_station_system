# AI产业集群空间服务管理平台 - 快速启动指南

## 🚀 一键启动（推荐）

### 快速启动脚本（仅核心服务）

```bash
# 启动用户端（自动打开浏览器）
python quick_start.py

# 直接启动管理后台（自动打开浏览器）
python quick_start.py --admin

# 停止所有服务
python quick_start.py stop
```

**特点**：
- ✅ 仅启动最核心的两个服务（后端API + 前端静态文件服务器）
- ✅ 自动打开浏览器显示页面
- ✅ 启动速度快，资源占用少
- ✅ 适合日常开发和演示

---

### 完整启动脚本（所有服务）

```bash
# 启动所有服务并打开浏览器
python start_all.py

# 启动但不自动打开浏览器
python start_all.py --no-browser

# 停止所有服务
python start_all.py stop
```

**特点**：
- ✅ 启动所有服务（水站、网关、前端）
- ✅ 功能完整，适合生产环境
- ⚠️ 需要配置网关服务

---

## 📍 访问地址

### 用户端

| 服务 | 地址 | 说明 |
|-----|------|------|
| 🏠 门户首页 | http://localhost:8080/portal/index.html | 统一入口，展示所有服务 |
| 💧 水站管理 | http://localhost:8080/Service_WaterManage/frontend/index.html | 饮用水领用、结算 |
| 🏛️ 会议室预定 | http://localhost:8080/Service_MeetingRoom/frontend/index.html | 会议室在线预约 |
| 🍽️ VIP餐厅 | http://localhost:8080/Service_Dining/frontend/index.html | 商务餐饮预定 |

### 管理后台

| 服务 | 地址 | 说明 |
|-----|------|------|
| 💧 水站管理 | http://localhost:8080/Service_WaterManage/frontend/admin.html | 商品、库存、结算管理 |
| 🏛️ 会议室管理 | http://localhost:8080/Service_MeetingRoom/frontend/admin.html | 会议室、预约管理 |
| 🍽️ 餐厅管理 | http://localhost:8080/Service_Dining/frontend/admin.html | 餐厅、包间管理 |

### API端点

| 服务 | 地址 | 说明 |
|-----|------|------|
| 🔗 水站API | http://localhost:8000/api | 核心业务API |
| 🔗 服务扩展API | http://localhost:8000/api/services | 通用服务API |

---

## 🔧 端口配置

| 服务 | 端口 | 说明 |
|-----|------|------|
| 后端API | 8000 | FastAPI服务 |
| 统一网关 | 8001 | API网关（可选） |
| 前端服务器 | 8080 | 静态文件服务 |

---

## 📝 使用流程

### 首次使用

1. **启动服务**：
   ```bash
   python quick_start.py
   ```

2. **自动打开浏览器**：
   - 默认打开门户首页（用户端）
   - 可以看到所有可用的服务

3. **选择服务**：
   - 点击对应服务卡片进入具体服务
   - 或直接访问管理后台URL

### 日常使用

```bash
# 启动用户端
python quick_start.py

# 或直接启动管理后台
python quick_start.py --admin

# 使用完毕后停止服务
python quick_start.py stop
```

---

## 🎯 快速测试

### 测试用户端

1. 运行 `python quick_start.py`
2. 浏览器自动打开门户首页
3. 点击"水站管理"测试领水功能
4. 点击"会议室预定"测试预约功能

### 测试管理后台

1. 运行 `python quick_start.py --admin`
2. 浏览器自动打开水站管理后台
3. 可以管理商品、查看领水记录、进行结算等

### 测试API

访问：http://localhost:8000/docs

可以在Swagger UI中测试所有API接口。

---

## 🛠️ 故障排查

### 端口被占用

```bash
# 手动清理端口
lsof -ti:8000 | xargs kill -9
lsof -ti:8080 | xargs kill -9

# 或使用停止命令
python quick_start.py stop
```

### 服务启动失败

1. 查看日志文件：
   ```bash
   tail -f logs/backend.log
   tail -f logs/frontend.log
   ```

2. 检查Python虚拟环境：
   ```bash
   ls -la .venv/bin/python
   ```

3. 确认依赖安装：
   ```bash
   pip install -r requirements.txt
   ```

### 浏览器未自动打开

手动访问：http://localhost:8080/portal/index.html

---

## 📦 项目结构

```
AIchanyejiqun/
├── quick_start.py          # 快速启动脚本（推荐）
├── start_all.py            # 完整启动脚本
├── stop_all.sh             # 停止脚本
├── portal/                 # 门户首页
│   └── index.html
├── Service_WaterManage/    # 水站服务
│   ├── backend/           # 后端API
│   └── frontend/          # 前端页面
├── Service_MeetingRoom/    # 会议室服务
│   ├── backend/
│   └── frontend/
├── Service_Dining/         # 餐厅服务
│   └── frontend/
├── logs/                   # 日志目录
└── .pids/                  # 进程ID文件
```

---

## 🎨 功能特点

### ✅ 已实现功能

- 💧 **水站管理**：领水登记、库存管理、结算统计
- 🏛️ **会议室预定**：在线预约、时段管理、冲突检测
- 🍽️ **VIP餐厅**：包间预定、商务接待
- ☕ **茶歇服务**：会议配套、套餐管理
- 🧹 **保洁服务**：环境维护、预约服务
- 🚗 **接送服务**：商务用车、行程管理

### 🔥 核心优势

- 🎯 **一键启动**：无需复杂配置，开箱即用
- 🌐 **自动打开浏览器**：启动即可看到界面
- 📱 **响应式设计**：支持PC和移动端
- 🚀 **高性能**：FastAPI + Vue3 现代化架构
- 🔒 **安全可靠**：用户认证、权限控制

---

## 💡 开发指南

### 本地开发

```bash
# 1. 启动服务
python quick_start.py

# 2. 访问API文档
open http://localhost:8000/docs

# 3. 修改代码后重启服务
python quick_start.py stop
python quick_start.py
```

### 生产部署

```bash
# 使用完整启动脚本
python start_all.py

# 配置Nginx反向代理
# 配置域名和SSL证书
```

---

## 📞 技术支持

- 📧 Email: support@ai-cluster.com
- 💬 微信: AI_Cluster_Service
- 📚 文档: [完整文档](./docs/)

---

## 📄 许可证

Copyright © 2026 AI产业集群空间服务管理平台. All rights reserved.

---

**最后更新**: 2026-04-01  
**版本**: v2.0.0