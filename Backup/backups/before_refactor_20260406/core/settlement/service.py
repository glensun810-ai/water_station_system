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


class SettlementService(BaseService[OfficePickup]):
    """
    结算管理服务

    统一处理水站和会议室的结算业务逻辑
    """

    def __init__(self, db: Session):
        super().__init__(OfficePickup, db)

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
                pickup.settlement_status = "applied"
                updated_count += 1
                total_amount += pickup.total_amount or 0
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

        pickup.settlement_status = "settled"

        # 记录确认信息（如果模型有这些字段）
        if hasattr(pickup, "confirmed_by") and confirmer_id:
            pickup.confirmed_by = confirmer_id
        if hasattr(pickup, "confirmed_at"):
            pickup.confirmed_at = datetime.now()

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

        pickup.settlement_status = "pending"

        # 记录拒绝原因（如果需要）
        if reason and hasattr(pickup, "note"):
            pickup.note = f"拒绝原因: {reason}"

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
                pickup.settlement_status = "settled"

                if hasattr(pickup, "confirmed_by") and confirmer_id:
                    pickup.confirmed_by = confirmer_id
                if hasattr(pickup, "confirmed_at"):
                    pickup.confirmed_at = datetime.now()

                updated_count += 1
                total_amount += pickup.total_amount or 0
            else:
                failed_ids.append(pickup_id)

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
