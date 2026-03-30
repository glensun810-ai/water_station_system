"""
数据库迁移脚本 v3.0 - 预付费功能
Run: python migrate_prepaid.py
"""
import sqlite3
from datetime import datetime

DB_PATH = "waterms.db"

def migrate():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        print("开始数据库迁移 v3.0 - 预付费功能...")
        
        # 1. 创建预付订单表 prepaid_orders
        print("\n1. 创建预付订单表 prepaid_orders...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS prepaid_orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                total_qty INTEGER NOT NULL,
                used_qty INTEGER DEFAULT 0,
                unit_price DECIMAL(10,2) NOT NULL,
                total_amount DECIMAL(10,2) NOT NULL,
                discount_amount DECIMAL(10,2) DEFAULT 0,
                payment_status VARCHAR(20) DEFAULT 'unpaid',
                payment_method VARCHAR(20) DEFAULT 'offline',
                payment_at DATETIME,
                created_by INTEGER NOT NULL,
                confirmed_by INTEGER,
                note TEXT,
                is_active INTEGER DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (product_id) REFERENCES products(id),
                FOREIGN KEY (created_by) REFERENCES users(id),
                FOREIGN KEY (confirmed_by) REFERENCES users(id)
            )
        """)
        conn.commit()
        print("   ✓ prepaid_orders 表创建成功")

        # 2. 创建预付领取记录表 prepaid_pickups
        print("\n2. 创建预付领取记录表 prepaid_pickups...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS prepaid_pickups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL,
                pickup_qty INTEGER NOT NULL,
                picked_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                picked_by INTEGER NOT NULL,
                note TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (order_id) REFERENCES prepaid_orders(id),
                FOREIGN KEY (picked_by) REFERENCES users(id)
            )
        """)
        conn.commit()
        print("   ✓ prepaid_pickups 表创建成功")

        # 3. 创建索引优化查询性能
        print("\n3. 创建索引...")
        
        # 预付订单用户索引
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_prepaid_user 
            ON prepaid_orders(user_id, is_active)
        """)
        
        # 预付订单状态索引
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_prepaid_status 
            ON prepaid_orders(payment_status)
        """)
        
        # 预付领取订单索引
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_pickup_order 
            ON prepaid_pickups(order_id)
        """)
        
        conn.commit()
        print("   ✓ 索引创建成功")

        # 4. 添加通知表新类型
        print("\n4. 检查通知表...")
        cursor.execute("PRAGMA table_info(notifications)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'type' in columns:
            print("   ✓ notifications 表已存在，支持预付费通知类型")
        else:
            print("   ⚠ notifications 表结构异常")
        
        print("\n" + "="*60)
        print("✓ 数据库迁移 v3.0 完成！")
        print("="*60)
        print("\n新增功能:")
        print("  • 预付订单管理（prepaid_orders）")
        print("  • 预付领取记录（prepaid_pickups）")
        print("  • 支持预付费余额查询")
        print("  • 支持余量不足提醒")
        print("\n迁移时间:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    except Exception as e:
        print(f"\n✗ 迁移失败：{e}")
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    migrate()
