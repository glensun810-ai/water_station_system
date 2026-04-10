"""
办公室充值相关模型
包含OfficeRecharge模型定义
"""

from sqlalchemy import Column, Integer, String, Float, DateTime
from datetime import datetime

from models.base import Base


class OfficeRecharge(Base):
    """
    办公室充值记录表
    """

    __tablename__ = "office_recharge"

    id = Column(Integer, primary_key=True, index=True)
    office_id = Column(Integer, nullable=False)
    office_name = Column(String(100), nullable=False)
    office_room_number = Column(String(50), nullable=True)
    product_id = Column(Integer, nullable=False)
    product_name = Column(String(100), nullable=False)
    product_specification = Column(String(50), nullable=True)

    # 充值数量
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Float, nullable=False)
    total_amount = Column(Float, nullable=False)

    # 充值人信息
    recharge_person = Column(String(100), nullable=True)
    recharge_person_id = Column(Integer, nullable=True)

    # 备注
    note = Column(String(500), nullable=True)

    # 审计字段
    created_at = Column(DateTime, default=datetime.now)
