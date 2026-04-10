"""
结算申请服务
负责创建和管理结算申请单
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime
from sqlalchemy import func

from models.pickup import OfficePickup
from models.settlement_v2 import SettlementApplication, SettlementItem
from utils.settlement_logger import SettlementLogger


class SettlementApplyService:
    """结算申请服务"""

    def __init__(self, db: Session):
        self.db = db
        self.logger = SettlementLogger(db)

    def generate_application_no(self, office_id: int) -> str:
        """生成申请单编号"""
        count = (
            self.db.query(func.count(SettlementApplication.id))
            .filter(SettlementApplication.office_id == office_id)
            .scalar()
            or 0
        )

        return f"SA{datetime.now().strftime('%Y%m%d')}-{office_id:03d}-{count + 1:03d}"

    def create_application(
        self,
        office_id: int,
        pickup_ids: List[int],
        applicant_id: int,
        applicant_name: str,
        note: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        创建结算申请单

        Args:
            office_id: 办公室ID
            pickup_ids: 领水记录ID列表
            applicant_id: 申请人ID
            applicant_name: 申请人姓名
            note: 备注

        Returns:
            申请结果
        """
        if not pickup_ids:
            return {"success": False, "message": "请选择要结算的记录"}

        pickups = (
            self.db.query(OfficePickup)
            .filter(
                OfficePickup.id.in_(pickup_ids),
                OfficePickup.office_id == office_id,
                OfficePickup.settlement_status == "pending",
                OfficePickup.is_deleted == 0,
            )
            .all()
        )

        if not pickups:
            return {"success": False, "message": "没有可用的记录"}

        if len(pickups) != len(pickup_ids):
            return {"success": False, "message": "部分记录不可用"}

        application_no = self.generate_application_no(office_id)
        total_amount = sum(p.total_amount or 0 for p in pickups)

        application = SettlementApplication(
            application_no=application_no,
            office_id=office_id,
            office_name=pickups[0].office_name,
            office_room_number=pickups[0].office_room_number,
            applicant_id=applicant_id,
            applicant_name=applicant_name,
            applicant_role="office_manager",
            record_count=len(pickups),
            total_amount=total_amount,
            status="applied",
            applied_at=datetime.now(),
            note=note,
        )

        self.db.add(application)
        self.db.flush()

        for pickup in pickups:
            pickup.settlement_status = "applied"
            pickup.settlement_application_id = application.id

            item = SettlementItem(
                application_id=application.id,
                pickup_id=pickup.id,
                product_name=pickup.product_name,
                product_id=pickup.product_id,
                quantity=pickup.quantity,
                unit_price=pickup.unit_price,
                amount=pickup.total_amount,
                pickup_status="applied",
                pickup_time=pickup.pickup_time,
                pickup_person=pickup.pickup_person,
                pickup_person_id=pickup.pickup_person_id,
            )

            self.db.add(item)

        self.db.commit()

        self.logger.log_operation(
            operation_type="apply",
            target_type="application",
            target_id=application.id,
            operator_id=applicant_id,
            operator_name=applicant_name,
            old_status=None,
            new_status="applied",
            note=f"创建结算申请单,{len(pickups)}条记录,总金额¥{total_amount:.2f}",
            operation_detail={
                "pickup_ids": pickup_ids,
                "record_count": len(pickups),
                "total_amount": total_amount,
            },
        )

        return {
            "success": True,
            "message": "结算申请单创建成功",
            "application_id": application.id,
            "application_no": application_no,
            "record_count": len(pickups),
            "total_amount": round(total_amount, 2),
        }

    def get_application(self, application_id: int) -> Optional[SettlementApplication]:
        """获取申请单详情"""
        return (
            self.db.query(SettlementApplication)
            .filter(SettlementApplication.id == application_id)
            .first()
        )

    def list_applications(
        self,
        office_id: Optional[int] = None,
        status: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        """获取申请单列表"""
        query = self.db.query(SettlementApplication)

        if office_id:
            query = query.filter(SettlementApplication.office_id == office_id)

        if status:
            query = query.filter(SettlementApplication.status == status)

        if start_date:
            query = query.filter(SettlementApplication.applied_at >= start_date)

        if end_date:
            query = query.filter(SettlementApplication.applied_at <= end_date)

        total = query.count()

        applications = (
            query.order_by(SettlementApplication.applied_at.desc())
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

    def get_application_pickups(self, application_id: int) -> List[OfficePickup]:
        """获取申请单关联的领水记录"""
        application = self.get_application(application_id)
        if not application:
            return []

        pickup_ids = [item.pickup_id for item in application.items]

        return self.db.query(OfficePickup).filter(OfficePickup.id.in_(pickup_ids)).all()
