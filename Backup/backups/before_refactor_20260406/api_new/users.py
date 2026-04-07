"""
用户相关API
使用UserService处理业务逻辑
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from config.database import get_db
from services import UserService
from api_new import require_admin, require_user, get_current_user

router = APIRouter(prefix="/v2/users", tags=["Users (New Architecture)"])


class UserCreate(BaseModel):
    name: str
    department: str
    role: str = "staff"
    password: Optional[str] = None


class UserUpdate(BaseModel):
    name: Optional[str] = None
    department: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[int] = None


class UserResponse(BaseModel):
    id: int
    name: str
    department: str
    role: str
    balance_credit: float
    is_active: int
    created_at: datetime

    class Config:
        from_attributes = True


@router.get("", response_model=List[UserResponse])
async def list_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    """
    获取用户列表
    """
    user_service = UserService(db)
    users = user_service.get_users(skip, limit)
    return users


@router.get("/search", response_model=List[UserResponse])
async def search_users(
    keyword: str,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    """
    搜索用户
    """
    user_service = UserService(db)
    users = user_service.search_users(keyword)
    return users


@router.get("/department/{department}", response_model=List[UserResponse])
async def get_users_by_department(
    department: str,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    """
    根据部门获取用户
    """
    user_service = UserService(db)
    users = user_service.get_users_by_department(department)
    return users


@router.get("/role/{role}", response_model=List[UserResponse])
async def get_users_by_role(
    role: str,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    """
    根据角色获取用户
    """
    user_service = UserService(db)
    users = user_service.get_users_by_role(role)
    return users


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    获取单个用户信息
    """
    if current_user.role != "admin" and current_user.id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权限访问")

    user_service = UserService(db)
    user = user_service.get_user(user_id)

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")

    return user


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    """
    创建用户
    """
    user_service = UserService(db)

    try:
        user = user_service.create_user(
            name=user_data.name,
            department=user_data.department,
            role=user_data.role,
            password=user_data.password,
        )
        return user
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    """
    更新用户信息
    """
    user_service = UserService(db)

    update_dict = user_data.model_dump(exclude_unset=True)

    try:
        user = user_service.update_user(user_id, update_dict)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在"
            )
        return user
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    """
    删除用户
    """
    user_service = UserService(db)

    success = user_service.delete_user(user_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")


@router.post("/{user_id}/deactivate", response_model=UserResponse)
async def deactivate_user(
    user_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    """
    停用用户
    """
    user_service = UserService(db)

    success = user_service.deactivate_user(user_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")

    return user_service.get_user(user_id)


@router.post("/{user_id}/activate", response_model=UserResponse)
async def activate_user(
    user_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    """
    激活用户
    """
    user_service = UserService(db)

    success = user_service.activate_user(user_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")

    return user_service.get_user(user_id)


@router.post("/{user_id}/reset-password")
async def reset_password(
    user_id: int,
    new_password: str,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    """
    重置用户密码
    """
    user_service = UserService(db)

    success = user_service.reset_password(user_id, new_password)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")

    return {"message": "密码已重置"}
