"""
账户相关模型
包含OfficeAccount和AccountTransaction模型定义
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship
from datetime import datetime

from models.base import Base


class OfficeAccount(Base):
    """办公室账户表"""

    __tablename__ = "office_account"

    id = Column(Integer, primary_key=True, index=True)
    office_id = Column(Integer, nullable=False)
    office_name = Column(String(100), nullable=False)
    office_room_number = Column(String(50), nullable=True)
    product_id = Column(Integer, nullable=False)
    product_name = Column(String(100), nullable=False)
    product_specification = Column(String(50), nullable=True)

    total_qty = Column(Integer, default=0)
    paid_qty = Column(Integer, default=0)
    free_qty = Column(Integer, default=0)
    remaining_qty = Column(Integer, default=0)
    reserved_qty = Column(Integer, default=0)

    reserved_person = Column(String(100), nullable=True)
    reserved_person_id = Column(Integer, nullable=True)
    manager_name = Column(String(100), nullable=True)
    manager_id = Column(Integer, nullable=True)
    configured_count = Column(Integer, default=0)

    account_type = Column(String(20), default="credit")  # credit/prepaid
    status = Column(String(20), default="active")  # active/frozen/closed
    low_stock_threshold = Column(Integer, default=5)
    note = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    transactions = relationship("AccountTransaction", back_populates="account")


class AccountTransaction(Base):
    """账户变动流水记录"""

    __tablename__ = "account_transactions"

    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("office_account.id"), nullable=False)
    office_id = Column(Integer, nullable=False)
    product_id = Column(Integer, nullable=False)
    type = Column(String(20), nullable=False)  # in/out/adjust/reserve/unreserve
    quantity = Column(Integer, nullable=False)
    before_qty = Column(Integer, nullable=False)
    after_qty = Column(Integer, nullable=False)
    reference_type = Column(String(50))
    reference_id = Column(Integer)
    operator_id = Column(Integer)
    note = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.now)

    account = relationship("OfficeAccount", back_populates="transactions")
