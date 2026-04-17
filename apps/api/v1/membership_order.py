"""
会员订单API路由 - 用户端
支持线下支付申请和订单管理
"""

from fastapi import APIRouter, Depends, HTTPException, Query
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
from depends.auth import get_current_user

router = APIRouter(prefix="/membership/orders", tags=["会员订单"])


class OrderCreateRequest(BaseModel):
    plan_id: int = Field(..., description="会员套餐ID")
    payment_method: Optional[str] = Field(
        None, description="支付方式(bank_transfer/cash/check)"
    )
    apply_note: Optional[str] = Field(None, description="申请备注")
    is_renewal: bool = Field(False, description="是否续费")


class OrderResponse(BaseModel):
    id: int
    order_no: str
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
    review_note: Optional[str]
    reviewed_at: Optional[str]
    paid_at: Optional[str]
    is_renewal: bool
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class OrderListResponse(BaseModel):
    orders: List[OrderResponse]
    total: int
    page: int
    page_size: int


class OrderDetailResponse(BaseModel):
    order: OrderResponse
    plan_info: dict
    user_info: dict
    balance_info: Optional[dict]


def generate_order_no(user_id: int) -> str:
    """生成订单号"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    random_suffix = str(random.randint(100000, 999999))
    return f"MB{timestamp}{random_suffix}"


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


@router.post("", response_model=dict)
async def create_order(
    request: OrderCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """创建会员订单 - 提交线下支付申请"""
    try:
        plan = (
            db.query(MembershipPlan)
            .filter(
                MembershipPlan.id == request.plan_id, MembershipPlan.is_active == True
            )
            .first()
        )

        if not plan:
            raise HTTPException(status_code=404, detail="会员套餐不存在或已停用")

        existing_pending = (
            db.query(MembershipOrder)
            .filter(
                MembershipOrder.user_id == current_user.id,
                MembershipOrder.status == MembershipOrderStatus.PENDING_REVIEW,
            )
            .first()
        )

        if existing_pending:
            raise HTTPException(
                status_code=400, detail="您有待审核的订单，请等待审核完成后再提交新订单"
            )

        order = MembershipOrder(
            order_no=generate_order_no(current_user.id),
            user_id=current_user.id,
            plan_id=plan.id,
            amount=Decimal(str(plan.price)),
            original_amount=Decimal(str(plan.original_price))
            if plan.original_price
            else None,
            discount_amount=Decimal(str(plan.original_price - plan.price))
            if plan.original_price and plan.original_price > plan.price
            else Decimal(0),
            payment_type=PaymentType.OFFLINE,
            payment_method=request.payment_method or "bank_transfer",
            status=MembershipOrderStatus.PENDING_REVIEW,
            apply_note=request.apply_note,
            is_renewal=request.is_renewal,
            member_days=plan.duration_months * 30,
        )

        db.add(order)
        db.commit()
        db.refresh(order)

        return {
            "success": True,
            "message": "订单已提交，请等待管理员审核",
            "order_no": order.order_no,
            "order_id": order.id,
            "amount": float(order.amount),
            "plan_name": plan.name,
            "duration_months": plan.duration_months,
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"创建订单失败: {str(e)}")


@router.get("/my", response_model=OrderListResponse)
async def get_my_orders(
    status: Optional[str] = Query(None, description="订单状态筛选"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=50, description="每页数量"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取我的订单列表"""
    try:
        query = db.query(MembershipOrder).filter(
            MembershipOrder.user_id == current_user.id
        )

        if status:
            try:
                status_enum = MembershipOrderStatus(status)
                query = query.filter(MembershipOrder.status == status_enum)
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
            plan = (
                db.query(MembershipPlan)
                .filter(MembershipPlan.id == order.plan_id)
                .first()
            )
            order_responses.append(
                OrderResponse(
                    id=order.id,
                    order_no=order.order_no,
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
                    review_note=order.review_note,
                    reviewed_at=str(order.reviewed_at) if order.reviewed_at else None,
                    paid_at=str(order.paid_at) if order.paid_at else None,
                    is_renewal=order.is_renewal,
                    created_at=str(order.created_at),
                    updated_at=str(order.updated_at),
                )
            )

        return OrderListResponse(
            orders=order_responses,
            total=total,
            page=page,
            page_size=page_size,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取订单失败: {str(e)}")


@router.get("/{order_id}", response_model=OrderDetailResponse)
async def get_order_detail(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取订单详情"""
    try:
        order = (
            db.query(MembershipOrder)
            .filter(
                MembershipOrder.id == order_id,
                MembershipOrder.user_id == current_user.id,
            )
            .first()
        )

        if not order:
            raise HTTPException(status_code=404, detail="订单不存在")

        plan = (
            db.query(MembershipPlan).filter(MembershipPlan.id == order.plan_id).first()
        )

        balance_account = (
            db.query(UserBalanceAccount)
            .filter(UserBalanceAccount.user_id == current_user.id)
            .first()
        )

        order_response = OrderResponse(
            id=order.id,
            order_no=order.order_no,
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
            review_note=order.review_note,
            reviewed_at=str(order.reviewed_at) if order.reviewed_at else None,
            paid_at=str(order.paid_at) if order.paid_at else None,
            is_renewal=order.is_renewal,
            created_at=str(order.created_at),
            updated_at=str(order.updated_at),
        )

        plan_info = {
            "id": plan.id if plan else None,
            "name": plan.name if plan else "未知",
            "description": plan.description if plan else None,
            "features": plan.features if plan else [],
            "icon": plan.icon if plan else "👑",
        }

        user_info = {
            "id": current_user.id,
            "name": current_user.name,
            "phone": current_user.phone,
        }

        balance_info = None
        if balance_account:
            balance_info = {
                "membership_balance": float(balance_account.membership_balance),
                "service_balance": float(balance_account.service_balance),
                "gift_balance": float(balance_account.gift_balance),
                "total_balance": float(balance_account.total_balance),
            }

        return OrderDetailResponse(
            order=order_response,
            plan_info=plan_info,
            user_info=user_info,
            balance_info=balance_info,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取订单详情失败: {str(e)}")


@router.post("/{order_id}/cancel", response_model=dict)
async def cancel_order(
    order_id: int,
    reason: Optional[str] = Query(None, description="取消原因"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """取消订单"""
    try:
        order = (
            db.query(MembershipOrder)
            .filter(
                MembershipOrder.id == order_id,
                MembershipOrder.user_id == current_user.id,
            )
            .first()
        )

        if not order:
            raise HTTPException(status_code=404, detail="订单不存在")

        if order.status != MembershipOrderStatus.PENDING_REVIEW:
            raise HTTPException(status_code=400, detail="只能取消待审核的订单")

        order.status = MembershipOrderStatus.CANCELLED
        order.cancel_reason = reason or "用户主动取消"
        order.updated_at = datetime.now()

        audit = MembershipOrderAudit(
            order_id=order.id,
            action="cancel",
            admin_id=current_user.id,
            before_status=MembershipOrderStatus.PENDING_REVIEW,
            after_status=MembershipOrderStatus.CANCELLED,
            note=reason or "用户主动取消",
        )

        db.add(audit)
        db.commit()

        return {
            "success": True,
            "message": "订单已取消",
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"取消订单失败: {str(e)}")


@router.get("/pending-count", response_model=dict)
async def get_pending_count(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取待审核订单数量"""
    try:
        count = (
            db.query(MembershipOrder)
            .filter(
                MembershipOrder.user_id == current_user.id,
                MembershipOrder.status == MembershipOrderStatus.PENDING_REVIEW,
            )
            .count()
        )

        return {
            "pending_count": count,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取待审核订单数量失败: {str(e)}")
