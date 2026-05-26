"""
Minimal compatibility routes for unified account API (water frontend compat).
Queries both main app DB (products, pickups, UserBalanceAccount) and water DB (wallet balances).
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
from models.user_balance import UserBalanceAccount, BalanceDeductRecord, BalanceTransaction

# 水服务数据库连接（独立 waterms.db）
from apps.water.database import SessionLocal as WaterSessionLocal
from apps.water.models_unified import AccountWallet

router = APIRouter(prefix="/api/unified", tags=["unified-account-compat"])


@router.get("/user/{user_id}/balance")
def get_user_balance(
    user_id: int,
    product_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get user balance for all products (or specific product).

    Queries main DB for products/pickups and water DB for wallet balances.
    """
    products = db.query(Product).filter(Product.is_active == True).all()

    # Query UserBalanceAccount for membership/service/gift balances
    balance_account = db.query(UserBalanceAccount).filter(
        UserBalanceAccount.user_id == user_id
    ).first()

    # Query water DB for wallet balances
    water_db = WaterSessionLocal()
    try:
        wallets = water_db.query(AccountWallet).filter(
            AccountWallet.user_id == user_id
        ).all()
        # Build lookup: product_id -> wallet
        wallet_map = {}
        for w in wallets:
            wallet_map[w.product_id] = w

        result = []
        for p in products:
            if product_id and p.id != product_id:
                continue

            from sqlalchemy import func
            picked = db.query(func.coalesce(func.sum(OfficePickup.quantity), 0)).filter(
                OfficePickup.pickup_person_id == user_id,
                OfficePickup.product_id == p.id,
                OfficePickup.is_deleted == False,
            ).scalar()

            wallet = wallet_map.get(p.id)

            result.append({
                "product_id": p.id,
                "product_name": p.name,
                "product_specification": p.specification,
                "unit": p.unit,
                "unit_price": float(p.price) if p.price else 0.0,
                "balance": {
                    "total_picked": int(picked),
                    "prepaid_remaining": wallet.available_qty if wallet else 0,
                    "credit_remaining": float(balance_account.membership_balance) if balance_account else 0.0,
                    "gifted_remaining": wallet.free_qty if wallet else 0,
                },
            })
        return {"user_id": user_id, "products": result}
    finally:
        water_db.close()


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
    """Record a pickup (creates office pickup record) with optional balance deduction."""
    user_id = request.get("user_id")
    product_id = request.get("product_id")
    quantity = request.get("quantity", 1)
    note = request.get("note", "")
    use_balance = request.get("use_balance", False)

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

    # 尝试从 UserBalanceAccount 抵扣额度
    balance_deducted = 0.0
    balance_details = {}
    if use_balance and total_amount > 0:
        balance_account = db.query(UserBalanceAccount).filter(
            UserBalanceAccount.user_id == user_id
        ).first()

        if balance_account:
            available = balance_account.get_available_balance()
            from decimal import Decimal
            remaining = Decimal(str(total_amount))
            m_deduct = s_deduct = g_deduct = Decimal(0)

            avail_m = Decimal(str(available["membership"]))
            avail_s = Decimal(str(available["service"]))
            avail_g = Decimal(str(available["gift"]))

            if avail_m > 0 and remaining > 0:
                m_deduct = min(remaining, avail_m)
                remaining -= m_deduct
                balance_account.membership_balance -= m_deduct

            if avail_s > 0 and remaining > 0:
                s_deduct = min(remaining, avail_s)
                remaining -= s_deduct
                balance_account.service_balance -= s_deduct

            if avail_g > 0 and remaining > 0:
                g_deduct = min(remaining, avail_g)
                remaining -= g_deduct
                balance_account.gift_balance -= g_deduct

            total_deducted = m_deduct + s_deduct + g_deduct

            # 信用额度：额度不足时，可透支消费（以信用额度为上限）
            credit_used_amount = Decimal(0)
            if remaining > 0:
                credit_limit = Decimal(str(balance_account.credit_limit or 0))
                credit_already_used = Decimal(str(balance_account.credit_used or 0))
                available_credit = credit_limit - credit_already_used
                if available_credit > 0:
                    credit_used_amount = min(remaining, available_credit)
                    remaining -= credit_used_amount
                    balance_account.credit_used = credit_already_used + credit_used_amount

            if total_deducted > 0 or credit_used_amount > 0:
                balance_account.update_total_balance()
                balance_account.total_deducted += total_deducted + credit_used_amount
                balance_account.last_transaction_at = datetime.now()

                deduct_record = BalanceDeductRecord(
                    deduct_no=f"WD{datetime.now().strftime('%Y%m%d%H%M%S%f')}",
                    user_id=user_id,
                    order_type="water",
                    order_id=0,
                    order_no=f"pickup_{user_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                    total_amount=Decimal(str(total_amount)),
                    membership_deduct=m_deduct,
                    service_deduct=s_deduct,
                    gift_deduct=g_deduct,
                    cash_amount=remaining,
                    description=f"用水领取 - {product.name} ×{quantity}",
                )
                db.add(deduct_record)

                tx = BalanceTransaction(
                    transaction_no=f"TX{datetime.now().strftime('%Y%m%d%H%M%S%f')}",
                    user_id=user_id,
                    transaction_type="DEDUCT",
                    amount=-(total_deducted + credit_used_amount),
                    before_total_balance=available["total"],
                    after_total_balance=float(balance_account.total_balance),
                    reference_type="water_pickup",
                    reference_no=f"pickup_{user_id}",
                    description=f"用水领取额度抵扣 - {product.name}",
                )
                db.add(tx)

                balance_deducted = float(total_deducted + credit_used_amount)
                balance_details = {
                    "membership_deduct": float(m_deduct),
                    "service_deduct": float(s_deduct),
                    "gift_deduct": float(g_deduct),
                    "credit_deduct": float(credit_used_amount),
                    "remaining_cash": float(remaining),
                }

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
        "balance_deducted": balance_deducted,
        **({"balance_details": balance_details} if balance_details else {}),
    }
