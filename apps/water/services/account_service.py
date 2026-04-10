"""
账户服务
处理账户相关的业务逻辑
"""

from typing import List, Optional
from sqlalchemy.orm import Session

from repositories.account_repository import (
    OfficeAccountRepository,
    AccountTransactionRepository,
)
from models.account import OfficeAccount, AccountTransaction


class AccountService:
    """账户服务"""

    def __init__(self, db: Session):
        self.db = db
        self.account_repo = OfficeAccountRepository(db)
        self.transaction_repo = AccountTransactionRepository(db)

    def get_accounts(self, skip: int = 0, limit: int = 100) -> List[OfficeAccount]:
        """获取账户列表"""
        return self.account_repo.get_multi(skip, limit)

    def get_account(self, account_id: int) -> Optional[OfficeAccount]:
        """获取单个账户"""
        return self.account_repo.get(account_id)

    def get_accounts_by_office(self, office_id: int) -> List[OfficeAccount]:
        """根据办公室获取账户列表"""
        return self.account_repo.get_by_office(office_id)

    def get_account_by_office_product(
        self, office_id: int, product_id: int
    ) -> Optional[OfficeAccount]:
        """根据办公室和产品获取账户"""
        return self.account_repo.get_by_office_and_product(office_id, product_id)

    def get_active_accounts(self) -> List[OfficeAccount]:
        """获取所有活跃账户"""
        return self.account_repo.get_active_accounts()

    def get_low_stock_accounts(self) -> List[OfficeAccount]:
        """获取低库存账户"""
        return self.account_repo.get_low_stock_accounts()

    def create_account(
        self,
        office_id: int,
        office_name: str,
        product_id: int,
        product_name: str,
        total_qty: int = 0,
        office_room_number: str = None,
        product_specification: str = None,
        account_type: str = "credit",
        low_stock_threshold: int = 5,
    ) -> OfficeAccount:
        """
        创建账户

        Args:
            office_id: 办公室ID
            office_name: 办公室名称
            product_id: 产品ID
            product_name: 产品名称
            total_qty: 总数量
            office_room_number: 办公室房间号
            product_specification: 产品规格
            account_type: 账户类型
            low_stock_threshold: 低库存阈值

        Returns:
            账户实例
        """
        existing = self.account_repo.get_by_office_and_product(office_id, product_id)
        if existing:
            raise ValueError(f"办公室 {office_id} 已存在产品 {product_id} 的账户")

        account_data = {
            "office_id": office_id,
            "office_name": office_name,
            "office_room_number": office_room_number,
            "product_id": product_id,
            "product_name": product_name,
            "product_specification": product_specification,
            "total_qty": total_qty,
            "paid_qty": 0,
            "free_qty": 0,
            "remaining_qty": total_qty,
            "reserved_qty": 0,
            "account_type": account_type,
            "status": "active",
            "low_stock_threshold": low_stock_threshold,
        }

        return self.account_repo.create(account_data)

    def update_account(
        self, account_id: int, account_data: dict
    ) -> Optional[OfficeAccount]:
        """更新账户信息"""
        return self.account_repo.update(account_id, account_data)

    def deposit(
        self,
        account_id: int,
        quantity: int,
        is_free: bool = False,
        operator_id: int = None,
        note: str = None,
    ) -> OfficeAccount:
        """
        充值/入库

        Args:
            account_id: 账户ID
            quantity: 数量
            is_free: 是否免费
            operator_id: 操作人ID
            note: 备注

        Returns:
            账户实例
        """
        account = self.account_repo.get(account_id)
        if not account:
            raise ValueError(f"账户ID {account_id} 不存在")

        before_qty = account.remaining_qty
        after_qty = before_qty + quantity

        # 更新账户数量
        update_data = {
            "total_qty": account.total_qty + quantity,
            "remaining_qty": after_qty,
        }
        if is_free:
            update_data["free_qty"] = account.free_qty + quantity
        else:
            update_data["paid_qty"] = account.paid_qty + quantity

        updated_account = self.account_repo.update(account_id, update_data)

        # 创建交易流水
        self.transaction_repo.create_transaction(
            account_id=account_id,
            office_id=account.office_id,
            product_id=account.product_id,
            transaction_type="in",
            quantity=quantity,
            before_qty=before_qty,
            after_qty=after_qty,
            operator_id=operator_id,
            note=note,
        )

        return updated_account

    def withdraw(
        self,
        account_id: int,
        quantity: int,
        operator_id: int = None,
        reference_type: str = None,
        reference_id: int = None,
        note: str = None,
    ) -> OfficeAccount:
        """
        取货/出库

        Args:
            account_id: 账户ID
            quantity: 数量
            operator_id: 操作人ID
            reference_type: 关联类型
            reference_id: 关联ID
            note: 备注

        Returns:
            账户实例
        """
        account = self.account_repo.get(account_id)
        if not account:
            raise ValueError(f"账户ID {account_id} 不存在")

        if account.remaining_qty < quantity:
            raise ValueError(
                f"账户余额不足，当前余额: {account.remaining_qty}，需要: {quantity}"
            )

        before_qty = account.remaining_qty
        after_qty = before_qty - quantity

        # 更新账户数量
        updated_account = self.account_repo.update(
            account_id, {"remaining_qty": after_qty}
        )

        # 创建交易流水
        self.transaction_repo.create_transaction(
            account_id=account_id,
            office_id=account.office_id,
            product_id=account.product_id,
            transaction_type="out",
            quantity=quantity,
            before_qty=before_qty,
            after_qty=after_qty,
            operator_id=operator_id,
            reference_type=reference_type,
            reference_id=reference_id,
            note=note,
        )

        return updated_account

    def reserve(
        self,
        account_id: int,
        quantity: int,
        reserved_person: str = None,
        reserved_person_id: int = None,
        operator_id: int = None,
        note: str = None,
    ) -> OfficeAccount:
        """
        预留

        Args:
            account_id: 账户ID
            quantity: 数量
            reserved_person: 预留人姓名
            reserved_person_id: 预留人ID
            operator_id: 操作人ID
            note: 备注

        Returns:
            账户实例
        """
        account = self.account_repo.get(account_id)
        if not account:
            raise ValueError(f"账户ID {account_id} 不存在")

        available_qty = account.remaining_qty - account.reserved_qty
        if available_qty < quantity:
            raise ValueError(f"可预留数量不足，当前可预留: {available_qty}")

        before_qty = account.reserved_qty
        after_qty = before_qty + quantity

        # 更新预留数量
        update_data = {"reserved_qty": after_qty}
        if reserved_person:
            update_data["reserved_person"] = reserved_person
        if reserved_person_id:
            update_data["reserved_person_id"] = reserved_person_id

        updated_account = self.account_repo.update(account_id, update_data)

        # 创建交易流水
        self.transaction_repo.create_transaction(
            account_id=account_id,
            office_id=account.office_id,
            product_id=account.product_id,
            transaction_type="reserve",
            quantity=quantity,
            before_qty=before_qty,
            after_qty=after_qty,
            operator_id=operator_id,
            note=note,
        )

        return updated_account

    def unreserve(
        self,
        account_id: int,
        quantity: int,
        operator_id: int = None,
        note: str = None,
    ) -> OfficeAccount:
        """
        取消预留

        Args:
            account_id: 账户ID
            quantity: 数量
            operator_id: 操作人ID
            note: 备注

        Returns:
            账户实例
        """
        account = self.account_repo.get(account_id)
        if not account:
            raise ValueError(f"账户ID {account_id} 不存在")

        if account.reserved_qty < quantity:
            raise ValueError(f"预留数量不足，当前预留: {account.reserved_qty}")

        before_qty = account.reserved_qty
        after_qty = before_qty - quantity

        # 更新预留数量
        update_data = {"reserved_qty": after_qty}
        if after_qty == 0:
            update_data["reserved_person"] = None
            update_data["reserved_person_id"] = None

        updated_account = self.account_repo.update(account_id, update_data)

        # 创建交易流水
        self.transaction_repo.create_transaction(
            account_id=account_id,
            office_id=account.office_id,
            product_id=account.product_id,
            transaction_type="unreserve",
            quantity=quantity,
            before_qty=before_qty,
            after_qty=after_qty,
            operator_id=operator_id,
            note=note,
        )

        return updated_account

    def freeze_account(self, account_id: int) -> bool:
        """冻结账户"""
        return self.account_repo.freeze(account_id)

    def unfreeze_account(self, account_id: int) -> bool:
        """解冻账户"""
        return self.account_repo.unfreeze(account_id)

    def delete_account(self, account_id: int) -> bool:
        """删除账户"""
        return self.account_repo.delete(account_id)

    # 交易流水相关方法
    def get_transactions(
        self, skip: int = 0, limit: int = 100
    ) -> List[AccountTransaction]:
        """获取交易流水列表"""
        return self.transaction_repo.get_multi(skip, limit)

    def get_account_transactions(
        self, account_id: int, skip: int = 0, limit: int = 100
    ) -> List[AccountTransaction]:
        """获取账户的交易流水"""
        return self.transaction_repo.get_by_account(account_id, skip, limit)

    def get_office_transactions(
        self, office_id: int, skip: int = 0, limit: int = 100
    ) -> List[AccountTransaction]:
        """获取办公室的交易流水"""
        return self.transaction_repo.get_by_office(office_id, skip, limit)
