"""
结算审核服务
负责审核和管理结算申请单
"""

from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime

from models.settlement_v2 import SettlementApplication, SettlementItem
from models.pickup import OfficePickup
from utils.settlement_logger import SettlementLogger


class SettlementReviewService:
    """结算审核服务"""

    def __init__(self, db: Session):
        self.db = db
        self.logger = SettlementLogger(db)

    def approve_application(
        self,
        application_id: int,
        reviewer_id: int,
        reviewer_name: str,
        note: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        审核通过结算申请

        Args:
            application_id: 申请单ID
            reviewer_id: 审核人ID
            reviewer_name: 审核人姓名
            note: 备注

        Returns:
            审核结果
        """
        application = (
            self.db.query(SettlementApplication)
            .filter(SettlementApplication.id == application_id)
            .first()
        )

        if not application:
            return {"success": False, "message": "申请单不存在"}

        if application.status != "applied":
            return {"success": False, "message": "只能审核已申请的申请单"}

        old_status = application.status
        application.status = "approved"
        application.approved_by = reviewer_id
        application.approved_by_name = reviewer_name
        application.approved_at = datetime.now()
        if note:
            application.note = note

        self.db.commit()

        self.logger.log_operation(
            operation_type="approve",
            target_type="application",
            target_id=application_id,
            operator_id=reviewer_id,
            operator_name=reviewer_name,
            old_status=old_status,
            new_status="approved",
            note=f"审核通过,申请单号:{application.application_no}",
            operation_detail={
                "application_no": application.application_no,
                "total_amount": application.total_amount,
            },
        )

        return {
            "success": True,
            "message": "审核通过",
            "application_id": application_id,
            "status": "approved",
        }

    def reject_application(
        self, application_id: int, reviewer_id: int, reviewer_name: str, reason: str
    ) -> Dict[str, Any]:
        """
        拒绝结算申请

        Args:
            application_id: 申请单ID
            reviewer_id: 审核人ID
            reviewer_name: 审核人姓名
            reason: 拒绝原因

        Returns:
            拒绝结果
        """
        application = (
            self.db.query(SettlementApplication)
            .filter(SettlementApplication.id == application_id)
            .first()
        )

        if not application:
            return {"success": False, "message": "申请单不存在"}

        if application.status not in ["applied", "approved"]:
            return {"success": False, "message": "只能拒绝已申请或已审核的申请单"}

        old_status = application.status
        application.status = "cancelled"
        application.reject_reason = reason

        for item in application.items:
            pickup = (
                self.db.query(OfficePickup)
                .filter(OfficePickup.id == item.pickup_id)
                .first()
            )

            if pickup:
                pickup.settlement_status = "pending"
                pickup.settlement_application_id = None

        self.db.commit()

        self.logger.log_operation(
            operation_type="reject",
            target_type="application",
            target_id=application_id,
            operator_id=reviewer_id,
            operator_name=reviewer_name,
            old_status=old_status,
            new_status="cancelled",
            note=f"拒绝申请,原因:{reason}",
            operation_detail={
                "application_no": application.application_no,
                "reason": reason,
            },
        )

        return {
            "success": True,
            "message": "申请已拒绝",
            "application_id": application_id,
            "status": "cancelled",
        }

    def list_pending_applications(
        self, office_id: Optional[int] = None, page: int = 1, page_size: int = 20
    ) -> Dict[str, Any]:
        """获取待审核申请单列表"""
        query = self.db.query(SettlementApplication).filter(
            SettlementApplication.status == "applied"
        )

        if office_id:
            query = query.filter(SettlementApplication.office_id == office_id)

        total = query.count()

        applications = (
            query.order_by(SettlementApplication.applied_at.asc())
            .limit(page_size)
            .offset((page - 1) * page_size)
            .all()
        )

        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "data": applications,
        }
