"""
押金管理API路由
支持押金的收取 / 退还 / 没收 / 查询 完整生命周期
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional
from pydantic import BaseModel
import random

from config.database import get_db
from models.user import User
from depends.auth import get_admin_user, get_current_user_required
from shared.models.space.deposit_record import DepositRecord
from shared.models.space.space_booking import SpaceBooking
from shared.schemas.space.response import ApiResponse, PaginatedResponse

router = APIRouter(prefix="/space/deposits", tags=["空间押金管理"])


class CollectDepositRequest(BaseModel):
    booking_id: int
    amount: float
    collect_method: str = "cash"
    collect_note: Optional[str] = None


class RefundDepositRequest(BaseModel):
    booking_id: int
    refund_method: str = "cash"
    refund_note: Optional[str] = None


class ForfeitDepositRequest(BaseModel):
    booking_id: int
    forfeit_reason: str


@router.get("", response_model=ApiResponse)
async def get_deposits(
    status: Optional[str] = Query(None, description="状态过滤"),
    booking_id: Optional[int] = Query(None, description="预约ID过滤"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    """获取押金记录列表"""

    query = db.query(DepositRecord)

    if status:
        query = query.filter(DepositRecord.status == status)
    if booking_id:
        query = query.filter(DepositRecord.booking_id == booking_id)

    total = query.count()
    deposits = (
        query.order_by(DepositRecord.created_at.desc())
        .offset((page - 1) * limit)
        .limit(limit)
        .all()
    )

    items = []
    for d in deposits:
        items.append({
            "id": d.id,
            "deposit_no": d.deposit_no,
            "booking_id": d.booking_id,
            "booking_no": d.booking_no,
            "user_id": d.user_id,
            "user_name": d.user_name,
            "amount": d.amount,
            "status": d.status,
            "collected_at": d.collected_at.isoformat() if d.collected_at else None,
            "collected_by": d.collected_by,
            "collect_method": d.collect_method,
            "refunded_at": d.refunded_at.isoformat() if d.refunded_at else None,
            "refunded_by": d.refunded_by,
            "refund_method": d.refund_method,
            "forfeited_at": d.forfeited_at.isoformat() if d.forfeited_at else None,
            "forfeited_by": d.forfeited_by,
            "forfeit_reason": d.forfeit_reason,
            "created_at": d.created_at.isoformat() if d.created_at else None,
        })

    return ApiResponse(
        data=PaginatedResponse(
            items=items,
            total=total,
            page=page,
            limit=limit,
            pages=(total + limit - 1) // limit if total > 0 else 0,
        )
    )


@router.get("/{booking_id}/booking", response_model=ApiResponse)
async def get_booking_deposits(
    booking_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_required),
):
    """获取某预约的押金记录"""

    booking = db.query(SpaceBooking).filter(SpaceBooking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="预约不存在")

    if current_user.role not in ["admin", "super_admin"] and booking.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权限查看")

    deposits = (
        db.query(DepositRecord)
        .filter(DepositRecord.booking_id == booking_id)
        .order_by(DepositRecord.created_at.desc())
        .all()
    )

    items = []
    for d in deposits:
        items.append({
            "id": d.id,
            "deposit_no": d.deposit_no,
            "amount": d.amount,
            "status": d.status,
            "collected_at": d.collected_at.isoformat() if d.collected_at else None,
            "collected_by": d.collected_by,
            "collect_method": d.collect_method,
            "refunded_at": d.refunded_at.isoformat() if d.refunded_at else None,
            "refunded_by": d.refunded_by,
            "forfeited_at": d.forfeited_at.isoformat() if d.forfeited_at else None,
            "forfeit_reason": d.forfeit_reason,
        })

    return ApiResponse(data={
        "booking_id": booking_id,
        "booking_no": booking.booking_no,
        "deposit_records": items,
    })


@router.post("/collect", response_model=ApiResponse)
async def collect_deposit(
    req: CollectDepositRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    """收取押金（管理员）"""

    booking = db.query(SpaceBooking).filter(SpaceBooking.id == req.booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="预约不存在")

    if not booking.requires_deposit:
        raise HTTPException(status_code=400, detail="该预约无需押金")

    existing_collected = (
        db.query(DepositRecord)
        .filter(
            DepositRecord.booking_id == req.booking_id,
            DepositRecord.status.in_(["collected", "refunding"]),
        )
        .first()
    )
    if existing_collected:
        raise HTTPException(status_code=409, detail="该预约已有押金记录，请勿重复收取")

    deposit_no = (
        f"DP{datetime.now().strftime('%Y%m%d%H%M%S')}{random.randint(1000, 9999)}"
    )

    record = DepositRecord(
        deposit_no=deposit_no,
        booking_id=booking.id,
        booking_no=booking.booking_no,
        user_id=booking.user_id,
        user_name=booking.user_name,
        amount=req.amount,
        status="collected",
        collected_at=datetime.now(),
        collected_by=current_user.name,
        collect_method=req.collect_method,
        collect_note=req.collect_note,
    )

    db.add(record)

    # 同步更新 booking 的押金标记
    booking.deposit_paid = True
    booking.deposit_paid_at = datetime.now()
    booking.deposit_payment_method = req.collect_method
    booking.deposit_amount = req.amount

    db.commit()
    db.refresh(record)

    return ApiResponse(
        message=f"押金已收取，金额 ¥{req.amount:.2f}，方式：{req.collect_method}",
        data={
            "deposit_id": record.id,
            "deposit_no": record.deposit_no,
            "booking_id": booking.id,
            "amount": req.amount,
            "status": "collected",
        },
    )


@router.post("/refund", response_model=ApiResponse)
async def refund_deposit(
    req: RefundDepositRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    """退还押金（管理员）"""

    record = (
        db.query(DepositRecord)
        .filter(
            DepositRecord.booking_id == req.booking_id,
            DepositRecord.status == "collected",
        )
        .first()
    )
    if not record:
        raise HTTPException(status_code=404, detail="未找到已收取的押金记录")

    record.status = "refunded"
    record.refunded_at = datetime.now()
    record.refunded_by = current_user.name
    record.refund_method = req.refund_method
    record.refund_note = req.refund_note

    # 同步更新 booking
    booking = db.query(SpaceBooking).filter(SpaceBooking.id == req.booking_id).first()
    if booking:
        booking.deposit_refunded = True
        booking.deposit_refund_amount = record.amount
        booking.deposit_refund_at = datetime.now()

    db.commit()

    return ApiResponse(
        message=f"押金已退还，金额 ¥{record.amount:.2f}，方式：{req.refund_method}",
        data={
            "deposit_id": record.id,
            "deposit_no": record.deposit_no,
            "booking_id": req.booking_id,
            "amount": record.amount,
            "status": "refunded",
        },
    )


@router.post("/forfeit", response_model=ApiResponse)
async def forfeit_deposit(
    req: ForfeitDepositRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    """没收押金（管理员）"""

    record = (
        db.query(DepositRecord)
        .filter(
            DepositRecord.booking_id == req.booking_id,
            DepositRecord.status == "collected",
        )
        .first()
    )
    if not record:
        raise HTTPException(status_code=404, detail="未找到已收取的押金记录")

    if not req.forfeit_reason or not req.forfeit_reason.strip():
        raise HTTPException(status_code=400, detail="没收押金必须提供原因")

    record.status = "forfeited"
    record.forfeited_at = datetime.now()
    record.forfeited_by = current_user.name
    record.forfeit_reason = req.forfeit_reason

    db.commit()

    return ApiResponse(
        message=f"押金已没收，金额 ¥{record.amount:.2f}，原因：{req.forfeit_reason}",
        data={
            "deposit_id": record.id,
            "deposit_no": record.deposit_no,
            "booking_id": req.booking_id,
            "amount": record.amount,
            "status": "forfeited",
        },
    )
