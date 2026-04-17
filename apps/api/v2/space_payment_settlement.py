"""
空间预约支付结算API路由
支持：记账模式、余额抵扣模式、预付模式
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime, date
from decimal import Decimal
import random

from config.database import get_db
from models.user import User
from models.user_balance import (
    UserBalanceAccount,
    BalanceTransaction,
    BalanceDeductRecord,
    TransactionType,
    BalanceType,
)
from models.credit_note import CreditNote, CreditNoteItem
from shared.models.space.space_booking import SpaceBooking
from depends.auth import get_current_user_required, get_admactiver

router = APIRouter(prefix="/space/payment", tags=["空间支付结算"])


class PaymentModeInfo(BaseModel):
    user_id: int
    user_type: str
    available_balance: float
    payment_modes: List[dict]
    recommended_mode: str
    booking_fee: float


class BalanceDeductRequest(BaseModel):
    booking_id: int
    use_membership: bool = True
    use_service: bool = True
    use_gift: bool = True


class BalanceDeductResponse(BaseModel):
    success: bool
    deduct_no: str
    total_amount: float
    membership_deduct: float
    service_deduct: float
    gift_deduct: float
    cash_amount: float
    remaining_balance: float


class CreditNoteResponse(BaseModel):
    id: int
    note_no: str
    user_name: str
    department: str
    month: str
    total_amount: float
    paid_amount: float
    booking_count: int
    status: str
    items: List[dict]

    class Config:
        from_attributes = True


class MonthlySettlementRequest(BaseModel):
    month: str = Field(..., description="结算月份，如 2026-04")
    user_id: Optional[int] = Field(None, description="指定用户ID，不填则处理全部")


@router.get("/modes/{booking_id}", response_model=dict)
async def get_payment_modes(
    booking_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_required),
):
    """获取预约的可用支付模式"""

    booking = db.query(SpaceBooking).filter(SpaceBooking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="预约不存在")

    if booking.user_id != current_user.id and current_user.role not in [
        "admin",
        "super_admin",
    ]:
        raise HTTPException(status_code=403, detail="无权限查看此预约")

    user_type = current_user.user_type or "internal"
    fee = float(booking.total_fee or booking.actual_fee or 0)

    payment_modes = []

    if user_type == "internal":
        balance_account = (
            db.query(UserBalanceAccount)
            .filter(UserBalanceAccount.user_id == current_user.id)
            .first()
        )

        available_balance = 0.0
        if balance_account:
            available = balance_account.get_available_balance()
            available_balance = available["total"]

        payment_modes.append(
            {
                "mode": "credit",
                "name": "记账模式",
                "description": "使用后结算，月底统一账单",
                "available": True,
                "balance_required": 0,
            }
        )

        if available_balance > 0:
            payment_modes.append(
                {
                    "mode": "balance_deduct",
                    "name": "余额抵扣",
                    "description": f"使用账户余额支付，可用余额 ¥{available_balance:.2f}",
                    "available": available_balance >= fee,
                    "balance_required": fee,
                    "available_balance": available_balance,
                }
            )

        recommended_mode = "balance_deduct" if available_balance >= fee else "credit"

    else:
        payment_modes.append(
            {
                "mode": "prepay",
                "name": "线下预付",
                "description": "使用前需线下付费",
                "available": True,
                "balance_required": fee,
            }
        )
        recommended_mode = "prepay"

    return {
        "user_id": current_user.id,
        "user_type": user_type,
        "available_balance": available_balance if user_type == "internal" else 0,
        "payment_modes": payment_modes,
        "recommended_mode": recommended_mode,
        "booking_fee": fee,
    }


@router.post("/deduct", response_model=BalanceDeductResponse)
async def deduct_balance(
    deduct_request: BalanceDeductRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_required),
):
    """余额抵扣扣款"""

    booking = (
        db.query(SpaceBooking)
        .filter(SpaceBooking.id == deduct_request.booking_id)
        .first()
    )
    if not booking:
        raise HTTPException(status_code=404, detail="预约不存在")

    if booking.user_id != current_user.id and current_user.role not in [
        "admin",
        "super_admin",
    ]:
        raise HTTPException(status_code=403, detail="无权限操作此预约")

    if booking.payment_status in ["paid", "deducted"]:
        raise HTTPException(status_code=400, detail="此预约已支付，无需重复扣款")

    total_fee = Decimal(str(booking.total_fee or booking.actual_fee or 0))

    balance_account = (
        db.query(UserBalanceAccount)
        .filter(UserBalanceAccount.user_id == booking.user_id)
        .first()
    )

    if not balance_account:
        raise HTTPException(status_code=400, detail="用户余额账户不存在，请先充值")

    available = balance_account.get_available_balance()

    membership_available = (
        Decimal(str(available["membership"]))
        if deduct_request.use_membership
        else Decimal("0")
    )
    service_available = (
        Decimal(str(available["service"]))
        if deduct_request.use_service
        else Decimal("0")
    )
    gift_available = (
        Decimal(str(available["gift"])) if deduct_request.use_gift else Decimal("0")
    )

    total_available = membership_available + service_available + gift_available

    if total_available < total_fee:
        raise HTTPException(
            status_code=400,
            detail=f"余额不足。需要 ¥{total_fee:.2f}，可用余额 ¥{total_available:.2f}",
        )

    membership_deduct = min(membership_available, total_fee)
    remaining = total_fee - membership_deduct
    service_deduct = min(service_available, remaining)
    remaining = remaining - service_deduct
    gift_deduct = min(gift_available, remaining)

    deduct_no = (
        f"DD{datetime.now().strftime('%Y%m%d%H%M%S')}{random.randint(1000, 9999)}"
    )

    deduct_record = BalanceDeductRecord(
        deduct_no=deduct_no,
        user_id=booking.user_id,
        order_type="space_booking",
        order_id=booking.id,
        order_no=booking.booking_no,
        total_amount=total_fee,
        membership_deduct=membership_deduct,
        service_deduct=service_deduct,
        gift_deduct=gift_deduct,
        cash_amount=Decimal("0"),
        description=f"空间预约余额抵扣：{booking.resource_name} {booking.booking_date}",
    )
    deduct_record.generate_deduct_no()
    db.add(deduct_record)

    balance_account.membership_balance -= membership_deduct
    balance_account.service_balance -= service_deduct
    balance_account.gift_balance -= gift_deduct
    balance_account.total_deducted += total_fee
    balance_account.update_total_balance()
    balance_account.last_transaction_at = datetime.now()

    tx_membership = None
    if membership_deduct > 0:
        tx_membership = BalanceTransaction(
            transaction_no=f"TX{datetime.now().strftime('%Y%m%d%H%M%S%f')}",
            user_id=booking.user_id,
            transaction_type=TransactionType.DEDUCT,
            amount=-membership_deduct,
            balance_type=BalanceType.MEMBERSHIP,
            before_membership_balance=balance_account.membership_balance
            + membership_deduct,
            before_total_balance=balance_account.total_balance + membership_deduct,
            after_membership_balance=balance_account.membership_balance,
            after_total_balance=balance_account.total_balance,
            reference_type="space_booking",
            reference_id=booking.id,
            reference_no=booking.booking_no,
            description=f"空间预约抵扣（会员余额）：{booking.resource_name}",
        )
        db.add(tx_membership)

    tx_service = None
    if service_deduct > 0:
        tx_service = BalanceTransaction(
            transaction_no=f"TX{datetime.now().strftime('%Y%m%d%H%M%S%f')}{random.randint(100, 999)}",
            user_id=booking.user_id,
            transaction_type=TransactionType.DEDUCT,
            amount=-service_deduct,
            balance_type=BalanceType.SERVICE,
            before_service_balance=balance_account.service_balance + service_deduct,
            before_total_balance=balance_account.total_balance + service_deduct,
            after_service_balance=balance_account.service_balance,
            after_total_balance=balance_account.total_balance,
            reference_type="space_booking",
            reference_id=booking.id,
            reference_no=booking.booking_no,
            description=f"空间预约抵扣（服务余额）：{booking.resource_name}",
        )
        db.add(tx_service)

    tx_gift = None
    if gift_deduct > 0:
        tx_gift = BalanceTransaction(
            transaction_no=f"TX{datetime.now().strftime('%Y%m%d%H%M%S%f')}{random.randint(1000, 9999)}",
            user_id=booking.user_id,
            transaction_type=TransactionType.DEDUCT,
            amount=-gift_deduct,
            balance_type=None,
            before_gift_balance=balance_account.gift_balance + gift_deduct,
            before_total_balance=balance_account.total_balance + gift_deduct,
            after_gift_balance=balance_account.gift_balance,
            after_total_balance=balance_account.total_balance,
            reference_type="space_booking",
            reference_id=booking.id,
            reference_no=booking.booking_no,
            description=f"空间预约抵扣（赠送余额）：{booking.resource_name}",
        )
        db.add(tx_gift)

    booking.payment_mode = "balance_deduct"
    booking.payment_status = "deducted"
    booking.deduct_record_id = deduct_record.id

    if booking.status == "pending":
        booking.status = "approved"
        booking.approved_at = datetime.now()
        booking.approved_by = "balance_auto"

    db.commit()
    db.refresh(balance_account)

    return BalanceDeductResponse(
        success=True,
        deduct_no=deduct_no,
        total_amount=float(total_fee),
        membership_deduct=float(membership_deduct),
        service_deduct=float(service_deduct),
        gift_deduct=float(gift_deduct),
        cash_amount=0.0,
        remaining_balance=float(balance_account.total_balance),
    )


@router.post("/settle-credit/{booking_id}", response_model=dict)
async def settle_credit_booking(
    booking_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admactiver),
):
    """结算记账模式预约"""

    booking = db.query(SpaceBooking).filter(SpaceBooking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="预约不存在")

    if booking.status != "completed":
        raise HTTPException(status_code=400, detail="只能结算已完成的预约")

    if booking.payment_mode != "credit":
        raise HTTPException(status_code=400, detail="此预约非记账模式")

    month = datetime.now().strftime("%Y-%m")

    credit_note = (
        db.query(CreditNote)
        .filter(and_(CreditNote.user_id == booking.user_id, CreditNote.month == month))
        .first()
    )

    if not credit_note:
        note_no = (
            f"CN{datetime.now().strftime('%Y%m%d%H%M%S')}{random.randint(1000, 9999)}"
        )
        credit_note = CreditNote(
            note_no=note_no,
            user_id=booking.user_id,
            user_name=booking.user_name,
            department=booking.department,
            month=month,
            status="pending",
        )
        credit_note.generate_note_no()
        db.add(credit_note)
        db.flush()

    item = credit_note.add_item(booking, booking.total_fee or booking.actual_fee or 0)
    db.add(item)

    booking.credit_note_id = credit_note.id
    booking.status = "settled"
    booking.payment_status = "settled"
    booking.settlement_status = "settled"
    booking.settled_at = datetime.now()
    booking.settled_by = current_user.name

    db.commit()

    return {
        "success": True,
        "booking_id": booking_id,
        "booking_no": booking.booking_no,
        "settled_amount": float(booking.total_fee or 0),
        "credit_note_no": credit_note.note_no,
        "credit_note_month": credit_note.month,
        "credit_note_total": float(credit_note.total_amount),
        "message": f"记账预约已结算，账单 {credit_note.note_no} 总金额 ¥{credit_note.total_amount:.2f}",
    }


@router.post("/monthly-settlement", response_model=dict)
async def process_monthly_settlement(
    settlement_request: MonthlySettlementRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admactiver),
):
    """处理月度记账账单结算"""

    month = settlement_request.month

    query = db.query(CreditNote).filter(CreditNote.month == month)

    if settlement_request.user_id:
        query = query.filter(CreditNote.user_id == settlement_request.user_id)

    credit_notes = query.filter(CreditNote.status != "settled").all()

    processed_count = 0
    total_amount = Decimal("0")

    for note in credit_notes:
        note.mark_settled(current_user.name)
        processed_count += 1
        total_amount += note.total_amount

    db.commit()

    return {
        "success": True,
        "month": month,
        "processed_count": processed_count,
        "total_amount": float(total_amount),
        "message": f"月度结算完成：{processed_count} 个账单，总金额 ¥{total_amount:.2f}",
    }


@router.get("/credit-notes", response_model=dict)
async def get_credit_notes(
    month: Optional[str] = Query(None),
    user_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admactiver),
):
    """获取记账账单列表"""

    query = db.query(CreditNote)

    if month:
        query = query.filter(CreditNote.month == month)

    if user_id:
        query = query.filter(CreditNote.user_id == user_id)

    if status:
        query = query.filter(CreditNote.status == status)

    total = query.count()

    notes = (
        query.order_by(CreditNote.created_at.desc())
        .offset((page - 1) * limit)
        .limit(limit)
        .all()
    )

    items = []
    for note in notes:
        note_items = []
        for item in note.items:
            note_items.append(
                {
                    "id": item.id,
                    "booking_no": item.booking_no,
                    "booking_date": str(item.booking_date)
                    if item.booking_date
                    else None,
                    "space_name": item.space_name,
                    "time_slot": item.time_slot,
                    "amount": float(item.amount),
                }
            )

        items.append(
            {
                "id": note.id,
                "note_no": note.note_no,
                "user_id": note.user_id,
                "user_name": note.user_name,
                "department": note.department,
                "month": note.month,
                "total_amount": float(note.total_amount),
                "paid_amount": float(note.paid_amount),
                "booking_count": note.booking_count,
                "status": note.status,
                "items": note_items,
                "created_at": str(note.created_at),
            }
        )

    return {"items": items, "total": total, "page": page, "limit": limit}


@router.get("/credit-notes/{note_id}", response_model=CreditNoteResponse)
async def get_credit_note_detail(
    note_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admactiver),
):
    """获取记账账单详情"""

    note = db.query(CreditNote).filter(CreditNote.id == note_id).first()

    if not note:
        raise HTTPException(status_code=404, detail="账单不存在")

    note_items = []
    for item in note.items:
        note_items.append(
            {
                "id": item.id,
                "booking_no": item.booking_no,
                "booking_date": str(item.booking_date) if item.booking_date else None,
                "space_name": item.space_name,
                "time_slot": item.time_slot,
                "amount": float(item.amount),
                "settled_at": str(item.settled_at) if item.settled_at else None,
            }
        )

    return CreditNoteResponse(
        id=note.id,
        note_no=note.note_no,
        user_name=note.user_name,
        department=note.department,
        month=note.month,
        total_amount=float(note.total_amount),
        paid_amount=float(note.paid_amount),
        booking_count=note.booking_count,
        status=note.status,
        items=note_items,
    )
