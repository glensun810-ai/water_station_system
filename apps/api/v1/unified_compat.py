"""
Minimal compatibility routes for unified account API (water frontend compat).
These stub the original apps.water.api_unified routes using existing models/services.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime

from config.database import get_db
from depends.auth import get_current_user
from models.user import User
from models.product import Product
from models.office import Office
from models.pickup import OfficePickup

router = APIRouter(prefix="/api/unified", tags=["unified-account-compat"])


@router.get("/user/{user_id}/balance")
def get_user_balance(
    user_id: int,
    product_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get user balance for all products (or specific product)."""
    products = db.query(Product).filter(Product.is_active == True).all()
    result = []
    for p in products:
        if product_id and p.id != product_id:
            continue
        # Calculate used quantity from pickups
        from sqlalchemy import func
        picked = db.query(func.coalesce(func.sum(OfficePickup.quantity), 0)).filter(
            OfficePickup.pickup_person_id == user_id,
            OfficePickup.product_id == p.id,
            OfficePickup.is_deleted == False,
        ).scalar()
        result.append({
            "product_id": p.id,
            "product_name": p.name,
            "product_specification": p.specification,
            "unit": p.unit,
            "unit_price": float(p.price) if p.price else 0.0,
            "balance": {
                "total_picked": int(picked),
                "prepaid_remaining": 0,
                "credit_remaining": 0,
                "gifted_remaining": 0,
            },
        })
    return {"user_id": user_id, "products": result}


@router.get("/transactions/{user_id}")
def get_transactions(
    user_id: int,
    limit: int = Query(20),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get recent transactions for a user (pickup records)."""
    pickups = db.query(OfficePickup).filter(
        OfficePickup.pickup_person_id == user_id,
        OfficePickup.is_deleted == False,
    ).order_by(OfficePickup.pickup_time.desc()).limit(limit).all()

    result = []
    for p in pickups:
        result.append({
            "id": p.id,
            "type": "pickup",
            "product_name": p.product_name,
            "quantity": p.quantity,
            "total_amount": float(p.total_amount) if p.total_amount else 0.0,
            "free_qty": p.free_qty or 0,
            "created_at": p.pickup_time.isoformat() if p.pickup_time else None,
            "status": p.settlement_status,
        })
    return result


@router.post("/pickup/calculate")
def calculate_pickup(
    request: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Calculate pickup cost before submitting."""
    product_id = request.get("product_id")
    quantity = request.get("quantity", 1)

    product = db.query(Product).filter(Product.id == product_id, Product.is_active == True).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    if product.stock < quantity:
        raise HTTPException(status_code=400, detail=f"Insufficient stock: {product.stock}")

    free_qty = 0
    if product.promo_threshold and product.promo_gift:
        total_qty = quantity
        cycles = total_qty // (product.promo_threshold + product.promo_gift)
        remainder = total_qty % (product.promo_threshold + product.promo_gift)
        free_qty = cycles * product.promo_gift
        if remainder > product.promo_threshold:
            free_qty += min(remainder - product.promo_threshold, product.promo_gift)

    paid_qty = quantity - free_qty
    unit_price = float(product.price) if product.price else 0.0
    total_amount = paid_qty * unit_price

    return {
        "product_id": product_id,
        "product_name": product.name,
        "quantity": quantity,
        "paid_qty": paid_qty,
        "free_qty": free_qty,
        "unit_price": unit_price,
        "total_amount": total_amount,
    }


@router.post("/pickup/record")
def record_pickup(
    request: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Record a pickup (creates office pickup record)."""
    user_id = request.get("user_id")
    product_id = request.get("product_id")
    quantity = request.get("quantity", 1)
    note = request.get("note", "")

    product = db.query(Product).filter(Product.id == product_id, Product.is_active == True).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    if product.stock < quantity:
        raise HTTPException(status_code=400, detail=f"Insufficient stock")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Find user's office
    office = None
    if user.department:
        office = db.query(Office).filter(Office.name == user.department, Office.is_active == True).first()

    # Calculate costs
    free_qty = 0
    if product.promo_threshold and product.promo_gift:
        cycles = quantity // (product.promo_threshold + product.promo_gift)
        remainder = quantity % (product.promo_threshold + product.promo_gift)
        free_qty = cycles * product.promo_gift
        if remainder > product.promo_threshold:
            free_qty += min(remainder - product.promo_threshold, product.promo_gift)

    paid_qty = quantity - free_qty
    unit_price = float(product.price) if product.price else 0.0
    total_amount = paid_qty * unit_price

    pickup = OfficePickup(
        office_id=office.id if office else None,
        office_name=office.name if office else (user.department or "Unknown"),
        office_room_number=office.room_number if office else "",
        product_id=product_id,
        product_name=product.name,
        product_specification=product.specification,
        quantity=quantity,
        unit_price=unit_price,
        total_amount=total_amount,
        free_qty=free_qty,
        pickup_person=user.username,
        pickup_person_id=user_id,
        pickup_time=datetime.now(),
        settlement_status="pending",
        is_deleted=False,
    )

    product.stock -= quantity
    db.add(pickup)
    db.commit()
    db.refresh(pickup)

    return {
        "id": pickup.id,
        "message": "Pickup recorded successfully",
        "paid_qty": paid_qty,
        "free_qty": free_qty,
        "total_amount": total_amount,
    }
