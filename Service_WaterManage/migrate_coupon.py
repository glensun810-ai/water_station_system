"""
Database Migration Script - Coupon System
优惠券系统数据库迁移脚本
"""
import sys
sys.path.append('backend')

from main import engine, Base
from models_coupon import Coupon, UserCoupon

def create_tables():
    """创建优惠券系统的数据表"""
    print("=" * 60)
    print("开始创建优惠券系统数据表...")
    print("=" * 60)
    
    # 只创建优惠券相关的表
    Coupon.__table__.create(bind=engine)
    print("✅ 表 coupons 创建成功")
    
    UserCoupon.__table__.create(bind=engine)
    print("✅ 表 user_coupons 创建成功")
    
    print("=" * 60)
    print("所有表创建完成!")
    print("=" * 60)


if __name__ == "__main__":
    create_tables()
