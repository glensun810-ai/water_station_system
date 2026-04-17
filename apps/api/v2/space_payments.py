"""
空间支付管理API路由
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional, List
import random

from config.database import get_db
from models.user import User
from depends.auth import get_admin_user, get_current_user_required
from shared.models.space.space_payment import SpacePayment
from shared.models.space.space_booking import SpaceBooking
from shared.schemas.space.space_payment import (
    SpacePaymentCreate,
    SpacePaymentConfirm,
    SpacePaymentVerify,
    SpacePaymentRefund,
    SpacePaymentResponse,
)
from shared.schemas.space.response import ApiResponse, PaginatedResponse

router = APIRouter(prefix="/space/payments", tags=["空间支付管理"])


@router.post("/confirm-offline", response_model=ApiResponse)
async def confirm_offline_payment(
    booking_id: int = Query(..., description="预约ID"),
    payment_method: str = Query("offline", description="支付方式"),
    payment_notes: Optional[str] = Query(None, description="支付备注"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_required),
):
    """用户确认线下支付完成（通知管理员审核）"""

    booking = db.query(SpaceBooking).filter(SpaceBooking.id == booking_id).first()

    if not booking:
        raise HTTPException(status_code=404, detail="预约不存在")

    if booking.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="只能确认自己的预约支付")

    if booking.status not in ["approved", "pending"]:
        raise HTTPException(status_code=400, detail="预约状态不允许支付确认")

    payment_no = (
        f"SP{datetime.now().strftime('%Y%m%d%H%M%S')}{random.randint(1000, 9999)}"
    )

    payment = SpacePayment(
        payment_no=payment_no,
        booking_id=booking_id,
        booking_no=booking.booking_no,
        user_id=current_user.id,
        user_name=current_user.name,
        payment_type="full",
        payment_purpose="预约全款支付",
        amount=booking.actual_fee or 0,
        currency="CNY",
        payment_method=payment_method,
        payment_channel="offline",
        status="pending_verification",
        initiated_at=datetime.now(),
        notes=payment_notes or "用户确认线下支付完成，等待管理员审核",
    )

    db.add(payment)

    booking.payment_status = "pending_verification"
    booking.user_payment_confirmed = True
    booking.user_payment_confirmed_at = datetime.now()

    db.commit()
    db.refresh(payment)

    return ApiResponse(
        message="支付确认已提交，管理员将审核收款后确认预约生效",
        data={
            "payment_id": payment.id,
            "payment_no": payment.payment_no,
            "booking_id": booking_id,
            "booking_no": booking.booking_no,
            "status": "pending_verification",
            "amount": payment.amount,
            "message": "请等待管理员确认收款，确认后预约将生效",
        },
    )


@router.get("", response_model=ApiResponse)
async def get_payments(
    status: Optional[str] = Query(None, description="支付状态过滤"),
    payment_type: Optional[str] = Query(None, description="支付类型过滤"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    """获取支付记录列表（管理员）"""

    query = db.query(SpacePayment)

    if status:
        query = query.filter(SpacePayment.status == status)
    if payment_type:
        query = query.filter(SpacePayment.payment_type == payment_type)

    total = query.count()
    payments = (
        query.order_by(SpacePayment.created_at.desc())
        .offset((page - 1) * limit)
        .limit(limit)
        .all()
    )

    items = [_format_payment(p) for p in payments]

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
async def get_my_payments(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_required),
):
    """获取我的支付记录"""

    query = db.query(SpacePayment).filter(SpacePayment.user_id == current_user.id)

    total = query.count()
    payments = (
        query.order_by(SpacePayment.created_at.desc())
        .offset((page - 1) * limit)
        .limit(limit)
        .all()
    )

    items = [_format_payment(p) for p in payments]

    return ApiResponse(
        data=PaginatedResponse(
            items=items,
            total=total,
            page=page,
            limit=limit,
            pages=(total + limit - 1) // limit,
        )
    )


@router.get("/pending", response_model=ApiResponse)
async def get_pending_payments(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    """获取待支付列表"""

    query = db.query(SpacePayment).filter(SpacePayment.status == "pending")

    total = query.count()
    payments = (
        query.order_by(SpacePayment.initiated_at.asc())
        .offset((page - 1) * limit)
        .limit(limit)
        .all()
    )

    items = [_format_payment(p) for p in payments]

    return ApiResponse(
        data=PaginatedResponse(
            items=items,
            total=total,
            page=page,
            limit=limit,
            pages=(total + limit - 1) // limit,
        )
    )


@router.get("/{payment_id}", response_model=ApiResponse)
async def get_payment(
    payment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_required),
):
    """获取支付详情"""

    payment = db.query(SpacePayment).filter(SpacePayment.id == payment_id).first()

    if not payment:
        raise HTTPException(status_code=404, detail="支付记录不存在")

    if current_user.role not in ["admin", "super_admin", "finance_staff"]:
        if payment.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="无权限查看此支付记录")

    return ApiResponse(data=_format_payment(payment))


@router.post("", response_model=ApiResponse)
async def create_payment(
    payment_data: SpacePaymentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_required),
):
    """创建支付记录"""

    booking = (
        db.query(SpaceBooking)
        .filter(SpaceBooking.id == payment_data.booking_id)
        .first()
    )
    if not booking:
        raise HTTPException(status_code=404, detail="预约不存在")

    payment_no = (
        f"SP{datetime.now().strftime('%Y%m%d%H%M%S')}{random.randint(1000, 9999)}"
    )

    payment = SpacePayment(
        **payment_data.model_dump(),
        payment_no=payment_no,
        booking_no=booking.booking_no,
        user_id=current_user.id,
        user_name=current_user.name,
        initiated_at=datetime.now(),
    )

    db.add(payment)
    db.commit()
    db.refresh(payment)

    return ApiResponse(
        code=201, message="支付记录创建成功", data=_format_payment(payment)
    )


@router.post("/{payment_id}/confirm", response_model=ApiResponse)
async def confirm_payment(
    payment_id: int,
    confirm_data: SpacePaymentConfirm,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_required),
):
    """确认支付"""

    payment = db.query(SpacePayment).filter(SpacePayment.id == payment_id).first()

    if not payment:
        raise HTTPException(status_code=404, detail="支付记录不存在")

    if payment.status != "pending":
        raise HTTPException(status_code=400, detail="支付状态不允许确认")

    payment.status = "success"
    payment.completed_at = datetime.now()
    payment.transaction_id = confirm_data.transaction_id
    payment.receipt_url = confirm_data.receipt_url
    payment.proof_url = confirm_data.proof_url
    payment.notes = confirm_data.notes

    booking = (
        db.query(SpaceBooking).filter(SpaceBooking.id == payment.booking_id).first()
    )
    if booking:
        if payment.payment_type == "deposit":
            booking.deposit_paid = True
            booking.deposit_paid_at = datetime.now()
            booking.deposit_payment_method = payment.payment_method
            booking.status = "deposit_paid"
        elif payment.payment_type == "balance":
            booking.balance_paid = True
            booking.balance_paid_at = datetime.now()
            booking.balance_payment_method = payment.payment_method
            booking.status = "confirmed"
        elif payment.payment_type == "full":
            booking.status = "confirmed"
            booking.confirmed_at = datetime.now()
            booking.confirmed_by = current_user.name

    db.commit()

    return ApiResponse(message="支付确认成功", data=_format_payment(payment))


@router.post("/{payment_id}/verify", response_model=ApiResponse)
async def verify_payment(
    payment_id: int,
    verify_data: SpacePaymentVerify,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    """审核支付（线下支付审核）- 管理员确认收款后自动审批预约"""

    payment = db.query(SpacePayment).filter(SpacePayment.id == payment_id).first()

    if not payment:
        raise HTTPException(status_code=404, detail="支付记录不存在")

    if payment.status not in ["pending", "pending_verification"]:
        raise HTTPException(status_code=400, detail="支付状态不允许审核")

    payment.status = "success"
    payment.completed_at = datetime.now()
    payment.verified_by = verify_data.verified_by or current_user.name
    payment.verified_at = datetime.now()
    payment.verification_notes = verify_data.verification_notes

    booking = (
        db.query(SpaceBooking).filter(SpaceBooking.id == payment.booking_id).first()
    )
    if booking:
        booking.payment_status = "paid"
        booking.admin_payment_verified = True
        booking.admin_payment_verified_at = datetime.now()
        booking.admin_payment_verified_by = current_user.name

        if booking.status == "pending":
            booking.status = "approved"
            booking.approved_by = current_user.name
            booking.approved_at = datetime.now()
            booking.approval_notes = "支付已确认，自动审批通过"
        elif booking.status == "approved":
            booking.status = "confirmed"
            booking.confirmed_at = datetime.now()
            booking.confirmed_by = current_user.name

        if payment.payment_type == "deposit":
            booking.deposit_paid = True
            booking.deposit_paid_at = datetime.now()
            booking.status = "deposit_paid"
        elif payment.payment_type == "full":
            booking.status = "confirmed"
            booking.confirmed_at = datetime.now()
            booking.confirmed_by = current_user.name

    db.commit()

    return ApiResponse(
        message="支付审核成功，预约已自动审批通过并生效",
        data={
            "payment": _format_payment(payment),
            "booking_status": booking.status if booking else None,
            "booking_confirmed": booking.status == "confirmed" if booking else False,
        },
    )


@router.post("/{payment_id}/refund", response_model=ApiResponse)
async def refund_payment(
    payment_id: int,
    refund_data: SpacePaymentRefund,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    """申请退款"""

    payment = db.query(SpacePayment).filter(SpacePayment.id == payment_id).first()

    if not payment:
        raise HTTPException(status_code=404, detail="支付记录不存在")

    if payment.status != "success":
        raise HTTPException(status_code=400, detail="只能退款已完成的支付")

    refund_amount = refund_data.refund_amount or payment.amount

    payment.status = "refunded"
    payment.refunded_at = datetime.now()
    payment.refund_amount = refund_amount
    payment.refund_reason = refund_data.refund_reason
    payment.refund_status = "completed"

    booking = (
        db.query(SpaceBooking).filter(SpaceBooking.id == payment.booking_id).first()
    )
    if booking:
        if payment.payment_type == "deposit":
            booking.deposit_refunded = True
            booking.deposit_refund_amount = refund_amount
            booking.deposit_refund_at = datetime.now()

    db.commit()

    return ApiResponse(message="退款申请成功", data=_format_payment(payment))


def _format_payment(payment: SpacePayment) -> dict:
    """格式化支付数据"""

    return {
        "id": payment.id,
        "payment_no": payment.payment_no,
        "booking_id": payment.booking_id,
        "booking_no": payment.booking_no,
        "user_id": payment.user_id,
        "user_name": payment.user_name,
        "payment_type": payment.payment_type,
        "payment_purpose": payment.payment_purpose,
        "amount": payment.amount,
        "currency": payment.currency,
        "payment_method": payment.payment_method,
        "payment_channel": payment.payment_channel,
        "status": payment.status,
        "initiated_at": payment.initiated_at.isoformat(),
        "completed_at": payment.completed_at.isoformat()
        if payment.completed_at
        else None,
        "transaction_id": payment.transaction_id,
        "receipt_url": payment.receipt_url,
        "proof_url": payment.proof_url,
        "verified_by": payment.verified_by,
        "verified_at": payment.verified_at.isoformat() if payment.verified_at else None,
        "refund_amount": payment.refund_amount,
        "refund_reason": payment.refund_reason,
        "created_at": payment.created_at.isoformat(),
        "updated_at": payment.updated_at.isoformat(),
    }
