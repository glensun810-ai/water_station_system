# P2级任务详细执行计划

**制定时间：** 2026年4月2日  
**架构师：** 系统架构师  
**任务级别：** P2（中长期优化）  
**执行原则：** 渐进式重构，不影响现有功能

---

## 一、P2任务清单确认

### 1.1 任务列表

| 任务编号 | 任务名称 | 预计工时 | 优先级 | 风险 |
|---------|---------|---------|--------|------|
| P2-1 | 数据模型迁移（渐进式） | 24h | 中 | 低 |
| P2-2 | 服务层实现 | 40h | 中 | 低 |
| P2-3 | API模块化拆分 | 40h | 中 | 低 |

### 1.2 执行原则

**核心原则：**
1. ✅ 不修改main.py现有代码
2. ✅ 新功能使用新架构
3. ✅ 保持现有功能100%正常
4. ✅ 可随时暂停和回滚
5. ✅ 完整测试验证

---

## 二、P2-1: 数据模型迁移（渐进式）

### 2.1 任务目标

将main.py中的数据模型逐步迁移到models/目录，采用渐进式策略。

### 2.2 迁移策略

**策略：双轨并行**
- 保持main.py中的模型不变
- 在models/中创建新模型定义
- 新功能使用models/中的模型
- 逐步迁移旧功能（可选）

### 2.3 执行步骤

**Step 1: 创建模型目录结构**
```bash
mkdir -p models
touch models/__init__.py
```

**Step 2: 提取核心模型**
- Product模型
- Transaction模型
- Office相关模型
- 其他模型

**Step 3: 创建模型文件**
- models/product.py
- models/transaction.py
- models/office.py

**Step 4: 验证模型兼容性**
- 确保与现有数据库兼容
- 测试模型关系

### 2.4 预期成果

```
models/
├── __init__.py      # 导出所有模型
├── base.py          # Base类（已存在）
├── user.py          # User模型（已存在）
├── product.py       # Product模型（新建）
├── transaction.py   # Transaction模型（新建）
└── office.py        # Office相关模型（新建）
```

---

## 三、P2-2: 服务层实现

### 3.1 任务目标

为业务逻辑创建独立的服务层，实现业务逻辑与数据访问分离。

### 3.2 设计原则

**分层架构：**
```
API层 (main.py/api/*.py)
    ↓ 调用
服务层 (services/*.py)
    ↓ 调用
仓库层 (repositories/*.py)
    ↓ 调用
数据模型 (models/*.py)
```

### 3.3 执行步骤

**Step 1: 创建服务目录**
```bash
mkdir -p services
touch services/__init__.py
```

**Step 2: 创建核心服务**
- UserService - 用户管理
- ProductService - 产品管理
- TransactionService - 交易管理
- OfficeService - 办公室管理

**Step 3: 实现服务类**
```python
class ProductService:
    def __init__(self, db: Session):
        self.db = db
        self.product_repo = ProductRepository(db)
    
    def get_products(self, skip: int = 0, limit: int = 100):
        return self.product_repo.get_multi(skip, limit)
```

### 3.4 预期成果

```
services/
├── __init__.py
├── user_service.py
├── product_service.py
├── transaction_service.py
└── office_service.py
```

---

## 四、P2-3: API模块化拆分

### 4.1 任务目标

创建模块化的API路由，不修改main.py现有代码。

### 4.2 拆分策略

**策略：增量添加**
- 创建api/目录
- 创建新的API模块
- 新功能使用新API模块
- 保持main.py现有路由不变

### 4.3 执行步骤

**Step 1: 创建API目录**
```bash
mkdir -p api
touch api/__init__.py
```

**Step 2: 创建API模块**
- api/users.py - 用户API
- api/products.py - 产品API
- api/transactions.py - 交易API

**Step 3: 注册路由**
在run.py中注册新路由：
```python
from api.users import router as users_router
app.include_router(users_router, prefix="/api/v2", tags=["users"])
```

### 4.4 预期成果

```
api/
├── __init__.py
├── auth.py          # 已存在
├── users.py         # 新建
├── products.py      # 新建
└── transactions.py  # 新建
```

---

## 五、执行计划

### 5.1 Phase 1: 数据模型迁移（2小时）

**任务：**
1. 创建模型文件
2. 提取模型定义
3. 验证兼容性

**验证：**
- 模型可正常导入
- 与现有数据库兼容
- 不影响现有功能

### 5.2 Phase 2: 服务层实现（3小时）

**任务：**
1. 创建服务目录
2. 实现核心服务类
3. 集成仓库层

**验证：**
- 服务类可正常使用
- 业务逻辑正确
- 不影响现有功能

### 5.3 Phase 3: API模块化（2小时）

**任务：**
1. 创建API模块
2. 实现API路由
3. 注册到应用

**验证：**
- API可正常访问
- 功能正确
- 不影响现有API

---

## 六、验证清单

### 6.1 功能验证

- [ ] 服务正常启动
- [ ] 健康检查正常
- [ ] 前端页面可访问
- [ ] API文档可访问
- [ ] 现有API正常工作

### 6.2 新功能验证

- [ ] 新模型可正常使用
- [ ] 新服务类可正常工作
- [ ] 新API可正常访问

### 6.3 兼容性验证

- [ ] 数据库兼容
- [ ] API兼容
- [ ] 前端兼容

---

## 七、风险控制

### 7.1 风险识别

| 风险 | 等级 | 缓解措施 |
|------|------|---------|
| 破坏现有功能 | 低 | 不修改现有代码 |
| 模型不兼容 | 低 | 保持数据库结构不变 |
| 服务层错误 | 低 | 完整测试验证 |
| API冲突 | 低 | 使用不同路径前缀 |

### 7.2 回滚策略

如果出现问题：
1. 停止服务
2. 删除新建文件
3. 重启服务
4. 验证功能正常

---

## 八、成果预期

### 8.1 代码改进

```
新建文件：10+ 个
新增代码：1,500+ 行
架构改进：90%
```

### 8.2 架构提升

```
分层清晰：API → Service → Repository → Model
可维护性：↑ 80%
可测试性：↑ 90%
扩展性：↑ 85%
```

---

## 九、执行时间表

| 时间 | 任务 | 预期成果 |
|------|------|---------|
| 0-2h | P2-1 模型迁移 | 新模型文件创建 |
| 2-5h | P2-2 服务层 | 服务类实现完成 |
| 5-7h | P2-3 API模块化 | 新API可用 |
| 7-8h | 验证测试 | 功能验证通过 |

---

## 十、下一步行动

**立即执行：**
1. 开始P2-1任务
2. 创建模型文件
3. 验证功能

**注意事项：**
- 保持渐进式重构
- 不修改现有代码
- 完整测试验证

---

**计划制定完成时间：** 2026年4月2日  
**下一步：** 开始执行P2-1任务