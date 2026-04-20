"""
用户余额管理API - 管理员端
支持余额调整、查询、统计
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Body
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
from depends.auth import get_admin_user

router = APIRouter(prefix="/admin/balance", tags=["管理员-余额管理"])


class BalanceAdjustRequest(BaseModel):
    user_id: int = Field(..., description="用户ID")
    amount: float = Field(..., description="调整金额(正数为增加,负数为减少)")
    balance_type: str = Field(
        "membership", description="余额类型(membership/service/gift)"
    )
    description: Optional[str] = Field(None, description="调整说明")
    expire_date: Optional[str] = Field(None, description="过期日期(仅会员余额)")


class AdminBalanceAccountResponse(BaseModel):
    id: int
    user_id: int
    user_name: str
    user_phone: Optional[str] = None
    membership_balance: float
    service_balance: float
    gift_balance: float
    total_balance: float
    frozen_membership_balance: float
    frozen_service_balance: float
    membership_expire_date: Optional[str] = None
    total_membership_charged: float
    total_service_charged: float
    total_deducted: float
    total_refunded: float
    last_transaction_at: Optional[str] = None
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class AdminBalanceListResponse(BaseModel):
    accounts: List[AdminBalanceAccountResponse]
    total: int
    page: int
    page_size: int


class AdminTransactionResponse(BaseModel):
    id: int
    transaction_no: str
    user_id: int
    user_name: str
    transaction_type: str
    transaction_type_text: str
    amount: float
    balance_type: Optional[str]
    before_total_balance: Optional[float]
    after_total_balance: Optional[float]
    reference_type: Optional[str]
    reference_no: Optional[str]
    description: Optional[str]
    admin_name: Optional[str]
    expire_date: Optional[str]
    created_at: str

    class Config:
        from_attributes = True


class AdminTransactionListResponse(BaseModel):
    transactions: List[AdminTransactionResponse]
    total: int
    page: int
    page_size: int


class BalanceStatsResponse(BaseModel):
    total_users: int
    total_membership_balance: float
    total_service_balance: float
    total_gift_balance: float
    total_balance: float
    total_membership_charged: float
    total_service_charged: float
    total_deducted: float
    month_charged: float
    month_deducted: float


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


@router.get("/accounts", response_model=AdminBalanceListResponse)
async def get_balance_accounts(
    user_id: Optional[int] = Query(None, description="用户ID筛选"),
    search: Optional[str] = Query(None, description="搜索(用户名/手机号)"),
    min_balance: Optional[float] = Query(None, description="最小余额筛选"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=50, description="每页数量"),
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_admin_user),
):
    """获取余额账户列表"""
    try:
        query = db.query(UserBalanceAccount).join(User)

        if user_id:
            query = query.filter(UserBalanceAccount.user_id == user_id)

        if search:
            query = query.filter(
                (User.name.contains(search)) | (User.phone.contains(search))
            )

        if min_balance:
            query = query.filter(
                UserBalanceAccount.total_balance >= Decimal(str(min_balance))
            )

        total = query.count()

        accounts = (
            query.order_by(UserBalanceAccount.total_balance.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )

        account_responses = []
        for account in accounts:
            user = db.query(User).filter(User.id == account.user_id).first()
            account_responses.append(
                AdminBalanceAccountResponse(
                    id=account.id,
                    user_id=account.user_id,
                    user_name=user.name if user else "未知",
                    user_phone=user.phone if user else "",
                    membership_balance=float(account.membership_balance),
                    service_balance=float(account.service_balance),
                    gift_balance=float(account.gift_balance),
                    total_balance=float(account.total_balance),
                    frozen_membership_balance=float(account.frozen_membership_balance),
                    frozen_service_balance=float(account.frozen_service_balance),
                    membership_expire_date=str(account.membership_expire_date)
                    if account.membership_expire_date
                    else None,
                    total_membership_charged=float(account.total_membership_charged),
                    total_service_charged=float(account.total_service_charged),
                    total_deducted=float(account.total_deducted),
                    total_refunded=float(account.total_refunded),
                    last_transaction_at=str(account.last_transaction_at)
                    if account.last_transaction_at
                    else None,
                    created_at=str(account.created_at),
                    updated_at=str(account.updated_at),
                )
            )

        return AdminBalanceListResponse(
            accounts=account_responses,
            total=total,
            page=page,
            page_size=page_size,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取余额账户列表失败: {str(e)}")


@router.get("/stats", response_model=BalanceStatsResponse)
async def get_balance_stats(
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_admin_user),
):
    """获取余额统计"""
    try:
        total_users = db.query(UserBalanceAccount).count()

        all_accounts = db.query(UserBalanceAccount).all()
        total_membership_balance = sum(
            float(acc.membership_balance) for acc in all_accounts
        )
        total_service_balance = sum(float(acc.service_balance) for acc in all_accounts)
        total_gift_balance = sum(float(acc.gift_balance) for acc in all_accounts)
        total_balance = sum(float(acc.total_balance) for acc in all_accounts)

        total_membership_charged = sum(
            float(acc.total_membership_charged) for acc in all_accounts
        )
        total_service_charged = sum(
            float(acc.total_service_charged) for acc in all_accounts
        )
        total_deducted = sum(float(acc.total_deducted) for acc in all_accounts)

        month_start = datetime.now().replace(
            day=1, hour=0, minute=0, second=0, microsecond=0
        )
        month_charged_txs = (
            db.query(BalanceTransaction)
            .filter(
                BalanceTransaction.transaction_type.in_(
                    [TransactionType.MEMBERSHIP_CHARGE, TransactionType.SERVICE_CHARGE]
                ),
                BalanceTransaction.created_at >= month_start,
            )
            .all()
        )
        month_charged = sum(float(tx.amount) for tx in month_charged_txs)

        month_deducted_txs = (
            db.query(BalanceTransaction)
            .filter(
                BalanceTransaction.transaction_type == TransactionType.DEDUCT,
                BalanceTransaction.created_at >= month_start,
            )
            .all()
        )
        month_deducted = sum(abs(float(tx.amount)) for tx in month_deducted_txs)

        return BalanceStatsResponse(
            total_users=total_users,
            total_membership_balance=total_membership_balance,
            total_service_balance=total_service_balance,
            total_gift_balance=total_gift_balance,
            total_balance=total_balance,
            total_membership_charged=total_membership_charged,
            total_service_charged=total_service_charged,
            total_deducted=total_deducted,
            month_charged=month_charged,
            month_deducted=month_deducted,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取余额统计失败: {str(e)}")


@router.get("/transactions", response_model=AdminTransactionListResponse)
async def get_transactions(
    user_id: Optional[int] = Query(None, description="用户ID筛选"),
    transaction_type: Optional[str] = Query(None, description="交易类型筛选"),
    balance_type: Optional[str] = Query(None, description="余额类型筛选"),
    start_date: Optional[str] = Query(None, description="开始日期"),
    end_date: Optional[str] = Query(None, description="结束日期"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=50, description="每页数量"),
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_admin_user),
):
    """获取交易记录列表"""
    try:
        query = db.query(BalanceTransaction)

        if user_id:
            query = query.filter(BalanceTransaction.user_id == user_id)

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

        if start_date:
            try:
                start_dt = datetime.strptime(start_date, "%Y-%m-%d")
                query = query.filter(BalanceTransaction.created_at >= start_dt)
            except ValueError:
                pass

        if end_date:
            try:
                end_dt = datetime.strptime(end_date, "%Y-%m-%d")
                query = query.filter(BalanceTransaction.created_at < end_dt)
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
            user = db.query(User).filter(User.id == tx.user_id).first()
            admin = (
                db.query(User).filter(User.id == tx.admin_id).first()
                if tx.admin_id
                else None
            )

            transaction_responses.append(
                AdminTransactionResponse(
                    id=tx.id,
                    transaction_no=tx.transaction_no,
                    user_id=tx.user_id,
                    user_name=user.name if user else "未知",
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
                    reference_no=tx.reference_no,
                    description=tx.description,
                    admin_name=admin.name if admin else None,
                    expire_date=str(tx.expire_date) if tx.expire_date else None,
                    created_at=str(tx.created_at),
                )
            )

        return AdminTransactionListResponse(
            transactions=transaction_responses,
            total=total,
            page=page,
            page_size=page_size,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取交易记录失败: {str(e)}")


@router.get("/accounts/{user_id}", response_model=dict)
async def get_user_balance_detail(
    user_id: int,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_admin_user),
):
    """获取用户余额详情"""
    try:
        balance_account = (
            db.query(UserBalanceAccount)
            .filter(UserBalanceAccount.user_id == user_id)
            .first()
        )

        if not balance_account:
            raise HTTPException(status_code=404, detail="用户余额账户不存在")

        user = db.query(User).filter(User.id == user_id).first()

        recent_transactions = (
            db.query(BalanceTransaction)
            .filter(BalanceTransaction.user_id == user_id)
            .order_by(BalanceTransaction.created_at.desc)
            .limit(10)
            .all()
        )

        recent_deducts = (
            db.query(BalanceDeductRecord)
            .filter(BalanceDeductRecord.user_id == user_id)
            .order_by(BalanceDeductRecord.created_at.desc)
            .limit(10)
            .all()
        )

        return {
            "account": {
                "id": balance_account.id,
                "user_id": balance_account.user_id,
                "membership_balance": float(balance_account.membership_balance),
                "service_balance": float(balance_account.service_balance),
                "gift_balance": float(balance_account.gift_balance),
                "total_balance": float(balance_account.total_balance),
                "frozen_membership_balance": float(
                    balance_account.frozen_membership_balance
                ),
                "frozen_service_balance": float(balance_account.frozen_service_balance),
                "membership_expire_date": str(balance_account.membership_expire_date)
                if balance_account.membership_expire_date
                else None,
                "total_membership_charged": float(
                    balance_account.total_membership_charged
                ),
                "total_service_charged": float(balance_account.total_service_charged),
                "total_deducted": float(balance_account.total_deducted),
                "total_refunded": float(balance_account.total_refunded),
            },
            "user": {
                "id": user.id if user else None,
                "name": user.name if user else "未知",
                "phone": user.phone if user else "",
            },
            "available": balance_account.get_available_balance(),
            "recent_transactions": [
                {
                    "id": tx.id,
                    "transaction_no": tx.transaction_no,
                    "transaction_type": get_transaction_type_text(tx.transaction_type),
                    "amount": float(tx.amount),
                    "description": tx.description,
                    "created_at": str(tx.created_at),
                }
                for tx in recent_transactions
            ],
            "recent_deducts": [
                {
                    "id": record.id,
                    "deduct_no": record.deduct_no,
                    "order_type": record.order_type,
                    "order_no": record.order_no,
                    "membership_deduct": float(record.membership_deduct),
                    "service_deduct": float(record.service_deduct),
                    "cash_amount": float(record.cash_amount),
                    "created_at": str(record.created_at),
                }
                for record in recent_deducts
            ],
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取用户余额详情失败: {str(e)}")


@router.post("/adjust", response_model=dict)
async def adjust_balance(
    request: BalanceAdjustRequest,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_admin_user),
):
    """调整用户余额"""
    try:
        user = db.query(User).filter(User.id == request.user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")

        balance_account = (
            db.query(UserBalanceAccount)
            .filter(UserBalanceAccount.user_id == request.user_id)
            .first()
        )

        if not balance_account:
            balance_account = UserBalanceAccount(
                user_id=request.user_id,
                membership_balance=Decimal(0),
                service_balance=Decimal(0),
                gift_balance=Decimal(0),
                total_balance=Decimal(0),
            )
            db.add(balance_account)
            db.flush()

        adjust_amount = Decimal(str(request.amount))

        before_membership = balance_account.membership_balance
        before_service = balance_account.service_balance
        before_gift = balance_account.gift_balance
        before_total = balance_account.total_balance

        balance_type_enum = None
        expire_date = None

        if request.balance_type == "membership":
            balance_type_enum = BalanceType.MEMBERSHIP
            balance_account.membership_balance += adjust_amount
            if adjust_amount > 0:
                balance_account.total_membership_charged += adjust_amount
            else:
                balance_account.total_refunded += abs(adjust_amount)
            if request.expire_date:
                try:
                    expire_date = datetime.strptime(
                        request.expire_date, "%Y-%m-%d"
                    ).date()
                    balance_account.membership_expire_date = expire_date
                except ValueError:
                    pass
        elif request.balance_type == "service":
            balance_type_enum = BalanceType.SERVICE
            balance_account.service_balance += adjust_amount
            if adjust_amount > 0:
                balance_account.total_service_charged += adjust_amount
            else:
                balance_account.total_refunded += abs(adjust_amount)
        elif request.balance_type == "gift":
            balance_account.gift_balance += adjust_amount

        balance_account.update_total_balance()
        balance_account.last_transaction_at = datetime.now()

        transaction = BalanceTransaction(
            transaction_no=f"TX{datetime.now().strftime('%Y%m%d%H%M%S%f')}",
            user_id=request.user_id,
            transaction_type=TransactionType.ADJUST,
            amount=adjust_amount,
            balance_type=balance_type_enum,
            before_membership_balance=before_membership,
            before_service_balance=before_service,
            before_gift_balance=before_gift,
            before_total_balance=before_total,
            after_membership_balance=balance_account.membership_balance,
            after_service_balance=balance_account.service_balance,
            after_gift_balance=balance_account.gift_balance,
            after_total_balance=balance_account.total_balance,
            reference_type="admin_adjust",
            reference_id=admin_user.id,
            description=request.description or f"管理员调整余额 - {admin_user.name}",
            admin_id=admin_user.id,
            expire_date=expire_date,
        )
        db.add(transaction)

        db.commit()

        return {
            "success": True,
            "message": "余额调整成功",
            "transaction_no": transaction.transaction_no,
            "adjust_amount": float(adjust_amount),
            "balance_type": request.balance_type,
            "before_balance": float(before_total),
            "after_balance": float(balance_account.total_balance),
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"调整余额失败: {str(e)}")


@router.post("/gift", response_model=dict)
async def gift_balance(
    user_id: int = Body(..., embed=True, description="用户ID"),
    amount: float = Body(..., embed=True, description="赠送金额"),
    description: Optional[str] = Body(None, embed=True, description="赠送说明"),
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_admin_user),
):
    """赠送余额"""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")

        balance_account = (
            db.query(UserBalanceAccount)
            .filter(UserBalanceAccount.user_id == user_id)
            .first()
        )

        if not balance_account:
            balance_account = UserBalanceAccount(
                user_id=user_id,
                membership_balance=Decimal(0),
                service_balance=Decimal(0),
                gift_balance=Decimal(0),
                total_balance=Decimal(0),
            )
            db.add(balance_account)
            db.flush()

        gift_amount = Decimal(str(amount))

        before_gift = balance_account.gift_balance
        before_total = balance_account.total_balance

        balance_account.gift_balance += gift_amount
        balance_account.update_total_balance()
        balance_account.last_transaction_at = datetime.now()

        transaction = BalanceTransaction(
            transaction_no=f"TX{datetime.now().strftime('%Y%m%d%H%M%S%f')}",
            user_id=user_id,
            transaction_type=TransactionType.GIFT,
            amount=gift_amount,
            balance_type=None,
            before_membership_balance=balance_account.membership_balance,
            before_service_balance=balance_account.service_balance,
            before_gift_balance=before_gift,
            before_total_balance=before_total,
            after_membership_balance=balance_account.membership_balance,
            after_service_balance=balance_account.service_balance,
            after_gift_balance=balance_account.gift_balance,
            after_total_balance=balance_account.total_balance,
            reference_type="admin_gift",
            reference_id=admin_user.id,
            description=description or f"管理员赠送 - {admin_user.name}",
            admin_id=admin_user.id,
        )
        db.add(transaction)

        db.commit()

        return {
            "success": True,
            "message": "赠送成功",
            "transaction_no": transaction.transaction_no,
            "gift_amount": float(gift_amount),
            "gift_balance": float(balance_account.gift_balance),
            "total_balance": float(balance_account.total_balance),
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"赠送失败: {str(e)}")
