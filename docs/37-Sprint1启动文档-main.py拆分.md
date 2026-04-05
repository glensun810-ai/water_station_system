# Sprint 1启动文档：main.py巨石文件拆分

**启动时间**: 2026-04-05  
**执行人**: 后端开发 + 架构师监督  
**预计完成**: 2026-04-12（7天）  
**目标**: 将4570行main.py拆分为清晰模块，保持功能100%不变

---

## 一、前置准备

### 1.1 完整备份

```bash
# 1. 备份整个项目
cd /Users/sgl/PycharmProjects/AIchanyejiqun
tar -czf backup_$(date +%Y%m%d_%H%M%S).tar.gz \
  Service_WaterManage/backend/main.py \
  Service_WaterManage/frontend/ \
  Service_MeetingRoom/frontend/ \
  portal/

# 2. 创建Git标签
git tag -a backup-before-refactor -m "重构前备份"
git push origin backup-before-refactor

# 3. 验证备份完整性
ls -lh backup_*.tar.gz
```

### 1.2 功能验证

```bash
# 启动服务
cd Service_WaterManage/backend
python main.py &

# 验证关键API
curl http://localhost:8000/api/products
curl http://localhost:8000/api/meeting/rooms
curl http://localhost:8000/api/auth/me -H "Authorization: Bearer {token}"

# 访问前端页面
curl http://localhost:8000/water-admin/index.html
curl http://localhost:8000/meeting-frontend/index.html
curl http://localhost:8000/portal/index.html
```

### 1.3 依赖清单

```bash
# 记录当前依赖
pip freeze > requirements.txt
```

---

## 二、拆分策略

### 2.1 拆分原则

**"三不"原则**：
1. **不修改业务逻辑** - 只移动代码，不改逻辑
2. **不改变API路径** - 所有URL保持不变
3. **不破坏数据结构** - 模型定义保持不变

**"三要"原则**：
1. **要创建完整备份** - 每一步都可回滚
2. **要充分测试验证** - 每一步都验证功能
3. **要逐步提交代码** - 每一步都提交Git

### 2.2 目录结构规划

```
Service_WaterManage/backend/
├── main.py                    (目标: < 500行)
│   └── 仅保留: 应用初始化、路由挂载、启动配置
│
├── config/                    (新建)
│   ├── __init__.py
│   ├── database.py            (数据库配置)
│   └── settings.py            (应用配置)
│
├── models/                    (新建)
│   ├── __init__.py
│   ├── base.py                (Base模型)
│   ├── user.py                (User, UserRole等)
│   ├── product.py             (Product, ProductCategory等)
│   ├── office.py              (OfficeAccount, OfficePickup等)
│   ├── transaction.py         (AccountTransaction等)
│   └── meeting.py             (MeetingRoom, MeetingBooking等)
│
├── api/                       (新建)
│   ├── __init__.py
│   ├── auth.py                (认证API: /api/auth/*)
│   ├── water.py               (水站API: /api/products, /api/user/office-pickup等)
│   ├── meeting.py             (会议室API: /api/meeting/*)
│   └── admin.py               (管理API: /api/admin/*)
│
├── utils/                     (新建)
│   ├── __init__.py
│   ├── auth.py                (认证工具: verify_password, create_token等)
│   ├── database.py            (数据库工具: get_db等)
│   └── helpers.py             (辅助函数)
│
├── schemas/                   (新建，Pydantic模型)
│   ├── __init__.py
│   ├── user.py                (UserBase, UserCreate, UserResponse等)
│   ├── product.py             (ProductBase, ProductCreate等)
│   └── ...
│
└── main.py.backup             (原文件备份)
```

---

## 三、详细执行步骤

### Day 1: 准备工作（1天）

#### 上午：代码分析

**任务**：分析main.py结构，标记拆分边界

