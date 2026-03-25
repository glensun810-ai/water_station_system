"""
Unified Account API Routes - 统一账户 API 路由
提供统一账户管理、领取、结算等功能接口
"""

from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy import create_engine, text, func
from datetime import datetime
from typing import List, Optional
import json

from models_unified import (
    UserAccount,
    AccountWallet,
    SettlementBatch,
    TransactionV2,
    PromotionConfigV2,
)
from account_service import AccountService, PickupService, SettlementService
from discount_strategy import discount_context, get_product
from exceptions import InsufficientBalanceError

# 本地定义 get_db 依赖注入，避免循环导入
SQLALCHEMY_DATABASE_URL = "sqlite:///./waterms.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# 需要导入主程序的依赖
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


router = APIRouter(prefix="/api/unified", tags=["unified-account"])


# ==================== 依赖注入 ====================
def get_unified_services(db: Session):
    """获取统一账户服务"""
    return {
        "account": AccountService(db),
        "pickup": PickupService(db),
        "settlement": SettlementService(db),
    }


# ==================== Pydantic Schemas ====================
from pydantic import BaseModel, ConfigDict
from typing import Dict, Any


class AccountBalanceResponse(BaseModel):
    """账户余额响应"""

    user_id: int
    balance_prepaid: float
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class WalletResponse(BaseModel):
    """钱包响应"""

    id: int
    user_id: int
    product_id: int
    wallet_type: str
    available_qty: int
    locked_qty: int
    total_consumed: int

    model_config = ConfigDict(from_attributes=True)


class WalletBalanceRequest(BaseModel):
    """钱包余额调整请求"""

    product_id: int
    wallet_type: str  # 'credit' or 'prepaid'
    quantity: int
    note: Optional[str] = None


class PickupCalculateRequest(BaseModel):
    """领取计算请求"""

    user_id: int
    product_id: int
    quantity: int


class PickupCalculateResponse(BaseModel):
    """领取计算响应"""

    quantity: int
    prepaid: Dict[str, Any]
    credit: Dict[str, Any]
    total_price: float
    balance_after: Dict[str, float]


class PickupRecordRequest(BaseModel):
    """领取记录请求"""

    user_id: int
    product_id: int
    quantity: int
    note: Optional[str] = None


class PickupRecordResponse(BaseModel):
    """领取记录响应"""

    transactions: List[Dict[str, Any]]
    consume_result: Dict[str, Any]
    message: str


class UserBalanceResponse(BaseModel):
    """用户余额响应"""

    user_id: int
    products: List[Dict[str, Any]]


class SettlementApplyRequest(BaseModel):
    """结算申请请求"""

    user_id: int
    transaction_ids: List[int]


class SettlementBatchResponse(BaseModel):
    """结算批次响应"""

    id: int
    batch_no: str
    user_id: int
    total_amount: float
    status: str
    created_at: datetime
    confirmed_at: Optional[datetime] = None
    confirmed_by: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


class PromotionConfigRequest(BaseModel):
    """优惠配置请求"""

    product_id: int
    mode: str  # 'credit' or 'prepaid'
    trigger_qty: int = 0
    gift_qty: int = 0
    discount_rate: float = 100.0
    is_active: int = 1
    description: Optional[str] = None


class PromotionConfigResponse(BaseModel):
    """优惠配置响应"""

    id: int
    product_id: int
    mode: str
    trigger_qty: int
    gift_qty: int
    discount_rate: float
    is_active: int
    description: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class FinancialReportResponse(BaseModel):
    """财务报表响应"""

    period: Dict[str, str]
    credit: Dict[str, Any]
    prepaid: Dict[str, Any]
    summary: Dict[str, Any]


# ==================== API Endpoints ====================


@router.get("/account/{user_id}")
def get_account(user_id: int, db: Session = Depends(get_db)) -> AccountBalanceResponse:
    """
    获取用户账户信息

    - **user_id**: 用户 ID
    """
    service = AccountService(db)
    account = service.get_account(user_id)

    if not account:
        # 如果账户不存在，返回空账户
        return AccountBalanceResponse(
            user_id=user_id, balance_credit=0.0, balance_prepaid=0.0
        )

    return account


