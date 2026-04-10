"""
统一 v1 API 路由代理
为前端页面提供统一的 /api/v1/* 端点，代理到现有的API实现
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel

from config.database import get_db
from models.user import User
from models.product import Product
from models.office import Office
from models.pickup import OfficePickup
from models.account import OfficeAccount
from sqlalchemy import func

router = APIRouter(prefix="/api/v1", tags=["v1统一API"])


# ==================== 用户管理 ====================
@router.get("/users")
def get_users(
    role: Optional[str] = None,
    department: Optional[str] = None,
    is_active: Optional[int] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """获取用户列表"""
    query = db.query(User)

    if role:
        query = query.filter(User.role == role)
    if department:
        query = query.filter(User.department == department)
    if is_active is not None:
        query = query.filter(User.is_active == is_active)
    if search:
        query = query.filter(
            User.name.contains(search) | User.username.contains(search)
        )

    users = query.all()

    return [
        {
            "id": u.id,
            "name": u.name,
            "role": u.role,
            "department": u.department,
            "is_active": u.is_active,
            "balance_credit": u.balance_credit or 0,
            "created_at": u.created_at.isoformat() if u.created_at else None,
        }
        for u in users
    ]


@router.get("/users/stats/overview")
def get_users_stats(db: Session = Depends(get_db)):
    """获取用户统计概览"""
    total = db.query(User).count()
    active = db.query(User).filter(User.is_active == 1).count()
    inactive = db.query(User).filter(User.is_active == 0).count()

    roles = db.query(User.role, func.count(User.id)).group_by(User.role).all()
    role_stats = {r: c for r, c in roles}

    departments = (
        db.query(User.department, func.count(User.id)).group_by(User.department).all()
    )
    dept_stats = {d: c for d, c in departments if d}

    return {
        "total": total,
        "active": active,
        "inactive": inactive,
        "by_role": role_stats,
        "by_department": dept_stats,
    }


@router.get("/users/{user_id}")
def get_user(user_id: int, db: Session = Depends(get_db)):
    """获取单个用户详情"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    return {
        "id": user.id,
        "name": user.name,
        "role": user.role,
        "department": user.department,
        "is_active": user.is_active,
        "balance_credit": user.balance_credit or 0,
        "created_at": user.created_at.isoformat() if user.created_at else None,
    }


@router.put("/users/{user_id}")
def update_user(user_id: int, data: dict, db: Session = Depends(get_db)):
    """更新用户信息"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    for key, value in data.items():
        if hasattr(user, key) and key not in ["id", "password_hash"]:
            setattr(user, key, value)

    user.updated_at = datetime.now()
    db.commit()

    return {"message": "用户更新成功", "user_id": user_id}


@router.delete("/users/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db)):
    """删除用户"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    user.is_active = 0
    db.commit()

    return {"message": "用户已禁用", "user_id": user_id}


@router.post("/users/batch")
def batch_update_users(data: dict, db: Session = Depends(get_db)):
    """批量更新用户"""
    user_ids = data.get("user_ids", [])
    updates = data.get("updates", {})

    updated_count = 0
    for user_id in user_ids:
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            for key, value in updates.items():
                if hasattr(user, key) and key not in ["id", "password_hash"]:
                    setattr(user, key, value)
            updated_count += 1

    db.commit()
    return {
        "message": f"成功更新 {updated_count} 个用户",
        "updated_count": updated_count,
    }


@router.post("/users/batch-delete")
def batch_delete_users(user_ids: List[int], db: Session = Depends(get_db)):
    """批量删除用户"""
    deleted_count = 0
    for user_id in user_ids:
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            user.is_active = 0
            deleted_count += 1

    db.commit()
    return {
        "message": f"成功禁用 {deleted_count} 个用户",
        "deleted_count": deleted_count,
    }


@router.get("/users/check-name/{name}")
def check_user_name(name: str, db: Session = Depends(get_db)):
    """检查用户名是否存在"""
    user = db.query(User).filter(User.name == name).first()

    if user:
        return {
            "exists": True,
            "user": {
                "id": user.id,
                "name": user.name,
                "role": user.role,
                "department": user.department,
            },
        }
    return {"exists": False}


# ==================== 产品管理 ====================
@router.get("/products")
def get_products(
    category_id: Optional[int] = None,
    is_active: Optional[int] = None,
    db: Session = Depends(get_db),
):
    """获取产品列表"""
    query = db.query(Product)

    if is_active is not None:
        query = query.filter(Product.is_active == is_active)

    products = query.all()

    return [
        {
            "id": p.id,
            "name": p.name,
            "specification": p.specification,
            "unit": p.unit,
            "price": float(p.price) if p.price else 0,
            "stock": p.stock or 0,
            "is_active": p.is_active,
            "promo_threshold": p.promo_threshold or 0,
            "promo_gift": p.promo_gift or 0,
        }
        for p in products
    ]


