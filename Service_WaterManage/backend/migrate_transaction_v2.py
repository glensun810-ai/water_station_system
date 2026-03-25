"""
数据库迁移脚本 - 添加 TransactionV2 领用明细字段

用途：为 transactions_v2 表添加 paid_qty_deducted, gift_qty_deducted, financial_amount 字段
"""
import sqlite3
from pathlib import Path

# 数据库路径
DB_PATH = Path(__file__).parent / "waterms.db"


def migrate():
    """执行数据库迁移"""
    print(f"开始数据库迁移：{DB_PATH}")
    
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    try:
        # 检查表是否存在
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='transactions_v2'
        """)
        
        if not cursor.fetchone():
            print("❌ 错误：transactions_v2 表不存在")
            return False
        
        # 添加 paid_qty_deducted 字段
        try:
            cursor.execute("""
                ALTER TABLE transactions_v2 
                ADD COLUMN paid_qty_deducted INTEGER DEFAULT 0
            """)
            print("✓ 添加 paid_qty_deducted 字段成功")
        except sqlite3.OperationalError as e:
            if "duplicate column" in str(e).lower():
                print("⚠️  paid_qty_deducted 字段已存在，跳过")
            else:
                raise
        
        # 添加 gift_qty_deducted 字段
        try:
            cursor.execute("""
                ALTER TABLE transactions_v2 
                ADD COLUMN gift_qty_deducted INTEGER DEFAULT 0
            """)
            print("✓ 添加 gift_qty_deducted 字段成功")
        except sqlite3.OperationalError as e:
            if "duplicate column" in str(e).lower():
                print("⚠️  gift_qty_deducted 字段已存在，跳过")
            else:
                raise
        
        # 添加 financial_amount 字段
        try:
            cursor.execute("""
                ALTER TABLE transactions_v2 
                ADD COLUMN financial_amount FLOAT DEFAULT 0.0
            """)
            print("✓ 添加 financial_amount 字段成功")
        except sqlite3.OperationalError as e:
            if "duplicate column" in str(e).lower():
                print("⚠️  financial_amount 字段已存在，跳过")
            else:
                raise
        
        conn.commit()
        print("\n✅ 数据库迁移完成！")
        return True
        
    except Exception as e:
        conn.rollback()
        print(f"\n❌ 迁移失败：{e}")
        return False
        
    finally:
        conn.close()


def rollback():
    """回滚迁移（SQLite 不支持 DROP COLUMN，需要重建表）"""
    print("⚠️  SQLite 不支持直接删除列，如需回滚请手动处理")
    print("建议：从备份恢复数据库文件")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "rollback":
        rollback()
    else:
        success = migrate()
        sys.exit(0 if success else 1)
