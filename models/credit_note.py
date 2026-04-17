"""
记账账单模型 - 用于内部员工记账模式的月度账单管理
"""

from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Date,
    Text,
    ForeignKey,
    DECIMAL,
)
from sqlalchemy.orm import relationship
from datetime import datetime
from decimal import Decimal

from models.base import Base


class CreditNote(Base):
    """
    记账账单表 - 内部员工月度账单
    """

    __tablename__ = "credit_notes"

    id = Column(Integer, primary_key=True, index=True)
    note_no = Column(
        String(50), unique=True, nullable=False, index=True, comment="账单编号"
    )
    user_id = Column(
        Integer, ForeignKey("users.id"), nullable=False, index=True, comment="用户ID"
    )
    user_name = Column(String(100), comment="用户姓名")
    department = Column(String(100), comment="所属部门")
    month = Column(String(10), nullable=False, index=True, comment="账单月份 2026-04")

    total_amount = Column(DECIMAL(10, 2), default=Decimal("0"), comment="账单总金额")
    paid_amount = Column(DECIMAL(10, 2), default=Decimal("0"), comment="已支付金额")
    booking_count = Column(Integer, default=0, comment="预约次数")

    status = Column(
        String(20),
        default="pending",
        index=True,
        comment="pending/partially_paid/paid/settled",
    )
    due_date = Column(Date, nullable=True, comment="应付截止日期")

    paid_at = Column(DateTime, nullable=True, comment="支付时间")
    settled_at = Column(DateTime, nullable=True, comment="结算时间")
    settled_by = Column(String(100), nullable=True, comment="结算确认人")

    notes = Column(Text, nullable=True, comment="备注")

    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    user = relationship("User", foreign_keys=[user_id])
    items = relationship(
        "CreditNoteItem", back_populates="note", cascade="all, delete-orphan"
    )

    def generate_note_no(self):
        if not self.note_no:
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            self.note_no = f"CN{timestamp}"
        return self.note_no

    def add_item(self, booking, amount):
        item = CreditNoteItem(
            note_id=self.id,
            booking_id=booking.id,
            booking_no=booking.booking_no,
            booking_date=booking.booking_date,
            space_name=booking.resource_name,
            time_slot=f"{booking.start_time}-{booking.end_time}",
            amount=Decimal(str(amount)),
        )
        self.total_amount += item.amount
        self.booking_count += 1
        return item

    def mark_paid(self, amount, paid_at=None):
        self.paid_amount += Decimal(str(amount))
        if self.paid_amount >= self.total_amount:
            self.status = "paid"
        else:
            self.status = "partially_paid"
        self.paid_at = paid_at or datetime.now()

    def mark_settled(self, settled_by):
        self.status = "settled"
        self.settled_at = datetime.now()
        self.settled_by = settled_by


class CreditNoteItem(Base):
    """
    记账账单明细表 - 每笔预约的记账明细
    """

    __tablename__ = "credit_note_items"

    id = Column(Integer, primary_key=True, index=True)
    note_id = Column(Integer, ForeignKey("credit_notes.id"), nullable=False, index=True)
    booking_id = Column(Integer, ForeignKey("space_bookings.id"), nullable=False)

    booking_no = Column(String(50), comment="预约编号")
    booking_date = Column(Date, comment="预约日期")
    space_name = Column(String(100), comment="空间名称")
    time_slot = Column(String(20), comment="预约时段")
    amount = Column(DECIMAL(10, 2), nullable=False, comment="记账金额")

    settled_at = Column(DateTime, nullable=True, comment="结算时间")
    created_at = Column(DateTime, default=datetime.now)

    note = relationship("CreditNote", back_populates="items")
    booking = relationship("SpaceBooking", foreign_keys=[booking_id])