# ==================== 水站服务 ====================
@router.get("/water/pickups")
def get_water_pickups(
    limit: int = 100,
    office_id: Optional[int] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """获取领水记录"""
    query = db.query(OfficePickup).filter(OfficePickup.is_deleted == False)

    if office_id:
        query = query.filter(OfficePickup.office_id == office_id)
    if status:
        query = query.filter(OfficePickup.settlement_status == status)

    pickups = query.order_by(OfficePickup.pickup_time.desc()).limit(limit).all()

    return [
        {
            "id": p.id,
            "office_id": p.office_id,
            "office_name": p.office_name,
            "product_id": p.product_id,
            "product_name": p.product_name,
            "quantity": p.quantity,
            "pickup_person": p.pickup_person,
            "pickup_person_id": p.pickup_person_id,
            "pickup_time": p.pickup_time.isoformat() if p.pickup_time else None,
            "settlement_status": p.settlement_status,
            "total_amount": float(p.total_amount) if p.total_amount else 0,
            "unit_price": float(p.unit_price) if p.unit_price else 0,
            "free_qty": getattr(p, "free_qty", 0) or 0,
        }
        for p in pickups
    ]


@router.get("/water/stats/today")
def get_water_stats_today(db: Session = Depends(get_db)):
    """获取今日水站统计"""
    today = datetime.now().date()

    pickups_today = (
        db.query(OfficePickup)
        .filter(
            func.date(OfficePickup.pickup_time) == today,
            OfficePickup.is_deleted == False,
        )
        .all()
    )

    total_qty = sum(p.quantity or 0 for p in pickups_today)
    total_amount = sum(float(p.total_amount or 0) for p in pickups_today)

    products = db.query(Product).filter(Product.is_active == 1).all()

    return {
        "date": today.isoformat(),
        "pickup_count": len(pickups_today),
        "total_quantity": total_qty,
        "total_amount": total_amount,
        "product_count": len(products),
    }


@router.get("/water/products")
def get_water_products(db: Session = Depends(get_db)):
    """获取水站产品"""
    products = db.query(Product).filter(Product.is_active == 1).all()

    return [
        {
            "id": p.id,
            "name": p.name,
            "specification": p.specification,
            "unit": p.unit,
            "price": float(p.price) if p.price else 0,
            "stock": p.stock or 0,
            "promo_threshold": p.promo_threshold or 0,
            "promo_gift": p.promo_gift or 0,
        }
        for p in products
    ]


@router.get("/water/accounts")
def get_water_accounts(
    office_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    """获取水站账户"""
    query = db.query(OfficeAccount)

    if office_id:
        query = query.filter(OfficeAccount.office_id == office_id)

    accounts = query.all()

    return [
        {
            "id": a.id,
            "office_id": a.office_id,
            "office_name": a.office_name,
            "product_id": a.product_id,
            "product_name": a.product_name,
            "reserved_qty": a.reserved_qty,
            "remaining_qty": a.remaining_qty,
        }
        for a in accounts
    ]


@router.post("/water/pickup")
def create_water_pickup(data: dict, db: Session = Depends(get_db)):
    """创建领水记录"""
    office_id = data.get("office_id")
    product_id = data.get("product_id")
    quantity = data.get("quantity", 1)

    office = db.query(Office).filter(Office.id == office_id).first()
    if not office:
        raise HTTPException(status_code=404, detail="办公室不存在")

    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="产品不存在")

    if product.stock < quantity:
        raise HTTPException(status_code=400, detail="库存不足")

    free_qty = 0
    if product.promo_threshold and product.promo_gift:
        cycles = quantity // (product.promo_threshold + product.promo_gift)
        free_qty = cycles * product.promo_gift

    paid_qty = quantity - free_qty
    total_amount = paid_qty * float(product.price)

    pickup = OfficePickup(
        office_id=office_id,
        office_name=office.name,
        office_room_number=office.room_number,
        product_id=product_id,
        product_name=product.name,
        product_specification=product.specification,
        quantity=quantity,
        pickup_time=datetime.now(),
        unit_price=float(product.price),
        total_amount=total_amount,
        free_qty=free_qty,
        settlement_status="pending",
        is_deleted=False,
    )

    product.stock -= quantity

    db.add(pickup)
    db.commit()
    db.refresh(pickup)

    return {
        "id": pickup.id,
        "message": "领水记录创建成功",
        "paid_qty": paid_qty,
        "free_qty": free_qty,
        "total_amount": total_amount,
    }


# ==================== 结算管理 ====================
@router.get("/settlements/summary")
def get_settlements_summary(db: Session = Depends(get_db)):
    """获取结算汇总"""
    pending = (
        db.query(OfficePickup)
        .filter(
            OfficePickup.settlement_status == "pending",
            OfficePickup.is_deleted == False,
        )
        .all()
    )

    applied = (
        db.query(OfficePickup)
        .filter(
            OfficePickup.settlement_status == "applied",
            OfficePickup.is_deleted == False,
        )
        .all()
    )

    settled = (
        db.query(OfficePickup)
        .filter(
            OfficePickup.settlement_status == "settled",
            OfficePickup.is_deleted == False,
        )
        .all()
    )

    return {
        "pending_count": len(pending),
        "pending_amount": sum(float(p.total_amount or 0) for p in pending),
        "applied_count": len(applied),
        "applied_amount": sum(float(p.total_amount or 0) for p in applied),
        "settled_count": len(settled),
        "settled_amount": sum(float(p.total_amount or 0) for p in settled),
    }


@router.post("/settlements/apply")
def apply_settlement(data: dict, db: Session = Depends(get_db)):
    """申请结算"""
    pickup_ids = data.get("pickup_ids", [])

    updated_count = 0
    for pickup_id in pickup_ids:
        pickup = db.query(OfficePickup).filter(OfficePickup.id == pickup_id).first()
        if pickup and pickup.settlement_status == "pending":
            pickup.settlement_status = "applied"
            updated_count += 1

    db.commit()
    return {
        "message": f"成功申请 {updated_count} 条结算",
        "updated_count": updated_count,
    }


@router.post("/settlements/batch-confirm")
def batch_confirm_settlement(pickup_ids: List[int], db: Session = Depends(get_db)):
    """批量确认结算"""
    updated_count = 0
    for pickup_id in pickup_ids:
        pickup = db.query(OfficePickup).filter(OfficePickup.id == pickup_id).first()
        if pickup and pickup.settlement_status in ["pending", "applied"]:
            pickup.settlement_status = "settled"
            updated_count += 1

    db.commit()
    return {
        "message": f"成功确认 {updated_count} 条结算",
        "updated_count": updated_count,
    }


# ==================== 会员计划 ====================
@router.get("/membership/plans")
def get_membership_plans(db: Session = Depends(get_db)):
    """获取会员计划列表"""
    try:
        from models.membership import MembershipPlan

        plans = db.query(MembershipPlan).filter(MembershipPlan.is_active == 1).all()

        return [
            {
                "id": p.id,
                "name": p.name,
                "price": float(p.price) if p.price else 0,
                "duration_months": p.duration_months,
                "benefits": p.benefits,
                "is_active": p.is_active,
            }
            for p in plans
        ]
    except:
        return []


# ==================== 会议室服务 ====================
@router.get("/meeting/rooms")
def get_meeting_rooms(db: Session = Depends(get_db)):
    """获取会议室列表"""
    try:
        from models.meeting_room import MeetingRoom

        rooms = db.query(MeetingRoom).filter(MeetingRoom.is_active == 1).all()

        return [
            {
                "id": r.id,
                "name": r.name,
                "capacity": r.capacity,
                "equipment": r.equipment,
                "hourly_rate": float(r.hourly_rate) if r.hourly_rate else 0,
                "is_active": r.is_active,
            }
            for r in rooms
        ]
    except:
        return []


@router.get("/meeting/bookings")
def get_meeting_bookings(
    date: Optional[str] = None,
    room_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    """获取会议室预订"""
    try:
        from models.meeting_booking import MeetingBooking

        query = db.query(MeetingBooking)

        if date:
            query = query.filter(MeetingBooking.booking_date == date)
        if room_id:
            query = query.filter(MeetingBooking.room_id == room_id)

        bookings = query.all()

        return [
            {
                "id": b.id,
                "room_id": b.room_id,
                "room_name": b.room_name,
                "user_id": b.user_id,
                "booking_date": b.booking_date.isoformat() if b.booking_date else None,
                "start_time": b.start_time,
                "end_time": b.end_time,
                "status": b.status,
            }
            for b in bookings
        ]
    except:
        return []


# ==================== 办公室账户 ====================
@router.get("/office-accounts")
def get_office_accounts(
    office_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    """获取办公室账户"""
    query = db.query(OfficeAccount)

    if office_id:
        query = query.filter(OfficeAccount.office_id == office_id)

    accounts = query.all()

    return [
        {
            "id": a.id,
            "office_id": a.office_id,
            "office_name": a.office_name,
            "office_room_number": a.office_room_number,
            "product_id": a.product_id,
            "product_name": a.product_name,
            "product_specification": a.product_specification,
            "reserved_qty": a.reserved_qty,
            "remaining_qty": a.remaining_qty,
            "used_qty": a.reserved_qty - a.remaining_qty,
        }
        for a in accounts
    ]
