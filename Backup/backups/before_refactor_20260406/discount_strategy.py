"""
Discount Strategy Module - 优惠策略模块
实现策略模式，支持不同业务模式的不同优惠计算
"""
from abc import ABC, abstractmethod
from typing import Dict, Tuple, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime


class ProductInfo:
    """产品信息数据类"""
    def __init__(self, id: int, name: str, price: float, specification: str = '', unit: str = ''):
        self.id = id
        self.name = name
        self.price = price
        self.specification = specification
        self.unit = unit


def get_product(db: Session, product_id: int) -> Optional[ProductInfo]:
    """获取产品信息"""
    result = db.execute(
        text("SELECT id, name, price, specification, unit FROM products WHERE id = :id"),
        {"id": product_id}
    ).fetchone()
    
    if not result:
        return None
    
    return ProductInfo(
        id=result[0],
        name=result[1],
        price=result[2],
        specification=result[3] or '',
        unit=result[4] or 'unit'
    )


class DiscountStrategy(ABC):
    """优惠策略基类"""

    @abstractmethod
    def calculate(self, db: Session, product_id: int, quantity: int, user_id: int = None) -> Dict:
        """
        计算优惠后的价格和数量
        
        Args:
            db: 数据库会话
            product_id: 产品 ID
            quantity: 购买数量
            user_id: 用户 ID（用于查询历史交易）
            
        Returns:
            dict: {
                'unit_price': 单价,
                'paid_qty': 付费数量,
                'free_qty': 免费数量,
                'total_price': 总金额,
                'discount_desc': 优惠描述
            }
        """
        pass


class CreditDiscountStrategy(DiscountStrategy):
    """
    先用后付优惠策略：标准价格，无优惠
    
    信用模式采用标准价格，不享受买赠优惠
    """

    def calculate(self, db: Session, product_id: int, quantity: int, user_id: int = None) -> Dict:
        product = get_product(db, product_id)
        if not product:
            raise ValueError(f"产品不存在：{product_id}")
        
        unit_price = product.price
        total_price = unit_price * quantity
        
        return {
            'unit_price': unit_price,
            'paid_qty': quantity,
            'free_qty': 0,
            'total_price': total_price,
            'discount_desc': '标准价格（先用后付）'
        }


class PrepaidDiscountStrategy(DiscountStrategy):
    """
    先付后用优惠策略：买 N 赠 M 优惠
    
    预付模式享受买赠优惠，根据历史交易记录计算免费数量
    """

    def calculate(self, db: Session, product_id: int, quantity: int, user_id: int = None) -> Dict:
        product = get_product(db, product_id)
        if not product:
            raise ValueError(f"产品不存在：{product_id}")
        
        # 获取优惠配置
        from models_unified import PromotionConfigV2, TransactionV2
        
        config = db.query(PromotionConfigV2).filter(
            PromotionConfigV2.product_id == product_id,
            PromotionConfigV2.mode == 'prepaid',
            PromotionConfigV2.is_active == 1
        ).first()
        
        if not config or config.trigger_qty <= 0:
            # 没有优惠配置，返回原价
            return {
                'unit_price': product.price,
                'paid_qty': quantity,
                'free_qty': 0,
                'total_price': product.price * quantity,
                'discount_desc': '标准价格'
            }
        
        # 计算历史交易次数（用于确定当前在买赠周期中的位置）
        if user_id:
            historical_count = db.query(TransactionV2).filter(
                TransactionV2.user_id == user_id,
                TransactionV2.product_id == product_id,
                TransactionV2.mode == 'prepaid',
                TransactionV2.status != 'cancelled'
            ).count()
        else:
            historical_count = 0
        
        # 买 N 赠 M 计算
        cycle = config.trigger_qty + config.gift_qty  # 一个完整周期的数量
        
        # 计算免费数量
        free_items = 0
        for i in range(quantity):
            position_in_cycle = (historical_count + i + 1) % cycle
            if position_in_cycle == 0:  # 每个周期的最后一个是免费的
                free_items += 1
        
        paid_items = quantity - free_items
        unit_price = product.price
        total_price = unit_price * paid_items
        
        # 构建优惠描述
        if free_items > 0:
            discount_desc = f'买{config.trigger_qty}赠{config.gift_qty}: {free_items}件免费'
        else:
            discount_desc = f'买{config.trigger_qty}赠{config.gift_qty}优惠中'
        
        return {
            'unit_price': unit_price,
            'paid_qty': paid_items,
            'free_qty': free_items,
            'total_price': total_price,
            'discount_desc': discount_desc
        }


class DiscountContext:
    """
    优惠策略上下文
    
    根据业务模式选择对应的优惠策略
    """
    
    def __init__(self):
        self.strategies = {
            'credit': CreditDiscountStrategy(),
            'prepaid': PrepaidDiscountStrategy()
        }
    
    def calculate_discount(self, db: Session, product_id: int, quantity: int, 
                          mode: str, user_id: int = None) -> Dict:
        """
        根据模式计算优惠
        
        Args:
            db: 数据库会话
            product_id: 产品 ID
            quantity: 购买数量
            mode: 业务模式 ('credit' 或 'prepaid')
            user_id: 用户 ID
            
        Returns:
            dict: 优惠计算结果
        """
        strategy = self.strategies.get(mode)
        if not strategy:
            raise ValueError(f"未知模式：{mode}")
        
        return strategy.calculate(db, product_id, quantity, user_id)


# 全局单例
discount_context = DiscountContext()


def calculate_pickup_price(db: Session, user_id: int, product_id: int, quantity: int, 
                           mode: str = 'credit') -> Dict:
    """
    计算领取价格的便捷函数
    
    Args:
        db: 数据库会话
        user_id: 用户 ID
        product_id: 产品 ID
        quantity: 领取数量
        mode: 业务模式
        
    Returns:
        dict: 价格计算结果
    """
    return discount_context.calculate_discount(db, product_id, quantity, mode, user_id)
