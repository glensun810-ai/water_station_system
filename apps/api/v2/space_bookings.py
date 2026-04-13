"""
空间预约管理API路由
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import date, datetime
from typing import Optional, List
from datetime import datetime as dt
import random

from config.database import get_db
from models.user import User
from depends.auth import get_current_user_required, get_admin_user
from shared.models.space.space_booking import SpaceBooking, BookingStatus
from shared.models.space.space_resource import SpaceResource
from shared.models.space.space_type import SpaceType
from shared.schemas.space.space_booking import (
    SpaceBookingCreate,
    SpaceBookingUpdate,
    SpaceBookingCancel,
    SpaceBookingResponse,
    FeeCalculationRequest,
    FeeCalculationResponse,
)
from shared.schemas.space.response import ApiResponse, PaginatedResponse

router = APIRouter(prefix="/space/bookings", tags=["空间预约管理"])


@router.get("", response_model=ApiResponse)
async def get_bookings(
    type_code: Optional[str] = Query(None, description="空间类型代码过滤"),
    status: Optional[str] = Query(None, description="状态过滤"),
    booking_date: Optional[date] = Query(None, description="预约日期过滤"),
    date_from: Optional[date] = Query(None, description="日期范围开始"),
    date_to: Optional[date] = Query(None, description="日期范围结束"),
    q: Optional[str] = Query(None, description="关键词搜索"),
    page: int = Query(1, ge=1, description="页码"),
    limit: int = Query(20, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_required),
):
    """获取预约列表"""

    query = db.query(SpaceBooking).filter(SpaceBooking.is_deleted == 0)

    if type_code:
        query = query.filter(SpaceBooking.type_code == type_code)
    if status:
        query = query.filter(SpaceBooking.status == status)
    if booking_date:
        query = query.filter(SpaceBooking.booking_date == booking_date)
    if date_from:
        query = query.filter(SpaceBooking.booking_date >= date_from)
    if date_to:
        query = query.filter(SpaceBooking.booking_date <= date_to)
    if q:
        query = query.filter(
            SpaceBooking.title.contains(q) | SpaceBooking.user_name.contains(q)
        )

    if current_user.role not in ["admin", "super_admin", "space_manager"]:
        query = query.filter(SpaceBooking.user_id == current_user.id)

    total = query.count()
    bookings = (
        query.order_by(SpaceBooking.created_at.desc())
        .offset((page - 1) * limit)
        .limit(limit)
        .all()
    )

    items = [_format_booking(b, db) for b in bookings]

    return ApiResponse(
        data=PaginatedResponse(
            items=items,
            total=total,
            page=page,
            limit=limit,
            pages=(total + limit - 1) // limit,
        )
    )


@router.get("/my", response_model=ApiResponse)
async def get_my_bookings(
    status: Optional[str] = Query(None, description="状态过滤"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_required),
):
    """获取我的预约列表"""

    query = db.query(SpaceBooking).filter(
        SpaceBooking.user_id == current_user.id, SpaceBooking.is_deleted == 0
    )

    if status:
        query = query.filter(SpaceBooking.status == status)

    total = query.count()
    bookings = (
        query.order_by(SpaceBooking.created_at.desc())
        .offset((page - 1) * limit)
        .limit(limit)
        .all()
    )

    items = [_format_booking(b, db) for b in bookings]

    return ApiResponse(
        data=PaginatedResponse(
            items=items,
            total=total,
            page=page,
            limit=limit,
            pages=(total + limit - 1) // limit,
        )
    )


@router.get("/{booking_id}", response_model=ApiResponse)
async def get_booking(
    booking_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_required),
):
    """获取预约详情"""

    booking = (
        db.query(SpaceBooking)
        .filter(SpaceBooking.id == booking_id, SpaceBooking.is_deleted == 0)
        .first()
    )

    if not booking:
        raise HTTPException(status_code=404, detail="预约不存在")

    if current_user.role not in ["admin", "super_admin", "space_manager"]:
        if booking.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="无权限查看此预约")

    return ApiResponse(data=_format_booking(booking, db))


@router.post("", response_model=ApiResponse)
async def create_booking(
    booking_data: SpaceBookingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_required),
):
    """创建预约"""

    resource = (
        db.query(SpaceResource)
        .filter(SpaceResource.id == booking_data.resource_id)
        .first()
    )
    if not resource:
        raise HTTPException(status_code=404, detail="空间资源不存在")

    space_type = db.query(SpaceType).filter(SpaceType.id == resource.type_id).first()

    try:
        start_dt = dt.strptime(booking_data.start_time, "%H:%M")
        end_dt = dt.strptime(booking_data.end_time, "%H:%M")
    except ValueError:
        raise HTTPException(status_code=400, detail="时间格式错误")

    if start_dt >= end_dt:
        raise HTTPException(status_code=400, detail="结束时间必须晚于开始时间")

    conflicting = (
        db.query(SpaceBooking)
        .filter(
            SpaceBooking.resource_id == booking_data.resource_id,
            SpaceBooking.booking_date == booking_data.booking_date,
            SpaceBooking.status.in_(
                ["pending_approval", "approved", "confirmed", "in_use", "completed"]
            ),
        )
        .all()
    )

    for existing in conflicting:
        try:
            existing_start = dt.strptime(existing.start_time, "%H:%M")
            existing_end = dt.strptime(existing.end_time, "%H:%M")
        except ValueError:
            continue

        if not (end_dt <= existing_start or start_dt >= existing_end):
            raise HTTPException(
                status_code=400,
                detail=f"时间段 {booking_data.start_time}-{booking_data.end_time} 已被预约",
            )

    duration = (end_dt - start_dt).seconds / 3600
    total_fee = duration * resource.base_price

    booking_no = (
        f"SB{datetime.now().strftime('%Y%m%d%H%M%S')}{random.randint(1000, 9999)}"
    )

    initial_status = (
        "pending_approval"
        if space_type and space_type.requires_approval
        else "confirmed"
    )

    booking = SpaceBooking(
        **booking_data.model_dump(exclude={"type_code", "end_date", "booking_days"}),
        booking_no=booking_no,
        duration=duration,
        duration_unit=space_type.min_duration_unit if space_type else "hour",
        type_id=resource.type_id,
        type_code=space_type.type_code if space_type else None,
        resource_name=resource.name,
        user_id=current_user.id,
        total_fee=total_fee,
        actual_fee=total_fee,
        base_fee=total_fee,
        requires_deposit=space_type.requires_deposit if space_type else False,
        deposit_amount=total_fee * (space_type.deposit_percentage if space_type else 0),
        status=initial_status,
        payment_status="unpaid",
        settlement_status="unsettled",
        confirmed_at=datetime.now() if initial_status == "confirmed" else None,
        confirmed_by="system" if initial_status == "confirmed" else None,
    )

    db.add(booking)
    db.flush()

    if initial_status == "pending_approval":
        from shared.models.space.space_approval import SpaceApproval

        approval_no = (
            f"SA{datetime.now().strftime('%Y%m%d%H%M%S')}{random.randint(1000, 9999)}"
        )

        approval = SpaceApproval(
            approval_no=approval_no,
            booking_id=booking.id,
            booking_no=booking.booking_no,
            approval_type="booking_approval",
            approval_stage="initial",
            approval_content=f"空间预约审批：{booking.title}",
            status="pending",
            submitted_at=datetime.now(),
        )

        db.add(approval)
        booking.approval_id = approval.id

    db.commit()
    db.refresh(booking)

    return ApiResponse(
        code=201, message="预约创建成功", data=_format_booking(booking, db)
    )


@router.put("/{booking_id}", response_model=ApiResponse)
async def update_booking(
    booking_id: int,
    booking_data: SpaceBookingUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_required),
):
    """修改预约"""

    booking = (
        db.query(SpaceBooking)
        .filter(SpaceBooking.id == booking_id, SpaceBooking.is_deleted == 0)
        .first()
    )

    if not booking:
        raise HTTPException(status_code=404, detail="预约不存在")

    if current_user.role not in ["admin", "super_admin"]:
        if booking.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="无权限修改此预约")

    if not booking.can_modify:
        raise HTTPException(status_code=400, detail="此预约不可修改")

    if booking.status not in ["pending_approval", "approved", "confirmed"]:
        raise HTTPException(status_code=400, detail="预约状态不允许修改")

    update_data = booking_data.model_dump(exclude_unset=True)

    if "start_time" in update_data or "end_time" in update_data:
        new_start = update_data.get("start_time", booking.start_time)
        new_end = update_data.get("end_time", booking.end_time)

        try:
            start_dt = dt.strptime(new_start, "%H:%M")
            end_dt = dt.strptime(new_end, "%H:%M")
        except ValueError:
            raise HTTPException(status_code=400, detail="时间格式错误")

        if start_dt >= end_dt:
            raise HTTPException(status_code=400, detail="结束时间必须晚于开始时间")

        conflicting = (
            db.query(SpaceBooking)
            .filter(
                SpaceBooking.resource_id == booking.resource_id,
                SpaceBooking.booking_date == booking.booking_date,
                SpaceBooking.status.in_(
                    ["pending_approval", "approved", "confirmed", "in_use"]
                ),
                SpaceBooking.id != booking_id,
            )
            .all()
        )

        for existing in conflicting:
            try:
                existing_start = dt.strptime(existing.start_time, "%H:%M")
                existing_end = dt.strptime(existing.end_time, "%H:%M")
            except ValueError:
                continue

            if not (end_dt <= existing_start or start_dt >= existing_end):
                raise HTTPException(status_code=400, detail="时间段已被预约")

        duration = (end_dt - start_dt).seconds / 3600
        booking.duration = duration
        booking.total_fee = (
            duration * booking.base_fee / booking.duration if booking.duration else 0
        )
        booking.actual_fee = booking.total_fee

    for key, value in update_data.items():
        if hasattr(booking, key):
            setattr(booking, key, value)

    db.commit()
    db.refresh(booking)

    return ApiResponse(message="预约修改成功", data=_format_booking(booking, db))


@router.put("/{booking_id}/cancel", response_model=ApiResponse)
async def cancel_booking(
    booking_id: int,
    cancel_data: SpaceBookingCancel,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_required),
):
    """取消预约"""

    booking = (
        db.query(SpaceBooking)
        .filter(SpaceBooking.id == booking_id, SpaceBooking.is_deleted == 0)
        .first()
    )

    if not booking:
        raise HTTPException(status_code=404, detail="预约不存在")

    if current_user.role not in ["admin", "super_admin"]:
        if booking.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="无权限取消此预约")

    if not booking.can_cancel:
        raise HTTPException(status_code=400, detail="此预约不可取消")

    if booking.status in ["cancelled", "completed", "rejected"]:
        raise HTTPException(status_code=400, detail="预约状态不允许取消")

    booking.status = "cancelled"
    booking.cancelled_at = datetime.now()
    booking.cancelled_by = current_user.name
    booking.cancel_reason = cancel_data.cancel_reason
    booking.cancel_type = cancel_data.cancel_type

    if booking.deposit_paid and not booking.deposit_refunded:
        booking.deposit_refund_amount = booking.deposit_amount
        booking.deposit_refunded = True
        booking.deposit_refund_at = datetime.now()

    db.commit()

    return ApiResponse(message="预约已取消", data=_format_booking(booking, db))


@router.put("/{booking_id}/approve", response_model=ApiResponse)
async def approve_booking(
    booking_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    """审批预约（管理员）"""

    booking = (
        db.query(SpaceBooking)
        .filter(SpaceBooking.id == booking_id, SpaceBooking.is_deleted == 0)
        .first()
    )

    if not booking:
        raise HTTPException(status_code=404, detail="预约不存在")

    if booking.status != "pending_approval":
        raise HTTPException(status_code=400, detail="只能审批待审批的预约")

    booking.status = "approved"
    booking.approved_by = current_user.name
    booking.approved_at = datetime.now()

    db.commit()
    db.refresh(booking)

    return ApiResponse(message="预约审批通过", data=_format_booking(booking, db))


@router.put("/{booking_id}/complete", response_model=ApiResponse)
async def complete_booking(
    booking_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    """完成预约（管理员）"""

    booking = (
        db.query(SpaceBooking)
        .filter(SpaceBooking.id == booking_id, SpaceBooking.is_deleted == 0)
        .first()
    )

    if not booking:
        raise HTTPException(status_code=404, detail="预约不存在")

    if booking.status not in ["approved", "confirmed", "in_use"]:
        raise HTTPException(status_code=400, detail="只能完成已审批/确认/使用中的预约")

    booking.status = "completed"
    booking.completed_at = datetime.now()
    booking.completed_by = current_user.name

    db.commit()
    db.refresh(booking)

    return ApiResponse(message="预约已完成", data=_format_booking(booking, db))


@router.delete("/{booking_id}", response_model=ApiResponse)
async def delete_booking(
    booking_id: int,
    delete_reason: Optional[str] = Query(None, description="删除原因"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    """删除预约（软删除，仅管理员）"""

    booking = db.query(SpaceBooking).filter(SpaceBooking.id == booking_id).first()

    if not booking:
        raise HTTPException(status_code=404, detail="预约不存在")

    booking.is_deleted = 1
    booking.deleted_at = datetime.now()
    booking.deleted_by = current_user.name
    booking.delete_reason = delete_reason

    db.commit()

    return ApiResponse(message="预约已删除")


@router.post("/calculate-fee", response_model=ApiResponse)
async def calculate_fee(
    fee_request: FeeCalculationRequest,
    db: Session = Depends(get_db),
):
    """计算费用"""

    resource = (
        db.query(SpaceResource)
        .filter(SpaceResource.id == fee_request.resource_id)
        .first()
    )
    if not resource:
        raise HTTPException(status_code=404, detail="空间资源不存在")

    try:
        start_dt = dt.strptime(fee_request.start_time, "%H:%M")
        end_dt = dt.strptime(fee_request.end_time, "%H:%M")
    except ValueError:
        raise HTTPException(status_code=400, detail="时间格式错误")

    duration = fee_request.duration or (end_dt - start_dt).seconds / 3600

    base_fee = duration * resource.base_price

    member_discount = 0
    if fee_request.member_level == "vip":
        member_discount = base_fee * 0.2
    elif fee_request.member_level == "enterprise":
        member_discount = base_fee * 0.3

    addon_fee = 0
    addon_items = []
    if fee_request.addons_selected:
        for addon in fee_request.addons_selected:
            addon_fee += addon.get("price", 0) * addon.get("quantity", 1)
            addon_items.append(
                {
                    "addon_code": addon.get("code"),
                    "quantity": addon.get("quantity", 1),
                    "subtotal": addon.get("price", 0) * addon.get("quantity", 1),
                }
            )

    subtotal = base_fee + addon_fee
    discount_total = member_discount
    final_fee = subtotal - discount_total

    deposit_info = {"requires_deposit": False, "deposit_amount": 0}

    space_type = db.query(SpaceType).filter(SpaceType.id == resource.type_id).first()
    if space_type and space_type.requires_deposit:
        deposit_info = {
            "requires_deposit": True,
            "deposit_amount": final_fee * space_type.deposit_percentage,
            "deposit_percentage": space_type.deposit_percentage,
        }

    return ApiResponse(
        data=FeeCalculationResponse(
            calculation_detail={
                "base_fee": {
                    "units": duration,
                    "price_per_unit": resource.base_price,
                    "subtotal": base_fee,
                },
                "member_discount": {
                    "member_level": fee_request.member_level,
                    "discount_amount": member_discount,
                },
                "addon_fee": {"items": addon_items, "subtotal": addon_fee},
            },
            fee_summary={
                "base_fee": base_fee,
                "addon_fee": addon_fee,
                "subtotal": subtotal,
                "discount_total": discount_total,
                "final_fee": final_fee,
            },
            deposit_info=deposit_info,
            payment_methods=["wechat", "alipay", "internal_account"],
        )
    )


def _format_booking(booking: SpaceBooking, db: Session) -> dict:
    """格式化预约数据"""

    resource = (
        db.query(SpaceResource).filter(SpaceResource.id == booking.resource_id).first()
    )
    space_type = (
        db.query(SpaceType).filter(SpaceType.id == booking.type_id).first()
        if booking.type_id
        else None
    )

    return {
        "id": booking.id,
        "booking_no": booking.booking_no,
        "resource_id": booking.resource_id,
        "resource_name": booking.resource_name or (resource.name if resource else None),
        "type_code": booking.type_code
        or (space_type.type_code if space_type else None),
        "type_name": space_type.type_name if space_type else None,
        "user_id": booking.user_id,
        "user_type": booking.user_type,
        "user_name": booking.user_name,
        "user_phone": booking.user_phone,
        "user_email": booking.user_email,
        "department": booking.department,
        "booking_date": booking.booking_date.isoformat(),
        "start_time": booking.start_time,
        "end_time": booking.end_time,
        "duration": booking.duration,
        "title": booking.title,
        "attendees_count": booking.attendees_count,
        "total_fee": booking.total_fee,
        "actual_fee": booking.actual_fee,
        "requires_deposit": booking.requires_deposit,
        "deposit_amount": booking.deposit_amount,
        "deposit_paid": booking.deposit_paid,
        "status": booking.status,
        "payment_status": booking.payment_status,
        "approved_by": booking.approved_by,
        "approved_at": booking.approved_at.isoformat() if booking.approved_at else None,
        "rejected_reason": booking.rejected_reason,
        "rejected_at": booking.rejected_at.isoformat() if booking.rejected_at else None,
        "confirmed_at": booking.confirmed_at.isoformat()
        if booking.confirmed_at
        else None,
        "cancelled_at": booking.cancelled_at.isoformat()
        if booking.cancelled_at
        else None,
        "cancelled_by": booking.cancelled_by,
        "cancel_reason": booking.cancel_reason,
        "can_modify": booking.can_modify,
        "can_cancel": booking.can_cancel,
        "created_at": booking.created_at.isoformat(),
        "updated_at": booking.updated_at.isoformat(),
    }
