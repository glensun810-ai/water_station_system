"""
办公室账户管理API - v1版本
为前端 accounts.html 页面提供完整的账户管理接口
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel

router = APIRouter(prefix="/office-accounts", tags=["办公室账户管理"])


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


def get_db():
    from config.database import SessionLocal

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("")
def get_office_accounts(
    office_id: Optional[int] = None,
    product_id: Optional[int] = None,
    status: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
):
    from models.account import OfficeAccount

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


@router.post("")
def create_office_account(
    account: OfficeAccountCreate,
    db: Session = Depends(get_db),
):
    from models.account import OfficeAccount
    from models.office import Office
    from models.product import Product

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


@router.put("/{account_id}")
def update_office_account(
    account_id: int,
    account: OfficeAccountUpdate,
    db: Session = Depends(get_db),
):
    from models.account import OfficeAccount
    from models.office import Office
    from models.product import Product

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


@router.delete("/{account_id}")
def delete_office_account(
    account_id: int,
    db: Session = Depends(get_db),
):
    from models.account import OfficeAccount

    account = db.query(OfficeAccount).filter(OfficeAccount.id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="账户不存在")

    db.delete(account)
    db.commit()

    return {"message": "账户已删除", "id": account_id}


@router.post("/{account_id}/recharge")
def recharge_office_account(
    account_id: int,
    recharge: OfficeAccountRecharge,
    db: Session = Depends(get_db),
):
    from models.account import OfficeAccount

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
