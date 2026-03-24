# 水站管理系统 - 架构设计文档

## 📐 系统架构

### 前端架构
```
Service_WaterManage/frontend/
├── admin.html                    # 主管理后台（集成所有功能）
├── admin.html.backup             # 备份文件（可删除）
├── index.html                    # 用户端 H5 页面
├── login.html                    # 登录页面
├── change-password.html          # 修改密码页面
├── draft/                        # 废弃文件归档
│   └── users.html.deprecated     # 废弃的独立用户管理页面
└── 使用说明.md                   # 用户使用说明
```

### 后端架构
```
Service_WaterManage/backend/
├── main.py                       # FastAPI 后端服务
├── seed.py                       # 初始化演示数据
├── migrate.py                    # 数据库迁移
└── requirements.txt              # Python 依赖
```

## 🎯 设计原则

### 1. 单一文件原则 (Single File)
- **admin.html** 包含所有管理功能
- 避免多文件维护带来的同步问题
- 降低技术债务

### 2. 模块化设计 (Modular Design)
- 各功能模块作为独立 Tab
- 状态管理隔离
- 函数职责单一

### 3. 渐进增强 (Progressive Enhancement)
- 保留原有所有功能
- 新增功能作为独立模块
- 向后兼容

### 4. 权限控制 (Role-Based Access)
- super_admin：完整权限
- admin：部分管理权限
- staff：基础操作权限

## 📊 功能模块

### admin.html 功能清单

| 模块 | Tab ID | 功能描述 | 权限要求 |
|------|--------|----------|----------|
| 数据看板 | dashboard | 核心指标、待办事项、快捷操作 | 所有用户 |
| 结算申请 | applications | 处理用户结算申请 | 管理员以上 |
| 交易记录 | transactions | 管理所有交易记录 | 管理员以上 |
| 库存管理 | inventory | 查看库存预警 | 所有用户 |
| 产品管理 | products | 管理产品信息和规格 | 管理员以上 |
| 提醒结算 | remind | 提醒长期未结算用户 | 管理员以上 |
| 部门统计 | departments | 查看各部门用水统计 | 所有用户 |
| **用户管理** | **users** | **管理系统用户、角色和权限** | **super_admin** |

## 🔧 技术栈

### 前端
- **框架**: Vue 3 (CDN)
- **UI**: TailwindCSS (CDN)
- **构建**: 无构建，直接运行
- **状态管理**: Vue 3 Composition API (ref, computed)

### 后端
- **框架**: FastAPI
- **数据库**: SQLite
- **ORM**: SQLAlchemy
- **认证**: JWT
- **密码加密**: bcrypt

## 📁 文件结构详解

### admin.html 结构
```
admin.html
├── <head>
│   ├── Meta 标签
│   ├── Vue 3 CDN
│   ├── TailwindCSS CDN
│   └── 样式定义
│       ├── 基础样式
│       ├── 侧边栏导航样式
│       ├── 面包屑导航样式
│       ├── 返回顶部按钮样式
│       └── 用户管理模块样式
├── <body>
│   ├── #app
│   │   ├── 侧边栏导航 (桌面端)
│   │   ├── 移动端菜单遮罩
│   │   ├── 加载屏幕
│   │   ├── 认证错误屏幕
│   │   ├── API 错误屏幕
│   │   ├── 主内容区
│   │   │   ├── 移动端菜单按钮
│   │   │   ├── 返回顶部按钮
│   │   │   ├── 面包屑导航
│   │   │   ├── 顶部导航栏
│   │   │   ├── Tab 内容
│   │   │   │   ├── dashboard (数据看板)
│   │   │   │   ├── applications (结算申请)
│   │   │   │   ├── transactions (交易记录)
│   │   │   │   ├── inventory (库存管理)
│   │   │   │   ├── products (产品管理)
│   │   │   │   ├── remind (提醒结算)
│   │   │   │   ├── departments (部门统计)
│   │   │   │   └── users (用户管理) ⭐ 新增
│   │   │   └── 移动端底部导航
│   │   ├── 新建/编辑用户模态框 ⭐ 新增
│   │   ├── 删除用户确认模态框 ⭐ 新增
│   │   └── 快捷键帮助模态框
│   └── <script>
│       ├── Vue App 初始化
│       ├── 状态管理
│       │   ├── 认证状态
│       │   ├── 导航状态
│       │   ├── 用户管理状态 ⭐ 新增
│       │   └── 各 Tab 数据状态
│       ├── 计算属性
│       │   ├── 用户管理计算属性 ⭐ 新增
│       │   └── 各 Tab 数据统计
│       ├── 方法
│       │   ├── 导航方法
│       │   ├── 认证方法
│       │   ├── 用户管理方法 ⭐ 新增
│       │   └── 各 Tab 业务方法
│       └── 生命周期
│           └── onMounted
└── </body>
```

## 🔐 安全设计

### 认证流程
```
用户登录 → 获取 Token → 存储 localStorage → 请求携带 Token → 后端验证
```

### 权限控制
```javascript
// 前端权限检查
if (user.value.role !== 'super_admin') {
    // 隐藏用户管理入口
}

// 后端权限验证
@app.put("/api/users/{user_id}")
def update_user(
    current_user: User = Depends(get_current_user),
    ...
):
    if current_user.role != "super_admin":
        raise HTTPException(status_code=403, detail="权限不足")
```

### 数据安全
- 密码 bcrypt 加密
- JWT Token 认证
- SQL 注入防护（SQLAlchemy ORM）
- CORS 跨域控制

## 📈 性能优化

### 前端优化
1. **CDN 加载**: Vue 和 TailwindCSS 使用 CDN
2. **按需加载**: Tab 切换时加载数据
3. **计算属性缓存**: Vue computed 自动缓存
4. **事件委托**: 统一事件处理

### 后端优化
1. **数据库连接池**: SQLAlchemy Session
2. **索引优化**: 关键字段建立索引
3. **批量操作**: 支持批量结算
4. **缓存策略**: Token 验证缓存

## 🧪 测试策略

### 前端测试
- [ ] 各 Tab 切换正常
- [ ] 表单验证有效
- [ ] 权限控制正确
- [ ] 响应式布局正常

### 后端测试
```bash
cd backend
python test_system.py
```

### 集成测试
1. 登录 → 访问各功能模块
2. 创建用户 → 编辑 → 删除
3. 创建产品 → 编辑 → 删除
4. 提交结算申请 → 确认 → 完成

## 🚀 部署指南

### 开发环境
```bash
# 后端
cd backend
pip install -r requirements.txt
python seed.py  # 初始化数据
uvicorn main:app --reload

# 前端
# 直接浏览器打开 admin.html
# 或使用 Python HTTP 服务器
python -m http.server 8080
```

### 生产环境
```bash
# 后端
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000

# 前端
# 使用 Nginx 或 Apache 托管静态文件
# 配置反向代理到后端 API
```

## 📝 版本历史

### v2.0 (2026-03-24)
- ✅ 集成用户管理模块到 admin.html
- ✅ 新增用户 CRUD 功能
- ✅ 新增权限控制
- ✅ 新增快捷键支持
- ✅ 优化导航体验

### v1.0 (初始版本)
- ✅ 基础数据看板
- ✅ 结算申请管理
- ✅ 交易记录管理
- ✅ 库存管理
- ✅ 产品管理
- ✅ 提醒功能

## 🔮 未来规划

### 短期 (1-3 个月)
- [ ] 数据导出功能（Excel）
- [ ] 图表可视化（ECharts）
- [ ] 消息通知系统
- [ ] 操作日志记录

### 中期 (3-6 个月)
- [ ] 移动端 App（小程序）
- [ ] 扫码领水功能
- [ ] 自动对账系统
- [ ] 数据备份恢复

### 长期 (6-12 个月)
- [ ] 多租户支持
- [ ] 云端部署
- [ ] API 开放平台
- [ ] 第三方集成

---

**文档版本**: v2.0  
**最后更新**: 2026-03-24  
**维护团队**: 系统架构组
