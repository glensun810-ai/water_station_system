"""
结算管理API v3 - 使用新结算单模型
提供完整的结算申请、审核、确认流程
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel

from config.database import get_db
from services.settlement_apply_service import SettlementApplyService
from services.settlement_review_service import SettlementReviewService
from services.settlement_confirm_service import SettlementConfirmService
from services.monthly_settlement_service import MonthlySettlementService
from depends.auth import get_admin_user
from models.user import User


router = APIRouter(prefix="/api/v3/settlements", tags=["结算管理-v3"])


# ==================== Pydantic Schemas ====================
class CreateApplicationRequest(BaseModel):
    """创建结算申请请求"""

    office_id: int
    pickup_ids: List[int]
    note: Optional[str] = None


class ApproveApplicationRequest(BaseModel):
    """审核通过请求"""

    note: Optional[str] = None


class RejectApplicationRequest(BaseModel):
    """拒绝申请请求"""

    reason: str


class ConfirmApplicationRequest(BaseModel):
    """确认收款请求"""

    payment_method: Optional[str] = None
    payment_reference: Optional[str] = None
    note: Optional[str] = None


class BatchConfirmRequest(BaseModel):
    """批量确认请求"""

    application_ids: List[int]
    payment_method: Optional[str] = None
    note: Optional[str] = None


class GenerateMonthlyRequest(BaseModel):
    """生成月度结算单请求"""

    office_id: int
    settlement_period: str
    note: Optional[str] = None


class ApproveMonthlyRequest(BaseModel):
    """审核月度结算单请求"""

    note: Optional[str] = None


class SettleMonthlyRequest(BaseModel):
    """结算月度结算单请求"""

    payment_method: Optional[str] = None
    payment_reference: Optional[str] = None
    note: Optional[str] = None


# ==================== API Routes ====================


@router.post("/applications")
def create_application(
    request: CreateApplicationRequest,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    """
    创建结算申请单

    将选中的领水记录创建为结算申请单
    """
    service = SettlementApplyService(db)
    result = service.create_application(
        office_id=request.office_id,
        pickup_ids=request.pickup_ids,
        applicant_id=current_user.id,
        applicant_name=current_user.name,
        note=request.note,
    )

    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])

    return result


@router.get("/applications")
def list_applications(
    office_id: Optional[int] = Query(None, description="办公室ID"),
    status: Optional[str] = Query(None, description="状态筛选"),
    page: int = Query(1, description="页码"),
    page_size: int = Query(20, description="每页数量"),
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    """获取结算申请单列表"""
    service = SettlementApplyService(db)
    result = service.list_applications(
        office_id=office_id, status=status, page=page, page_size=page_size
    )

    return result


@router.get("/applications/{application_id}")
def get_application(
    application_id: int,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    """获取结算申请单详情"""
    service = SettlementApplyService(db)
    application = service.get_application(application_id)

    if not application:
        raise HTTPException(status_code=404, detail="申请单不存在")

    pickups = service.get_application_pickups(application_id)

    return {"application": application, "pickups": pickups}


@router.post("/applications/{application_id}/approve")
def approve_application(
    application_id: int,
    request: ApproveApplicationRequest,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    """审核通过结算申请"""
    service = SettlementReviewService(db)
    result = service.approve_application(
        application_id=application_id,
        reviewer_id=current_user.id,
        reviewer_name=current_user.name,
        note=request.note,
    )

    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])

    return result


@router.post("/applications/{application_id}/reject")
def reject_application(
    application_id: int,
    request: RejectApplicationRequest,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    """拒绝结算申请"""
    service = SettlementReviewService(db)
    result = service.reject_application(
        application_id=application_id,
        reviewer_id=current_user.id,
        reviewer_name=current_user.name,
        reason=request.reason,
    )

    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])

    return result


@router.post("/applications/{application_id}/confirm")
def confirm_application(
    application_id: int,
    request: ConfirmApplicationRequest,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    """确认收款"""
    service = SettlementConfirmService(db)
    result = service.confirm_application(
        application_id=application_id,
        confirmer_id=current_user.id,
        confirmer_name=current_user.name,
        payment_method=request.payment_method,
        payment_reference=request.payment_reference,
        note=request.note,
    )

    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])

    return result


@router.post("/batch-confirm")
def batch_confirm_applications(
    request: BatchConfirmRequest,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    """批量确认收款"""
    service = SettlementConfirmService(db)
    result = service.batch_confirm_applications(
        application_ids=request.application_ids,
        confirmer_id=current_user.id,
        confirmer_name=current_user.name,
        payment_method=request.payment_method,
        note=request.note,
    )

    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])

    return result


@router.get("/pending-review")
def get_pending_reviews(
    office_id: Optional[int] = Query(None, description="办公室ID"),
    page: int = Query(1, description="页码"),
    page_size: int = Query(20, description="每页数量"),
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    """获取待审核申请单列表"""
    service = SettlementReviewService(db)
    result = service.list_pending_applications(
        office_id=office_id, page=page, page_size=page_size
    )

    return result


@router.get("/pending-confirmation")
def get_pending_confirmations(
    office_id: Optional[int] = Query(None, description="办公室ID"),
    page: int = Query(1, description="页码"),
    page_size: int = Query(20, description="每页数量"),
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    """获取待确认申请单列表"""
    service = SettlementConfirmService(db)
    result = service.get_pending_confirmations(
        office_id=office_id, page=page, page_size=page_size
    )

    return result


@router.get("/statistics")
def get_statistics(
    office_id: Optional[int] = Query(None, description="办公室ID"),
    start_date: Optional[str] = Query(None, description="开始日期 YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="结束日期 YYYY-MM-DD"),
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    """获取结算统计信息"""
    service = SettlementConfirmService(db)

    start_dt = None
    end_dt = None

    if start_date:
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
    if end_date:
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")

    result = service.get_settlement_statistics(
        office_id=office_id, start_date=start_dt, end_date=end_dt
    )

    return result


# ==================== 月度结算单API ====================


@router.post("/monthly-settlements")
def generate_monthly_settlement(
    request: GenerateMonthlyRequest,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    """生成月度结算单"""
    service = MonthlySettlementService(db)
    result = service.generate_monthly_settlement(
        office_id=request.office_id,
        settlement_period=request.settlement_period,
        operator_id=current_user.id,
        operator_name=current_user.name,
        note=request.note,
    )

    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])

    return result


@router.get("/monthly-settlements")
def list_monthly_settlements(
    office_id: Optional[int] = Query(None, description="办公室ID"),
    status: Optional[str] = Query(None, description="状态筛选"),
    start_period: Optional[str] = Query(None, description="开始周期 YYYY-MM"),
    end_period: Optional[str] = Query(None, description="结束周期 YYYY-MM"),
    page: int = Query(1, description="页码"),
    page_size: int = Query(20, description="每页数量"),
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    """获取月度结算单列表"""
    service = MonthlySettlementService(db)
    result = service.list_monthly_settlements(
        office_id=office_id,
        status=status,
        start_period=start_period,
        end_period=end_period,
        page=page,
        page_size=page_size,
    )

    return result


@router.get("/monthly-settlements/available-periods")
def get_available_periods(
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    """获取可生成结算单的周期列表"""
    service = MonthlySettlementService(db)
    periods = service.get_available_periods()

    return {"periods": periods}


@router.get("/monthly-settlements/{settlement_id}")
def get_monthly_settlement(
    settlement_id: int,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    """获取月度结算单详情"""
    from models.settlement_v2 import MonthlySettlement

    settlement = (
        db.query(MonthlySettlement)
        .filter(MonthlySettlement.id == settlement_id)
        .first()
    )

    if not settlement:
        raise HTTPException(status_code=404, detail="结算单不存在")

    return settlement


@router.post("/monthly-settlements/{settlement_id}/approve")
def approve_monthly_settlement(
    settlement_id: int,
    request: ApproveMonthlyRequest,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    """审核月度结算单"""
    service = MonthlySettlementService(db)
    result = service.approve_monthly_settlement(
        settlement_id=settlement_id,
        approver_id=current_user.id,
        approver_name=current_user.name,
        note=request.note,
    )

    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])

    return result


@router.post("/monthly-settlements/{settlement_id}/settle")
def settle_monthly_settlement(
    settlement_id: int,
    request: SettleMonthlyRequest,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    """结算月度结算单"""
    service = MonthlySettlementService(db)
    result = service.settle_monthly_settlement(
        settlement_id=settlement_id,
        settler_id=current_user.id,
        settler_name=current_user.name,
        payment_method=request.payment_method,
        payment_reference=request.payment_reference,
        note=request.note,
    )

    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])

    return result


@router.get("/monthly-settlements/statistics")
def get_monthly_statistics(
    start_period: Optional[str] = Query(None, description="开始周期 YYYY-MM"),
    end_period: Optional[str] = Query(None, description="结束周期 YYYY-MM"),
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    """获取月度结算统计信息"""
    service = MonthlySettlementService(db)
    result = service.get_settlement_statistics(
        start_period=start_period, end_period=end_period
    )

    return result
