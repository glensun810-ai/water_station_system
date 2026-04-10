"""
系统服务API路由
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from config.database import get_db
from models.user import User
from models.office import Office
from depends.auth import get_current_user, get_admin_user
from schemas.system import (
    UserResponse,
    OfficeResponse,
    AuthResponse,
)

router = APIRouter(prefix="/system", tags=["系统服务"])


@router.get("/users", response_model=List[UserResponse])
def get_users(
    role: Optional[str] = Query(None, description="用户角色过滤"),
    department_id: Optional[int] = Query(None, description="部门ID过滤"),
    is_active: Optional[bool] = Query(None, description="激活状态过滤"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),  # 只有管理员可以访问
):
    """获取用户列表（仅管理员）"""

    query = db.query(User)

    if role:
        query = query.filter(User.role == role)

    if department_id:
        query = query.filter(User.department_id == department_id)

    if is_active is not None:
        query = query.filter(User.is_active == is_active)

    users = query.all()
    return users


@router.get("/offices", response_model=List[OfficeResponse])
def get_offices(
    is_active: Optional[bool] = Query(True, description="是否只返回激活的办公室"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取办公室列表"""

    query = db.query(Office)

    if is_active is not None:
        query = query.filter(Office.is_active == is_active)

    offices = query.order_by(Office.name).all()
    return offices


@router.post("/auth/login", response_model=AuthResponse)
def login(login_data: dict, db: Session = Depends(get_db)):
    """用户登录"""

    username = login_data.get("username")
    password = login_data.get("password")

    if not username or not password:
        raise HTTPException(status_code=400, detail="用户名和密码不能为空")

    user = db.query(User).filter(User.username == username).first()

    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    # 这里应该验证密码哈希，简化处理
    # 在实际应用中应该使用 bcrypt.verify(password, user.password_hash)
    if password != "123456":  # 简化密码验证
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    # 生成token（简化处理）
    import jwt
    from datetime import datetime, timedelta

    token_data = {
        "user_id": user.id,
        "username": user.username,
        "role": user.role,
        "exp": datetime.utcnow() + timedelta(hours=24),
    }

    token = jwt.encode(token_data, "secret_key", algorithm="HS256")

    return {
        "access_token": token,
        "token_type": "bearer",
        "user_info": {
            "user_id": user.id,
            "username": user.username,
            "role": user.role,
            "role_name": user.role_name,
            "department": user.department,
            "avatar": "👤",
        },
    }


@router.post("/auth/logout")
def logout(current_user: User = Depends(get_current_user)):
    """用户登出"""
    # 实际应用中应该在服务端维护token黑名单
    return {"message": "登出成功"}
