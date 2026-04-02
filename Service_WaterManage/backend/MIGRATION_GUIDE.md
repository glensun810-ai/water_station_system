"""
架构迁移指南
从旧架构迁移到新架构的开发指南
"""

# 架构迁移指南

## 概述

本文档提供从旧架构（main.py单体应用）迁移到新架构（分层架构）的详细指南。

## 架构对比

### 旧架构
```
main.py (4695行)
├── 数据库连接
├── 模型定义（17个）
├── API端点（91个）
├── 业务逻辑
└── 数据访问
```

**问题：**
- 所有代码集中在一个文件
- 业务逻辑与数据访问耦合
- 难以测试和维护
- 代码重复率高

### 新架构
```
models/           数据模型层
repositories/     数据访问层
services/         业务逻辑层
api_new/          API层
config/          配置管理
utils/           工具函数
```

**优势：**
- 清晰的分层架构
- 职责单一，易于维护
- 高度可测试
- 代码复用率高

## 迁移策略

### 渐进式迁移原则

1. **不影响现有功能** - 旧代码保持不变
2. **新功能使用新架构** - 新API使用v2前缀
3. **逐步迁移旧功能** - 可选，按需迁移
4. **保持数据库兼容** - 不修改表结构

### 迁移路径

```
阶段1: 新功能开发
  ↓ 使用新架构
阶段2: 创建新API端点
  ↓ /v2/ 前缀
阶段3: 前端逐步迁移
  ↓ 调用新API
阶段4: 旧API标记废弃
  ↓ 保留兼容性
阶段5: 完全迁移
  ↓ 移除旧代码
```

## 具体迁移步骤

### 步骤1: 创建数据模型

**旧代码（main.py）：**
```python
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)
    # ... 其他字段
```

**新代码（models/user.py）：**
```python
from sqlalchemy import Column, Integer, String
from models.base import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)
    # ... 其他字段
```

**变化：**
- 独立文件
- 从`models.base`导入Base
- 添加类型注解和文档

### 步骤2: 创建仓库层

**旧代码（main.py API端点）：**
```python
@app.get("/api/users")
def get_users(db: Session = Depends(get_db)):
    users = db.query(User).all()
    return users
```

**新代码（repositories/user_repository.py）：**
```python
from repositories.base import BaseRepository
from models.user import User

class UserRepository(BaseRepository[User]):
    def __init__(self, db: Session):
        super().__init__(User, db)
    
    def get_by_name(self, name: str) -> Optional[User]:
        return self.db.query(User).filter(User.name == name).first()
```

**优势：**
- 数据访问逻辑集中管理
- 可复用的CRUD操作
- 易于测试

### 步骤3: 创建服务层

**旧代码（main.py 业务逻辑）：**
```python
@app.post("/api/users")
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    # 检查用户名是否存在
    existing = db.query(User).filter(User.name == user.name).first()
    if existing:
        raise HTTPException(400, "用户名已存在")
    
    # 创建用户
    db_user = User(**user.dict())
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user
```

**新代码（services/user_service.py）：**
```python
class UserService:
    def __init__(self, db: Session):
        self.user_repo = UserRepository(db)
    
    def create_user(self, name: str, department: str, role: str = "staff"):
        if self.user_repo.name_exists(name):
            raise ValueError(f"用户名 '{name}' 已存在")
        
        return self.user_repo.create({
            "name": name,
            "department": department,
            "role": role
        })
```

**优势：**
- 业务逻辑集中管理
- 验证逻辑清晰
- 易于测试

### 步骤4: 创建API端点

**旧代码（main.py）：**
```python
@app.post("/api/users", response_model=UserResponse)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    # ... 业务逻辑
```

**新代码（api_new/users.py）：**
```python
from fastapi import APIRouter, Depends
from services import UserService

router = APIRouter(prefix="/v2/users")

@router.post("", response_model=UserResponse)
async def create_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin)
):
    service = UserService(db)
    
    try:
        user = service.create_user(
            name=user_data.name,
            department=user_data.department,
            role=user_data.role
        )
        return user
    except ValueError as e:
        raise HTTPException(400, str(e))
```

