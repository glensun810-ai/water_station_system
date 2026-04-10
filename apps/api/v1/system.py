"""
系统服务API路由 - v1版本
统一的API端点 following API design specification
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from config.database import get_db
from config.settings import settings
from models.user import User
from models.office import Office
from depends.auth import get_current_user, get_admin_user, get_super_admin_user
from schemas.system import (
    UserResponse,
    OfficeResponse,
    AuthResponse,
)

router = APIRouter(prefix="/system", tags=["系统服务"])


@router.get("/users", response_model=dict)
def get_users(
    page: int = Query(1, description="页码"),
    limit: int = Query(20, description="每页数量"),
    role: Optional[str] = Query(None, description="用户角色过滤"),
    department: Optional[str] = Query(None, description="部门过滤"),
    is_active: Optional[bool] = Query(None, description="激活状态过滤"),
    q: Optional[str] = Query(None, description="全局搜索关键词"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),  # 只有管理员可以访问
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

    # 防止普通管理员修改超级管理员
    if user.role == "super_admin" and current_user.role != "super_admin":
        raise HTTPException(status_code=403, detail="无权限修改超级管理员")

    update_data = {
        k: v for k, v in user_update.items() if hasattr(User, k) and k not in ["id"]
    }

    for key, value in update_data.items():
        setattr(user, key, value)

    db.commit()
    db.refresh(user)

    return {"message": "用户信息更新成功", "user_id": user_id}


@router.delete("/users/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_super_admin_user),  # 仅超级管理员可删除用户
):
    """删除用户（仅超级管理员）"""

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    # 禁止删除自己
    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="不能删除自己的账户")

    # 禁止删除其他超级管理员
    if user.role == "super_admin":
        raise HTTPException(status_code=403, detail="不能删除超级管理员账户")

    user.is_active = False
    db.commit()

    return {"message": "用户已停用", "user_id": user_id}


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

    token = jwt.encode(token_data, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

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
