"""
月度结算单生成服务
负责生成和管理月度结算单
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime, date
from sqlalchemy import func, and_
from calendar import monthrange

from models.pickup import OfficePickup
from models.settlement_v2 import (
    SettlementApplication,
    MonthlySettlement,
    SettlementItem,
)
from models.office import Office
from utils.settlement_logger import SettlementLogger


class MonthlySettlementService:
    """月度结算单服务"""

    def __init__(self, db: Session):
        self.db = db
        self.logger = SettlementLogger(db)

    def generate_settlement_no(self, office_id: int, period: str) -> str:
        """生成月度结算单编号"""
        count = (
            self.db.query(func.count(MonthlySettlement.id))
            .filter(
                MonthlySettlement.office_id == office_id,
                MonthlySettlement.settlement_period == period,
            )
            .scalar()
            or 0
        )

        return f"MS{period.replace('-', '')}-{office_id:03d}-{count + 1:03d}"

    def generate_monthly_settlement(
        self,
        office_id: int,
        settlement_period: str,
        operator_id: int,
        operator_name: str,
        note: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        生成月度结算单

        Args:
            office_id: 办公室ID
            settlement_period: 结算周期 (格式: YYYY-MM)
            operator_id: 操作人ID
            operator_name: 操作人姓名
            note: 备注

        Returns:
            生成结果
        """
        try:
            year, month = map(int, settlement_period.split("-"))
            start_date = date(year, month, 1)
            end_date = date(year, month, monthrange(year, month)[1])
        except (ValueError, AttributeError):
            return {"success": False, "message": "结算周期格式错误,应为 YYYY-MM"}

        office = self.db.query(Office).filter(Office.id == office_id).first()
        if not office:
            return {"success": False, "message": "办公室不存在"}

        settlements = (
            self.db.query(SettlementApplication)
            .filter(
                SettlementApplication.office_id == office_id,
                SettlementApplication.status == "settled",
                func.date(SettlementApplication.settled_at) >= start_date,
                func.date(SettlementApplication.settled_at) <= end_date,
            )
            .all()
        )

        if not settlements:
            return {"success": False, "message": "该周期内没有已结清的记录"}

        total_amount = sum(s.total_amount for s in settlements)
        record_count = sum(s.record_count for s in settlements)

        existing = (
            self.db.query(MonthlySettlement)
            .filter(
                MonthlySettlement.office_id == office_id,
                MonthlySettlement.settlement_period == settlement_period,
                MonthlySettlement.status.in_(["pending", "approved"]),
            )
            .first()
        )

        if existing:
            return {"success": False, "message": "该周期已生成结算单"}

        settlement_no = self.generate_settlement_no(office_id, settlement_period)

        monthly_settlement = MonthlySettlement(
            settlement_no=settlement_no,
            office_id=office_id,
            office_name=office.name,
            office_room_number=office.room_number,
            settlement_period=settlement_period,
            start_date=start_date,
            end_date=end_date,
            record_count=record_count,
            total_amount=total_amount,
            status="pending",
            note=note,
            created_at=datetime.now(),
        )

        self.db.add(monthly_settlement)
        self.db.commit()

        self.logger.log_operation(
            operation_type="generate_monthly",
            target_type="monthly_settlement",
            target_id=monthly_settlement.id,
            operator_id=operator_id,
            operator_name=operator_name,
            old_status=None,
            new_status="pending",
            note=f"生成月度结算单,{settlement_period},涉及{len(settlements)}个申请单",
            operation_detail={
                "settlement_period": settlement_period,
                "settlement_count": len(settlements),
                "total_amount": total_amount,
            },
        )

        return {
            "success": True,
            "message": "月度结算单生成成功",
            "settlement_id": monthly_settlement.id,
            "settlement_no": settlement_no,
            "record_count": record_count,
            "total_amount": round(total_amount, 2),
        }

    def list_monthly_settlements(
        self,
        office_id: Optional[int] = None,
        status: Optional[str] = None,
        start_period: Optional[str] = None,
        end_period: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        """获取月度结算单列表"""
        query = self.db.query(MonthlySettlement)

        if office_id:
            query = query.filter(MonthlySettlement.office_id == office_id)

        if status:
            query = query.filter(MonthlySettlement.status == status)

        if start_period:
            query = query.filter(MonthlySettlement.settlement_period >= start_period)

        if end_period:
            query = query.filter(MonthlySettlement.settlement_period <= end_period)

        total = query.count()

        settlements = (
            query.order_by(
                MonthlySettlement.settlement_period.desc(),
                MonthlySettlement.office_id.asc(),
            )
            .limit(page_size)
            .offset((page - 1) * page_size)
            .all()
        )

        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "data": settlements,
        }

    def approve_monthly_settlement(
        self,
        settlement_id: int,
        approver_id: int,
        approver_name: str,
        note: Optional[str] = None,
    ) -> Dict[str, Any]:
        """审核月度结算单"""
        settlement = (
            self.db.query(MonthlySettlement)
            .filter(MonthlySettlement.id == settlement_id)
            .first()
        )

        if not settlement:
            return {"success": False, "message": "结算单不存在"}

        if settlement.status != "pending":
            return {"success": False, "message": "只能审核待审核的结算单"}

        old_status = settlement.status
        settlement.status = "approved"
        settlement.approved_by = approver_id
        settlement.approved_by_name = approver_name
        settlement.approved_at = datetime.now()
        if note:
            settlement.note = note

        self.db.commit()

        self.logger.log_operation(
            operation_type="approve",
            target_type="monthly_settlement",
            target_id=settlement_id,
            operator_id=approver_id,
            operator_name=approver_name,
            old_status=old_status,
            new_status="approved",
            note=f"审核通过月度结算单,{settlement.settlement_period}",
            operation_detail={
                "settlement_no": settlement.settlement_no,
                "total_amount": settlement.total_amount,
            },
        )

        return {
            "success": True,
            "message": "审核通过",
            "settlement_id": settlement_id,
            "status": "approved",
        }

    def settle_monthly_settlement(
        self,
        settlement_id: int,
        settler_id: int,
        settler_name: str,
        payment_method: Optional[str] = None,
        payment_reference: Optional[str] = None,
        note: Optional[str] = None,
    ) -> Dict[str, Any]:
        """结算月度结算单"""
        settlement = (
            self.db.query(MonthlySettlement)
            .filter(MonthlySettlement.id == settlement_id)
            .first()
        )

        if not settlement:
            return {"success": False, "message": "结算单不存在"}

        if settlement.status != "approved":
            return {"success": False, "message": "只能结算已审核的结算单"}

        old_status = settlement.status
        settlement.status = "settled"
        settlement.settled_by = settler_id
        settlement.settled_by_name = settler_name
        settlement.settled_at = datetime.now()
        settlement.payment_method = payment_method
        settlement.payment_reference = payment_reference
        if note:
            settlement.note = note

        self.db.commit()

        self.logger.log_operation(
            operation_type="settle",
            target_type="monthly_settlement",
            target_id=settlement_id,
            operator_id=settler_id,
            operator_name=settler_name,
            old_status=old_status,
            new_status="settled",
            note=f"结算月度结算单,{settlement.settlement_period},金额:¥{settlement.total_amount:.2f}",
            operation_detail={
                "settlement_no": settlement.settlement_no,
                "total_amount": settlement.total_amount,
                "payment_method": payment_method,
            },
        )

        return {
            "success": True,
            "message": "结算成功",
            "settlement_id": settlement_id,
            "status": "settled",
            "total_amount": settlement.total_amount,
        }

    def get_settlement_statistics(
        self, start_period: Optional[str] = None, end_period: Optional[str] = None
    ) -> Dict[str, Any]:
        """获取月度结算统计信息"""
        query = self.db.query(MonthlySettlement)

        if start_period:
            query = query.filter(MonthlySettlement.settlement_period >= start_period)

        if end_period:
            query = query.filter(MonthlySettlement.settlement_period <= end_period)

        total_count = query.count()

        pending_count = query.filter(MonthlySettlement.status == "pending").count()

        approved_count = query.filter(MonthlySettlement.status == "approved").count()

        settled_count = query.filter(MonthlySettlement.status == "settled").count()

        pending_amount = (
            query.filter(MonthlySettlement.status == "pending")
            .with_entities(func.sum(MonthlySettlement.total_amount))
            .scalar()
            or 0
        )

        approved_amount = (
            query.filter(MonthlySettlement.status == "approved")
            .with_entities(func.sum(MonthlySettlement.total_amount))
            .scalar()
            or 0
        )

        settled_amount = (
            query.filter(MonthlySettlement.status == "settled")
            .with_entities(func.sum(MonthlySettlement.total_amount))
            .scalar()
            or 0
        )

        return {
            "total_count": total_count,
            "pending": {"count": pending_count, "amount": round(pending_amount, 2)},
            "approved": {"count": approved_count, "amount": round(approved_amount, 2)},
            "settled": {"count": settled_count, "amount": round(settled_amount, 2)},
            "total_amount": round(pending_amount + approved_amount + settled_amount, 2),
        }

    def get_available_periods(self) -> List[str]:
        """获取可生成结算单的周期列表"""
        from sqlalchemy import distinct

        periods = (
            self.db.query(
                distinct(func.strftime("%Y-%m", SettlementApplication.settled_at))
            )
            .filter(SettlementApplication.status == "settled")
            .order_by(func.strftime("%Y-%m", SettlementApplication.settled_at).desc())
            .all()
        )

        return [p[0] for p in periods if p[0]]
