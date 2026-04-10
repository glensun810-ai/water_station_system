"""
库存仓库
处理库存相关的数据访问
"""

from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import datetime

from repositories.base import BaseRepository
from models.inventory import InventoryRecord, InventoryAlertConfig


class InventoryRecordRepository(BaseRepository[InventoryRecord]):
    """库存记录仓库"""

    def __init__(self, db: Session):
        super().__init__(InventoryRecord, db)

    def get_by_product(
        self, product_id: int, skip: int = 0, limit: int = 100
    ) -> List[InventoryRecord]:
        """
        根据产品ID获取库存记录

        Args:
            product_id: 产品ID
            skip: 跳过记录数
            limit: 返回记录数

        Returns:
            库存记录列表
        """
        return (
            self.db.query(InventoryRecord)
            .filter(InventoryRecord.product_id == product_id)
            .order_by(InventoryRecord.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_type(
        self, record_type: str, skip: int = 0, limit: int = 100
    ) -> List[InventoryRecord]:
        """
        根据类型获取库存记录

        Args:
            record_type: 记录类型 (in/out/adjust/loss)
            skip: 跳过记录数
            limit: 返回记录数

        Returns:
            库存记录列表
        """
        return (
            self.db.query(InventoryRecord)
            .filter(InventoryRecord.type == record_type)
            .order_by(InventoryRecord.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_date_range(
        self, start_date: datetime, end_date: datetime, skip: int = 0, limit: int = 100
    ) -> List[InventoryRecord]:
        """
        根据日期范围获取库存记录

        Args:
            start_date: 开始日期
            end_date: 结束日期
            skip: 跳过记录数
            limit: 返回记录数

        Returns:
            库存记录列表
        """
        return (
            self.db.query(InventoryRecord)
            .filter(InventoryRecord.created_at >= start_date)
            .filter(InventoryRecord.created_at <= end_date)
            .order_by(InventoryRecord.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def create_record(
        self,
        product_id: int,
        record_type: str,
        quantity: int,
        before_stock: int,
        after_stock: int,
        operator_id: int = None,
        reference_type: str = None,
        reference_id: int = None,
        note: str = None,
    ) -> InventoryRecord:
        """
        创建库存记录

        Args:
            product_id: 产品ID
            record_type: 记录类型
            quantity: 数量
            before_stock: 变动前库存
            after_stock: 变动后库存
            operator_id: 操作人ID
            reference_type: 关联类型
            reference_id: 关联ID
            note: 备注

        Returns:
            库存记录实例
        """
        record_data = {
            "product_id": product_id,
            "type": record_type,
            "quantity": quantity,
            "before_stock": before_stock,
            "after_stock": after_stock,
            "operator_id": operator_id,
            "reference_type": reference_type,
            "reference_id": reference_id,
            "note": note,
        }
        return self.create(record_data)


class InventoryAlertConfigRepository(BaseRepository[InventoryAlertConfig]):
    """库存预警配置仓库"""

    def __init__(self, db: Session):
        super().__init__(InventoryAlertConfig, db)

    def get_by_product(self, product_id: int) -> Optional[InventoryAlertConfig]:
        """
        根据产品ID获取预警配置

        Args:
            product_id: 产品ID

        Returns:
            预警配置实例或None
        """
        return (
            self.db.query(InventoryAlertConfig)
            .filter(InventoryAlertConfig.product_id == product_id)
            .filter(InventoryAlertConfig.is_active == 1)
            .first()
        )

    def get_active_configs(self) -> List[InventoryAlertConfig]:
        """
        获取所有活跃的预警配置

        Returns:
            预警配置列表
        """
        return (
            self.db.query(InventoryAlertConfig)
            .filter(InventoryAlertConfig.is_active == 1)
            .all()
        )

    def update_thresholds(
        self,
        product_id: int,
        warning_threshold: int = None,
        critical_threshold: int = None,
    ) -> Optional[InventoryAlertConfig]:
        """
        更新预警阈值

        Args:
            product_id: 产品ID
            warning_threshold: 预警阈值
            critical_threshold: 严重阈值

        Returns:
            更新后的配置实例
        """
        config = self.get_by_product(product_id)
        if not config:
            return None

        update_data = {}
        if warning_threshold is not None:
            update_data["warning_threshold"] = warning_threshold
        if critical_threshold is not None:
            update_data["critical_threshold"] = critical_threshold

        if update_data:
            update_data["updated_at"] = datetime.now()
            return self.update(config.id, update_data)

        return config

    def deactivate(self, product_id: int) -> bool:
        """
        停用预警配置

        Args:
            product_id: 产品ID

        Returns:
            是否停用成功
        """
        config = self.get_by_product(product_id)
        if not config:
            return False

        return (
            self.update(config.id, {"is_active": 0, "updated_at": datetime.now()})
            is not None
        )
