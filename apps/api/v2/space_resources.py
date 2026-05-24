"""
空间资源管理API路由 - 完整版本（包含批量操作、导出、统计）
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.orm import Session
from datetime import date
from typing import Optional, List
from datetime import datetime as dt
import io
import csv

from config.database import get_db
from models.user import User
from depends.auth import get_current_user_required, get_admin_user, get_super_admin_user, get_office_admin_user, check_office_permission
from shared.models.space.space_resource import SpaceResource
from shared.models.space.space_booking import SpaceBooking
from shared.models.space.space_type import SpaceType
from shared.models.space.resource_time_slot import ResourceTimeSlot
from shared.schemas.space.space_resource import (
    SpaceResourceCreate,
    SpaceResourceUpdate,
    SpaceResourceResponse,
    SpaceAvailabilityResponse,
    ResourceTimeSlotCreate,
    ResourceTimeSlotUpdate,
    ResourceTimeSlotResponse,
)
from shared.schemas.space.response import ApiResponse, PaginatedResponse

router = APIRouter(prefix="/space/resources", tags=["空间资源管理"])


@router.get("", response_model=ApiResponse)
async def get_space_resources(
    type_code: Optional[str] = Query(None, description="空间类型代码过滤"),
    type_id: Optional[int] = Query(None, description="空间类型ID过滤"),
    is_active: Optional[bool] = Query(None, description="激活状态过滤"),
    is_available: Optional[bool] = Query(None, description="可预约状态过滤"),
    capacity_gte: Optional[int] = Query(None, description="容量大于等于"),
    capacity_lte: Optional[int] = Query(None, description="容量小于等于"),
    location: Optional[str] = Query(None, description="位置关键词搜索"),
    q: Optional[str] = Query(None, description="名称关键词搜索"),
    page: int = Query(1, ge=1, description="页码"),
    limit: int = Query(20, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db),
):
    """获取空间资源列表"""

    query = db.query(SpaceResource)

    if type_id:
        query = query.filter(SpaceResource.type_id == type_id)
    if type_code:
        space_type = (
            db.query(SpaceType).filter(SpaceType.type_code == type_code).first()
        )
        if space_type:
            query = query.filter(SpaceResource.type_id == space_type.id)
    if is_active is not None:
        query = query.filter(SpaceResource.is_active == is_active)
    if is_available is not None:
        query = query.filter(SpaceResource.is_available == is_available)
    if capacity_gte:
        query = query.filter(SpaceResource.capacity >= capacity_gte)
    if capacity_lte:
        query = query.filter(SpaceResource.capacity <= capacity_lte)
    if location:
        query = query.filter(SpaceResource.location.contains(location))
    if q:
        query = query.filter(SpaceResource.name.contains(q))

    total = query.count()
    resources = (
        query.order_by(SpaceResource.id).offset((page - 1) * limit).limit(limit).all()
    )

    items = []
    for r in resources:
        space_type = (
            db.query(SpaceType).filter(SpaceType.id == r.type_id).first()
            if r.type_id
            else None
        )
        items.append(
            {
                "id": r.id,
                "type_id": r.type_id,
                "type_code": space_type.type_code if space_type else None,
                "type_name": space_type.type_name if space_type else None,
                "name": r.name,
                "location": r.location,
                "capacity": r.capacity,
                "base_price": r.base_price,
                "member_price": r.member_price,
                "price_unit": r.price_unit,
                "free_hours_per_month": r.free_hours_per_month,
                "is_active": r.is_active,
                "is_available": r.is_available,
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


@router.get("/{resource_id}", response_model=ApiResponse)
async def get_space_resource(
    resource_id: int,
    db: Session = Depends(get_db),
):
    """获取空间资源详情"""

    resource = db.query(SpaceResource).filter(SpaceResource.id == resource_id).first()

    if not resource:
        raise HTTPException(status_code=404, detail="空间资源不存在")

    return ApiResponse(data=SpaceResourceResponse.model_validate(resource))


@router.post("", response_model=ApiResponse)
async def create_space_resource(
    resource_data: SpaceResourceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    """创建空间资源（仅管理员）"""

    resource = SpaceResource(**resource_data.model_dump())
    db.add(resource)
    db.commit()
    db.refresh(resource)

    return ApiResponse(
        code=201,
        message="空间资源创建成功",
        data=SpaceResourceResponse.model_validate(resource),
    )


@router.put("/{resource_id}", response_model=ApiResponse)
async def update_space_resource(
    resource_id: int,
    resource_data: SpaceResourceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    """更新空间资源（仅管理员）"""

    resource = db.query(SpaceResource).filter(SpaceResource.id == resource_id).first()

    if not resource:
        raise HTTPException(status_code=404, detail="空间资源不存在")

    update_data = resource_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        if hasattr(resource, key):
            setattr(resource, key, value)

    db.commit()
    db.refresh(resource)

    return ApiResponse(
        message="空间资源更新成功", data=SpaceResourceResponse.model_validate(resource)
    )


@router.delete("/{resource_id}", response_model=ApiResponse)
async def delete_space_resource(
    resource_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_super_admin_user),
):
    """删除空间资源（仅超级管理员）"""

    resource = db.query(SpaceResource).filter(SpaceResource.id == resource_id).first()

    if not resource:
        raise HTTPException(status_code=404, detail="空间资源不存在")

    db.delete(resource)
    db.commit()

    return ApiResponse(message="空间资源已删除")


@router.get("/{resource_id}/availability", response_model=ApiResponse)
async def check_resource_availability(
    resource_id: int,
    date: date = Query(..., description="查询日期"),
    booking_unit: Optional[str] = Query(None, description="预订单位过滤"),
    end_date: Optional[date] = Query(None, description="结束日期（多日预订）"),
    db: Session = Depends(get_db),
):
    """查询空间可用时段"""

    resource = db.query(SpaceResource).filter(SpaceResource.id == resource_id).first()

    if not resource:
        raise HTTPException(status_code=404, detail="空间资源不存在")

    bookings = (
        db.query(SpaceBooking)
        .filter(
            SpaceBooking.resource_id == resource_id,
            SpaceBooking.booking_date >= date,
            SpaceBooking.status.in_(["pending", "approved", "confirmed", "active"]),
        )
        .order_by(SpaceBooking.start_time)
        .all()
    )

    if end_date:
        bookings = bookings.filter(SpaceBooking.booking_date <= end_date)

    booked_slots = []
    for b in bookings:
        booked_slots.append(
            {
                "start_time": b.start_time,
                "end_time": b.end_time,
                "booking_date": b.booking_date.isoformat() if b.booking_date else None,
                "end_date": b.end_date.isoformat() if b.end_date else None,
                "time_slot_key": b.time_slot_key,
                "booking_unit": b.booking_unit or "hour",
                "booking_id": b.id,
                "booking_title": b.title,
                "user_name": b.user_name,
            }
        )

    available_slots = _calculate_available_slots(resource, booked_slots, date, booking_unit)

    total_available = len(available_slots)

    return ApiResponse(
        data={
            "resource_id": resource_id,
            "resource_name": resource.name,
            "date": date.isoformat(),
            "end_date": end_date.isoformat() if end_date else None,
            "booking_unit": booking_unit,
            "booked_slots": booked_slots,
            "available_slots": available_slots,
            "total_available": total_available,
        }
    )


def _calculate_available_slots(
    resource: SpaceResource,
    booked_slots: List[dict],
    query_date: date,
    booking_unit: Optional[str] = None,
) -> List[dict]:
    """计算可用时段——支持多种预订单位"""

    time_slots = resource.time_slots if hasattr(resource, 'time_slots') and resource.time_slots else []

    # If resource has configured time_slots, use them
    active_slots = [s for s in time_slots if s.is_active]

    if active_slots:
        if booking_unit:
            active_slots = [s for s in active_slots if s.duration_unit == booking_unit]

        available = []
        for slot in active_slots:
            # Count bookings that conflict with this slot
            conflicting_count = 0
            for b in booked_slots:
                if slot.slot_type in ("fixed_time",):
                    # Same day + same slot_key → conflict
                    if b.get("booking_date") == query_date.isoformat() and b.get("time_slot_key") == slot.slot_key:
                        conflicting_count += 1
                    # Also check hour-based bookings overlapping with this slot
                    elif b.get("booking_date") == query_date.isoformat() and b.get("booking_unit") == "hour":
                        if _time_ranges_overlap(
                            slot.start_time, slot.end_time,
                            b.get("start_time"), b.get("end_time"),
                        ):
                            conflicting_count += 1
                elif slot.slot_type == "session":
                    if b.get("booking_date") == query_date.isoformat() and b.get("time_slot_key") == slot.slot_key:
                        conflicting_count += 1
                elif slot.slot_type in ("day", "week", "month"):
                    b_end = b.get("end_date") or b.get("booking_date")
                    if _date_ranges_overlap(
                        str(query_date), str(query_date),
                        b.get("booking_date"), b_end,
                    ):
                        conflicting_count += 1

            available.append(
                {
                    "slot_key": slot.slot_key,
                    "slot_name": slot.slot_name,
                    "slot_type": slot.slot_type,
                    "start_time": slot.start_time,
                    "end_time": slot.end_time,
                    "duration_value": slot.duration_value,
                    "duration_unit": slot.duration_unit,
                    "max_bookings": slot.max_bookings_per_slot,
                    "booked_count": conflicting_count,
                    "available_count": max(0, slot.max_bookings_per_slot - conflicting_count),
                    "is_available": conflicting_count < slot.max_bookings_per_slot,
                }
            )

        return available

    # Fallback: no time_slots configured — use legacy hourly calculation
    hourly_booked = [b for b in booked_slots if b.get("booking_unit", "hour") == "hour"]

    if not hourly_booked:
        return [{"start_time": "08:00", "end_time": "23:00", "duration": 15, "slot_type": "hourly"}]

    available = []
    current_start = "08:00"

    for booked in sorted(hourly_booked, key=lambda x: x["start_time"] or ""):
        if not booked.get("start_time") or not booked.get("end_time"):
            continue
        if booked.get("booking_date") != query_date.isoformat():
            continue
        if booked["start_time"] > current_start:
            start_dt = dt.strptime(current_start, "%H:%M")
            end_dt = dt.strptime(booked["start_time"], "%H:%M")
            duration = (end_dt - start_dt).seconds / 3600
            available.append(
                {"start_time": current_start, "end_time": booked["start_time"], "duration": duration, "slot_type": "hourly"}
            )
        current_start = max(current_start, booked["end_time"]) if booked["end_time"] > current_start else current_start

    if current_start < "23:00":
        start_dt = dt.strptime(current_start, "%H:%M")
        end_dt = dt.strptime("23:00", "%H:%M")
        duration = (end_dt - start_dt).seconds / 3600
        available.append(
            {"start_time": current_start, "end_time": "23:00", "duration": duration, "slot_type": "hourly"}
        )

    return available


def _time_ranges_overlap(start1, end1, start2, end2):
    """Check if two time ranges overlap"""
    if not all([start1, end1, start2, end2]):
        return False
    return start1 < end2 and start2 < end1


def _date_ranges_overlap(start1, end1, start2, end2):
    """Check if two date ranges overlap"""
    if not all([start1, start2]):
        return False
    end1 = end1 or start1
    end2 = end2 or start2
    return start1 <= end2 and start2 <= end1


# ==================== 批量操作API ====================


@router.post("/batch/activate", response_model=ApiResponse)
async def batch_activate_resources(
    resource_ids: List[int] = Body(..., description="资源ID列表"),
    is_active: bool = Body(True, description="激活状态"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    """批量激活/停用资源"""

    if not resource_ids:
        raise HTTPException(status_code=400, detail="资源ID列表不能为空")

    updated_count = 0
    for resource_id in resource_ids:
        resource = (
            db.query(SpaceResource).filter(SpaceResource.id == resource_id).first()
        )
        if resource:
            resource.is_active = is_active
            updated_count += 1

    db.commit()

    return ApiResponse(
        message=f"成功更新{updated_count}个资源状态",
        data={"updated_count": updated_count},
    )


@router.post("/batch/delete", response_model=ApiResponse)
async def batch_delete_resources(
    resource_ids: List[int] = Body(..., description="资源ID列表"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_super_admin_user),
):
    """批量删除资源（仅超级管理员）"""

    if not resource_ids:
        raise HTTPException(status_code=400, detail="资源ID列表不能为空")

    deleted_count = 0
    for resource_id in resource_ids:
        resource = (
            db.query(SpaceResource).filter(SpaceResource.id == resource_id).first()
        )
        if resource:
            db.delete(resource)
            deleted_count += 1

    db.commit()

    return ApiResponse(
        message=f"成功删除{deleted_count}个资源", data={"deleted_count": deleted_count}
    )


# ==================== 导出功能API ====================


@router.get("/export/csv")
async def export_resources_csv(
    type_id: Optional[int] = Query(None, description="空间类型ID过滤"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    """导出资源数据为CSV"""

    query = db.query(SpaceResource)

    if type_id:
        query = query.filter(SpaceResource.type_id == type_id)

    resources = query.all()

    # 创建CSV数据
    output = io.StringIO()
    writer = csv.writer(output)

    # 写入表头
    writer.writerow(
        [
            "ID",
            "资源名称",
            "类型",
            "位置",
            "容量",
            "基础价格",
            "会员价格",
            "免费时长",
            "激活状态",
            "可预约状态",
            "创建时间",
        ]
    )

    # 写入数据行
    for r in resources:
        space_type = db.query(SpaceType).filter(SpaceType.id == r.type_id).first()
        writer.writerow(
            [
                r.id,
                r.name,
                space_type.type_name if space_type else "",
                r.location,
                r.capacity or "不限",
                r.base_price,
                r.member_price or "",
                r.free_hours_per_month or 0,
                "激活" if r.is_active else "停用",
                "可预约" if r.is_available else "不可预约",
                r.created_at.strftime("%Y-%m-%d %H:%M:%S") if r.created_at else "",
            ]
        )

    output.seek(0)

    # 返回CSV文件
    from fastapi.responses import StreamingResponse

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=space_resources_{dt.now().strftime('%Y%m%d_%H%M%S')}.csv"
        },
    )


# ==================== 统计功能API ====================


@router.get("/statistics/overview", response_model=ApiResponse)
async def get_resources_statistics(
    type_id: Optional[int] = Query(None, description="空间类型ID过滤"),
    db: Session = Depends(get_db),
):
    """获取资源统计概览"""

    query = db.query(SpaceResource)

    if type_id:
        query = query.filter(SpaceResource.type_id == type_id)

    resources = query.all()

    # 统计数据
    total_count = len(resources)
    active_count = sum(1 for r in resources if r.is_active)
    available_count = sum(1 for r in resources if r.is_available)

    # 按类型统计
    type_stats = {}
    for r in resources:
        space_type = db.query(SpaceType).filter(SpaceType.id == r.type_id).first()
        if space_type:
            type_code = space_type.type_code
            if type_code not in type_stats:
                type_stats[type_code] = {
                    "type_name": space_type.type_name,
                    "icon": space_type.icon,
                    "count": 0,
                    "active_count": 0,
                    "avg_price": 0,
                    "total_price": 0,
                }
            type_stats[type_code]["count"] += 1
            type_stats[type_code]["total_price"] += r.base_price
            if r.is_active:
                type_stats[type_code]["active_count"] += 1

    # 计算平均价格
    for type_code, stats in type_stats.items():
        if stats["count"] > 0:
            stats["avg_price"] = round(stats["total_price"] / stats["count"], 2)

    return ApiResponse(
        data={
            "total_count": total_count,
            "active_count": active_count,
            "inactive_count": total_count - active_count,
            "available_count": available_count,
            "type_statistics": type_stats,
        }
    )


@router.put("/{resource_id}/toggle-active", response_model=ApiResponse)
async def toggle_resource_active(
    resource_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    """切换资源激活/停用状态（仅管理员）"""

    resource = db.query(SpaceResource).filter(SpaceResource.id == resource_id).first()

    if not resource:
        raise HTTPException(status_code=404, detail="空间资源不存在")

    resource.is_active = not resource.is_active
    db.commit()
    db.refresh(resource)

    return ApiResponse(
        message=f"资源已{'激活' if resource.is_active else '停用'}",
        data={"id": resource.id, "is_active": resource.is_active},
    )


@router.get("/{resource_id}/usage-statistics", response_model=ApiResponse)
async def get_resource_usage_statistics(
    resource_id: int,
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    db: Session = Depends(get_db),
):
    """获取单个资源的使用统计"""

    resource = db.query(SpaceResource).filter(SpaceResource.id == resource_id).first()

    if not resource:
        raise HTTPException(status_code=404, detail="空间资源不存在")

    # 查询预约记录
    query = db.query(SpaceBooking).filter(SpaceBooking.resource_id == resource_id)

    if start_date:
        query = query.filter(SpaceBooking.booking_date >= start_date)
    if end_date:
        query = query.filter(SpaceBooking.booking_date <= end_date)

    bookings = query.all()

    # 统计数据
    total_bookings = len(bookings)
    total_hours = sum(b.duration or 0 for b in bookings)
    total_revenue = sum(b.total_fee or 0 for b in bookings)

    # 按状态统计
    status_count = {}
    for b in bookings:
        status = b.status or "pending"
        status_count[status] = status_count.get(status, 0) + 1

    # 按月份统计
    monthly_stats = {}
    for b in bookings:
        month_key = b.booking_date.strftime("%Y-%m") if b.booking_date else "unknown"
        if month_key not in monthly_stats:
            monthly_stats[month_key] = {"booking_count": 0, "hours": 0, "revenue": 0}
        monthly_stats[month_key]["booking_count"] += 1
        monthly_stats[month_key]["hours"] += b.duration or 0
        monthly_stats[month_key]["revenue"] += b.total_fee or 0

    return ApiResponse(
        data={
            "resource_id": resource_id,
            "resource_name": resource.name,
            "total_bookings": total_bookings,
            "total_hours": round(total_hours, 2),
            "total_revenue": round(total_revenue, 2),
            "status_distribution": status_count,
            "monthly_statistics": monthly_stats,
            "utilization_rate": round(total_hours / (30 * 8) * 100, 2)
            if total_hours > 0
            else 0,
        }
    )


# ==================== 批量导入API ====================


@router.post("/batch/import", response_model=ApiResponse)
async def batch_import_resources(
    resources_data: List[dict] = Body(..., description="资源数据列表"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    """批量导入资源"""

    imported_count = 0
    failed_count = 0
    errors = []

    for data in resources_data:
        try:
            # 验证必填字段
            if (
                not data.get("name")
                or not data.get("type_id")
                or not data.get("base_price")
            ):
                failed_count += 1
                errors.append(f"资源 '{data.get('name', '未知')}' 缺少必填字段")
                continue

            # 创建资源
            resource = SpaceResource(
                type_id=data["type_id"],
                name=data["name"],
                location=data.get("location", ""),
                capacity=data.get("capacity"),
                base_price=data["base_price"],
                member_price=data.get("member_price"),
                price_unit=data.get("price_unit", "hour"),
                free_hours_per_month=data.get("free_hours_per_month", 0),
                is_active=data.get("is_active", True),
                is_available=data.get("is_available", True),
            )

            db.add(resource)
            imported_count += 1

        except Exception as e:
            failed_count += 1
            errors.append(f"导入失败: {str(e)}")

    db.commit()

    return ApiResponse(
        message=f"成功导入{imported_count}个资源，失败{failed_count}个",
        data={
            "imported_count": imported_count,
            "failed_count": failed_count,
            "errors": errors[:10],
        },
    )


# ==================== 办公室管理员资源管理API ====================


def _get_office_name_from_id(office_id: int, db: Session) -> Optional[str]:
    """根据办公室ID获取办公室名称，用于权限校验"""
    from sqlalchemy import text
    result = db.execute(text("SELECT name FROM offices WHERE id = :id"), {"id": office_id}).fetchone()
    return result[0] if result else None


def _require_office_admin_for_resource(resource_id: int, db: Session, current_user: User):
    """校验 office_admin 对资源的管辖权限"""
    resource = db.query(SpaceResource).filter(SpaceResource.id == resource_id).first()
    if not resource:
        raise HTTPException(status_code=404, detail="空间资源不存在")
    if not resource.office_id:
        raise HTTPException(status_code=400, detail="该资源未关联办公室")
    office_name = _get_office_name_from_id(resource.office_id, db)
    if not office_name:
        raise HTTPException(status_code=404, detail="关联办公室不存在")
    if current_user.role not in ("admin", "super_admin"):
        if current_user.role == "office_admin" and current_user.department != office_name:
            raise HTTPException(
                status_code=403,
                detail=f"无权限管理办公室 '{office_name}' 的资源",
            )
    return resource, office_name


@router.get("/office/{office_id}", response_model=ApiResponse)
async def get_office_resources(
    office_id: int,
    type_id: Optional[int] = Query(None, description="空间类型过滤"),
    is_active: Optional[bool] = Query(None, description="激活状态过滤"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_office_admin_user),
):
    """获取办公室的资源列表（办公室管理员）"""
    office_name = _get_office_name_from_id(office_id, db)
    if not office_name:
        raise HTTPException(status_code=404, detail="办公室不存在")

    if current_user.role not in ("admin", "super_admin"):
        if current_user.department != office_name:
            raise HTTPException(status_code=403, detail=f"无权限查看办公室 '{office_name}' 的资源")

    query = db.query(SpaceResource).filter(SpaceResource.office_id == office_id)
    if type_id:
        query = query.filter(SpaceResource.type_id == type_id)
    if is_active is not None:
        query = query.filter(SpaceResource.is_active == is_active)

    resources = query.order_by(SpaceResource.id).all()

    items = []
    for r in resources:
        space_type = db.query(SpaceType).filter(SpaceType.id == r.type_id).first() if r.type_id else None
        items.append(
            {
                "id": r.id,
                "type_id": r.type_id,
                "type_code": space_type.type_code if space_type else None,
                "type_name": space_type.type_name if space_type else None,
                "name": r.name,
                "location": r.location,
                "capacity": r.capacity,
                "base_price": r.base_price,
                "is_active": r.is_active,
                "is_available": r.is_available,
                "maintenance_status": r.maintenance_status,
            }
        )

    return ApiResponse(data={"office_id": office_id, "office_name": office_name, "resources": items})


@router.put("/{resource_id}/office-toggle-active", response_model=ApiResponse)
async def office_toggle_resource_active(
    resource_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_office_admin_user),
):
    """办公室管理员启用/停用资源"""
    resource, office_name = _require_office_admin_for_resource(resource_id, db, current_user)

    resource.is_active = not resource.is_active
    db.commit()
    db.refresh(resource)

    return ApiResponse(
        message=f"资源已{'激活' if resource.is_active else '停用'}",
        data={"id": resource.id, "is_active": resource.is_active, "office_name": office_name},
    )


# ==================== 资源时段管理API ====================


@router.get("/{resource_id}/time-slots", response_model=ApiResponse)
async def get_resource_time_slots(
    resource_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_required),
):
    """获取资源的可用时段配置"""
    resource = db.query(SpaceResource).filter(SpaceResource.id == resource_id).first()
    if not resource:
        raise HTTPException(status_code=404, detail="空间资源不存在")

    time_slots = db.query(ResourceTimeSlot).filter(
        ResourceTimeSlot.resource_id == resource_id, ResourceTimeSlot.is_active == True
    ).order_by(ResourceTimeSlot.sort_order).all()

    return ApiResponse(
        data={
            "resource_id": resource_id,
            "resource_name": resource.name,
            "time_slots": [
                {
                    "id": ts.id,
                    "slot_key": ts.slot_key,
                    "slot_name": ts.slot_name,
                    "slot_type": ts.slot_type,
                    "start_time": ts.start_time,
                    "end_time": ts.end_time,
                    "duration_value": ts.duration_value,
                    "duration_unit": ts.duration_unit,
                    "max_bookings_per_slot": ts.max_bookings_per_slot,
                    "applicable_days": ts.applicable_days,
                    "price_override": ts.price_override,
                    "is_active": ts.is_active,
                }
                for ts in time_slots
            ],
        }
    )


@router.put("/{resource_id}/time-slots", response_model=ApiResponse)
async def update_resource_time_slots(
    resource_id: int,
    time_slots_data: List[ResourceTimeSlotCreate] = Body(..., description="时段配置列表"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    """配置资源可用时段（管理员/办公室管理员）"""
    resource = db.query(SpaceResource).filter(SpaceResource.id == resource_id).first()
    if not resource:
        raise HTTPException(status_code=404, detail="空间资源不存在")

    # office_admin scope check
    if current_user.role == "office_admin":
        if resource.office_id:
            office_name = _get_office_name_from_id(resource.office_id, db)
            if office_name and current_user.department != office_name:
                raise HTTPException(status_code=403, detail=f"无权限配置办公室 '{office_name}' 的资源时段")

    # Delete existing time slots and replace
    db.query(ResourceTimeSlot).filter(ResourceTimeSlot.resource_id == resource_id).delete()

    for ts_data in time_slots_data:
        ts = ResourceTimeSlot(
            resource_id=resource_id,
            slot_key=ts_data.slot_key,
            slot_name=ts_data.slot_name,
            slot_type=ts_data.slot_type,
            start_time=ts_data.start_time,
            end_time=ts_data.end_time,
            duration_value=ts_data.duration_value,
            duration_unit=ts_data.duration_unit,
            max_bookings_per_slot=ts_data.max_bookings_per_slot,
            applicable_days=ts_data.applicable_days,
            price_override=ts_data.price_override,
            is_active=ts_data.is_active,
            sort_order=ts_data.sort_order,
        )
        db.add(ts)

    db.commit()

    updated_slots = db.query(ResourceTimeSlot).filter(
        ResourceTimeSlot.resource_id == resource_id
    ).order_by(ResourceTimeSlot.sort_order).all()

    return ApiResponse(
        message=f"时段配置已更新，共 {len(updated_slots)} 个时段",
        data={
            "resource_id": resource_id,
            "time_slots": [
                {
                    "id": ts.id,
                    "slot_key": ts.slot_key,
                    "slot_name": ts.slot_name,
                    "slot_type": ts.slot_type,
                    "start_time": ts.start_time,
                    "end_time": ts.end_time,
                    "duration_value": ts.duration_value,
                    "duration_unit": ts.duration_unit,
                    "is_active": ts.is_active,
                }
                for ts in updated_slots
            ],
        },
    )
