"""
领水API路由
包含办公室领水、结算等功能
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta

from config.database import get_db
from models.user import User
from models.product import Product
from models.account import OfficeAccount
from models.inventory import InventoryRecord
from models.office import Office
from models.pickup import OfficePickup
from depends.auth import get_current_user, get_admin_user, get_super_admin_user
from schemas.water import (
    OfficePickupCreate,
    OfficePickupUpdate,
    OfficePickupResponse,
    SettlementApply,
    SettlementConfirm,
    OfficeAccountResponse,
    UserOfficeResponse,
)
from promo_calculator import calculate_promo_amount

router = APIRouter(prefix="/api", tags=["领水管理"])


@router.get("/user/offices", response_model=List[UserOfficeResponse])
def get_user_offices(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取用户可用的办公室列表（根据用户部门过滤）"""

    query = db.query(OfficeAccount).filter(OfficeAccount.status == "active")

    if current_user.role not in ["admin", "super_admin"]:
        query = query.filter(OfficeAccount.office_name == current_user.department)

    accounts = query.distinct(OfficeAccount.office_id).all()

    offices = {}
    for a in accounts:
        if a.office_id not in offices:
            offices[a.office_id] = {
                "office_id": a.office_id,
                "office_name": a.office_name,
                "office_room_number": a.office_room_number,
                "manager_name": a.manager_name,
            }

    return list(offices.values())


@router.post("/user/office-pickup")
def create_office_pickup(
    pickup: dict,
    current_user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """创建办公室领水记录"""
    from promo_calculator import calculate_promo_amount

    office_id = pickup.get("office_id")
    product_id = pickup.get("product_id")
    quantity = pickup.get("quantity")
    pickup_person = pickup.get("pickup_person")
    pickup_person_id = pickup.get("pickup_person_id")
    pickup_time_str = pickup.get("pickup_time")

    office = db.query(Office).filter(Office.id == office_id).first()
    if not office:
        raise HTTPException(status_code=404, detail="办公室不存在")

    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="产品不存在")

    if product.stock is None:
        product.stock = 0
    if product.stock < quantity:
        raise HTTPException(
            status_code=400,
            detail=f"库存不足，当前库存: {product.stock} {product.unit}，领取数量: {quantity} {product.unit}",
        )
    before_stock = product.stock
    product.stock -= quantity

    pickup_time = datetime.now()
    if pickup_time_str:
        try:
            pickup_time = datetime.fromisoformat(pickup_time_str.replace("Z", "+00:00"))
        except:
            pickup_time = datetime.now()

    unit_price = product.price or 0
    promo_result = calculate_promo_amount(
        quantity=quantity,
        unit_price=unit_price,
        promo_threshold=product.promo_threshold or 0,
        promo_gift=product.promo_gift or 0,
    )
    total_amount = promo_result["total_amount"]
    free_qty = promo_result["free_qty"]
    discount_desc = promo_result["discount_desc"]

    pickup_person_name = pickup_person
    pickup_person_id_val = pickup_person_id

    if not pickup_person_name and current_user:
        pickup_person_name = current_user.name
    if not pickup_person_id_val and current_user:
        pickup_person_id_val = current_user.id

    new_pickup = OfficePickup(
        office_id=office_id,
        office_name=office.name,
        office_room_number=office.room_number,
        product_id=product_id,
        product_name=product.name,
        product_specification=product.specification,
        quantity=quantity,
        pickup_person=pickup_person_name or "匿名",
        pickup_person_id=pickup_person_id_val,
        pickup_time=pickup_time,
        unit_price=unit_price,
        total_amount=total_amount,
        free_qty=free_qty,
        discount_desc=discount_desc if free_qty > 0 else None,
        settlement_status="pending",
    )

    db.add(new_pickup)
    db.flush()

    inventory_record = InventoryRecord(
        product_id=product.id,
        type="out",
        quantity=quantity,
        before_stock=before_stock,
        after_stock=product.stock,
        reference_type="office_pickup",
        reference_id=new_pickup.id,
        operator_id=pickup_person_id_val,
        note=f"办公室领水: {office.name}",
    )
    db.add(inventory_record)
    db.commit()
    db.refresh(new_pickup)

    return {"id": new_pickup.id, "message": "领水记录创建成功"}


