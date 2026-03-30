"""
Migration script to add manager and configured_count fields to office_account table
添加负责人和配置人数字段到办公室账户表
"""

import sqlite3

DATABASE_PATH = "waterms.db"


def migrate():
    """添加新字段到 office_account 表"""
    
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # 检查字段是否已存在
    cursor.execute("PRAGMA table_info(office_account)")
    columns = [col[1] for col in cursor.fetchall()]
    
    # 添加 manager_name 字段
    if 'manager_name' not in columns:
        cursor.execute("""
            ALTER TABLE office_account
            ADD COLUMN manager_name VARCHAR(100)
        """)
        print("✓ Added manager_name column")
    else:
        print("✓ manager_name column already exists")
    
    # 添加 manager_id 字段
    if 'manager_id' not in columns:
        cursor.execute("""
            ALTER TABLE office_account
            ADD COLUMN manager_id INTEGER
        """)
        print("✓ Added manager_id column")
    else:
        print("✓ manager_id column already exists")
    
    # 添加 configured_count 字段
    if 'configured_count' not in columns:
        cursor.execute("""
            ALTER TABLE office_account
            ADD COLUMN configured_count INTEGER DEFAULT 0
        """)
        print("✓ Added configured_count column")
    else:
        print("✓ configured_count column already exists")
    
    conn.commit()
    conn.close()
    
    print("\n✓ Migration completed successfully!")
    print("✓ 数据库迁移完成!")


if __name__ == "__main__":
    migrate()
