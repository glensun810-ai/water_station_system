"""
账户仓库
处理账户相关的数据访问
"""

from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import datetime

from repositories.base import BaseRepository
from models.account import OfficeAccount, AccountTransaction


class OfficeAccountRepository(BaseRepository[OfficeAccount]):
    """办公室账户仓库"""

    def __init__(self, db: Session):
        super().__init__(OfficeAccount, db)

    def get_by_office(self, office_id: int) -> List[OfficeAccount]:
        """
        根据办公室ID获取账户列表

        Args:
            office_id: 办公室ID

        Returns:
            账户列表
        """
        return (
            self.db.query(OfficeAccount)
            .filter(OfficeAccount.office_id == office_id)
            .all()
        )

    def get_by_office_and_product(
        self, office_id: int, product_id: int
    ) -> Optional[OfficeAccount]:
        """
        根据办公室和产品获取账户

        Args:
            office_id: 办公室ID
            product_id: 产品ID

        Returns:
            账户实例或None
        """
        return (
            self.db.query(OfficeAccount)
            .filter(OfficeAccount.office_id == office_id)
            .filter(OfficeAccount.product_id == product_id)
            .first()
        )

    def get_active_accounts(self) -> List[OfficeAccount]:
        """
        获取所有活跃账户

        Returns:
            账户列表
        """
        return (
            self.db.query(OfficeAccount).filter(OfficeAccount.status == "active").all()
        )

    def get_low_stock_accounts(self) -> List[OfficeAccount]:
        """
        获取低库存账户

        Returns:
            低库存账户列表
        """
        accounts = (
            self.db.query(OfficeAccount).filter(OfficeAccount.status == "active").all()
        )

        low_stock_accounts = []
        for account in accounts:
            if account.remaining_qty <= account.low_stock_threshold:
                low_stock_accounts.append(account)

        return low_stock_accounts

    def update_quantities(
        self,
        account_id: int,
        total_qty: int = None,
        paid_qty: int = None,
        free_qty: int = None,
        remaining_qty: int = None,
        reserved_qty: int = None,
    ) -> Optional[OfficeAccount]:
        """
        更新账户数量

        Args:
            account_id: 账户ID
            total_qty: 总数量
            paid_qty: 付费数量
            free_qty: 免费数量
            remaining_qty: 剩余数量
            reserved_qty: 预留数量

        Returns:
            更新后的账户实例
        """
        account = self.get(account_id)
        if not account:
            return None

        update_data = {"updated_at": datetime.now()}
        if total_qty is not None:
            update_data["total_qty"] = total_qty
        if paid_qty is not None:
            update_data["paid_qty"] = paid_qty
        if free_qty is not None:
            update_data["free_qty"] = free_qty
        if remaining_qty is not None:
            update_data["remaining_qty"] = remaining_qty
        if reserved_qty is not None:
            update_data["reserved_qty"] = reserved_qty

        return self.update(account_id, update_data)

    def freeze(self, account_id: int) -> bool:
        """
        冻结账户

        Args:
            account_id: 账户ID

        Returns:
            是否冻结成功
        """
        account = self.get(account_id)
        if not account:
            return False

        return (
            self.update(account_id, {"status": "frozen", "updated_at": datetime.now()})
            is not None
        )

    def unfreeze(self, account_id: int) -> bool:
        """
        解冻账户

        Args:
            account_id: 账户ID

        Returns:
            是否解冻成功
        """
        account = self.get(account_id)
        if not account:
            return False

        return (
            self.update(account_id, {"status": "active", "updated_at": datetime.now()})
            is not None
        )


class AccountTransactionRepository(BaseRepository[AccountTransaction]):
    """账户交易流水仓库"""

    def __init__(self, db: Session):
        super().__init__(AccountTransaction, db)

    def get_by_account(
        self, account_id: int, skip: int = 0, limit: int = 100
    ) -> List[AccountTransaction]:
        """
        根据账户ID获取交易流水

        Args:
            account_id: 账户ID
            skip: 跳过记录数
            limit: 返回记录数

        Returns:
            交易流水列表
        """
        return (
            self.db.query(AccountTransaction)
            .filter(AccountTransaction.account_id == account_id)
            .order_by(AccountTransaction.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_office(
        self, office_id: int, skip: int = 0, limit: int = 100
    ) -> List[AccountTransaction]:
        """
        根据办公室ID获取交易流水

        Args:
            office_id: 办公室ID
            skip: 跳过记录数
            limit: 返回记录数

        Returns:
            交易流水列表
        """
        return (
            self.db.query(AccountTransaction)
            .filter(AccountTransaction.office_id == office_id)
            .order_by(AccountTransaction.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_type(
        self, transaction_type: str, skip: int = 0, limit: int = 100
    ) -> List[AccountTransaction]:
        """
        根据类型获取交易流水

        Args:
            transaction_type: 交易类型
            skip: 跳过记录数
            limit: 返回记录数

        Returns:
            交易流水列表
        """
        return (
            self.db.query(AccountTransaction)
            .filter(AccountTransaction.type == transaction_type)
            .order_by(AccountTransaction.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def create_transaction(
        self,
        account_id: int,
        office_id: int,
        product_id: int,
        transaction_type: str,
        quantity: int,
        before_qty: int,
        after_qty: int,
        operator_id: int = None,
        reference_type: str = None,
        reference_id: int = None,
        note: str = None,
    ) -> AccountTransaction:
        """
        创建交易流水

        Args:
            account_id: 账户ID
            office_id: 办公室ID
            product_id: 产品ID
            transaction_type: 交易类型
            quantity: 数量
            before_qty: 变动前数量
            after_qty: 变动后数量
            operator_id: 操作人ID
            reference_type: 关联类型
            reference_id: 关联ID
            note: 备注

        Returns:
            交易流水实例
        """
        transaction_data = {
            "account_id": account_id,
            "office_id": office_id,
            "product_id": product_id,
            "type": transaction_type,
            "quantity": quantity,
            "before_qty": before_qty,
            "after_qty": after_qty,
            "operator_id": operator_id,
            "reference_type": reference_type,
            "reference_id": reference_id,
            "note": note,
        }

        return self.create(transaction_data)