@router.get("/user/office-pickups")
def get_user_office_pickups(
    limit: int = 100,
    offset: int = 0,
    current_user: Optional[User] = Depends(get_current_user),
    office_id: Optional[int] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """获取当前用户的办公室领水记录"""

    query = db.query(OfficePickup).filter(OfficePickup.is_deleted == 0)

    if current_user and current_user.role not in ["admin", "super_admin"]:
        user_name = current_user.name
        user_department = current_user.department
        query = query.filter(
            (OfficePickup.pickup_person == user_name)
            | (OfficePickup.office_name == user_department)
        )

    if office_id is not None:
        query = query.filter(OfficePickup.office_id == office_id)

    if status and status != "all":
        query = query.filter(OfficePickup.settlement_status == status)

    pickups = (
        query.order_by(OfficePickup.pickup_time.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    results = []
    for pickup in pickups:
        results.append(
            {
                "id": pickup.id,
                "office_id": pickup.office_id,
                "user_id": pickup.pickup_person_id,
                "user_name": pickup.pickup_person,
                "department": pickup.office_name,
                "office_name": pickup.office_name,
                "office_room_number": pickup.office_room_number,
                "product_id": pickup.product_id,
                "product_name": pickup.product_name,
                "product_specification": pickup.product_specification,
                "quantity": pickup.quantity,
                "pickup_person": pickup.pickup_person,
                "pickup_person_id": pickup.pickup_person_id,
                "pickup_time": pickup.pickup_time.isoformat()
                if pickup.pickup_time
                else None,
                "payment_mode": pickup.payment_mode,
                "settlement_status": pickup.settlement_status,
                "unit_price": pickup.unit_price,
                "total_amount": pickup.total_amount,
                "status": pickup.settlement_status,
            }
        )

    return results


@router.get("/user/office-pickup-summary")
def get_user_office_pickup_summary(
    office_id: int = None,
    current_user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取用户办公室领水汇总信息"""

    if not office_id:
        return {
            "pending": {"count": 0, "amount": 0},
            "applied": {"count": 0, "amount": 0},
            "settled": {"count": 0, "amount": 0},
        }

    query = db.query(OfficePickup).filter(
        OfficePickup.office_id == office_id, OfficePickup.is_deleted == 0
    )

    if current_user and current_user.role not in ["admin", "super_admin"]:
        query = query.filter(OfficePickup.pickup_person == current_user.name)

    pickups = query.all()

    pending_count = 0
    pending_amount = 0.0
    applied_count = 0
    applied_amount = 0.0
    settled_count = 0
    settled_amount = 0.0

    for p in pickups:
        if p.settlement_status == "pending":
            pending_count += 1
            pending_amount += p.total_amount or 0
        elif p.settlement_status == "applied":
            applied_count += 1
            applied_amount += p.total_amount or 0
        elif p.settlement_status == "settled":
            settled_count += 1
            settled_amount += p.total_amount or 0

    return {
        "pending": {"count": pending_count, "amount": round(pending_amount, 2)},
        "applied": {"count": applied_count, "amount": round(applied_amount, 2)},
        "settled": {"count": settled_count, "amount": round(settled_amount, 2)},
    }


@router.put("/admin/office-pickups/{pickup_id}")
def update_office_pickup(
    pickup_id: int,
    pickup_update: dict,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    """编辑办公室领水记录（管理员）"""
    from promo_calculator import calculate_promo_amount

    pickup = db.query(OfficePickup).filter(OfficePickup.id == pickup_id).first()
    if not pickup:
        raise HTTPException(status_code=404, detail="领水记录不存在")

    if "quantity" in pickup_update:
        old_quantity = pickup.quantity
        new_quantity = pickup_update["quantity"]

        product = db.query(Product).filter(Product.id == pickup.product_id).first()
        if product:
            product.stock += old_quantity
            if product.stock < new_quantity:
                raise HTTPException(status_code=400, detail=f"库存不足")
            product.stock -= new_quantity

            unit_price = product.price or 0
            promo_result = calculate_promo_amount(
                quantity=new_quantity,
                unit_price=unit_price,
                promo_threshold=product.promo_threshold or 0,
                promo_gift=product.promo_gift or 0,
            )
            pickup.quantity = new_quantity
            pickup.total_amount = promo_result["total_amount"]
            pickup.free_qty = promo_result["free_qty"]
            pickup.discount_desc = (
                promo_result["discount_desc"] if promo_result["free_qty"] > 0 else None
            )

    if "pickup_person" in pickup_update:
        pickup.pickup_person = pickup_update["pickup_person"]

    if "note" in pickup_update:
        pickup.note = pickup_update["note"]

    if "pickup_time" in pickup_update:
        try:
            pickup.pickup_time = datetime.fromisoformat(
                pickup_update["pickup_time"].replace("Z", "+00:00")
            )
        except:
            pass

    db.commit()
    db.refresh(pickup)

    return {"id": pickup.id, "message": "领水记录更新成功"}


@router.delete("/admin/office-pickups/{pickup_id}")
def delete_office_pickup(
    pickup_id: int,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    """删除办公室领水记录（管理员）- 软删除"""

    pickup = db.query(OfficePickup).filter(OfficePickup.id == pickup_id).first()
    if not pickup:
        raise HTTPException(status_code=404, detail="领水记录不存在")

    product = db.query(Product).filter(Product.id == pickup.product_id).first()
    if product:
        product.stock += pickup.quantity

    pickup.is_deleted = 1
    pickup.deleted_at = datetime.now()
    pickup.deleted_by = current_user.id
    pickup.delete_reason = "管理员删除"

    db.commit()

    return {"message": "领水记录删除成功"}


@router.post("/admin/settlement/apply")
def apply_settlement(
    application: dict,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    """提交结算申请（管理员）"""

    pickup_ids = application.get("pickup_ids", [])
    if not pickup_ids:
        raise HTTPException(status_code=400, detail="请选择要结算的记录")

    updated_count = 0
    total_amount = 0

    for pickup_id in pickup_ids:
        pickup = (
            db.query(OfficePickup)
            .filter(
                OfficePickup.id == pickup_id,
                OfficePickup.settlement_status == "pending",
            )
            .first()
        )

        if pickup:
            pickup.settlement_status = "applied"
            updated_count += 1
            total_amount += pickup.total_amount

    db.commit()

    return {
        "message": "结算申请提交成功",
        "updated_count": updated_count,
        "total_amount": total_amount,
    }


@router.post("/admin/settlement/{pickup_id}/confirm")
def confirm_settlement(
    pickup_id: int,
    confirmation: dict,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    """确认结算（管理员）"""

    pickup = db.query(OfficePickup).filter(OfficePickup.id == pickup_id).first()
    if not pickup:
        raise HTTPException(status_code=404, detail="领水记录不存在")

    if pickup.settlement_status not in ["pending", "applied"]:
        raise HTTPException(status_code=400, detail="该记录不可确认结算")

    pickup.settlement_status = "settled"
    db.commit()

    return {"message": "结算确认成功", "pickup_id": pickup_id}


@router.post("/admin/settlement/{pickup_id}/reject")
def reject_settlement(
    pickup_id: int,
    rejection: dict,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    """拒绝结算（管理员）- 将状态改回pending"""

    pickup = db.query(OfficePickup).filter(OfficePickup.id == pickup_id).first()
    if not pickup:
        raise HTTPException(status_code=404, detail="领水记录不存在")

    if pickup.settlement_status != "applied":
        raise HTTPException(status_code=400, detail="只能拒绝已申请的结算")

    pickup.settlement_status = "pending"
    db.commit()

    return {"message": "结算已拒绝", "pickup_id": pickup_id}


@router.post("/admin/settlement/batch-confirm")
def batch_confirm_settlement(
    confirmation: dict,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    """批量确认结算（管理员）"""

    pickup_ids = confirmation.get("pickup_ids", [])
    if not pickup_ids:
        raise HTTPException(status_code=400, detail="请选择要确认的记录")

    updated_count = 0
    total_amount = 0

    for pickup_id in pickup_ids:
        pickup = (
            db.query(OfficePickup)
            .filter(
                OfficePickup.id == pickup_id,
                OfficePickup.settlement_status.in_(["pending", "applied"]),
            )
            .first()
        )

        if pickup:
            pickup.settlement_status = "settled"
            updated_count += 1
            total_amount += pickup.total_amount

    db.commit()

    return {
        "message": "批量确认结算成功",
        "updated_count": updated_count,
        "total_amount": total_amount,
    }


@router.get("/admin/office-pickups/trash")
def get_trash_office_pickups(
    days: int = 30,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    """获取回收站中的领水记录（保留最近 days 天）"""

    cutoff_date = datetime.now() - timedelta(days=days)

    pickups = (
        db.query(OfficePickup)
        .filter(OfficePickup.is_deleted == 1, OfficePickup.deleted_at >= cutoff_date)
        .order_by(OfficePickup.deleted_at.desc())
        .all()
    )

    results = []
    for p in pickups:
        deleter = (
            db.query(User).filter(User.id == p.deleted_by).first()
            if p.deleted_by
            else None
        )

        results.append(
            {
                "id": p.id,
                "office_id": p.office_id,
                "office_name": p.office_name,
                "product_name": p.product_name,
                "product_specification": p.product_specification,
                "quantity": p.quantity,
                "pickup_person": p.pickup_person,
                "pickup_time": p.pickup_time.isoformat() if p.pickup_time else None,
                "payment_mode": p.payment_mode,
                "settlement_status": p.settlement_status,
                "total_amount": p.total_amount,
                "deleted_at": p.deleted_at.isoformat() if p.deleted_at else None,
                "deleted_by": p.deleted_by,
                "deleter_name": deleter.name if deleter else "Unknown",
                "delete_reason": p.delete_reason,
            }
        )

    return results


@router.post("/admin/office-pickups/trash/restore")
def restore_trash_office_pickups(
    request: dict,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    """恢复回收站中的领水记录"""

    pickup_ids = request.get("transaction_ids", [])

    restored = 0
    for pid in pickup_ids:
        pickup = (
            db.query(OfficePickup)
            .filter(OfficePickup.id == pid, OfficePickup.is_deleted == 1)
            .first()
        )
        if pickup:
            pickup.is_deleted = 0
            pickup.deleted_at = None
            pickup.deleted_by = None
            pickup.delete_reason = None
            restored += 1

    db.commit()
    return {"message": f"成功恢复 {restored} 条记录", "restored_count": restored}


@router.delete("/admin/office-pickups/trash/{pickup_id}")
def permanently_delete_office_pickup(
    pickup_id: int,
    current_user: User = Depends(get_super_admin_user),
    db: Session = Depends(get_db),
):
    """永久删除回收站中的领水记录（仅超级管理员）"""

    pickup = (
        db.query(OfficePickup)
        .filter(OfficePickup.id == pickup_id, OfficePickup.is_deleted == 1)
        .first()
    )

    if not pickup:
        raise HTTPException(status_code=404, detail="记录不存在")

    db.delete(pickup)
    db.commit()

    return {"message": "记录已永久删除", "pickup_id": pickup_id}
