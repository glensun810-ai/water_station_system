"""
认证相关API
使用UserService处理认证逻辑
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime, timedelta

from config.database import get_db
from config.settings import settings
from services import UserService
from models import User

router = APIRouter(prefix="/v2/auth", tags=["Auth (New Architecture)"])


class LoginRequest(BaseModel):
    name: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user_id: int
    user_name: str
    role: str


class PasswordChangeRequest(BaseModel):
    old_password: str
    new_password: str


@router.post("/login", response_model=TokenResponse)
async def login(
    login_data: LoginRequest,
    db: Session = Depends(get_db),
):
    """
    用户登录
    """
    user_service = UserService(db)

    user = user_service.authenticate(login_data.name, login_data.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="用户名或密码错误"
        )

    from jose import jwt

    expire = datetime.utcnow() + timedelta(hours=settings.ACCESS_TOKEN_EXPIRE_HOURS)

    payload = {
        "sub": str(user.id),
        "name": user.name,
        "role": user.role,
        "exp": expire,
    }

    access_token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_HOURS * 3600,
        "user_id": user.id,
        "user_name": user.name,
        "role": user.role,
    }


@router.post("/change-password")
async def change_password(
    password_data: PasswordChangeRequest,
    current_user: User = Depends(get_db),
    db: Session = Depends(get_db),
):
    """
    修改密码
    """
    from api_new import require_user

    user = await require_user(current_user)

    user_service = UserService(db)

    try:
        success = user_service.update_password(
            user.id,
            password_data.old_password,
            password_data.new_password,
        )
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="密码修改失败"
            )
        return {"message": "密码已修改"}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
