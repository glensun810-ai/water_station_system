"""
发票相关模型
"""

from sqlalchemy import Column, Integer, String, DateTime, Enum, ForeignKey
from sqlalchemy.dialects.mysql import DECIMAL
from sqlalchemy.orm import relationship
from datetime import datetime

from models.base import Base


class Invoice(Base):
    """
    发票表
    """

    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, index=True)
    invoice_no = Column(String(64), unique=True, nullable=False, comment="发票号码")
    order_id = Column(
        Integer, ForeignKey("payment_orders.id"), nullable=False, comment="订单ID"
    )
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="用户ID")
    invoice_type = Column(
        Enum("individual", "company"), nullable=False, comment="发票类型：个人/企业"
    )
    title = Column(String(200), nullable=False, comment="发票抬头")
    tax_no = Column(String(50), nullable=True, comment="税号（企业必填）")
    address = Column(String(200), nullable=True, comment="地址")
    phone = Column(String(50), nullable=True, comment="电话")
    bank_name = Column(String(100), nullable=True, comment="开户银行")
    bank_account = Column(String(50), nullable=True, comment="银行账号")
    amount = Column(DECIMAL(10, 2), nullable=False, comment="金额")
    email = Column(String(100), nullable=True, comment="接收邮箱")
    file_path = Column(String(255), nullable=True, comment="发票文件路径")
    status = Column(
        Enum("pending", "issued", "sent"), default="pending", comment="状态"
    )
    issued_at = Column(DateTime, nullable=True, comment="开具时间")
    issued_by = Column(Integer, nullable=True, comment="开具人ID")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    order = relationship("PaymentOrder", foreign_keys=[order_id])
    user = relationship("User", foreign_keys=[user_id])
