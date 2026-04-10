"""
水站服务API路由 - v1版本
统一的API端点，与前端修复后的调用路径匹配
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from config.database import get_db
from models.user import User
from models.product import Product
from models.office import Office
from models.pickup import OfficePickup
from depends.auth import get_current_user, get_admin_user, get_current_user_required
from schemas.water import (
    OfficePickupCreate,
    OfficePickupResponse,
)

router = APIRouter(prefix="/water", tags=["水站服务"])


@router.get("/products")
def get_water_products(
    active_only: bool = Query(True, description="是否只返回激活的产品"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取水站产品列表"""

    query = db.query(Product).filter(Product.is_active == True)

    if active_only:
        query = query.filter(Product.stock > 0)

    products = query.all()

    results = []
    for product in products:
        results.append(
            {
                "id": product.id,
                "name": product.name,
                "specification": product.specification,
                "unit": product.unit,
                "price": float(product.price) if product.price else 0.0,
                "stock": int(product.stock) if product.stock else 0,
                "promo_threshold": product.promo_threshold or 0,
                "promo_gift": product.promo_gift or 0,
            }
        )

    return results


@router.get("/pickups")
def get_user_pickups(
    limit: int = Query(100, description="返回记录数量限制"),
    office_id: Optional[int] = Query(None, description="办公室ID过滤"),
    status: Optional[str] = Query(None, description="状态过滤"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_required),
):
    """获取用户的领水记录"""

    query = db.query(OfficePickup).filter(OfficePickup.is_deleted == False)

    # 普通用户只能查看自己的记录
    if current_user.role not in ["admin", "super_admin"]:
        query = query.filter(OfficePickup.pickup_person_id == current_user.id)

    if office_id:
        query = query.filter(OfficePickup.office_id == office_id)

    if status and status != "all":
        query = query.filter(OfficePickup.settlement_status == status)

    pickups = query.order_by(OfficePickup.pickup_time.desc()).limit(limit).all()

    results = []
    for pickup in pickups:
        results.append(
            {
                "id": pickup.id,
                "office_id": pickup.office_id,
                "office_name": pickup.office_name,
                "product_id": pickup.product_id,
                "product_name": pickup.product_name,
                "product_specification": pickup.product_specification,
                "quantity": pickup.quantity,
                "pickup_person": pickup.pickup_person,
                "pickup_person_id": pickup.pickup_person_id,
                "pickup_time": pickup.pickup_time.isoformat()
                if pickup.pickup_time
                else None,
                "settlement_status": pickup.settlement_status,
                "total_amount": float(pickup.total_amount)
                if pickup.total_amount
                else 0.0,
                "free_qty": pickup.free_qty or 0,
            }
        )

    return results


