"""
统一 v1 API 路由代理
为前端页面提供统一的 /api/v1/* 端点，代理到现有的API实现
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel

from config.database import get_db, get_meeting_db
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
    # meeting db
    db: Session = Depends(get_meeting_db),
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
    # meeting db
    db: Session = Depends(get_meeting_db),
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
    # meeting db
    db: Session = Depends(get_meeting_db),
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
                "location": getattr(r, "location", None),
                "capacity": r.capacity or 10,
                "facilities": getattr(r, "facilities", None),
                "price_per_hour": float(r.price_per_hour) if r.price_per_hour else 0,
                "member_price_per_hour": float(getattr(r, "member_price_per_hour", 0))
                if hasattr(r, "member_price_per_hour")
                else 0,
                "free_hours_per_month": getattr(r, "free_hours_per_month", 0) or 0,
                "is_active": r.is_active,
            }
            for r in rooms
        ]
    except Exception as e:
        print(f"获取会议室失败: {e}")
        return []


@router.post("/meeting/rooms")
def create_meeting_room(data: dict, db: Session = Depends(get_db)):
    """创建会议室"""
    try:
        from models.meeting_room import MeetingRoom

        room = MeetingRoom(
            name=data.get("name"),
            location=data.get("location"),
            capacity=data.get("capacity", 10),
            facilities=data.get("facilities"),
            price_per_hour=data.get("price_per_hour", 0),
            member_price_per_hour=data.get("member_price_per_hour", 0),
            free_hours_per_month=data.get("free_hours_per_month", 0),
            is_active=1,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        db.add(room)
        db.commit()
        db.refresh(room)

        return {
            "id": room.id,
            "name": room.name,
            "message": "会议室创建成功",
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"创建会议室失败: {str(e)}")


@router.put("/meeting/rooms/{room_id}")
def update_meeting_room(room_id: int, data: dict, db: Session = Depends(get_db)):
    """更新会议室"""
    try:
        from models.meeting_room import MeetingRoom

        room = db.query(MeetingRoom).filter(MeetingRoom.id == room_id).first()
        if not room:
            raise HTTPException(status_code=404, detail="会议室不存在")

        for key, value in data.items():
            if hasattr(room, key) and key not in ["id", "created_at"]:
                setattr(room, key, value)

        room.updated_at = datetime.now()
        db.commit()
        db.refresh(room)

        return {
            "id": room.id,
            "name": room.name,
            "message": "会议室更新成功",
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"更新会议室失败: {str(e)}")


@router.delete("/meeting/rooms/{room_id}")
def delete_meeting_room(room_id: int, db: Session = Depends(get_db)):
    """删除会议室"""
    try:
        from models.meeting_room import MeetingRoom

        room = db.query(MeetingRoom).filter(MeetingRoom.id == room_id).first()
        if not room:
            raise HTTPException(status_code=404, detail="会议室不存在")

        room.is_active = 0
        room.updated_at = datetime.now()
        db.commit()

        return {"message": "会议室已禁用", "room_id": room_id}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"删除会议室失败: {str(e)}")


@router.get("/meeting/bookings")
def get_meeting_bookings(
    date: Optional[str] = None,
    room_id: Optional[int] = None,
    # meeting db
    db: Session = Depends(get_meeting_db),
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
                "user_name": b.user_name,
                "booking_date": b.booking_date.isoformat() if b.booking_date else None,
                "start_time": b.start_time,
                "end_time": b.end_time,
                "duration": getattr(b, "duration", None),
                "meeting_title": getattr(b, "meeting_title", None),
                "status": b.status,
                "total_fee": float(getattr(b, "total_fee", 0) or 0),
            }
            for b in bookings
        ]
    except:
        return []


# ==================== 办公室账户 ====================
@router.get("/office-accounts")
def get_office_accounts(
    office_id: Optional[int] = None,
    product_id: Optional[int] = None,
    status: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """获取办公室账户"""
    query = db.query(OfficeAccount)

    if office_id:
        query = query.filter(OfficeAccount.office_id == office_id)

    if product_id:
        query = query.filter(OfficeAccount.product_id == product_id)

    if status == "normal":
        query = query.filter(OfficeAccount.remaining_qty > 10)
    elif status == "low":
        query = query.filter(
            OfficeAccount.remaining_qty > 0, OfficeAccount.remaining_qty <= 10
        )
    elif status == "empty":
        query = query.filter(OfficeAccount.remaining_qty == 0)

    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            (OfficeAccount.office_name.ilike(search_pattern))
            | (OfficeAccount.office_room_number.ilike(search_pattern))
        )

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
            "status": "normal"
            if a.remaining_qty > 10
            else ("low" if a.remaining_qty > 0 else "empty"),
            "reserved_person": getattr(a, "reserved_person", None),
            "note": getattr(a, "note", None),
        }
        for a in accounts
    ]


class OfficeAccountCreate(BaseModel):
    office_id: int
    product_id: int
    reserved_qty: int
    remaining_qty: Optional[int] = None
    reserved_person: Optional[str] = None
    note: Optional[str] = None


class OfficeAccountUpdate(BaseModel):
    office_id: Optional[int] = None
    product_id: Optional[int] = None
    reserved_qty: Optional[int] = None
    remaining_qty: Optional[int] = None
    reserved_person: Optional[str] = None
    note: Optional[str] = None


class OfficeAccountRecharge(BaseModel):
    quantity: int


@router.post("/office-accounts")
def create_office_account(
    account: OfficeAccountCreate,
    db: Session = Depends(get_db),
):
    """创建办公室账户"""
    office = db.query(Office).filter(Office.id == account.office_id).first()
    product = db.query(Product).filter(Product.id == account.product_id).first()

    if not office:
        raise HTTPException(status_code=404, detail="办公室不存在")
    if not product:
        raise HTTPException(status_code=404, detail="产品不存在")

    remaining_qty = (
        account.remaining_qty
        if account.remaining_qty is not None
        else account.reserved_qty
    )

    new_account = OfficeAccount(
        office_id=account.office_id,
        office_name=office.name,
        office_room_number=office.room_number,
        product_id=account.product_id,
        product_name=product.name,
        product_specification=product.specification,
        reserved_qty=account.reserved_qty,
        remaining_qty=remaining_qty,
        reserved_person=account.reserved_person,
        note=account.note,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )

    db.add(new_account)
    db.commit()
    db.refresh(new_account)

    return {
        "id": new_account.id,
        "office_id": new_account.office_id,
        "office_name": new_account.office_name,
        "office_room_number": new_account.office_room_number,
        "product_id": new_account.product_id,
        "product_name": new_account.product_name,
        "product_specification": new_account.product_specification,
        "reserved_qty": new_account.reserved_qty,
        "remaining_qty": new_account.remaining_qty,
        "status": "normal"
        if new_account.remaining_qty > 10
        else ("low" if new_account.remaining_qty > 0 else "empty"),
        "reserved_person": new_account.reserved_person,
        "note": new_account.note,
    }


@router.put("/office-accounts/{account_id}")
def update_office_account(
    account_id: int,
    account: OfficeAccountUpdate,
    db: Session = Depends(get_db),
):
    """更新办公室账户"""
    existing = db.query(OfficeAccount).filter(OfficeAccount.id == account_id).first()
    if not existing:
        raise HTTPException(status_code=404, detail="账户不存在")

    update_data = account.model_dump(exclude_unset=True)

    if "office_id" in update_data:
        office = db.query(Office).filter(Office.id == update_data["office_id"]).first()
        if not office:
            raise HTTPException(status_code=404, detail="办公室不存在")
        existing.office_name = office.name
        existing.office_room_number = office.room_number

    if "product_id" in update_data:
        product = (
            db.query(Product).filter(Product.id == update_data["product_id"]).first()
        )
        if not product:
            raise HTTPException(status_code=404, detail="产品不存在")
        existing.product_name = product.name
        existing.product_specification = product.specification

    for key, value in update_data.items():
        if hasattr(existing, key):
            setattr(existing, key, value)

    existing.updated_at = datetime.now()
    db.commit()
    db.refresh(existing)

    return {
        "id": existing.id,
        "office_id": existing.office_id,
        "office_name": existing.office_name,
        "office_room_number": existing.office_room_number,
        "product_id": existing.product_id,
        "product_name": existing.product_name,
        "product_specification": existing.product_specification,
        "reserved_qty": existing.reserved_qty,
        "remaining_qty": existing.remaining_qty,
        "status": "normal"
        if existing.remaining_qty > 10
        else ("low" if existing.remaining_qty > 0 else "empty"),
        "reserved_person": existing.reserved_person,
        "note": existing.note,
    }


@router.delete("/office-accounts/{account_id}")
def delete_office_account(
    account_id: int,
    db: Session = Depends(get_db),
):
    """删除办公室账户"""
    account = db.query(OfficeAccount).filter(OfficeAccount.id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="账户不存在")

    db.delete(account)
    db.commit()

    return {"message": "账户已删除", "id": account_id}


@router.post("/office-accounts/{account_id}/recharge")
def recharge_office_account(
    account_id: int,
    recharge: OfficeAccountRecharge,
    db: Session = Depends(get_db),
):
    """充值/扣减办公室账户"""
    account = db.query(OfficeAccount).filter(OfficeAccount.id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="账户不存在")

    new_remaining = account.remaining_qty + recharge.quantity

    if new_remaining < 0:
        raise HTTPException(status_code=400, detail="扣减数量不能超过剩余数量")

    if new_remaining > account.reserved_qty:
        account.reserved_qty = new_remaining

    account.remaining_qty = new_remaining
    account.updated_at = datetime.now()
    db.commit()
    db.refresh(account)

    return {
        "id": account.id,
        "office_name": account.office_name,
        "product_name": account.product_name,
        "reserved_qty": account.reserved_qty,
        "remaining_qty": account.remaining_qty,
        "recharge_qty": recharge.quantity,
        "status": "normal"
        if account.remaining_qty > 10
        else ("low" if account.remaining_qty > 0 else "empty"),
    }


# ==================== 会议室补充功能 ====================


# 1. 会议室统计API
@router.get("/meeting/statistics")
def get_meeting_statistics(
    room_id: Optional[int] = None,
    month: Optional[str] = None,
    db: Session = Depends(get_meeting_db),
):
    """
    获取会议室统计信息
    - room_id: 指定会议室ID，不传则返回所有会议室统计
    - month: 指定月份，格式YYYY-MM，不传则返回当月
    """
    try:
        from models.meeting_room import (
            MeetingRoom,
            MeetingRoomStatistics,
            MeetingBooking,
        )
        from sqlalchemy import func

        if not month:
            month = datetime.now().strftime("%Y-%m")

        if room_id:
            rooms = db.query(MeetingRoom).filter(MeetingRoom.id == room_id).all()
        else:
            rooms = db.query(MeetingRoom).filter(MeetingRoom.is_active == 1).all()

        result = []
        for room in rooms:
            month_start = datetime.strptime(month + "-01", "%Y-%m-%d")
            if month_start.month == 12:
                month_end = datetime(month_start.year + 1, 1, 1)
            else:
                month_end = datetime(month_start.year, month_start.month + 1, 1)

            bookings = (
                db.query(MeetingBooking)
                .filter(
                    MeetingBooking.room_id == room.id,
                    MeetingBooking.booking_date >= month_start,
                    MeetingBooking.booking_date < month_end,
                    MeetingBooking.status.in_(["confirmed", "completed"]),
                )
                .all()
            )

            total_bookings = len(bookings)
            total_hours = sum(float(getattr(b, "duration", 1) or 1) for b in bookings)
            total_revenue = sum(
                float(getattr(b, "total_fee", 0) or 0) for b in bookings
            )

            working_days = 22
            working_hours_per_day = 10
            total_available_hours = working_days * working_hours_per_month
            utilization_rate = (
                (total_hours / total_available_hours * 100)
                if total_available_hours > 0
                else 0
            )

            result.append(
                {
                    "room_id": room.id,
                    "room_name": room.name,
                    "month": month,
                    "total_bookings": total_bookings,
                    "total_hours": round(total_hours, 2),
                    "total_revenue": round(total_revenue, 2),
                    "utilization_rate": round(utilization_rate, 2),
                    "capacity": room.capacity,
                    "price_per_hour": float(room.price_per_hour)
                    if room.price_per_hour
                    else 0,
                }
            )

        return result
    except Exception as e:
        print(f"获取会议室统计失败: {e}")
        return []


@router.get("/meeting/statistics/overview")
def get_meeting_statistics_overview(db: Session = Depends(get_db)):
    """获取会议室统计概览（Dashboard使用）"""
    try:
        from models.meeting_room import MeetingRoom, MeetingBooking
        from sqlalchemy import func

        today = datetime.now().date()
        month_start = datetime(today.year, today.month, 1)

        total_rooms = db.query(MeetingRoom).filter(MeetingRoom.is_active == 1).count()

        today_bookings = (
            db.query(MeetingBooking)
            .filter(
                func.date(MeetingBooking.booking_date) == today,
                MeetingBooking.status.in_(["pending", "confirmed"]),
            )
            .count()
        )

        month_bookings = (
            db.query(MeetingBooking)
            .filter(
                MeetingBooking.booking_date >= month_start,
                MeetingBooking.status.in_(["confirmed", "completed"]),
            )
            .all()
        )

        month_revenue = sum(
            float(getattr(b, "total_fee", 0) or 0) for b in month_bookings
        )
        month_hours = sum(float(getattr(b, "duration", 1) or 1) for b in month_bookings)

        pending_approvals = (
            db.query(MeetingBooking).filter(MeetingBooking.status == "pending").count()
        )

        return {
            "total_rooms": total_rooms,
            "today_bookings": today_bookings,
            "month_bookings": len(month_bookings),
            "month_revenue": round(month_revenue, 2),
            "month_hours": round(month_hours, 2),
            "pending_approvals": pending_approvals,
            "avg_utilization": round(month_hours / (total_rooms * 22 * 10) * 100, 2)
            if total_rooms > 0
            else 0,
        }
    except Exception as e:
        print(f"获取统计概览失败: {e}")
        return {
            "total_rooms": 0,
            "today_bookings": 0,
            "month_bookings": 0,
            "month_revenue": 0,
            "month_hours": 0,
            "pending_approvals": 0,
            "avg_utilization": 0,
        }


# 2. 预约时间冲突检测API
@router.get("/meeting/check-availability")
def check_meeting_availability(
    room_id: int,
    booking_date: str,
    start_time: str,
    end_time: str,
    # meeting db
    db: Session = Depends(get_meeting_db),
):
    """
    检查会议室预约时间是否可用
    返回是否可用、冲突的预约列表
    """
    try:
        from models.meeting_booking import MeetingBooking

        date_obj = datetime.strptime(booking_date, "%Y-%m-%d").date()

        conflicts = (
            db.query(MeetingBooking)
            .filter(
                MeetingBooking.room_id == room_id,
                MeetingBooking.booking_date == date_obj,
                MeetingBooking.status.in_(["pending", "confirmed"]),
                MeetingBooking.start_time < end_time,
                MeetingBooking.end_time > start_time,
            )
            .all()
        )

        is_available = len(conflicts) == 0

        return {
            "room_id": room_id,
            "booking_date": booking_date,
            "start_time": start_time,
            "end_time": end_time,
            "is_available": is_available,
            "conflicts": [
                {
                    "id": c.id,
                    "start_time": c.start_time,
                    "end_time": c.end_time,
                    "status": c.status,
                }
                for c in conflicts
            ]
            if not is_available
            else [],
        }
    except Exception as e:
        return {
            "room_id": room_id,
            "booking_date": booking_date,
            "start_time": start_time,
            "end_time": end_time,
            "is_available": False,
            "error": str(e),
        }


@router.get("/meeting/available-slots/{room_id}/{booking_date}")
def get_available_time_slots(
    room_id: int,
    booking_date: str,
    # meeting db
    db: Session = Depends(get_meeting_db),
):
    """
    获取指定日期的可预约时段列表
    """
    try:
        from models.meeting_booking import MeetingBooking

        date_obj = datetime.strptime(booking_date, "%Y-%m-%d").date()

        bookings = (
            db.query(MeetingBooking)
            .filter(
                MeetingBooking.room_id == room_id,
                MeetingBooking.booking_date == date_obj,
                MeetingBooking.status.in_(["pending", "confirmed"]),
            )
            .all()
        )

        booked_slots = [(b.start_time, b.end_time) for b in bookings]

        all_slots = []
        for hour in range(7, 22):
            for minute in [0, 30]:
                start = f"{hour:02d}:{minute:02d}"
                if minute == 0:
                    end = f"{hour:02d}:30"
                else:
                    end = f"{(hour + 1):02d}:00"

                is_available = True
                for booked_start, booked_end in booked_slots:
                    if start < booked_end and end > booked_start:
                        is_available = False
                        break

                all_slots.append(
                    {
                        "start_time": start,
                        "end_time": end,
                        "is_available": is_available,
                    }
                )

        return {
            "room_id": room_id,
            "booking_date": booking_date,
            "slots": all_slots,
            "total_slots": len(all_slots),
            "available_count": len([s for s in all_slots if s["is_available"]]),
        }
    except Exception as e:
        return {
            "room_id": room_id,
            "booking_date": booking_date,
            "slots": [],
            "error": str(e),
        }


# 3. 审批流程API
@router.get("/meeting/approvals")
def get_meeting_approvals(
    status: Optional[str] = None,
    # meeting db
    db: Session = Depends(get_meeting_db),
):
    """获取待审批的会议室预约列表"""
    try:
        from models.meeting_booking import MeetingBooking

        query = db.query(MeetingBooking).filter(
            MeetingBooking.is_approved == 0, MeetingBooking.status == "pending"
        )

        approvals = query.order_by(MeetingBooking.created_at.desc()).all()

        return [
            {
                "id": b.id,
                "room_id": b.room_id,
                "room_name": b.room_name,
                "user_id": b.user_id,
                "user_name": b.user_name,
                "booking_date": b.booking_date.isoformat() if b.booking_date else None,
                "start_time": b.start_time,
                "end_time": b.end_time,
                "meeting_title": getattr(b, "meeting_title", None),
                "attendees_count": getattr(b, "attendees_count", 1),
                "total_fee": float(getattr(b, "total_fee", 0) or 0),
                "created_at": b.created_at.isoformat() if b.created_at else None,
            }
            for b in approvals
        ]
    except Exception as e:
        return []


@router.post("/meeting/approvals/{booking_id}/approve")
def approve_meeting_booking(booking_id: int, db: Session = Depends(get_db)):
    """批准会议室预约"""
    try:
        from models.meeting_booking import MeetingBooking

        booking = (
            db.query(MeetingBooking).filter(MeetingBooking.id == booking_id).first()
        )
        if not booking:
            raise HTTPException(status_code=404, detail="预约不存在")

        booking.is_approved = 1
        booking.status = "confirmed"
        booking.approved_at = datetime.now()
        booking.updated_at = datetime.now()

        db.commit()

        return {
            "id": booking.id,
            "status": booking.status,
            "message": "预约已批准",
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"批准失败: {str(e)}")


@router.post("/meeting/approvals/{booking_id}/reject")
def reject_meeting_booking(
    booking_id: int, reason: Optional[str] = None, db: Session = Depends(get_db)
):
    """拒绝会议室预约"""
    try:
        from models.meeting_booking import MeetingBooking

        booking = (
            db.query(MeetingBooking).filter(MeetingBooking.id == booking_id).first()
        )
        if not booking:
            raise HTTPException(status_code=404, detail="预约不存在")

        booking.is_approved = 0
        booking.status = "rejected"
        booking.updated_at = datetime.now()

        db.commit()

        return {
            "id": booking.id,
            "status": booking.status,
            "message": "预约已拒绝",
            "reason": reason,
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"拒绝失败: {str(e)}")


# 4. 结算汇总API
@router.get("/meeting/settlements/summary")
def get_meeting_settlement_summary(
    month: Optional[str] = None,
    # meeting db
    db: Session = Depends(get_meeting_db),
):
    """获取会议室结算汇总"""
    try:
        from models.meeting_room import MeetingBooking
        from sqlalchemy import func

        if not month:
            month = datetime.now().strftime("%Y-%m")

        month_start = datetime.strptime(month + "-01", "%Y-%m-%d")
        if month_start.month == 12:
            month_end = datetime(month_start.year + 1, 1, 1)
        else:
            month_end = datetime(month_start.year, month_start.month + 1, 1)

        bookings = (
            db.query(MeetingBooking)
            .filter(
                MeetingBooking.booking_date >= month_start,
                MeetingBooking.booking_date < month_end,
                MeetingBooking.status == "completed",
            )
            .all()
        )

        total_bookings = len(bookings)
        total_hours = sum(float(getattr(b, "duration", 1) or 1) for b in bookings)
        total_revenue = sum(float(getattr(b, "total_fee", 0) or 0) for b in bookings)

        free_hours_used = sum(
            float(getattr(b, "free_hours_used", 0) or 0)
            for b in bookings
            if getattr(b, "free_hours_used", 0) > 0
        )
        paid_hours = total_hours - free_hours_used

        by_room = {}
        for b in bookings:
            room_id = b.room_id
            if room_id not in by_room:
                by_room[room_id] = {
                    "room_id": room_id,
                    "room_name": b.room_name,
                    "bookings": 0,
                    "hours": 0,
                    "revenue": 0,
                }
            by_room[room_id]["bookings"] += 1
            by_room[room_id]["hours"] += float(getattr(b, "duration", 1) or 1)
            by_room[room_id]["revenue"] += float(getattr(b, "total_fee", 0) or 0)

        return {
            "month": month,
            "total_bookings": total_bookings,
            "total_hours": round(total_hours, 2),
            "total_revenue": round(total_revenue, 2),
            "free_hours_used": round(free_hours_used, 2),
            "paid_hours": round(paid_hours, 2),
            "by_room": list(by_room.values()),
        }
    except Exception as e:
        print(f"获取结算汇总失败: {e}")
        return {
            "month": month,
            "total_bookings": 0,
            "total_hours": 0,
            "total_revenue": 0,
            "free_hours_used": 0,
            "paid_hours": 0,
            "by_room": [],
        }


@router.post("/meeting/bookings")
def create_meeting_booking(data: dict, db: Session = Depends(get_db)):
    """创建会议室预约"""
    try:
        from models.meeting_booking import MeetingBooking

        room_id = data.get("room_id")
        booking_date = data.get("booking_date")
        start_time = data.get("start_time")
        end_time = data.get("end_time")

        date_obj = datetime.strptime(booking_date, "%Y-%m-%d").date()

        conflicts = (
            db.query(MeetingBooking)
            .filter(
                MeetingBooking.room_id == room_id,
                MeetingBooking.booking_date == date_obj,
                MeetingBooking.status.in_(["pending", "confirmed"]),
                MeetingBooking.start_time < end_time,
                MeetingBooking.end_time > start_time,
            )
            .count()
        )

        if conflicts > 0:
            raise HTTPException(
                status_code=400, detail="该时段已被预约，请选择其他时段"
            )

        start_hour = int(start_time.split(":")[0])
        end_hour = int(end_time.split(":")[0])
        duration = end_hour - start_hour

        booking = MeetingBooking(
            room_id=room_id,
            room_name=data.get("room_name"),
            user_id=data.get("user_id"),
            user_name=data.get("user_name"),
            booking_date=date_obj,
            start_time=start_time,
            end_time=end_time,
            duration=duration,
            meeting_title=data.get("meeting_title"),
            attendees_count=data.get("attendees_count", 1),
            total_fee=duration * float(data.get("price_per_hour", 0)),
            status="pending",
            payment_status="pending",
            is_approved=0,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        db.add(booking)
        db.commit()
        db.refresh(booking)

        return {
            "id": booking.id,
            "room_name": booking.room_name,
            "booking_date": booking.booking_date.isoformat(),
            "start_time": booking.start_time,
            "end_time": booking.end_time,
            "message": "预约创建成功",
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"创建预约失败: {str(e)}")


@router.put("/meeting/bookings/{booking_id}/confirm")
def confirm_meeting_booking(booking_id: int, db: Session = Depends(get_db)):
    """确认会议室预约"""
    try:
        from models.meeting_booking import MeetingBooking

        booking = (
            db.query(MeetingBooking).filter(MeetingBooking.id == booking_id).first()
        )
        if not booking:
            raise HTTPException(status_code=404, detail="预约不存在")

        booking.status = "confirmed"
        booking.updated_at = datetime.now()

        db.commit()

        return {"message": "预约已确认", "booking_id": booking_id}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"确认失败: {str(e)}")


@router.put("/meeting/bookings/{booking_id}/cancel")
def cancel_meeting_booking(
    booking_id: int, reason: Optional[str] = None, db: Session = Depends(get_db)
):
    """取消会议室预约"""
    try:
        from models.meeting_booking import MeetingBooking

        booking = (
            db.query(MeetingBooking).filter(MeetingBooking.id == booking_id).first()
        )
        if not booking:
            raise HTTPException(status_code=404, detail="预约不存在")

        booking.status = "cancelled"
        booking.updated_at = datetime.now()

        db.commit()

        return {"message": "预约已取消", "booking_id": booking_id, "reason": reason}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"取消失败: {str(e)}")


# 5. 会员免费额度API
@router.get("/meeting/free-quota/{user_id}")
def get_user_free_quota(user_id: int, db: Session = Depends(get_db)):
    """获取用户会议室免费额度"""
    try:
        from models.meeting_room import MeetingBooking, MeetingRoom

        today = datetime.now().date()
        month_start = datetime(today.year, today.month, 1)

        month_bookings = (
            db.query(MeetingBooking)
            .filter(
                MeetingBooking.user_id == user_id,
                MeetingBooking.booking_date >= month_start,
                MeetingBooking.status.in_(["confirmed", "completed"]),
            )
            .all()
        )

        free_hours_used = sum(
            float(getattr(b, "free_hours_used", 0) or 0)
            for b in month_bookings
            if getattr(b, "free_hours_used", 0) > 0
        )

        default_free_hours = 5

        remaining_free_hours = max(0, default_free_hours - free_hours_used)

        return {
            "user_id": user_id,
            "month": today.strftime("%Y-%m"),
            "total_free_hours": default_free_hours,
            "used_free_hours": round(free_hours_used, 2),
            "remaining_free_hours": round(remaining_free_hours, 2),
        }
    except Exception as e:
        return {
            "user_id": user_id,
            "month": datetime.now().strftime("%Y-%m"),
            "total_free_hours": 5,
            "used_free_hours": 0,
            "remaining_free_hours": 5,
            "error": str(e),
        }


@router.get("/meeting/user/{user_id}/bookings")
def get_user_meeting_bookings(
    user_id: int, limit: int = 20, db: Session = Depends(get_db)
):
    """获取用户的会议室预约记录"""
    try:
        from models.meeting_booking import MeetingBooking

        bookings = (
            db.query(MeetingBooking)
            .filter(MeetingBooking.user_id == user_id)
            .order_by(MeetingBooking.created_at.desc())
            .limit(limit)
            .all()
        )

        return [
            {
                "id": b.id,
                "room_id": b.room_id,
                "room_name": b.room_name,
                "booking_date": b.booking_date.isoformat() if b.booking_date else None,
                "start_time": b.start_time,
                "end_time": b.end_time,
                "duration": getattr(b, "duration", None),
                "meeting_title": getattr(b, "meeting_title", None),
                "status": b.status,
                "total_fee": float(getattr(b, "total_fee", 0) or 0),
                "created_at": b.created_at.isoformat() if b.created_at else None,
            }
            for b in bookings
        ]
    except Exception as e:
        return []


# ==================== 结算管理补充 ====================


# 添加 /api/v1/water/settlements 路由（代理到v3结算API）
@router.get("/water/settlements/applications")
def get_water_settlements_applications(
    status: Optional[str] = None,
    office_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    """获取结算申请列表"""
    try:
        from models.pickup import OfficePickup

        query = db.query(OfficePickup).filter(OfficePickup.is_deleted == False)

        if status:
            query = query.filter(OfficePickup.settlement_status == status)
        if office_id:
            query = query.filter(OfficePickup.office_id == office_id)

        pickups = query.order_by(OfficePickup.pickup_time.desc()).all()

        applications = []
        for p in pickups:
            applications.append(
                {
                    "id": p.id,
                    "application_no": f"SA{p.id:06d}",
                    "office_id": p.office_id,
                    "office_name": p.office_name,
                    "office_room_number": getattr(p, "office_room_number", None),
                    "product_id": p.product_id,
                    "product_name": p.product_name,
                    "quantity": p.quantity,
                    "total_amount": float(getattr(p, "total_amount", 0) or 0),
                    "pickup_time": p.pickup_time.isoformat()
                    if hasattr(p, "pickup_time") and p.pickup_time
                    else None,
                    "status": p.settlement_status,
                    "pickup_person": getattr(p, "pickup_person", None),
                    "record_count": 1,
                    "applicant_name": getattr(p, "pickup_person", None),
                    "applied_at": p.pickup_time.isoformat()
                    if hasattr(p, "pickup_time") and p.pickup_time
                    else None,
                    "created_at": p.pickup_time.isoformat()
                    if hasattr(p, "pickup_time") and p.pickup_time
                    else None,
                }
            )

        return {"data": applications}
    except Exception as e:
        return {"data": []}


@router.get("/water/settlements/statistics")
def get_water_settlements_statistics(db: Session = Depends(get_db)):
    """获取结算统计"""
    try:
        from models.pickup import OfficePickup

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
            "pending_amount": sum(
                float(getattr(p, "total_amount", 0) or 0) for p in pending
            ),
            "applied_count": len(applied),
            "applied_amount": sum(
                float(getattr(p, "total_amount", 0) or 0) for p in applied
            ),
            "settled_count": len(settled),
            "settled_amount": sum(
                float(getattr(p, "total_amount", 0) or 0) for p in settled
            ),
        }
    except Exception as e:
        return {
            "pending_count": 0,
            "pending_amount": 0,
            "applied_count": 0,
            "applied_amount": 0,
            "settled_count": 0,
            "settled_amount": 0,
        }


@router.get("/water/settlements/applications/{application_id}")
def get_water_settlement_application(
    application_id: int, db: Session = Depends(get_db)
):
    """获取结算申请详情"""
    try:
        from models.pickup import OfficePickup

        pickup = (
            db.query(OfficePickup).filter(OfficePickup.id == application_id).first()
        )

        if not pickup:
            raise HTTPException(status_code=404, detail="申请不存在")

        return {
            "id": pickup.id,
            "application_no": f"SA{pickup.id:06d}",
            "office_id": pickup.office_id,
            "office_name": pickup.office_name,
            "office_room_number": getattr(pickup, "office_room_number", None),
            "product_id": pickup.product_id,
            "product_name": pickup.product_name,
            "quantity": pickup.quantity,
            "total_amount": float(getattr(pickup, "total_amount", 0) or 0),
            "pickup_time": pickup.pickup_time.isoformat()
            if hasattr(pickup, "pickup_time") and pickup.pickup_time
            else None,
            "status": pickup.settlement_status,
            "pickup_person": getattr(pickup, "pickup_person", None),
            "applicant_name": getattr(pickup, "pickup_person", None),
            "applied_at": pickup.pickup_time.isoformat()
            if hasattr(pickup, "pickup_time") and pickup.pickup_time
            else None,
            "created_at": pickup.pickup_time.isoformat()
            if hasattr(pickup, "pickup_time") and pickup.pickup_time
            else None,
            "pickups": [
                {
                    "id": pickup.id,
                    "product_name": pickup.product_name,
                    "quantity": pickup.quantity,
                    "amount": float(getattr(pickup, "total_amount", 0) or 0),
                }
            ],
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"获取详情失败: {str(e)}")


@router.post("/water/settlements/applications")
def create_water_settlement_application(data: dict, db: Session = Depends(get_db)):
    """创建结算申请"""
    try:
        from models.pickup import OfficePickup

        pickup_ids = data.get("pickup_ids", [])

        updated_count = 0
        for pickup_id in pickup_ids:
            pickup = db.query(OfficePickup).filter(OfficePickup.id == pickup_id).first()
            if pickup and pickup.settlement_status == "pending":
                pickup.settlement_status = "applied"
                pickup.updated_at = datetime.now()
                updated_count += 1

        db.commit()

        return {
            "message": f"成功创建申请，包含{updated_count}条记录",
            "updated_count": updated_count,
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"创建申请失败: {str(e)}")


@router.post("/water/settlements/applications/{application_id}/approve")
def approve_water_settlement_application(
    application_id: int, db: Session = Depends(get_db)
):
    """批准结算申请"""
    try:
        from models.pickup import OfficePickup

        pickup = (
            db.query(OfficePickup).filter(OfficePickup.id == application_id).first()
        )

        if not pickup:
            raise HTTPException(status_code=404, detail="申请不存在")

        pickup.settlement_status = "settled"
        pickup.updated_at = datetime.now()

        db.commit()

        return {
            "message": "申请已批准",
            "application_id": application_id,
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"批准失败: {str(e)}")


@router.post("/water/settlements/applications/{application_id}/reject")
def reject_water_settlement_application(
    application_id: int, data: dict, db: Session = Depends(get_db)
):
    """拒绝结算申请"""
    try:
        from models.pickup import OfficePickup

        pickup = (
            db.query(OfficePickup).filter(OfficePickup.id == application_id).first()
        )

        if not pickup:
            raise HTTPException(status_code=404, detail="申请不存在")

        pickup.settlement_status = "pending"
        pickup.updated_at = datetime.now()

        db.commit()

        return {
            "message": "申请已拒绝",
            "application_id": application_id,
            "reason": data.get("reason", ""),
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"拒绝失败: {str(e)}")


@router.post("/water/settlements/applications/{application_id}/confirm")
def confirm_water_settlement_application(
    application_id: int, db: Session = Depends(get_db)
):
    """确认结算申请"""
    try:
        from models.pickup import OfficePickup

        pickup = (
            db.query(OfficePickup).filter(OfficePickup.id == application_id).first()
        )

        if not pickup:
            raise HTTPException(status_code=404, detail="申请不存在")

        pickup.settlement_status = "settled"
        pickup.updated_at = datetime.now()

        db.commit()

        return {
            "message": "申请已确认",
            "application_id": application_id,
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"确认失败: {str(e)}")


@router.post("/water/settlements/batch-confirm")
def batch_confirm_water_settlements(data: dict, db: Session = Depends(get_db)):
    """批量确认结算"""
    try:
        from models.pickup import OfficePickup

        application_ids = data.get("application_ids", [])

        updated_count = 0
        for application_id in application_ids:
            pickup = (
                db.query(OfficePickup).filter(OfficePickup.id == application_id).first()
            )
            if pickup and pickup.settlement_status in ["pending", "applied"]:
                pickup.settlement_status = "settled"
                pickup.updated_at = datetime.now()
                updated_count += 1

        db.commit()

        return {
            "message": f"成功确认{updated_count}条申请",
            "updated_count": updated_count,
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"批量确认失败: {str(e)}")


# 6. 操作日志API
@router.get("/meeting/operation-logs")
def get_meeting_operation_logs(
    room_id: Optional[int] = None,
    limit: int = 50,
    # meeting db
    db: Session = Depends(get_meeting_db),
):
    """获取会议室操作日志"""
    try:
        from sqlalchemy import text

        query = "SELECT * FROM meeting_operation_logs WHERE 1=1"
        if room_id:
            query += f" AND room_id = {room_id}"
        query += " ORDER BY created_at DESC LIMIT :limit"

        results = db.execute(text(query), {"limit": limit}).fetchall()

        return [
            {
                "id": r.id,
                "room_id": r.room_id,
                "operation_type": r.operation_type,
                "operator_id": r.operator_id,
                "operator_name": r.operator_name,
                "details": r.details,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in results
        ]
    except Exception as e:
        return []
