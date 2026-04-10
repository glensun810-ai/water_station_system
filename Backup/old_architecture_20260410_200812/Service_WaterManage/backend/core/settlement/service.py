"""
结算管理服务
封装水站和会议室的统一结算逻辑
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime
import json

from models.pickup import OfficePickup
from models.settlement import OfficeSettlement
from services.base import BaseService
from utils.settlement_logger import SettlementLogger


class SettlementService(BaseService[OfficePickup]):
    """
    结算管理服务

    统一处理水站和会议室的结算业务逻辑
    """

    def __init__(self, db: Session):
        super().__init__(OfficePickup, db)
        self.logger = SettlementLogger(db)

    def apply_settlement(
        self,
        pickup_ids: List[int],
        applicant_id: Optional[int] = None,
        applicant_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        申请结算

        Args:
            pickup_ids: 领水记录ID列表
            applicant_id: 申请人ID
            applicant_name: 申请人姓名

        Returns:
            结算申请结果
        """
        if not pickup_ids:
            return {
                "success": False,
                "message": "请选择要结算的记录",
                "updated_count": 0,
                "total_amount": 0,
            }

        updated_count = 0
        total_amount = 0.0
        failed_ids = []
        successful_ids = []

        for pickup_id in pickup_ids:
            pickup = (
                self.db.query(OfficePickup)
                .filter(
                    OfficePickup.id == pickup_id,
                    OfficePickup.settlement_status == "pending",
                    OfficePickup.is_deleted == 0,
                )
                .first()
            )

            if pickup:
                old_status = pickup.settlement_status
                pickup.settlement_status = "applied"
                updated_count += 1
                total_amount += pickup.total_amount or 0
                successful_ids.append(pickup_id)

                self.logger.log_operation(
                    operation_type="apply",
                    target_type="pickup",
                    target_id=pickup_id,
                    operator_id=applicant_id or 0,
                    operator_name=applicant_name or "系统",
                    old_status=old_status,
                    new_status="applied",
                    note=f"申请结算,金额: ¥{pickup.total_amount or 0:.2f}",
                    operation_detail={"amount": pickup.total_amount or 0},
                )
            else:
                failed_ids.append(pickup_id)

        self.db.commit()

        return {
            "success": True,
            "message": "结算申请提交成功",
            "updated_count": updated_count,
            "total_amount": round(total_amount, 2),
            "failed_count": len(failed_ids),
            "failed_ids": failed_ids,
        }

    def confirm_settlement(
        self,
        pickup_id: int,
        confirmer_id: Optional[int] = None,
        confirmer_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        确认结算

        Args:
            pickup_id: 领水记录ID
            confirmer_id: 确认人ID
            confirmer_name: 确认人姓名

        Returns:
            确认结果
        """
        pickup = self.get(pickup_id)

        if not pickup:
            return {"success": False, "message": "领水记录不存在"}

        if pickup.settlement_status not in ["pending", "applied"]:
            return {"success": False, "message": "该记录不可确认结算"}

        old_status = pickup.settlement_status
        pickup.settlement_status = "settled"

        if hasattr(pickup, "confirmed_by") and confirmer_id:
            pickup.confirmed_by = confirmer_id
        if hasattr(pickup, "confirmed_at"):
            pickup.confirmed_at = datetime.now()

        self.logger.log_operation(
            operation_type="confirm",
            target_type="pickup",
            target_id=pickup_id,
            operator_id=confirmer_id or 0,
            operator_name=confirmer_name or "管理员",
            old_status=old_status,
            new_status="settled",
            note=f"确认收款,金额: ¥{pickup.total_amount or 0:.2f}",
            operation_detail={"amount": pickup.total_amount or 0},
        )

        self.db.commit()

        return {"success": True, "message": "结算确认成功", "pickup_id": pickup_id}

    def reject_settlement(
        self, pickup_id: int, reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        拒绝结算

        Args:
            pickup_id: 领水记录ID
            reason: 拒绝原因

        Returns:
            拒绝结果
        """
        pickup = self.get(pickup_id)

        if not pickup:
            return {"success": False, "message": "领水记录不存在"}

        if pickup.settlement_status != "applied":
            return {"success": False, "message": "只能拒绝已申请的结算"}

        old_status = pickup.settlement_status
        pickup.settlement_status = "pending"

        if reason and hasattr(pickup, "note"):
            pickup.note = f"拒绝原因: {reason}"

        self.logger.log_operation(
            operation_type="reject",
            target_type="pickup",
            target_id=pickup_id,
            operator_id=0,
            operator_name="系统",
            old_status=old_status,
            new_status="pending",
            note=f"拒绝结算: {reason}",
        )

        self.db.commit()

        return {"success": True, "message": "结算已拒绝", "pickup_id": pickup_id}

    def batch_confirm_settlement(
        self,
        pickup_ids: List[int],
        confirmer_id: Optional[int] = None,
        confirmer_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        批量确认结算

        Args:
            pickup_ids: 领水记录ID列表
            confirmer_id: 确认人ID
            confirmer_name: 确认人姓名

        Returns:
            批量确认结果
        """
        if not pickup_ids:
            return {
                "success": False,
                "message": "请选择要确认的记录",
                "updated_count": 0,
                "total_amount": 0,
            }

        updated_count = 0
        total_amount = 0.0
        failed_ids = []
        successful_ids = []

        for pickup_id in pickup_ids:
            pickup = (
                self.db.query(OfficePickup)
                .filter(
                    OfficePickup.id == pickup_id,
                    OfficePickup.settlement_status.in_(["pending", "applied"]),
                )
                .first()
            )

            if pickup:
                old_status = pickup.settlement_status
                pickup.settlement_status = "settled"

                if hasattr(pickup, "confirmed_by") and confirmer_id:
                    pickup.confirmed_by = confirmer_id
                if hasattr(pickup, "confirmed_at"):
                    pickup.confirmed_at = datetime.now()

                updated_count += 1
                total_amount += pickup.total_amount or 0
                successful_ids.append(pickup_id)
            else:
                failed_ids.append(pickup_id)

        if successful_ids:
            self.logger.log_batch_operation(
                operation_type="batch_confirm",
                target_type="pickup",
                target_ids=successful_ids,
                operator_id=confirmer_id or 0,
                operator_name=confirmer_name or "管理员",
                note=f"批量确认收款,涉及{len(successful_ids)}条记录,总金额¥{round(total_amount, 2)}",
                operation_detail={
                    "count": len(successful_ids),
                    "total_amount": round(total_amount, 2),
                },
            )

        self.db.commit()

        return {
            "success": True,
            "message": "批量确认结算成功",
            "updated_count": updated_count,
            "total_amount": round(total_amount, 2),
            "failed_count": len(failed_ids),
            "failed_ids": failed_ids,
        }

    def get_settlement_statistics(
        self,
        office_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        获取结算统计信息

        Args:
            office_id: 办公室ID（可选）
            start_date: 开始日期（可选）
            end_date: 结束日期（可选）

        Returns:
            统计信息
        """
        query = self.db.query(OfficePickup).filter(OfficePickup.is_deleted == 0)

        if office_id:
            query = query.filter(OfficePickup.office_id == office_id)

        if start_date:
            query = query.filter(OfficePickup.pickup_time >= start_date)

        if end_date:
            query = query.filter(OfficePickup.pickup_time <= end_date)

        # 统计各状态的记录
        pending_count = query.filter(
            OfficePickup.settlement_status == "pending"
        ).count()

        applied_count = query.filter(
            OfficePickup.settlement_status == "applied"
        ).count()

        settled_count = query.filter(
            OfficePickup.settlement_status == "settled"
        ).count()

        # 统计金额
        pending_amount = (
            query.filter(OfficePickup.settlement_status == "pending")
            .with_entities(func.sum(OfficePickup.total_amount))
            .scalar()
            or 0
        )

        applied_amount = (
            query.filter(OfficePickup.settlement_status == "applied")
            .with_entities(func.sum(OfficePickup.total_amount))
            .scalar()
            or 0
        )

        settled_amount = (
            query.filter(OfficePickup.settlement_status == "settled")
            .with_entities(func.sum(OfficePickup.total_amount))
            .scalar()
            or 0
        )

        return {
            "pending": {"count": pending_count, "amount": round(pending_amount, 2)},
            "applied": {"count": applied_count, "amount": round(applied_amount, 2)},
            "settled": {"count": settled_count, "amount": round(settled_amount, 2)},
            "total_count": pending_count + applied_count + settled_count,
            "total_amount": round(pending_amount + applied_amount + settled_amount, 2),
        }
