"""
新架构API模块
使用分层架构: API -> Service -> Repository -> Model
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional

from config.database import get_db
from services import UserService, ProductService, TransactionService
from models import User

security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> Optional[User]:
    """
    获取当前认证用户
    """
    if not credentials:
        return None

    token = credentials.credentials
    user_service = UserService(db)

    try:
        from jose import jwt
        from config.settings import settings

        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        user_id = payload.get("sub")

        if not user_id:
            return None

        user = user_service.get_user(int(user_id))
        if not user or not user.is_active:
            return None

        return user
    except Exception:
        return None


async def require_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    要求管理员权限
    """
    if not current_user or current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="需要管理员权限"
        )
    return current_user


async def require_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    要求已认证用户
    """
    if not current_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="未认证")
    return current_user
