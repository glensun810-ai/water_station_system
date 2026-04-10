"""会议室审批和支付API路由"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime, date
from typing import List, Optional
from pydantic import BaseModel
import random

from config.database import get_db
from models.approval import MeetingApproval, MeetingPayment
from models.booking import MeetingBooking, BookingStatus
from models.meeting import MeetingRoom

router = APIRouter(prefix="/api/meeting", tags=["会议室审批和支付"])


# ==================== Pydantic Schemas ====================


class ApprovalCreate(BaseModel):
    booking_id: int
    approver_id: int
    approver_name: str
    notes: Optional[str] = None


class ApprovalResponse(BaseModel):
    id: int
    approval_no: str
    booking_id: int
    approver_id: int
    approver_name: str
    status: str
    notes: Optional[str] = None
    approved_at: Optional[datetime] = None
    rejected_at: Optional[datetime] = None
    reject_reason: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class PaymentCreate(BaseModel):
    booking_id: int
    user_id: int
    user_name: str
    amount: float
    payment_method: str  # cash/credit_card/wechat/alipay
    notes: Optional[str] = None


class PaymentResponse(BaseModel):
    id: int
    payment_no: str
    booking_id: int
    user_id: int
    user_name: str
    amount: float
    payment_method: str
    payment_status: str
    paid_at: Optional[datetime] = None
    transaction_id: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ==================== 审批API ====================


@router.get("/approvals", response_model=List[ApprovalResponse])
def get_approvals(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """获取审批列表"""
    query = db.query(MeetingApproval)

    if status:
        query = query.filter(MeetingApproval.status == status)

    approvals = (
        query.order_by(MeetingApproval.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return approvals


@router.post("/approval/submit", response_model=ApprovalResponse)
def submit_approval(approval: ApprovalCreate, db: Session = Depends(get_db)):
    """提交审批"""
    # 检查预约是否存在
    booking = (
        db.query(MeetingBooking)
        .filter(MeetingBooking.id == approval.booking_id)
        .first()
    )
    if not booking:
        raise HTTPException(status_code=404, detail="预约不存在")

    # 检查是否已经有审批记录
    existing = (
        db.query(MeetingApproval)
        .filter(MeetingApproval.booking_id == approval.booking_id)
        .first()
    )
    if existing:
        raise HTTPException(status_code=400, detail="该预约已有审批记录")

    # 生成审批号
    approval_no = (
        f"AP{datetime.now().strftime('%Y%m%d%H%M%S')}{random.randint(1000, 9999)}"
    )

    db_approval = MeetingApproval(
        approval_no=approval_no,
        booking_id=approval.booking_id,
        approver_id=approval.approver_id,
        approver_name=approval.approver_name,
        notes=approval.notes,
        status="pending",
    )

    db.add(db_approval)
    db.commit()
    db.refresh(db_approval)

    return db_approval


@router.get("/approval/{approval_id}", response_model=ApprovalResponse)
def get_approval(approval_id: int, db: Session = Depends(get_db)):
    """获取审批详情"""
    approval = (
        db.query(MeetingApproval).filter(MeetingApproval.id == approval_id).first()
    )
    if not approval:
        raise HTTPException(status_code=404, detail="审批记录不存在")
    return approval


@router.post("/approval/approve", response_model=ApprovalResponse)
def approve_approval(
    approval_id: int,
    approver_id: int,
    approver_name: str,
    db: Session = Depends(get_db),
):
    """审批通过"""
    approval = (
        db.query(MeetingApproval).filter(MeetingApproval.id == approval_id).first()
    )
    if not approval:
        raise HTTPException(status_code=404, detail="审批记录不存在")

    if approval.status != "pending":
        raise HTTPException(status_code=400, detail="审批状态不允许操作")

    approval.status = "approved"
    approval.approved_at = datetime.now()
    approval.approver_id = approver_id
    approval.approver_name = approver_name

    # 更新预约状态
    booking = (
        db.query(MeetingBooking)
        .filter(MeetingBooking.id == approval.booking_id)
        .first()
    )
    if booking:
        booking.status = BookingStatus.confirmed.value

    db.commit()
    db.refresh(approval)

    return approval


@router.post("/approval/batch-approve")
def batch_approve(
    approval_ids: List[int],
    approver_id: int,
    approver_name: str,
    db: Session = Depends(get_db),
):
    """批量审批"""
    approved_count = 0

    for approval_id in approval_ids:
        approval = (
            db.query(MeetingApproval).filter(MeetingApproval.id == approval_id).first()
        )
        if approval and approval.status == "pending":
            approval.status = "approved"
            approval.approved_at = datetime.now()
            approval.approver_id = approver_id
            approval.approver_name = approver_name

            # 更新预约状态
            booking = (
                db.query(MeetingBooking)
                .filter(MeetingBooking.id == approval.booking_id)
                .first()
            )
            if booking:
                booking.status = BookingStatus.confirmed.value

            approved_count += 1

    db.commit()

    return {
        "approved_count": approved_count,
        "message": f"成功审批 {approved_count} 条记录",
    }


# ==================== 支付API ====================


@router.get("/payments", response_model=List[PaymentResponse])
def get_payments(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    user_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    """获取支付记录列表"""
    query = db.query(MeetingPayment)

    if status:
        query = query.filter(MeetingPayment.payment_status == status)
    if user_id:
        query = query.filter(MeetingPayment.user_id == user_id)

    payments = (
        query.order_by(MeetingPayment.created_at.desc()).offset(skip).limit(limit).all()
    )
    return payments


@router.post("/payment/submit", response_model=PaymentResponse)
def submit_payment(payment: PaymentCreate, db: Session = Depends(get_db)):
    """提交支付"""
    # 检查预约是否存在
    booking = (
        db.query(MeetingBooking).filter(MeetingBooking.id == payment.booking_id).first()
    )
    if not booking:
        raise HTTPException(status_code=404, detail="预约不存在")

    # 生成支付号
    payment_no = (
        f"PAY{datetime.now().strftime('%Y%m%d%H%M%S')}{random.randint(1000, 9999)}"
    )

    db_payment = MeetingPayment(
        payment_no=payment_no,
        booking_id=payment.booking_id,
        user_id=payment.user_id,
        user_name=payment.user_name,
        amount=payment.amount,
        payment_method=payment.payment_method,
        payment_status="unpaid",
        notes=payment.notes,
    )

    db.add(db_payment)
    db.commit()
    db.refresh(db_payment)

    return db_payment


@router.post("/payment/confirm")
def confirm_payment(
    payment_id: int,
    transaction_id: str,
    db: Session = Depends(get_db),
):
    """确认支付"""
    payment = db.query(MeetingPayment).filter(MeetingPayment.id == payment_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="支付记录不存在")

    if payment.payment_status != "unpaid":
        raise HTTPException(status_code=400, detail="支付状态不允许操作")

    payment.payment_status = "paid"
    payment.paid_at = datetime.now()
    payment.transaction_id = transaction_id

    # 更新预约支付状态
    booking = (
        db.query(MeetingBooking).filter(MeetingBooking.id == payment.booking_id).first()
    )
    if booking:
        booking.payment_status = "paid"

    db.commit()

    return {"message": "支付确认成功"}


@router.post("/payment/batch-confirm")
def batch_confirm_payment(
    payment_ids: List[int],
    db: Session = Depends(get_db),
):
    """批量确认支付"""
    confirmed_count = 0

    for payment_id in payment_ids:
        payment = (
            db.query(MeetingPayment).filter(MeetingPayment.id == payment_id).first()
        )
        if payment and payment.payment_status == "unpaid":
            payment.payment_status = "paid"
            payment.paid_at = datetime.now()
            payment.transaction_id = f"TXN{datetime.now().strftime('%Y%m%d%H%M%S')}{random.randint(1000, 9999)}"

            # 更新预约支付状态
            booking = (
                db.query(MeetingBooking)
                .filter(MeetingBooking.id == payment.booking_id)
                .first()
            )
            if booking:
                booking.payment_status = "paid"

            confirmed_count += 1

    db.commit()

    return {
        "confirmed_count": confirmed_count,
        "message": f"成功确认 {confirmed_count} 条支付记录",
    }


@router.get("/settlement/{batch_id}")
def get_settlement(batch_id: str, db: Session = Depends(get_db)):
    """获取结算详情"""
    # 这里batch_id可以是booking_id或payment_id
    payment = (
        db.query(MeetingPayment).filter(MeetingPayment.payment_no == batch_id).first()
    )

    if not payment:
        raise HTTPException(status_code=404, detail="结算记录不存在")

    booking = (
        db.query(MeetingBooking).filter(MeetingBooking.id == payment.booking_id).first()
    )

    result = {
        "payment": {
            "id": payment.id,
            "payment_no": payment.payment_no,
            "amount": payment.amount,
            "payment_status": payment.payment_status,
            "paid_at": payment.paid_at.isoformat() if payment.paid_at else None,
        },
        "booking": {
            "id": booking.id,
            "booking_no": booking.booking_no,
            "status": booking.status,
            "total_fee": booking.total_fee,
        }
        if booking
        else None,
    }

    return result


@router.get("/settlements")
def get_settlements(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """获取结算列表"""
    query = db.query(MeetingPayment)

    if status:
        query = query.filter(MeetingPayment.payment_status == status)

    payments = (
        query.order_by(MeetingPayment.created_at.desc()).offset(skip).limit(limit).all()
    )

    result = []
    for payment in payments:
        booking = (
            db.query(MeetingBooking)
            .filter(MeetingBooking.id == payment.booking_id)
            .first()
        )

        result.append(
            {
                "payment_no": payment.payment_no,
                "amount": payment.amount,
                "payment_status": payment.payment_status,
                "paid_at": payment.paid_at.isoformat() if payment.paid_at else None,
                "booking_no": booking.booking_no if booking else None,
                "user_name": payment.user_name,
            }
        )

    return result


@router.post("/settlement/create")
def create_settlement(
    booking_id: int,
    user_id: int,
    user_name: str,
    db: Session = Depends(get_db),
):
    """创建结算（支付请求）"""
    booking = db.query(MeetingBooking).filter(MeetingBooking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="预约不存在")

    # 检查是否已有支付记录
    existing = (
        db.query(MeetingPayment).filter(MeetingPayment.booking_id == booking_id).first()
    )
    if existing:
        raise HTTPException(status_code=400, detail="该预约已有支付记录")

    # 创建支付记录
    payment_no = (
        f"PAY{datetime.now().strftime('%Y%m%d%H%M%S')}{random.randint(1000, 9999)}"
    )

    db_payment = MeetingPayment(
        payment_no=payment_no,
        booking_id=booking_id,
        user_id=user_id,
        user_name=user_name,
        amount=booking.total_fee,
        payment_method="wechat",  # 默认微信支付
        payment_status="unpaid",
    )

    db.add(db_payment)
    db.commit()
    db.refresh(db_payment)

    return {
        "payment_no": payment_no,
        "amount": booking.total_fee,
        "message": "结算创建成功",
    }
