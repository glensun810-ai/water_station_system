"""
Coupon API - 优惠券管理接口
支持优惠券的创建、领取、使用和自动匹配
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from typing import Optional, List, Dict
from datetime import datetime
import json
import random
import string

# 本地定义 get_db，避免与 main.py 循环导入
SQLALCHEMY_DATABASE_URL = "sqlite:///./waterms.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

from models_coupon import Coupon, UserCoupon
from models_unified_order import UnifiedOrder
from account_service import get_current_user, User

router = APIRouter(prefix="/api/coupons", tags=["优惠券管理"])


# ==================== 工具函数 ====================

def generate_coupon_code(length: int = 8) -> str:
    """生成随机优惠券码"""
    characters = string.ascii_uppercase + string.digits
    return ''.join(random.choices(characters, k=length))


def calculate_coupon_discount(
    coupon: Coupon,
    order_amount: float,
    payment_method: str
) -> float:
    """
    计算优惠券折扣金额
    
    叠加规则:
    - 预付模式：在买赠后的价格基础上再打折
    - 信用模式：标准折扣
    
    Args:
        coupon: 优惠券对象
        order_amount: 订单金额 (已应用买赠优惠后的金额)
        payment_method: 支付方式 ('prepaid' | 'credit')
    
    Returns:
        折扣金额 (正数，表示减免的金额)
    """
    # 检查是否适用于该支付模式
    if coupon.applicable_modes:
        applicable_modes = json.loads(coupon.applicable_modes)
        if payment_method not in applicable_modes:
            return 0.0
    
    # 检查最低消费金额
    if order_amount < coupon.min_amount:
        return 0.0
    
    # 计算折扣
    if coupon.type == 'discount':
        # 折扣券 (如 95 折)
        discount = order_amount * (1 - coupon.value / 100)
        
        # 应用最大优惠限制
        if coupon.max_discount:
            discount = min(discount, coupon.max_discount)
    elif coupon.type == 'fixed':
        # 满减券 (如满 100 减 10)
        discount = min(coupon.value, order_amount)
    else:
        return 0.0
    
    return round(discount, 2)


# ==================== Pydantic 请求/响应模型 ====================

from pydantic import BaseModel

class CouponCreate(BaseModel):
    """创建优惠券请求"""
    name: str
    type: str  # 'discount' | 'fixed'
    value: float
    min_amount: float = 0.0
    max_discount: Optional[float] = None
    applicable_products: Optional[List[int]] = None
    applicable_modes: Optional[List[str]] = None  # ['prepaid', 'credit']
    valid_days: int = 30  # 有效期天数
    total_quantity: int = 0  # 0 表示无限制


class CouponIssueRequest(BaseModel):
    """发放优惠券请求"""
    user_ids: List[int]  # 用户 ID 列表
    coupon_id: int


class CouponUseRequest(BaseModel):
    """使用优惠券请求"""
    coupon_id: int
    order_id: int


class CouponCalculateRequest(BaseModel):
    """计算最优优惠券请求"""
    order_amount: float
    payment_method: str
    product_id: Optional[int] = None


# ==================== API 接口 ====================

@router.post("", response_model=None)
def create_coupon(
    request: CouponCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    创建优惠券 (管理员专用)
    
    权限要求:
    - admin 或 super_admin
    """
    if not current_user or current_user.role not in ['admin', 'super_admin']:
        raise HTTPException(status_code=403, detail="权限不足")
    
    # 验证类型
    if request.type not in ['discount', 'fixed']:
        raise HTTPException(status_code=400, detail="优惠券类型必须是 'discount' 或 'fixed'")
    
    # 验证适用范围
    if request.applicable_modes:
        for mode in request.applicable_modes:
            if mode not in ['prepaid', 'credit']:
                raise HTTPException(status_code=400, detail="适用模式只能是 'prepaid' 或 'credit'")
    
    # 生成优惠券码
    coupon_code = generate_coupon_code()
    
    # 计算有效期
    now = datetime.now()
    valid_from = now
    valid_until = datetime(now.year, now.month, now.day)
    from datetime import timedelta
    valid_until += timedelta(days=request.valid_days)
    valid_until = valid_until.replace(hour=23, minute=59, second=59)
    
    # 创建优惠券
    coupon = Coupon(
        coupon_code=coupon_code,
        name=request.name,
        type=request.type,
        value=request.value,
        min_amount=request.min_amount,
        max_discount=request.max_discount,
        applicable_products=json.dumps(request.applicable_products) if request.applicable_products else None,
        applicable_modes=json.dumps(request.applicable_modes) if request.applicable_modes else None,
        valid_from=valid_from,
        valid_until=valid_until,
        total_quantity=request.total_quantity,
        status='active'
    )
    
    db.add(coupon)
    db.commit()
    db.refresh(coupon)
    
    return {
        'message': '优惠券创建成功',
        'coupon': coupon.to_dict()
    }


