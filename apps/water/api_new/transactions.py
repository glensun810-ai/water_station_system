"""
交易相关API
使用TransactionService处理业务逻辑
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel
from datetime import datetime

from config.database import get_db
from services import TransactionService
from api_new import require_admin, require_user, get_current_user
from models import User

router = APIRouter(prefix="/v2/transactions", tags=["Transactions (New Architecture)"])


class TransactionCreate(BaseModel):
    user_id: int
    product_id: int
    quantity: int = 1
    actual_price: Optional[float] = None
    type: str = "pickup"
    note: Optional[str] = None


class TransactionUpdate(BaseModel):
    quantity: Optional[int] = None
    actual_price: Optional[float] = None
    note: Optional[str] = None
    status: Optional[str] = None


class TransactionResponse(BaseModel):
    id: int
    user_id: int
    product_id: int
    quantity: int
    actual_price: float
    type: str
    status: str
    settlement_applied: int
    note: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class BatchSettleRequest(BaseModel):
    transaction_ids: List[int]


class BatchSettleResponse(BaseModel):
    success_count: int
    failed_count: int
    failed_details: List[dict]


@router.get("", response_model=List[TransactionResponse])
async def list_transactions(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    """
    获取交易列表
    """
    transaction_service = TransactionService(db)
    transactions = transaction_service.get_transactions(skip, limit)
    return transactions


@router.get("/unsettled", response_model=List[TransactionResponse])
async def list_unsettled(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    """
    获取未结算的交易
    """
    transaction_service = TransactionService(db)
    transactions = transaction_service.get_unsettled_transactions(skip, limit)
    return transactions


@router.get("/settled", response_model=List[TransactionResponse])
async def list_settled(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    """
    获取已结算的交易
    """
    transaction_service = TransactionService(db)
    transactions = transaction_service.get_settled_transactions(skip, limit)
    return transactions


@router.get("/status/{status}", response_model=List[TransactionResponse])
async def get_by_status(
    status: str,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    """
    根据状态获取交易
    """
    transaction_service = TransactionService(db)
    transactions = transaction_service.get_transactions_by_status(status, skip, limit)
    return transactions


@router.get("/type/{type}", response_model=List[TransactionResponse])
async def get_by_type(
    type: str,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    """
    根据类型获取交易
    """
    transaction_service = TransactionService(db)
    transactions = transaction_service.get_transactions_by_type(type, skip, limit)
    return transactions


@router.get("/user/{user_id}", response_model=List[TransactionResponse])
async def get_user_transactions(
    user_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    获取用户的交易记录
    """
    if current_user.role != "admin" and current_user.id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权限访问")

    transaction_service = TransactionService(db)
    transactions = transaction_service.get_user_transactions(user_id, skip, limit)
    return transactions


@router.get("/product/{product_id}", response_model=List[TransactionResponse])
async def get_product_transactions(
    product_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    """
    获取产品的交易记录
    """
    transaction_service = TransactionService(db)
    transactions = transaction_service.get_product_transactions(product_id, skip, limit)
    return transactions


@router.get("/{transaction_id}", response_model=TransactionResponse)
async def get_transaction(
    transaction_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    """
    获取单个交易
    """
    transaction_service = TransactionService(db)
    transaction = transaction_service.get_transaction(transaction_id)

    if not transaction:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="交易不存在")

    return transaction


@router.post(
    "", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED
)
async def create_transaction(
    transaction_data: TransactionCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_user),
):
    """
    创建交易
    """
    transaction_service = TransactionService(db)

    try:
        transaction = transaction_service.create_transaction(
            user_id=transaction_data.user_id,
            product_id=transaction_data.product_id,
            quantity=transaction_data.quantity,
            actual_price=transaction_data.actual_price,
            type=transaction_data.type,
            note=transaction_data.note,
        )
        return transaction
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put("/{transaction_id}", response_model=TransactionResponse)
async def update_transaction(
    transaction_id: int,
    transaction_data: TransactionUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    """
    更新交易信息
    """
    transaction_service = TransactionService(db)

    update_dict = transaction_data.model_dump(exclude_unset=True)
    transaction = transaction_service.update_transaction(transaction_id, update_dict)

    if not transaction:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="交易不存在")

    return transaction


@router.delete("/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_transaction(
    transaction_id: int,
    delete_reason: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user),
):
    """
    删除交易（软删除）
    """
    transaction_service = TransactionService(db)

    try:
        success = transaction_service.delete_transaction(
            transaction_id,
            deleted_by=current_user.id,
            delete_reason=delete_reason,
        )
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="交易不存在"
            )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{transaction_id}/apply-settlement")
async def apply_settlement(
    transaction_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_user),
):
    """
    申请结算
    """
    transaction_service = TransactionService(db)

    try:
        success = transaction_service.apply_settlement(transaction_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="交易不存在"
            )
        return {"message": "已申请结算"}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{transaction_id}/settle")
async def settle_transaction(
    transaction_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    """
    结算交易
    """
    transaction_service = TransactionService(db)

    try:
        success = transaction_service.settle_transaction(transaction_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="交易不存在"
            )
        return {"message": "交易已结算"}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/batch-settle", response_model=BatchSettleResponse)
async def batch_settle(
    request: BatchSettleRequest,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    """
    批量结算交易
    """
    transaction_service = TransactionService(db)

    result = transaction_service.batch_settle_transactions(request.transaction_ids)
    return result


@router.get("/user/{user_id}/total-amount")
async def get_user_total_amount(
    user_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    """
    获取用户交易总金额
    """
    transaction_service = TransactionService(db)
    total_amount = transaction_service.get_user_total_amount(user_id)
    return {"user_id": user_id, "total_amount": total_amount}


@router.get("/user/{user_id}/count")
async def get_user_transaction_count(
    user_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    """
    获取用户交易数量
    """
    transaction_service = TransactionService(db)
    count = transaction_service.get_user_transaction_count(user_id)
    return {"user_id": user_id, "transaction_count": count}
