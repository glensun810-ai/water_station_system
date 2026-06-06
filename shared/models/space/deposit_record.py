"""
押金记录模型
管理空间预约押金的收取和退还流水
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from .base import Base, TimestampMixin


class DepositRecord(Base, TimestampMixin):
    """押金记录模型"""

    __tablename__ = "deposit_records"

    id = Column(Integer, primary_key=True, index=True)

    deposit_no = Column(String(50), unique=True, nullable=False, index=True, comment="押金编号")

    booking_id = Column(Integer, ForeignKey("space_bookings.id"), nullable=False, index=True)
    booking_no = Column(String(50), comment="预约编号")

    user_id = Column(Integer, nullable=False, comment="用户ID")
    user_name = Column(String(100), comment="用户姓名")

    amount = Column(Float, nullable=False, default=0.0, comment="押金金额")

    status = Column(String(20), default="pending", index=True, comment="pending(待收)/collected(已收)/refunding(退还中)/refunded(已退还)/forfeited(已没收)")

    collected_at = Column(DateTime, nullable=True, comment="收取时间")
    collected_by = Column(String(100), comment="收取人")
    collect_method = Column(String(20), comment="收取方式: cash/transfer/wechat/alipay")
    collect_note = Column(Text, comment="收取备注")

    refunded_at = Column(DateTime, nullable=True, comment="退还时间")
    refunded_by = Column(String(100), comment="退还经办人")
    refund_method = Column(String(20), comment="退还方式")
    refund_note = Column(Text, comment="退还备注")

    forfeited_at = Column(DateTime, nullable=True, comment="没收时间")
    forfeited_by = Column(String(100), comment="没收经办人")
    forfeit_reason = Column(Text, comment="没收原因")

    def __repr__(self):
        return f"<DepositRecord(id={self.id}, deposit_no={self.deposit_no}, status={self.status})>"
