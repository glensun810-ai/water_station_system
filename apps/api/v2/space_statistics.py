"""
空间统计分析API路由
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date, datetime, timedelta
from typing import Optional

from config.database import get_db
from models.user import User
from depends.auth import get_admin_user, get_current_user_required
from shared.models.space.space_booking import SpaceBooking
from shared.models.space.space_resource import SpaceResource
from shared.models.space.space_type import SpaceType
from shared.schemas.space.response import ApiResponse

router = APIRouter(prefix="/space/statistics", tags=["统计分析"])


@router.get("/my", response_model=ApiResponse)
async def get_my_statistics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_required),
):
    """获取用户个人统计信息"""

    total_bookings = (
        db.query(SpaceBooking)
        .filter(
            SpaceBooking.user_id == current_user.id,
            SpaceBooking.is_deleted == 0,
        )
        .count()
    )

    this_month_start = date.today().replace(day=1)
    this_month = (
        db.query(SpaceBooking)
        .filter(
            SpaceBooking.user_id == current_user.id,
            SpaceBooking.booking_date >= this_month_start,
            SpaceBooking.is_deleted == 0,
        )
        .count()
    )

    total_fee = (
        db.query(func.sum(SpaceBooking.actual_fee))
        .filter(
            SpaceBooking.user_id == current_user.id,
            SpaceBooking.status.in_(["confirmed", "completed", "settled"]),
            SpaceBooking.is_deleted == 0,
        )
        .scalar()
        or 0
    )

    free_hours_remaining = 0
    if current_user.role in ["member", "vip"]:
        free_hours_remaining = 2

    saved_amount = 0
    if current_user.role == "member":
        saved_amount = total_fee * 0.2
    elif current_user.role == "vip":
        saved_amount = total_fee * 0.3

    return ApiResponse(
        data={
            "total_bookings": total_bookings,
            "this_month": this_month,
            "free_hours_remaining": free_hours_remaining,
            "saved_amount": saved_amount,
            "total_spent": total_fee,
        }
    )


@router.get("/overview", response_model=ApiResponse)
async def get_statistics_overview(
    date_from: Optional[date] = Query(None, description="开始日期"),
    date_to: Optional[date] = Query(None, description="结束日期"),
    type_code: Optional[str] = Query(None, description="空间类型过滤"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    """获取统计概览"""

    if not date_from:
        date_from = date.today() - timedelta(days=30)
    if not date_to:
        date_to = date.today()

    query = db.query(SpaceBooking).filter(
        SpaceBooking.booking_date >= date_from,
        SpaceBooking.booking_date <= date_to,
        SpaceBooking.is_deleted == 0,
    )

    if type_code:
        query = query.filter(SpaceBooking.type_code == type_code)

    total_bookings = query.count()

    total_hours = query.with_entities(func.sum(SpaceBooking.duration)).scalar() or 0

    total_revenue = query.with_entities(func.sum(SpaceBooking.actual_fee)).scalar() or 0

    completed_bookings = query.filter(SpaceBooking.status == "completed").count()
    avg_duration = total_hours / total_bookings if total_bookings > 0 else 0

    success_bookings = query.filter(
        SpaceBooking.status.in_(["confirmed", "completed", "settled"])
    ).count()
    success_rate = (
        (success_bookings / total_bookings * 100) if total_bookings > 0 else 0
    )

    cancelled_bookings = query.filter(SpaceBooking.status == "cancelled").count()
    cancel_rate = (
        (cancelled_bookings / total_bookings * 100) if total_bookings > 0 else 0
    )

    by_type = []
    types = db.query(SpaceType).filter(SpaceType.is_active == True).all()
    for t in types:
        type_query = query.filter(SpaceBooking.type_id == t.id)
        type_count = type_query.count()
        type_hours = (
            type_query.with_entities(func.sum(SpaceBooking.duration)).scalar() or 0
        )
        type_revenue = (
            type_query.with_entities(func.sum(SpaceBooking.actual_fee)).scalar() or 0
        )

        by_type.append(
            {
                "type_code": t.type_code,
                "type_name": t.type_name,
                "booking_count": type_count,
                "hours": type_hours,
                "revenue": type_revenue,
            }
        )

    by_status = {}
    status_list = [
        "pending_approval",
        "approved",
        "confirmed",
        "completed",
        "cancelled",
        "rejected",
    ]
    for status in status_list:
        by_status[status] = query.filter(SpaceBooking.status == status).count()

    return ApiResponse(
        data={
            "period": {"from": date_from.isoformat(), "to": date_to.isoformat()},
            "summary": {
                "total_bookings": total_bookings,
                "total_hours": total_hours,
                "total_revenue": total_revenue,
                "average_booking_duration": avg_duration,
                "booking_success_rate": success_rate,
                "cancellation_rate": cancel_rate,
            },
            "by_type": by_type,
            "by_status": by_status,
        }
    )


@router.get("/dashboard", response_model=ApiResponse)
async def get_dashboard_data(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    """获取Dashboard数据"""

    today = date.today()

    today_bookings = (
        db.query(SpaceBooking)
        .filter(SpaceBooking.booking_date == today, SpaceBooking.is_deleted == 0)
        .count()
    )

    pending_approvals = (
        db.query(SpaceBooking)
        .filter(SpaceBooking.status == "pending_approval", SpaceBooking.is_deleted == 0)
        .count()
    )

    completed_today = (
        db.query(SpaceBooking)
        .filter(
            SpaceBooking.booking_date == today,
            SpaceBooking.status == "completed",
            SpaceBooking.is_deleted == 0,
        )
        .count()
    )

    today_revenue = (
        db.query(func.sum(SpaceBooking.actual_fee))
        .filter(
            SpaceBooking.booking_date == today,
            SpaceBooking.status.in_(["confirmed", "completed", "settled"]),
            SpaceBooking.is_deleted == 0,
        )
        .scalar()
        or 0
    )

    yesterday = today - timedelta(days=1)
    yesterday_bookings = (
        db.query(SpaceBooking)
        .filter(SpaceBooking.booking_date == yesterday, SpaceBooking.is_deleted == 0)
        .count()
    )

    booking_change = (
        ((today_bookings - yesterday_bookings) / yesterday_bookings * 100)
        if yesterday_bookings > 0
        else 0
    )

    yesterday_revenue = (
        db.query(func.sum(SpaceBooking.actual_fee))
        .filter(
            SpaceBooking.booking_date == yesterday,
            SpaceBooking.status.in_(["confirmed", "completed", "settled"]),
            SpaceBooking.is_deleted == 0,
        )
        .scalar()
        or 0
    )

    revenue_change = (
        ((today_revenue - yesterday_revenue) / yesterday_revenue * 100)
        if yesterday_revenue > 0
        else 0
    )

    return ApiResponse(
        data={
            "today": {
                "bookings": today_bookings,
                "pending_approvals": pending_approvals,
                "completed": completed_today,
                "revenue": today_revenue,
            },
            "changes": {
                "booking_change": booking_change,
                "revenue_change": revenue_change,
            },
            "yesterday": {
                "bookings": yesterday_bookings,
                "revenue": yesterday_revenue,
            },
        }
    )


@router.get("/usage", response_model=ApiResponse)
async def get_usage_statistics(
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    type_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    """获取使用率统计"""

    if not date_from:
        date_from = date.today() - timedelta(days=30)
    if not date_to:
        date_to = date.today()

    resources = db.query(SpaceResource).filter(SpaceResource.is_active == True)
    if type_id:
        resources = resources.filter(SpaceResource.type_id == type_id)

    usage_data = []
    for resource in resources.all():
        bookings = (
            db.query(SpaceBooking)
            .filter(
                SpaceBooking.resource_id == resource.id,
                SpaceBooking.booking_date >= date_from,
                SpaceBooking.booking_date <= date_to,
                SpaceBooking.status.in_(["confirmed", "completed", "settled"]),
                SpaceBooking.is_deleted == 0,
            )
            .all()
        )

        used_hours = sum(b.duration or 0 for b in bookings)

        days = (date_to - date_from).days + 1
        available_hours = days * 14

        utilization = (used_hours / available_hours * 100) if available_hours > 0 else 0

        usage_data.append(
            {
                "resource_id": resource.id,
                "resource_name": resource.name,
                "type_id": resource.type_id,
                "bookings_count": len(bookings),
                "used_hours": used_hours,
                "available_hours": available_hours,
                "utilization": utilization,
            }
        )

    return ApiResponse(
        data={
            "period": {"from": date_from.isoformat(), "to": date_to.isoformat()},
            "resources": usage_data,
        }
    )


@router.get("/trends", response_model=ApiResponse)
async def get_booking_trends(
    days: int = Query(30, ge=7, le=90, description="统计天数"),
    type_code: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    """获取预约趋势"""

    end_date = date.today()
    start_date = end_date - timedelta(days=days)

    trends = []
    current_date = start_date

    while current_date <= end_date:
        query = db.query(SpaceBooking).filter(
            SpaceBooking.booking_date == current_date, SpaceBooking.is_deleted == 0
        )

        if type_code:
            query = query.filter(SpaceBooking.type_code == type_code)

        count = query.count()
        revenue = query.with_entities(func.sum(SpaceBooking.actual_fee)).scalar() or 0

        trends.append(
            {
                "date": current_date.isoformat(),
                "bookings": count,
                "revenue": revenue,
            }
        )

        current_date += timedelta(days=1)

    return ApiResponse(
        data={
            "days": days,
            "type_code": type_code,
            "trends": trends,
        }
    )


@router.get("/revenue", response_model=ApiResponse)
async def get_revenue_statistics(
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    """获取收入统计"""

    if not date_from:
        date_from = date.today() - timedelta(days=30)
    if not date_to:
        date_to = date.today()

    query = db.query(SpaceBooking).filter(
        SpaceBooking.booking_date >= date_from,
        SpaceBooking.booking_date <= date_to,
        SpaceBooking.status.in_(["confirmed", "completed", "settled"]),
        SpaceBooking.is_deleted == 0,
    )

    total_revenue = query.with_entities(func.sum(SpaceBooking.actual_fee)).scalar() or 0

    base_revenue = query.with_entities(func.sum(SpaceBooking.base_fee)).scalar() or 0

    addon_revenue = query.with_entities(func.sum(SpaceBooking.addon_fee)).scalar() or 0

    by_payment_status = {}
    for status in ["unpaid", "deposit_paid", "fully_paid", "refunded"]:
        status_revenue = (
            query.filter(SpaceBooking.payment_status == status)
            .with_entities(func.sum(SpaceBooking.actual_fee))
            .scalar()
            or 0
        )
        by_payment_status[status] = status_revenue

    return ApiResponse(
        data={
            "period": {"from": date_from.isoformat(), "to": date_to.isoformat()},
            "total_revenue": total_revenue,
            "base_revenue": base_revenue,
            "addon_revenue": addon_revenue,
            "by_payment_status": by_payment_status,
        }
    )
