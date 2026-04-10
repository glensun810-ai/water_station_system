"""
仓库层包
导出所有仓库类
"""

from repositories.base import BaseRepository
from repositories.user_repository import UserRepository
from repositories.product_repository import ProductRepository, ProductCategoryRepository
from repositories.transaction_repository import TransactionRepository
from repositories.inventory_repository import (
    InventoryRecordRepository,
    InventoryAlertConfigRepository,
)
from repositories.account_repository import (
    OfficeAccountRepository,
    AccountTransactionRepository,
)

__all__ = [
    "BaseRepository",
    "UserRepository",
    "ProductRepository",
    "ProductCategoryRepository",
    "TransactionRepository",
    "InventoryRecordRepository",
    "InventoryAlertConfigRepository",
    "OfficeAccountRepository",
    "AccountTransactionRepository",
]
