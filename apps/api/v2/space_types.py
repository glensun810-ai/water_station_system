"""
空间类型管理API路由
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List

from sqlalchemy import func
from config.database import get_db
from models.user import User
from depends.auth import get_admin_user, get_super_admin_user  # noqa: F811
from shared.models.space.space_type import SpaceType
from shared.models.space.space_resource import SpaceResource
from shared.models.space.space_booking import SpaceBooking
from shared.schemas.space.space_type import (
    SpaceTypeCreate,
    SpaceTypeUpdate,
    SpaceTypeResponse,
)
from shared.schemas.space.response import ApiResponse, PaginatedResponse
from pydantic import BaseModel, field_validator

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
        price_from = db.query(func.min(SpaceResource.base_price)).filter(
            SpaceResource.type_id == t.id,
            SpaceResource.is_active == True,
            SpaceResource.base_price > 0,
        ).scalar()

        price_unit = db.query(SpaceResource.price_unit).filter(
            SpaceResource.type_id == t.id,
            SpaceResource.is_active == True,
        ).order_by(SpaceResource.base_price.asc()).limit(1).scalar()

        items.append(
            {
                "id": t.id,
                "type_code": t.type_code,
                "type_name": t.type_name,
                "type_name_en": t.type_name_en,
                "description": t.description,
                "auto_approval_max_amount": t.auto_approval_max_amount or 0,
                "free_quota_applicable_units": t.free_quota_applicable_units,
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
                "price_from": float(price_from) if price_from else None,
                "price_unit": price_unit or t.min_duration_unit,
                "supported_duration_units": t.supported_duration_units,
                "time_slot_preset": t.time_slot_preset,
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
    current_user: User = Depends(get_admin_user),
):
    """创建空间类型（仅管理员）"""

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
    current_user: User = Depends(get_admin_user),
):
    """更新空间类型（仅管理员）"""

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


@router.get("/{type_id}/stats", response_model=ApiResponse)
async def get_type_stats(
    type_id: int,
    db: Session = Depends(get_db),
):
    """获取类型的关联数据统计（用于删除前确认）"""

    space_type = db.query(SpaceType).filter(SpaceType.id == type_id).first()
    if not space_type:
        raise HTTPException(status_code=404, detail="空间类型不存在")

    resource_count = db.query(SpaceResource).filter(
        SpaceResource.type_id == type_id
    ).count()

    resource_ids = db.query(SpaceResource.id).filter(
        SpaceResource.type_id == type_id
    ).subquery()

    booking_count = db.query(SpaceBooking).filter(
        SpaceBooking.resource_id.in_(resource_ids)
    ).count()

    return ApiResponse(data={
        "type_id": type_id,
        "type_code": space_type.type_code,
        "type_name": space_type.type_name,
        "resource_count": resource_count,
        "booking_count": booking_count,
        "can_delete": resource_count == 0,
    })


@router.delete("/{type_id}", response_model=ApiResponse)
async def delete_space_type(
    type_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_super_admin_user),
):
    """删除空间类型（仅超级管理员，且类型下必须无资源）"""

    space_type = db.query(SpaceType).filter(SpaceType.id == type_id).first()

    if not space_type:
        raise HTTPException(status_code=404, detail="空间类型不存在")

    resource_count = db.query(SpaceResource).filter(
        SpaceResource.type_id == type_id
    ).count()

    if resource_count > 0:
        raise HTTPException(
            status_code=409,
            detail=f"该类型下存在 {resource_count} 个资源，无法删除。请先将资源迁移到其他类型，或停用此类型。"
        )

    db.delete(space_type)
    db.commit()

    return ApiResponse(message=f"空间类型「{space_type.type_name}」已删除")


class MigrateResourcesRequest(BaseModel):
    to_type_id: int

    @field_validator("to_type_id")
    def must_be_positive(cls, v):
        if v <= 0:
            raise ValueError("目标类型ID必须大于0")
        return v


@router.post("/{type_id}/migrate-resources", response_model=ApiResponse)
async def migrate_type_resources(
    type_id: int,
    migrate_data: MigrateResourcesRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_super_admin_user),
):
    """将某类型下的所有资源迁移到另一个类型（仅超级管理员）"""

    if migrate_data.to_type_id == type_id:
        raise HTTPException(status_code=400, detail="源类型和目标类型不能相同")

    from_type = db.query(SpaceType).filter(SpaceType.id == type_id).first()
    if not from_type:
        raise HTTPException(status_code=404, detail="源类型不存在")

    to_type = db.query(SpaceType).filter(SpaceType.id == migrate_data.to_type_id).first()
    if not to_type:
        raise HTTPException(status_code=404, detail="目标类型不存在")

    # 检查预订单位兼容性
    from_unit = from_type.min_duration_unit
    to_unit = to_type.min_duration_unit
    compatible_groups = [
        {"hour"},
        {"half_day", "session", "slot"},
        {"day", "week", "month"},
        {"meal"},
    ]
    from_group = next((g for g in compatible_groups if from_unit in g), None)
    to_group = next((g for g in compatible_groups if to_unit in g), None)

    if from_group != to_group:
        raise HTTPException(
            status_code=400,
            detail=f"预订单位不兼容：{from_unit} 无法迁移到 {to_unit}。仅支持同类型单位之间的迁移（如 day→week、half_day→session）。"
        )

    resources = db.query(SpaceResource).filter(
        SpaceResource.type_id == type_id
    ).all()

    if not resources:
        raise HTTPException(status_code=404, detail="该类型下没有可迁移的资源")

    migrated_names = []
    for resource in resources:
        migrated_names.append(resource.name)
        resource.type_id = migrate_data.to_type_id

    db.commit()

    return ApiResponse(
        message=f"已将 {len(resources)} 个资源从「{from_type.type_name}」迁移至「{to_type.type_name}」",
        data={
            "migrated_count": len(resources),
            "from_type_id": type_id,
            "from_type_name": from_type.type_name,
            "to_type_id": migrate_data.to_type_id,
            "to_type_name": to_type.type_name,
            "resource_names": migrated_names,
        }
    )


@router.put("/{type_id}/toggle-active", response_model=ApiResponse)
async def toggle_type_active(
    type_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    """切换类型的启用/停用状态（管理员）"""

    space_type = db.query(SpaceType).filter(SpaceType.id == type_id).first()
    if not space_type:
        raise HTTPException(status_code=404, detail="空间类型不存在")

    space_type.is_active = not space_type.is_active
    db.commit()

    action = "启用" if space_type.is_active else "停用"
    return ApiResponse(
        message=f"空间类型「{space_type.type_name}」已{action}",
        data={"is_active": space_type.is_active}
    )
