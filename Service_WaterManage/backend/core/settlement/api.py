"""
结算管理API - 使用服务层
提供统一的结算管理接口
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel

from config.database import get_db
from core.settlement import SettlementService
from depends.auth import get_admin_user
from models.user import User


router = APIRouter(prefix="/api/v2/settlements", tags=["结算管理-服务层"])


# ==================== Pydantic Schemas ====================
class SettlementApplyRequest(BaseModel):
    """结算申请请求"""

    pickup_ids: List[int]


class SettlementConfirmRequest(BaseModel):
    """结算确认请求"""

    note: Optional[str] = None


class BatchConfirmRequest(BaseModel):
    """批量确认请求"""

    pickup_ids: List[int]


# ==================== API Routes ====================
@router.post("/apply")
def apply_settlement(
    request: SettlementApplyRequest,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    """
    申请结算 - 使用服务层

    将选中的领水记录状态从 pending 改为 applied
    """
    service = SettlementService(db)
    result = service.apply_settlement(
        pickup_ids=request.pickup_ids,
        applicant_id=current_user.id,
        applicant_name=current_user.name,
    )

    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])

    return result


@router.post("/{pickup_id}/confirm")
def confirm_settlement(
    pickup_id: int,
    request: SettlementConfirmRequest,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    """
    确认结算 - 使用服务层

    将领水记录状态从 applied 改为 settled
    """
    service = SettlementService(db)
    result = service.confirm_settlement(
        pickup_id=pickup_id,
        confirmer_id=current_user.id,
        confirmer_name=current_user.name,
    )

    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])

    return result


@router.post("/{pickup_id}/reject")
def reject_settlement(
    pickup_id: int,
    request: SettlementConfirmRequest,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    """
    拒绝结算 - 使用服务层

    将领水记录状态从 applied 改回 pending
    """
    service = SettlementService(db)
    result = service.reject_settlement(pickup_id=pickup_id, reason=request.note)

    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])

    return result


@router.post("/batch-confirm")
def batch_confirm_settlement(
    request: BatchConfirmRequest,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    """
    批量确认结算 - 使用服务层

    批量将领水记录状态改为 settled
    """
    service = SettlementService(db)
    result = service.batch_confirm_settlement(
        pickup_ids=request.pickup_ids,
        confirmer_id=current_user.id,
        confirmer_name=current_user.name,
    )

    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])

    return result


@router.get("/statistics")
def get_settlement_statistics(
    office_id: Optional[int] = Query(None, description="办公室ID"),
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    """
    获取结算统计信息 - 使用服务层

    返回各状态的记录数量和金额统计
    """
    service = SettlementService(db)
    statistics = service.get_settlement_statistics(office_id=office_id)

    return statistics


@router.get("/offices/{office_id}/statistics")
def get_office_settlement_statistics(
    office_id: int,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    """
    获取指定办公室的结算统计
    """
    service = SettlementService(db)
    statistics = service.get_settlement_statistics(office_id=office_id)

    return {"office_id": office_id, **statistics}
