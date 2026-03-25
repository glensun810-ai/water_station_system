"""
Unified Account Models - 双模式业务统一架构
水站管理系统 - 统一账户数据模型
"""

from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Float,
    DateTime,
    ForeignKey,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import sessionmaker, Session, relationship, declarative_base
from datetime import datetime

SQLALCHEMY_DATABASE_URL = "sqlite:///./waterms.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class UserAccount(Base):
    """
    用户账户表 - 统一账户余额模型

    每个用户只有一个账户：
    - balance_prepaid: 预付余额（先付后用可用额度）
    """

    __tablename__ = "user_account"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, unique=True, nullable=False)  # 移除外键约束，避免测试问题

    # 预付余额
    balance_prepaid = Column(Float, default=0.0)  # 预付余额（先付后用）

    # 审计字段
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class AccountWallet(Base):
    """
    账户钱包表 - 按产品细分余额

    每个用户每个产品有预付钱包：
    - wallet_type='prepaid': 预付钱包（先付后用）
    """

    __tablename__ = "account_wallet"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)  # 移除外键
    product_id = Column(Integer, nullable=False)  # 移除外键
    wallet_type = Column(String(20), nullable=False)  # 'prepaid'

    # 余额字段
    available_qty = Column(Integer, default=0)  # 可用总数量
    paid_qty = Column(Integer, default=0)  # 付费数量
    free_qty = Column(Integer, default=0)  # 赠送数量
    locked_qty = Column(Integer, default=0)  # 锁定数量（申请结算中）
    total_consumed = Column(Integer, default=0)  # 累计消费数量

    # 审计字段
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # 唯一约束：每个用户每个产品每种钱包类型只有一条记录
    __table_args__ = (
        UniqueConstraint(
            "user_id", "product_id", "wallet_type", name="uq_wallet_user_product_type"
        ),
    )


class SettlementBatch(Base):
    """
    结算批次表 - 统一管理结算

    用于批量结算先用后付的交易记录
    """

    __tablename__ = "settlement_batch"

    id = Column(Integer, primary_key=True, index=True)
    batch_no = Column(String(50), unique=True, nullable=False)  # 批次号

    user_id = Column(Integer, nullable=False)  # 移除外键
    transaction_ids = Column(Text, nullable=False)  # JSON 字符串，交易 ID 列表

    total_amount = Column(Float, nullable=False)  # 结算总金额
    status = Column(
        String(20), default="pending"
    )  # 'pending', 'confirmed', 'completed'

    # 确认信息
    confirmed_at = Column(DateTime, nullable=True)
    confirmed_by = Column(Integer, nullable=True)  # 移除外键

    # 审计字段
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class TransactionV2(Base):
    """
    统一交易记录 - V2 版本

    支持双模式业务的统一交易记录
    """

    __tablename__ = "transactions_v2"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)  # 移除外键
    product_id = Column(Integer, nullable=False)  # 移除外键
    wallet_id = Column(Integer, nullable=True)  # 移除外键

    # 交易信息
    quantity = Column(Integer, default=1)
    unit_price = Column(Float, nullable=False)  # 单价
    actual_price = Column(Float, nullable=False)  # 实际金额

    # 模式信息
    mode = Column(String(20), default="credit")  # 'credit' 或 'prepaid'
    wallet_type = Column(String(20), default="credit")  # 冗余字段，便于查询

    # 状态信息
    status = Column(
        String(20), default="pending"
    )  # 'pending'(待结算), 'applied'(已支付待确认), 'settled'(已结算), 'cancelled'
    settlement_batch_id = Column(Integer, nullable=True)  # 移除外键

    # 结算字段（对齐产品方案）
    # settlement_status: pending | settled | partially_settled（本系统通常按交易拆分，因此多为 pending/settled）
    settlement_status = Column(String(20), default="pending")
    paid_amount = Column(Float, default=0.0)  # 已结算金额
    remaining_amount = Column(Float, default=0.0)  # 待结算金额

    # 优惠信息
    discount_desc = Column(String(200), nullable=True)  # 优惠描述
    free_qty = Column(Integer, default=0)  # 免费数量（先付时用）

    # 领用明细字段（新增）- 用于记录本次扣除的付费桶和赠送桶数量及对应财务金额
    paid_qty_deducted = Column(Integer, default=0)  # 扣除的付费桶数量
    gift_qty_deducted = Column(Integer, default=0)  # 扣除的赠送桶数量
    financial_amount = Column(Float, default=0.0)  # 对应的财务金额（赠送桶为 0 元）

    # 审计字段
    note = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class PromotionConfigV2(Base):
    """
    优惠配置表 V2 - 支持按模式配置不同优惠

    每个产品可以为不同模式配置不同的优惠策略
    """

    __tablename__ = "promotion_config_v2"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, nullable=False)  # 移除外键
    mode = Column(String(20), nullable=False, default="credit")  # 'credit' 或 'prepaid'

    # 优惠策略
    trigger_qty = Column(Integer, nullable=False, default=10)  # 买 N
    gift_qty = Column(Integer, nullable=False, default=0)  # 赠 M
    discount_rate = Column(Float, nullable=False, default=100.0)  # 折扣率（百分比）

    # 状态
    is_active = Column(Integer, default=1)
    description = Column(String(200), nullable=True)

    # 审计字段
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class OfficeAccount(Base):
    """
    办公室账户表 - 按办公室管理的预付账户

    每个办公室有一个账户，用于管理该办公室的饮用水预定
    """

    __tablename__ = "office_account"

    id = Column(Integer, primary_key=True, index=True)
    office_id = Column(Integer, nullable=False)
    office_name = Column(String(100), nullable=False)
    office_room_number = Column(String(50), nullable=True)
    product_id = Column(Integer, nullable=False)
    product_name = Column(String(100), nullable=False)
    product_specification = Column(String(50), nullable=True)

    # 预定数量
    reserved_qty = Column(Integer, default=0)  # 预定总数量
    remaining_qty = Column(Integer, default=0)  # 剩余数量

    # 预定人信息
    reserved_person = Column(String(100), nullable=True)  # 预定人姓名
    reserved_person_id = Column(Integer, nullable=True)  # 预定人用户ID

    # 备注
    note = Column(String(500), nullable=True)

    # 审计字段
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    __table_args__ = (
        UniqueConstraint(
            "office_id", "product_id", name="uq_office_account_office_product"
        ),
    )


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
    quantity = Column(Integer, nullable=False)  # 充值数量
    unit_price = Column(Float, nullable=False)  # 单价
    total_amount = Column(Float, nullable=False)  # 总金额

    # 充值人信息
    recharge_person = Column(String(100), nullable=True)  # 充值操作人
    recharge_person_id = Column(Integer, nullable=True)

    # 备注
    note = Column(String(500), nullable=True)

    # 审计字段
    created_at = Column(DateTime, default=datetime.now)


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

    # 审计字段
    created_at = Column(DateTime, default=datetime.now)


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


class SystemConfig(Base):
    """
    系统配置表 - 存储全局配置如收款二维码等
    """

    __tablename__ = "system_config"

    id = Column(Integer, primary_key=True, index=True)
    config_key = Column(String(100), unique=True, nullable=False)
    config_value = Column(Text, nullable=True)
    description = Column(String(500), nullable=True)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


def init_unified_db():
    """初始化统一账户数据库表"""
    Base.metadata.create_all(bind=engine)
    print("统一账户数据库表初始化完成")


if __name__ == "__main__":
    init_unified_db()