```bash
# 1. 统计各类代码行数
echo "=== 模型定义 ===" 
grep -n "^class.*Base" main.py | wc -l

echo "=== API路由 ==="
grep -n "@app\." main.py | wc -l

echo "=== 工具函数 ==="
grep -n "^def " main.py | wc -l

# 2. 生成代码结构图
cat > code_structure.txt << EOF
# main.py代码结构分析

## 1. 导入部分 (约1-100行)
- 标准库导入
- 第三方库导入
- 本地导入

## 2. 配置部分 (约40-100行)
- SECRET_KEY等配置
- 数据库配置
- 安全配置

## 3. 模型定义 (约100-430行)
- User (131-144)
- Product (156-178)
- OfficeAccount (227-258)
- OfficePickup (302-341)
- ...

## 4. Pydantic模型 (约430-700行)
- UserBase, UserCreate等
- ProductBase, ProductCreate等
- ...

## 5. 工具函数 (约60-130行)
- hash_password
- verify_password
- create_access_token
- verify_token
- get_db

## 6. API路由 (约700-4496行)
- /api/auth/* (约920-1010)
- /api/products (约1020-1100)
- /api/user/* (约2759-2892)
- /api/admin/* (约2573-2660)
- /api/meeting/* (约2663-2757)

## 7. 静态文件挂载 (约728-773行)

## 8. 启动配置 (约4496-4570行)
EOF
```

#### 下午：创建目录结构

```bash
# 1. 创建目录
cd /Users/sgl/PycharmProjects/AIchanyejiqun/Service_WaterManage/backend
mkdir -p config models api utils schemas

# 2. 创建__init__.py
touch config/__init__.py
touch models/__init__.py
touch api/__init__.py
touch utils/__init__.py
touch schemas/__init__.py

# 3. 验证目录结构
tree -L 2
```

**验证点**：
- [ ] 目录创建成功
- [ ] __init__.py文件存在
- [ ] 权限正确

---

### Day 2: 提取配置模块（1天）

#### 上午：提取数据库配置

**创建 `config/database.py`**：
```python
"""
数据库配置模块
从main.py提取的数据库连接配置
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os

# 数据库路径
SQLALCHEMY_DATABASE_URL = "sqlite:///./waterms.db"

# 创建引擎
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}
)

# 创建Session工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建Base
Base = declarative_base()

# 依赖注入函数
def get_db():
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

#### 下午：提取应用配置

**创建 `config/settings.py`**：
```python
"""
应用配置模块
从main.py提取的应用配置
"""
import os
import secrets
from datetime import timedelta

class Settings:
    # 安全配置
    SECRET_KEY: str = os.getenv("SECRET_KEY", secrets.token_urlsafe(32))
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24小时
    
    # 数据库配置
    DATABASE_URL: str = "sqlite:///./waterms.db"
    
    # 服务配置
    PORT: int = int(os.getenv("PORT", 8000))
    DEBUG: bool = True
    
    # CORS配置
    ALLOWED_ORIGINS = [
        "http://localhost",
        "http://localhost:8000",
        "http://127.0.0.1",
        "http://127.0.0.1:8000",
    ]

settings = Settings()
```

**更新 `config/__init__.py`**：
```python
from .database import Base, SessionLocal, engine, get_db
from .settings import settings

__all__ = ['Base', 'SessionLocal', 'engine', 'get_db', 'settings']
```

**验证点**：
- [ ] 配置文件创建成功
- [ ] 导入正常
- [ ] 服务启动正常

---

### Day 3: 提取模型定义（2天）

#### Day 3 上午：提取基础模型

**创建 `models/base.py`**：
```python
"""
基础模型
"""
from datetime import datetime
from sqlalchemy import Column, DateTime

class TimestampMixin:
    """时间戳混入类"""
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
```

**创建 `models/user.py`**：
```python
"""
用户相关模型
从main.py第131-144行提取
"""
from sqlalchemy import Column, Integer, String, Float
from sqlalchemy.orm import relationship
from config.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)
    department = Column(String, nullable=False)
    role = Column(String, default="staff")  # staff, admin, super_admin
    password_hash = Column(String, nullable=True)
    balance_credit = Column(Float, default=0)
    is_active = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.now)

    notifications = relationship("Notification", back_populates="user")
