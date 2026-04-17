"""
用户余额API路由 - 用户端
支持余额查询、交易记录、抵扣记录
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from decimal import Decimal
from pydantic import BaseModel, Field
from datetime import datetime, date

from config.database import get_db
from models.user_balance import (
    UserBalanceAccount,
    BalanceTransaction,
    BalanceDeductRecord,
    TransactionType,
    BalanceType,
)
from models.user import User
from depends.auth import get_current_user

router = APIRouter(prefix="/balance", tags=["用户余额"])


class BalanceInfoResponse(BaseModel):
    user_id: int
    membership_balance: float
    service_balance: float
    gift_balance: float
    total_balance: float
    available_membership_balance: float
    available_service_balance: float
    available_total_balance: float
    membership_expire_date: Optional[str]
    total_membership_charged: float
    total_service_charged: float
    total_deducted: float
    total_refunded: float
    last_transaction_at: Optional[str]


class TransactionResponse(BaseModel):
    id: int
    transaction_no: str
    transaction_type: str
    transaction_type_text: str
    amount: float
    balance_type: Optional[str]
    before_total_balance: Optional[float]
    after_total_balance: Optional[float]
    reference_type: Optional[str]
    reference_id: Optional[int]
    reference_no: Optional[str]
    description: Optional[str]
    expire_date: Optional[str]
    created_at: str

    class Config:
        from_attributes = True


class TransactionListResponse(BaseModel):
    transactions: List[TransactionResponse]
    total: int
    page: int
    page_size: int


class DeductRecordResponse(BaseModel):
    id: int
    deduct_no: str
    order_type: str
    order_id: int
    order_no: Optional[str]
    total_amount: float
    member_discount: float
    member_free_amount: float
    membership_deduct: float
    service_deduct: float
    gift_deduct: float
    cash_amount: float
    description: Optional[str]
    created_at: str

    class Config:
        from_attributes = True


class DeductRecordListResponse(BaseModel):
    records: List[DeductRecordResponse]
    total: int
    page: int
    page_size: int


def get_transaction_type_text(transaction_type: TransactionType) -> str:
    """获取交易类型文本"""
    type_texts = {
        TransactionType.MEMBERSHIP_CHARGE: "会员充值",
        TransactionType.SERVICE_CHARGE: "服务充值",
        TransactionType.DEDUCT: "余额抵扣",
        TransactionType.REFUND: "退款",
        TransactionType.GIFT: "赠送",
        TransactionType.ADJUST: "管理员调整",
        TransactionType.TRANSFER: "余额转账",
    }
    return type_texts.get(transaction_type, transaction_type.value)


@router.get("/my", response_model=BalanceInfoResponse)
async def get_my_balance(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取我的余额信息"""
    try:
        balance_account = (
            db.query(UserBalanceAccount)
            .filter(UserBalanceAccount.user_id == current_user.id)
            .first()
        )

        if not balance_account:
            balance_account = UserBalanceAccount(
                user_id=current_user.id,
                membership_balance=Decimal(0),
                service_balance=Decimal(0),
                gift_balance=Decimal(0),
                total_balance=Decimal(0),
            )
            db.add(balance_account)
            db.commit()
            db.refresh(balance_account)

        available = balance_account.get_available_balance()

        return BalanceInfoResponse(
            user_id=balance_account.user_id,
            membership_balance=float(balance_account.membership_balance),
            service_balance=float(balance_account.service_balance),
            gift_balance=float(balance_account.gift_balance),
            total_balance=float(balance_account.total_balance),
            available_membership_balance=available["membership"],
            available_service_balance=available["service"],
            available_total_balance=available["total"],
            membership_expire_date=str(balance_account.membership_expire_date)
            if balance_account.membership_expire_date
            else None,
            total_membership_charged=float(balance_account.total_membership_charged),
            total_service_charged=float(balance_account.total_service_charged),
            total_deducted=float(balance_account.total_deducted),
            total_refunded=float(balance_account.total_refunded),
            last_transaction_at=str(balance_account.last_transaction_at)
            if balance_account.last_transaction_at
            else None,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取余额失败: {str(e)}")


@router.get("/transactions", response_model=TransactionListResponse)
async def get_transactions(
    transaction_type: Optional[str] = Query(None, description="交易类型筛选"),
    balance_type: Optional[str] = Query(None, description="余额类型筛选"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=50, description="每页数量"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取余额变动记录"""
    try:
        query = db.query(BalanceTransaction).filter(
            BalanceTransaction.user_id == current_user.id
        )

        if transaction_type:
            try:
                type_enum = TransactionType(transaction_type)
                query = query.filter(BalanceTransaction.transaction_type == type_enum)
            except ValueError:
                pass

        if balance_type:
            try:
                balance_enum = BalanceType(balance_type)
                query = query.filter(BalanceTransaction.balance_type == balance_enum)
            except ValueError:
                pass

        total = query.count()

        transactions = (
            query.order_by(BalanceTransaction.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )

        transaction_responses = []
        for tx in transactions:
            transaction_responses.append(
                TransactionResponse(
                    id=tx.id,
                    transaction_no=tx.transaction_no,
                    transaction_type=tx.transaction_type.value,
                    transaction_type_text=get_transaction_type_text(
                        tx.transaction_type
                    ),
                    amount=float(tx.amount),
                    balance_type=tx.balance_type.value if tx.balance_type else None,
                    before_total_balance=float(tx.before_total_balance)
                    if tx.before_total_balance
                    else None,
                    after_total_balance=float(tx.after_total_balance)
                    if tx.after_total_balance
                    else None,
                    reference_type=tx.reference_type,
                    reference_id=tx.reference_id,
                    reference_no=tx.reference_no,
                    description=tx.description,
                    expire_date=str(tx.expire_date) if tx.expire_date else None,
                    created_at=str(tx.created_at),
                )
            )

        return TransactionListResponse(
            transactions=transaction_responses,
            total=total,
            page=page,
            page_size=page_size,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取交易记录失败: {str(e)}")


@router.get("/deduct-records", response_model=DeductRecordListResponse)
async def get_deduct_records(
    order_type: Optional[str] = Query(None, description="订单类型筛选"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=50, description="每页数量"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取抵扣记录"""
    try:
        query = db.query(BalanceDeductRecord).filter(
            BalanceDeductRecord.user_id == current_user.id
        )

        if order_type:
            query = query.filter(BalanceDeductRecord.order_type == order_type)

        total = query.count()

        records = (
            query.order_by(BalanceDeductRecord.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )

        record_responses = []
        for record in records:
            record_responses.append(
                DeductRecordResponse(
                    id=record.id,
                    deduct_no=record.deduct_no,
                    order_type=record.order_type,
                    order_id=record.order_id,
                    order_no=record.order_no,
                    total_amount=float(record.total_amount),
                    member_discount=float(record.member_discount),
                    member_free_amount=float(record.member_free_amount),
                    membership_deduct=float(record.membership_deduct),
                    service_deduct=float(record.service_deduct),
                    gift_deduct=float(record.gift_deduct),
                    cash_amount=float(record.cash_amount),
                    description=record.description,
                    created_at=str(record.created_at),
                )
            )

        return DeductRecordListResponse(
            records=record_responses,
            total=total,
            page=page,
            page_size=page_size,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取抵扣记录失败: {str(e)}")


@router.get("/summary", response_model=dict)
async def get_balance_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取余额统计摘要"""
    try:
        balance_account = (
            db.query(UserBalanceAccount)
            .filter(UserBalanceAccount.user_id == current_user.id)
            .first()
        )

        if not balance_account:
            return {
                "total_balance": 0,
                "membership_balance": 0,
                "service_balance": 0,
                "gift_balance": 0,
                "total_charged": 0,
                "total_deducted": 0,
                "month_deducted": 0,
            }

        month_start = datetime.now().replace(
            day=1, hour=0, minute=0, second=0, microsecond=0
        )
        month_deducted = (
            db.query(BalanceTransaction)
            .filter(
                BalanceTransaction.user_id == current_user.id,
                BalanceTransaction.transaction_type == TransactionType.DEDUCT,
                BalanceTransaction.created_at >= month_start,
            )
            .count()
        )

        month_deduct_amount = (
            db.query(BalanceTransaction)
            .filter(
                BalanceTransaction.user_id == current_user.id,
                BalanceTransaction.transaction_type == TransactionType.DEDUCT,
                BalanceTransaction.created_at >= month_start,
            )
            .all()
        )

        total_month_deduct = sum(abs(float(tx.amount)) for tx in month_deduct_amount)

        return {
            "total_balance": float(balance_account.total_balance),
            "membership_balance": float(balance_account.membership_balance),
            "service_balance": float(balance_account.service_balance),
            "gift_balance": float(balance_account.gift_balance),
            "total_charged": float(
                balance_account.total_membership_charged
                + balance_account.total_service_charged
            ),
            "total_deducted": float(balance_account.total_deducted),
            "month_deduct_count": month_deducted,
            "month_deduct_amount": total_month_deduct,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取余额统计失败: {str(e)}")