@router.post("/pickup")
def create_water_pickup(
    pickup_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """创建领水记录"""

    office_id = pickup_data.get("office_id")
    product_id = pickup_data.get("product_id")
    quantity = pickup_data.get("quantity")
    pickup_person = pickup_data.get("pickup_person", current_user.username)
    pickup_time_str = pickup_data.get("pickup_time")

    # 验证办公室
    office = (
        db.query(Office)
        .filter(Office.id == office_id, Office.is_active == True)
        .first()
    )
    if not office:
        raise HTTPException(status_code=404, detail="办公室不存在或已停用")

    # 验证产品
    product = (
        db.query(Product)
        .filter(Product.id == product_id, Product.is_active == True)
        .first()
    )
    if not product:
        raise HTTPException(status_code=404, detail="产品不存在或已停用")

    if product.stock < quantity:
        raise HTTPException(
            status_code=400,
            detail=f"库存不足，当前库存: {product.stock} {product.unit}",
        )

    # 计算优惠
    free_qty = 0
    total_amount = 0.0

    if product.promo_threshold and product.promo_gift:
        # 买N赠M逻辑
        cycles = quantity // (product.promo_threshold + product.promo_gift)
        remainder = quantity % (product.promo_threshold + product.promo_gift)
        free_qty = cycles * product.promo_gift

        if remainder > product.promo_threshold:
            free_qty += min(remainder - product.promo_threshold, product.promo_gift)

    # 实际付费数量
    paid_qty = quantity - free_qty
    total_amount = paid_qty * float(product.price)

    # 创建领水记录
    pickup_time = datetime.now()
    if pickup_time_str:
        try:
            pickup_time = datetime.fromisoformat(pickup_time_str.replace("Z", "+00:00"))
        except:
            pass

    new_pickup = OfficePickup(
        office_id=office_id,
        office_name=office.name,
        office_room_number=office.room_number,
        product_id=product_id,
        product_name=product.name,
        product_specification=product.specification,
        quantity=quantity,
        pickup_person=pickup_person,
        pickup_person_id=current_user.id,
        pickup_time=pickup_time,
        unit_price=float(product.price),
        total_amount=total_amount,
        free_qty=free_qty,
        settlement_status="pending",
        is_deleted=False,
    )

    # 更新库存
    product.stock -= quantity

    db.add(new_pickup)
    db.commit()
    db.refresh(new_pickup)

    return {
        "id": new_pickup.id,
        "message": "领水记录创建成功",
        "paid_qty": paid_qty,
        "free_qty": free_qty,
        "total_amount": total_amount,
    }


@router.post("/pickup/{pickup_id}/pay")
def mark_pickup_as_paid(
    pickup_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """标记领水记录为已付款"""

    pickup = (
        db.query(OfficePickup)
        .filter(OfficePickup.id == pickup_id, OfficePickup.is_deleted == False)
        .first()
    )

    if not pickup:
        raise HTTPException(status_code=404, detail="领水记录不存在")

    # 检查权限：只能操作自己的记录
    if pickup.pickup_person_id != current_user.id and current_user.role not in [
        "admin",
        "super_admin",
    ]:
        raise HTTPException(status_code=403, detail="无权限操作此记录")

    if pickup.settlement_status != "pending":
        raise HTTPException(
            status_code=400, detail="只能对'待付款'状态的记录进行付款操作"
        )

    pickup.settlement_status = "applied"
    db.commit()

    return {"message": "付款状态更新成功", "pickup_id": pickup_id}


@router.get("/offices")
def get_active_offices(
    is_active: bool = Query(True, description="是否只返回激活的办公室"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取办公室列表"""

    query = db.query(Office)

    if is_active:
        query = query.filter(Office.is_active == True)

    offices = query.order_by(Office.name).all()

    results = []
    for office in offices:
        results.append(
            {
                "id": office.id,
                "name": office.name,
                "room_number": office.room_number,
                "leader_name": office.leader_name,
            }
        )

    return results


@router.get("/stats/today")
def get_water_stats_today(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    """获取今日水站统计数据"""

    from datetime import date
    from sqlalchemy import func

    today = date.today()

    # 今日领水次数
    pickup_count = (
        db.query(func.count(OfficePickup.id))
        .filter(OfficePickup.pickup_time >= today, OfficePickup.is_deleted == False)
        .scalar()
        or 0
    )

    # 今日领水金额
    today_amount = (
        db.query(func.sum(OfficePickup.total_amount))
        .filter(OfficePickup.pickup_time >= today, OfficePickup.is_deleted == False)
        .scalar()
        or 0.0
    )

    # 待结算金额
    pending_amount = (
        db.query(func.sum(OfficePickup.total_amount))
        .filter(
            OfficePickup.settlement_status == "pending",
            OfficePickup.is_deleted == False,
        )
        .scalar()
        or 0.0
    )

    # 异常告警（库存不足）
    low_stock_count = (
        db.query(func.count(Product.id))
        .filter(Product.stock < 10, Product.is_active == True)
        .scalar()
        or 0
    )

    return {
        "pickup_count": pickup_count,
        "today_amount": float(today_amount),
        "pending_amount": float(pending_amount),
        "alerts": low_stock_count,
    }


@router.get("/settlements/summary")
def get_settlement_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    """获取结算汇总数据"""

    from sqlalchemy import func

    # 待结算
    pending = (
        db.query(func.sum(OfficePickup.total_amount))
        .filter(
            OfficePickup.settlement_status == "pending",
            OfficePickup.is_deleted == False,
        )
        .scalar()
        or 0.0
    )

    # 已申请结算
    applied = (
        db.query(func.sum(OfficePickup.total_amount))
        .filter(
            OfficePickup.settlement_status == "applied",
            OfficePickup.is_deleted == False,
        )
        .scalar()
        or 0.0
    )

    # 已结算
    settled = (
        db.query(func.sum(OfficePickup.total_amount))
        .filter(
            OfficePickup.settlement_status == "settled",
            OfficePickup.is_deleted == False,
        )
        .scalar()
        or 0.0
    )

    return {
        "total": {
            "pending_amount": float(pending),
            "applied_amount": float(applied),
            "settled_amount": float(settled),
        }
    }
