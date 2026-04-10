"""
交易仓库
处理交易相关的数据访问
"""

from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from datetime import datetime

from repositories.base import BaseRepository
from models.transaction import Transaction


class TransactionRepository(BaseRepository[Transaction]):
    """交易仓库"""

    def __init__(self, db: Session):
        super().__init__(Transaction, db)

    def get_by_user(
        self, user_id: int, skip: int = 0, limit: int = 100
    ) -> List[Transaction]:
        """
        根据用户ID获取交易列表

        Args:
            user_id: 用户ID
            skip: 跳过记录数
            limit: 返回记录数

        Returns:
            交易列表
        """
        return (
            self.db.query(Transaction)
            .filter(Transaction.user_id == user_id)
            .filter(Transaction.is_deleted == 0)
            .order_by(Transaction.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_product(
        self, product_id: int, skip: int = 0, limit: int = 100
    ) -> List[Transaction]:
        """
        根据产品ID获取交易列表

        Args:
            product_id: 产品ID
            skip: 跳过记录数
            limit: 返回记录数

        Returns:
            交易列表
        """
        return (
            self.db.query(Transaction)
            .filter(Transaction.product_id == product_id)
            .filter(Transaction.is_deleted == 0)
            .order_by(Transaction.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_status(
        self, status: str, skip: int = 0, limit: int = 100
    ) -> List[Transaction]:
        """
        根据状态获取交易列表

        Args:
            status: 交易状态
            skip: 跳过记录数
            limit: 返回记录数

        Returns:
            交易列表
        """
        return (
            self.db.query(Transaction)
            .filter(Transaction.status == status)
            .filter(Transaction.is_deleted == 0)
            .order_by(Transaction.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_type(
        self, type: str, skip: int = 0, limit: int = 100
    ) -> List[Transaction]:
        """
        根据类型获取交易列表

        Args:
            type: 交易类型 (pickup/reserve)
            skip: 跳过记录数
            limit: 返回记录数

        Returns:
            交易列表
        """
        return (
            self.db.query(Transaction)
            .filter(Transaction.type == type)
            .filter(Transaction.is_deleted == 0)
            .order_by(Transaction.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_unsettled(self, skip: int = 0, limit: int = 100) -> List[Transaction]:
        """
        获取未结算的交易

        Args:
            skip: 跳过记录数
            limit: 返回记录数

        Returns:
            交易列表
        """
        return self.get_by_status("unsettled", skip, limit)

    def get_settled(self, skip: int = 0, limit: int = 100) -> List[Transaction]:
        """
        获取已结算的交易

        Args:
            skip: 跳过记录数
            limit: 返回记录数

        Returns:
            交易列表
        """
        return self.get_by_status("settled", skip, limit)

    def get_by_date_range(
        self, start_date: datetime, end_date: datetime, skip: int = 0, limit: int = 100
    ) -> List[Transaction]:
        """
        根据日期范围获取交易列表

        Args:
            start_date: 开始日期
            end_date: 结束日期
            skip: 跳过记录数
            limit: 返回记录数

        Returns:
            交易列表
        """
        return (
            self.db.query(Transaction)
            .filter(Transaction.created_at >= start_date)
            .filter(Transaction.created_at <= end_date)
            .filter(Transaction.is_deleted == 0)
            .order_by(Transaction.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def soft_delete(
        self, transaction_id: int, deleted_by: int, delete_reason: str = None
    ) -> bool:
        """
        软删除交易

        Args:
            transaction_id: 交易ID
            deleted_by: 删除人ID
            delete_reason: 删除原因

        Returns:
            是否删除成功
        """
        transaction = self.get(transaction_id)
        if not transaction:
            return False

        transaction.is_deleted = 1
        transaction.deleted_at = datetime.now()
        transaction.deleted_by = deleted_by
        transaction.delete_reason = delete_reason
        self.db.commit()
        return True

    def restore(self, transaction_id: int) -> bool:
        """
        恢复已删除的交易

        Args:
            transaction_id: 交易ID

        Returns:
            是否恢复成功
        """
        transaction = self.get(transaction_id)
        if not transaction:
            return False

        transaction.is_deleted = 0
        transaction.deleted_at = None
        transaction.deleted_by = None
        transaction.delete_reason = None
        self.db.commit()
        return True

    def get_user_total_amount(self, user_id: int) -> float:
        """
        获取用户交易总金额

        Args:
            user_id: 用户ID

        Returns:
            总金额
        """
        from sqlalchemy import func

        result = (
            self.db.query(func.sum(Transaction.actual_price * Transaction.quantity))
            .filter(Transaction.user_id == user_id)
            .filter(Transaction.status == "settled")
            .filter(Transaction.is_deleted == 0)
            .first()
        )
        return result[0] if result[0] else 0.0

    def get_user_transaction_count(self, user_id: int) -> int:
        """
        获取用户交易数量

        Args:
            user_id: 用户ID

        Returns:
            交易数量
        """
        return (
            self.db.query(Transaction)
            .filter(Transaction.user_id == user_id)
            .filter(Transaction.is_deleted == 0)
            .count()
        )

    def apply_settlement(self, transaction_id: int) -> bool:
        """
        申请结算

        Args:
            transaction_id: 交易ID

        Returns:
            是否申请成功
        """
        return self.update(transaction_id, {"settlement_applied": 1}) is not None

    def settle(self, transaction_id: int) -> bool:
        """
        结算交易

        Args:
            transaction_id: 交易ID

        Returns:
            是否结算成功
        """
        return self.update(transaction_id, {"status": "settled"}) is not None
