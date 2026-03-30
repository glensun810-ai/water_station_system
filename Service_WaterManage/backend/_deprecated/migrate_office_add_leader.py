"""
Migration script to add leader_name and water_user_count fields to office table
添加负责人和配置人数字段到办公室表
"""

import sqlite3

DATABASE_PATH = "waterms.db"


def migrate():
    """添加新字段到 office 表"""
    
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # 检查字段是否已存在
    cursor.execute("PRAGMA table_info(office)")
    columns = [col[1] for col in cursor.fetchall()]
    
    # 添加 leader_name 字段
    if 'leader_name' not in columns:
        cursor.execute("""
            ALTER TABLE office
            ADD COLUMN leader_name VARCHAR(100)
        """)
        print("✓ Added leader_name column")
    else:
        print("✓ leader_name column already exists")
    
    # 添加 water_user_count 字段
    if 'water_user_count' not in columns:
        cursor.execute("""
            ALTER TABLE office
            ADD COLUMN water_user_count INTEGER DEFAULT 0
        """)
        print("✓ Added water_user_count column")
    else:
        print("✓ water_user_count column already exists")
    
    conn.commit()
    conn.close()
    
    print("\n✓ Migration completed successfully!")
    print("✓ 数据库迁移完成!")


if __name__ == "__main__":
    migrate()
