"""
Complete Data Migration Script - 完整数据迁移脚本
迁移现有数据到统一账户架构，支持增量迁移和回滚
"""
import sqlite3
import json
from datetime import datetime
from typing import Dict, List, Optional
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

DATABASE_PATH = "waterms.db"
BACKUP_PATH = f"waterms_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"


class DataMigration:
    """数据迁移服务"""
    
    def __init__(self, db_path: str = DATABASE_PATH):
        self.db_path = db_path
        self.stats = {
            'start_time': None,
            'end_time': None,
            'users_migrated': 0,
            'wallets_migrated': 0,
            'transactions_migrated': 0,
            'orders_migrated': 0,
            'errors': []
        }
    
    def get_connection(self) -> sqlite3.Connection:
        """获取数据库连接"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def backup_database(self) -> str:
        """备份数据库"""
        import shutil
        try:
            shutil.copy(self.db_path, BACKUP_PATH)
            logger.info(f"✓ 数据库已备份到：{BACKUP_PATH}")
            return BACKUP_PATH
        except Exception as e:
            logger.error(f"✗ 数据库备份失败：{e}")
            raise
    
    def create_tables(self):
        """创建新表结构"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        logger.info("开始创建表结构...")
        
        try:
            # 1. user_account
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_account (
                id INTEGER PRIMARY KEY,
                user_id INTEGER UNIQUE NOT NULL,
                balance_credit FLOAT DEFAULT 0.0,
                balance_prepaid FLOAT DEFAULT 0.0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """)
            
            # 2. account_wallet
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
                UNIQUE(user_id, product_id, wallet_type)
            )
            """)
            
            # 3. settlement_batch
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
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """)
            
            # 4. transactions_v2
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
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """)
            
            # 5. promotion_config_v2
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
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """)
            
            # 创建索引
            logger.info("创建索引...")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_wallet_user ON account_wallet(user_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_wallet_product ON account_wallet(product_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_wallet_type ON account_wallet(wallet_type)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_txn_user ON transactions_v2(user_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_txn_product ON transactions_v2(product_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_txn_mode ON transactions_v2(mode)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_settlement_user ON settlement_batch(user_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_settlement_status ON settlement_batch(status)")
            
            conn.commit()
            logger.info("✓ 表结构创建完成")
            
        except Exception as e:
            conn.rollback()
            logger.error(f"✗ 表结构创建失败：{e}")
            raise
        finally:
            conn.close()
    
    def migrate_users(self) -> int:
        """迁移用户账户"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        logger.info("开始迁移用户账户...")
        
        try:
            # 迁移所有用户的信用余额
            cursor.execute("""
            INSERT OR REPLACE INTO user_account (user_id, balance_credit, balance_prepaid, created_at, updated_at)
            SELECT 
                id,
                COALESCE(balance_credit, 0) as balance_credit,
                0 as balance_prepaid,
                COALESCE(created_at, CURRENT_TIMESTAMP),
                CURRENT_TIMESTAMP
            FROM users
            WHERE is_active = 1
            """)
            
            migrated_count = cursor.rowcount
            conn.commit()
            
            logger.info(f"✓ 迁移用户账户完成：{migrated_count} 条")
            self.stats['users_migrated'] = migrated_count
            return migrated_count
            
        except Exception as e:
            conn.rollback()
            logger.error(f"✗ 用户账户迁移失败：{e}")
            self.stats['errors'].append(f'users: {str(e)}')
            return 0
        finally:
            conn.close()
    
    def migrate_prepaid_orders(self) -> int:
        """迁移预付订单到钱包"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        logger.info("开始迁移预付订单到钱包...")
        
        try:
            # 聚合每个用户每个产品的预付余额
            cursor.execute("""
            INSERT OR REPLACE INTO account_wallet 
            (user_id, product_id, wallet_type, available_qty, locked_qty, total_consumed, created_at, updated_at)
            SELECT 
                user_id,
                product_id,
                'prepaid' as wallet_type,
                SUM(total_qty - used_qty) as available_qty,
                0 as locked_qty,
                SUM(used_qty) as total_consumed,
                MIN(created_at),
                CURRENT_TIMESTAMP
            FROM prepaid_orders
            WHERE payment_status = 'paid' AND is_active = 1
            GROUP BY user_id, product_id
            HAVING SUM(total_qty - used_qty) > 0
            """)
            
            migrated_count = cursor.rowcount
            conn.commit()
            
            logger.info(f"✓ 迁移预付订单到钱包完成：{migrated_count} 条")
            self.stats['wallets_migrated'] = migrated_count
            return migrated_count
            
        except Exception as e:
            conn.rollback()
            logger.error(f"✗ 预付订单迁移失败：{e}")
            self.stats['errors'].append(f'prepaid_orders: {str(e)}')
            return 0
        finally:
            conn.close()
    
    def migrate_transactions(self, batch_size: int = 1000) -> int:
        """迁移交易记录到 V2 表"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        logger.info("开始迁移交易记录...")
        
        try:
            # 分批迁移
            offset = 0
            total_migrated = 0
            
            while True:
                cursor.execute("""
                INSERT INTO transactions_v2 
                (user_id, product_id, quantity, unit_price, actual_price, mode, wallet_type, status,
                 discount_desc, free_qty, note, created_at, updated_at)
                SELECT 
                    user_id,
                    product_id,
                    quantity,
                    CASE WHEN quantity > 0 THEN actual_price / quantity ELSE 0 END as unit_price,
                    actual_price,
                    CASE WHEN mode = 'prepay' THEN 'prepaid' ELSE 'credit' END as mode,
                    CASE WHEN mode = 'prepay' THEN 'prepaid' ELSE 'credit' END as wallet_type,
                    CASE WHEN status = 'settled' THEN 'settled' ELSE 'pending' END as status,
                    note as discount_desc,
                    0 as free_qty,
                    note,
                    created_at,
                    CURRENT_TIMESTAMP
                FROM transactions
                WHERE is_deleted = 0
                ORDER BY created_at DESC
                LIMIT :batch_size OFFSET :offset
                """, {"batch_size": batch_size, "offset": offset})
                
                migrated_count = cursor.rowcount
                conn.commit()
                
                if migrated_count == 0:
                    break
                
                total_migrated += migrated_count
                offset += batch_size
                logger.info(f"  已迁移 {total_migrated} 条交易记录...")
            
            logger.info(f"✓ 迁移交易记录完成：{total_migrated} 条")
            self.stats['transactions_migrated'] = total_migrated
            return total_migrated
            
        except Exception as e:
            conn.rollback()
            logger.error(f"✗ 交易记录迁移失败：{e}")
            self.stats['errors'].append(f'transactions: {str(e)}')
            return 0
        finally:
            conn.close()
    
    def migrate_promotion_configs(self) -> int:
        """迁移优惠配置"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        logger.info("开始迁移优惠配置...")
        
        try:
            # 迁移旧的优惠配置到 prepaid 模式
            cursor.execute("""
            INSERT OR IGNORE INTO promotion_config_v2
            (product_id, mode, trigger_qty, gift_qty, discount_rate, is_active, description, created_at, updated_at)
            SELECT 
                product_id,
                'prepaid' as mode,
                trigger_qty,
                gift_qty,
                100.0 as discount_rate,
                is_active,
                '买' || trigger_qty || '赠' || gift_qty as description,
                created_at,
                CURRENT_TIMESTAMP
            FROM promotion_config
            WHERE is_active = 1
            """)
            
            prepaid_count = cursor.rowcount
            
            # 为每个产品添加 credit 模式配置（标准价格）
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
            
            credit_count = cursor.rowcount
            conn.commit()
            
            total_count = prepaid_count + credit_count
            logger.info(f"✓ 迁移优惠配置完成：{total_count} 条 (prepaid={prepaid_count}, credit={credit_count})")
            self.stats['orders_migrated'] = total_count
            return total_count
            
        except Exception as e:
            conn.rollback()
            logger.error(f"✗ 优惠配置迁移失败：{e}")
            self.stats['errors'].append(f'promotion_config: {str(e)}')
            return 0
        finally:
            conn.close()
    
    def verify_migration(self) -> Dict:
        """验证迁移结果"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        logger.info("开始验证迁移结果...")
        
        try:
            verification = {}
            
            # 1. 验证用户账户
            cursor.execute("SELECT COUNT(*) FROM user_account")
            verification['user_accounts'] = cursor.fetchone()[0]
            
            # 2. 验证钱包
            cursor.execute("SELECT COUNT(*) FROM account_wallet")
            verification['wallets'] = cursor.fetchone()[0]
            
            # 3. 验证交易记录 V2
            cursor.execute("SELECT COUNT(*) FROM transactions_v2")
            verification['transactions_v2'] = cursor.fetchone()[0]
            
            # 4. 验证优惠配置 V2
            cursor.execute("SELECT COUNT(*) FROM promotion_config_v2")
            verification['promotion_config_v2'] = cursor.fetchone()[0]
            
            # 5. 验证数据一致性
            issues = []
            
            # 检查是否有用户没有账户
            cursor.execute("""
            SELECT COUNT(*) FROM users u
            LEFT JOIN user_account ua ON u.id = ua.user_id
            WHERE ua.user_id IS NULL AND u.is_active = 1
            """)
            users_without_account = cursor.fetchone()[0]
            if users_without_account > 0:
                issues.append(f'{users_without_account} 个活跃用户没有账户')
            
            verification['issues'] = issues
            verification['is_valid'] = len(issues) == 0
            
            logger.info(f"✓ 验证完成：{verification}")
            return verification
            
        except Exception as e:
            logger.error(f"✗ 验证失败：{e}")
            return {'error': str(e)}
        finally:
            conn.close()
    
    def rollback(self):
        """回滚迁移（从备份恢复）"""
        import shutil
        import os
        
        logger.info("开始回滚迁移...")
        
        try:
            # 查找最近的备份
            backup_files = [f for f in os.listdir('.') if f.startswith('waterms_backup_') and f.endswith('.db')]
            
            if not backup_files:
                logger.error("✗ 未找到备份文件")
                return False
            
            latest_backup = max(backup_files)
            shutil.copy(latest_backup, self.db_path)
            
            logger.info(f"✓ 已从备份 {latest_backup} 恢复")
            return True
            
        except Exception as e:
            logger.error(f"✗ 回滚失败：{e}")
            return False
    
    def run_full_migration(self, backup: bool = True) -> Dict:
        """运行完整迁移"""
        self.stats['start_time'] = datetime.now()
        
        logger.info("=" * 60)
        logger.info("开始完整数据迁移")
        logger.info("=" * 60)
        
        try:
            # 1. 备份数据库
            if backup:
                self.backup_database()
            
            # 2. 创建表结构
            self.create_tables()
            
            # 3. 迁移数据
            self.migrate_users()
            self.migrate_prepaid_orders()
            self.migrate_transactions()
            self.migrate_promotion_configs()
            
            # 4. 验证迁移
            verification = self.verify_migration()
            
            self.stats['end_time'] = datetime.now()
            self.stats['verification'] = verification
            
            # 5. 输出统计
            duration = (self.stats['end_time'] - self.stats['start_time']).total_seconds()
            
            logger.info("=" * 60)
            logger.info("迁移完成统计")
            logger.info("=" * 60)
            logger.info(f"耗时：{duration:.2f} 秒")
            logger.info(f"用户账户：{self.stats['users_migrated']}")
            logger.info(f"钱包：{self.stats['wallets_migrated']}")
            logger.info(f"交易记录：{self.stats['transactions_migrated']}")
            logger.info(f"优惠配置：{self.stats['orders_migrated']}")
            logger.info(f"错误：{len(self.stats['errors'])}")
            
            if self.stats['errors']:
                logger.warning("错误详情:")
                for error in self.stats['errors']:
                    logger.warning(f"  - {error}")
            
            return {
                'success': verification.get('is_valid', False),
                'stats': self.stats,
                'verification': verification
            }
            
        except Exception as e:
            logger.error(f"✗ 迁移失败：{e}")
            self.stats['errors'].append(f'fatal: {str(e)}')
            
            # 自动回滚
            if backup:
                logger.info("尝试自动回滚...")
                self.rollback()
            
            return {
                'success': False,
                'stats': self.stats,
                'error': str(e)
            }


def main():
    """主函数"""
    print("=" * 60)
    print("统一账户架构 - 完整数据迁移工具")
    print("=" * 60)
    print()
    
    migration = DataMigration()
    
    # 运行完整迁移
    result = migration.run_full_migration(backup=True)
    
    print()
    print("=" * 60)
    
    if result['success']:
        print("✓ 迁移成功完成！")
    else:
        print("✗ 迁移失败，请检查日志")
        if 'error' in result:
            print(f"错误：{result['error']}")
    
    print("=" * 60)
    
    return result


if __name__ == "__main__":
    main()
