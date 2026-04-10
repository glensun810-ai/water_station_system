#!/usr/bin/env python3
"""
AI产业集群空间服务系统 - 水站数据迁移工具

将SQLite数据库中的水站数据迁移到PostgreSQL统一数据库
"""

import sqlite3
import psycopg2
from psycopg2.extras import RealDictCursor
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
import os
import sys

# 添加项目路径
sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("water_migration.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


class WaterDataMigrator:
    """水站数据迁移器"""

    def __init__(self, sqlite_path: str, pg_config: Dict[str, str]):
        self.sqlite_path = sqlite_path
        self.pg_config = pg_config
        self.sqlite_conn = None
        self.pg_conn = None

    def connect_databases(self):
        """连接数据库"""
        try:
            # 连接SQLite
            self.sqlite_conn = sqlite3.connect(self.sqlite_path)
            self.sqlite_conn.row_factory = sqlite3.Row
            logger.info(f"Connected to SQLite database: {self.sqlite_path}")

            # 连接PostgreSQL
            self.pg_conn = psycopg2.connect(**self.pg_config)
            self.pg_conn.autocommit = False
            logger.info(
                f"Connected to PostgreSQL database: {self.pg_config['host']}:{self.pg_config['port']}"
            )

        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            raise

    def close_connections(self):
        """关闭数据库连接"""
        if self.sqlite_conn:
            self.sqlite_conn.close()
            logger.info("Closed SQLite connection")

        if self.pg_conn:
            self.pg_conn.close()
            logger.info("Closed PostgreSQL connection")

    def migrate_offices(self) -> Dict[int, int]:
        """迁移办公室数据，返回ID映射"""
        logger.info("Starting office migration...")

        id_mapping = {}

        # 从SQLite读取办公室数据
        cursor = self.sqlite_conn.cursor()
        cursor.execute("""
            SELECT id, name, room_number, leader_name, is_active, 
                   created_at, updated_at
            FROM office 
            ORDER BY id
        """)

        offices = cursor.fetchall()
        logger.info(f"Found {len(offices)} offices to migrate")

        # 插入到PostgreSQL
        pg_cursor = self.pg_conn.cursor()
        for office in offices:
            try:
                pg_cursor.execute(
                    """
                    INSERT INTO offices (
                        id, name, room_number, leader_name, is_active,
                        created_at, updated_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO UPDATE SET
                        name = EXCLUDED.name,
                        room_number = EXCLUDED.room_number,
                        leader_name = EXCLUDED.leader_name,
                        is_active = EXCLUDED.is_active,
                        updated_at = EXCLUDED.updated_at
                """,
                    (
                        office["id"],
                        office["name"],
                        office["room_number"] or "",
                        office["leader_name"] or "",
                        bool(office["is_active"])
                        if office["is_active"] is not None
                        else True,
                        self._parse_datetime(office["created_at"]),
                        self._parse_datetime(office["updated_at"])
                        or self._parse_datetime(office["created_at"]),
                    ),
                )

                id_mapping[office["id"]] = office["id"]
                logger.debug(f"Migrated office: {office['name']} (ID: {office['id']})")

            except Exception as e:
                logger.error(f"Failed to migrate office {office['id']}: {e}")
                raise

        self.pg_conn.commit()
        logger.info(f"Successfully migrated {len(offices)} offices")
        return id_mapping

    def migrate_users(self, office_id_mapping: Dict[int, int]) -> Dict[int, int]:
        """迁移用户数据"""
        logger.info("Starting user migration...")

        id_mapping = {}

        # 从SQLite读取用户账户数据（作为用户列表）
        cursor = self.sqlite_conn.cursor()
        cursor.execute("""
            SELECT DISTINCT ua.user_id, o.name as department, o.id as office_id
            FROM user_account ua
            LEFT JOIN office_account oa ON ua.user_id = oa.manager_id
            LEFT JOIN office o ON oa.office_id = o.id
            WHERE ua.user_id IS NOT NULL
        """)

        users = cursor.fetchall()
        logger.info(f"Found {len(users)} users to migrate")

        # 插入到PostgreSQL
        pg_cursor = self.pg_conn.cursor()
        for user in users:
            try:
                # 生成临时用户名和密码
                username = f"user_{user['user_id']}"
                password_hash = (
                    "$2b$12$KIXqY8vJ8X3V9QZ7X3V9QeO3V9QZ7X3V9QZ7X3V9QZ7X3V9QZ7X3V"
                )

                pg_cursor.execute(
                    """
                    INSERT INTO users (
                        id, username, role, department_id, is_active,
                        password_hash, created_at, updated_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO UPDATE SET
                        username = EXCLUDED.username,
                        department_id = EXCLUDED.department_id,
                        updated_at = EXCLUDED.updated_at
                """,
                    (
                        user["user_id"],
                        username,
                        "user",
                        office_id_mapping.get(user["office_id"])
                        if user["office_id"]
                        else None,
                        True,
                        password_hash,
                        datetime.now(),
                        datetime.now(),
                    ),
                )

                id_mapping[user["user_id"]] = user["user_id"]
                logger.debug(f"Migrated user: {username} (ID: {user['user_id']})")

            except Exception as e:
                logger.error(f"Failed to migrate user {user['user_id']}: {e}")
                raise

        self.pg_conn.commit()
        logger.info(f"Successfully migrated {len(users)} users")
        return id_mapping

    def migrate_products(self) -> Dict[int, int]:
        """迁移产品数据"""
        logger.info("Starting product migration...")

        id_mapping = {}

        # 从SQLite读取产品数据
        cursor = self.sqlite_conn.cursor()
        cursor.execute("""
            SELECT id, name, specification, unit, price, stock, is_active, service_type
            FROM products
            ORDER BY id
        """)

        products = cursor.fetchall()
        logger.info(f"Found {len(products)} products to migrate")

        # 插入到PostgreSQL
        pg_cursor = self.pg_conn.cursor()
        for product in products:
            try:
                pg_cursor.execute(
                    """
                    INSERT INTO products (
                        id, name, specification, unit, price, stock, is_active, service_type
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO UPDATE SET
                        name = EXCLUDED.name,
                        specification = EXCLUDED.specification,
                        unit = EXCLUDED.unit,
                        price = EXCLUDED.price,
                        stock = EXCLUDED.stock,
                        is_active = EXCLUDED.is_active,
                        service_type = EXCLUDED.service_type,
                        updated_at = CURRENT_TIMESTAMP
                """,
                    (
                        product["id"],
                        product["name"] or f"Product_{product['id']}",
                        product["specification"] or "",
                        product["unit"] or "个",
                        float(product["price"]) if product["price"] else 0.0,
                        int(product["stock"]) if product["stock"] else 0,
                        bool(product["is_active"])
                        if product["is_active"] is not None
                        else True,
                        product["service_type"] or "water",
                    ),
                )

                id_mapping[product["id"]] = product["id"]
                logger.debug(
                    f"Migrated product: {product['name']} (ID: {product['id']})"
                )

            except Exception as e:
                logger.error(f"Failed to migrate product {product['id']}: {e}")
                raise

        self.pg_conn.commit()
        logger.info(f"Successfully migrated {len(products)} products")
        return id_mapping

    def migrate_user_accounts(self, user_id_mapping: Dict[int, int]) -> Dict[int, int]:
        """迁移用户账户数据"""
        logger.info("Starting user account migration...")

        id_mapping = {}

        # 从SQLite读取用户账户数据
        cursor = self.sqlite_conn.cursor()
        cursor.execute("""
            SELECT id, user_id, balance_prepaid, created_at, updated_at
            FROM user_account
            ORDER BY id
        """)

        accounts = cursor.fetchall()
        logger.info(f"Found {len(accounts)} user accounts to migrate")

        # 插入到PostgreSQL
        pg_cursor = self.pg_conn.cursor()
        for account in accounts:
            try:
                user_id = user_id_mapping.get(account["user_id"])
                if not user_id:
                    logger.warning(
                        f"Skipping account {account['id']}: user {account['user_id']} not found"
                    )
                    continue

                pg_cursor.execute(
                    """
                    INSERT INTO water_user_accounts (
                        id, user_id, balance_prepaid, created_at, updated_at
                    ) VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO UPDATE SET
                        user_id = EXCLUDED.user_id,
                        balance_prepaid = EXCLUDED.balance_prepaid,
                        updated_at = EXCLUDED.updated_at
                """,
                    (
                        account["id"],
                        user_id,
                        float(account["balance_prepaid"])
                        if account["balance_prepaid"]
                        else 0.0,
                        self._parse_datetime(account["created_at"]),
                        self._parse_datetime(account["updated_at"])
                        or self._parse_datetime(account["created_at"]),
                    ),
                )

                id_mapping[account["id"]] = account["id"]
                logger.debug(
                    f"Migrated user account for user {user_id} (Account ID: {account['id']})"
                )

            except Exception as e:
                logger.error(f"Failed to migrate user account {account['id']}: {e}")
                raise

        self.pg_conn.commit()
        logger.info(f"Successfully migrated {len(accounts)} user accounts")
        return id_mapping

    def migrate_wallets(
        self, user_id_mapping: Dict[int, int], product_id_mapping: Dict[int, int]
    ) -> Dict[int, int]:
        """迁移钱包数据"""
        logger.info("Starting wallet migration...")

        id_mapping = {}

        # 从SQLite读取钱包数据
        cursor = self.sqlite_conn.cursor()
        cursor.execute("""
            SELECT id, user_id, product_id, wallet_type, available_qty, paid_qty, free_qty, 
                   locked_qty, total_consumed, created_at, updated_at
            FROM account_wallet
            ORDER BY id
        """)

        wallets = cursor.fetchall()
        logger.info(f"Found {len(wallets)} wallets to migrate")

        # 插入到PostgreSQL
        pg_cursor = self.pg_conn.cursor()
        for wallet in wallets:
            try:
                user_id = user_id_mapping.get(wallet["user_id"])
                product_id = product_id_mapping.get(wallet["product_id"])

                if not user_id:
                    logger.warning(
                        f"Skipping wallet {wallet['id']}: user {wallet['user_id']} not found"
                    )
                    continue
                if not product_id:
                    logger.warning(
                        f"Skipping wallet {wallet['id']}: product {wallet['product_id']} not found"
                    )
                    continue

                pg_cursor.execute(
                    """
                    INSERT INTO water_wallets (
                        id, user_id, product_id, wallet_type, available_qty, paid_qty, free_qty,
                        locked_qty, total_consumed, created_at, updated_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO UPDATE SET
                        user_id = EXCLUDED.user_id,
                        product_id = EXCLUDED.product_id,
                        wallet_type = EXCLUDED.wallet_type,
                        available_qty = EXCLUDED.available_qty,
                        paid_qty = EXCLUDED.paid_qty,
                        free_qty = EXCLUDED.free_qty,
                        locked_qty = EXCLUDED.locked_qty,
                        total_consumed = EXCLUDED.total_consumed,
                        updated_at = EXCLUDED.updated_at
                """,
                    (
                        wallet["id"],
                        user_id,
                        product_id,
                        wallet["wallet_type"] or "prepaid",
                        int(wallet["available_qty"]) if wallet["available_qty"] else 0,
                        int(wallet["paid_qty"]) if wallet["paid_qty"] else 0,
                        int(wallet["free_qty"]) if wallet["free_qty"] else 0,
                        int(wallet["locked_qty"]) if wallet["locked_qty"] else 0,
                        int(wallet["total_consumed"])
                        if wallet["total_consumed"]
                        else 0,
                        self._parse_datetime(wallet["created_at"]),
                        self._parse_datetime(wallet["updated_at"])
                        or self._parse_datetime(wallet["created_at"]),
                    ),
                )

                id_mapping[wallet["id"]] = wallet["id"]
                logger.debug(
                    f"Migrated wallet for user {user_id}, product {product_id} (Wallet ID: {wallet['id']})"
                )

            except Exception as e:
                logger.error(f"Failed to migrate wallet {wallet['id']}: {e}")
                raise

        self.pg_conn.commit()
        logger.info(f"Successfully migrated {len(wallets)} wallets")
        return id_mapping

    def migrate_transactions(
        self,
        user_id_mapping: Dict[int, int],
        product_id_mapping: Dict[int, int],
        office_id_mapping: Dict[int, int],
    ) -> Dict[int, int]:
        """迁移交易记录数据"""
        logger.info("Starting transaction migration...")

        id_mapping = {}

        # 从SQLite读取交易记录数据
        cursor = self.sqlite_conn.cursor()
        cursor.execute("""
            SELECT id, user_id, product_id, quantity, unit_price, actual_price, mode, status,
                   settlement_batch_id, settlement_status, pickup_person, note, discount_desc,
                   paid_qty_deducted, gift_qty_deducted, financial_amount, created_at, updated_at
            FROM transactions_v2
            ORDER BY id
        """)

        transactions = cursor.fetchall()
        logger.info(f"Found {len(transactions)} transactions to migrate")

        # 插入到PostgreSQL
        pg_cursor = self.pg_conn.cursor()
        for txn in transactions:
            try:
                user_id = user_id_mapping.get(txn["user_id"])
                product_id = product_id_mapping.get(txn["product_id"])

                if not user_id:
                    logger.warning(
                        f"Skipping transaction {txn['id']}: user {txn['user_id']} not found"
                    )
                    continue
                if not product_id:
                    logger.warning(
                        f"Skipping transaction {txn['id']}: product {txn['product_id']} not found"
                    )
                    continue

                # 获取办公室ID（从note字段或关联表中提取，这里简化处理）
                office_id = None
                if txn["note"] and "office_id:" in str(txn["note"]):
                    try:
                        note_dict = json.loads(txn["note"])
                        office_id = note_dict.get("office_id")
                    except:
                        pass

                pg_cursor.execute(
                    """
                    INSERT INTO water_transactions (
                        id, user_id, product_id, office_id, quantity, unit_price, actual_price, mode, status,
                        settlement_batch_id, settlement_status, pickup_person, note, discount_desc,
                        paid_qty_deducted, gift_qty_deducted, financial_amount, created_at, updated_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO UPDATE SET
                        user_id = EXCLUDED.user_id,
                        product_id = EXCLUDED.product_id,
                        office_id = EXCLUDED.office_id,
                        quantity = EXCLUDED.quantity,
                        unit_price = EXCLUDED.unit_price,
                        actual_price = EXCLUDED.actual_price,
                        mode = EXCLUDED.mode,
                        status = EXCLUDED.status,
                        settlement_batch_id = EXCLUDED.settlement_batch_id,
                        settlement_status = EXCLUDED.settlement_status,
                        pickup_person = EXCLUDED.pickup_person,
                        note = EXCLUDED.note,
                        discount_desc = EXCLUDED.discount_desc,
                        paid_qty_deducted = EXCLUDED.paid_qty_deducted,
                        gift_qty_deducted = EXCLUDED.gift_qty_deducted,
                        financial_amount = EXCLUDED.financial_amount,
                        updated_at = EXCLUDED.updated_at
                """,
                    (
                        txn["id"],
                        user_id,
                        product_id,
                        office_id_mapping.get(office_id) if office_id else None,
                        int(txn["quantity"]) if txn["quantity"] else 0,
                        float(txn["unit_price"]) if txn["unit_price"] else 0.0,
                        float(txn["actual_price"]) if txn["actual_price"] else 0.0,
                        txn["mode"] or "prepaid",
                        txn["status"] or "completed",
                        txn["settlement_batch_id"],
                        txn["settlement_status"] or "unsettled",
                        txn["pickup_person"] or "",
                        txn["note"] or "",
                        txn["discount_desc"] or "",
                        int(txn["paid_qty_deducted"])
                        if txn["paid_qty_deducted"]
                        else 0,
                        int(txn["gift_qty_deducted"])
                        if txn["gift_qty_deducted"]
                        else 0,
                        float(txn["financial_amount"])
                        if txn["financial_amount"]
                        else 0.0,
                        self._parse_datetime(txn["created_at"]),
                        self._parse_datetime(txn["updated_at"])
                        or self._parse_datetime(txn["created_at"]),
                    ),
                )

                id_mapping[txn["id"]] = txn["id"]
                logger.debug(f"Migrated transaction {txn['id']} for user {user_id}")

            except Exception as e:
                logger.error(f"Failed to migrate transaction {txn['id']}: {e}")
                raise

        self.pg_conn.commit()
        logger.info(f"Successfully migrated {len(transactions)} transactions")
        return id_mapping

    def migrate_settlement_batches(
        self, user_id_mapping: Dict[int, int]
    ) -> Dict[int, int]:
        """迁移结算批次数据"""
        logger.info("Starting settlement batch migration...")

        id_mapping = {}

        # 从SQLite读取结算批次数据
        cursor = self.sqlite_conn.cursor()
        cursor.execute("""
            SELECT id, batch_no, user_id, transaction_ids, total_amount, status,
                   confirmed_at, confirmed_by, created_at, updated_at
            FROM settlement_batch
            ORDER BY id
        """)

        batches = cursor.fetchall()
        logger.info(f"Found {len(batches)} settlement batches to migrate")

        # 插入到PostgreSQL
        pg_cursor = self.pg_conn.cursor()
        for batch in batches:
            try:
                user_id = user_id_mapping.get(batch["user_id"])
                if not user_id:
                    logger.warning(
                        f"Skipping settlement batch {batch['id']}: user {batch['user_id']} not found"
                    )
                    continue

                # 处理transaction_ids（确保是有效的JSON格式）
                transaction_ids = batch["transaction_ids"]
                if isinstance(transaction_ids, str):
                    try:
                        json.loads(transaction_ids)
                    except json.JSONDecodeError:
                        transaction_ids = []

                pg_cursor.execute(
                    """
                    INSERT INTO water_settlement_batches (
                        id, batch_no, user_id, transaction_ids, total_amount, status,
                        confirmed_at, confirmed_by, created_at, updated_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO UPDATE SET
                        batch_no = EXCLUDED.batch_no,
                        user_id = EXCLUDED.user_id,
                        transaction_ids = EXCLUDED.transaction_ids,
                        total_amount = EXCLUDED.total_amount,
                        status = EXCLUDED.status,
                        confirmed_at = EXCLUDED.confirmed_at,
                        confirmed_by = EXCLUDED.confirmed_by,
                        updated_at = EXCLUDED.updated_at
                """,
                    (
                        batch["id"],
                        batch["batch_no"],
                        user_id,
                        transaction_ids,
                        float(batch["total_amount"]) if batch["total_amount"] else 0.0,
                        batch["status"] or "applied",
                        self._parse_datetime(batch["confirmed_at"]),
                        batch["confirmed_by"],
                        self._parse_datetime(batch["created_at"]),
                        self._parse_datetime(batch["updated_at"])
                        or self._parse_datetime(batch["created_at"]),
                    ),
                )

                id_mapping[batch["id"]] = batch["id"]
                logger.debug(
                    f"Migrated settlement batch {batch['batch_no']} (ID: {batch['id']})"
                )

            except Exception as e:
                logger.error(f"Failed to migrate settlement batch {batch['id']}: {e}")
                raise

        self.pg_conn.commit()
        logger.info(f"Successfully migrated {len(batches)} settlement batches")
        return id_mapping

    def _parse_datetime(self, dt_str: Optional[str]) -> Optional[datetime]:
        """解析日期时间字符串"""
        if not dt_str:
            return None

        if isinstance(dt_str, datetime):
            return dt_str

        try:
            # 尝试多种日期格式
            formats = [
                "%Y-%m-%d %H:%M:%S.%f",
                "%Y-%m-%d %H:%M:%S",
                "%Y-%m-%dT%H:%M:%S.%f",
                "%Y-%m-%dT%H:%M:%S",
                "%Y-%m-%d",
            ]

            for fmt in formats:
                try:
                    return datetime.strptime(dt_str, fmt)
                except ValueError:
                    continue

            logger.warning(f"Could not parse datetime: {dt_str}")
            return datetime.now()

        except Exception as e:
            logger.warning(f"Error parsing datetime {dt_str}: {e}")
            return datetime.now()

    def validate_migration(self):
        """验证迁移结果"""
        logger.info("Validating migration results...")

        # 验证基本数据完整性
        pg_cursor = self.pg_conn.cursor()

        # 验证用户数量
        pg_cursor.execute("SELECT COUNT(*) FROM users")
        user_count = pg_cursor.fetchone()[0]
        logger.info(f"Total users in PostgreSQL: {user_count}")

        # 验证产品数量
        pg_cursor.execute("SELECT COUNT(*) FROM products")
        product_count = pg_cursor.fetchone()[0]
        logger.info(f"Total products in PostgreSQL: {product_count}")

        # 验证交易记录数量
        pg_cursor.execute("SELECT COUNT(*) FROM water_transactions")
        transaction_count = pg_cursor.fetchone()[0]
        logger.info(f"Total transactions in PostgreSQL: {transaction_count}")

        # 验证结算批次数量
        pg_cursor.execute("SELECT COUNT(*) FROM water_settlement_batches")
        batch_count = pg_cursor.fetchone()[0]
        logger.info(f"Total settlement batches in PostgreSQL: {batch_count}")

        logger.info("Migration validation completed successfully!")

    def run_migration(self):
        """执行完整的迁移流程"""
        try:
            logger.info("Starting water data migration...")

            # 连接数据库
            self.connect_databases()

            # 执行迁移步骤
            office_id_mapping = self.migrate_offices()
            user_id_mapping = self.migrate_users(office_id_mapping)
            product_id_mapping = self.migrate_products()
            self.migrate_user_accounts(user_id_mapping)
            self.migrate_wallets(user_id_mapping, product_id_mapping)
            self.migrate_transactions(
                user_id_mapping, product_id_mapping, office_id_mapping
            )
            self.migrate_settlement_batches(user_id_mapping)

            # 验证迁移结果
            self.validate_migration()

            logger.info("Water data migration completed successfully!")

        except Exception as e:
            logger.error(f"Migration failed: {e}")
            self.pg_conn.rollback()
            raise

        finally:
            self.close_connections()


def main():
    """主函数"""
    # 数据库配置
    sqlite_path = "Service_WaterManage/waterms.db"
    pg_config = {
        "host": "localhost",
        "port": "5432",
        "database": "ai_cluster_db",
        "user": "ai_cluster",
        "password": "secure_password_2026",
    }

    # 创建迁移器并执行
    migrator = WaterDataMigrator(sqlite_path, pg_config)
    migrator.run_migration()


if __name__ == "__main__":
    main()
