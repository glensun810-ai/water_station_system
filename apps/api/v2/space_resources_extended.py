"""
空间资源管理API路由 - 补充批量操作和导出功能
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
from depends.auth import get_current_user_required, get_admin_user
from shared.models.space.space_resource import SpaceResource
from shared.models.space.space_booking import SpaceBooking
from shared.models.space.space_type import SpaceType
from shared.schemas.space.space_resource import (
    SpaceResourceCreate,
    SpaceResourceUpdate,
    SpaceResourceResponse,
    SpaceAvailabilityResponse,
)
from shared.schemas.space.response import ApiResponse, PaginatedResponse

router = APIRouter(prefix="/space/resources", tags=["空间资源管理"])

# ... 保留原有的GET、POST、PUT、DELETE接口 ...


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
    current_user: User = Depends(get_admin_user),
):
    """批量删除资源"""

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
                r.created_at.strftime("%Y-%m-%d %H:%M:%S"),
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
                }
            type_stats[type_code]["count"] += 1
            if r.is_active:
                type_stats[type_code]["active_count"] += 1

    # 计算平均价格
    for type_code, stats in type_stats.items():
        type_resources = [
            r for r in resources if r.type_id == type_stats[type_code]["count"]
        ]
        if type_resources:
            avg_price = sum(r.base_price for r in type_resources) / len(type_resources)
            stats["avg_price"] = round(avg_price, 2)

    return ApiResponse(
        data={
            "total_count": total_count,
            "active_count": active_count,
            "inactive_count": total_count - active_count,
            "available_count": available_count,
            "type_statistics": type_stats,
        }
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
    total_hours = sum(b.duration_hours or 0 for b in bookings)
    total_revenue = sum(b.total_price or 0 for b in bookings)

    # 按状态统计
    status_count = {}
    for b in bookings:
        status = b.status or "pending"
        status_count[status] = status_count.get(status, 0) + 1

    # 按月份统计（最近6个月）
    monthly_stats = {}
    for b in bookings:
        month_key = b.booking_date.strftime("%Y-%m") if b.booking_date else "unknown"
        if month_key not in monthly_stats:
            monthly_stats[month_key] = {"booking_count": 0, "hours": 0, "revenue": 0}
        monthly_stats[month_key]["booking_count"] += 1
        monthly_stats[month_key]["hours"] += b.duration_hours or 0
        monthly_stats[month_key]["revenue"] += b.total_price or 0

    return ApiResponse(
        data={
            "resource_id": resource_id,
            "resource_name": resource.name,
            "total_bookings": total_bookings,
            "total_hours": total_hours,
            "total_revenue": round(total_revenue, 2),
            "status_distribution": status_count,
            "monthly_statistics": monthly_stats,
            "utilization_rate": round(total_hours / (30 * 8) * 100, 2)
            if total_hours > 0
            else 0,  # 假设每月工作240小时
        }
    )


@router.post("/batch/import")
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
            "errors": errors[:10],  # 只返回前10个错误
        },
    )
