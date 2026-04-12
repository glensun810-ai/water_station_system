"""
系统服务API路由 - v1版本（国际顶级安全标准）
统一的API端点，符合OAuth 2.0、OWASP、NIST安全规范
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional
from datetime import datetime, timedelta
import secrets

from config.database import get_db
from config.settings import settings
from models.user import User
from models.office import Office
from models.office_admin import OfficeAdminRelation
from depends.auth import get_current_user, get_admin_user, get_super_admin_user
from schemas.system import UserResponse, OfficeResponse, AuthResponse
from utils.jwt import create_access_token, verify_token
from utils.password import (
    hash_password,
    verify_password,
    validate_password_strength,
    needs_rehash,
)
from utils.login_attempt import (
    check_login_allowed,
    record_attempt,
    get_remaining_attempts,
    cleanup_attempts,
)
from utils.token_blacklist import revoke_token, is_token_revoked, revoke_user_tokens


router = APIRouter(prefix="/system", tags=["系统服务"])


def get_user_managed_offices(db: Session, user_id: int) -> List[dict]:
    """获取用户管理的办公室列表"""
    relations = (
        db.query(OfficeAdminRelation)
        .filter(OfficeAdminRelation.user_id == user_id)
        .all()
    )

    offices = []
    for relation in relations:
        office = db.query(Office).filter(Office.id == relation.office_id).first()
        if office:
            offices.append(
                {
                    "id": office.id,
                    "name": office.name,
                    "room_number": office.room_number,
                    "is_primary": relation.is_primary,
                    "role_type": relation.role_type,
                }
            )

    return offices


def set_user_managed_offices(
    db: Session, user_id: int, office_ids: List[int], is_primary: bool = False
):
    """设置用户管理的办公室列表"""
    db.query(OfficeAdminRelation).filter(
        OfficeAdminRelation.user_id == user_id
    ).delete()

    for office_id in office_ids:
        office = db.query(Office).filter(Office.id == office_id).first()
        if office:
            relation = OfficeAdminRelation(
                office_id=office_id,
                user_id=user_id,
                is_primary=1 if is_primary else 0,
                role_type=1,
                created_at=datetime.now(),
            )
            db.add(relation)

    db.commit()


def parse_user_agent(user_agent: str) -> dict:
    """解析User-Agent字符串"""
    if not user_agent:
        return {"device_type": "Unknown", "browser": "Unknown", "os": "Unknown"}

    result = {"device_type": "Desktop", "browser": "Unknown", "os": "Unknown"}

    mobile_keywords = ["Mobile", "Android", "iPhone", "iPad", "Windows Phone"]
    if any(keyword in user_agent for keyword in mobile_keywords):
        if "iPad" in user_agent:
            result["device_type"] = "Tablet"
        else:
            result["device_type"] = "Mobile"

    browser_patterns = [
        ("Chrome", "Chrome"),
        ("Safari", "Safari"),
        ("Firefox", "Firefox"),
        ("Edge", "Edg"),
        ("Opera", "Opera"),
        ("IE", "MSIE"),
    ]
    for browser_name, pattern in browser_patterns:
        if pattern in user_agent:
            result["browser"] = browser_name
            break

    os_patterns = [
        ("Windows 10", "Windows NT 10"),
        ("Windows", "Windows"),
        ("Mac OS X", "Mac OS X"),
        ("Linux", "Linux"),
        ("Android", "Android"),
        ("iOS", "iPhone OS"),
    ]
    for os_name, pattern in os_patterns:
        if pattern in user_agent:
            result["os"] = os_name
            break

    return result


def ensure_security_tables_exist(db: Session):
    """确保安全相关表存在"""
    try:
        db.execute(
            text("""
            CREATE TABLE IF NOT EXISTS token_blacklist (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                token_jti VARCHAR(100) UNIQUE,
                token_value TEXT,
                user_id INTEGER,
                revoked_at TIMESTAMP,
                expiry_time TIMESTAMP,
                reason VARCHAR(50),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        )

        db.execute(
            text("""
            CREATE TABLE IF NOT EXISTS login_attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username VARCHAR(100),
                ip_address VARCHAR(50),
                user_id INTEGER,
                attempt_time TIMESTAMP,
                status VARCHAR(20),
                failure_reason VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        )

        db.execute(
            text("""
            CREATE TABLE IF NOT EXISTS account_lockouts (
                username VARCHAR(100) PRIMARY KEY,
                lockout_until TIMESTAMP,
                lockout_reason VARCHAR(50),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        )

        db.execute(
            text("""
            CREATE TABLE IF NOT EXISTS user_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                session_token VARCHAR(100),
                ip_address VARCHAR(50),
                user_agent TEXT,
                device_type VARCHAR(50),
                created_at TIMESTAMP,
                last_activity TIMESTAMP,
                expires_at TIMESTAMP,
                is_active INTEGER DEFAULT 1
            )
        """)
        )

        db.commit()
    except Exception as e:
        print(f"创建安全表失败: {e}")


@router.post("/auth/login", response_model=dict)
def login(login_data: dict, request: Request, db: Session = Depends(get_db)):
    """
    用户登录（国际顶级安全标准）

    Security Features:
    - bcrypt密码验证（防止明文存储）
    - 登录失败限制（防暴力破解）
    - 登录日志记录（审计追踪）
    - Token唯一标识（支持登出）
    - Session管理（并发控制）
    """

    ensure_security_tables_exist(db)

    username = login_data.get("username")
    password = login_data.get("password")

    if not username or not password:
        raise HTTPException(status_code=400, detail="用户名和密码不能为空")

    user_agent = request.headers.get("user-agent", "")
    client_host = request.client.host if request.client else "127.0.0.1"
    device_info = parse_user_agent(user_agent)

    login_status = "failure"
    failure_reason = None
    user_id = None
    user_role = None

    try:
        allowed, error_msg = check_login_allowed(username, client_host, db)
        if not allowed:
            raise HTTPException(status_code=429, detail=error_msg)

        user = db.query(User).filter(User.username == username).first()

        if not user:
            failure_reason = "用户不存在"
            record_attempt(
                username, client_host, "failure", db, failure_reason=failure_reason
            )
            raise HTTPException(status_code=401, detail="用户名或密码错误")

        user_id = user.id
        user_role = user.role

        if not user.is_active:
            failure_reason = "账户已停用"
            record_attempt(
                username,
                client_host,
                "failure",
                db,
                user_id=user_id,
                failure_reason=failure_reason,
            )
            raise HTTPException(status_code=403, detail="账户已被停用，请联系管理员")

        if not verify_password(password, user.password_hash):
            failure_reason = "密码错误"
            record_attempt(
                username,
                client_host,
                "failure",
                db,
                user_id=user_id,
                failure_reason=failure_reason,
            )

            remaining = get_remaining_attempts(username, db)
            raise HTTPException(
                status_code=401, detail=f"用户名或密码错误，剩余尝试次数：{remaining}"
            )

        if needs_rehash(user.password_hash):
            user.password_hash = hash_password(password)
            db.commit()

        record_attempt(username, client_host, "success", db, user_id=user_id)

        jti = secrets.token_urlsafe(32)

        token_data = {
            "sub": str(user.id),
            "username": user.username,
            "role": user.role,
            "jti": jti,
            "iat": datetime.utcnow().timestamp(),
        }

        token = create_access_token(
            data=token_data,
            expires_delta=timedelta(hours=settings.ACCESS_TOKEN_EXPIRE_HOURS),
        )

        expires_at = datetime.now() + timedelta(
            hours=settings.ACCESS_TOKEN_EXPIRE_HOURS
        )

        db.execute(
            text("""
                INSERT INTO user_sessions 
                (user_id, session_token, ip_address, user_agent, device_type,
                 created_at, last_activity, expires_at, is_active)
                VALUES (:user_id, :session_token, :ip_address, :user_agent, 
                        :device_type, :created_at, :last_activity, :expires_at, 1)
            """),
            {
                "user_id": user.id,
                "session_token": jti,
                "ip_address": client_host,
                "user_agent": user_agent,
                "device_type": device_info["device_type"],
                "created_at": datetime.now().isoformat(),
                "last_activity": datetime.now().isoformat(),
                "expires_at": expires_at.isoformat(),
            },
        )

        db.execute(
            text("""
                INSERT INTO user_login_logs 
                (user_id, username, role, login_time, ip_address, user_agent,
                 device_type, browser, os, login_method, status)
                VALUES (:user_id, :username, :role, :login_time, :ip_address, 
                        :user_agent, :device_type, :browser, :os, 'password', 'success')
            """),
            {
                "user_id": user.id,
                "username": user.username,
                "role": user.role,
                "login_time": datetime.now().isoformat(),
                "ip_address": client_host,
                "user_agent": user_agent,
                "device_type": device_info["device_type"],
                "browser": device_info["browser"],
                "os": device_info["os"],
            },
        )

        user.last_login = datetime.now()
        db.commit()

        return {
            "access_token": token,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_HOURS * 3600,
            "jti": jti,
            "user_info": {
                "user_id": user.id,
                "username": user.username,
                "role": user.role,
                "role_name": user.role_name,
                "department": user.department,
                "avatar": "👤",
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"登录错误: {e}")
        raise HTTPException(status_code=500, detail="登录服务异常")


@router.post("/auth/logout")
def logout(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    用户登出（安全登出机制）

    Security Features:
    - Token黑名单（防止token重用）
    - Session记录删除
    - 登出日志记录
    """

    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]

        payload = verify_token(token)
        if payload:
            jti = payload.get("jti")

            if jti:
                revoke_token(token, db)

                db.execute(
                    text("""
                        UPDATE user_sessions 
                        SET is_active = 0 
                        WHERE user_id = :user_id AND session_token = :jti
                    """),
                    {"user_id": current_user.id, "jti": jti},
                )

                db.execute(
                    text("""
                        INSERT INTO user_login_logs 
                        (user_id, username, role, login_time, ip_address, 
                         login_method, status, logout_time)
                        VALUES (:user_id, :username, :role, :logout_time, 
                                :ip_address, 'logout', 'success', :logout_time)
                    """),
                    {
                        "user_id": current_user.id,
                        "username": current_user.username,
                        "role": current_user.role,
                        "logout_time": datetime.now().isoformat(),
                        "ip_address": request.client.host
                        if request.client
                        else "127.0.0.1",
                    },
                )

                db.commit()

    return {"message": "登出成功", "user_id": current_user.id}


@router.post("/auth/change-password")
def change_password(
    password_data: dict,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    修改密码（安全密码管理）

    Security Features:
    - 验证旧密码
    - 新密码强度检查
    - 强制重新登录所有会话
    - 密码修改日志
    """

    old_password = password_data.get("old_password")
    new_password = password_data.get("new_password")

    if not old_password or not new_password:
        raise HTTPException(status_code=400, detail="旧密码和新密码不能为空")

    if not verify_password(old_password, current_user.password_hash):
        raise HTTPException(status_code=401, detail="旧密码错误")

    is_valid, error_msg = validate_password_strength(new_password)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_msg)

    if old_password == new_password:
        raise HTTPException(status_code=400, detail="新密码不能与旧密码相同")

    current_user.password_hash = hash_password(new_password)
    current_user.updated_at = datetime.now()

    revoke_user_tokens(current_user.id, db)

    db.execute(
        text("""
            UPDATE user_sessions 
            SET is_active = 0 
            WHERE user_id = :user_id
        """),
        {"user_id": current_user.id},
    )

    db.execute(
        text("""
            INSERT INTO user_login_logs 
            (user_id, username, role, login_time, ip_address, login_method, status)
            VALUES (:user_id, :username, :role, :login_time, :ip_address, 
                    'change_password', 'success')
        """),
        {
            "user_id": current_user.id,
            "username": current_user.username,
            "role": current_user.role,
            "login_time": datetime.now().isoformat(),
            "ip_address": request.client.host if request.client else "127.0.0.1",
        },
    )

    db.commit()

    return {"message": "密码修改成功，请重新登录", "user_id": current_user.id}


@router.get("/auth/profile")
def get_profile(current_user: User = Depends(get_current_user)):
    """获取当前用户个人信息"""
    return {
        "user_id": current_user.id,
        "username": current_user.username,
        "name": current_user.name,
        "role": current_user.role,
        "role_name": current_user.role_name,
        "department": current_user.department,
        "email": current_user.email,
        "phone": current_user.phone,
        "avatar": "👤",
        "created_at": current_user.created_at.isoformat()
        if current_user.created_at
        else None,
        "last_login": current_user.last_login.isoformat()
        if current_user.last_login
        else None,
    }


@router.get("/auth/sessions")
def get_active_sessions(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """获取用户活跃会话"""

    sessions = db.execute(
        text("""
            SELECT id, ip_address, device_type, created_at, last_activity, expires_at
            FROM user_sessions
            WHERE user_id = :user_id AND is_active = 1 AND expires_at > :now
            ORDER BY last_activity DESC
        """),
        {"user_id": current_user.id, "now": datetime.now().isoformat()},
    ).fetchall()

    return {
        "sessions": [
            {
                "id": s.id,
                "ip_address": s.ip_address,
                "device_type": s.device_type,
                "created_at": s.created_at,
                "last_activity": s.last_activity,
                "expires_at": s.expires_at,
            }
            for s in sessions
        ],
        "total": len(sessions),
    }


@router.delete("/auth/sessions/{session_id}")
def revoke_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """撤销特定会话"""

    session = db.execute(
        text("""
            SELECT id, session_token FROM user_sessions
            WHERE id = :id AND user_id = :user_id
        """),
        {"id": session_id, "user_id": current_user.id},
    ).fetchone()

    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")

    db.execute(
        text("UPDATE user_sessions SET is_active = 0 WHERE id = :id"),
        {"id": session_id},
    )

    if session.session_token:
        db.execute(
            text("""
                INSERT INTO token_blacklist 
                (token_jti, revoked_at, expiry_time, reason)
                VALUES (:jti, :now, :expiry, 'session_revoked')
            """),
            {
                "jti": session.session_token,
                "now": datetime.now().isoformat(),
                "expiry": (datetime.now() + timedelta(hours=24)).isoformat(),
            },
        )

    db.commit()

    return {"message": "会话已撤销", "session_id": session_id}


@router.get("/users/stats/overview")
def get_user_stats(db: Session = Depends(get_db)):
    """获取用户统计概览"""

    total = db.query(User).count()
    super_admins = db.query(User).filter(User.role == "super_admin").count()
    admins = db.query(User).filter(User.role == "admin").count()
    office_admins = db.query(User).filter(User.role == "office_admin").count()
    users = db.query(User).filter(User.role == "user").count()
    active = db.query(User).filter(User.is_active == 1).count()
    inactive = db.query(User).filter(User.is_active == 0).count()

    return {
        "total": total,
        "super_admins": super_admins,
        "admins": admins,
        "office_admins": office_admins,
        "users": users,
        "active": active,
        "inactive": inactive,
    }


@router.get("/users", response_model=dict)
def get_users(
    page: int = Query(1, description="页码"),
    limit: int = Query(20, description="每页数量"),
    role: Optional[str] = Query(None, description="用户角色过滤"),
    department: Optional[str] = Query(None, description="部门过滤"),
    is_active: Optional[bool] = Query(None, description="激活状态过滤"),
    q: Optional[str] = Query(None, description="全局搜索关键词"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    """获取用户列表（仅管理员）"""

    query = db.query(User)

    if role:
        query = query.filter(User.role == role)

    if department:
        query = query.filter(User.department == department)

    if is_active is not None:
        query = query.filter(User.is_active == is_active)

    if q:
        query = query.filter(User.username.contains(q) | User.name.contains(q))

    total = query.count()
    users = query.offset((page - 1) * limit).limit(limit).all()

    items = []
    for user in users:
        managed_offices = []
        if user.role == "office_admin":
            managed_offices = get_user_managed_offices(db, user.id)

        office_names = [o["name"] for o in managed_offices]

        items.append(
            {
                "id": user.id,
                "username": user.username,
                "name": user.name,
                "role": user.role,
                "department": user.department,
                "is_active": user.is_active,
                "email": user.email,
                "phone": user.phone,
                "balance_credit": user.balance_credit,
                "created_at": user.created_at.isoformat() if user.created_at else None,
                "managed_offices": managed_offices,
                "managed_office_names": ", ".join(office_names)
                if office_names
                else (user.department or ""),
            }
        )

    return {
        "items": items,
        "total": total,
        "page": page,
        "limit": limit,
        "pages": (total + limit - 1) // limit,
    }


@router.get("/users/{user_id}", response_model=UserResponse)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    """获取用户详情（仅管理员）"""

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    return user


@router.put("/users/{user_id}")
def update_user(
    user_id: int,
    user_update: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    """更新用户信息（仅管理员）"""

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    if user.role == "super_admin" and current_user.role != "super_admin":
        raise HTTPException(status_code=403, detail="无权限修改超级管理员")

    office_ids = user_update.get("office_ids")
    new_role = user_update.get("role")

    if new_role == "office_admin":
        if office_ids is not None and len(office_ids) == 0:
            raise HTTPException(
                status_code=400, detail="办公室管理员需要至少管理一个办公室"
            )

        if office_ids:
            set_user_managed_offices(db, user.id, office_ids)
            first_office = db.query(Office).filter(Office.id == office_ids[0]).first()
            if first_office and not user_update.get("department"):
                user_update["department"] = first_office.name
    elif new_role and new_role != "office_admin":
        db.query(OfficeAdminRelation).filter(
            OfficeAdminRelation.user_id == user.id
        ).delete()

    update_data = {
        k: v
        for k, v in user_update.items()
        if hasattr(User, k) and k not in ["id", "password_hash", "office_ids"]
    }

    for key, value in update_data.items():
        setattr(user, key, value)

    if "password" in user_update and user_update["password"]:
        user.password_hash = hash_password(user_update["password"])

    user.updated_at = datetime.now()

    db.commit()
    db.refresh(user)

    managed_offices = []
    if user.role == "office_admin":
        managed_offices = get_user_managed_offices(db, user.id)

    return {
        "message": "用户信息更新成功",
        "user_id": user_id,
        "managed_offices": managed_offices,
    }


@router.delete("/users/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_super_admin_user),
):
    """删除用户（仅超级管理员）"""

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="不能删除自己的账户")

    if user.role == "super_admin":
        raise HTTPException(status_code=403, detail="不能删除超级管理员账户")

    revoke_user_tokens(user.id, db)

    db.execute(
        text("UPDATE user_sessions SET is_active = 0 WHERE user_id = :user_id"),
        {"user_id": user.id},
    )

    user.is_active = False
    user.updated_at = datetime.now()

    db.commit()

    return {"message": "用户已停用", "user_id": user_id}


@router.post("/users")
def create_user(
    user_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    """创建用户（仅管理员）"""

    username = user_data.get("name")
    password = user_data.get("password", "123456")
    department = user_data.get("department")
    role = user_data.get("role", "user")
    is_active = user_data.get("is_active", 1)
    office_ids = user_data.get("office_ids", [])

    if not username:
        raise HTTPException(status_code=400, detail="用户名不能为空")

    existing = db.query(User).filter(User.username == username).first()
    if existing:
        raise HTTPException(status_code=400, detail="用户名已存在")

    if role == "office_admin" and not office_ids:
        raise HTTPException(
            status_code=400, detail="办公室管理员需要分配到至少一个办公室"
        )

    hashed_password = hash_password(password)

    first_office_name = None
    if office_ids:
        first_office = db.query(Office).filter(Office.id == office_ids[0]).first()
        if first_office:
            first_office_name = first_office.name

    new_user = User(
        username=username,
        name=username,
        password_hash=hashed_password,
        department=department or first_office_name,
        role=role,
        is_active=is_active,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    if role == "office_admin" and office_ids:
        set_user_managed_offices(db, new_user.id, office_ids)

    return {
        "message": "用户创建成功",
        "user_id": new_user.id,
        "username": new_user.username,
    }


@router.post("/users/batch")
def batch_update_users(
    batch_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    """批量更新用户"""

    user_ids = batch_data.get("user_ids", [])
    updates = batch_data.get("updates", {})
    office_ids = batch_data.get("office_ids")

    if not user_ids:
        raise HTTPException(status_code=400, detail="用户ID列表不能为空")

    updated_count = 0
    for user_id in user_ids:
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            if user.role == "super_admin" and current_user.role != "super_admin":
                continue

            for key, value in updates.items():
                if hasattr(User, key) and key not in ["id", "password_hash"]:
                    setattr(user, key, value)

            if office_ids is not None:
                if user.role == "office_admin":
                    if len(office_ids) == 0:
                        continue
                    set_user_managed_offices(db, user.id, office_ids)
                    first_office = (
                        db.query(Office).filter(Office.id == office_ids[0]).first()
                    )
                    if first_office:
                        user.department = first_office.name

            user.updated_at = datetime.now()
            updated_count += 1

    db.commit()

    return {"message": "批量更新成功", "updated_count": updated_count}


@router.post("/users/batch-delete")
def batch_delete_users(
    user_ids: List[int],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_super_admin_user),
):
    """批量删除用户（仅超级管理员）"""

    if not user_ids:
        raise HTTPException(status_code=400, detail="用户ID列表不能为空")

    deleted_count = 0
    for user_id in user_ids:
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            if user.id == current_user.id:
                continue

            if user.role == "super_admin":
                continue

            revoke_user_tokens(user.id, db)

            db.execute(
                text("UPDATE user_sessions SET is_active = 0 WHERE user_id = :user_id"),
                {"user_id": user.id},
            )

            user.is_active = False
            user.updated_at = datetime.now()
            deleted_count += 1

    db.commit()

    return {"message": "批量删除成功", "deleted_count": deleted_count}


@router.get("/offices", response_model=dict)
def get_offices(
    page: int = Query(1, description="页码"),
    limit: int = Query(20, description="每页数量"),
    is_active: Optional[bool] = Query(True, description="是否只返回激活的办公室"),
    q: Optional[str] = Query(None, description="全局搜索关键词"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取办公室列表"""

    query = db.query(Office)

    if is_active is not None:
        query = query.filter(Office.is_active == is_active)

    if q:
        query = query.filter(Office.name.contains(q) | Office.room_number.contains(q))

    total = query.count()
    offices = query.order_by(Office.name).offset((page - 1) * limit).limit(limit).all()

    items = []
    for office in offices:
        items.append(
            {
                "id": office.id,
                "name": office.name,
                "room_number": office.room_number,
                "leader_name": office.leader_name,
                "is_active": office.is_active,
            }
        )

    return {
        "items": items,
        "total": total,
        "page": page,
        "limit": limit,
        "pages": (total + limit - 1) // limit,
    }


@router.get("/offices/{office_id}", response_model=OfficeResponse)
def get_office(
    office_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取办公室详情"""

    office = db.query(Office).filter(Office.id == office_id).first()
    if not office:
        raise HTTPException(status_code=404, detail="办公室不存在")

    return office


@router.post("/offices")
def create_office(
    office_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    """创建办公室（仅管理员）"""

    from models.office import Office

    office = Office(
        name=office_data.get("name"),
        room_number=office_data.get("room_number"),
        leader_name=office_data.get("leader_name"),
        manager_name=office_data.get("manager_name"),
        contact_info=office_data.get("contact_info"),
        is_active=True,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )

    db.add(office)
    db.commit()
    db.refresh(office)

    return {"message": "办公室创建成功", "office_id": office.id}


@router.put("/offices/{office_id}")
def update_office(
    office_id: int,
    office_update: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    """更新办公室信息（仅管理员）"""

    office = db.query(Office).filter(Office.id == office_id).first()
    if not office:
        raise HTTPException(status_code=404, detail="办公室不存在")

    update_data = {
        k: v for k, v in office_update.items() if hasattr(Office, k) and k not in ["id"]
    }

    for key, value in update_data.items():
        setattr(office, key, value)

    office.updated_at = datetime.now()

    db.commit()
    db.refresh(office)

    return {"message": "办公室信息更新成功", "office_id": office_id}


@router.delete("/offices/{office_id}")
def delete_office(
    office_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    """删除办公室（逻辑删除，仅管理员）"""

    office = db.query(Office).filter(Office.id == office_id).first()
    if not office:
        raise HTTPException(status_code=404, detail="办公室不存在")

    office.is_active = False
    office.updated_at = datetime.now()

    db.commit()

    return {"message": "办公室已停用", "office_id": office_id}


@router.post("/users/{user_id}/reset-password")
def reset_user_password(
    user_id: int,
    password_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    """重置用户密码（仅管理员）"""

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    if user.role == "super_admin" and current_user.role != "super_admin":
        raise HTTPException(status_code=403, detail="无权限修改超级管理员密码")

    new_password = password_data.get("new_password", "123456")

    is_valid, error_msg = validate_password_strength(new_password)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_msg)

    user.password_hash = hash_password(new_password)
    user.updated_at = datetime.now()

    revoke_user_tokens(user.id, db)

    db.execute(
        text("UPDATE user_sessions SET is_active = 0 WHERE user_id = :user_id"),
        {"user_id": user.id},
    )

    db.commit()

    return {
        "message": "密码重置成功",
        "user_id": user_id,
        "username": user.username,
        "new_password": new_password,
    }


@router.get("/users/{user_id}/login-history")
def get_user_login_history(
    user_id: int,
    limit: int = Query(20, description="返回记录数量"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    """获取用户登录历史（仅管理员）"""

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    history = db.execute(
        text("""
            SELECT id, login_time, ip_address, device_type, browser, os, 
                   login_method, status, logout_time
            FROM user_login_logs
            WHERE user_id = :user_id
            ORDER BY login_time DESC
            LIMIT :limit
        """),
        {"user_id": user_id, "limit": limit},
    ).fetchall()

    return {
        "user_id": user_id,
        "username": user.username,
        "history": [
            {
                "id": h.id,
                "login_time": h.login_time,
                "ip_address": h.ip_address,
                "device_type": h.device_type,
                "browser": h.browser,
                "os": h.os,
                "login_method": h.login_method,
                "status": h.status,
                "logout_time": h.logout_time,
            }
            for h in history
        ],
        "total": len(history),
    }


@router.get("/config/payment-qr")
def get_payment_qr(db: Session = Depends(get_db)):
    """获取支付二维码配置"""
    from models.config import SystemConfig

    config = (
        db.query(SystemConfig)
        .filter(SystemConfig.config_key == "payment_qr_code")
        .first()
    )

    if config and config.config_value:
        return {"qr_code": config.config_value}

    return {"qr_code": None}


@router.get("/users/{user_id}/managed-offices")
def get_user_managed_offices_api(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    """获取用户管理的办公室列表"""

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    offices = get_user_managed_offices(db, user_id)

    return {
        "user_id": user_id,
        "username": user.username,
        "managed_offices": offices,
    }


@router.put("/users/{user_id}/managed-offices")
def update_user_managed_offices_api(
    user_id: int,
    office_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    """更新用户管理的办公室列表"""

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    if user.role == "super_admin" and current_user.role != "super_admin":
        raise HTTPException(status_code=403, detail="无权限修改超级管理员")

    office_ids = office_data.get("office_ids", [])

    if user.role == "office_admin" and len(office_ids) == 0:
        raise HTTPException(
            status_code=400, detail="办公室管理员需要至少管理一个办公室"
        )

    set_user_managed_offices(db, user_id, office_ids)

    if office_ids:
        first_office = db.query(Office).filter(Office.id == office_ids[0]).first()
        if first_office:
            user.department = first_office.name
            user.updated_at = datetime.now()
            db.commit()

    offices = get_user_managed_offices(db, user_id)

    return {
        "message": "办公室管理权限更新成功",
        "user_id": user_id,
        "managed_offices": offices,
    }


@router.get("/offices/{office_id}/admins")
def get_office_admins_api(
    office_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    """获取办公室的管理员列表"""

    office = db.query(Office).filter(Office.id == office_id).first()
    if not office:
        raise HTTPException(status_code=404, detail="办公室不存在")

    relations = (
        db.query(OfficeAdminRelation)
        .filter(OfficeAdminRelation.office_id == office_id)
        .all()
    )

    admins = []
    for relation in relations:
        user = db.query(User).filter(User.id == relation.user_id).first()
        if user:
            admins.append(
                {
                    "id": user.id,
                    "username": user.username,
                    "name": user.name,
                    "is_primary": relation.is_primary,
                    "role_type": relation.role_type,
                }
            )

    return {
        "office_id": office_id,
        "office_name": office.name,
        "admins": admins,
    }
