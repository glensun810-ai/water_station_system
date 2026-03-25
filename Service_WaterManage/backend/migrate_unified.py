"""
Database Migration Script - 统一账户架构迁移
创建新表结构：UserAccount, AccountWallet, SettlementBatch, TransactionV2, PromotionConfigV2
"""
import sqlite3
from datetime import datetime

DATABASE_PATH = "waterms.db"


def migrate_unified_schema():
    """迁移统一账户架构"""
    
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    print("开始迁移统一账户架构...")
    
    try:
        # 1. 创建 UserAccount 表
        print("创建 user_account 表...")
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_account (
            id INTEGER PRIMARY KEY,
            user_id INTEGER UNIQUE NOT NULL,
            balance_credit FLOAT DEFAULT 0.0,
            balance_prepaid FLOAT DEFAULT 0.0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
        """)
        
        # 2. 创建 AccountWallet 表
        print("创建 account_wallet 表...")
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS account_wallet (
            id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            wallet_type VARCHAR(20) NOT NULL,
            available_qty INTEGER DEFAULT 0,
            locked_qty INTEGER DEFAULT 0,
            total_consumed INTEGER DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (product_id) REFERENCES products(id),
            UNIQUE(user_id, product_id, wallet_type)
        )
        """)
        
        # 3. 创建 SettlementBatch 表
        print("创建 settlement_batch 表...")
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS settlement_batch (
            id INTEGER PRIMARY KEY,
            batch_no VARCHAR(50) UNIQUE NOT NULL,
            user_id INTEGER NOT NULL,
            transaction_ids TEXT NOT NULL,
            total_amount FLOAT NOT NULL,
            status VARCHAR(20) DEFAULT 'pending',
            confirmed_at DATETIME,
            confirmed_by INTEGER,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (confirmed_by) REFERENCES users(id)
        )
        """)
        
        # 4. 创建 TransactionV2 表（统一交易记录）
        print("创建 transactions_v2 表...")
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions_v2 (
            id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            wallet_id INTEGER,
            quantity INTEGER DEFAULT 1,
            unit_price FLOAT NOT NULL,
            actual_price FLOAT NOT NULL,
            mode VARCHAR(20) DEFAULT 'credit',
            wallet_type VARCHAR(20) DEFAULT 'credit',
            status VARCHAR(20) DEFAULT 'pending',
            settlement_batch_id INTEGER,
            discount_desc VARCHAR(200),
            free_qty INTEGER DEFAULT 0,
            note TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (product_id) REFERENCES products(id),
            FOREIGN KEY (wallet_id) REFERENCES account_wallet(id),
            FOREIGN KEY (settlement_batch_id) REFERENCES settlement_batch(id)
        )
        """)
        
        # 5. 创建 PromotionConfigV2 表（优惠配置 V2）
        print("创建 promotion_config_v2 表...")
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS promotion_config_v2 (
            id INTEGER PRIMARY KEY,
            product_id INTEGER NOT NULL,
            mode VARCHAR(20) NOT NULL DEFAULT 'credit',
            trigger_qty INTEGER NOT NULL DEFAULT 10,
            gift_qty INTEGER NOT NULL DEFAULT 0,
            discount_rate FLOAT DEFAULT 100.0,
            is_active INTEGER DEFAULT 1,
            description VARCHAR(200),
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (product_id) REFERENCES products(id)
        )
        """)
        
        # 创建索引
        print("创建索引...")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_wallet_user ON account_wallet(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_wallet_product ON account_wallet(product_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_txn_user ON transactions_v2(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_txn_product ON transactions_v2(product_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_txn_mode ON transactions_v2(mode)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_settlement_user ON settlement_batch(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_promo_config_product ON promotion_config_v2(product_id)")
        
        conn.commit()
        print("✓ 统一账户架构迁移完成！")
        
        # 显示创建的表
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%account%' OR name LIKE '%settlement%' OR name LIKE '%v2%'")
        tables = cursor.fetchall()
        print(f"\n创建的表：{[t[0] for t in tables]}")
        
    except Exception as e:
        conn.rollback()
        print(f"✗ 迁移失败：{e}")
        raise
    finally:
        conn.close()


def migrate_existing_data():
    """迁移现有数据到新表结构"""
    
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    print("\n开始迁移现有数据...")
    
    try:
        # 1. 从 PrepaidOrder 迁移预付余额到 AccountWallet
        print("迁移预付订单余额...")
        cursor.execute("""
        INSERT OR REPLACE INTO account_wallet (user_id, product_id, wallet_type, available_qty, created_at, updated_at)
        SELECT 
            user_id,
            product_id,
            'prepaid' as wallet_type,
            (total_qty - used_qty) as available_qty,
            created_at,
            CURRENT_TIMESTAMP
        FROM prepaid_orders
        WHERE payment_status = 'paid' 
          AND is_active = 1
          AND (total_qty - used_qty) > 0
        """)
        print(f"  ✓ 迁移了 {cursor.rowcount} 条预付余额记录")
        
        # 2. 初始化用户的信用余额（从 users 表）
        print("迁移用户信用余额...")
        cursor.execute("""
        INSERT OR REPLACE INTO user_account (user_id, balance_credit, balance_prepaid, created_at, updated_at)
        SELECT 
            id,
            COALESCE(balance_credit, 0) as balance_credit,
            0 as balance_prepaid,
            created_at,
            CURRENT_TIMESTAMP
        FROM users
        WHERE balance_credit > 0 OR id IN (SELECT DISTINCT user_id FROM account_wallet)
        """)
        print(f"  ✓ 迁移了 {cursor.rowcount} 条用户账户记录")
        
        # 3. 从旧的优惠配置表迁移到 V2
        print("迁移优惠配置...")
        cursor.execute("""
        INSERT OR IGNORE INTO promotion_config_v2 
            (product_id, mode, trigger_qty, gift_qty, discount_rate, is_active, created_at, updated_at)
        SELECT 
            product_id,
            'prepaid' as mode,
            trigger_qty,
            gift_qty,
            100.0 as discount_rate,
            is_active,
            created_at,
            CURRENT_TIMESTAMP
        FROM promotion_config
        WHERE is_active = 1
        """)
        print(f"  ✓ 迁移了 {cursor.rowcount} 条预付优惠配置")
        
        # 4. 为每个产品添加默认的信用优惠配置（标准价格，无优惠）
        print("添加默认信用优惠配置...")
        cursor.execute("""
        INSERT OR IGNORE INTO promotion_config_v2 
            (product_id, mode, trigger_qty, gift_qty, discount_rate, is_active, description, created_at, updated_at)
        SELECT 
            id,
            'credit' as mode,
            0 as trigger_qty,
            0 as gift_qty,
            100.0 as discount_rate,
            1,
            '标准价格，无优惠' as description,
            CURRENT_TIMESTAMP,
            CURRENT_TIMESTAMP
        FROM products
        """)
        print(f"  ✓ 添加了 {cursor.rowcount} 条信用优惠配置")
        
        conn.commit()
        print("\n✓ 数据迁移完成！")
        
    except Exception as e:
        conn.rollback()
        print(f"✗ 数据迁移失败：{e}")
        raise
    finally:
        conn.close()


def verify_migration():
    """验证迁移结果"""
    
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    print("\n验证迁移结果...")
    
    try:
        # 检查 UserAccount
        cursor.execute("SELECT COUNT(*) as count FROM user_account")
        count = cursor.fetchone()['count']
        print(f"  UserAccount: {count} 条记录")
        
        # 检查 AccountWallet
        cursor.execute("SELECT COUNT(*) as count FROM account_wallet")
        count = cursor.fetchone()['count']
        print(f"  AccountWallet: {count} 条记录")
        
        # 检查 PromotionConfigV2
        cursor.execute("SELECT COUNT(*) as count FROM promotion_config_v2")
        count = cursor.fetchone()['count']
        print(f"  PromotionConfigV2: {count} 条记录")
        
        # 显示示例数据
        print("\n示例用户账户:")
        cursor.execute("""
        SELECT ua.*, u.name, u.department 
        FROM user_account ua 
        JOIN users u ON ua.user_id = u.id 
        LIMIT 3
        """)
        for row in cursor.fetchall():
            print(f"  - {row['name']} ({row['department']}): 信用={row['balance_credit']}, 预付={row['balance_prepaid']}")
        
        print("\n示例钱包:")
        cursor.execute("""
        SELECT aw.*, u.name, p.name as product_name 
        FROM account_wallet aw 
        JOIN users u ON aw.user_id = u.id 
        JOIN products p ON aw.product_id = p.id 
        LIMIT 3
        """)
        for row in cursor.fetchall():
            print(f"  - {row['name']} - {row['product_name']} ({row['wallet_type']}): 可用={row['available_qty']}")
        
        print("\n优惠配置:")
        cursor.execute("""
        SELECT pc.*, p.name as product_name 
        FROM promotion_config_v2 pc 
        JOIN products p ON pc.product_id = p.id 
        LIMIT 5
        """)
        for row in cursor.fetchall():
            desc = f"买{row['trigger_qty']}赠{row['gift_qty']}" if row['trigger_qty'] > 0 else "标准价格"
            print(f"  - {row['product_name']} ({row['mode']}): {desc}")
        
    except Exception as e:
        print(f"✗ 验证失败：{e}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    print("=" * 60)
    print("统一账户架构迁移脚本")
    print("=" * 60)
    
    # Step 1: 创建表结构
    migrate_unified_schema()
    
    # Step 2: 迁移数据
    migrate_existing_data()
    
    # Step 3: 验证
    verify_migration()
    
    print("\n" + "=" * 60)
    print("迁移完成！")
    print("=" * 60)
