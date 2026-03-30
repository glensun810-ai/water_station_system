#!/usr/bin/env python3
"""
数据库迁移脚本 - 添加交易记录软删除功能和删除日志表
Migration: Add soft delete for transactions and delete logs table
"""

import sys
import os

# 添加 backend 目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, inspect
from sqlalchemy.orm import sessionmaker, declarative_base
from datetime import datetime

SQLALCHEMY_DATABASE_URL = "sqlite:///./waterms.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
Base = declarative_base()


class Transaction(Base):
    __tablename__ = "transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, default=1)
    actual_price = Column(Float)
    type = Column(String, default="pickup")
    status = Column(String, default="unsettled")
    settlement_applied = Column(Integer, default=0)
    note = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    
    # 新增软删除字段
    is_deleted = Column(Integer, default=0)
    deleted_at = Column(DateTime, nullable=True)
    deleted_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    delete_reason = Column(String, nullable=True)


class DeleteLog(Base):
    """删除操作审计日志表"""
    __tablename__ = "delete_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    operator_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    operator_name = Column(String, nullable=False)
    action = Column(String, nullable=False)
    target_type = Column(String, nullable=False)
    target_ids = Column(String, nullable=False)
    reason = Column(String, nullable=True)
    ip_address = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.now)


def migrate():
    """执行数据库迁移"""
    print("=" * 60)
    print("🔄 数据库迁移 - 交易记录软删除功能")
    print("=" * 60)
    
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()
    print(f"\n📋 当前数据库表：{existing_tables}")
    
    # 1. 创建 delete_logs 表（如果不存在）
    if "delete_logs" not in existing_tables:
        print("\n✅ 创建 delete_logs 表...")
        DeleteLog.__table__.create(engine)
        print("   ✓ delete_logs 表创建成功")
    else:
        print("\nℹ️  delete_logs 表已存在，跳过")
    
    # 2. 为 transactions 表添加软删除字段
    if "transactions" in existing_tables:
        print("\n📝 检查 transactions 表字段...")
        existing_columns = [col['name'] for col in inspector.get_columns('transactions')]
        print(f"   当前字段：{existing_columns}")
        
        # 需要添加的字段
        new_columns = ['is_deleted', 'deleted_at', 'deleted_by', 'delete_reason']
        
        with engine.connect() as conn:
            for col_name in new_columns:
                if col_name not in existing_columns:
                    print(f"   ➕ 添加字段：{col_name}")
                    if col_name == 'is_deleted':
                        conn.execute(f"ALTER TABLE transactions ADD COLUMN {col_name} INTEGER DEFAULT 0")
                    elif col_name == 'deleted_at':
                        conn.execute(f"ALTER TABLE transactions ADD COLUMN {col_name} DATETIME")
                    elif col_name == 'deleted_by':
                        conn.execute(f"ALTER TABLE transactions ADD COLUMN {col_name} INTEGER")
                    elif col_name == 'delete_reason':
                        conn.execute(f"ALTER TABLE transactions ADD COLUMN {col_name} TEXT")
                    print(f"   ✓ 字段 {col_name} 添加成功")
                else:
                    print(f"   ℹ️  字段 {col_name} 已存在，跳过")
            
            conn.commit()
    
    print("\n" + "=" * 60)
    print("✅ 数据库迁移完成！")
    print("=" * 60)
    print("\n📋 变更内容：")
    print("   1. ✓ 创建 delete_logs 表（删除操作审计日志）")
    print("   2. ✓ transactions 表新增 is_deleted 字段（软删除标记）")
    print("   3. ✓ transactions 表新增 deleted_at 字段（删除时间）")
    print("   4. ✓ transactions 表新增 deleted_by 字段（删除人 ID）")
    print("   5. ✓ transactions 表新增 delete_reason 字段（删除原因）")
    
    print("\n💡 使用说明：")
    print("   - 删除操作现在为软删除，数据不会被物理删除")
    print("   - 可通过 include_deleted=true 参数查看已删除记录")
    print("   - 所有删除操作都会记录在 delete_logs 表中")


if __name__ == "__main__":
    # 切换到 backend 目录
    os.chdir(os.path.join(os.path.dirname(__file__), 'backend'))
    migrate()
