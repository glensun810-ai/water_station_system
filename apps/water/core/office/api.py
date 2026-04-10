"""
办公室管理API - 使用服务层
演示如何使用服务层封装业务逻辑
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from config.database import get_db
from core.office import OfficeService, OfficeAccountService, OfficeRechargeService
from models.office import Office
from models.account import OfficeAccount
from pydantic import BaseModel
from datetime import datetime
from typing import Optional


router = APIRouter(prefix="/api/v2/offices", tags=["办公室管理-服务层示例"])


# ==================== Pydantic Schemas ====================
class OfficeCreate(BaseModel):
    name: str
    room_number: Optional[str] = None
    description: Optional[str] = None
    leader_name: Optional[str] = None
    water_user_count: int = 0
    is_common: int = 1


class OfficeResponse(BaseModel):
    id: int
    name: str
    room_number: Optional[str] = None
    description: Optional[str] = None
    leader_name: Optional[str] = None
    water_user_count: int = 0
    is_common: int = 1
    is_active: int = 1
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ==================== API Routes ====================
@router.get("", response_model=List[OfficeResponse])
def get_offices(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    获取办公室列表 - 使用服务层

    演示如何使用OfficeService
    """
    service = OfficeService(db)
    offices = service.get_multi(skip=skip, limit=limit, is_active=1)
    return offices


@router.get("/{office_id}", response_model=OfficeResponse)
def get_office(office_id: int, db: Session = Depends(get_db)):
    """
    获取办公室详情 - 使用服务层
    """
    service = OfficeService(db)
    office = service.get(office_id)

    if not office:
        raise HTTPException(status_code=404, detail="办公室不存在")

    return office


@router.post("", response_model=OfficeResponse)
def create_office(office: OfficeCreate, db: Session = Depends(get_db)):
    """
    创建办公室 - 使用服务层

    演示服务层封装创建逻辑
    """
    service = OfficeService(db)

    # 检查名称是否已存在
    existing = service.get_office_by_name(office.name)
    if existing:
        raise HTTPException(status_code=400, detail="办公室名称已存在")

    # 使用服务层创建
    new_office = service.create_office(office.model_dump())
    return new_office


@router.get("/{office_id}/accounts")
def get_office_accounts(office_id: int, db: Session = Depends(get_db)):
    """
    获取办公室账户列表 - 使用服务层

    演示如何使用OfficeAccountService
    """
    office_service = OfficeService(db)
    office = office_service.get(office_id)

    if not office:
        raise HTTPException(status_code=404, detail="办公室不存在")

    account_service = OfficeAccountService(db)
    accounts = account_service.get_accounts_by_office(office_id)

    return {
        "office_id": office_id,
        "office_name": office.name,
        "accounts": [
            {
                "id": acc.id,
                "product_id": acc.product_id,
                "product_name": acc.product_name,
                "remaining_qty": acc.remaining_qty,
                "total_qty": acc.total_qty,
            }
            for acc in accounts
        ],
    }


@router.get("/{office_id}/recharge-summary")
def get_office_recharge_summary(office_id: int, db: Session = Depends(get_db)):
    """
    获取办公室充值统计 - 使用服务层

    演示业务逻辑封装在服务层
    """
    office_service = OfficeService(db)
    office = office_service.get(office_id)

    if not office:
        raise HTTPException(status_code=404, detail="办公室不存在")

    recharge_service = OfficeRechargeService(db)
    summary = recharge_service.get_recharge_total(office_id)

    return {"office_id": office_id, "office_name": office.name, **summary}
