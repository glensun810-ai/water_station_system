"""
Unified Order API - 统一订单管理接口
支持先用后付和先付后用两种模式的统一管理
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from typing import Optional, List, Dict
from datetime import datetime
import random
import json

# 本地定义 get_db，避免与 main.py 循环导入
SQLALCHEMY_DATABASE_URL = "sqlite:///./waterms.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


from models_unified_order import UnifiedOrder, UnifiedTransaction
from models_unified import AccountWallet, PromotionConfigV2, TransactionV2
from api_admin_auth import get_current_user
from models.user import User

router = APIRouter(prefix="/api/unified", tags=["统一订单管理"])


# ==================== 工具函数 ====================


def generate_order_no() -> str:
    """生成订单号：WO + 时间戳 + 随机数"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    random_num = random.randint(1000, 9999)
    return f"WO{timestamp}{random_num}"


def get_product(db: Session, product_id: int):
    """获取产品信息"""
    from models_unified import Product

    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(404, "产品不存在")
    return product


def get_prepaid_wallet(
    db: Session, user_id: int, product_id: int
) -> Optional[AccountWallet]:
    """获取用户预付钱包"""
    wallet = (
        db.query(AccountWallet)
        .filter(
            AccountWallet.user_id == user_id,
            AccountWallet.product_id == product_id,
            AccountWallet.wallet_type == "prepaid",
        )
        .first()
    )
    return wallet


def get_promotion_config(
    db: Session, product_id: int, promotion_type: str
) -> Optional[PromotionConfigV2]:
    """获取产品的优惠配置"""
    config = (
        db.query(PromotionConfigV2)
        .filter(
            PromotionConfigV2.product_id == product_id,
            PromotionConfigV2.mode == promotion_type,
            PromotionConfigV2.is_active == 1,
        )
        .first()
    )
    return config


def calculate_gift_quantity(quantity: int, promo_config: PromotionConfigV2) -> int:
    """
    计算赠送数量

    规则：每满足 trigger_qty 个，赠送 gift_qty 个
    """
    if not promo_config:
        return 0

    trigger_cycles = quantity // promo_config.trigger_qty
    return trigger_cycles * promo_config.gift_qty


def get_next_settlement_date() -> str:
    """获取下一个结算日期 (次月 1 号)"""
    from datetime import timedelta

    today = datetime.now()
    # 下个月 1 号
    if today.month == 12:
        next_month = today.replace(year=today.year + 1, month=1, day=1)
    else:
        next_month = today.replace(month=today.month + 1, day=1)

    return next_month.strftime("%Y-%m-%d")