@router.post("/account/{user_id}/initialize")
def initialize_account(user_id: int, db: Session = Depends(get_db)):
    """
    初始化用户账户

    - **user_id**: 用户 ID
    """
    service = AccountService(db)
    account = service.get_or_create_account(user_id)

    return {
        "message": "账户初始化成功",
        "account": {
            "user_id": account.user_id,
            "balance_prepaid": account.balance_prepaid,
        },
    }


@router.get("/wallet/{user_id}/{product_id}/{wallet_type}")
def get_wallet(
    user_id: int, product_id: int, wallet_type: str, db: Session = Depends(get_db)
) -> WalletResponse:
    """
    获取用户钱包信息

    - **user_id**: 用户 ID
    - **product_id**: 产品 ID
    - **wallet_type**: 钱包类型 ('prepaid')
    """
    if wallet_type != "prepaid":
        raise HTTPException(status_code=400, detail="钱包类型必须是 'prepaid'")

    service = AccountService(db)
    wallet = service.get_wallet(user_id, product_id, wallet_type)

    if not wallet:
        raise HTTPException(status_code=404, detail="钱包不存在")

    return wallet


@router.post("/wallet/balance")
def adjust_wallet_balance(
    request: WalletBalanceRequest, user_id: int, db: Session = Depends(get_db)
):
    """
    调整钱包余额（充值/授信）- 支持买赠优惠

    - **product_id**: 产品 ID
    - **wallet_type**: 钱包类型 ('credit' 或 'prepaid')
    - **quantity**: 调整数量（正数增加，负数减少）
    - **note**: 备注
    - **user_id**: 用户 ID（从认证信息获取）
    """
    if request.wallet_type not in ["credit", "prepaid"]:
        raise HTTPException(
            status_code=400, detail="钱包类型必须是 'credit' 或 'prepaid'"
        )

    service = AccountService(db)

    if request.quantity > 0:
        # 增加余额
        if request.wallet_type == "prepaid":
            # 预付充值：计算买赠优惠
            product = get_product(db, request.product_id)
            if not product:
                raise HTTPException(status_code=404, detail="产品不存在")

            # 获取优惠配置
            config = (
                db.query(PromotionConfigV2)
                .filter(
                    PromotionConfigV2.product_id == request.product_id,
                    PromotionConfigV2.mode == "prepaid",
                    PromotionConfigV2.is_active == 1,
                )
                .first()
            )

            # 计算赠送数量
            free_quantity = 0
            if config and config.trigger_qty > 0:
                # 买 N 赠 M: 每买 trigger_qty 个，就赠送 gift_qty 个
                # 例如：买 10 赠 1，充值 10 个 → 赠送 1 个；充值 20 个 → 赠送 2 个
                free_quantity = (
                    request.quantity // config.trigger_qty
                ) * config.gift_qty

            # 充值并应用优惠
            result = service.add_prepaid_balance(
                user_id=user_id,
                product_id=request.product_id,
                paid_quantity=request.quantity,
                free_quantity=free_quantity,
                unit_price=product.price,
            )

            message = f"预付充值成功：付费{result['paid_qty']}个"
            if free_quantity > 0:
                message += f"，赠送{free_quantity}个"
            message += "，共" + str(result["total_qty"]) + "个"

            return {
                "message": message,
                "wallet": {
                    "id": result["wallet_id"],
                    "product_id": request.product_id,
                    "wallet_type": "prepaid",
                    "paid_qty": result["paid_qty"],
                    "free_qty": result["free_qty"],
                    "available_qty": result["available_qty"],
                    "total_amount": result["total_amount"],
                },
            }
        else:
            # 信用授信
            result = service.add_credit_balance(
                user_id=user_id,
                product_id=request.product_id,
                quantity=request.quantity,
            )

            return {
                "message": f"信用授信成功：{result['quantity']}个",
                "wallet": {
                    "id": result["wallet_id"],
                    "product_id": request.product_id,
                    "wallet_type": "credit",
                    "quantity": result["quantity"],
                    "available_qty": result["available_qty"],
                },
            }
    else:
        # 减少余额
        try:
            result = service.adjust_wallet_balance(
                user_id=user_id,
                product_id=request.product_id,
                wallet_type=request.wallet_type,
                quantity=request.quantity,
                note=request.note,
            )

            return {
                "message": f"扣减余额成功：{abs(request.quantity)}个",
                "wallet": {
                    "id": result["wallet_id"],
                    "product_id": request.product_id,
                    "wallet_type": request.wallet_type,
                    "available_qty": result["available_qty"],
                },
            }
        except (ValueError, InsufficientBalanceError) as e:
            raise HTTPException(status_code=400, detail=str(e))


