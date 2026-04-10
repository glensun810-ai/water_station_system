"""
领水记录相关模型
包含OfficePickup模型定义
"""

from sqlalchemy import Column, Integer, String, Float, DateTime
from datetime import datetime

from models.base import Base


class OfficePickup(Base):
    """
    办公室领水记录表
    """

    __tablename__ = "office_pickup"

    id = Column(Integer, primary_key=True, index=True)
    office_id = Column(Integer, nullable=False)
    office_name = Column(String(100), nullable=False)
    office_room_number = Column(String(50), nullable=True)
    product_id = Column(Integer, nullable=False)
    product_name = Column(String(100), nullable=False)
    product_specification = Column(String(50), nullable=True)

    # 领水数量
    quantity = Column(Integer, nullable=False)

    # 领水人信息
    pickup_person = Column(String(100), nullable=True)
    pickup_person_id = Column(Integer, nullable=True)

    # 领水时间
    pickup_time = Column(DateTime, nullable=False)

    # 支付模式: prepaid(预付) / credit(信用/先用后付)
    payment_mode = Column(String(20), default="credit")

    # 结算状态: pending(待结算) / applied(已申请待确认) / settled(已结清)
    settlement_status = Column(String(20), default="pending")

    # 金额
    unit_price = Column(Float, nullable=False)
    total_amount = Column(Float, nullable=False)

    # 备注
    note = Column(String(500), nullable=True)

    # 软删除字段
    is_deleted = Column(Integer, default=0)
    deleted_at = Column(DateTime, nullable=True)
    deleted_by = Column(Integer, nullable=True)
    delete_reason = Column(String(500), nullable=True)

    # 审计字段
    created_at = Column(DateTime, default=datetime.now)