```

#### Day 3 下午：提取产品模型

**创建 `models/product.py`**：
```python
"""
产品相关模型
从main.py第156-199行提取
"""
# 复制main.py中的Product, ProductCategory模型定义
# 保持完全一致
```

#### Day 4：继续提取其他模型

按同样方式提取：
- `models/office.py` - OfficeAccount, OfficePickup等
- `models/transaction.py` - AccountTransaction等
- `models/meeting.py` - MeetingRoom, MeetingBooking等（如果还在main.py中）

**更新 `models/__init__.py`**：
```python
from .user import User
from .product import Product, ProductCategory
from .office import OfficeAccount, OfficePickup
from .transaction import AccountTransaction
# ... 导入其他模型

__all__ = [
    'User', 'Product', 'ProductCategory',
    'OfficeAccount', 'OfficePickup',
    'AccountTransaction',
    # ...
]
```

**验证点**：
- [ ] 所有模型提取完成
- [ ] 导入正常
- [ ] 数据库创建正常

---

### Day 5: 提取Pydantic模型（1天）

**创建 `schemas/user.py`**：
```python
"""
用户相关的Pydantic模型
从main.py第494-521行提取
"""
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class UserBase(BaseModel):
    name: str
    department: str
    role: str = "staff"

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    name: Optional[str] = None
    department: Optional[str] = None
    role: Optional[str] = None
    balance_credit: Optional[float] = None
    is_active: Optional[int] = None

class UserResponse(UserBase):
    id: int
    balance_credit: float
    is_active: int
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
```

同样方式创建：
- `schemas/product.py`
- `schemas/office.py`
- `schemas/transaction.py`

---

### Day 6: 提取工具函数（1天）

**创建 `utils/auth.py`**：
```python
"""
认证工具函数
从main.py第62-105行提取
"""
import bcrypt
from jose import jwt
from datetime import datetime, timedelta
from typing import Optional
from config.settings import settings

def hash_password(password: str) -> str:
    """使用 bcrypt 加密密码"""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"), 
            hashed_password.encode("utf-8")
        )
    except Exception:
        return False

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """创建 JWT Token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now() + expires_delta
    else:
        expire = datetime.now() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> Optional[dict]:
    """验证 JWT Token"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except Exception:
        return None
```

**创建 `utils/helpers.py`**：
```python
"""
辅助函数
"""
# 提取其他辅助函数
```

---

### Day 7: 提取API路由并重构main.py（1天）

#### Day 7 上午：提取API路由

**创建 `api/auth.py`**：
```python
"""
认证API
从main.py第920-1010行提取
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from config.database import get_db
from models.user import User
from schemas.user import UserLogin
from utils.auth import verify_password, create_access_token

router = APIRouter(prefix="/api/auth", tags=["auth"])

@router.post("/login")
def login(login_data: UserLogin, db: Session = Depends(get_db)):
    """用户登录"""
    # 复制原login函数代码
    pass

@router.get("/me")
def get_current_user_info(current_user: User = Depends(get_current_user)):
    """获取当前用户信息"""
    # 复制原函数代码
    pass
```

同样方式创建：
- `api/water.py` - 水站相关API
- `api/meeting.py` - 会议室相关API
- `api/admin.py` - 管理相关API

#### Day 7 下午：重构main.py

**新的main.py（目标< 500行）**：
```python
"""
AI产业集群空间服务系统 - 主应用
重构后的精简入口文件
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from pathlib import Path

# 导入配置
from config.database import engine, Base
from config.settings import settings

# 导入API路由
from api.auth import router as auth_router
from api.water import router as water_router
from api.meeting import router as meeting_router
from api.admin import router as admin_router

