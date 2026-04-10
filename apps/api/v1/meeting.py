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
from depends.auth import get_current_user, get_admin_user, get_current_user_required

router = APIRouter(prefix="/meeting", tags=["会议室服务"])


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
    current_user: User = Depends(get_current_user_required),
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
    current_user: User = Depends(get_current_user_required),
):
    """获取预约列表"""
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
