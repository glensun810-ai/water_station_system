"""
数据库迁移脚本 - 添加新字段
Run: python migrate.py
"""

import sqlite3

DB_PATH = "waterms.db"


def migrate():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # 检查 transactions 表的字段
        cursor.execute("PRAGMA table_info(transactions)")
        columns_transactions = [col[1] for col in cursor.fetchall()]

        if "settlement_applied" not in columns_transactions:
            cursor.execute("""
                ALTER TABLE transactions
                ADD COLUMN settlement_applied INTEGER DEFAULT 0
            """)
            conn.commit()
            print("✓ 已添加 settlement_applied 字段到 transactions 表")
        else:
            print("✓ settlement_applied 字段已存在")

        # 检查 products 表的字段
        cursor.execute("PRAGMA table_info(products)")
        columns_products = [col[1] for col in cursor.fetchall()]

        if "is_active" not in columns_products:
            cursor.execute("""
                ALTER TABLE products
                ADD COLUMN is_active INTEGER DEFAULT 1
            """)
            conn.commit()
            print("✓ 已添加 is_active 字段到 products 表")
        else:
            print("✓ is_active 字段已存在")

        # 检查 office 表的字段
        cursor.execute("PRAGMA table_info(office)")
        columns_office = [col[1] for col in cursor.fetchall()]

        if "super_admin_id" not in columns_office:
            cursor.execute("""
                ALTER TABLE office
                ADD COLUMN super_admin_id INTEGER
            """)
            conn.commit()
            print("✓ 已添加 super_admin_id 字段到 office 表")
        else:
            print("✓ super_admin_id 字段已存在")

        print("\n迁移完成！")

    except Exception as e:
        print(f"✗ 迁移失败：{e}")
        conn.rollback()
    finally:
        conn.close()


if __name__ == "__main__":
    migrate()
