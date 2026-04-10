"""
交易相关模型
包含Transaction模型定义
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from models.base import Base


class Transaction(Base):
    """交易表"""

    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, default=1)
    actual_price = Column(Float)  # Price after promotion
    type = Column(String, default="pickup")  # pickup or reserve
    status = Column(String, default="unsettled")  # unsettled, settled, reserved
    settlement_applied = Column(Integer, default=0)  # 0: 未申请结算，1: 已申请待确认
    note = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.now)

    # 软删除字段
    is_deleted = Column(Integer, default=0)  # 0: 未删除，1: 已删除
    deleted_at = Column(DateTime, nullable=True)  # 删除时间
    deleted_by = Column(Integer, ForeignKey("users.id"), nullable=True)  # 删除人 ID
    delete_reason = Column(String, nullable=True)  # 删除原因

    # 保护字段
    is_protected = Column(
        Integer, default=0
    )  # 0: 可删除, 1: 受保护(发布后自动保护真实数据)

    # 双模式业务字段
    mode = Column(String(20), default="pay_later")  # 'pay_later' 或 'prepay'
    reserved_qty = Column(Integer, default=0)  # 预定时预留的数量
    used_qty = Column(Integer, default=0)  # 已使用的数量
    payment_status = Column(
        String(20), default="unpaid"
    )  # 'unpaid', 'paid', 'refunded'

    user = relationship("User", foreign_keys=[user_id], back_populates="transactions")
    product = relationship("Product", back_populates="transactions")
