"""
会议室服务API路由 - v1版本
统一的API端点 following API design specification
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import date, time, datetime
from typing import List, Optional
from pydantic import BaseModel, field_validator

from config.database import get_db
from models.meeting import MeetingRoom
from models.booking import MeetingBooking, BookingStatus
from models.user import User
from depends.auth import get_current_user, get_admin_user, get_current_user

router = APIRouter(prefix="/meeting", tags=["会议室服务"])


@router.get("/stats/today")
def get_meeting_stats_today(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    """获取今日会议室统计数据"""

    from datetime import date
    from sqlalchemy import func

    today = date.today()

    booking_count = (
        db.query(func.count(MeetingBooking.id))
        .filter(MeetingBooking.booking_date == today)
        .scalar()
        or 0
    )

    pending_approvals = (
        db.query(func.count(MeetingBooking.id))
        .filter(MeetingBooking.status == BookingStatus.PENDING)
        .scalar()
        or 0
    )

    cancelled_count = (
        db.query(func.count(MeetingBooking.id))
        .filter(
            MeetingBooking.booking_date == today,
            MeetingBooking.status == BookingStatus.CANCELLED,
        )
        .scalar()
        or 0
    )

    alerts = cancelled_count

    return {
        "booking_count": booking_count,
        "pending_approvals": pending_approvals,
        "cancelled_count": cancelled_count,
        "alerts": alerts,
        "date": today.isoformat(),
    }


@router.get("/stats/usage-rate")
def get_usage_rate(
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    room_id: Optional[int] = Query(None, description="会议室ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    """计算会议室使用率：实际使用小时/可用总小时 * 100"""

    from datetime import timedelta
    from sqlalchemy import func

    if not start_date:
        start_date = date.today() - timedelta(days=7)
    if not end_date:
        end_date = date.today()

    query = db.query(MeetingBooking).filter(
        MeetingBooking.booking_date >= start_date,
        MeetingBooking.booking_date <= end_date,
        MeetingBooking.status == BookingStatus.CONFIRMED,
    )

    if room_id:
        query = query.filter(MeetingBooking.room_id == room_id)

    bookings = query.all()

    total_used_hours = sum([b.duration or 0 for b in bookings])

    days_diff = (end_date - start_date).days + 1

    if room_id:
        room = db.query(MeetingRoom).filter(MeetingRoom.id == room_id).first()
        available_hours_per_day = 15  # 假设每天可用15小时（07:00-22:00）
        total_available_hours = days_diff * available_hours_per_day
    else:
        active_rooms = (
            db.query(MeetingRoom).filter(MeetingRoom.is_active == True).count()
        )
        available_hours_per_day = 15
        total_available_hours = days_diff * available_hours_per_day * active_rooms

    usage_rate = (
        (total_used_hours / total_available_hours * 100)
        if total_available_hours > 0
        else 0
    )

    return {
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "room_id": room_id,
        "total_used_hours": total_used_hours,
        "total_available_hours": total_available_hours,
        "usage_rate": round(usage_rate, 2),
        "booking_count": len(bookings),
    }


@router.get("/stats/weekly")
def get_weekly_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    """获取本周统计数据"""

    from datetime import timedelta
    from sqlalchemy import func

    today = date.today()
    start_of_week = today - timedelta(days=today.weekday())
    end_of_week = start_of_week + timedelta(days=6)

    booking_count = (
        db.query(func.count(MeetingBooking.id))
        .filter(
            MeetingBooking.booking_date >= start_of_week,
            MeetingBooking.booking_date <= end_of_week,
        )
        .scalar()
        or 0
    )

    confirmed_count = (
        db.query(func.count(MeetingBooking.id))
        .filter(
            MeetingBooking.booking_date >= start_of_week,
            MeetingBooking.booking_date <= end_of_week,
            MeetingBooking.status == BookingStatus.CONFIRMED,
        )
        .scalar()
        or 0
    )

    total_revenue = (
        db.query(func.sum(MeetingBooking.actual_fee))
        .filter(
            MeetingBooking.booking_date >= start_of_week,
            MeetingBooking.booking_date <= end_of_week,
            MeetingBooking.status.in_(
                [BookingStatus.CONFIRMED, BookingStatus.COMPLETED]
            ),
        )
        .scalar()
        or 0.0
    )

    return {
        "week_start": start_of_week.isoformat(),
        "week_end": end_of_week.isoformat(),
        "booking_count": booking_count,
        "confirmed_count": confirmed_count,
        "total_revenue": float(total_revenue),
        "avg_daily_bookings": round(booking_count / 7, 1) if booking_count > 0 else 0,
    }


@router.get("/stats/monthly")
def get_monthly_stats(
    month: Optional[int] = Query(None, description="月份（1-12）"),
    year: Optional[int] = Query(None, description="年份"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    """获取月度统计数据"""

    from calendar import monthrange
    from sqlalchemy import func

    today = date.today()
    target_year = year or today.year
    target_month = month or today.month

    start_of_month = date(target_year, target_month, 1)
    _, last_day = monthrange(target_year, target_month)
    end_of_month = date(target_year, target_month, last_day)

    booking_count = (
        db.query(func.count(MeetingBooking.id))
        .filter(
            MeetingBooking.booking_date >= start_of_month,
            MeetingBooking.booking_date <= end_of_month,
        )
        .scalar()
        or 0
    )

    confirmed_count = (
        db.query(func.count(MeetingBooking.id))
        .filter(
            MeetingBooking.booking_date >= start_of_month,
            MeetingBooking.booking_date <= end_of_month,
            MeetingBooking.status == BookingStatus.CONFIRMED,
        )
        .scalar()
        or 0
    )

    completed_count = (
        db.query(func.count(MeetingBooking.id))
        .filter(
            MeetingBooking.booking_date >= start_of_month,
            MeetingBooking.booking_date <= end_of_month,
            MeetingBooking.status == BookingStatus.COMPLETED,
        )
        .scalar()
        or 0
    )

    cancelled_count = (
        db.query(func.count(MeetingBooking.id))
        .filter(
            MeetingBooking.booking_date >= start_of_month,
            MeetingBooking.booking_date <= end_of_month,
            MeetingBooking.status == BookingStatus.CANCELLED,
        )
        .scalar()
        or 0
    )

    total_revenue = (
        db.query(func.sum(MeetingBooking.actual_fee))
        .filter(
            MeetingBooking.booking_date >= start_of_month,
            MeetingBooking.booking_date <= end_of_month,
            MeetingBooking.status.in_(
                [BookingStatus.CONFIRMED, BookingStatus.COMPLETED]
            ),
        )
        .scalar()
        or 0.0
    )

    pending_revenue = (
        db.query(func.sum(MeetingBooking.total_fee))
        .filter(
            MeetingBooking.booking_date >= start_of_month,
            MeetingBooking.booking_date <= end_of_month,
            MeetingBooking.status == BookingStatus.PENDING,
        )
        .scalar()
        or 0.0
    )

    days_in_month = last_day

    return {
        "month": target_month,
        "year": target_year,
        "month_start": start_of_month.isoformat(),
        "month_end": end_of_month.isoformat(),
        "days_in_month": days_in_month,
        "booking_count": booking_count,
        "confirmed_count": confirmed_count,
        "completed_count": completed_count,
        "cancelled_count": cancelled_count,
        "total_revenue": float(total_revenue),
        "pending_revenue": float(pending_revenue),
        "avg_daily_bookings": round(booking_count / days_in_month, 1)
        if booking_count > 0
        else 0,
        "completion_rate": round(confirmed_count / booking_count * 100, 1)
        if booking_count > 0
        else 0,
    }


@router.get("/stats/revenue")
def get_revenue_stats(
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    """获取收入统计数据"""

    from datetime import timedelta
    from sqlalchemy import func

    if not start_date:
        start_date = date.today() - timedelta(days=30)
    if not end_date:
        end_date = date.today()

    total_revenue = (
        db.query(func.sum(MeetingBooking.actual_fee))
        .filter(
            MeetingBooking.booking_date >= start_date,
            MeetingBooking.booking_date <= end_date,
            MeetingBooking.status.in_(
                [BookingStatus.CONFIRMED, BookingStatus.COMPLETED]
            ),
        )
        .scalar()
        or 0.0
    )

    pending_revenue = (
        db.query(func.sum(MeetingBooking.total_fee))
        .filter(
            MeetingBooking.booking_date >= start_date,
            MeetingBooking.booking_date <= end_date,
            MeetingBooking.status == BookingStatus.PENDING,
        )
        .scalar()
        or 0.0
    )

    cancelled_revenue = (
        db.query(func.sum(MeetingBooking.total_fee))
        .filter(
            MeetingBooking.booking_date >= start_date,
            MeetingBooking.booking_date <= end_date,
            MeetingBooking.status == BookingStatus.CANCELLED,
        )
        .scalar()
        or 0.0
    )

    booking_count = (
        db.query(func.count(MeetingBooking.id))
        .filter(
            MeetingBooking.booking_date >= start_date,
            MeetingBooking.booking_date <= end_date,
            MeetingBooking.status.in_(
                [BookingStatus.CONFIRMED, BookingStatus.COMPLETED]
            ),
        )
        .scalar()
        or 0
    )

    return {
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "total_revenue": float(total_revenue),
        "pending_revenue": float(pending_revenue),
        "cancelled_revenue": float(cancelled_revenue),
        "paid_booking_count": booking_count,
        "avg_revenue_per_booking": round(float(total_revenue) / booking_count, 2)
        if booking_count > 0
        else 0,
    }


@router.get("/stats/trend")
def get_booking_trend(
    days: int = Query(7, description="统计天数"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    """获取预约趋势数据（用于ECharts图表）"""

    from datetime import timedelta
    from sqlalchemy import func

    end_date = date.today()
    start_date = end_date - timedelta(days=days - 1)

    trend_data = []

    for i in range(days):
        current_date = start_date + timedelta(days=i)

        booking_count = (
            db.query(func.count(MeetingBooking.id))
            .filter(MeetingBooking.booking_date == current_date)
            .scalar()
            or 0
        )

        revenue = (
            db.query(func.sum(MeetingBooking.actual_fee))
            .filter(
                MeetingBooking.booking_date == current_date,
                MeetingBooking.status.in_(
                    [BookingStatus.CONFIRMED, BookingStatus.COMPLETED]
                ),
            )
            .scalar()
            or 0.0
        )

        trend_data.append(
            {
                "date": current_date.isoformat(),
                "booking_count": booking_count,
                "revenue": float(revenue),
            }
        )

    return {
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "days": days,
        "trend_data": trend_data,
    }


# ==================== Pydantic Schemas ====================


class MeetingRoomBase(BaseModel):
    name: str
    location: Optional[str] = None
    capacity: int = 10
    facilities: Optional[str] = None
    price_per_hour: float = 0.0
    member_price_per_hour: float = 0.0
    free_hours_per_month: int = 0
    is_active: bool = True

    @field_validator("name")
    def name_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError("会议室名称不能为空")
        return v

    @field_validator("capacity")
    def capacity_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError("容纳人数必须大于0")
        return v

    @field_validator("price_per_hour")
    def price_must_be_non_negative(cls, v):
        if v < 0:
            raise ValueError("价格不能为负数")
        return v


class MeetingRoomCreate(MeetingRoomBase):
    pass


class MeetingRoomUpdate(BaseModel):
    name: Optional[str] = None
    location: Optional[str] = None
    capacity: Optional[int] = None
    facilities: Optional[str] = None
    price_per_hour: Optional[float] = None
    member_price_per_hour: Optional[float] = None
    free_hours_per_month: Optional[int] = None
    is_active: Optional[bool] = None


class MeetingRoomResponse(MeetingRoomBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class MeetingBookingBase(BaseModel):
    room_id: int
    user_type: str = "external"
    office_id: Optional[int] = None
    user_name: str
    user_phone: Optional[str] = None
    department: Optional[str] = None
    booking_date: date
    start_time: str
    end_time: str
    meeting_title: Optional[str] = None
    attendees_count: int = 1


class MeetingBookingCreate(MeetingBookingBase):
    pass


class MeetingBookingUpdate(BaseModel):
    booking_date: Optional[date] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    meeting_title: Optional[str] = None
    attendees_count: Optional[int] = None
    user_phone: Optional[str] = None
    department: Optional[str] = None


class MeetingBookingResponse(BaseModel):
    id: int
    booking_no: str
    room_id: int
    room_name: Optional[str] = None
    user_type: str = "external"
    office_id: Optional[int] = None
    user_id: Optional[int] = None
    user_name: str
    user_phone: Optional[str] = None
    department: Optional[str] = None
    booking_date: date
    start_time: str
    end_time: str
    duration: Optional[float] = None
    meeting_title: Optional[str] = None
    attendees_count: int = 1
    status: str
    total_fee: float = 0.0
    actual_fee: float = 0.0
    payment_status: str
    payment_method: Optional[str] = None
    cancel_reason: Optional[str] = None
    cancelled_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ==================== API Endpoints ====================

# --- 会议室管理 ---


@router.get("/rooms", response_model=dict)
def get_meeting_rooms(
    page: int = Query(1, description="页码"),
    limit: int = Query(20, description="每页数量"),
    is_active: Optional[bool] = Query(None, description="激活状态过滤"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取会议室列表"""
    query = db.query(MeetingRoom)

    if is_active is not None:
        query = query.filter(MeetingRoom.is_active == is_active)

    total = query.count()
    rooms = query.offset((page - 1) * limit).limit(limit).all()

    items = []
    for room in rooms:
        items.append(
            {
                "id": room.id,
                "name": room.name,
                "location": room.location,
                "capacity": room.capacity,
                "price_per_hour": room.price_per_hour,
                "member_price_per_hour": room.member_price_per_hour,
                "is_active": room.is_active,
            }
        )

    return {
        "items": items,
        "total": total,
        "page": page,
        "limit": limit,
        "pages": (total + limit - 1) // limit,
    }


