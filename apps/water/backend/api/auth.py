"""
认证API路由（模块化版本）
处理登录、登出、密码修改等
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from datetime import timedelta
from typing import Optional

from config.database import get_db
from config.settings import settings
from models.user import User
from schemas.user import UserLogin, TokenResponse, UserResponse, PasswordChange
from utils.password import hash_password, verify_password
from utils.jwt import create_access_token, verify_token

router = APIRouter(prefix="/api/auth", tags=["认证"])
security = HTTPBearer(auto_error=False)


@router.post("/login", response_model=TokenResponse)
def login(login_data: UserLogin, db: Session = Depends(get_db)):
    """
    用户登录

    Returns:
        TokenResponse: 包含access_token和用户信息
    """
    # 查找用户
    user = db.query(User).filter(User.name == login_data.name).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="用户名或密码错误"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="用户已被禁用"
        )

    # 如果没有密码，使用默认密码 admin123 验证（兼容旧数据）
    if not user.password_hash:
        if login_data.password != "admin123":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="用户名或密码错误"
            )
    else:
        # 验证密码
        if not verify_password(login_data.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="用户名或密码错误"
            )

    # 创建Token
    access_token = create_access_token(
        data={"sub": str(user.id), "role": user.role},
        expires_delta=timedelta(hours=settings.ACCESS_TOKEN_EXPIRE_HOURS),
    )

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.model_validate(user),
    )


@router.get("/me", response_model=UserResponse)
def get_current_user_info(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    """
    获取当前登录用户信息
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
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="无效的令牌"
        )

    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="用户不存在"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="用户已被禁用"
        )

    return UserResponse.model_validate(user)


@router.post("/logout")
def logout():
    """用户登出"""
    return {"message": "登出成功"}


@router.post("/change-password")
def change_password(
    password_change: PasswordChange,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db),
):
    """
    修改密码
    """
    import logging

    logger = logging.getLogger(__name__)

    # 验证token获取用户
    if not credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="未登录")

    token = credentials.credentials
    payload = verify_token(token)

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="登录已过期"
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="无效的令牌"
        )

    # 从数据库查询用户
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="用户不存在或已禁用"
        )

    logger.info(f"Changing password for user: {user.name}")

    # 验证旧密码
    if user.password_hash:
        if not verify_password(password_change.old_password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="旧密码错误"
            )
    else:
        # 兼容旧数据（无密码）
        if password_change.old_password != "admin123":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="旧密码错误"
            )

    # 验证新密码
    if len(password_change.new_password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="新密码长度至少6位"
        )

    # 更新密码
    user.password_hash = hash_password(password_change.new_password)
    db.commit()

    logger.info(f"Password changed successfully for user: {user.name}")

    return {"message": "密码修改成功"}