def smart_payment_recommend(
    db: Session, user_id: int, product_id: int, quantity: int
) -> Dict:
    """
    智能推荐最优支付方式

    核心逻辑：对比各方案的总成本，推荐最省钱的
    详细展示买赠优惠计算过程
    """
    product = get_product(db, product_id)
    unit_price = product.price

    options = []

    # 获取优惠配置
    promo_config = get_promotion_config(db, product_id, "prepaid")

    # 方案 1: 预付钱包 (有买赠优惠)
    prepaid_option = None
    prepaid_wallet = get_prepaid_wallet(db, user_id, product_id)

    if prepaid_wallet and prepaid_wallet.available_qty >= quantity:
        # 计算买赠优惠
        if promo_config:
            gift_qty = calculate_gift_quantity(quantity, promo_config)
            actual_pay_qty = quantity - gift_qty
            total_cost = actual_pay_qty * unit_price
            savings = gift_qty * unit_price

            # 详细展示买赠计算过程
            trigger_cycles = quantity // promo_config.trigger_qty
            detail_text = f"买{promo_config.trigger_qty}赠{promo_config.gift_qty}"
            if trigger_cycles > 0:
                detail_text += f" × {trigger_cycles} = 赠{gift_qty}桶"

            prepaid_option = {
                "method": "prepaid",
                "pay_qty": actual_pay_qty,
                "gift_qty": gift_qty,
                "total_qty": quantity,
                "total_cost": total_cost,
                "unit_price": unit_price,
                "savings": savings,
                "description": f"付费{actual_pay_qty}桶 + 赠送{gift_qty}桶",
                "detail": detail_text,
                "cycles": trigger_cycles,
                "remaining_balance": prepaid_wallet.available_qty - actual_pay_qty,
            }
        else:
            # 没有优惠配置，按原价
            prepaid_option = {
                "method": "prepaid",
                "pay_qty": quantity,
                "gift_qty": 0,
                "total_qty": quantity,
                "total_cost": quantity * unit_price,
                "unit_price": unit_price,
                "savings": 0,
                "description": f"付费{quantity}桶",
                "detail": "无优惠活动",
                "cycles": 0,
                "remaining_balance": prepaid_wallet.available_qty - quantity,
            }

    # 方案 2: 信用支付 (标准价格)
    credit_limit = 10000.0  # TODO: 从用户信用额度表获取

    if credit_limit >= quantity * unit_price:
        credit_option = {
            "method": "credit",
            "qty": quantity,
            "total_qty": quantity,
            "gift_qty": 0,
            "total_cost": quantity * unit_price,
            "unit_price": unit_price,
            "settlement_date": get_next_settlement_date(),
            "description": f"次月结算，共{quantity}桶",
            "detail": "先用后付，标准价格",
            "cycles": 0,
        }
        options.append(credit_option)

    if prepaid_option:
        options.append(prepaid_option)

    if not options:
        return {
            "recommended_method": None,
            "reason": "余额不足且信用额度不足",
            "options": [],
            "promo_config": {
                "trigger_qty": promo_config.trigger_qty if promo_config else 0,
                "gift_qty": promo_config.gift_qty if promo_config else 0,
            },
        }

    # 推荐最省钱的方案
    recommended = min(options, key=lambda x: x["total_cost"])

    return {
        "recommended_method": recommended["method"],
        "reason": "此方案最省钱",
        "options": options,
        "promo_config": {
            "trigger_qty": promo_config.trigger_qty if promo_config else 0,
            "gift_qty": promo_config.gift_qty if promo_config else 0,
            "rule": f"买{promo_config.trigger_qty}赠{promo_config.gift_qty}"
            if promo_config
            else "无优惠",
        },
    }


# ==================== Pydantic 请求/响应模型 ====================

from pydantic import BaseModel


class PickupRequest(BaseModel):
    """领水订单请求"""

    product_id: int
    quantity: int
    preferred_payment: Optional[str] = None  # 'credit' | 'prepaid'


class PaymentRequest(BaseModel):
    """支付确认请求"""

    use_coupon: bool = False
    coupon_id: Optional[int] = None


class OrderResponse(BaseModel):
    """订单响应"""

    order: Dict
    recommendation: Dict
    message: str


# ==================== API 接口 ====================


