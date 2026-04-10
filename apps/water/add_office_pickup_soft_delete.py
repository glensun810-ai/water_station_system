"""
为 office_pickup 表添加软删除字段的迁移脚本
部署到生产环境时执行
"""
import sqlite3
from datetime import datetime

def migrate():
    conn = sqlite3.connect('waterms.db')
    cur = conn.cursor()
    
    # 检查字段是否已存在
    cur.execute("PRAGMA table_info(office_pickup)")
    columns = [col[1] for col in cur.fetchall()]
    
    if 'is_deleted' not in columns:
        cur.execute("ALTER TABLE office_pickup ADD COLUMN is_deleted INTEGER DEFAULT 0")
        print("✅ Added is_deleted column")
    
    if 'deleted_at' not in columns:
        cur.execute("ALTER TABLE office_pickup ADD COLUMN deleted_at DATETIME")
        print("✅ Added deleted_at column")
    
    if 'deleted_by' not in columns:
        cur.execute("ALTER TABLE office_pickup ADD COLUMN deleted_by INTEGER")
        print("✅ Added deleted_by column")
    
    if 'delete_reason' not in columns:
        cur.execute("ALTER TABLE office_pickup ADD COLUMN delete_reason VARCHAR(500)")
        print("✅ Added delete_reason column")
    
    conn.commit()
    
    # 验证
    cur.execute("PRAGMA table_info(office_pickup)")
    new_columns = [col[1] for col in cur.fetchall()]
    print(f"\n✅ 当前 office_pickup 表共有 {len(new_columns)} 个字段")
    
    conn.close()
    print("\n✅ Migration completed successfully")

if __name__ == "__main__":
    migrate()