# 创建应用
app = FastAPI(
    title="AI产业集群空间服务",
    description="水站管理、会议室预约、用餐服务",
    version="2.0.0"
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 创建数据库表
Base.metadata.create_all(bind=engine)

# 注册路由
app.include_router(auth_router)
app.include_router(water_router)
app.include_router(meeting_router)
app.include_router(admin_router)

# 挂载静态文件
FRONTEND_DIR = Path(__file__).parent.parent / "frontend"
MEETING_FRONTEND_DIR = Path(__file__).parent.parent.parent / "Service_MeetingRoom" / "frontend"
PORTAL_DIR = Path(__file__).parent.parent.parent / "portal"

if FRONTEND_DIR.exists():
    app.mount("/water-admin", StaticFiles(directory=str(FRONTEND_DIR), html=True))

if MEETING_FRONTEND_DIR.exists():
    app.mount("/meeting-frontend", StaticFiles(directory=str(MEETING_FRONTEND_DIR), html=True))

if PORTAL_DIR.exists():
    app.mount("/portal", StaticFiles(directory=str(PORTAL_DIR), html=True))

# 根路径重定向
@app.get("/")
async def root():
    return RedirectResponse(url="/portal/index.html")

# 健康检查
@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "2.0.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=settings.PORT)
```

---

## 四、验证测试

### 4.1 功能验证清单

```bash
# 1. 启动服务
python main.py

# 2. 验证API
curl http://localhost:8000/api/products
curl http://localhost:8000/api/meeting/rooms

# 3. 验证登录
TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"name":"admin","password":"admin123"}' \
  | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")

# 4. 验证用户信息
curl http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer $TOKEN"

# 5. 验证前端页面
curl http://localhost:8000/water-admin/index.html
curl http://localhost:8000/meeting-frontend/index.html
curl http://localhost:8000/portal/index.html
```

### 4.2 代码验证

```bash
# 1. 检查main.py行数
wc -l main.py
# 目标: < 500行

# 2. 检查导入
python -c "from config.database import Base, get_db; print('OK')"
python -c "from models.user import User; print('OK')"
python -c "from api.auth import router; print('OK')"

# 3. 检查模型创建
python -c "from config.database import Base, engine; Base.metadata.create_all(bind=engine); print('OK')"
```

---

## 五、回滚方案

### 5.1 立即回滚

```bash
# 如果出现任何问题，立即回滚
cd /Users/sgl/PycharmProjects/AIchanyejiqun/Service_WaterManage/backend

# 1. 停止服务
pkill -f "python main.py"

# 2. 恢复原文件
cp main.py.backup main.py

# 3. 删除新目录
rm -rf config models api utils schemas

# 4. 重启服务
python main.py &
```

### 5.2 Git回滚

```bash
# 回滚到重构前
git checkout backup-before-refactor

# 或者回滚最近的提交
git reset --hard HEAD~1
```

---

## 六、注意事项

### 6.1 禁止事项

**❌ 绝对禁止**：
1. 修改业务逻辑
2. 改变API路径
3. 修改数据库结构
4. 删除任何功能

### 6.2 必须事项

**✅ 必须执行**：
1. 每一步都创建备份
2. 每一步都测试验证
3. 每一步都提交Git
4. 每一步都更新文档

---

## 七、交付清单

### 7.1 代码交付

- [ ] config/ 目录完整
- [ ] models/ 目录完整
- [ ] api/ 目录完整
- [ ] utils/ 目录完整
- [ ] schemas/ 目录完整
- [ ] main.py < 500行
- [ ] main.py.backup 存在

### 7.2 文档交付

- [ ] Sprint 1完成报告
- [ ] 代码结构文档
- [ ] API文档（自动生成）
- [ ] 测试报告

---

**Sprint 1启动时间**: 2026-04-05  
**预计完成时间**: 2026-04-12  
**执行人**: 后端开发  
**监督人**: 系统架构师  
**状态**: 📋 准备启动