@router.post("/pickup", response_model=None)
def create_pickup_order(
    request: PickupRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    创建统一领水订单

    请求参数:
    - product_id: 产品 ID
    - quantity: 数量
    - preferred_payment: 首选支付方式 (可选)

    返回:
    - 订单信息
    - 推荐支付方案
    """
    # 1. 验证产品
    product = get_product(db, request.product_id)

    # 2. 智能推荐支付方式
    recommendation = smart_payment_recommend(
        db=db,
        user_id=current_user.id,
        product_id=request.product_id,
        quantity=request.quantity,
    )

    # 3. 确定支付方式 (用户首选 or 智能推荐)
    payment_method = request.preferred_payment or recommendation.get(
        "recommended_method"
    )

    if not payment_method:
        raise HTTPException(400, "无法确定支付方式，请检查余额或信用额度")

    # 4. 计算优惠信息
    if payment_method == "prepaid":
        # 预付模式：计算买赠
        promo_config = get_promotion_config(db, request.product_id, "prepaid")
        if promo_config:
            gift_qty = calculate_gift_quantity(request.quantity, promo_config)
            paid_qty = request.quantity - gift_qty
            total_amount = paid_qty * product.price
        else:
            gift_qty = 0
            paid_qty = request.quantity
            total_amount = request.quantity * product.price
    else:
        # 信用模式：标准价格
        gift_qty = 0
        paid_qty = 0
        total_amount = request.quantity * product.price

    # 5. 创建统一订单
    order = UnifiedOrder(
        order_no=generate_order_no(),
        user_id=current_user.id,
        product_id=request.product_id,
        quantity=request.quantity,
        unit_price=product.price,
        total_amount=total_amount,
        payment_method=payment_method,
        payment_status="pending",
        prepaid_paid_qty=paid_qty,
        prepaid_gift_qty=gift_qty,
    )

    db.add(order)
    db.commit()
    db.refresh(order)

    return {
        "order": order.to_dict(),
        "recommendation": recommendation,
        "message": f"订单创建成功，推荐使用{payment_method}支付",
    }


@router.post("/orders/{order_id}/pay", response_model=None)
def pay_order(
    order_id: int,
    request: PaymentRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    支付订单

    根据订单的 payment_method 自动选择扣款方式:
    - prepaid: 扣除预付钱包余额
    - credit: 创建待结算交易记录
    """
    # 1. 获取订单
    order = (
        db.query(UnifiedOrder)
        .filter(
            UnifiedOrder.id == order_id,
            UnifiedOrder.user_id == current_user.id,
            UnifiedOrder.payment_status == "pending",
        )
        .first()
    )

    if not order:
        raise HTTPException(404, "订单不存在或已支付")

    # 2. 根据支付方式处理
    if order.payment_method == "prepaid":
        result = process_prepaid_payment(db, order, current_user.id)
    elif order.payment_method == "credit":
        result = process_credit_payment(db, order, current_user.id)
    else:
        raise HTTPException(400, "不支持的支付方式")

    # 3. 更新订单状态
    order.payment_status = "paid"
    order.paid_at = datetime.now()

    # 4. 创建统一交易记录
    transaction = UnifiedTransaction(
        order_id=order.id,
        user_id=current_user.id,
        product_id=order.product_id,
        quantity=order.quantity,
        unit_price=order.unit_price,
        total_amount=order.total_amount,
        discount_amount=order.discount_amount,
        actual_amount=order.total_amount - order.discount_amount,
        payment_details=json.dumps(
            {
                "credit_qty": 0
                if order.payment_method == "prepaid"
                else order.quantity,
                "prepaid_paid_qty": order.prepaid_paid_qty,
                "prepaid_gift_qty": order.prepaid_gift_qty,
                "coupon_discount": order.discount_amount,
            }
        ),
        status="completed",
        payment_method=order.payment_method,
    )

    db.add(transaction)
    db.commit()

    return {
        "message": "支付成功",
        "order_no": order.order_no,
        "payment_method": order.payment_method,
        "amount": order.total_amount,
        "details": result,
    }


def process_prepaid_payment(db: Session, order: UnifiedOrder, user_id: int):
    """
    预付钱包扣款 - 严格遵循"先扣付费，后扣赠送"原则
    """
    wallet = (
        db.query(AccountWallet)
        .filter(
            AccountWallet.user_id == user_id,
            AccountWallet.product_id == order.product_id,
            AccountWallet.wallet_type == "prepaid",
        )
        .first()
    )

    if not wallet:
        raise HTTPException(400, "预付钱包不存在")

    # 检查余额是否足够
    required_paid_qty = order.prepaid_paid_qty
    required_gift_qty = order.prepaid_gift_qty

    if wallet.paid_qty < required_paid_qty:
        raise HTTPException(
            400, f"付费桶余额不足，需要{required_paid_qty}，可用{wallet.paid_qty}"
        )

    if wallet.free_qty < required_gift_qty:
        raise HTTPException(
            400, f"赠送桶余额不足，需要{required_gift_qty}，可用{wallet.free_qty}"
        )

    # 扣款
    wallet.paid_qty -= required_paid_qty
    wallet.free_qty -= required_gift_qty
    wallet.available_qty = wallet.paid_qty + wallet.free_qty
    wallet.total_consumed += required_paid_qty + required_gift_qty

    db.commit()

    return {
        "wallet_id": wallet.id,
        "deducted_paid_qty": required_paid_qty,
        "deducted_gift_qty": required_gift_qty,
        "remaining_balance": wallet.available_qty,
    }


def process_credit_payment(db: Session, order: UnifiedOrder, user_id: int):
    """
    信用支付 - 创建待结算交易记录
    """
    # 创建信用交易记录
    transaction = TransactionV2(
        user_id=user_id,
        product_id=order.product_id,
        quantity=order.quantity,
        unit_price=order.unit_price,
        actual_price=order.total_amount,
        mode="credit",
        wallet_type="credit",
        status="pending",
        settlement_status="pending",
        paid_amount=0.0,
        remaining_amount=order.total_amount,
        note=f"unified_order:{order.id}",
    )

    db.add(transaction)
    db.commit()

    return {
        "transaction_id": transaction.id,
        "settlement_date": get_next_settlement_date(),
        "amount": order.total_amount,
    }


@router.get("/orders", response_model=None)
def get_orders(
    user_id: Optional[int] = Query(None),
    payment_method: Optional[str] = Query(None),
    payment_status: Optional[str] = Query(None),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    查询订单列表

    支持筛选:
    - 按用户 ID (管理员)
    - 按支付方式
    - 按支付状态
    - 按时间范围
    """
    query = db.query(UnifiedOrder).filter(UnifiedOrder.user_id == current_user.id)

    # 管理员可以查看所有用户订单
    if user_id and current_user.role == "admin":
        query = query.filter(UnifiedOrder.user_id == user_id)

    if payment_method:
        query = query.filter(UnifiedOrder.payment_method == payment_method)

    if payment_status:
        query = query.filter(UnifiedOrder.payment_status == payment_status)

    if date_from:
        query = query.filter(UnifiedOrder.created_at >= date_from)

    if date_to:
        query = query.filter(UnifiedOrder.created_at <= date_to)

    orders = (
        query.order_by(UnifiedOrder.created_at.desc()).offset(skip).limit(limit).all()
    )

    return {
        "orders": [order.to_dict() for order in orders],
        "total": query.count(),
        "skip": skip,
        "limit": limit,
    }


@router.get("/orders/{order_id}")
def get_order_detail(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取订单详情"""
    order = (
        db.query(UnifiedOrder)
        .filter(UnifiedOrder.id == order_id, UnifiedOrder.user_id == current_user.id)
        .first()
    )

    if not order:
        raise HTTPException(404, "订单不存在")

    return {"order": order.to_dict()}


@router.get("/transactions", response_model=None)
def get_transactions(
    user_id: Optional[int] = Query(None),
    payment_method: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    查询统一交易记录

    支持筛选:
    - 按用户 ID
    - 按支付方式
    - 按状态
    - 按时间范围
    """
    query = db.query(UnifiedTransaction).filter(
        UnifiedTransaction.user_id == current_user.id
    )

    if user_id and current_user.role == "admin":
        query = query.filter(UnifiedTransaction.user_id == user_id)

    if payment_method:
        query = query.filter(UnifiedTransaction.payment_method == payment_method)

    if status:
        query = query.filter(UnifiedTransaction.status == status)

    if date_from:
        query = query.filter(UnifiedTransaction.created_at >= date_from)

    if date_to:
        query = query.filter(UnifiedTransaction.created_at <= date_to)

    transactions = (
        query.order_by(UnifiedTransaction.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    return {
        "transactions": [trans.to_dict() for trans in transactions],
        "total": query.count(),
        "skip": skip,
        "limit": limit,
    }
