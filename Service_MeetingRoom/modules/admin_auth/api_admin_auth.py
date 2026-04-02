"""
管理员权限验证模块
功能：JWT登录验证、角色权限体系、操作日志记录
Created by: AI Development Team
Version: 1.0.0
"""

from fastapi import APIRouter, HTTPException, Depends, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import text
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional, List
from pydantic import BaseModel, EmailStr
from jose import jwt, JWTError
from passlib.context import CryptContext
import os

router = APIRouter(prefix="/api/admin", tags=["admin_auth"])

# JWT配置
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production-2026")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 2

# 密码加密
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Bearer Token认证
security = HTTPBearer()


# ==================== 数据模型 ====================


class AdminLogin(BaseModel):
    """管理员登录请求"""

    username: str
    password: str


class AdminUserCreate(BaseModel):
    """创建管理员用户"""

    username: str
    password: str
    email: Optional[str] = None
    role_id: int = 2  # 默认为普通管理员


class AdminUserResponse(BaseModel):
    """管理员用户响应"""

    id: int
    username: str
    email: Optional[str]
    role_id: int
    role_name: Optional[str] = None
    is_active: bool
    created_at: datetime


class TokenResponse(BaseModel):
    """Token响应"""

    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user_info: dict


class OperationLogCreate(BaseModel):
    """操作日志创建"""

    user_id: int
    operation_type: str
    operation_content: str
    operation_result: str = "success"


class OperationLogResponse(BaseModel):
    """操作日志响应"""

    id: int
    user_id: int
    username: Optional[str]
    operation_type: str
    operation_content: str
    operation_result: str
    created_at: datetime


# ==================== 工具函数 ====================


def get_db():
    """获取数据库会话"""
    from Service_WaterManage.backend.api_meeting import MeetingSessionLocal

    db = MeetingSessionLocal()
    try:
        yield db
    finally:
        db.close()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """生成密码哈希"""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    创建JWT访问令牌

    Args:
        data: 要编码的数据
        expires_delta: 过期时间增量

    Returns:
        JWT令牌
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> dict:
    """
    解码JWT令牌

    Args:
        token: JWT令牌

    Returns:
        解码后的数据

    Raises:
        HTTPException: 令牌无效或过期
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=401,
            detail="无效的认证令牌",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> dict:
    """
    获取当前登录用户（依赖注入）

    Args:
        credentials: HTTP Bearer认证凭据
        db: 数据库会话

    Returns:
        用户信息字典

    Raises:
        HTTPException: 未授权
    """
    token = credentials.credentials
    payload = decode_access_token(token)

    user_id = payload.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="无效的令牌载荷")

    # 查询用户信息（参数化查询）
    query = text("""
        SELECT u.id, u.username, u.email, u.role_id, u.is_active,
               r.role_name, r.permissions
        FROM admin_users u
        LEFT JOIN admin_roles r ON u.role_id = r.id
        WHERE u.id = :user_id AND u.is_active = 1
    """)

    result = db.execute(query, {"user_id": user_id})
    user = result.fetchone()

    if not user:
        raise HTTPException(status_code=401, detail="用户不存在或已禁用")

    return {
        "user_id": user.id,
        "username": user.username,
        "email": user.email,
        "role_id": user.role_id,
        "role_name": user.role_name,
        "permissions": user.permissions,
    }


def check_permission(user: dict, required_permission: str) -> bool:
    """
    检查用户权限

    Args:
        user: 用户信息
        required_permission: 需要的权限

    Returns:
        是否有权限
    """
    # 超级管理员拥有所有权限
    if user.get("role_id") == 1:
        return True

    # 检查具体权限
    permissions = user.get("permissions", "")
    if not permissions:
        return False

    # 权限是JSON数组字符串，简单检查是否包含
    return required_permission in permissions


def require_permission(permission: str):
    """
    权限装饰器

    Args:
        permission: 需要的权限

    Returns:
        依赖函数
    """

    async def permission_checker(current_user: dict = Depends(get_current_user)):
        if not check_permission(current_user, permission):
            raise HTTPException(
                status_code=403, detail=f"权限不足：需要 {permission} 权限"
            )
        return current_user

    return permission_checker


# ==================== 初始化数据 ====================


def init_admin_tables(db: Session):
    """
    初始化管理员表和默认数据

    Args:
        db: 数据库会话
    """
    # 创建角色表
    db.execute(
        text("""
        CREATE TABLE IF NOT EXISTS admin_roles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            role_name VARCHAR(50) UNIQUE NOT NULL,
            permissions TEXT,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    )

    # 创建用户表
    db.execute(
        text("""
        CREATE TABLE IF NOT EXISTS admin_users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username VARCHAR(50) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            email VARCHAR(100),
            role_id INTEGER,
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP,
            FOREIGN KEY (role_id) REFERENCES admin_roles(id)
        )
    """)
    )

    # 创建操作日志表
    db.execute(
        text("""
        CREATE TABLE IF NOT EXISTS admin_operation_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            operation_type VARCHAR(50),
            operation_content TEXT,
            operation_result VARCHAR(20),
            ip_address VARCHAR(50),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES admin_users(id)
        )
    """)
    )

    db.commit()

    # 初始化默认角色
    roles = [
        (1, "超级管理员", '["all"]', "拥有所有权限"),
        (
            2,
            "会议室管理员",
            '["booking_manage", "room_manage", "stats_view"]',
            "管理预约和会议室",
        ),
        (
            3,
            "财务人员",
            '["booking_view", "stats_view", "finance_report"]',
            "查看预约和财务报表",
        ),
        (4, "普通员工", '["booking_view"]', "仅查看预约"),
    ]

    for role_id, role_name, permissions, description in roles:
        # 检查角色是否存在
        result = db.execute(
            text("SELECT id FROM admin_roles WHERE id = :id"), {"id": role_id}
        )
        if not result.fetchone():
            db.execute(
                text("""
                INSERT INTO admin_roles (id, role_name, permissions, description)
                VALUES (:id, :role_name, :permissions, :description)
            """),
                {
                    "id": role_id,
                    "role_name": role_name,
                    "permissions": permissions,
                    "description": description,
                },
            )

    db.commit()

    # 初始化默认超级管理员（用户名：admin，密码：admin123）
    result = db.execute(text("SELECT id FROM admin_users WHERE username = 'admin'"))
    if not result.fetchone():
        hashed_password = get_password_hash("admin123")
        db.execute(
            text("""
            INSERT INTO admin_users (username, password_hash, role_id, is_active)
            VALUES ('admin', :password_hash, 1, 1)
        """),
            {"password_hash": hashed_password},
        )
        db.commit()


