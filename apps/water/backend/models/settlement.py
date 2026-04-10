"""
办公室结算相关模型
包含OfficeSettlement模型定义
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Text
from datetime import datetime

from models.base import Base


class OfficeSettlement(Base):
    """
    办公室结算记录表
    """

    __tablename__ = "office_settlement"

    id = Column(Integer, primary_key=True, index=True)
    settlement_no = Column(String(50), unique=True, nullable=False)

    office_id = Column(Integer, nullable=False)
    office_name = Column(String(100), nullable=False)
    office_room_number = Column(String(50), nullable=True)

    # 结算信息
    total_quantity = Column(Integer, nullable=False)
    total_amount = Column(Float, nullable=False)

    # 状态: pending(待支付) / applied(已支付待确认) / confirmed(已确认) / cancelled(已取消)
    status = Column(String(20), default="pending")

    # 申请人信息
    applied_by = Column(String(100), nullable=True)
    applied_by_id = Column(Integer, nullable=True)
    applied_at = Column(DateTime, nullable=True)

    # 确认人信息
    confirmed_by = Column(String(100), nullable=True)
    confirmed_by_id = Column(Integer, nullable=True)
    confirmed_at = Column(DateTime, nullable=True)

    # 关联的领水记录ID列表(JSON)
    pickup_ids = Column(Text, nullable=True)

    # 备注
    note = Column(String(500), nullable=True)

    # 审计字段
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
