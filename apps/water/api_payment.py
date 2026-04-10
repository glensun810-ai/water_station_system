"""
会员支付订单API
提供订单创建、查询、支付等功能
"""

from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import and_
import uuid
import json
import logging

from config.database import get_db
from models import User, MembershipPlan, PaymentOrder
from models.payment_order import PaymentOrder as PaymentOrderModel

router = APIRouter()
logger = logging.getLogger(__name__)


class OrderCreate(BaseModel):
    plan_id: int
    payment_method: str  # alipay or wechat


class OrderResponse(BaseModel):
    id: int
    order_no: str
    user_id: int
    plan_id: int
    amount: float
    payment_method: Optional[str]
    status: str
    paid_at: Optional[datetime]
    trade_no: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class OrderList(BaseModel):
    orders: List[OrderResponse]
    total: int


def generate_order_no():
    """生成订单号"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    random_str = uuid.uuid4().hex[:8].upper()
    return f"MP{timestamp}{random_str}"


@router.post("/api/payment/orders")
async def create_order(
    order_data: OrderCreate, request: Request, db: Session = Depends(get_db)
):
    """
    创建支付订单
    """
    try:
        # 获取当前用户（从请求中获取）
        # TODO: 从JWT token中获取用户ID，这里暂时使用测试用户
        user_id = request.headers.get("X-User-Id")
        if not user_id:
            raise HTTPException(status_code=401, detail="未登录")

        user_id = int(user_id)

        # 验证用户是否存在
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")

        # 验证套餐是否存在且有效
        plan = (
            db.query(MembershipPlan)
            .filter(
                and_(
                    MembershipPlan.id == order_data.plan_id,
                    MembershipPlan.is_active == True,
                )
            )
            .first()
        )

        if not plan:
            raise HTTPException(status_code=404, detail="会员套餐不存在或已下架")

        # 检查用户是否已有未支付订单
        existing_order = (
            db.query(PaymentOrderModel)
            .filter(
                and_(
                    PaymentOrderModel.user_id == user_id,
                    PaymentOrderModel.status == "pending",
                )
            )
            .first()
        )

        if existing_order:
            raise HTTPException(
                status_code=400, detail="您已有未支付的订单，请先支付或取消"
            )

        # 创建订单
        order_no = generate_order_no()
        order = PaymentOrderModel(
            order_no=order_no,
            user_id=user_id,
            plan_id=plan.id,
            amount=plan.price,
            payment_method=order_data.payment_method,
            status="pending",
        )

        db.add(order)
        db.commit()
        db.refresh(order)

        logger.info(
            f"创建订单成功: order_no={order_no}, user_id={user_id}, plan_id={plan.id}"
        )

        return {
            "success": True,
            "message": "订单创建成功",
            "order_no": order_no,
            "amount": float(plan.price),
            "plan_name": plan.name,
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"创建订单失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"创建订单失败: {str(e)}")


@router.get("/api/payment/orders/{order_no}", response_model=OrderResponse)
async def get_order(order_no: str, request: Request, db: Session = Depends(get_db)):
    """
    查询订单详情
    """
    try:
        # 获取当前用户
        user_id = request.headers.get("X-User-Id")
        if not user_id:
            raise HTTPException(status_code=401, detail="未登录")

        user_id = int(user_id)

        order = (
            db.query(PaymentOrderModel)
            .filter(PaymentOrderModel.order_no == order_no)
            .first()
        )

        if not order:
            raise HTTPException(status_code=404, detail="订单不存在")

        # 验证订单所属用户
        if order.user_id != user_id:
            raise HTTPException(status_code=403, detail="无权查看此订单")

        return {
            "id": order.id,
            "order_no": order.order_no,
            "user_id": order.user_id,
            "plan_id": order.plan_id,
            "amount": float(order.amount),
            "payment_method": order.payment_method,
            "status": order.status,
            "paid_at": order.paid_at,
            "trade_no": order.trade_no,
            "created_at": order.created_at,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"查询订单失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"查询订单失败: {str(e)}")


@router.get("/api/payment/orders/user/{user_id}", response_model=OrderList)
async def get_user_orders(
    user_id: int,
    request: Request,
    status: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
):
    """
    获取用户订单列表
    """
    try:
        # 验证权限
        current_user_id = request.headers.get("X-User-Id")
        if not current_user_id:
            raise HTTPException(status_code=401, detail="未登录")

        current_user_id = int(current_user_id)

        # 只能查看自己的订单（管理员可以查看所有）
        # TODO: 添加管理员权限判断
        if current_user_id != user_id:
            raise HTTPException(status_code=403, detail="无权查看此用户订单")

        query = db.query(PaymentOrderModel).filter(PaymentOrderModel.user_id == user_id)

        if status:
            query = query.filter(PaymentOrderModel.status == status)

        total = query.count()
        orders = (
            query.order_by(PaymentOrderModel.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )

        return {
            "orders": [
                {
                    "id": order.id,
                    "order_no": order.order_no,
                    "user_id": order.user_id,
                    "plan_id": order.plan_id,
                    "amount": float(order.amount),
                    "payment_method": order.payment_method,
                    "status": order.status,
                    "paid_at": order.paid_at,
                    "trade_no": order.trade_no,
                    "created_at": order.created_at,
                }
                for order in orders
            ],
            "total": total,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取订单列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取订单列表失败: {str(e)}")


@router.post("/api/payment/orders/{order_no}/cancel")
async def cancel_order(order_no: str, request: Request, db: Session = Depends(get_db)):
    """
    取消订单
    """
    try:
        # 获取当前用户
        user_id = request.headers.get("X-User-Id")
        if not user_id:
            raise HTTPException(status_code=401, detail="未登录")

        user_id = int(user_id)

        order = (
            db.query(PaymentOrderModel)
            .filter(PaymentOrderModel.order_no == order_no)
            .first()
        )

        if not order:
            raise HTTPException(status_code=404, detail="订单不存在")

        # 验证订单所属用户
        if order.user_id != user_id:
            raise HTTPException(status_code=403, detail="无权操作此订单")

        # 只能取消未支付的订单
        if order.status != "pending":
            raise HTTPException(status_code=400, detail="只能取消未支付的订单")

        order.status = "cancelled"
        order.cancel_reason = "用户主动取消"
        db.commit()

        logger.info(f"订单取消成功: order_no={order_no}, user_id={user_id}")

        return {"success": True, "message": "订单取消成功"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"取消订单失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"取消订单失败: {str(e)}")


# ==================== 支付宝支付相关接口 ====================


@router.post("/api/payment/alipay/create")
async def create_alipay_payment(
    order_no: str, request: Request, db: Session = Depends(get_db)
):
    """
    创建支付宝支付
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
            .filter(PaymentOrderModel.order_no == order_no)
            .first()
        )

        if not order:
            raise HTTPException(status_code=404, detail="订单不存在")

        # 验证订单所属用户
        if order.user_id != user_id:
            raise HTTPException(status_code=403, detail="无权操作此订单")

        # 验证订单状态
        if order.status != "pending":
            raise HTTPException(status_code=400, detail="订单状态不正确")

        # 获取套餐信息
        plan = (
            db.query(MembershipPlan).filter(MembershipPlan.id == order.plan_id).first()
        )

        if not plan:
            raise HTTPException(status_code=404, detail="会员套餐不存在")

        # TODO: 从配置中读取支付宝配置
        # 这里需要从配置文件或环境变量中读取
        from utils.alipay_service import create_alipay_service

        alipay_config = {
            "app_id": "YOUR_APP_ID",  # 从配置读取
            "private_key_path": "/path/to/private_key.pem",
            "alipay_public_key_path": "/path/to/alipay_public_key.pem",
            "debug": True,  # 沙箱环境
            "notify_url": "http://yourdomain.com/api/payment/callback/alipay",
            "return_url": "http://yourdomain.com/payment/result",
        }

        alipay_service = create_alipay_service(alipay_config)

        # 创建支付
        result = alipay_service.create_payment(
            order_no=order_no,
            amount=float(order.amount),
            subject=f"会员套餐-{plan.name}",
            body=plan.description,
        )

        if result.get("success"):
            logger.info(f"创建支付宝支付成功: order_no={order_no}")
            return {"success": True, "pay_url": result.get("pay_url")}
        else:
            raise HTTPException(
                status_code=500, detail=result.get("message", "创建支付失败")
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建支付宝支付失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"创建支付失败: {str(e)}")