**优势：**
- API层职责单一
- 依赖注入清晰
- 错误处理统一

## 迁移清单

### 模型迁移清单
- [ ] User ✅
- [ ] Product ✅
- [ ] ProductCategory ✅
- [ ] Transaction ✅
- [ ] InventoryRecord ✅
- [ ] InventoryAlertConfig ✅
- [ ] OfficeAccount ✅
- [ ] AccountTransaction ✅
- [ ] PrepaidPackage ✅
- [ ] PrepaidOrder ✅
- [ ] PrepaidPickup ✅
- [ ] DeleteLog ✅
- [ ] Notification ✅
- [ ] Office ❌
- [ ] Promotion ❌
- [ ] ReservationPickup ❌

### 服务迁移清单
- [ ] UserService ✅
- [ ] ProductService ✅
- [ ] TransactionService ✅
- [ ] InventoryService ✅
- [ ] AccountService ✅
- [ ] PrepaidService ❌
- [ ] OfficeService ❌

### API端点迁移清单
- [ ] /v2/auth/* ✅ (2个端点)
- [ ] /v2/users/* ✅ (9个端点)
- [ ] /v2/products/* ✅ (14个端点)
- [ ] /v2/transactions/* ✅ (16个端点)
- [ ] /v2/inventory/* ❌
- [ ] /v2/accounts/* ❌
- [ ] /v2/prepaid/* ❌

## 测试策略

### 单元测试
```python
# tests/test_services/test_user_service.py
def test_create_user(db_session):
    service = UserService(db_session)
    
    user = service.create_user(
        name="test_user",
        department="技术部"
    )
    
    assert user.id is not None
    assert user.name == "test_user"
```

### 集成测试
```python
# tests/test_api/test_users_api.py
def test_create_user_api(client):
    response = client.post(
        "/v2/users",
        json={
            "name": "new_user",
            "department": "技术部",
            "role": "staff"
        },
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    assert response.status_code == 201
```

## 性能优化建议

### 1. 数据库查询优化
- 使用`joinedload`避免N+1查询
- 添加适当的索引
- 使用`select_related`预加载关联数据

### 2. 缓存策略
- 使用Redis缓存频繁访问的数据
- 实现查询结果缓存
- 使用缓存装饰器

### 3. 异步处理
- 使用后台任务处理耗时操作
- 实现异步API端点
- 使用消息队列

## 常见问题

### Q1: 旧API还能用吗？
**A:** 可以。旧的`/api/`接口继续可用，不受影响。

### Q2: 数据库会改变吗？
**A:** 不会。新旧架构使用相同的数据库，表结构保持不变。

### Q3: 如何处理并发访问？
**A:** 新架构通过Service层管理事务，确保数据一致性。

### Q4: 前端需要修改吗？
**A:** 不需要立即修改。可以逐步将API调用从`/api/`改为`/v2/`。

### Q5: 测试覆盖率如何保证？
**A:** 为新代码编写完整的单元测试和集成测试，目标覆盖率>80%。

## 回滚计划

如果出现问题，可以快速回滚：

1. **停止服务**
```bash
pkill -f "python.*run.py"
```

2. **注释新路由**
```python
# run.py中注释掉以下行
# app.include_router(users_router)
# app.include_router(products_router)
# ...
```

3. **重启服务**
```bash
python main.py  # 使用旧的main.py
```

4. **验证功能**
- 检查API文档：http://localhost:8080/docs
- 测试关键功能
- 确认数据完整性

## 总结

新架构提供了更好的可维护性、可测试性和可扩展性。通过渐进式迁移，我们可以在不影响现有功能的情况下，逐步提升代码质量。

**建议：**
- 新功能优先使用新架构
- 逐步迁移关键业务逻辑
- 保持完整的测试覆盖
- 定期review和优化

**下一步：**
- 完成剩余模型的迁移
- 补充更多服务类
- 添加性能监控
- 完善文档体系