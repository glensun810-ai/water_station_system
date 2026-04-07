"""
统一用户登录API
支持所有用户类型登录（超级管理员、系统管理员、办公室管理员、普通用户）
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import timedelta, datetime
from pydantic import BaseModel
from typing import Optional
from passlib.context import CryptContext

from config.database import get_db
from config.settings import settings
from utils.jwt import create_access_token, verify_token

router = APIRouter(prefix="/api/user", tags=["user_auth"])
security = HTTPBearer(auto_error=False)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ACCESS_TOKEN_EXPIRE_HOURS = 24


# ==================== 数据模型 ====================


class UserLogin(BaseModel):
    name: str
    password: str


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str


class UserRegister(BaseModel):
    name: str
    password: str
    user_type: str = "internal"  # 'internal' or 'external'
    department: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    company: Optional[str] = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user_info: dict


class UserInfo(BaseModel):
    id: int
    name: str
    department: Optional[str] = None
    role: str
    role_name: str
    is_active: int
    office_name: Optional[str] = None


# ==================== 辅助函数 ====================


def get_role_display_name(role: str, department: str = None) -> str:
    """获取角色显示名称"""
    role_names = {
        "super_admin": "超级管理员",
        "admin": "系统管理员",
        "office_admin": "办公室管理员",
        "user": "普通用户",
    }

    if role == "office_admin" and department:
        return f"{department}管理员"

    return role_names.get(role, role)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    if not hashed_password:
        # 兼容无密码的旧数据
        return plain_password == "123456"
    return pwd_context.verify(plain_password, hashed_password)


def parse_user_agent(user_agent: str) -> dict:
    """解析User-Agent字符串，提取设备信息"""
    if not user_agent:
        return {"device_type": "Unknown", "browser": "Unknown", "os": "Unknown"}

    result = {"device_type": "Desktop", "browser": "Unknown", "os": "Unknown"}

    # 检测移动设备
    mobile_keywords = ["Mobile", "Android", "iPhone", "iPad", "Windows Phone"]
    if any(keyword in user_agent for keyword in mobile_keywords):
        if "iPad" in user_agent:
            result["device_type"] = "Tablet"
        else:
            result["device_type"] = "Mobile"

    # 检测浏览器
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

    # 检测操作系统
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


# ==================== API接口 ====================


@router.post("/register")
def user_register(
    register_data: UserRegister, request: Request, db: Session = Depends(get_db)
):
    """
    用户注册

    内部用户：
    - name: 用户名（唯一）
    - password: 密码（至少6位）
    - user_type: 'internal'（默认）
    - department: 所属办公室（可选，由管理员分配）

    外部用户：
    - name: 用户名（唯一）
    - password: 密码（至少6位）
    - user_type: 'external'
    - phone: 手机号（必填）
    - email: 邮箱（可选）
    - company: 公司名称（可选）
    """
    user_agent = request.headers.get("user-agent", "")
    client_host = request.client.host if request.client else "127.0.0.1"
    device_info = parse_user_agent(user_agent)

    # 验证用户名长度
    if len(register_data.name) < 2 or len(register_data.name) > 50:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名长度应在2-50个字符之间",
        )

    # 验证用户名格式（只允许字母、数字、下划线、中文）
    import re

    if not re.match(r"^[\w\u4e00-\u9fa5]+$", register_data.name):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名只能包含字母、数字、下划线和中文",
        )

    # 验证密码长度
    if len(register_data.password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="密码长度至少为6位"
        )

    # 验证user_type
    if register_data.user_type not in ["internal", "external"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户类型必须是 'internal' 或 'external'",
        )

    # 外部用户验证
    if register_data.user_type == "external":
        # 必须提供手机号
        if not register_data.phone:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="外部用户必须提供手机号",
            )

        # 验证手机号格式
        if not re.match(r"^1[3-9]\d{9}$", register_data.phone):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="手机号格式不正确",
            )

        # 检查手机号是否已存在
        phone_check = text("SELECT id FROM users WHERE phone = :phone")
        existing_phone = db.execute(
            phone_check, {"phone": register_data.phone}
        ).fetchone()

        if existing_phone:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="该手机号已被注册",
            )

    # 检查用户名是否已存在
    check_query = text("SELECT id FROM users WHERE name = :name")
    existing_user = db.execute(check_query, {"name": register_data.name}).fetchone()

    if existing_user:
        # 记录注册失败日志
        db.execute(
            text("""
            INSERT INTO user_login_logs 
            (user_id, username, login_time, ip_address, user_agent,
             device_type, browser, os, login_method, status, failure_reason)
            VALUES 
            (0, :username, :login_time, :ip_address, :user_agent,
             :device_type, :browser, :os, 'register', 'failure', '用户名已存在')
        """),
            {
                "username": register_data.name,
                "login_time": datetime.now().isoformat(),
                "ip_address": client_host,
                "user_agent": user_agent,
                "device_type": device_info["device_type"],
                "browser": device_info["browser"],
                "os": device_info["os"],
            },
        )
        db.commit()

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="用户名已存在"
        )

    # 验证邮箱格式（如果提供）
    if register_data.email:
        if not re.match(
            r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", register_data.email
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="邮箱格式不正确"
            )

        # 检查邮箱是否已存在
        email_check = text("SELECT id FROM users WHERE email = :email")
        existing_email = db.execute(
            email_check, {"email": register_data.email}
        ).fetchone()

        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="该邮箱已被注册"
            )

    # 创建用户
    password_hash = pwd_context.hash(register_data.password)

    # 外部用户直接激活，内部用户需要管理员审核
    is_active = 1 if register_data.user_type == "external" else 0

    try:
        insert_query = text("""
            INSERT INTO users (name, password_hash, department, role, is_active, balance_credit, 
                             user_type, phone, email, company, created_at)
            VALUES (:name, :password_hash, :department, 'user', :is_active, 0, 
                   :user_type, :phone, :email, :company, :created_at)
        """)

        db.execute(
            insert_query,
            {
                "name": register_data.name,
                "password_hash": password_hash,
                "department": register_data.department
                if register_data.user_type == "internal"
                else "",
                "is_active": is_active,
                "user_type": register_data.user_type,
                "phone": register_data.phone or None,
                "email": register_data.email or None,
                "company": register_data.company or None,
                "created_at": datetime.now().isoformat(),
            },
        )
        db.commit()

        # 获取新创建的用户ID
        user_query = text("SELECT id FROM users WHERE name = :name")
        new_user = db.execute(user_query, {"name": register_data.name}).fetchone()

        user_type_text = (
            "外部用户" if register_data.user_type == "external" else "内部用户"
        )
        message = (
            "注册成功"
            if register_data.user_type == "external"
            else "注册成功，请等待管理员审核激活"
        )

        # 记录注册成功日志
        db.execute(
            text("""
            INSERT INTO user_login_logs 
            (user_id, username, role, login_time, ip_address, user_agent,
             device_type, browser, os, login_method, status)
            VALUES 
            (:user_id, :username, 'user', :login_time, :ip_address, :user_agent,
             :device_type, :browser, :os, 'register', 'success')
        """),
            {
                "user_id": new_user.id,
                "username": register_data.name,
                "login_time": datetime.now().isoformat(),
                "ip_address": client_host,
                "user_agent": user_agent,
                "device_type": device_info["device_type"],
                "browser": device_info["browser"],
                "os": device_info["os"],
            },
        )
        db.commit()

        return {
            "message": message,
            "user_id": new_user.id,
            "username": register_data.name,
            "user_type": register_data.user_type,
            "status": "active" if is_active else "pending_activation",
        }

    except Exception as e:
        print(f"注册错误: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"注册失败: {str(e)}",
        )



@router.post("/login", response_model=TokenResponse)
def user_login(login_data: UserLogin, request: Request, db: Session = Depends(get_db)):
    """
    用户登录

    支持所有角色用户登录：
    - super_admin: 超级管理员
    - admin: 系统管理员
    - office_admin: 办公室管理员
    - user: 普通用户

    返回JWT令牌和用户信息
    """
    user_agent = request.headers.get("user-agent", "")
    client_host = request.client.host if request.client else "127.0.0.1"

    # 解析设备信息
    device_info = parse_user_agent(user_agent)

    login_status = "failure"
    failure_reason = None
    user_id = None
    username = None
    user_role = None

    try:
        # 查询用户
        query = text("""
            SELECT id, name, department, role, password_hash, is_active, balance_credit,
                   user_type, phone, email
            FROM users
            WHERE name = :name
        """)

        result = db.execute(query, {"name": login_data.name})
        user = result.fetchone()

        # 验证用户存在
        if not user:
            failure_reason = "用户不存在"
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="用户名或密码错误"
            )

        user_id = user.id
        username = user.name
        user_role = user.role

        # 验证用户状态
        if not user.is_active:
            failure_reason = "账户已停用"
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="该账户已被停用，请联系管理员",
            )

        # 验证密码
        if not verify_password(login_data.password, user.password_hash):
            failure_reason = "密码错误"
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="用户名或密码错误"
            )

        login_status = "success"

        # 创建JWT令牌
        access_token = create_access_token(
            data={
                "sub": str(user.id),
                "name": user.name,
                "role": user.role,
                "department": user.department or "",
            },
            expires_delta=timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS),
        )

        # 记录成功登录日志
        db.execute(
            text("""
            INSERT INTO user_login_logs 
            (user_id, username, role, login_time, ip_address, user_agent, 
             device_type, browser, os, login_method, status)
            VALUES 
            (:user_id, :username, :role, :login_time, :ip_address, :user_agent,
             :device_type, :browser, :os, :login_method, :status)
        """),
            {
                "user_id": user.id,
                "username": user.name,
                "role": user.role,
                "login_time": datetime.now().isoformat(),
                "ip_address": client_host,
                "user_agent": user_agent,
                "device_type": device_info["device_type"],
                "browser": device_info["browser"],
                "os": device_info["os"],
                "login_method": "password",
                "status": "success",
            },
        )
        db.commit()

        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=ACCESS_TOKEN_EXPIRE_HOURS * 3600,
            user_info={
                "user_id": user.id,
                "name": user.name,
                "username": user.name,
                "department": user.department,
                "role": user.role,
                "role_name": get_role_display_name(user.role, user.department),
                "is_active": user.is_active,
                "balance_credit": user.balance_credit or 0,
                "user_type": user.user_type or "internal",
                "phone": user.phone,
                "email": user.email,
            },
        )

    except HTTPException as e:
        # 记录失败登录日志
        if user_id or login_data.name:
            try:
                db.execute(
                    text("""
                    INSERT INTO user_login_logs 
                    (user_id, username, role, login_time, ip_address, user_agent,
                     device_type, browser, os, login_method, status, failure_reason)
                    VALUES 
                    (:user_id, :username, :role, :login_time, :ip_address, :user_agent,
                     :device_type, :browser, :os, :login_method, :status, :failure_reason)
                """),
                    {
                        "user_id": user_id or 0,
                        "username": username or login_data.name,
                        "role": user_role or "unknown",
                        "login_time": datetime.now().isoformat(),
                        "ip_address": client_host,
                        "user_agent": user_agent,
                        "device_type": device_info["device_type"],
                        "browser": device_info["browser"],
                        "os": device_info["os"],
                        "login_method": "password",
                        "status": "failure",
                        "failure_reason": failure_reason or "未知错误",
                    },
                )
                db.commit()
            except:
                pass
        raise
    except Exception as e:
        print(f"登录错误: {e}")
        # 记录系统错误日志
        try:
            db.execute(
                text("""
                INSERT INTO user_login_logs 
                (user_id, username, login_time, ip_address, user_agent,
                 device_type, browser, os, login_method, status, failure_reason)
                VALUES 
                (:user_id, :username, :login_time, :ip_address, :user_agent,
                 :device_type, :browser, :os, :login_method, :status, :failure_reason)
            """),
                {
                    "user_id": user_id or 0,
                    "username": username or login_data.name,
                    "login_time": datetime.now().isoformat(),
                    "ip_address": client_host,
                    "user_agent": user_agent,
                    "device_type": device_info["device_type"],
                    "browser": device_info["browser"],
                    "os": device_info["os"],
                    "login_method": "password",
                    "status": "failure",
                    "failure_reason": f"系统错误: {str(e)}",
                },
            )
            db.commit()
        except:
            pass

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"登录失败: {str(e)}",
        )


@router.get("/me")
def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    """获取当前登录用户信息"""
    if not credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="未登录")

    token = credentials.credentials
    payload = verify_token(token)

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="登录已过期，请重新登录"
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="无效的令牌"
        )

    # 查询用户信息
    query = text("""
        SELECT id, name, department, role, is_active, balance_credit
        FROM users
        WHERE id = :id
    """)

    result = db.execute(query, {"id": int(user_id)})
    user = result.fetchone()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="用户不存在"
        )

    return {
        "id": user.id,
        "name": user.name,
        "department": user.department,
        "role": user.role,
        "role_name": get_role_display_name(user.role, user.department),
        "is_active": user.is_active,
        "balance_credit": user.balance_credit or 0,
    }


@router.post("/logout")
def user_logout(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    """用户登出"""
    # JWT是无状态的，登出只需客户端删除token
    # 这里可以添加token黑名单逻辑
    return {"message": "登出成功"}


@router.post("/change-password")
def change_password(
    request_data: ChangePasswordRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    """
    修改密码

    - old_password: 原密码
    - new_password: 新密码（至少6位）
    """
    if not credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="未登录")

    token = credentials.credentials
    payload = verify_token(token)

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="登录已过期"
        )

    user_id = payload.get("sub")

    # 验证新密码强度
    if len(request_data.new_password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="新密码长度至少为6位"
        )

    # 查询用户
    query = text("""
        SELECT id, name, password_hash FROM users WHERE id = :id
    """)
    result = db.execute(query, {"id": int(user_id)})
    user = result.fetchone()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")

    # 验证旧密码
    if not verify_password(request_data.old_password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="原密码错误"
        )

    # 新密码不能与旧密码相同
    if verify_password(request_data.new_password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="新密码不能与原密码相同"
        )

    # 更新密码
    new_hash = pwd_context.hash(request_data.new_password)
    db.execute(
        text("""
        UPDATE users SET password_hash = :hash, updated_at = :now WHERE id = :id
    """),
        {"hash": new_hash, "now": datetime.now().isoformat(), "id": int(user_id)},
    )
    db.commit()

    # 记录密码修改日志
    try:
        db.execute(
            text("""
            INSERT INTO user_login_logs 
            (user_id, username, login_time, ip_address, login_method, status, failure_reason)
            VALUES 
            (:user_id, :username, :login_time, '127.0.0.1', 'password_change', 'success', '密码修改成功')
        """),
            {
                "user_id": user.id,
                "username": user.name,
                "login_time": datetime.now().isoformat(),
            },
        )
        db.commit()
    except:
        pass

    return {"message": "密码修改成功", "user_id": user.id, "username": user.name}


# ==================== 兼容性路由 ====================


# 为管理后台提供兼容的登录接口
@router.post("/admin/login", response_model=TokenResponse)
def admin_login_compatibility(
    login_data: UserLogin, request: Request, db: Session = Depends(get_db)
):
    """
    管理后台登录（兼容接口）

    与 /api/user/login 功能相同，用于兼容现有前端
    """
    return user_login(login_data, request, db)