# ==================== API接口 ====================


@router.post("/login", response_model=TokenResponse)
async def admin_login(login_data: AdminLogin, db: Session = Depends(get_db)):
    """
    管理员登录

    功能：
    1. 验证用户名和密码
    2. 生成JWT令牌（2小时有效）
    3. 记录登录日志

    安全：
    - 密码加密存储（bcrypt）
    - 参数化查询（防SQL注入）
    - 登录失败不泄露详细信息
    """
    try:
        # 初始化表结构
        init_admin_tables(db)

        # 查询用户（参数化查询）
        query = text("""
            SELECT u.id, u.username, u.password_hash, u.email, u.role_id, u.is_active,
                   r.role_name, r.permissions
            FROM admin_users u
            LEFT JOIN admin_roles r ON u.role_id = r.id
            WHERE u.username = :username
        """)

        result = db.execute(query, {"username": login_data.username})
        user = result.fetchone()

        # 验证用户存在且激活
        if not user or not user.is_active:
            raise HTTPException(status_code=401, detail="用户名或密码错误")

        # 验证密码
        if not verify_password(login_data.password, user.password_hash):
            raise HTTPException(status_code=401, detail="用户名或密码错误")

        # 生成JWT令牌
        access_token = create_access_token(
            data={
                "user_id": user.id,
                "username": user.username,
                "role_id": user.role_id,
            }
        )

        # 记录登录日志
        db.execute(
            text("""
            INSERT INTO admin_operation_logs (user_id, operation_type, operation_content, operation_result)
            VALUES (:user_id, 'login', '管理员登录', 'success')
        """),
            {"user_id": user.id},
        )
        db.commit()

        return TokenResponse(
            access_token=access_token,
            expires_in=ACCESS_TOKEN_EXPIRE_HOURS * 3600,
            user_info={
                "user_id": user.id,
                "username": user.username,
                "email": user.email,
                "role_id": user.role_id,
                "role_name": user.role_name,
                "permissions": user.permissions,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"登录失败: {str(e)}")


@router.post("/logout")
async def admin_logout(
    current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)
):
    """
    管理员登出

    功能：记录登出日志
    """
    try:
        # 记录登出日志
        db.execute(
            text("""
            INSERT INTO admin_operation_logs (user_id, operation_type, operation_content, operation_result)
            VALUES (:user_id, 'logout', '管理员登出', 'success')
        """),
            {"user_id": current_user["user_id"]},
        )
        db.commit()

        return {"message": "登出成功"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"登出失败: {str(e)}")


