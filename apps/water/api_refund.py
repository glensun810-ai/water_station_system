"""
退款API
提供退款申请、查询等功能
"""

from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, date
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import and_
import uuid
import logging

from config.database import get_db
from models import User, PaymentOrder, MembershipPlan
from models.payment_order import PaymentOrder as PaymentOrderModel
from models.refund_record import RefundRecord

router = APIRouter()
logger = logging.getLogger(__name__)


class RefundApply(BaseModel):
    order_no: str
    reason: str


class RefundResponse(BaseModel):
    id: int
    refund_no: str
    order_id: int
    user_id: int
    original_amount: float
    refund_amount: float
    used_days: Optional[int]
    reason: Optional[str]
    status: str
    refund_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class RefundList(BaseModel):
    refunds: List[RefundResponse]
    total: int


def generate_refund_no():
    """生成退款单号"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    random_str = uuid.uuid4().hex[:8].upper()
    return f"RF{timestamp}{random_str}"


def calculate_refund_amount(original_amount, total_days, used_days):
    """
    计算退款金额（按比例）

    Args:
        original_amount: 原订单金额
        total_days: 会员总天数
        used_days: 已使用天数

    Returns:
        退款金额
    """
    if used_days >= total_days:
        return Decimal("0.00")

    # 按比例计算
    unused_days = total_days - used_days
    refund_amount = original_amount * unused_days / total_days

    # 保留两位小数
    return refund_amount.quantize(Decimal("0.01"))


@router.post("/api/payment/refund")
async def apply_refund(
    refund_data: RefundApply, request: Request, db: Session = Depends(get_db)
):
    """
    申请退款
    """
    try:
        # 获取当前用户
        user_id = request.headers.get("X-User-Id")
        if not user_id:
            raise HTTPException(status_code=401, detail="未登录")

        user_id = int(user_id)

        # 查询订单
        order = (
            db.query(PaymentOrderModel)
            .filter(PaymentOrderModel.order_no == refund_data.order_no)
            .first()
        )

        if not order:
            raise HTTPException(status_code=404, detail="订单不存在")

        # 验证订单所属用户
        if order.user_id != user_id:
            raise HTTPException(status_code=403, detail="无权操作此订单")

        # 验证订单状态（只能退款已支付的订单）
        if order.status != "paid":
            raise HTTPException(status_code=400, detail="只能退款已支付的订单")

        # 检查是否已申请退款
        existing_refund = (
            db.query(RefundRecord)
            .filter(
                and_(
                    RefundRecord.order_id == order.id, RefundRecord.status == "pending"
                )
            )
            .first()
        )

        if existing_refund:
            raise HTTPException(status_code=400, detail="已存在待处理的退款申请")

        # 获取套餐信息
        plan = (
            db.query(MembershipPlan).filter(MembershipPlan.id == order.plan_id).first()
        )

        if not plan:
            raise HTTPException(status_code=404, detail="会员套餐不存在")

        # 计算已使用天数
        # TODO: 从会员记录中获取实际开始时间
        paid_date = order.paid_at.date() if order.paid_at else date.today()
        today = date.today()
        used_days = (today - paid_date).days

        # 会员总天数
        total_days = plan.duration_months * 30

        # 计算退款金额
        refund_amount = calculate_refund_amount(
            original_amount=order.amount, total_days=total_days, used_days=used_days
        )

        if refund_amount <= Decimal("0.00"):
            raise HTTPException(status_code=400, detail="会员已过期，无法退款")

        # 创建退款记录
        refund_no = generate_refund_no()
        refund = RefundRecord(
            refund_no=refund_no,
            order_id=order.id,
            user_id=user_id,
            original_amount=order.amount,
            refund_amount=refund_amount,
            used_days=used_days,
            reason=refund_data.reason,
            status="pending",
        )

        db.add(refund)
        db.commit()
        db.refresh(refund)

        logger.info(
            f"创建退款申请成功: refund_no={refund_no}, order_no={refund_data.order_no}"
        )

        return {
            "success": True,
            "message": "退款申请已提交",
            "refund_no": refund_no,
            "refund_amount": float(refund_amount),
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"申请退款失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"申请退款失败: {str(e)}")


@router.get("/api/payment/refund/{refund_no}", response_model=RefundResponse)
async def get_refund(refund_no: str, request: Request, db: Session = Depends(get_db)):
    """
    查询退款详情
    """
    try:
        # 获取当前用户
        user_id = request.headers.get("X-User-Id")
        if not user_id:
            raise HTTPException(status_code=401, detail="未登录")

        user_id = int(user_id)

        refund = (
            db.query(RefundRecord).filter(RefundRecord.refund_no == refund_no).first()
        )

        if not refund:
            raise HTTPException(status_code=404, detail="退款记录不存在")

        # 验证退款所属用户
        if refund.user_id != user_id:
            raise HTTPException(status_code=403, detail="无权查看此退款")

        return {
            "id": refund.id,
            "refund_no": refund.refund_no,
            "order_id": refund.order_id,
            "user_id": refund.user_id,
            "original_amount": float(refund.original_amount),
            "refund_amount": float(refund.refund_amount),
            "used_days": refund.used_days,
            "reason": refund.reason,
            "status": refund.status,
            "refund_at": refund.refund_at,
            "created_at": refund.created_at,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"查询退款详情失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"查询退款详情失败: {str(e)}")


@router.get("/api/payment/refunds/user/{user_id}", response_model=RefundList)
async def get_user_refunds(
    user_id: int,
    request: Request,
    status: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
):
    """
    获取用户退款列表
    """
    try:
        # 验证权限
        current_user_id = request.headers.get("X-User-Id")
        if not current_user_id:
            raise HTTPException(status_code=401, detail="未登录")

        current_user_id = int(current_user_id)

        # 只能查看自己的退款（管理员可以查看所有）
        if current_user_id != user_id:
            raise HTTPException(status_code=403, detail="无权查看此用户退款")

        query = db.query(RefundRecord).filter(RefundRecord.user_id == user_id)

        if status:
            query = query.filter(RefundRecord.status == status)

        total = query.count()
        refunds = (
            query.order_by(RefundRecord.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )

        return {
            "refunds": [
                {
                    "id": refund.id,
                    "refund_no": refund.refund_no,
                    "order_id": refund.order_id,
                    "user_id": refund.user_id,
                    "original_amount": float(refund.original_amount),
                    "refund_amount": float(refund.refund_amount),
                    "used_days": refund.used_days,
                    "reason": refund.reason,
                    "status": refund.status,
                    "refund_at": refund.refund_at,
                    "created_at": refund.created_at,
                }
                for refund in refunds
            ],
            "total": total,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取退款列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取退款列表失败: {str(e)}")


# ==================== 管理员退款处理接口 ====================


@router.post("/api/admin/payment/refund/{refund_no}/approve")
async def approve_refund(
    refund_no: str, request: Request, db: Session = Depends(get_db)
):
    """
    管理员批准退款
    """
    try:
        # TODO: 添加管理员权限验证

        refund = (
            db.query(RefundRecord).filter(RefundRecord.refund_no == refund_no).first()
        )

        if not refund:
            raise HTTPException(status_code=404, detail="退款记录不存在")

        if refund.status != "pending":
            raise HTTPException(status_code=400, detail="退款状态不正确")

        # 获取订单信息
        order = (
            db.query(PaymentOrderModel)
            .filter(PaymentOrderModel.id == refund.order_id)
            .first()
        )

        if not order:
            raise HTTPException(status_code=404, detail="订单不存在")

        # TODO: 调用支付宝退款接口
        # from utils.alipay_service import create_alipay_service
        # alipay_service = create_alipay_service(config)
        # result = alipay_service.refund(
        #     order_no=order.order_no,
        #     refund_amount=float(refund.refund_amount),
        #     refund_reason=refund.reason
        # )

        # 更新退款状态
        refund.status = "success"
        refund.refund_at = datetime.now()
        # refund.refund_trade_no = result.get("refund_no")

        # 更新订单状态
        order.status = "refunded"

        db.commit()

        logger.info(f"退款批准成功: refund_no={refund_no}")

        return {"success": True, "message": "退款已批准"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"批准退款失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"批准退款失败: {str(e)}")


@router.post("/api/admin/payment/refund/{refund_no}/reject")
async def reject_refund(
    refund_no: str, reject_reason: str, request: Request, db: Session = Depends(get_db)
):
    """
    管理员拒绝退款
    """
    try:
        # TODO: 添加管理员权限验证

        refund = (
            db.query(RefundRecord).filter(RefundRecord.refund_no == refund_no).first()
        )

        if not refund:
            raise HTTPException(status_code=404, detail="退款记录不存在")

        if refund.status != "pending":
            raise HTTPException(status_code=400, detail="退款状态不正确")

        # 更新退款状态
        refund.status = "failed"
        refund.reject_reason = reject_reason

        db.commit()

        logger.info(f"退款拒绝成功: refund_no={refund_no}, reason={reject_reason}")

        return {"success": True, "message": "退款已拒绝"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"拒绝退款失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"拒绝退款失败: {str(e)}")
