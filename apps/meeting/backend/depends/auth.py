"""
会议室认证依赖函数
用于FastAPI的依赖注入
"""

from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from config.database import get_db
from models.user import User
from utils.jwt import verify_token

security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db),
) -> Optional[User]:
    """获取当前登录用户（可选）"""
    if not credentials:
        return None

    token = credentials.credentials
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
    return user


async def get_current_user_required(
    current_user: Optional[User] = Depends(get_current_user),
) -> User:
    """获取当前登录用户（必需）"""
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未登录或登录已过期",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="用户已被禁用"
        )

    return current_user


async def get_admin_user(
    current_user: User = Depends(get_current_user_required),
) -> User:
    """获取管理员用户"""
    if current_user.role not in ["admin", "super_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="权限不足，需要管理员权限"
        )
    return current_user


async def get_super_admin_user(
    current_user: User = Depends(get_current_user_required),
) -> User:
    """获取超级管理员用户"""
    if current_user.role != "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="权限不足，需要超级管理员权限"
        )
    return current_user
