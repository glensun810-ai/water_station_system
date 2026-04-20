# AI产业集群空间服务系统

## 项目简介

统一的办公空间服务平台，集成水站服务、会议室预约、空间预订等功能。

## 核心目录结构

```
├── apps/           # 应用核心代码
│   ├── api/        # API路由
│   ├── main.py     # 主入口
│   ├── water/      # 水站服务
│   └── meeting/    # 会议室服务
├── portal/         # Portal前端（首页）
├── space-frontend/ # Space前端（空间预订）
├── config/         # 配置文件
├── models/         # 数据模型
├── schemas/        # 数据结构定义
├── services/       # 业务服务层
├── shared/         # 共享代码
├── utils/          # 工具类
├── data/           # 数据库文件
├── migrations/     # 数据迁移
├── deploy/         # 部署配置
├── requirements.txt # Python依赖
├── run.py          # 启动脚本
└── init_db.py      # 数据库初始化
```

## 快速启动

### 本地开发
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python run.py
```

### 生产部署
参考 `deploy/` 目录下的部署脚本。

## 访问地址

- Portal首页: `/portal/index.html`
- Space首页: `/space-frontend/index.html`
- API文档: `/docs`

## 登录信息

- 用户名: `admin`
- 密码: `Admin@2026`

## 技术栈

- 后端: FastAPI + SQLAlchemy + SQLite
- 前端: Vue.js + HTML/CSS/JS
- 服务器: Nginx + Uvicorn

## 部署信息

- 服务器IP: 120.76.156.83
- 域名: service.jhw-ai.com
- API端口: 8008