"""
空间预约管理API路由
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import date, datetime
from typing import Optional, List
from datetime import datetime as dt
from decimal import Decimal
import random

from config.database import get_db
from models.user import User
from depends.auth import get_current_user_required, get_admactiver, get_super_admactiver
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
    BatchOperationRequest,
    BatchOperationResult,
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
    payment_mode: Optional[str] = Query(
        "credit",
        description="支付模式: credit(记账)/balance_deduct(余额抵扣)/prepay(预付)",
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_required),
):
    """创建预约

    支付模式说明：
    - credit（记账模式）：内部员工默认模式，使用后结算，月底统一账单
    - balance_deduct（余额抵扣）：有余额时可选择，实时从账户扣款
    - prepay（预付模式）：外部访客必须，使用前线下付费
    """

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
                ["pending", "approved", "confirmed", "active", "completed"]
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

    user_type = current_user.user_type or "internal"

    deduct_amount = Decimal("0")
    credit_amount = Decimal("0")

    if user_type == "internal":
        from models.user_balance import UserBalanceAccount

        balance_account = (
            db.query(UserBalanceAccount)
            .filter(UserBalanceAccount.user_id == current_user.id)
            .first()
        )

        available_balance = Decimal(
            str(balance_account.total_balance if balance_account else 0)
        )

        if available_balance >= Decimal(str(total_fee)):
            deduct_amount = Decimal(str(total_fee))
            credit_amount = Decimal("0")
            payment_mode = "balance_deduct"
            payment_status = "deducted"
            approval_notes = "内部员工预约，余额全额抵扣，自动审批通过"
        elif available_balance > Decimal("0"):
            deduct_amount = available_balance
            credit_amount = Decimal(str(total_fee)) - available_balance
            payment_mode = "mixed"
            payment_status = "partial_deducted"
            approval_notes = f"内部员工预约，余额抵扣¥{deduct_amount:.2f}+记账¥{credit_amount:.2f}，自动审批通过"
        else:
            deduct_amount = Decimal("0")
            credit_amount = Decimal(str(total_fee))
            payment_mode = "credit"
            payment_status = "credit"
            approval_notes = "内部员工预约，全记账模式，自动审批通过"

        initial_status = "approved"
        approved_at = datetime.now()
        approved_by = "system_auto"

    else:
        if payment_mode != "prepay":
            raise HTTPException(
                status_code=400,
                detail="外部访客必须使用预付模式，请线下付费后由管理员确认",
            )

        initial_status = "pending"
        approved_at = None
        approved_by = None
        approval_notes = None
        payment_status = "pending"
        deduct_amount = Decimal("0")
        credit_amount = Decimal("0")

    if space_type and space_type.requires_approval:
        initial_status = "pending"
        approved_at = None
        approved_by = None
        approval_notes = (
            None
            if user_type == "external"
            else f"内部员工预约高价值空间，需人工审批。支付：{payment_mode}"
        )
        if user_type == "internal":
            payment_status = "pending"

    booking = SpaceBooking(
        **booking_data.model_dump(
            exclude={
                "type_code",
                "end_date",
                "booking_days",
                "user_type",
                "duration_hours",
                "user_name",
                "user_phone",
                "user_email",
                "department",
                "office_id",
                "meal_session",
                "meal_standard",
                "guests_count",
                "content_type",
                "content_url",
                "exhibition_type",
                "exhibition_plan_url",
            }
        ),
        booking_no=booking_no,
        duration=duration,
        duration_unit=space_type.min_duration_unit if space_type else "hour",
        type_id=resource.type_id,
        type_code=space_type.type_code if space_type else None,
        resource_name=resource.name,
        user_id=current_user.id,
        user_type=user_type,
        user_name=current_user.name or current_user.username,
        user_phone=current_user.phone,
        user_email=current_user.email,
        department=current_user.department,
        total_fee=total_fee,
        actual_fee=total_fee,
        base_fee=total_fee,
        requires_deposit=space_type.requires_deposit if space_type else False,
        deposit_amount=total_fee
        * (space_type.deposit_percentage / 100 if space_type else 0),
        status=initial_status,
        payment_status=payment_status,
        payment_mode=payment_mode,
        deduct_amount=float(deduct_amount),
        credit_amount=float(credit_amount),
        approved_at=approved_at,
        approved_by=approved_by,
        approval_notes=approval_notes,
    )

    db.add(booking)
    db.flush()

    if deduct_amount > Decimal("0"):
        from models.user_balance import (
            UserBalanceAccount,
            BalanceTransaction,
            BalanceDeductRecord,
            TransactionType,
            BalanceType,
        )

        balance_account = (
            db.query(UserBalanceAccount)
            .filter(UserBalanceAccount.user_id == current_user.id)
            .first()
        )

        if balance_account:
            deduct_no = f"DD{datetime.now().strftime('%Y%m%d%H%M%S')}{random.randint(1000, 9999)}"

            deduct_record = BalanceDeductRecord(
                deduct_no=deduct_no,
                user_id=current_user.id,
                order_type="space_booking",
                order_id=booking.id,
                order_no=booking.booking_no,
                total_amount=float(deduct_amount),
                membership_deduct=min(
                    Decimal(str(balance_account.membership_balance)),
                    deduct_amount,
                ),
                service_deduct=min(
                    Decimal(str(balance_account.service_balance)),
                    deduct_amount
                    - min(
                        Decimal(str(balance_account.membership_balance)),
                        deduct_amount,
                    ),
                ),
                gift_deduct=0,
                cash_amount=0,
                description=f"空间预约余额抵扣：{booking.resource_name} {booking.booking_date}（抵扣¥{deduct_amount:.2f}）",
            )
            db.add(deduct_record)

            membership_deduct = min(
                Decimal(str(balance_account.membership_balance)),
                deduct_amount,
            )
            remaining = deduct_amount - membership_deduct
            service_deduct = min(
                Decimal(str(balance_account.service_balance)), remaining
            )

            balance_account.membership_balance -= membership_deduct
            balance_account.service_balance -= service_deduct
            balance_account.total_deducted += deduct_amount
            balance_account.update_total_balance()
            balance_account.last_transaction_at = datetime.now()

            booking.deduct_record_id = deduct_record.id

            if membership_deduct > 0:
                tx = BalanceTransaction(
                    transaction_no=f"TX{datetime.now().strftime('%Y%m%d%H%M%S%f')}",
                    user_id=current_user.id,
                    transaction_type=TransactionType.DEDUCT,
                    amount=-membership_deduct,
                    balance_type=BalanceType.MEMBERSHIP,
                    before_membership_balance=balance_account.membership_balance
                    + membership_deduct,
                    before_total_balance=balance_account.total_balance
                    + membership_deduct,
                    after_membership_balance=balance_account.membership_balance,
                    after_total_balance=balance_account.total_balance,
                    reference_type="space_booking",
                    reference_id=booking.id,
                    reference_no=booking.booking_no,
                    description=f"空间预约抵扣（会员余额）：{booking.resource_name}",
                )
                db.add(tx)

            if service_deduct > 0:
                tx2 = BalanceTransaction(
                    transaction_no=f"TX{datetime.now().strftime('%Y%m%d%H%M%S%f')}{random.randint(100, 999)}",
                    user_id=current_user.id,
                    transaction_type=TransactionType.DEDUCT,
                    amount=-service_deduct,
                    balance_type=BalanceType.SERVICE,
                    before_service_balance=balance_account.service_balance
                    + service_deduct,
                    before_total_balance=balance_account.total_balance + service_deduct,
                    after_service_balance=balance_account.service_balance,
                    after_total_balance=balance_account.total_balance,
                    reference_type="space_booking",
                    reference_id=booking.id,
                    reference_no=booking.booking_no,
                    description=f"空间预约抵扣（服务余额）：{booking.resource_name}",
                )
                db.add(tx2)

    if initial_status == "pending":
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

    payment_mode_text = {
        "credit": "记账模式（使用后结算）",
        "balance_deduct": "余额抵扣（已全额扣款）",
        "mixed": "混合支付（余额抵扣+记账）",
        "prepay": "预付模式（待线下支付）",
    }

    if payment_mode == "balance_deduct":
        message = f"预约创建成功！费用 ¥{total_fee:.2f} 已从账户余额全额扣除。"
    elif payment_mode == "mixed":
        message = f"预约创建成功！费用 ¥{total_fee:.2f}，其中 ¥{deduct_amount:.2f} 已从余额扣除，¥{credit_amount:.2f} 记账待结算。"
    elif payment_mode == "credit":
        message = f"预约创建成功！费用 ¥{total_fee:.2f} 已记账，将在使用后结算，月度账单统一处理。"
    elif initial_status == "pending":
        message = f"预约创建成功！等待管理员审批和支付确认。"
    else:
        message = f"预约创建成功，已自动审批通过。"

    return ApiResponse(code=201, message=message, data=_format_booking(booking, db))


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

    if booking.status not in ["pending", "approved", "confirmed"]:
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
                SpaceBooking.status.in_(["pending", "approved", "confirmed", "active"]),
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


@router.put("/{booking_id}/confirm", response_model=ApiResponse)
async def confirm_booking(
    booking_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admactiver),
):
    """确认预约生效（管理员）- 将预约从 approved 标记为 confirmed"""

    booking = (
        db.query(SpaceBooking)
        .filter(SpaceBooking.id == booking_id, SpaceBooking.is_deleted == 0)
        .first()
    )

    if not booking:
        raise HTTPException(status_code=404, detail="预约不存在")

    if booking.status != "approved":
        raise HTTPException(
            status_code=400, detail=f"只能确认已批准的预约，当前状态为 {booking.status}"
        )

    if booking.payment_status == "pending":
        raise HTTPException(
            status_code=400, detail="支付状态仍为待支付，请先确认收款后再确认生效"
        )

    booking.status = "confirmed"
    booking.confirmed_at = datetime.now()
    booking.confirmed_by = current_user.name

    db.commit()
    db.refresh(booking)

    return ApiResponse(
        message="预约已确认生效，预约正式生效", data=_format_booking(booking, db)
    )


@router.put("/{booking_id}/activate", response_model=ApiResponse)
async def activate_booking(
    booking_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admactiver),
):
    """标记开始使用（管理员）- 将预约从 confirmed 标记为 active"""

    booking = (
        db.query(SpaceBooking)
        .filter(SpaceBooking.id == booking_id, SpaceBooking.is_deleted == 0)
        .first()
    )

    if not booking:
        raise HTTPException(status_code=404, detail="预约不存在")

    if booking.status != "confirmed":
        raise HTTPException(
            status_code=400, detail=f"只能激活已确认的预约，当前状态为 {booking.status}"
        )

    booking.status = "active"
    booking.activated_at = datetime.now()
    booking.activated_by = current_user.name

    db.commit()
    db.refresh(booking)

    return ApiResponse(message="预约已标记为进行中", data=_format_booking(booking, db))


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
    current_user: User = Depends(get_admactiver),
):
    """审批预约（管理员）"""

    booking = (
        db.query(SpaceBooking)
        .filter(SpaceBooking.id == booking_id, SpaceBooking.is_deleted == 0)
        .first()
    )

    if not booking:
        raise HTTPException(status_code=404, detail="预约不存在")

    if booking.status != "pending":
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
    current_user: User = Depends(get_admactiver),
):
    """完成预约（管理员）"""

    booking = (
        db.query(SpaceBooking)
        .filter(SpaceBooking.id == booking_id, SpaceBooking.is_deleted == 0)
        .first()
    )

    if not booking:
        raise HTTPException(status_code=404, detail="预约不存在")

    if booking.status not in ["approved", "confirmed", "active"]:
        raise HTTPException(status_code=400, detail="只能完成已审批/确认/使用中的预约")

    booking.status = "completed"
    booking.completed_at = datetime.now()
    booking.completed_by = current_user.name

    db.commit()
    db.refresh(booking)

    return ApiResponse(message="预约已完成", data=_format_booking(booking, db))


@router.put("/{booking_id}/settle", response_model=ApiResponse)
async def settle_booking(
    booking_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admactiver),
):
    """确认结算（管理员）- 将预约状态从completed改为settled"""

    booking = db.query(SpaceBooking).filter(SpaceBooking.id == booking_id).first()

    if not booking:
        raise HTTPException(status_code=404, detail="预约不存在")

    if booking.status != "completed":
        raise HTTPException(status_code=400, detail="只能结算已完成的预约")

    booking.status = "settled"
    booking.settlement_status = "settled"
    booking.settled_at = datetime.now()
    booking.settled_by = current_user.name

    db.commit()
    db.refresh(booking)

    return ApiResponse(message="结算确认成功", data=_format_booking(booking, db))


@router.put("/{booking_id}/unsettle", response_model=ApiResponse)
async def unsettle_booking(
    booking_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admactiver),
):
    """取消结算（管理员）- 将预约状态从settled改回completed"""

    booking = db.query(SpaceBooking).filter(SpaceBooking.id == booking_id).first()

    if not booking:
        raise HTTPException(status_code=404, detail="预约不存在")

    if booking.status != "settled":
        raise HTTPException(status_code=400, detail="只能取消已结算的预约")

    booking.status = "completed"
    booking.settlement_status = "unsettled"
    booking.settled_at = None
    booking.settled_by = None

    db.commit()
    db.refresh(booking)

    return ApiResponse(message="取消结算成功", data=_format_booking(booking, db))


@router.delete("/{booking_id}", response_model=ApiResponse)
async def delete_booking(
    booking_id: int,
    delete_reason: Optional[str] = Query(None, description="删除原因"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_super_admactiver),
):
    """删除预约（软删除，仅超级管理员）"""

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


@router.post("/batch-operation", response_model=ApiResponse)
async def batch_operation(
    batch_data: BatchOperationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admactiver),
):
    """批量操作预约"""

    if batch_data.operation == "delete":
        if current_user.role != "super_admin":
            raise HTTPException(status_code=403, detail="批量删除仅超级管理员可用")

    total = len(batch_data.booking_ids)
    success_ids = []
    failed_items = []

    for booking_id in batch_data.booking_ids:
        try:
            booking = (
                db.query(SpaceBooking).filter(SpaceBooking.id == booking_id).first()
            )

            if not booking:
                failed_items.append({"id": booking_id, "error": "预约不存在"})
                continue

            if batch_data.operation == "delete":
                if booking.is_deleted == 1:
                    failed_items.append({"id": booking_id, "error": "预约已删除"})
                    continue

                booking.is_deleted = 1
                booking.deleted_at = datetime.now()
                booking.deleted_by = current_user.name
                booking.delete_reason = batch_data.reason or "批量删除"

            elif batch_data.operation == "approve":
                if booking.status != "pending":
                    failed_items.append(
                        {"id": booking_id, "error": f"状态为{booking.status}，无法审批"}
                    )
                    continue

                booking.status = "approved"
                booking.approved_by = current_user.name
                booking.approved_at = datetime.now()

            elif batch_data.operation == "cancel":
                if booking.status in ["cancelled", "completed", "rejected"]:
                    failed_items.append(
                        {"id": booking_id, "error": f"状态为{booking.status}，无法取消"}
                    )
                    continue

                booking.status = "cancelled"
                booking.cancelled_at = datetime.now()
                booking.cancelled_by = current_user.name
                booking.cancel_reason = batch_data.reason or "批量取消"

            elif batch_data.operation == "complete":
                if booking.status not in ["approved", "confirmed", "active"]:
                    failed_items.append(
                        {"id": booking_id, "error": f"状态为{booking.status}，无法完成"}
                    )
                    continue

                booking.status = "completed"
                booking.completed_at = datetime.now()
                booking.completed_by = current_user.name

            success_ids.append(booking_id)

        except Exception as e:
            failed_items.append({"id": booking_id, "error": str(e)})

    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"批量操作失败: {str(e)}")

    success_count = len(success_ids)
    failed_count = len(failed_items)

    result_message = f"批量操作完成：成功{success_count}条，失败{failed_count}条"

    return ApiResponse(
        message=result_message,
        data=BatchOperationResult(
            total=total,
            success_count=success_count,
            failed_count=failed_count,
            success_ids=success_ids,
            failed_items=failed_items,
            message=result_message,
        ),
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
        "payment_mode": booking.payment_mode,
        "deduct_amount": booking.deduct_amount,
        "credit_amount": booking.credit_amount,
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


@router.put("/{booking_id}/approve-with-payment", response_model=ApiResponse)
async def approve_booking_with_payment(
    booking_id: int,
    payment_method: str = Query(
        "offline_cash", description="支付方式: offline_cash/offline_transfer/etc"
    ),
    payment_notes: Optional[str] = Query(None, description="收款备注"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admactiver),
):
    """
    管理员审批预约并确认收款（一步完成）

    适用场景：外部访客预约
    - 预约状态：pending → approved
    - 支付状态：pending → paid
    - 同时记录收款信息

    注意：仅适用于pending状态的预约
    """

    booking = db.query(SpaceBooking).filter(SpaceBooking.id == booking_id).first()

    if not booking:
        raise HTTPException(status_code=404, detail="预约不存在")

    if booking.status != "pending":
        raise HTTPException(
            status_code=400,
            detail="只能审批pending状态的预约。当前状态：" + booking.status,
        )

    # 检查时段是否仍有冲突（审批前再次确认）
    try:
        start_dt = dt.strptime(booking.start_time, "%H:%M")
        end_dt = dt.strptime(booking.end_time, "%H:%M")
    except ValueError:
        raise HTTPException(status_code=400, detail="预约时间格式错误")

    conflicting = (
        db.query(SpaceBooking)
        .filter(
            SpaceBooking.resource_id == booking.resource_id,
            SpaceBooking.booking_date == booking.booking_date,
            SpaceBooking.status.in_(["approved", "confirmed", "active"]),
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
            raise HTTPException(
                status_code=400,
                detail=f"时段冲突：{booking.start_time}-{booking.end_time} 已被其他已批准的预约占用",
            )

    # 更新预约状态
    booking.status = "approved"
    booking.approved_at = datetime.now()
    booking.approved_by = current_user.name
    booking.approval_notes = payment_notes or "管理员确认收款并审批通过"

    # 更新支付状态
    if booking.total_fee and booking.total_fee > 0:
        booking.payment_status = "paid"
        booking.deposit_paid = True
        booking.deposit_paid_at = datetime.now()
        booking.deposit_payment_method = payment_method

    # 创建支付记录
    from shared.models.space.space_payment import SpacePayment
    import random

    payment_no = (
        f"SP{datetime.now().strftime('%Y%m%d%H%M%S')}{random.randint(1000, 9999)}"
    )

    payment = SpacePayment(
        payment_no=payment_no,
        booking_id=booking_id,
        booking_no=booking.booking_no,
        user_id=booking.user_id,
        user_name=booking.user_name,
        payment_type="full",
        payment_purpose="管理员确认收款",
        amount=booking.actual_fee or booking.total_fee or 0,
        currency="CNY",
        payment_method=payment_method,
        payment_channel="offline",
        status="completed",
        initiated_at=datetime.now(),
        completed_at=datetime.now(),
        verified_by=current_user.name,
        verified_at=datetime.now(),
        verification_notes=payment_notes or "管理员线下确认收款",
    )

    db.add(payment)

    # 更新审批记录（如果存在）
    if booking.approval_id:
        from shared.models.space.space_approval import SpaceApproval

        approval = (
            db.query(SpaceApproval)
            .filter(SpaceApproval.id == booking.approval_id)
            .first()
        )
        if approval:
            approval.status = "approved"
            approval.result = "approved"
            approval.approved_at = datetime.now()
            approval.approver_id = current_user.id
            approval.approver_name = current_user.name
            approval.approval_notes = payment_notes or "管理员确认收款并审批通过"

    db.commit()
    db.refresh(booking)

    return ApiResponse(
        message="审批成功并已确认收款",
        data={
            "booking_id": booking_id,
            "booking_no": booking.booking_no,
            "status": booking.status,
            "payment_status": booking.payment_status,
            "approved_at": booking.approved_at.isoformat(),
            "approved_by": booking.approved_by,
            "amount": payment.amount,
            "payment_method": payment_method,
        },
    )