@router.post("/api/payment/callback/alipay")
async def alipay_callback(request: Request, db: Session = Depends(get_db)):
    """
    支付宝支付回调
    """
    try:
        # 获取回调数据
        form_data = await request.form()
        data = dict(form_data)

        logger.info(f"收到支付宝回调: {data}")

        # TODO: 从配置中读取支付宝配置
        from utils.alipay_service import create_alipay_service

        alipay_config = {
            "app_id": "YOUR_APP_ID",
            "private_key_path": "/path/to/private_key.pem",
            "alipay_public_key_path": "/path/to/alipay_public_key.pem",
            "debug": True,
        }

        alipay_service = create_alipay_service(alipay_config)

        # 验证签名
        result = alipay_service.verify_notify(data)

        if result.get("success"):
            order_no = result.get("order_no")
            trade_no = result.get("trade_no")
            trade_status = result.get("trade_status")

            # 查询订单
            order = (
                db.query(PaymentOrderModel)
                .filter(PaymentOrderModel.order_no == order_no)
                .first()
            )

            if not order:
                logger.error(f"订单不存在: order_no={order_no}")
                return "fail"

            # 更新订单状态
            if trade_status in ("TRADE_SUCCESS", "TRADE_FINISHED"):
                order.status = "paid"
                order.trade_no = trade_no
                order.paid_at = datetime.now()

                # TODO: 更新用户会员信息
                # 创建或更新会员记录

                db.commit()

                logger.info(f"订单支付成功: order_no={order_no}, trade_no={trade_no}")

                return "success"
            else:
                logger.warning(
                    f"支付状态异常: order_no={order_no}, trade_status={trade_status}"
                )
                return "fail"
        else:
            logger.error(f"支付宝回调验证失败: {result}")
            return "fail"

    except Exception as e:
        logger.error(f"处理支付宝回调失败: {str(e)}")
        db.rollback()
        return "fail"


@router.get("/api/payment/orders/{order_no}/status")
async def get_payment_status(
    order_no: str, request: Request, db: Session = Depends(get_db)
):
    """
    查询订单支付状态（轮询接口）
    """
    try:
        # 获取当前用户
        user_id = request.headers.get("X-User-Id")
        if not user_id:
            raise HTTPException(status_code=401, detail="未登录")

        user_id = int(user_id)

        order = (
            db.query(PaymentOrderModel)
            .filter(PaymentOrderModel.order_no == order_no)
            .first()
        )

        if not order:
            raise HTTPException(status_code=404, detail="订单不存在")

        # 验证订单所属用户
        if order.user_id != user_id:
            raise HTTPException(status_code=403, detail="无权查看此订单")

        return {
            "success": True,
            "status": order.status,
            "paid_at": order.paid_at.isoformat() if order.paid_at else None,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"查询订单状态失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"查询订单状态失败: {str(e)}")
