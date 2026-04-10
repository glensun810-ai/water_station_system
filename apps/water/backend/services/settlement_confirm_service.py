"""
结算确认服务
负责确认收款和完成结算
"""

from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from datetime import datetime
from sqlalchemy import func

from models.settlement_v2 import SettlementApplication, SettlementItem
from models.pickup import OfficePickup
from utils.settlement_logger import SettlementLogger


class SettlementConfirmService:
    """结算确认服务"""

    def __init__(self, db: Session):
        self.db = db
        self.logger = SettlementLogger(db)

    def confirm_application(
        self,
        application_id: int,
        confirmer_id: int,
        confirmer_name: str,
        payment_method: Optional[str] = None,
        payment_reference: Optional[str] = None,
        note: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        确认收款

        Args:
            application_id: 申请单ID
            confirmer_id: 确认人ID
            confirmer_name: 确认人姓名
            payment_method: 支付方式
            payment_reference: 支付凭证
            note: 备注

        Returns:
            确认结果
        """
        application = (
            self.db.query(SettlementApplication)
            .filter(SettlementApplication.id == application_id)
            .first()
        )

        if not application:
            return {"success": False, "message": "申请单不存在"}

        if application.status not in ["applied", "approved", "confirmed"]:
            return {"success": False, "message": "只能确认已申请或已审核的申请单"}

        old_status = application.status
        application.status = "settled"
        application.confirmed_by = confirmer_id
        application.confirmed_by_name = confirmer_name
        application.confirmed_at = datetime.now()
        application.settled_by = confirmer_id
        application.settled_by_name = confirmer_name
        application.settled_at = datetime.now()
        application.payment_method = payment_method
        application.payment_reference = payment_reference
        if note:
            application.note = note

        for item in application.items:
            pickup = (
                self.db.query(OfficePickup)
                .filter(OfficePickup.id == item.pickup_id)
                .first()
            )

            if pickup:
                pickup.settlement_status = "settled"
                item.pickup_status = "settled"

        self.db.commit()

        self.logger.log_operation(
            operation_type="confirm",
            target_type="application",
            target_id=application_id,
            operator_id=confirmer_id,
            operator_name=confirmer_name,
            old_status=old_status,
            new_status="settled",
            note=f"确认收款,申请单号:{application.application_no},金额:¥{application.total_amount:.2f}",
            operation_detail={
                "application_no": application.application_no,
                "total_amount": application.total_amount,
                "payment_method": payment_method,
            },
        )

        return {
            "success": True,
            "message": "确认收款成功",
            "application_id": application_id,
            "status": "settled",
            "total_amount": application.total_amount,
        }

    def batch_confirm_applications(
        self,
        application_ids: List[int],
        confirmer_id: int,
        confirmer_name: str,
        payment_method: Optional[str] = None,
        note: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        批量确认收款

        Args:
            application_ids: 申请单ID列表
            confirmer_id: 确认人ID
            confirmer_name: 确认人姓名
            payment_method: 支付方式
            note: 备注

        Returns:
            批量确认结果
        """
        if not application_ids:
            return {"success": False, "message": "请选择要确认的申请单"}

        success_count = 0
        failed_count = 0
        total_amount = 0.0
        failed_ids = []

        for application_id in application_ids:
            result = self.confirm_application(
                application_id=application_id,
                confirmer_id=confirmer_id,
                confirmer_name=confirmer_name,
                payment_method=payment_method,
                note=note,
            )

            if result["success"]:
                success_count += 1
                total_amount += result.get("total_amount", 0)
            else:
                failed_count += 1
                failed_ids.append(application_id)

        if success_count > 0:
            self.logger.log_batch_operation(
                operation_type="batch_confirm",
                target_type="application",
                target_ids=[aid for aid in application_ids if aid not in failed_ids],
                operator_id=confirmer_id,
                operator_name=confirmer_name,
                note=f"批量确认收款,{success_count}个申请单,总金额¥{total_amount:.2f}",
                operation_detail={
                    "success_count": success_count,
                    "failed_count": failed_count,
                    "total_amount": total_amount,
                },
            )

        return {
            "success": True,
            "message": f"批量确认完成,成功{success_count}个,失败{failed_count}个",
            "success_count": success_count,
            "failed_count": failed_count,
            "failed_ids": failed_ids,
            "total_amount": round(total_amount, 2),
        }

    def get_pending_confirmations(
        self, office_id: Optional[int] = None, page: int = 1, page_size: int = 20
    ) -> Dict[str, Any]:
        """获取待确认申请单列表"""
        query = self.db.query(SettlementApplication).filter(
            SettlementApplication.status.in_(["applied", "approved", "confirmed"])
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

        total_amount = sum(app.total_amount for app in applications)

        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_amount": round(total_amount, 2),
            "data": applications,
        }

    def get_settlement_statistics(
        self,
        office_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """获取结算统计信息"""
        query = self.db.query(SettlementApplication)

        if office_id:
            query = query.filter(SettlementApplication.office_id == office_id)

        if start_date:
            query = query.filter(SettlementApplication.applied_at >= start_date)

        if end_date:
            query = query.filter(SettlementApplication.applied_at <= end_date)

        total_count = query.count()

        applied_count = query.filter(SettlementApplication.status == "applied").count()

        approved_count = query.filter(
            SettlementApplication.status == "approved"
        ).count()

        settled_count = query.filter(SettlementApplication.status == "settled").count()

        applied_amount = (
            query.filter(SettlementApplication.status == "applied")
            .with_entities(func.sum(SettlementApplication.total_amount))
            .scalar()
            or 0
        )

        approved_amount = (
            query.filter(SettlementApplication.status == "approved")
            .with_entities(func.sum(SettlementApplication.total_amount))
            .scalar()
            or 0
        )

        settled_amount = (
            query.filter(SettlementApplication.status == "settled")
            .with_entities(func.sum(SettlementApplication.total_amount))
            .scalar()
            or 0
        )

        return {
            "total_count": total_count,
            "applied": {"count": applied_count, "amount": round(applied_amount, 2)},
            "approved": {"count": approved_count, "amount": round(approved_amount, 2)},
            "settled": {"count": settled_count, "amount": round(settled_amount, 2)},
            "total_amount": round(applied_amount + approved_amount + settled_amount, 2),
        }
