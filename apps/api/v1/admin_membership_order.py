"""
会员订单管理API - 管理员端
支持订单审核、查询、统计
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.orm import Session
from typing import Optional, List
from decimal import Decimal
from pydantic import BaseModel, Field
from datetime import datetime, date, timedelta
import random

from config.database import get_db
from models.membership_plan import MembershipPlan
from models.membership_order import (
    MembershipOrder,
    MembershipOrderStatus,
    PaymentType,
    MembershipOrderAudit,
)
from models.user_balance import (
    UserBalanceAccount,
    BalanceTransaction,
    TransactionType,
    BalanceType,
)
from models.user import User
from depends.auth import get_admin_user

router = APIRouter(prefix="/admin/membership/orders", tags=["管理员-会员订单"])


class OrderReviewRequest(BaseModel):
    approved: bool = Field(..., description="是否通过")
    review_note: Optional[str] = Field(None, description="审核备注")
    balance_added: Optional[float] = Field(None, description="入账金额(默认为订单金额)")
    member_start_date: Optional[str] = Field(
        None, description="会员开始日期(默认为审核通过当天)"
    )


class AdminOrderResponse(BaseModel):
    id: int
    order_no: str
    user_id: int
    user_name: str
    user_phone: str
    plan_id: int
    plan_name: str
    plan_duration_months: int
    amount: float
    original_amount: Optional[float]
    discount_amount: float
    payment_type: str
    payment_method: Optional[str]
    status: str
    status_text: str
    balance_added: float
    member_start_date: Optional[str]
    member_end_date: Optional[str]
    member_days: int
    apply_note: Optional[str]
    admin_id: Optional[int]
    admin_name: Optional[str]
    review_note: Optional[str]
    reviewed_at: Optional[str]
    paid_at: Optional[str]
    is_renewal: bool
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class AdminOrderListResponse(BaseModel):
    orders: List[AdminOrderResponse]
    total: int
    page: int
    page_size: int


class OrderStatsResponse(BaseModel):
    total_orders: int
    pending_orders: int
    approved_orders: int
    rejected_orders: int
    total_amount: float
    pending_amount: float
    approved_amount: float
    month_orders: int
    month_amount: float


def get_status_text(status: MembershipOrderStatus) -> str:
    """获取状态文本"""
    status_texts = {
        MembershipOrderStatus.PENDING_REVIEW: "待审核",
        MembershipOrderStatus.APPROVED: "已通过",
        MembershipOrderStatus.REJECTED: "已拒绝",
        MembershipOrderStatus.CANCELLED: "已取消",
        MembershipOrderStatus.EXPIRED: "已过期",
    }
    return status_texts.get(status, status.value)


@router.get("", response_model=AdminOrderListResponse)
async def get_orders(
    status: Optional[str] = Query(None, description="订单状态筛选"),
    user_id: Optional[int] = Query(None, description="用户ID筛选"),
    search: Optional[str] = Query(None, description="搜索(订单号/用户名/手机号)"),
    start_date: Optional[str] = Query(None, description="开始日期"),
    end_date: Optional[str] = Query(None, description="结束日期"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=50, description="每页数量"),
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_admin_user),
):
    """获取订单列表 - 管理员"""
    try:
        query = db.query(MembershipOrder)

        if status:
            try:
                status_enum = MembershipOrderStatus(status)
                query = query.filter(MembershipOrder.status == status_enum)
            except ValueError:
                pass

        if user_id:
            query = query.filter(MembershipOrder.user_id == user_id)

        if search:
            query = query.join(User).filter(
                (MembershipOrder.order_no.contains(search))
                | (User.name.contains(search))
                | (User.phone.contains(search))
            )

        if start_date:
            try:
                start_dt = datetime.strptime(start_date, "%Y-%m-%d")
                query = query.filter(MembershipOrder.created_at >= start_dt)
            except ValueError:
                pass

        if end_date:
            try:
                end_dt = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)
                query = query.filter(MembershipOrder.created_at < end_dt)
            except ValueError:
                pass

        total = query.count()

        orders = (
            query.order_by(MembershipOrder.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )

        order_responses = []
        for order in orders:
            user = db.query(User).filter(User.id == order.user_id).first()
            plan = (
                db.query(MembershipPlan)
                .filter(MembershipPlan.id == order.plan_id)
                .first()
            )
            admin = (
                db.query(User).filter(User.id == order.admin_id).first()
                if order.admin_id
                else None
            )

            order_responses.append(
                AdminOrderResponse(
                    id=order.id,
                    order_no=order.order_no,
                    user_id=order.user_id,
                    user_name=user.name if user else "未知",
                    user_phone=user.phone if user else "",
                    plan_id=order.plan_id,
                    plan_name=plan.name if plan else "未知套餐",
                    plan_duration_months=plan.duration_months if plan else 0,
                    amount=float(order.amount),
                    original_amount=float(order.original_amount)
                    if order.original_amount
                    else None,
                    discount_amount=float(order.discount_amount),
                    payment_type=order.payment_type.value,
                    payment_method=order.payment_method,
                    status=order.status.value,
                    status_text=get_status_text(order.status),
                    balance_added=float(order.balance_added),
                    member_start_date=str(order.member_start_date)
                    if order.member_start_date
                    else None,
                    member_end_date=str(order.member_end_date)
                    if order.member_end_date
                    else None,
                    member_days=order.member_days,
                    apply_note=order.apply_note,
                    admin_id=order.admin_id,
                    admin_name=admin.name if admin else None,
                    review_note=order.review_note,
                    reviewed_at=str(order.reviewed_at) if order.reviewed_at else None,
                    paid_at=str(order.paid_at) if order.paid_at else None,
                    is_renewal=order.is_renewal,
                    created_at=str(order.created_at),
                    updated_at=str(order.updated_at),
                )
            )

        return AdminOrderListResponse(
            orders=order_responses,
            total=total,
            page=page,
            page_size=page_size,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取订单列表失败: {str(e)}")


@router.get("/stats", response_model=OrderStatsResponse)
async def get_order_stats(
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_admin_user),
):
    """获取订单统计"""
    try:
        total_orders = db.query(MembershipOrder).count()
        pending_orders = (
            db.query(MembershipOrder)
            .filter(MembershipOrder.status == MembershipOrderStatus.PENDING_REVIEW)
            .count()
        )
        approved_orders = (
            db.query(MembershipOrder)
            .filter(MembershipOrder.status == MembershipOrderStatus.APPROVED)
            .count()
        )
        rejected_orders = (
            db.query(MembershipOrder)
            .filter(MembershipOrder.status == MembershipOrderStatus.REJECTED)
            .count()
        )

        total_amount_orders = db.query(MembershipOrder).all()
        total_amount = sum(float(order.amount) for order in total_amount_orders)

        pending_orders_list = (
            db.query(MembershipOrder)
            .filter(MembershipOrder.status == MembershipOrderStatus.PENDING_REVIEW)
            .all()
        )
        pending_amount = sum(float(order.amount) for order in pending_orders_list)

        approved_orders_list = (
            db.query(MembershipOrder)
            .filter(MembershipOrder.status == MembershipOrderStatus.APPROVED)
            .all()
        )
        approved_amount = sum(float(order.amount) for order in approved_orders_list)

        month_start = datetime.now().replace(
            day=1, hour=0, minute=0, second=0, microsecond=0
        )
        month_orders = (
            db.query(MembershipOrder)
            .filter(MembershipOrder.created_at >= month_start)
            .count()
        )
        month_orders_list = (
            db.query(MembershipOrder)
            .filter(MembershipOrder.created_at >= month_start)
            .all()
        )
        month_amount = sum(float(order.amount) for order in month_orders_list)

        return OrderStatsResponse(
            total_orders=total_orders,
            pending_orders=pending_orders,
            approved_orders=approved_orders,
            rejected_orders=rejected_orders,
            total_amount=total_amount,
            pending_amount=pending_amount,
            approved_amount=approved_amount,
            month_orders=month_orders,
            month_amount=month_amount,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取订单统计失败: {str(e)}")


@router.get("/pending", response_model=AdminOrderListResponse)
async def get_pending_orders(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=50, description="每页数量"),
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_admin_user),
):
    """获取待审核订单列表 - 快捷入口"""
    try:
        query = db.query(MembershipOrder).filter(
            MembershipOrder.status == MembershipOrderStatus.PENDING_REVIEW
        )

        total = query.count()

        orders = (
            query.order_by(MembershipOrder.created_at.asc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )

        order_responses = []
        for order in orders:
            user = db.query(User).filter(User.id == order.user_id).first()
            plan = (
                db.query(MembershipPlan)
                .filter(MembershipPlan.id == order.plan_id)
                .first()
            )

            order_responses.append(
                AdminOrderResponse(
                    id=order.id,
                    order_no=order.order_no,
                    user_id=order.user_id,
                    user_name=user.name if user else "未知",
                    user_phone=user.phone if user else "",
                    plan_id=order.plan_id,
                    plan_name=plan.name if plan else "未知套餐",
                    plan_duration_months=plan.duration_months if plan else 0,
                    amount=float(order.amount),
                    original_amount=float(order.original_amount)
                    if order.original_amount
                    else None,
                    discount_amount=float(order.discount_amount),
                    payment_type=order.payment_type.value,
                    payment_method=order.payment_method,
                    status=order.status.value,
                    status_text=get_status_text(order.status),
                    balance_added=float(order.balance_added),
                    member_start_date=str(order.member_start_date)
                    if order.member_start_date
                    else None,
                    member_end_date=str(order.member_end_date)
                    if order.member_end_date
                    else None,
                    member_days=order.member_days,
                    apply_note=order.apply_note,
                    admin_id=order.admin_id,
                    admin_name=None,
                    review_note=order.review_note,
                    reviewed_at=str(order.reviewed_at) if order.reviewed_at else None,
                    paid_at=str(order.paid_at) if order.paid_at else None,
                    is_renewal=order.is_renewal,
                    created_at=str(order.created_at),
                    updated_at=str(order.updated_at),
                )
            )

        return AdminOrderListResponse(
            orders=order_responses,
            total=total,
            page=page,
            page_size=page_size,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取待审核订单失败: {str(e)}")


@router.get("/{order_id}", response_model=dict)
async def get_order_detail(
    order_id: int,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_admin_user),
):
    """获取订单详情 - 管理员"""
    try:
        order = db.query(MembershipOrder).filter(MembershipOrder.id == order_id).first()

        if not order:
            raise HTTPException(status_code=404, detail="订单不存在")

        user = db.query(User).filter(User.id == order.user_id).first()
        plan = (
            db.query(MembershipPlan).filter(MembershipPlan.id == order.plan_id).first()
        )
        admin = (
            db.query(User).filter(User.id == order.admin_id).first()
            if order.admin_id
            else None
        )

        balance_account = (
            db.query(UserBalanceAccount)
            .filter(UserBalanceAccount.user_id == order.user_id)
            .first()
        )

        audit_records = (
            db.query(MembershipOrderAudit)
            .filter(MembershipOrderAudit.order_id == order_id)
            .all()
        )

        return {
            "order": {
                "id": order.id,
                "order_no": order.order_no,
                "amount": float(order.amount),
                "original_amount": float(order.original_amount)
                if order.original_amount
                else None,
                "discount_amount": float(order.discount_amount),
                "payment_type": order.payment_type.value,
                "payment_method": order.payment_method,
                "status": order.status.value,
                "status_text": get_status_text(order.status),
                "balance_added": float(order.balance_added),
                "member_start_date": str(order.member_start_date)
                if order.member_start_date
                else None,
                "member_end_date": str(order.member_end_date)
                if order.member_end_date
                else None,
                "member_days": order.member_days,
                "apply_note": order.apply_note,
                "review_note": order.review_note,
                "is_renewal": order.is_renewal,
                "created_at": str(order.created_at),
                "reviewed_at": str(order.reviewed_at) if order.reviewed_at else None,
            },
            "user": {
                "id": user.id if user else None,
                "name": user.name if user else "未知",
                "phone": user.phone if user else "",
                "email": user.email if user else None,
            },
            "plan": {
                "id": plan.id if plan else None,
                "name": plan.name if plan else "未知",
                "description": plan.description if plan else None,
                "duration_months": plan.duration_months if plan else 0,
                "features": plan.features if plan else [],
                "icon": plan.icon if plan else "👑",
            },
            "balance": {
                "membership_balance": float(balance_account.membership_balance)
                if balance_account
                else 0,
                "service_balance": float(balance_account.service_balance)
                if balance_account
                else 0,
                "total_balance": float(balance_account.total_balance)
                if balance_account
                else 0,
            },
            "admin": {
                "id": admin.id if admin else None,
                "name": admin.name if admin else None,
            },
            "audit_records": [
                {
                    "id": audit.id,
                    "action": audit.action,
                    "admin_name": db.query(User)
                    .filter(User.id == audit.admin_id)
                    .first()
                    .name
                    if audit.admin_id
                    else None,
                    "before_status": audit.before_status.value
                    if audit.before_status
                    else None,
                    "after_status": audit.after_status.value
                    if audit.after_status
                    else None,
                    "note": audit.note,
                    "created_at": str(audit.created_at),
                }
                for audit in audit_records
            ],
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取订单详情失败: {str(e)}")


@router.put("/{order_id}/review", response_model=dict)
async def review_order(
    order_id: int,
    request: OrderReviewRequest,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_admin_user),
):
    """审核订单"""
    try:
        order = db.query(MembershipOrder).filter(MembershipOrder.id == order_id).first()

        if not order:
            raise HTTPException(status_code=404, detail="订单不存在")

        if order.status != MembershipOrderStatus.PENDING_REVIEW:
            raise HTTPException(status_code=400, detail="只能审核待审核状态的订单")

        before_status = order.status

        if request.approved:
            order.status = MembershipOrderStatus.APPROVED
            order.admin_id = admin_user.id
            order.review_note = request.review_note
            order.reviewed_at = datetime.now()
            order.paid_at = datetime.now()

            balance_to_add = Decimal(str(request.balance_added or float(order.amount)))
            order.balance_added = balance_to_add

            plan = (
                db.query(MembershipPlan)
                .filter(MembershipPlan.id == order.plan_id)
                .first()
            )

            start_date = None
            if request.member_start_date:
                try:
                    start_date = datetime.strptime(
                        request.member_start_date, "%Y-%m-%d"
                    ).date()
                except ValueError:
                    start_date = date.today()
            else:
                start_date = date.today()

            end_date = start_date + timedelta(days=order.member_days)

            order.member_start_date = start_date
            order.member_end_date = end_date

            balance_account = (
                db.query(UserBalanceAccount)
                .filter(UserBalanceAccount.user_id == order.user_id)
                .first()
            )

            if not balance_account:
                balance_account = UserBalanceAccount(
                    user_id=order.user_id,
                    membership_balance=Decimal(0),
                    service_balance=Decimal(0),
                    gift_balance=Decimal(0),
                    total_balance=Decimal(0),
                )
                db.add(balance_account)

            before_membership = balance_account.membership_balance
            before_total = balance_account.total_balance

            balance_account.membership_balance += balance_to_add
            balance_account.total_membership_charged += balance_to_add
            balance_account.membership_expire_date = end_date
            balance_account.update_total_balance()
            balance_account.last_transaction_at = datetime.now()

            transaction = BalanceTransaction(
                transaction_no=f"TX{datetime.now().strftime('%Y%m%d%H%M%S%f')}",
                user_id=order.user_id,
                transaction_type=TransactionType.MEMBERSHIP_CHARGE,
                amount=balance_to_add,
                balance_type=BalanceType.MEMBERSHIP,
                before_membership_balance=before_membership,
                before_service_balance=balance_account.service_balance,
                before_gift_balance=balance_account.gift_balance,
                before_total_balance=before_total,
                after_membership_balance=balance_account.membership_balance,
                after_service_balance=balance_account.service_balance,
                after_gift_balance=balance_account.gift_balance,
                after_total_balance=balance_account.total_balance,
                reference_type="membership_order",
                reference_id=order.id,
                reference_no=order.order_no,
                description=f"会员套餐充值 - {plan.name if plan else '未知套餐'}",
                expire_date=end_date,
            )
            db.add(transaction)

            audit = MembershipOrderAudit(
                order_id=order.id,
                action="approve",
                admin_id=admin_user.id,
                before_status=before_status,
                after_status=MembershipOrderStatus.APPROVED,
                note=request.review_note or "审核通过，余额已入账",
            )
            db.add(audit)

            db.commit()

            return {
                "success": True,
                "message": "订单审核通过，余额已入账",
                "balance_added": float(balance_to_add),
                "member_start_date": str(start_date),
                "member_end_date": str(end_date),
                "membership_balance": float(balance_account.membership_balance),
                "total_balance": float(balance_account.total_balance),
            }
        else:
            order.status = MembershipOrderStatus.REJECTED
            order.admin_id = admin_user.id
            order.review_note = request.review_note or "审核拒绝"
            order.reviewed_at = datetime.now()

            audit = MembershipOrderAudit(
                order_id=order.id,
                action="reject",
                admin_id=admin_user.id,
                before_status=before_status,
                after_status=MembershipOrderStatus.REJECTED,
                note=request.review_note or "审核拒绝",
            )
            db.add(audit)

            db.commit()

            return {
                "success": True,
                "message": "订单已拒绝",
            }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"审核订单失败: {str(e)}")


@router.post("/{order_id}/cancel", response_model=dict)
async def cancel_order_by_admin(
    order_id: int,
    reason: Optional[str] = Body(None, embed=True, description="取消原因"),
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_admin_user),
):
    """管理员取消订单"""
    try:
        order = db.query(MembershipOrder).filter(MembershipOrder.id == order_id).first()

        if not order:
            raise HTTPException(status_code=404, detail="订单不存在")

        if order.status not in [
            MembershipOrderStatus.PENDING_REVIEW,
            MembershipOrderStatus.APPROVED,
        ]:
            raise HTTPException(status_code=400, detail="只能取消待审核或已通过的订单")

        before_status = order.status

        if order.status == MembershipOrderStatus.APPROVED:
            balance_account = (
                db.query(UserBalanceAccount)
                .filter(UserBalanceAccount.user_id == order.user_id)
                .first()
            )

            if balance_account and order.balance_added > 0:
                before_membership = balance_account.membership_balance
                before_total = balance_account.total_balance

                balance_account.membership_balance -= order.balance_added
                balance_account.total_membership_charged -= order.balance_added
                balance_account.update_total_balance()

                transaction = BalanceTransaction(
                    transaction_no=f"TX{datetime.now().strftime('%Y%m%d%H%M%S%f')}",
                    user_id=order.user_id,
                    transaction_type=TransactionType.REFUND,
                    amount=-order.balance_added,
                    balance_type=BalanceType.MEMBERSHIP,
                    before_membership_balance=before_membership,
                    before_service_balance=balance_account.service_balance,
                    before_gift_balance=balance_account.gift_balance,
                    before_total_balance=before_total,
                    after_membership_balance=balance_account.membership_balance,
                    after_service_balance=balance_account.service_balance,
                    after_gift_balance=balance_account.gift_balance,
                    after_total_balance=balance_account.total_balance,
                    reference_type="membership_order",
                    reference_id=order.id,
                    reference_no=order.order_no,
                    description=f"订单取消退款 - {reason or '管理员取消'}",
                )
                db.add(transaction)

                balance_account.total_refunded += order.balance_added

        order.status = MembershipOrderStatus.CANCELLED
        order.cancel_reason = reason or "管理员取消"
        order.updated_at = datetime.now()

        audit = MembershipOrderAudit(
            order_id=order.id,
            action="cancel",
            admin_id=admin_user.id,
            before_status=before_status,
            after_status=MembershipOrderStatus.CANCELLED,
            note=reason or "管理员取消订单",
        )
        db.add(audit)

        db.commit()

        return {
            "success": True,
            "message": "订单已取消",
            "refunded": float(order.balance_added) if order.balance_added > 0 else 0,
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"取消订单失败: {str(e)}")
