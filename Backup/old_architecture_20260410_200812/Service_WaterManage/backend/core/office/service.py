"""
办公室管理服务
封装办公室相关的业务逻辑
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime

from models.office import Office
from models.account import OfficeAccount, AccountTransaction
from models.recharge import OfficeRecharge
from services.base import BaseService


class OfficeService(BaseService[Office]):
    """办公室管理服务"""

    def __init__(self, db: Session):
        super().__init__(Office, db)

    def get_active_offices(self) -> List[Office]:
        """获取所有活跃的办公室"""
        return (
            self.db.query(Office)
            .filter(Office.is_active == 1)
            .order_by(Office.created_at.desc())
            .all()
        )

    def get_office_by_name(self, name: str) -> Optional[Office]:
        """根据名称获取办公室"""
        return self.db.query(Office).filter(Office.name == name).first()

    def create_office(self, office_data: dict) -> Office:
        """
        创建办公室

        Args:
            office_data: 办公室数据字典

        Returns:
            创建的办公室对象
        """
        return self.create(office_data)

    def update_office(self, office_id: int, office_data: dict) -> Optional[Office]:
        """
        更新办公室信息

        Args:
            office_id: 办公室ID
            office_data: 更新数据

        Returns:
            更新后的办公室对象
        """
        return self.update(office_id, office_data)

    def delete_office(self, office_id: int, force: bool = False) -> Dict[str, Any]:
        """
        删除办公室

        Args:
            office_id: 办公室ID
            force: 是否强制删除（即使有关联数据）

        Returns:
            操作结果
        """
        office = self.get(office_id)
        if not office:
            return {"success": False, "message": "办公室不存在"}

        # 检查是否有关联数据
        accounts = (
            self.db.query(OfficeAccount)
            .filter(OfficeAccount.office_id == office_id)
            .count()
        )

        if accounts > 0 and not force:
            return {
                "success": False,
                "message": f"该办公室有 {accounts} 个关联账户，无法删除",
            }

        # 删除
        self.db.delete(office)
        self.db.commit()

        return {"success": True, "message": "办公室已删除"}


class OfficeAccountService(BaseService[OfficeAccount]):
    """办公室账户管理服务"""

    def __init__(self, db: Session):
        super().__init__(OfficeAccount, db)

    def get_accounts_by_office(self, office_id: int) -> List[OfficeAccount]:
        """获取办公室的所有账户"""
        return (
            self.db.query(OfficeAccount)
            .filter(OfficeAccount.office_id == office_id)
            .all()
        )

    def get_active_accounts(self) -> List[OfficeAccount]:
        """获取所有活跃账户"""
        return (
            self.db.query(OfficeAccount).filter(OfficeAccount.status == "active").all()
        )

    def create_account(self, account_data: dict) -> OfficeAccount:
        """创建办公室账户"""
        return self.create(account_data)

    def update_balance(
        self,
        account_id: int,
        quantity_change: int,
        transaction_type: str = "adjust",
        note: str = None,
    ) -> Optional[OfficeAccount]:
        """
        更新账户余额

        Args:
            account_id: 账户ID
            quantity_change: 数量变化（正数增加，负数减少）
            transaction_type: 交易类型
            note: 备注

        Returns:
            更新后的账户对象
        """
        account = self.get(account_id)
        if not account:
            return None

        # 更新余额
        account.remaining_qty += quantity_change
        if transaction_type == "in":
            account.total_qty += quantity_change
            account.paid_qty += quantity_change

        # 创建交易记录
        transaction = AccountTransaction(
            account_id=account_id,
            office_id=account.office_id,
            product_id=account.product_id,
            type=transaction_type,
            quantity=quantity_change,
            before_qty=account.remaining_qty - quantity_change,
            after_qty=account.remaining_qty,
            note=note,
        )

        self.db.add(transaction)
        self.db.commit()
        self.db.refresh(account)

        return account


class OfficeRechargeService(BaseService[OfficeRecharge]):
    """办公室充值管理服务"""

    def __init__(self, db: Session):
        super().__init__(OfficeRecharge, db)

    def get_recharges_by_office(
        self, office_id: int, skip: int = 0, limit: int = 100
    ) -> List[OfficeRecharge]:
        """获取办公室的充值记录"""
        return (
            self.db.query(OfficeRecharge)
            .filter(OfficeRecharge.office_id == office_id)
            .order_by(OfficeRecharge.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def create_recharge(self, recharge_data: dict) -> OfficeRecharge:
        """创建充值记录"""
        return self.create(recharge_data)

    def get_recharge_total(self, office_id: int) -> Dict[str, Any]:
        """
        获取办公室充值统计

        Args:
            office_id: 办公室ID

        Returns:
            充值统计信息
        """
        recharges = (
            self.db.query(OfficeRecharge)
            .filter(OfficeRecharge.office_id == office_id)
            .all()
        )

        total_quantity = sum(r.quantity for r in recharges)
        total_amount = sum(r.total_amount for r in recharges)

        return {
            "office_id": office_id,
            "total_recharges": len(recharges),
            "total_quantity": total_quantity,
            "total_amount": total_amount,
        }
