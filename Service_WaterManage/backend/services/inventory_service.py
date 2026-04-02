"""
库存服务
处理库存相关的业务逻辑
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from datetime import datetime

from repositories.inventory_repository import (
    InventoryRecordRepository,
    InventoryAlertConfigRepository,
)
from repositories.product_repository import ProductRepository
from models.inventory import InventoryRecord, InventoryAlertConfig


class InventoryService:
    """库存服务"""

    def __init__(self, db: Session):
        self.db = db
        self.record_repo = InventoryRecordRepository(db)
        self.alert_config_repo = InventoryAlertConfigRepository(db)
        self.product_repo = ProductRepository(db)

    def get_records(self, skip: int = 0, limit: int = 100) -> List[InventoryRecord]:
        """获取库存记录列表"""
        return self.record_repo.get_multi(skip, limit)

    def get_record(self, record_id: int) -> Optional[InventoryRecord]:
        """获取单个库存记录"""
        return self.record_repo.get(record_id)

    def get_product_records(
        self, product_id: int, skip: int = 0, limit: int = 100
    ) -> List[InventoryRecord]:
        """获取产品的库存记录"""
        return self.record_repo.get_by_product(product_id, skip, limit)

    def get_records_by_type(
        self, record_type: str, skip: int = 0, limit: int = 100
    ) -> List[InventoryRecord]:
        """根据类型获取库存记录"""
        return self.record_repo.get_by_type(record_type, skip, limit)

    def get_records_by_date_range(
        self, start_date: datetime, end_date: datetime, skip: int = 0, limit: int = 100
    ) -> List[InventoryRecord]:
        """根据日期范围获取库存记录"""
        return self.record_repo.get_by_date_range(start_date, end_date, skip, limit)

    def stock_in(
        self,
        product_id: int,
        quantity: int,
        operator_id: int = None,
        note: str = None,
    ) -> InventoryRecord:
        """
        入库操作

        Args:
            product_id: 产品ID
            quantity: 入库数量
            operator_id: 操作人ID
            note: 备注

        Returns:
            库存记录实例
        """
        product = self.product_repo.get(product_id)
        if not product:
            raise ValueError(f"产品ID {product_id} 不存在")

        before_stock = product.stock
        after_stock = before_stock + quantity

        # 更新产品库存
        self.product_repo.update(product_id, {"stock": after_stock})

        # 创建库存记录
        record = self.record_repo.create_record(
            product_id=product_id,
            record_type="in",
            quantity=quantity,
            before_stock=before_stock,
            after_stock=after_stock,
            operator_id=operator_id,
            note=note,
        )

        return record

    def stock_out(
        self,
        product_id: int,
        quantity: int,
        operator_id: int = None,
        reference_type: str = None,
        reference_id: int = None,
        note: str = None,
    ) -> InventoryRecord:
        """
        出库操作

        Args:
            product_id: 产品ID
            quantity: 出库数量
            operator_id: 操作人ID
            reference_type: 关联类型
            reference_id: 关联ID
            note: 备注

        Returns:
            库存记录实例
        """
        product = self.product_repo.get(product_id)
        if not product:
            raise ValueError(f"产品ID {product_id} 不存在")

        before_stock = product.stock
        if before_stock < quantity:
            raise ValueError(f"库存不足，当前库存: {before_stock}，需要: {quantity}")

        after_stock = before_stock - quantity

        # 更新产品库存
        self.product_repo.update(product_id, {"stock": after_stock})

        # 创建库存记录
        record = self.record_repo.create_record(
            product_id=product_id,
            record_type="out",
            quantity=quantity,
            before_stock=before_stock,
            after_stock=after_stock,
            operator_id=operator_id,
            reference_type=reference_type,
            reference_id=reference_id,
            note=note,
        )

        return record

    def stock_adjust(
        self,
        product_id: int,
        quantity: int,
        operator_id: int = None,
        note: str = None,
    ) -> InventoryRecord:
        """
        库存调整

        Args:
            product_id: 产品ID
            quantity: 调整数量（可正可负）
            operator_id: 操作人ID
            note: 备注

        Returns:
            库存记录实例
        """
        product = self.product_repo.get(product_id)
        if not product:
            raise ValueError(f"产品ID {product_id} 不存在")

        before_stock = product.stock
        after_stock = before_stock + quantity

        if after_stock < 0:
            raise ValueError(f"调整后库存不能为负数")

        # 更新产品库存
        self.product_repo.update(product_id, {"stock": after_stock})

        # 创建库存记录
        record = self.record_repo.create_record(
            product_id=product_id,
            record_type="adjust",
            quantity=quantity,
            before_stock=before_stock,
            after_stock=after_stock,
            operator_id=operator_id,
            note=note,
        )

        return record

    def stock_loss(
        self,
        product_id: int,
        quantity: int,
        operator_id: int = None,
        note: str = None,
    ) -> InventoryRecord:
        """
        库存报损

        Args:
            product_id: 产品ID
            quantity: 报损数量
            operator_id: 操作人ID
            note: 备注

        Returns:
            库存记录实例
        """
        product = self.product_repo.get(product_id)
        if not product:
            raise ValueError(f"产品ID {product_id} 不存在")

        before_stock = product.stock
        if before_stock < quantity:
            raise ValueError(f"库存不足，当前库存: {before_stock}，报损: {quantity}")

        after_stock = before_stock - quantity

        # 更新产品库存
        self.product_repo.update(product_id, {"stock": after_stock})

        # 创建库存记录
        record = self.record_repo.create_record(
            product_id=product_id,
            record_type="loss",
            quantity=quantity,
            before_stock=before_stock,
            after_stock=after_stock,
            operator_id=operator_id,
            note=note,
        )

        return record

    # 预警配置相关方法
    def get_alert_config(self, product_id: int) -> Optional[InventoryAlertConfig]:
        """获取产品的预警配置"""
        return self.alert_config_repo.get_by_product(product_id)

    def get_active_alert_configs(self) -> List[InventoryAlertConfig]:
        """获取所有活跃的预警配置"""
        return self.alert_config_repo.get_active_configs()

    def create_alert_config(
        self,
        product_id: int,
        warning_threshold: int = 10,
        critical_threshold: int = 5,
    ) -> InventoryAlertConfig:
        """
        创建预警配置

        Args:
            product_id: 产品ID
            warning_threshold: 预警阈值
            critical_threshold: 严重阈值

        Returns:
            预警配置实例
        """
        product = self.product_repo.get(product_id)
        if not product:
            raise ValueError(f"产品ID {product_id} 不存在")

        existing = self.alert_config_repo.get_by_product(product_id)
        if existing:
            raise ValueError(f"产品ID {product_id} 已存在预警配置")

        config_data = {
            "product_id": product_id,
            "warning_threshold": warning_threshold,
            "critical_threshold": critical_threshold,
            "is_active": 1,
        }

        return self.alert_config_repo.create(config_data)

    def update_alert_config(
        self,
        product_id: int,
        warning_threshold: int = None,
        critical_threshold: int = None,
    ) -> Optional[InventoryAlertConfig]:
        """更新预警配置"""
        return self.alert_config_repo.update_thresholds(
            product_id, warning_threshold, critical_threshold
        )

    def deactivate_alert_config(self, product_id: int) -> bool:
        """停用预警配置"""
        return self.alert_config_repo.deactivate(product_id)

    def check_stock_alert(self, product_id: int) -> Optional[dict]:
        """
        检查库存预警

        Args:
            product_id: 产品ID

        Returns:
            预警信息，如果无预警返回None
        """
        product = self.product_repo.get(product_id)
        if not product:
            return None

        config = self.alert_config_repo.get_by_product(product_id)
        if not config:
            return None

        current_stock = product.stock

        if current_stock <= config.critical_threshold:
            return {
                "product_id": product_id,
                "product_name": product.name,
                "current_stock": current_stock,
                "alert_level": "critical",
                "threshold": config.critical_threshold,
                "message": f"库存严重不足: {current_stock} (阈值: {config.critical_threshold})",
            }
        elif current_stock <= config.warning_threshold:
            return {
                "product_id": product_id,
                "product_name": product.name,
                "current_stock": current_stock,
                "alert_level": "warning",
                "threshold": config.warning_threshold,
                "message": f"库存预警: {current_stock} (阈值: {config.warning_threshold})",
            }

        return None

    def check_all_alerts(self) -> List[dict]:
        """
        检查所有产品的库存预警

        Returns:
            预警信息列表
        """
        configs = self.alert_config_repo.get_active_configs()
        alerts = []

        for config in configs:
            alert = self.check_stock_alert(config.product_id)
            if alert:
                alerts.append(alert)

        return alerts
