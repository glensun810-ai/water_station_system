"""
Database Migration Script - Unified Order System
统一订单系统数据库迁移脚本
"""
import sys
sys.path.append('backend')

from main import engine, Base
from models_unified_order import UnifiedOrder, UnifiedTransaction

def create_tables():
    """创建统一订单系统的数据表"""
    print("=" * 60)
    print("开始创建统一订单系统数据表...")
    print("=" * 60)
    
    # 只创建统一订单相关的表
    UnifiedOrder.__table__.create(bind=engine)
    print("✅ 表 unified_orders 创建成功")
    
    UnifiedTransaction.__table__.create(bind=engine)
    print("✅ 表 unified_transactions 创建成功")
    
    print("=" * 60)
    print("所有表创建完成!")
    print("=" * 60)


if __name__ == "__main__":
    create_tables()
