"""
统一认证依赖函数 - 符合OAuth 2.0和JWT最佳实践
消除代码重复，统一认证逻辑
"""

from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from config.database import get_db
from models.user import User
from utils.jwt import verify_token
from utils.token_blacklist import is_token_revoked


security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db),
) -> Optional[User]:
    """
    获取当前登录用户（可选）

    Security Checks:
    - Token格式验证
    - Token签名验证
    - Token黑名单检查
    - 用户状态验证

    Returns:
        User对象或None
    """
    if not credentials:
        return None

    token = credentials.credentials

    if is_token_revoked(token, db):
        return None

    payload = verify_token(token)

    if not payload:
        return None

    user_id = payload.get("user_id") or payload.get("sub")
    if not user_id:
        return None

    try:
        user_id_int = int(user_id)
    except (ValueError, TypeError):
        return None

    user = db.query(User).filter(User.id == user_id_int).first()

    if user and not user.is_active:
        return None

    return user


async def get_current_user_required(
    current_user: Optional[User] = Depends(get_current_user),
) -> User:
    """
    获取当前登录用户（必需）

    Raises:
        HTTPException: 未登录或登录已过期

    Returns:
        User对象
    """
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未登录或登录已过期，请重新登录",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="用户已被禁用，请联系管理员"
        )

    return current_user


async def get_admin_user(
    current_user: User = Depends(get_current_user_required),
) -> User:
    """
    获取管理员用户

    Role hierarchy:
    - super_admin: 最高权限，可以管理所有系统
    - admin: 系统管理员，可以管理大部分功能
    - office_admin: 办公室管理员，管理特定办公室

    Raises:
        HTTPException: 权限不足

    Returns:
        User对象
    """
    if current_user.role not in ["admin", "super_admin", "office_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="权限不足，需要管理员权限"
        )

    return current_user


async def get_super_admin_user(
    current_user: User = Depends(get_current_user_required),
) -> User:
    """
    获取超级管理员用户

    Raises:
        HTTPException: 权限不足

    Returns:
        User对象

    Security:
    - 仅super_admin角色可访问
    - 用于最敏感的操作：删除用户、系统配置等
    """
    if current_user.role != "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="权限不足，需要超级管理员权限"
        )

    return current_user


async def get_office_admin_user(
    current_user: User = Depends(get_current_user_required),
    db: Session = Depends(get_db),
) -> User:
    """
    获取办公室管理员用户

    Raises:
        HTTPException: 权限不足

    Returns:
        User对象

    Security:
    - office_admin仅能管理自己所属办公室的资源
    """
    if current_user.role not in ["office_admin", "admin", "super_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足，需要办公室管理员权限",
        )

    return current_user


async def check_resource_permission(
    resource_user_id: int,
    current_user: User = Depends(get_current_user_required),
) -> User:
    """
    检查资源访问权限

    Args:
        resource_user_id: 资源所属用户ID
        current_user: 当前用户

    Returns:
        User对象

    Security:
    - 用户只能访问自己的资源
    - 管理员可以访问所有资源
    """
    if current_user.role in ["admin", "super_admin"]:
        return current_user

    if current_user.id != resource_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="无权限访问此资源"
        )

    return current_user


async def check_office_permission(
    office_name: str,
    current_user: User = Depends(get_current_user_required),
) -> User:
    """
    检查办公室权限

    Args:
        office_name: 办公室名称
        current_user: 当前用户

    Returns:
        User对象

    Security:
    - office_admin只能管理自己所属办公室
    - admin和super_admin可以管理所有办公室
    """
    if current_user.role in ["admin", "super_admin"]:
        return current_user

    if current_user.role == "office_admin":
        if current_user.department != office_name:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"无权限管理办公室: {office_name}",
            )

    return current_user


get_admactiver = get_admin_user
get_super_admactiver = get_super_admin_user
