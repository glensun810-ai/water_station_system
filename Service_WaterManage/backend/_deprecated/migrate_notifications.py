"""
数据库迁移脚本 - 添加消息通知表
运行：python migrate_notifications.py
"""
import sqlite3
from datetime import datetime

DATABASE_URL = "waterms.db"

def migrate():
    conn = sqlite3.connect(DATABASE_URL)
    cursor = conn.cursor()
    
    # 创建通知表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            type TEXT DEFAULT 'info',
            is_read INTEGER DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)
    
    # 创建索引
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_notifications_user_id ON notifications(user_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_notifications_is_read ON notifications(is_read)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_notifications_created_at ON notifications(created_at)")
    
    conn.commit()
    conn.close()
    
    print("✅ 消息通知表创建成功！")
    print("   - notifications 表已创建")
    print("   - 索引已建立：user_id, is_read, created_at")

if __name__ == "__main__":
    migrate()