@router.get("/me", response_model=AdminUserResponse)
async def get_current_user_info(
    current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)
):
    """
    获取当前用户信息
    """
    try:
        query = text("""
            SELECT u.id, u.username, u.email, u.role_id, u.is_active, u.created_at,
                   r.role_name
            FROM admin_users u
            LEFT JOIN admin_roles r ON u.role_id = r.id
            WHERE u.id = :user_id
        """)

        result = db.execute(query, {"user_id": current_user["user_id"]})
        user = result.fetchone()

        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")

        return AdminUserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            role_id=user.role_id,
            role_name=user.role_name,
            is_active=bool(user.is_active),
            created_at=user.created_at or datetime.now(),
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取用户信息失败: {str(e)}")


@router.get("/logs", response_model=List[OperationLogResponse])
async def get_operation_logs(
    limit: int = 50,
    offset: int = 0,
    current_user: dict = Depends(require_permission("logs_view")),
    db: Session = Depends(get_db),
):
    """
    获取操作日志（需要权限）

    权限要求：超级管理员或拥有 logs_view 权限
    """
    try:
        query = text("""
            SELECT l.id, l.user_id, u.username, l.operation_type, 
                   l.operation_content, l.operation_result, l.created_at
            FROM admin_operation_logs l
            LEFT JOIN admin_users u ON l.user_id = u.id
            ORDER BY l.created_at DESC
            LIMIT :limit OFFSET :offset
        """)

        result = db.execute(query, {"limit": limit, "offset": offset})
        logs = []

        for row in result:
            logs.append(
                OperationLogResponse(
                    id=row.id,
                    user_id=row.user_id,
                    username=row.username,
                    operation_type=row.operation_type,
                    operation_content=row.operation_content,
                    operation_result=row.operation_result,
                    created_at=row.created_at or datetime.now(),
                )
            )

        return logs

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取操作日志失败: {str(e)}")


@router.post("/users", response_model=AdminUserResponse)
async def create_admin_user(
    user_data: AdminUserCreate,
    current_user: dict = Depends(require_permission("user_manage")),
    db: Session = Depends(get_db),
):
    """
    创建管理员用户（需要权限）

    权限要求：超级管理员或拥有 user_manage 权限
    """
    try:
        # 检查用户名是否已存在
        result = db.execute(
            text("SELECT id FROM admin_users WHERE username = :username"),
            {"username": user_data.username},
        )
        if result.fetchone():
            raise HTTPException(status_code=400, detail="用户名已存在")

        # 创建用户
        hashed_password = get_password_hash(user_data.password)
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        db.execute(
            text("""
            INSERT INTO admin_users (username, password_hash, email, role_id, is_active, created_at)
            VALUES (:username, :password_hash, :email, :role_id, 1, :created_at)
        """),
            {
                "username": user_data.username,
                "password_hash": hashed_password,
                "email": user_data.email,
                "role_id": user_data.role_id,
                "created_at": now,
            },
        )

        # 获取新创建的用户ID
        result = db.execute(text("SELECT last_insert_rowid()"))
        user_id = result.fetchone()[0]

        # 记录操作日志
        db.execute(
            text("""
            INSERT INTO admin_operation_logs (user_id, operation_type, operation_content, operation_result)
            VALUES (:user_id, 'create_user', :content, 'success')
        """),
            {
                "user_id": current_user["user_id"],
                "content": f"创建管理员用户：{user_data.username}",
            },
        )

        db.commit()

        # 返回创建的用户
        result = db.execute(
            text(
                "SELECT id, username, email, role_id, is_active, created_at FROM admin_users WHERE id = :id"
            ),
            {"id": user_id},
        )
        user = result.fetchone()

        return AdminUserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            role_id=user.role_id,
            is_active=bool(user.is_active),
            created_at=user.created_at or datetime.now(),
        )

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"创建用户失败: {str(e)}")


@router.get("/roles")
async def get_roles(
    current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)
):
    """获取所有角色列表"""
    try:
        result = db.execute(
            text("""
            SELECT id, role_name, permissions, description, created_at
            FROM admin_roles
            ORDER BY id
        """)
        )

        roles = []
        for row in result:
            roles.append(
                {
                    "id": row.id,
                    "role_name": row.role_name,
                    "permissions": row.permissions,
                    "description": row.description,
                    "created_at": row.created_at,
                }
            )

        return {"roles": roles}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取角色列表失败: {str(e)}")


# 导出依赖函数供其他模块使用
__all__ = [
    "get_current_user",
    "require_permission",
    "check_permission",
    "create_access_token",
    "decode_access_token",
    "init_admin_tables",
]
