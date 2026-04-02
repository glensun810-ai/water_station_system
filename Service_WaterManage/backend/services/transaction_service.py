"""
交易服务
处理交易相关的业务逻辑
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from datetime import datetime

from repositories.transaction_repository import TransactionRepository
from repositories.product_repository import ProductRepository
from repositories.user_repository import UserRepository
from models.transaction import Transaction


class TransactionService:
    """交易服务"""

    def __init__(self, db: Session):
        self.db = db
        self.transaction_repo = TransactionRepository(db)
        self.product_repo = ProductRepository(db)
        self.user_repo = UserRepository(db)

    def get_transactions(self, skip: int = 0, limit: int = 100) -> List[Transaction]:
        """获取交易列表"""
        return self.transaction_repo.get_multi(skip, limit)

    def get_transaction(self, transaction_id: int) -> Optional[Transaction]:
        """获取单个交易"""
        return self.transaction_repo.get(transaction_id)

    def get_user_transactions(
        self, user_id: int, skip: int = 0, limit: int = 100
    ) -> List[Transaction]:
        """获取用户的交易列表"""
        return self.transaction_repo.get_by_user(user_id, skip, limit)

    def get_product_transactions(
        self, product_id: int, skip: int = 0, limit: int = 100
    ) -> List[Transaction]:
        """获取产品的交易列表"""
        return self.transaction_repo.get_by_product(product_id, skip, limit)

    def get_unsettled_transactions(
        self, skip: int = 0, limit: int = 100
    ) -> List[Transaction]:
        """获取未结算的交易"""
        return self.transaction_repo.get_unsettled(skip, limit)

    def get_settled_transactions(
        self, skip: int = 0, limit: int = 100
    ) -> List[Transaction]:
        """获取已结算的交易"""
        return self.transaction_repo.get_settled(skip, limit)

    def get_transactions_by_status(
        self, status: str, skip: int = 0, limit: int = 100
    ) -> List[Transaction]:
        """根据状态获取交易"""
        return self.transaction_repo.get_by_status(status, skip, limit)

    def get_transactions_by_type(
        self, type: str, skip: int = 0, limit: int = 100
    ) -> List[Transaction]:
        """根据类型获取交易"""
        return self.transaction_repo.get_by_type(type, skip, limit)

    def get_transactions_by_date_range(
        self, start_date: datetime, end_date: datetime, skip: int = 0, limit: int = 100
    ) -> List[Transaction]:
        """根据日期范围获取交易"""
        return self.transaction_repo.get_by_date_range(
            start_date, end_date, skip, limit
        )

    def create_transaction(
        self,
        user_id: int,
        product_id: int,
        quantity: int = 1,
        actual_price: float = None,
        type: str = "pickup",
        note: str = None,
    ) -> Transaction:
        """
        创建交易

        Args:
            user_id: 用户ID
            product_id: 产品ID
            quantity: 数量
            actual_price: 实际价格（可选，如果不提供则使用产品价格）
            type: 交易类型 (pickup/reserve)
            note: 备注

        Returns:
            创建的交易实例
        """
        product = self.product_repo.get(product_id)
        if not product:
            raise ValueError(f"产品ID {product_id} 不存在")

        user = self.user_repo.get(user_id)
        if not user:
            raise ValueError(f"用户ID {user_id} 不存在")

        if actual_price is None:
            actual_price = product.price

        transaction_data = {
            "user_id": user_id,
            "product_id": product_id,
            "quantity": quantity,
            "actual_price": actual_price,
            "type": type,
            "status": "unsettled",
            "note": note,
        }

        transaction = self.transaction_repo.create(transaction_data)

        self.product_repo.decrease_stock(product_id, quantity)

        return transaction

    def update_transaction(
        self, transaction_id: int, transaction_data: dict
    ) -> Optional[Transaction]:
        """
        更新交易

        Args:
            transaction_id: 交易ID
            transaction_data: 更新数据

        Returns:
            更新后的交易实例
        """
        return self.transaction_repo.update(transaction_id, transaction_data)

    def delete_transaction(
        self, transaction_id: int, deleted_by: int, delete_reason: str = None
    ) -> bool:
        """
        删除交易（软删除）

        Args:
            transaction_id: 交易ID
            deleted_by: 删除人ID
            delete_reason: 删除原因

        Returns:
            是否删除成功
        """
        transaction = self.transaction_repo.get(transaction_id)
        if not transaction:
            return False

        if transaction.is_protected == 1:
            raise ValueError("该交易受保护，无法删除")

        success = self.transaction_repo.soft_delete(
            transaction_id, deleted_by, delete_reason
        )
        if success:
            self.product_repo.increase_stock(
                transaction.product_id, transaction.quantity
            )

        return success

    def restore_transaction(self, transaction_id: int) -> bool:
        """
        恢复已删除的交易

        Args:
            transaction_id: 交易ID

        Returns:
            是否恢复成功
        """
        transaction = self.transaction_repo.get(transaction_id)
        if not transaction:
            return False

        success = self.transaction_repo.restore(transaction_id)
        if success:
            self.product_repo.decrease_stock(
                transaction.product_id, transaction.quantity
            )

        return success

    def apply_settlement(self, transaction_id: int) -> bool:
        """
        申请结算

        Args:
            transaction_id: 交易ID

        Returns:
            是否申请成功
        """
        transaction = self.transaction_repo.get(transaction_id)
        if not transaction:
            return False

        if transaction.status != "unsettled":
            raise ValueError("只有未结算的交易才能申请结算")

        return self.transaction_repo.apply_settlement(transaction_id)

    def settle_transaction(self, transaction_id: int) -> bool:
        """
        结算交易

        Args:
            transaction_id: 交易ID

        Returns:
            是否结算成功
        """
        transaction = self.transaction_repo.get(transaction_id)
        if not transaction:
            return False

        if transaction.status != "unsettled":
            raise ValueError("只有未结算的交易才能结算")

        total_amount = transaction.actual_price * transaction.quantity

        success = self.user_repo.update_balance(transaction.user_id, -total_amount)
        if not success:
            return False

        return self.transaction_repo.settle(transaction_id)

    def get_user_total_amount(self, user_id: int) -> float:
        """获取用户交易总金额"""
        return self.transaction_repo.get_user_total_amount(user_id)

    def get_user_transaction_count(self, user_id: int) -> int:
        """获取用户交易数量"""
        return self.transaction_repo.get_user_transaction_count(user_id)

    def batch_settle_transactions(self, transaction_ids: List[int]) -> dict:
        """
        批量结算交易

        Args:
            transaction_ids: 交易ID列表

        Returns:
            结算结果 {成功数量, 失败数量, 失败详情}
        """
        success_count = 0
        failed_count = 0
        failed_details = []

        for transaction_id in transaction_ids:
            try:
                if self.settle_transaction(transaction_id):
                    success_count += 1
                else:
                    failed_count += 1
                    failed_details.append(
                        {"transaction_id": transaction_id, "reason": "结算失败"}
                    )
            except Exception as e:
                failed_count += 1
                failed_details.append(
                    {"transaction_id": transaction_id, "reason": str(e)}
                )

        return {
            "success_count": success_count,
            "failed_count": failed_count,
            "failed_details": failed_details,
        }