@router.post("/rooms", response_model=MeetingRoomResponse)
def create_meeting_room(
    room: MeetingRoomCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    """创建会议室（仅管理员）"""
    db_room = MeetingRoom(**room.model_dump())
    db.add(db_room)
    db.commit()
    db.refresh(db_room)
    return db_room


@router.get("/rooms/{room_id}", response_model=MeetingRoomResponse)
def get_meeting_room(
    room_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取会议室详情"""
    room = db.query(MeetingRoom).filter(MeetingRoom.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="会议室不存在")
    return room


@router.put("/rooms/{room_id}", response_model=MeetingRoomResponse)
def update_meeting_room(
    room_id: int,
    room_update: MeetingRoomUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    """更新会议室信息（仅管理员）"""
    room = db.query(MeetingRoom).filter(MeetingRoom.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="会议室不存在")

    update_data = room_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        if hasattr(room, key):
            setattr(room, key, value)

    db.commit()
    db.refresh(room)
    return room


@router.delete("/rooms/{room_id}")
def delete_meeting_room(
    room_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    """删除会议室（仅管理员）"""
    room = db.query(MeetingRoom).filter(MeetingRoom.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="会议室不存在")

    db.delete(room)
    db.commit()
    return {"message": "会议室已删除"}


# --- 预约管理 ---


@router.get("/bookings", response_model=dict)
def get_bookings(
    page: int = Query(1, description="页码"),
    limit: int = Query(20, description="每页数量"),
    room_id: Optional[int] = Query(None, description="会议室ID过滤"),
    user_type: Optional[str] = Query(None, description="用户类型过滤"),
    status: Optional[str] = Query(None, description="状态过滤"),
    q: Optional[str] = Query(None, description="全局搜索关键词"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取预约列表"""

    # 如果用户未登录，抛出401错误
    if not current_user:
        raise HTTPException(status_code=401, detail="未登录或token已过期")

    query = db.query(MeetingBooking)

    if room_id:
        query = query.filter(MeetingBooking.room_id == room_id)
    if user_type:
        query = query.filter(MeetingBooking.user_type == user_type)
    if status:
        query = query.filter(MeetingBooking.status == status)
    if q:
        query = query.filter(
            MeetingBooking.meeting_title.contains(q)
            | MeetingBooking.user_name.contains(q)
        )

    # 普通用户只能查看自己的预约
    if current_user.role not in ["admin", "super_admin"]:
        query = query.filter(MeetingBooking.user_name == current_user.username)

    total = query.count()
    bookings = (
        query.order_by(MeetingBooking.created_at.desc())
        .offset((page - 1) * limit)
        .limit(limit)
        .all()
    )

    items = []
    for booking in bookings:
        items.append(
            {
                "id": booking.id,
                "booking_no": booking.booking_no,
                "room_id": booking.room_id,
                "room_name": booking.room_name,
                "user_name": booking.user_name,
                "booking_date": booking.booking_date.isoformat()
                if booking.booking_date
                else None,
                "start_time": booking.start_time,
                "end_time": booking.end_time,
                "meeting_title": booking.meeting_title,
                "status": booking.status,
                "total_fee": booking.total_fee,
            }
        )

    return {
        "items": items,
        "total": total,
        "page": page,
        "limit": limit,
        "pages": (total + limit - 1) // limit,
    }


@router.post("/bookings", response_model=MeetingBookingResponse)
def create_booking(
    booking: MeetingBookingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """创建预约"""
    import random
    from datetime import datetime as dt

    # 检查会议室是否存在
    room = db.query(MeetingRoom).filter(MeetingRoom.id == booking.room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="会议室不存在")

    # 检查时间格式并解析
    try:
        start_time_obj = dt.strptime(booking.start_time, "%H:%M").time()
        end_time_obj = dt.strptime(booking.end_time, "%H:%M").time()
    except ValueError:
        raise HTTPException(status_code=400, detail="时间格式错误，请使用 HH:MM 格式")

    if start_time_obj >= end_time_obj:
        raise HTTPException(status_code=400, detail="结束时间必须晚于开始时间")

    # 检查该时间段是否有冲突
    conflicting = (
        db.query(MeetingBooking)
        .filter(
            MeetingBooking.room_id == booking.room_id,
            MeetingBooking.booking_date == booking.booking_date,
            MeetingBooking.status.in_(
                [BookingStatus.confirmed.value, BookingStatus.pending.value]
            ),
        )
        .all()
    )

    for existing in conflicting:
        try:
            existing_start = dt.strptime(existing.start_time, "%H:%M").time()
            existing_end = dt.strptime(existing.end_time, "%H:%M").time()
        except ValueError:
            continue

        if not (end_time_obj <= existing_start or start_time_obj >= existing_end):
            raise HTTPException(status_code=400, detail="该时间段已被预约")

    # 计算时长和费用
    start_dt = dt.combine(booking.booking_date, start_time_obj)
    end_dt = dt.combine(booking.booking_date, end_time_obj)
    duration = (end_dt - start_dt).total_seconds() / 3600
    price = room.price_per_hour

    # 生成预约号
    booking_no = (
        f"MB{datetime.now().strftime('%Y%m%d%H%M%S')}{random.randint(1000, 9999)}"
    )

    # 构建booking数据
    booking_data = booking.model_dump()
    booking_data["booking_no"] = booking_no
    booking_data["duration"] = duration
    booking_data["total_fee"] = duration * price
    booking_data["actual_fee"] = duration * price
    booking_data["status"] = BookingStatus.pending.value
    booking_data["user_id"] = current_user.id if current_user else None
    booking_data["payment_status"] = "unpaid"
    booking_data["room_name"] = room.name

    db_booking = MeetingBooking(**booking_data)

    db.add(db_booking)
    db.commit()
    db.refresh(db_booking)

    return db_booking


@router.get("/bookings/{booking_id}", response_model=MeetingBookingResponse)
def get_booking(
    booking_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取预约详情"""

    if not current_user:
        raise HTTPException(status_code=401, detail="未登录或token已过期")

    booking = db.query(MeetingBooking).filter(MeetingBooking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="预约不存在")

    # 权限检查：普通用户只能查看自己的预约
    if (
        current_user.role not in ["admin", "super_admin"]
        and booking.user_id != current_user.id
    ):
        raise HTTPException(status_code=403, detail="无权限查看此预约")

    if booking.room:
        booking.room_name = booking.room.name

    return booking


@router.put("/bookings/{booking_id}/cancel")
def cancel_booking(
    booking_id: int,
    reason: Optional[str] = Query(None, description="取消原因"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """取消预约"""

    if not current_user:
        raise HTTPException(status_code=401, detail="未登录或token已过期")

    booking = db.query(MeetingBooking).filter(MeetingBooking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="预约不存在")

    # 权限检查：普通用户只能取消自己的预约
    if (
        current_user.role not in ["admin", "super_admin"]
        and booking.user_id != current_user.id
    ):
        raise HTTPException(status_code=403, detail="无权限取消此预约")

    if booking.status in [BookingStatus.cancelled.value, BookingStatus.completed.value]:
        raise HTTPException(status_code=400, detail="预约状态不允许取消")

    booking.status = BookingStatus.cancelled.value
    booking.cancelled_at = datetime.now()
    booking.cancel_reason = reason

    db.commit()
    return {"message": "预约已取消"}


@router.put("/bookings/{booking_id}", response_model=MeetingBookingResponse)
def update_booking(
    booking_id: int,
    booking_update: MeetingBookingUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """修改预约信息（时间、人数、主题等）"""
    import random
    from datetime import datetime as dt

    if not current_user:
        raise HTTPException(status_code=401, detail="未登录或token已过期")

    booking = db.query(MeetingBooking).filter(MeetingBooking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="预约不存在")

    # 权限检查：普通用户只能修改自己的预约
    if (
        current_user.role not in ["admin", "super_admin"]
        and booking.user_id != current_user.id
    ):
        raise HTTPException(status_code=403, detail="无权限修改此预约")

    # 检查预约状态（只能修改待审批或已确认的预约）
    if booking.status not in [
        BookingStatus.pending.value,
        BookingStatus.confirmed.value,
    ]:
        raise HTTPException(status_code=400, detail="该预约状态不允许修改")

    # 获取修改数据
    update_data = booking_update.model_dump(exclude_unset=True)

    # 如果修改了时间，需要重新验证和冲突检测
    if (
        "start_time" in update_data
        or "end_time" in update_data
        or "booking_date" in update_data
    ):
        new_start_time = update_data.get("start_time", booking.start_time)
        new_end_time = update_data.get("end_time", booking.end_time)
        new_booking_date = update_data.get("booking_date", booking.booking_date)

        # 检查时间格式并解析
        try:
            start_time_obj = dt.strptime(new_start_time, "%H:%M").time()
            end_time_obj = dt.strptime(new_end_time, "%H:%M").time()
        except ValueError:
            raise HTTPException(
                status_code=400, detail="时间格式错误，请使用 HH:MM 格式"
            )

        if start_time_obj >= end_time_obj:
            raise HTTPException(status_code=400, detail="结束时间必须晚于开始时间")

        # 检查时长范围（30分钟-8小时）
        start_dt = dt.combine(new_booking_date, start_time_obj)
        end_dt = dt.combine(new_booking_date, end_time_obj)
        duration = (end_dt - start_dt).total_seconds() / 3600

        if duration < 0.5:
            raise HTTPException(status_code=400, detail="预约时长最少30分钟")
        if duration > 8:
            raise HTTPException(status_code=400, detail="预约时长最多8小时")

        # 检查该时间段是否有冲突（排除当前预约）
        conflicting = (
            db.query(MeetingBooking)
            .filter(
                MeetingBooking.room_id == booking.room_id,
                MeetingBooking.booking_date == new_booking_date,
                MeetingBooking.id != booking_id,
                MeetingBooking.status.in_(
                    [BookingStatus.confirmed.value, BookingStatus.pending.value]
                ),
            )
            .all()
        )

        for existing in conflicting:
            try:
                existing_start = dt.strptime(existing.start_time, "%H:%M").time()
                existing_end = dt.strptime(existing.end_time, "%H:%M").time()
            except ValueError:
                continue

            if not (end_time_obj <= existing_start or start_time_obj >= existing_end):
                raise HTTPException(status_code=400, detail="该时间段已被预约")

        # 更新时长和费用
        room = db.query(MeetingRoom).filter(MeetingRoom.id == booking.room_id).first()
        price = room.price_per_hour if room else 0

        update_data["duration"] = duration
        update_data["total_fee"] = duration * price
        update_data["actual_fee"] = duration * price

    # 验证参会人数
    if "attendees_count" in update_data:
        if update_data["attendees_count"] <= 0:
            raise HTTPException(status_code=400, detail="参会人数必须大于0")

        room = db.query(MeetingRoom).filter(MeetingRoom.id == booking.room_id).first()
        if room and update_data["attendees_count"] > room.capacity:
            raise HTTPException(
                status_code=400,
                detail=f"参会人数超出会议室容量（最大{room.capacity}人）",
            )

    # 应用修改
    for key, value in update_data.items():
        if hasattr(booking, key):
            setattr(booking, key, value)

    db.commit()
    db.refresh(booking)

    return booking


@router.put("/bookings/{booking_id}/approve")
def approve_booking(
    booking_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    """审批预约（仅管理员）"""
    booking = db.query(MeetingBooking).filter(MeetingBooking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="预约不存在")

    if booking.status != BookingStatus.pending.value:
        raise HTTPException(status_code=400, detail="只能审批待审批的预约")

    booking.status = BookingStatus.confirmed.value
    booking.payment_status = "confirmed"

    db.commit()
    return {"message": "预约已审批通过", "booking_id": booking_id}


@router.get("/rooms/{room_id}/availability")
def check_room_availability(
    room_id: int,
    date: date,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """检查会议室可用时间段"""
    room = db.query(MeetingRoom).filter(MeetingRoom.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="会议室不存在")

    # 获取当天的所有预约
    bookings = (
        db.query(MeetingBooking)
        .filter(
            MeetingBooking.room_id == room_id,
            MeetingBooking.booking_date == date,
            MeetingBooking.status.in_(
                [BookingStatus.confirmed.value, BookingStatus.pending.value]
            ),
        )
        .order_by(MeetingBooking.start_time)
        .all()
    )

    # 计算可用时间段
    booked_slots = [(b.start_time, b.end_time) for b in bookings]

    return {
        "room_id": room_id,
        "room_name": room.name,
        "date": date.isoformat(),
        "booked_slots": booked_slots,
        "bookings_count": len(bookings),
    }
