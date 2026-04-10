"""
用户管理API - 核心域
提供用户管理的REST API接口
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from config.database import get_db
from depends.auth import get_current_user, get_admin_user
from models.user import User
from schemas.user import (
    UserCreate,
    UserUpdate,
    UserResponse,
    PasswordChange,
)
from .service import UserService

router = APIRouter(prefix="/api/v2/users", tags=["用户管理 - 核心域"])


def get_user_service(db: Session = Depends(get_db)) -> UserService:
    """获取用户服务实例"""
    return UserService(db)


@router.get("", response_model=List[UserResponse])
async def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    department: str = Query(None, description="按部门筛选"),
    role: str = Query(None, description="按角色筛选"),
    is_active: int = Query(None, description="按状态筛选"),
    keyword: str = Query(None, description="搜索关键词"),
    service: UserService = Depends(get_user_service),
    current_user: User = Depends(get_current_user),
):
    """
    获取用户列表

    - 支持分页
    - 支持按部门、角色、状态筛选
    - 支持关键词搜索
    """
    if keyword:
        return service.search_users(keyword, skip, limit)

    if department:
        return service.get_by_department(department, skip, limit)

    if role:
        return service.get_by_role(role, skip, limit)

    if is_active is not None:
        if is_active == 1:
            return service.get_active_users(skip, limit)

    return service.get_multi(skip, limit)


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    service: UserService = Depends(get_user_service),
    current_user: User = Depends(get_current_user),
):
    """获取单个用户详情"""
    user = service.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    return user


@router.post("", response_model=UserResponse, status_code=201)
async def create_user(
    user_data: UserCreate,
    service: UserService = Depends(get_user_service),
    current_user: User = Depends(get_admin_user),
):
    """
    创建用户（仅管理员）

    - 用户名唯一
    - 可设置初始密码和余额
    """
    try:
        user = service.create_user(
            name=user_data.name,
            department=user_data.department,
            role=user_data.role,
            password=user_data.password,
            balance_credit=user_data.balance_credit,
        )
        return user
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    service: UserService = Depends(get_user_service),
    current_user: User = Depends(get_admin_user),
):
    """
    更新用户信息（仅管理员）

    - 可更新用户名、部门、角色、余额、状态
    """
    update_dict = user_data.model_dump(exclude_unset=True)
    if not update_dict:
        raise HTTPException(status_code=400, detail="没有需要更新的字段")

    try:
        user = service.update_user(user_id, update_dict)
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")
        return user
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{user_id}")
async def delete_user(
    user_id: int,
    service: UserService = Depends(get_user_service),
    current_user: User = Depends(get_admin_user),
):
    """删除用户（仅管理员）"""
    user = service.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    if service.delete(user_id):
        return {"message": "用户删除成功"}
    raise HTTPException(status_code=500, detail="用户删除失败")


@router.post("/{user_id}/activate")
async def activate_user(
    user_id: int,
    service: UserService = Depends(get_user_service),
    current_user: User = Depends(get_admin_user),
):
    """激活用户（仅管理员）"""
    if service.activate_user(user_id):
        return {"message": "用户激活成功"}
    raise HTTPException(status_code=404, detail="用户不存在")


@router.post("/{user_id}/deactivate")
async def deactivate_user(
    user_id: int,
    service: UserService = Depends(get_user_service),
    current_user: User = Depends(get_admin_user),
):
    """停用用户（仅管理员）"""
    if service.deactivate_user(user_id):
        return {"message": "用户停用成功"}
    raise HTTPException(status_code=404, detail="用户不存在")


@router.post("/{user_id}/reset-password")
async def reset_user_password(
    user_id: int,
    new_password: str = Query(..., min_length=6, description="新密码"),
    service: UserService = Depends(get_user_service),
    current_user: User = Depends(get_admin_user),
):
    """重置用户密码（仅管理员）"""
    if service.reset_password(user_id, new_password):
        return {"message": "密码重置成功"}
    raise HTTPException(status_code=404, detail="用户不存在")


@router.post("/{user_id}/change-password")
async def change_user_password(
    user_id: int,
    password_data: PasswordChange,
    service: UserService = Depends(get_user_service),
    current_user: User = Depends(get_current_user),
):
    """修改用户密码"""
    if current_user.id != user_id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="无权修改他人密码")

    try:
        if service.update_password(
            user_id, password_data.old_password, password_data.new_password
        ):
            return {"message": "密码修改成功"}
        raise HTTPException(status_code=404, detail="用户不存在")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{user_id}/balance")
async def update_user_balance(
    user_id: int,
    amount: float = Query(..., description="变动金额（可正可负）"),
    service: UserService = Depends(get_user_service),
    current_user: User = Depends(get_admin_user),
):
    """更新用户余额（仅管理员）"""
    try:
        if service.update_balance(user_id, amount):
            user = service.get(user_id)
            return {
                "message": "余额更新成功",
                "new_balance": user.balance_credit,
            }
        raise HTTPException(status_code=404, detail="用户不存在")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