@router.post("/pickup/calculate")
def calculate_pickup(
    request: PickupCalculateRequest, db: Session = Depends(get_db)
) -> PickupCalculateResponse:
    """
    计算领取详情

    计算领取指定数量产品所需的余额和价格
    """
    service = PickupService(db)

    try:
        result = service.calculate_pickup(
            user_id=request.user_id,
            product_id=request.product_id,
            quantity=request.quantity,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/pickup/record")
def record_pickup(
    request: PickupRecordRequest, db: Session = Depends(get_db)
) -> PickupRecordResponse:
    """
    记录领取

    统一领取逻辑：自动优先使用预付余额，不足时使用信用余额
    """
    service = PickupService(db)

    try:
        result = service.record_pickup(
            user_id=request.user_id,
            product_id=request.product_id,
            quantity=request.quantity,
            note=request.note,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/user/{user_id}/balance")
def get_user_balance(
    user_id: int, product_id: Optional[int] = None, db: Session = Depends(get_db)
) -> UserBalanceResponse:
    """
    获取用户余额信息 - 清晰显示付费桶数和赠送桶数

    - **user_id**: 用户 ID
    - **product_id**: 产品 ID（可选，不传则返回所有产品）
    """
    service = PickupService(db)
    result = service.get_user_pickup_balance(user_id, product_id)

    # 【增强】返回详细的付费桶和赠送桶信息
    for product_info in result["products"]:
        balance = product_info["balance"]
        # 获取钱包详情
        prepaid_wallet = service.account_service.get_wallet(
            user_id, product_info["product_id"], "prepaid"
        )
        credit_wallet = service.account_service.get_wallet(
            user_id, product_info["product_id"], "credit"
        )

        # 【新增】详细余额信息
        product_info["balance_detail"] = {
            "prepaid": {
                "total": balance["prepaid_available"],
                "paid": prepaid_wallet.paid_qty if prepaid_wallet else 0,  # 付费桶数
                "gift": prepaid_wallet.free_qty if prepaid_wallet else 0,  # 赠送桶数
            },
            "credit": {
                "total": balance["credit_available"],
                "available": credit_wallet.available_qty if credit_wallet else 0,
                "locked": credit_wallet.locked_qty if credit_wallet else 0,
            },
        }

    return result


@router.post("/settlement/apply")
def apply_settlement(
    request: SettlementApplyRequest, db: Session = Depends(get_db)
) -> SettlementBatchResponse:
    """
    申请结算

    申请结算先用后付（信用模式）的交易记录
    """
    service = SettlementService(db)

    try:
        batch = service.apply_settlement(
            user_id=request.user_id, transaction_ids=request.transaction_ids
        )
        return batch
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/settlement/{batch_id}/confirm")
def confirm_settlement(
    batch_id: int, confirmed_by: int, db: Session = Depends(get_db)
) -> SettlementBatchResponse:
    """
    确认结算

    管理员确认结算批次

    - **batch_id**: 批次 ID
    - **confirmed_by**: 确认人 ID（管理员）
    """
    service = SettlementService(db)

    try:
        batch = service.confirm_settlement(batch_id=batch_id, confirmed_by=confirmed_by)
        return batch
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/settlement/pending")
def get_pending_settlements(
    user_id: Optional[int] = None, db: Session = Depends(get_db)
):
    """
    获取待结算列表

    - **user_id**: 用户 ID（可选，不传则返回所有用户的待结算）
    """
    service = SettlementService(db)
    batches = service.get_pending_settlements(user_id)

    return [
        {
            "id": b.id,
            "batch_no": b.batch_no,
            "user_id": b.user_id,
            "total_amount": b.total_amount,
            "status": b.status,
            "created_at": b.created_at,
            "transaction_count": len(json.loads(b.transaction_ids)),
        }
        for b in batches
    ]


@router.get("/promotion-config/{product_id}")
def get_promotion_config(product_id: int, db: Session = Depends(get_db)):
    """
    获取产品优惠配置

    - **product_id**: 产品 ID
    """
    configs = (
        db.query(PromotionConfigV2)
        .filter(
            PromotionConfigV2.product_id == product_id, PromotionConfigV2.is_active == 1
        )
        .all()
    )

    return [
        {
            "id": c.id,
            "product_id": c.product_id,
            "mode": c.mode,
            "trigger_qty": c.trigger_qty,
            "gift_qty": c.gift_qty,
            "discount_rate": c.discount_rate,
            "description": c.description,
        }
        for c in configs
    ]


@router.post("/promotion-config")
def create_promotion_config(
    config: PromotionConfigRequest, db: Session = Depends(get_db)
) -> PromotionConfigResponse:
    """
    创建/更新优惠配置

    为产品设置不同模式的优惠策略
    """
    # 检查是否已存在
    existing = (
        db.query(PromotionConfigV2)
        .filter(
            PromotionConfigV2.product_id == config.product_id,
            PromotionConfigV2.mode == config.mode,
        )
        .first()
    )

    if existing:
        # 更新
        existing.trigger_qty = config.trigger_qty
        existing.gift_qty = config.gift_qty
        existing.discount_rate = config.discount_rate
        existing.is_active = config.is_active
        existing.description = config.description
        db.commit()
        db.refresh(existing)
        return existing
    else:
        # 创建
        new_config = PromotionConfigV2(
            product_id=config.product_id,
            mode=config.mode,
            trigger_qty=config.trigger_qty,
            gift_qty=config.gift_qty,
            discount_rate=config.discount_rate,
            is_active=config.is_active,
            description=config.description,
        )
        db.add(new_config)
        db.commit()
        db.refresh(new_config)
        return new_config


@router.get("/report/financial")
def get_financial_report(
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    db: Session = Depends(get_db),
) -> FinancialReportResponse:
    """
    获取财务报表

    按业务模式分类统计：
    - 先用后付（信用）：统计已结算的交易
    - 先付后用（预付）：统计所有交易

    - **date_from**: 开始日期（YYYY-MM-DD）
    - **date_to**: 结束日期（YYYY-MM-DD）
    """
    from datetime import timedelta

    # 默认统计本月
    if not date_from:
        now = datetime.now()
        date_from = now.replace(day=1).strftime("%Y-%m-%d")
    if not date_to:
        date_to = datetime.now().strftime("%Y-%m-%d")

    try:
        from_dt = datetime.strptime(date_from, "%Y-%m-%d")
        to_dt = datetime.strptime(date_to, "%Y-%m-%d") + timedelta(days=1)
    except ValueError:
        raise HTTPException(status_code=400, detail="日期格式错误，应为 YYYY-MM-DD")

    # 先用后付统计（信用模式，已结算）
    credit_stats = (
        db.query(
            func.sum(TransactionV2.quantity).label("total_qty"),
            func.sum(TransactionV2.actual_price).label("total_amount"),
            func.count(TransactionV2.id).label("transaction_count"),
        )
        .filter(
            TransactionV2.mode == "credit",
            TransactionV2.status == "settled",
            TransactionV2.created_at >= from_dt,
            TransactionV2.created_at < to_dt,
        )
        .scalar_one_or_none()
    )

    # 先付后用统计（预付模式）
    prepaid_stats = (
        db.query(
            func.sum(TransactionV2.quantity).label("total_qty"),
            func.sum(TransactionV2.actual_price).label("total_amount"),
            func.count(TransactionV2.id).label("transaction_count"),
        )
        .filter(
            TransactionV2.mode == "prepaid",
            TransactionV2.created_at >= from_dt,
            TransactionV2.created_at < to_dt,
        )
        .scalar_one_or_none()
    )

    # 【新增】按领用类型统计
    prepaid_paid_stats = (
        db.query(
            func.sum(TransactionV2.paid_qty_deducted).label("paid_qty"),
            func.sum(TransactionV2.financial_amount).label("paid_amount"),
        )
        .filter(
            TransactionV2.mode == "prepaid",
            TransactionV2.paid_qty_deducted > 0,
            TransactionV2.created_at >= from_dt,
            TransactionV2.created_at < to_dt,
        )
        .scalar_one_or_none()
    )

    prepaid_gift_stats = (
        db.query(func.sum(TransactionV2.gift_qty_deducted).label("gift_qty"))
        .filter(
            TransactionV2.mode == "prepaid",
            TransactionV2.gift_qty_deducted > 0,
            TransactionV2.created_at >= from_dt,
            TransactionV2.created_at < to_dt,
        )
        .scalar_one_or_none()
    )

    credit_qty = credit_stats[0] if credit_stats and credit_stats[0] else 0
    credit_amount = credit_stats[1] if credit_stats and credit_stats[1] else 0.0
    credit_count = credit_stats[2] if credit_stats and credit_stats[2] else 0

    prepaid_qty = prepaid_stats[0] if prepaid_stats and prepaid_stats[0] else 0
    prepaid_amount = prepaid_stats[1] if prepaid_stats and prepaid_stats[1] else 0.0
    prepaid_count = prepaid_stats[2] if prepaid_stats and prepaid_stats[2] else 0

    return FinancialReportResponse(
        period={"date_from": date_from, "date_to": date_to},
        credit={
            "total_qty": credit_qty,
            "total_amount": credit_amount,
            "transaction_count": credit_count,
            "mode_desc": "先用后付（信用）",
        },
        prepaid={
            "total_qty": prepaid_qty,
            "total_amount": prepaid_amount,
            "transaction_count": prepaid_count,
            "mode_desc": "先付后用（预付）",
            # 【新增】明细统计
            "paid_qty": prepaid_paid_stats[0]
            if prepaid_paid_stats and prepaid_paid_stats[0]
            else 0,
            "paid_amount": prepaid_paid_stats[1]
            if prepaid_paid_stats and prepaid_paid_stats[1]
            else 0.0,
            "gift_qty": prepaid_gift_stats[0]
            if prepaid_gift_stats and prepaid_gift_stats[0]
            else 0,
            "gift_amount": 0.0,  # 赠送桶金额为 0
        },
        summary={
            "total_qty": credit_qty + prepaid_qty,
            "total_amount": credit_amount + prepaid_amount,
            "prepaid_ratio": round(
                prepaid_amount / (credit_amount + prepaid_amount) * 100, 1
            )
            if (credit_amount + prepaid_amount) > 0
            else 0,
        },
    )


@router.get("/transactions/{user_id}")
def get_user_transactions(
    user_id: int,
    mode: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    """
    获取用户交易记录

    - **user_id**: 用户 ID
    - **mode**: 模式筛选（'credit' 或 'prepaid'）
    - **status**: 状态筛选（'pending', 'applied', 'settled', 'cancelled'）
    - **limit**: 返回数量限制
    """
    query = db.query(TransactionV2).filter(TransactionV2.user_id == user_id)

    if mode:
        query = query.filter(TransactionV2.mode == mode)
    if status:
        query = query.filter(TransactionV2.status == status)

    transactions = query.order_by(TransactionV2.created_at.desc()).limit(limit).all()

    return [
        {
            "id": t.id,
            "product_id": t.product_id,
            "quantity": t.quantity,
            "unit_price": t.unit_price,
            "actual_price": t.actual_price,
            "mode": t.mode,
            "wallet_type": t.wallet_type,
            "status": t.status,
            "settlement_status": t.settlement_status,
            "paid_amount": t.paid_amount,
            "remaining_amount": t.remaining_amount,
            "discount_desc": t.discount_desc,
            "free_qty": t.free_qty,
            "settlement_batch_id": t.settlement_batch_id,
            "created_at": t.created_at,
        }
        for t in transactions
    ]


@router.get("/settlement/summary")
def get_settlement_summary(user_id: int, db: Session = Depends(get_db)):
    """
    获取用户结算汇总（待结算/已支付待确认/已结算）
    """
    pending_amount = (
        db.query(func.sum(TransactionV2.remaining_amount))
        .filter(
            TransactionV2.user_id == user_id,
            TransactionV2.mode == "credit",
            TransactionV2.status == "pending",
        )
        .scalar()
        or 0.0
    )

    applied_amount = (
        db.query(func.sum(TransactionV2.remaining_amount))
        .filter(
            TransactionV2.user_id == user_id,
            TransactionV2.mode == "credit",
            TransactionV2.status == "applied",
        )
        .scalar()
        or 0.0
    )

    settled_amount = (
        db.query(func.sum(TransactionV2.paid_amount))
        .filter(
            TransactionV2.user_id == user_id,
            TransactionV2.mode == "credit",
            TransactionV2.status == "settled",
        )
        .scalar()
        or 0.0
    )

    return {
        "user_id": user_id,
        "pending_amount": round(pending_amount, 2),
        "applied_amount": round(applied_amount, 2),
        "settled_amount": round(settled_amount, 2),
        "total_unsettled": round(pending_amount + applied_amount, 2),
    }


@router.get("/settlement/items")
def get_settlement_items(
    user_id: int,
    status: Optional[str] = None,
    limit: int = 200,
    db: Session = Depends(get_db),
):
    """
    获取用户待结算/已结算明细（信用模式）
    """
    query = db.query(TransactionV2).filter(
        TransactionV2.user_id == user_id, TransactionV2.mode == "credit"
    )
    if status:
        query = query.filter(TransactionV2.status == status)

    txns = query.order_by(TransactionV2.created_at.desc()).limit(limit).all()

    # 批次状态映射，避免前端多次请求
    batch_ids = {t.settlement_batch_id for t in txns if t.settlement_batch_id}
    batch_map = {}
    if batch_ids:
        batches = (
            db.query(SettlementBatch)
            .filter(SettlementBatch.id.in_(list(batch_ids)))
            .all()
        )
        batch_map = {
            b.id: {
                "batch_no": b.batch_no,
                "status": b.status,
                "total_amount": b.total_amount,
            }
            for b in batches
        }

    items = []
    for t in txns:
        product = get_product(db, t.product_id)
        items.append(
            {
                "id": t.id,
                "product_id": t.product_id,
                "product_name": product.name if product else "",
                "specification": product.specification if product else "",
                "unit": product.unit if product else "",
                "quantity": t.quantity,
                "unit_price": t.unit_price,
                "actual_price": t.actual_price,
                "status": t.status,
                "settlement_status": t.settlement_status,
                "paid_amount": t.paid_amount,
                "remaining_amount": t.remaining_amount,
                "settlement_batch_id": t.settlement_batch_id,
                "settlement_batch": batch_map.get(t.settlement_batch_id),
                "created_at": t.created_at,
                "note": t.note,
            }
        )

    return {"items": items, "total": len(items)}
