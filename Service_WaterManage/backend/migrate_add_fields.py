"""
数据库迁移脚本 - 添加 account_wallet 表缺失的字段
"""
import sqlite3

DB_PATH = "waterms.db"

def migrate():
    """执行数据库迁移"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 检查 paid_qty 字段是否存在
    cursor.execute("PRAGMA table_info(account_wallet)")
    columns = [desc[1] for desc in cursor.fetchall()]
    
    print("当前 account_wallet 表的字段:")
    for col in columns:
        print(f"  - {col}")
    
    # 添加缺失的字段
    if 'paid_qty' not in columns:
        print("\n添加 paid_qty 字段...")
        cursor.execute('''
            ALTER TABLE account_wallet 
            ADD COLUMN paid_qty INTEGER DEFAULT 0
        ''')
        print("✅ paid_qty 字段添加成功")
    else:
        print("\n⚠️  paid_qty 字段已存在")
    
    if 'free_qty' not in columns:
        print("添加 free_qty 字段...")
        cursor.execute('''
            ALTER TABLE account_wallet 
            ADD COLUMN free_qty INTEGER DEFAULT 0
        ''')
        print("✅ free_qty 字段添加成功")
    else:
        print("⚠️  free_qty 字段已存在")
    
    # 提交更改
    conn.commit()
    conn.close()
    
    print("\n✅ 数据库迁移完成!")
    print("📁 数据库文件:", DB_PATH)

if __name__ == "__main__":
    migrate()
