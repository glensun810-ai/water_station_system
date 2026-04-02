"""
认证API路由
处理登录、登出、密码修改等
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from datetime import timedelta
from typing import Optional

from config.database import get_db
from config.settings import settings

router = APIRouter(prefix="/api/auth", tags=["认证"])
security = HTTPBearer(auto_error=False)


# Pydantic模型
from pydantic import BaseModel


class UserLogin(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


class PasswordChange(BaseModel):
    old_password: str
    new_password: str


@router.post("/login", response_model=TokenResponse)
async def login(login_data: UserLogin, db: Session = Depends(get_db)):
    """
    用户登录
    """
    from main import User, verify_password, create_access_token

    user = db.query(User).filter(User.name == login_data.username).first()

    if not user:
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="用户已被禁用")

    if not user.password_hash:
        if login_data.password != "admin123":
            raise HTTPException(status_code=401, detail="用户名或密码错误")
    else:
        if not verify_password(login_data.password, user.password_hash):
            raise HTTPException(status_code=401, detail="用户名或密码错误")

    access_token = create_access_token(
        data={"sub": str(user.id), "role": user.role},
        expires_delta=timedelta(hours=settings.ACCESS_TOKEN_EXPIRE_HOURS),
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "name": user.name,
            "department": user.department,
            "role": user.role,
        },
    }


@router.post("/logout")
async def logout():
    """用户登出"""
    return {"message": "登出成功"}


@router.post("/change-password")
async def change_password(
    password_change: PasswordChange,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db),
):
    """修改密码"""
    from main import User, verify_password, hash_password

    if not credentials:
        raise HTTPException(status_code=401, detail="未登录")

    token = credentials.credentials
    from main import verify_token

    payload = verify_token(token)

    if not payload:
        raise HTTPException(status_code=401, detail="登录已过期")

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="无效的令牌")

    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="用户不存在或已禁用")

    if not user.password_hash:
        if password_change.old_password != "admin123":
            raise HTTPException(status_code=400, detail="原密码错误")
    else:
        if not verify_password(password_change.old_password, user.password_hash):
            raise HTTPException(status_code=400, detail="原密码错误")

    new_hash = hash_password(password_change.new_password)
    user.password_hash = new_hash
    db.commit()

    return {"message": "密码修改成功"}