@router.get("", response_model=None)
def get_coupons(
    status: Optional[str] = Query(None),
    coupon_type: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    查询优惠券列表
    
    支持筛选:
    - 按状态
    - 按类型
    """
    query = db.query(Coupon)
    
    if status:
        query = query.filter(Coupon.status == status)
    
    if coupon_type:
        query = query.filter(Coupon.type == coupon_type)
    
    coupons = query.order_by(
        Coupon.created_at.desc()
    ).offset(skip).limit(limit).all()
    
    total = query.count()
    
    return {
        'coupons': [c.to_dict() for c in coupons],
        'total': total,
        'skip': skip,
        'limit': limit
    }


@router.post("/issue", response_model=None)
def issue_coupon_to_users(
    request: CouponIssueRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    向用户发放优惠券 (管理员专用)
    
    权限要求:
    - admin 或 super_admin
    """
    if not current_user or current_user.role not in ['admin', 'super_admin']:
        raise HTTPException(status_code=403, detail="权限不足")
    
    # 验证优惠券是否存在
    coupon = db.query(Coupon).filter(Coupon.id == request.coupon_id).first()
    if not coupon:
        raise HTTPException(status_code=404, detail="优惠券不存在")
    
    # 检查优惠券是否有效
    if not coupon.is_valid():
        raise HTTPException(status_code=400, detail="优惠券已失效")
    
    # 检查数量限制
    if coupon.total_quantity > 0:
        remaining = coupon.total_quantity - coupon.issued_quantity
        if len(request.user_ids) > remaining:
            raise HTTPException(
                status_code=400, 
                detail=f"优惠券剩余数量不足，仅剩{remaining}张"
            )
    
    # 发放优惠券
    issued_count = 0
    for user_id in request.user_ids:
        user_coupon = UserCoupon(
            user_id=user_id,
            coupon_id=coupon.id,
            coupon_code=coupon.coupon_code,
            status='unused',
            expires_at=coupon.valid_until
        )
        db.add(user_coupon)
        issued_count += 1
    
    # 更新已发放数量
    coupon.issued_quantity += issued_count
    
    # 检查是否已发完
    if coupon.total_quantity > 0 and coupon.issued_quantity >= coupon.total_quantity:
        coupon.status = 'exhausted'
    
    db.commit()
    
    return {
        'message': f'成功发放 {issued_count} 张优惠券',
        'issued_count': issued_count
    }


@router.get("/my", response_model=None)
def get_my_coupons(
    status: Optional[str] = Query('unused'),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取我的优惠券
    
    默认只返回未使用的优惠券
    """
    if not current_user:
        raise HTTPException(status_code=401, detail="未登录")
    
    query = db.query(UserCoupon).filter(
        UserCoupon.user_id == current_user.id
    )
    
    if status:
        query = query.filter(UserCoupon.status == status)
    
    user_coupons = query.order_by(
        UserCoupon.expires_at.asc()
    ).all()
    
    results = []
    for uc in user_coupons:
        coupon = db.query(Coupon).filter(Coupon.id == uc.coupon_id).first()
        if coupon:
            result = uc.to_dict()
            result['coupon'] = coupon.to_dict()
            result['is_usable'] = uc.is_usable()
            results.append(result)
    
    return {
        'coupons': results,
        'total': len(results)
    }


@router.post("/calculate-best", response_model=None)
def calculate_best_coupon(
    request: CouponCalculateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    计算最优优惠券
    
    策略:
    1. 优先使用即将过期的优惠券
    2. 选择折扣力度最大的
    3. 如果是预付模式，叠加买赠优惠
    
    Returns:
        {
            'recommended_coupon': {...},
            'discount_amount': 10.5,
            'final_amount': 89.5
        }
    """
    if not current_user:
        raise HTTPException(status_code=401, detail="未登录")
    
    # 获取用户所有可用的优惠券
    user_coupons = db.query(UserCoupon).filter(
        UserCoupon.user_id == current_user.id,
        UserCoupon.status == 'unused'
    ).all()
    
    best_coupon = None
    max_discount = 0.0
    
    for uc in user_coupons:
        if not uc.is_usable():
            continue
        
        coupon = db.query(Coupon).filter(Coupon.id == uc.coupon_id).first()
        if not coupon or not coupon.is_valid():
            continue
        
        # 检查是否适用于该产品
        if coupon.applicable_products and request.product_id:
            applicable_products = json.loads(coupon.applicable_products)
            if request.product_id not in applicable_products:
                continue
        
        # 计算折扣
        discount = calculate_coupon_discount(coupon, request.order_amount, request.payment_method)
        
        if discount > max_discount:
            max_discount = discount
            best_coupon = uc
    
    if not best_coupon or max_discount <= 0:
        return {
            'recommended_coupon': None,
            'discount_amount': 0.0,
            'final_amount': request.order_amount,
            'message': '没有可用的优惠券'
        }
    
    coupon = db.query(Coupon).filter(Coupon.id == best_coupon.coupon_id).first()
    
    return {
        'recommended_coupon': {
            'user_coupon_id': best_coupon.id,
            'coupon_code': coupon.coupon_code,
            'name': coupon.name,
            'type': coupon.type,
            'value': coupon.value
        },
        'discount_amount': max_discount,
        'final_amount': round(request.order_amount - max_discount, 2)
    }


@router.post("/use", response_model=None)
def use_coupon(
    request: CouponUseRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    使用优惠券
    
    将优惠券标记为已使用，并关联到订单
    """
    if not current_user:
        raise HTTPException(status_code=401, detail="未登录")
    
    # 获取用户优惠券
    user_coupon = db.query(UserCoupon).filter(
        UserCoupon.id == request.coupon_id,
        UserCoupon.user_id == current_user.id,
        UserCoupon.status == 'unused'
    ).first()
    
    if not user_coupon:
        raise HTTPException(status_code=404, detail="优惠券不存在或不可用")
    
    # 检查是否过期
    if not user_coupon.is_usable():
        raise HTTPException(status_code=400, detail="优惠券已过期")
    
    # 验证优惠券是否有效
    coupon = db.query(Coupon).filter(Coupon.id == user_coupon.coupon_id).first()
    if not coupon or not coupon.is_valid():
        raise HTTPException(status_code=400, detail="优惠券已失效")
    
    # 验证订单是否存在且属于当前用户
    order = db.query(UnifiedOrder).filter(
        UnifiedOrder.id == request.order_id,
        UnifiedOrder.user_id == current_user.id
    ).first()
    
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")
    
    # 更新优惠券状态
    user_coupon.status = 'used'
    user_coupon.used_at = datetime.now()
    user_coupon.order_id = request.order_id
    
    # 更新优惠券使用数量
    coupon.used_quantity += 1
    
    # 更新订单的优惠券信息
    order.coupon_id = coupon.id
    
    # 计算折扣金额
    discount = calculate_coupon_discount(coupon, order.total_amount, order.payment_method)
    order.discount_amount = discount
    order.total_amount -= discount
    
    db.commit()
    
    return {
        'message': '优惠券使用成功',
        'discount_amount': discount,
        'final_amount': order.total_amount
    }


@router.delete("/{user_coupon_id}")
def expire_coupon(
    user_coupon_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    作废优惠券 (仅管理员)
    
    权限要求:
    - admin 或 super_admin
    """
    if not current_user or current_user.role not in ['admin', 'super_admin']:
        raise HTTPException(status_code=403, detail="权限不足")
    
    user_coupon = db.query(UserCoupon).filter(
        UserCoupon.id == user_coupon_id
    ).first()
    
    if not user_coupon:
        raise HTTPException(status_code=404, detail="优惠券不存在")
    
    if user_coupon.status == 'used':
        raise HTTPException(status_code=400, detail="已使用的优惠券不能作废")
    
    user_coupon.status = 'expired'
    db.commit()
    
    return {'message': '优惠券已作废'}
