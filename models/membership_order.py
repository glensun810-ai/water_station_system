"""
会员订单模型 - 支持线下支付和审核流程
"""

from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Enum,
    ForeignKey,
    Text,
    Date,
    Boolean,
)
from sqlalchemy.dialects.mysql import DECIMAL
from sqlalchemy.orm import relationship
from datetime import datetime
from enum import Enum as PyEnum

from models.base import Base


class PaymentType(PyEnum):
    ONLINE = "online"
    OFFLINE = "offline"


class MembershipOrderStatus(PyEnum):
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class MembershipOrder(Base):
    """
    会员订单表 - 支持线下支付审核流程
    """

    __tablename__ = "membership_orders"

    id = Column(Integer, primary_key=True, index=True)
    order_no = Column(String(64), unique=True, nullable=False, comment="订单号")
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="用户ID")
    plan_id = Column(
        Integer, ForeignKey("membership_plans.id"), nullable=False, comment="会员套餐ID"
    )

    amount = Column(DECIMAL(10, 2), nullable=False, comment="订单金额")
    original_amount = Column(DECIMAL(10, 2), nullable=True, comment="原价金额")
    discount_amount = Column(DECIMAL(10, 2), default=0, comment="优惠金额")

    payment_type = Column(
        Enum(PaymentType), default=PaymentType.OFFLINE, comment="支付类型"
    )
    payment_method = Column(
        String(50), nullable=True, comment="支付方式(线下:bank_transfer/cash/check)"
    )
    payment_proof = Column(String(255), nullable=True, comment="支付凭证文件路径")

    status = Column(
        Enum(MembershipOrderStatus),
        default=MembershipOrderStatus.PENDING_REVIEW,
        comment="订单状态",
    )

    admin_id = Column(
        Integer, ForeignKey("users.id"), nullable=True, comment="审核管理员ID"
    )
    review_note = Column(Text, nullable=True, comment="审核备注")
    reviewed_at = Column(DateTime, nullable=True, comment="审核时间")

    balance_added = Column(DECIMAL(10, 2), default=0, comment="入账余额金额")
    member_start_date = Column(Date, nullable=True, comment="会员开始日期")
    member_end_date = Column(Date, nullable=True, comment="会员结束日期")
    member_days = Column(Integer, default=0, comment="会员天数")

    apply_note = Column(Text, nullable=True, comment="申请备注")
    cancel_reason = Column(Text, nullable=True, comment="取消原因")

    paid_at = Column(DateTime, nullable=True, comment="支付确认时间")
    trade_no = Column(String(128), nullable=True, comment="第三方交易号")

    is_renewal = Column(Boolean, default=False, comment="是否续费订单")
    previous_order_id = Column(Integer, nullable=True, comment="前一次订单ID(续费)")

    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    user = relationship("User", foreign_keys=[user_id], backref="membership_orders")
    plan = relationship("MembershipPlan", foreign_keys=[plan_id])
    admin = relationship("User", foreign_keys=[admin_id])

    def generate_order_no(self):
        """生成订单号"""
        if not self.order_no:
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            random_suffix = str(self.user_id).zfill(6)[-6:]
            self.order_no = f"MB{timestamp}{random_suffix}"
        return self.order_no


class MembershipOrderAudit(Base):
    """
    会员订单审核记录表 - 记录每次审核操作
    """

    __tablename__ = "membership_order_audits"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(
        Integer, ForeignKey("membership_orders.id"), nullable=False, comment="订单ID"
    )

    action = Column(
        String(20), nullable=False, comment="操作类型(approve/reject/cancel)"
    )
    admin_id = Column(
        Integer, ForeignKey("users.id"), nullable=False, comment="操作管理员ID"
    )

    before_status = Column(
        Enum(MembershipOrderStatus), nullable=True, comment="操作前状态"
    )
    after_status = Column(
        Enum(MembershipOrderStatus), nullable=True, comment="操作后状态"
    )

    note = Column(Text, nullable=True, comment="操作备注")

    created_at = Column(DateTime, default=datetime.now)

    order = relationship("MembershipOrder", foreign_keys=[order_id])
    admin = relationship("User", foreign_keys=[admin_id])
