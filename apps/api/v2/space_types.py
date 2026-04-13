"""
空间类型管理API路由
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List

from config.database import get_db
from models.user import User
from depends.auth import get_admin_user, get_super_admin_user
from shared.models.space.space_type import SpaceType
from shared.schemas.space.space_type import (
    SpaceTypeCreate,
    SpaceTypeUpdate,
    SpaceTypeResponse,
)
from shared.schemas.space.response import ApiResponse, PaginatedResponse

router = APIRouter(prefix="/space/types", tags=["空间类型管理"])


@router.get("", response_model=ApiResponse)
async def get_space_types(
    is_active: Optional[bool] = Query(None, description="激活状态过滤"),
    page: int = Query(1, ge=1, description="页码"),
    limit: int = Query(20, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db),
):
    """获取空间类型列表"""

    query = db.query(SpaceType)

    if is_active is not None:
        query = query.filter(SpaceType.is_active == is_active)

    total = query.count()
    types = (
        query.order_by(SpaceType.sort_order)
        .offset((page - 1) * limit)
        .limit(limit)
        .all()
    )

    items = []
    for t in types:
        items.append(
            {
                "id": t.id,
                "type_code": t.type_code,
                "type_name": t.type_name,
                "type_name_en": t.type_name_en,
                "description": t.description,
                "min_duration_unit": t.min_duration_unit,
                "min_duration_value": t.min_duration_value,
                "max_duration_value": t.max_duration_value,
                "advance_booking_days": t.advance_booking_days,
                "min_capacity": t.min_capacity,
                "max_capacity": t.max_capacity,
                "requires_approval": t.requires_approval,
                "approval_type": t.approval_type,
                "requires_deposit": t.requires_deposit,
                "deposit_percentage": t.deposit_percentage,
                "standard_facilities": t.standard_facilities,
                "optional_addons": t.optional_addons,
                "is_active": t.is_active,
                "icon": t.icon,
                "color_theme": t.color_theme,
            }
        )

    return ApiResponse(
        data=PaginatedResponse(
            items=items,
            total=total,
            page=page,
            limit=limit,
            pages=(total + limit - 1) // limit,
        )
    )


@router.get("/{type_id}", response_model=ApiResponse)
async def get_space_type(
    type_id: int,
    db: Session = Depends(get_db),
):
    """获取空间类型详情"""

    space_type = db.query(SpaceType).filter(SpaceType.id == type_id).first()

    if not space_type:
        raise HTTPException(status_code=404, detail="空间类型不存在")

    return ApiResponse(data=SpaceTypeResponse.model_validate(space_type))


@router.post("", response_model=ApiResponse)
async def create_space_type(
    type_data: SpaceTypeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_super_admin_user),
):
    """创建空间类型（仅超级管理员）"""

    existing = (
        db.query(SpaceType).filter(SpaceType.type_code == type_data.type_code).first()
    )
    if existing:
        raise HTTPException(status_code=409, detail="空间类型代码已存在")

    space_type = SpaceType(**type_data.model_dump())
    db.add(space_type)
    db.commit()
    db.refresh(space_type)

    return ApiResponse(
        code=201,
        message="空间类型创建成功",
        data=SpaceTypeResponse.model_validate(space_type),
    )


@router.put("/{type_id}", response_model=ApiResponse)
async def update_space_type(
    type_id: int,
    type_data: SpaceTypeUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_super_admin_user),
):
    """更新空间类型（仅超级管理员）"""

    space_type = db.query(SpaceType).filter(SpaceType.id == type_id).first()

    if not space_type:
        raise HTTPException(status_code=404, detail="空间类型不存在")

    update_data = type_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        if hasattr(space_type, key):
            setattr(space_type, key, value)

    db.commit()
    db.refresh(space_type)

    return ApiResponse(
        message="空间类型更新成功", data=SpaceTypeResponse.model_validate(space_type)
    )


@router.delete("/{type_id}", response_model=ApiResponse)
async def delete_space_type(
    type_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_super_admin_user),
):
    """删除空间类型（仅超级管理员）"""

    space_type = db.query(SpaceType).filter(SpaceType.id == type_id).first()

    if not space_type:
        raise HTTPException(status_code=404, detail="空间类型不存在")

    db.delete(space_type)
    db.commit()

    return ApiResponse(message="空间类型已删除")
