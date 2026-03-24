"""
数据库迁移脚本 v2.0 - 双模式业务支持
Run: python migrate_v2.py
"""
import sqlite3
from datetime import datetime

DB_PATH = "waterms.db"

def migrate():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        print("开始数据库迁移 v2.0...")
        
        # 1. 创建优惠配置表 promotion_config
        print("\n1. 创建优惠配置表 promotion_config...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS promotion_config (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER NOT NULL,
                mode VARCHAR(20) NOT NULL DEFAULT 'pay_later',
                trigger_qty INTEGER NOT NULL DEFAULT 10,
                gift_qty INTEGER NOT NULL DEFAULT 0,
                discount_rate DECIMAL(5,2) DEFAULT 100,
                is_active INTEGER DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (product_id) REFERENCES products(id)
            )
        """)
        conn.commit()
        print("   ✓ promotion_config 表创建成功")

        # 2. 检查并添加 transactions 表的新字段
        print("\n2. 扩展 transactions 表字段...")
        cursor.execute("PRAGMA table_info(transactions)")
        columns_transactions = [col[1] for col in cursor.fetchall()]

        # 添加 mode 字段
        if "mode" not in columns_transactions:
            cursor.execute("""
                ALTER TABLE transactions
                ADD COLUMN mode VARCHAR(20) DEFAULT 'pay_later'
            """)
            conn.commit()
            print("   ✓ 已添加 mode 字段")
        else:
            print("   ✓ mode 字段已存在")

        # 添加 reserved_qty 字段
        if "reserved_qty" not in columns_transactions:
            cursor.execute("""
                ALTER TABLE transactions
                ADD COLUMN reserved_qty INTEGER DEFAULT 0
            """)
            conn.commit()
            print("   ✓ 已添加 reserved_qty 字段")
        else:
            print("   ✓ reserved_qty 字段已存在")

        # 添加 used_qty 字段
        if "used_qty" not in columns_transactions:
            cursor.execute("""
                ALTER TABLE transactions
                ADD COLUMN used_qty INTEGER DEFAULT 0
            """)
            conn.commit()
            print("   ✓ 已添加 used_qty 字段")
        else:
            print("   ✓ used_qty 字段已存在")

        # 添加 payment_status 字段
        if "payment_status" not in columns_transactions:
            cursor.execute("""
                ALTER TABLE transactions
                ADD COLUMN payment_status VARCHAR(20) DEFAULT 'unpaid'
            """)
            conn.commit()
            print("   ✓ 已添加 payment_status 字段")
        else:
            print("   ✓ payment_status 字段已存在")

        # 3. 创建预定领取记录表 reservation_pickups
        print("\n3. 创建预定领取记录表 reservation_pickups...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reservation_pickups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                reservation_id INTEGER NOT NULL,
                pickup_qty INTEGER NOT NULL,
                picked_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                picked_by INTEGER NOT NULL,
                status VARCHAR(20) DEFAULT 'completed',
                FOREIGN KEY (reservation_id) REFERENCES transactions(id),
                FOREIGN KEY (picked_by) REFERENCES users(id)
            )
        """)
        conn.commit()
        print("   ✓ reservation_pickups 表创建成功")

        # 4. 初始化现有产品的优惠配置
        print("\n4. 初始化现有产品的优惠配置...")
        cursor.execute("SELECT id, promo_threshold, promo_gift FROM products WHERE is_active = 1")
        products = cursor.fetchall()
        
        configs_created = 0
        for product_id, threshold, gift in products:
            # 先用后付模式（默认无优惠）
            cursor.execute("""
                INSERT INTO promotion_config (product_id, mode, trigger_qty, gift_qty, discount_rate, is_active)
                VALUES (?, 'pay_later', ?, 0, 100, 1)
            """, (product_id, threshold))
            
            # 先付后用模式（享受买赠优惠）
            cursor.execute("""
                INSERT INTO promotion_config (product_id, mode, trigger_qty, gift_qty, discount_rate, is_active)
                VALUES (?, 'prepay', ?, ?, 100, 1)
            """, (product_id, threshold, gift))
            
            configs_created += 2
        
        conn.commit()
        print(f"   ✓ 已创建 {configs_created} 条优惠配置记录")

        # 5. 更新现有交易记录的 mode 字段
        print("\n5. 更新现有交易记录的模式...")
        cursor.execute("""
            UPDATE transactions 
            SET mode = 'pay_later', 
                payment_status = CASE 
                    WHEN status = 'settled' THEN 'paid'
                    ELSE 'unpaid'
                END
            WHERE mode IS NULL OR mode = ''
        """)
        conn.commit()
        print("   ✓ 现有交易记录已更新")

        print("\n" + "="*50)
        print("✓ 数据库迁移 v2.0 完成！")
        print("="*50)
        print("\n新增功能:")
        print("  • 支持先用后付和先付后用两种业务模式")
        print("  • 支持按模式配置不同的优惠策略")
        print("  • 支持预定和分次领取功能")
        print("\n迁移时间:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    except Exception as e:
        print(f"\n✗ 迁移失败：{e}")
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    migrate()
