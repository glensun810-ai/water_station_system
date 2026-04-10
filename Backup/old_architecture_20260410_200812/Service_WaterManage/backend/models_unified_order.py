"""
Unified Order Models - 统一订单数据模型
支持先用后付和先付后用两种支付模式的统一管理
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime

# 独立声明 Base，避免导入 main.py 引发循环依赖
Base = declarative_base()


class UnifiedOrder(Base):
    """统一订单表"""
    __tablename__ = "unified_orders"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    order_no = Column(String(50), unique=True, nullable=False, index=True)  # 订单号
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    
    # 订单基本信息
    quantity = Column(Integer, nullable=False)  # 总数量
    unit_price = Column(Float, nullable=False)  # 单价
    total_amount = Column(Float, nullable=False)  # 订单总金额
    
    # 支付信息
    payment_method = Column(String(20), nullable=False)  # 'credit' | 'prepaid'
    payment_status = Column(String(20), default='pending')  # 'pending' | 'paid' | 'refunded'
    
    # 预付模式专用字段
    prepaid_paid_qty = Column(Integer, default=0)  # 付费数量 (买赠中的付费部分)
    prepaid_gift_qty = Column(Integer, default=0)  # 赠送数量 (买赠中的赠送部分)
    
    # 优惠信息 (Phase 2 实现)
    coupon_id = Column(Integer, nullable=True)
    discount_amount = Column(Float, default=0.0)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.now, nullable=False, index=True)
    paid_at = Column(DateTime, nullable=True)
    
    # 关联关系（避免跨模块映射导致初始化依赖）
    # user/product 通过外键 ID 查询，不在此声明 relationship
    
    # 复合索引优化查询
    __table_args__ = (
        Index('idx_user_payment', 'user_id', 'payment_method'),
        Index('idx_user_status', 'user_id', 'payment_status'),
        Index('idx_created_payment', 'created_at', 'payment_method'),
    )
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'order_no': self.order_no,
            'user_id': self.user_id,
            'product_id': self.product_id,
            'quantity': self.quantity,
            'unit_price': self.unit_price,
            'total_amount': self.total_amount,
            'payment_method': self.payment_method,
            'payment_status': self.payment_status,
            'prepaid_paid_qty': self.prepaid_paid_qty,
            'prepaid_gift_qty': self.prepaid_gift_qty,
            'discount_amount': self.discount_amount,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'paid_at': self.paid_at.strftime('%Y-%m-%d %H:%M:%S') if self.paid_at else None
        }


class UnifiedTransaction(Base):
    """统一交易记录表"""
    __tablename__ = "unified_transactions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey("unified_orders.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    
    # 交易信息
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Float, nullable=False)
    total_amount = Column(Float, nullable=False)
    discount_amount = Column(Float, default=0.0)
    actual_amount = Column(Float, nullable=False)  # 实际支付金额
    
    # 支付明细 (JSON 格式存储详细信息)
    # 示例：{
    #     "credit_qty": 0,
    #     "prepaid_paid_qty": 9,
    #     "prepaid_gift_qty": 1,
    #     "coupon_discount": 5.0
    # }
    payment_details = Column(String, nullable=True)  # SQLite 用 TEXT 存储 JSON
    
    # 状态
    status = Column(String(20), default='completed')  # 'completed' | 'refunded'
    payment_method = Column(String(20), nullable=False)  # 'credit' | 'prepaid'
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.now, nullable=False, index=True)
    
    # 关联关系
    order = relationship("UnifiedOrder", foreign_keys=[order_id])
    # user/product 通过外键 ID 查询，不在此声明 relationship
    
    # 索引
    __table_args__ = (
        Index('idx_trans_user', 'user_id', 'created_at'),
        Index('idx_trans_payment', 'payment_method', 'status'),
    )
    
    def to_dict(self):
        """转换为字典"""
        import json
        return {
            'id': self.id,
            'order_id': self.order_id,
            'user_id': self.user_id,
            'product_id': self.product_id,
            'quantity': self.quantity,
            'unit_price': self.unit_price,
            'total_amount': self.total_amount,
            'discount_amount': self.discount_amount,
            'actual_amount': self.actual_amount,
            'payment_details': json.loads(self.payment_details) if self.payment_details else {},
            'status': self.status,
            'payment_method': self.payment_method,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }
