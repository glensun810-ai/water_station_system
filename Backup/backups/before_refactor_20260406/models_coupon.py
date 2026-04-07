"""
Coupon Models - 优惠券数据模型
支持多种优惠类型和使用规则
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Index, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from main import Base


class Coupon(Base):
    """
    优惠券表
    
    支持两种优惠类型:
    1. discount - 折扣券 (如 95 折)
    2. fixed - 满减券 (如满 100 减 10)
    """
    __tablename__ = "coupons"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    coupon_code = Column(String(50), unique=True, nullable=False, index=True)  # 优惠券码
    name = Column(String(100), nullable=False)  # 优惠券名称
    
    # 优惠类型和值
    type = Column(String(20), nullable=False)  # 'discount' | 'fixed'
    value = Column(Float, nullable=False)  # 折扣值 (95 表示 95 折) 或固定金额
    
    # 使用条件
    min_amount = Column(Float, default=0.0)  # 最低消费金额
    max_discount = Column(Float, nullable=True)  # 最大优惠金额 (可选，防止过度优惠)
    
    # 适用范围
    applicable_products = Column(String, nullable=True)  # JSON 格式存储适用产品 ID 列表，NULL 表示通用
    applicable_modes = Column(String, nullable=True)  # JSON 格式存储适用模式 ['prepaid', 'credit']，NULL 表示通用
    
    # 有效期
    valid_from = Column(DateTime, nullable=False)
    valid_until = Column(DateTime, nullable=False)
    
    # 发放数量限制
    total_quantity = Column(Integer, default=0)  # 总发放数量，0 表示无限制
    issued_quantity = Column(Integer, default=0)  # 已发放数量
    used_quantity = Column(Integer, default=0)  # 已使用数量
    
    # 状态
    status = Column(String(20), default='active')  # 'active' | 'inactive' | 'exhausted'
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)
    
    # 索引优化
    __table_args__ = (
        Index('idx_coupon_status', 'status', 'valid_until'),
        Index('idx_coupon_code', 'coupon_code', 'status'),
    )
    
    def to_dict(self):
        """转换为字典"""
        import json
        return {
            'id': self.id,
            'coupon_code': self.coupon_code,
            'name': self.name,
            'type': self.type,
            'value': self.value,
            'min_amount': self.min_amount,
            'max_discount': self.max_discount,
            'applicable_products': json.loads(self.applicable_products) if self.applicable_products else None,
            'applicable_modes': json.loads(self.applicable_modes) if self.applicable_modes else None,
            'valid_from': self.valid_from.strftime('%Y-%m-%d %H:%M:%S') if self.valid_from else None,
            'valid_until': self.valid_until.strftime('%Y-%m-%d %H:%M:%S') if self.valid_until else None,
            'total_quantity': self.total_quantity,
            'issued_quantity': self.issued_quantity,
            'used_quantity': self.used_quantity,
            'status': self.status,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None
        }
    
    def is_valid(self) -> bool:
        """检查优惠券是否有效"""
        now = datetime.now()
        return (
            self.status == 'active' and
            self.valid_from <= now <= self.valid_until and
            (self.total_quantity == 0 or self.issued_quantity < self.total_quantity)
        )


class UserCoupon(Base):
    """
    用户优惠券表
    
    记录用户领取的优惠券及其使用状态
    """
    __tablename__ = "user_coupons"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    coupon_id = Column(Integer, ForeignKey("coupons.id"), nullable=False)
    
    # 优惠券码 (冗余字段，方便查询)
    coupon_code = Column(String(50), nullable=False)
    
    # 使用状态
    status = Column(String(20), default='unused')  # 'unused' | 'used' | 'expired'
    used_at = Column(DateTime, nullable=True)  # 使用时间
    order_id = Column(Integer, ForeignKey("unified_orders.id"), nullable=True)  # 使用的订单 ID
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    expires_at = Column(DateTime, nullable=False)  # 过期时间 (基于优惠券的有效期)
    
    # 关联关系
    user = relationship("User", foreign_keys=[user_id])
    coupon = relationship("Coupon", foreign_keys=[coupon_id])
    order = relationship("UnifiedOrder", foreign_keys=[order_id])
    
    # 索引优化
    __table_args__ = (
        Index('idx_user_status', 'user_id', 'status'),
        Index('idx_user_coupon', 'user_id', 'coupon_id', 'status'),
        Index('idx_expires', 'expires_at', 'status'),
    )
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'coupon_id': self.coupon_id,
            'coupon_code': self.coupon_code,
            'status': self.status,
            'used_at': self.used_at.strftime('%Y-%m-%d %H:%M:%S') if self.used_at else None,
            'order_id': self.order_id,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'expires_at': self.expires_at.strftime('%Y-%m-%d %H:%M:%S') if self.expires_at else None
        }
    
    def is_usable(self) -> bool:
        """检查用户优惠券是否可用"""
        now = datetime.now()
        return (
            self.status == 'unused' and
            now <= self.expires_at
        )
