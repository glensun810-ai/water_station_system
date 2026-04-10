# 项目架构清理计划

## 一、清理目标

根据新架构设计原则，清理废弃文件，保留核心业务模块。

## 二、需要移动到Backup的文件/目录

### 1. 非核心业务模块

**ai_team/ 目录**
- 原因：AI开发辅助工具，不属于核心业务系统
- 内容：AI团队协作工具（PM Agent、Architect Agent、Dev Agent等）
- 目标位置：Backup/deprecated_non_core/

**apps/unified/ 目录**
- 原因：空目录，新架构设计中未使用的模块
- 内容：backend/ 和 frontend/ 都是空目录
- 目标位置：Backup/deprecated_modules/

### 2. 旧版本文件

**apps/system/backend/api_system.py**
- 原因：旧版本系统API（116行），功能不完整
- 对比：apps/api/v1/system.py（357行）为新版本，功能完整
- 目标位置：Backup/deprecated_api/

**portal/dist/ 目录**
- 原因：Vite构建的旧版SPA前端，已不使用
- 对比：portal/index.html为新版完整前端（59KB）
- 目标位置：Backup/deprecated_frontend/

### 3. 开发辅助文件（可选）

**根目录测试文件**
- add_test_data.py - 测试数据生成脚本
- test_fixes.py - 测试脚本
- verify_portal_fix.py - Portal修复验证脚本
- check_portal_links.py - Portal链接检查脚本
- test_portal_pages.py - Portal页面测试脚本
- 目标位置：scripts/ 或 Backup/dev_tools/

## 三、保留的核心文件结构

### 一级目录（核心）

**apps/ - 统一应用服务**
- main.py - 统一API网关入口（端口8000）
- api/v1/ - 统一API路由层
  - water.py - 水站服务API
  - meeting.py - 会议室服务API
  - system.py - 系统服务API
- water/ - 水站服务模块
- meeting/ - 会议室服务模块
- system/ - 系统服务模块（backend/为空，待清理）

**config/ - 统一配置中心**
- database.py - 数据库配置
- settings.py - 应用配置

**models/ - 统一数据模型层**
- base.py - 基础模型类
- user.py - 用户模型
- office.py - 办公室模型
- product.py - 产品模型
- settlement.py - 结算模型
- meeting.py - 会议室模型
- booking.py - 预约模型

**schemas/ - API Schema层**
- system.py - 系统服务Schema
- water.py - 水站服务Schema

**depends/ - 依赖注入层**
- auth.py - 认证依赖

**utils/ - 工具函数层**
- jwt.py - JWT工具

**portal/ - 统一前端入口**
- index.html - 门户首页
- water/ - 水站前端页面
- admin/ - 管理后台页面
- components/ - 共享组件库
- assets/ - 静态资源

**shared/ - 共享资源**
- models/ - 共享模型
- schemas/ - 共享Schema
- utils/ - 共享工具（api-client.js、api-endpoints.js）

**docs/ - 文档中心**
- 架构设计文档
- API规范文档
- 实施报告文档

**infra/ - 基础设施**
- database/ - 数据库迁移工具
- api-gateway/ - API网关配置
- monitoring/ - 监控配置

**data/ - 数据存储**
- app.db - SQLite数据库（开发环境）

**logs/ - 日志目录**
- API服务日志

**tests/ - 测试目录**
- 单元测试、集成测试

**scripts/ - 脚本目录**
- 部署脚本、维护脚本

**deploy/ - 部署配置**
- Docker配置、环境配置

## 四、清理步骤

### 步骤1：创建Backup子目录
```bash
mkdir -p Backup/deprecated_non_core
mkdir -p Backup/deprecated_modules
mkdir -p Backup/deprecated_api
mkdir -p Backup/deprecated_frontend
mkdir -p Backup/dev_tools
```

### 步骤2：移动非核心模块
```bash
mv ai_team Backup/deprecated_non_core/
mv apps/unified Backup/deprecated_modules/
```

### 步骤3：移动旧版本文件
```bash
mv apps/system/backend Backup/deprecated_api/system_backend_old
mv portal/dist Backup/deprecated_frontend/
```

### 步骤4：移动开发辅助文件（可选）
```bash
mv add_test_data.py scripts/
mv test_fixes.py scripts/
mv verify_portal_fix.py scripts/
mv check_portal_links.py scripts/
mv test_portal_pages.py scripts/
```

### 步骤5：清理空目录
```bash
rm -rf apps/system/backend
```

## 五、清理后验证

### 验证点
1. API服务正常启动
2. 前端页面正常访问
3. 数据库连接正常
4. 核心功能完整可用

### 验证命令
```bash
# 启动服务
python -m uvicorn apps.main:app --host 0.0.0.0 --port 8008

# 检查健康状态
curl http://127.0.0.1:8008/health

# 检查前端页面
curl http://127.0.0.1:8008/portal/index.html

# 运行系统健康检查
python verify_system_health.py
```

## 六、风险评估

### 低风险项
- ai_team/ - 独立模块，不影响核心业务
- apps/unified/ - 空目录，无实际功能
- portal/dist/ - 已不使用的旧版前端

### 中风险项
- apps/system/backend/ - 需确认无其他模块依赖
- 根目录测试文件 - 开发辅助工具，不影响生产

### 回滚方案
所有移动到Backup的文件都可以通过反向移动回原位置来恢复。

## 七、预计效果

清理后项目将更加清晰：
- 核心业务模块集中在 apps/ 目录
- 配置统一在 config/ 目录
- 前端统一在 portal/ 目录
- 文档统一在 docs/ 目录
- 基础设施统一在 infra/ 目录

符合新架构的"统一化、模块化、标准化"设计理念。