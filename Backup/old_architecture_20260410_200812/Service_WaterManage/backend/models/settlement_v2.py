"""
结算模块v2数据模型
包含SettlementApplication, SettlementItem, MonthlySettlement模型
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey, Date
from datetime import datetime
from sqlalchemy.orm import relationship

from models.base import Base


class SettlementApplication(Base):
    """
    结算申请单表
    记录用户提交的结算申请
    """

    __tablename__ = "settlement_applications"

    id = Column(Integer, primary_key=True, index=True)

    application_no = Column(String(50), unique=True, nullable=False, index=True)

    office_id = Column(Integer, nullable=False, index=True)
    office_name = Column(String(100), nullable=False)
    office_room_number = Column(String(50))

    applicant_id = Column(Integer, nullable=False, index=True)
    applicant_name = Column(String(100), nullable=False)
    applicant_role = Column(String(20))

    record_count = Column(Integer, nullable=False, default=0)
    total_amount = Column(Float, nullable=False, default=0.00)

    status = Column(String(20), nullable=False, default="applied", index=True)

    applied_at = Column(DateTime, nullable=False, default=datetime.now)

    approved_at = Column(DateTime)
    approved_by = Column(Integer)
    approved_by_name = Column(String(100))

    confirmed_at = Column(DateTime)
    confirmed_by = Column(Integer)
    confirmed_by_name = Column(String(100))

    settled_at = Column(DateTime)
    settled_by = Column(Integer)
    settled_by_name = Column(String(100))

    payment_method = Column(String(50))
    payment_account = Column(String(100))
    payment_reference = Column(String(100))
    payment_at = Column(DateTime)

    note = Column(String(500))
    reject_reason = Column(String(500))

    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    items = relationship(
        "SettlementItem", back_populates="application", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<SettlementApplication(id={self.id}, no={self.application_no}, status={self.status})>"


class SettlementItem(Base):
    """
    结算明细表
    关联结算申请单和领水记录
    """

    __tablename__ = "settlement_items"

    id = Column(Integer, primary_key=True, index=True)

    application_id = Column(
        Integer,
        ForeignKey("settlement_applications.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    pickup_id = Column(Integer, nullable=False, index=True)

    product_name = Column(String(100))
    product_id = Column(Integer)

    quantity = Column(Integer, nullable=False)
    unit_price = Column(Float)
    amount = Column(Float, nullable=False)

    pickup_status = Column(String(20), nullable=False, default="applied")

    pickup_time = Column(DateTime)

    pickup_person = Column(String(100))
    pickup_person_id = Column(Integer)

    note = Column(String(500))

    created_at = Column(DateTime, default=datetime.now)

    application = relationship("SettlementApplication", back_populates="items")

    def __repr__(self):
        return f"<SettlementItem(id={self.id}, application_id={self.application_id}, pickup_id={self.pickup_id})>"


class MonthlySettlement(Base):
    """
    月度结算单表
    记录月度结算汇总信息
    """

    __tablename__ = "monthly_settlements"

    id = Column(Integer, primary_key=True, index=True)

    settlement_no = Column(String(50), unique=True, nullable=False, index=True)

    office_id = Column(Integer, nullable=False, index=True)
    office_name = Column(String(100), nullable=False)
    office_room_number = Column(String(50))

    settlement_period = Column(String(20), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)

    record_count = Column(Integer, nullable=False, default=0)
    total_amount = Column(Float, nullable=False, default=0.00)

    status = Column(String(20), nullable=False, default="pending", index=True)

    approved_at = Column(DateTime)
    approved_by = Column(Integer)
    approved_by_name = Column(String(100))

    settled_at = Column(DateTime)
    settled_by = Column(Integer)
    settled_by_name = Column(String(100))

    payment_method = Column(String(50))
    payment_account = Column(String(100))
    payment_reference = Column(String(100))
    payment_at = Column(DateTime)

    note = Column(String(500))

    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    def __repr__(self):
        return f"<MonthlySettlement(id={self.id}, no={self.settlement_no}, period={self.settlement_period})>"
