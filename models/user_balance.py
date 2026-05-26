"""
用户余额账户模型 - 支持会员充值和服务充值
"""

from sqlalchemy import Column, Integer, String, DateTime, Enum, ForeignKey, Text, Date, Numeric
from sqlalchemy.orm import relationship
from datetime import datetime
from enum import Enum as PyEnum

from models.base import Base


class BalanceType(PyEnum):
    MEMBERSHIP = "membership"
    SERVICE = "service"
    GIFT = "gift"


class TransactionType(PyEnum):
    MEMBERSHIP_CHARGE = "membership_charge"
    SERVICE_CHARGE = "service_charge"
    DEDUCT = "deduct"
    REFUND = "refund"
    GIFT = "gift"
    ADJUST = "adjust"
    TRANSFER = "transfer"


class UserBalanceAccount(Base):
    """
    用户余额账户表 - 区分会员余额和服务余额
    """

    __tablename__ = "user_balance_accounts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer, ForeignKey("users.id"), unique=True, nullable=False, comment="用户ID"
    )

    membership_balance = Column(Numeric(10, 2), default=0, comment="会员充值余额")
    service_balance = Column(Numeric(10, 2), default=0, comment="服务充值余额")
    gift_balance = Column(Numeric(10, 2), default=0, comment="赠送余额")
    total_balance = Column(Numeric(10, 2), default=0, comment="总余额(只读)")

    membership_expire_date = Column(Date, nullable=True, comment="会员余额过期日期")

    frozen_membership_balance = Column(
        Numeric(10, 2), default=0, comment="冻结会员余额"
    )
    frozen_service_balance = Column(Numeric(10, 2), default=0, comment="冻结服务余额")

    credit_limit = Column(Numeric(10, 2), default=0, comment="信用额度上限(可透支金额，0=不启用)")
    credit_used = Column(Numeric(10, 2), default=0, comment="已使用信用额度(负余额部分)")

    total_membership_charged = Column(Numeric(10, 2), default=0, comment="累计会员充值")
    total_service_charged = Column(Numeric(10, 2), default=0, comment="累计服务充值")
    total_deducted = Column(Numeric(10, 2), default=0, comment="累计抵扣")
    total_refunded = Column(Numeric(10, 2), default=0, comment="累计退款")

    last_transaction_at = Column(DateTime, nullable=True, comment="最后交易时间")

    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    user = relationship("User", foreign_keys=[user_id], backref="balance_account")

    def get_available_balance(self):
        """获取可用余额（含信用额度信息）"""
        mb = self.membership_balance or 0
        sb = self.service_balance or 0
        gb = self.gift_balance or 0
        frozen_mb = self.frozen_membership_balance or 0
        frozen_sb = self.frozen_service_balance or 0

        available_total = float(mb + sb + gb - frozen_mb - frozen_sb)
        credit = float(self.credit_limit or 0)
        credit_remaining = max(0, credit - float(self.credit_used or 0))

        return {
            "membership": float(mb - frozen_mb),
            "service": float(sb - frozen_sb),
            "gift": float(gb),
            "total": available_total,
            "total_with_credit": available_total + credit_remaining,
            "credit_limit": credit,
            "credit_used": float(self.credit_used or 0),
            "credit_remaining": credit_remaining,
        }

    def update_total_balance(self):
        """更新总余额"""
        self.total_balance = (
            (self.membership_balance or 0)
            + (self.service_balance or 0)
            + (self.gift_balance or 0)
        )


class BalanceTransaction(Base):
    """
    余额变动记录表 - 记录所有余额变动
    """

    __tablename__ = "balance_transactions"

    id = Column(Integer, primary_key=True, index=True)
    transaction_no = Column(
        String(64), unique=True, nullable=False, comment="交易流水号"
    )
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="用户ID")

    transaction_type = Column(Enum(TransactionType), nullable=False, comment="交易类型")

    amount = Column(
        Numeric(10, 2), nullable=False, comment="变动金额(正数为增加,负数为减少)"
    )

    balance_type = Column(Enum(BalanceType), nullable=True, comment="余额类型")

    before_membership_balance = Column(
        Numeric(10, 2), nullable=True, comment="变动前会员余额"
    )
    before_service_balance = Column(
        Numeric(10, 2), nullable=True, comment="变动前服务余额"
    )
    before_gift_balance = Column(
        Numeric(10, 2), nullable=True, comment="变动前赠送余额"
    )
    before_total_balance = Column(Numeric(10, 2), nullable=True, comment="变动前总余额")

    after_membership_balance = Column(
        Numeric(10, 2), nullable=True, comment="变动后会员余额"
    )
    after_service_balance = Column(
        Numeric(10, 2), nullable=True, comment="变动后服务余额"
    )
    after_gift_balance = Column(Numeric(10, 2), nullable=True, comment="变动后赠送余额")
    after_total_balance = Column(Numeric(10, 2), nullable=True, comment="变动后总余额")

    reference_type = Column(
        String(50),
        nullable=True,
        comment="关联类型(membership_order/service_order/deduct_order)",
    )
    reference_id = Column(Integer, nullable=True, comment="关联记录ID")
    reference_no = Column(String(64), nullable=True, comment="关联记录编号")

    description = Column(Text, nullable=True, comment="交易描述")

    admin_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=True,
        comment="操作管理员ID(手动调整时)",
    )

    expire_date = Column(Date, nullable=True, comment="余额过期日期(会员余额)")

    created_at = Column(DateTime, default=datetime.now)

    user = relationship("User", foreign_keys=[user_id], backref="balance_transactions")
    admin = relationship("User", foreign_keys=[admin_id])

    def generate_transaction_no(self):
        """生成交易流水号"""
        if not self.transaction_no:
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
            self.transaction_no = f"TX{timestamp}"
        return self.transaction_no


class BalanceDeductRecord(Base):
    """
    余额抵扣记录表 - 记录每次抵扣消费
    """

    __tablename__ = "balance_deduct_records"

    id = Column(Integer, primary_key=True, index=True)
    deduct_no = Column(String(64), unique=True, nullable=False, comment="抵扣流水号")
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="用户ID")

    order_type = Column(
        String(50), nullable=False, comment="订单类型(meeting/dining/water)"
    )
    order_id = Column(Integer, nullable=False, comment="订单ID")
    order_no = Column(String(64), nullable=True, comment="订单编号")

    total_amount = Column(Numeric(10, 2), nullable=False, comment="订单总金额")
    member_discount = Column(Numeric(10, 2), default=0, comment="会员折扣金额")
    member_free_amount = Column(Numeric(10, 2), default=0, comment="会员免费金额")

    membership_deduct = Column(Numeric(10, 2), default=0, comment="会员余额抵扣")
    service_deduct = Column(Numeric(10, 2), default=0, comment="服务余额抵扣")
    gift_deduct = Column(Numeric(10, 2), default=0, comment="赠送余额抵扣")

    cash_amount = Column(Numeric(10, 2), default=0, comment="现金支付金额")

    description = Column(Text, nullable=True, comment="抵扣说明")

    created_at = Column(DateTime, default=datetime.now)

    user = relationship("User", foreign_keys=[user_id], backref="deduct_records")

    def generate_deduct_no(self):
        """生成抵扣流水号"""
        if not self.deduct_no:
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            self.deduct_no = f"DD{timestamp}"
        return self.deduct_no
