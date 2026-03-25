"""
Dual-Write Service - 双写服务模式
实现新旧系统数据同步，确保数据一致性
"""

from typing import Dict, List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DualWriteService:
    """
    双写服务

    在新旧系统并行期间，确保数据同时写入新旧两套系统
    """

    def __init__(self, db: Session):
        self.db = db
        self.stats = {"success": 0, "failed": 0, "last_sync": None}

    # ==================== 用户账户双写 ====================

    def sync_user_account(self, user_id: int) -> Dict:
        """
        同步用户账户到统一账户表

        Args:
            user_id: 用户 ID

        Returns:
            dict: 同步结果
        """
        try:
            # 从旧表获取用户信息
            user = self.db.execute(
                text("SELECT id, name FROM users WHERE id = :user_id"),
                {"user_id": user_id},
            ).fetchone()

            if not user:
                return {"success": False, "error": "用户不存在"}

            # 检查是否已存在账户
            existing = self.db.execute(
                text("SELECT id FROM user_account WHERE user_id = :user_id"),
                {"user_id": user_id},
            ).fetchone()

            if existing:
                return {"success": False, "error": "账户已存在"}

            # 创建统一账户（仅预付余额）
            self.db.execute(
                text("""
                INSERT INTO user_account (user_id, balance_prepaid, created_at, updated_at)
                VALUES (:user_id, 0, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                """),
                {"user_id": user_id},
            )
            self.db.commit()

            self.stats["success"] += 1
            self.stats["last_sync"] = datetime.now()

            logger.info(f"✓ 同步用户账户成功：user_id={user_id}")
            return {"success": True, "user_id": user_id}

        except Exception as e:
            self.db.rollback()
            self.stats["failed"] += 1
            logger.error(f"✗ 同步用户账户失败：user_id={user_id}, error={e}")
            return {"success": False, "error": str(e)}

    # ==================== 钱包双写 ====================

    def sync_wallet_from_prepaid_order(self, order_id: int) -> Dict:
        """
        从预付订单同步到钱包

        Args:
            order_id: 预付订单 ID

        Returns:
            dict: 同步结果
        """
        try:
            # 获取预付订单
            order = self.db.execute(
                text("""
                SELECT user_id, product_id, total_qty, used_qty 
                FROM prepaid_orders 
                WHERE id = :order_id AND payment_status = 'paid' AND is_active = 1
                """),
                {"order_id": order_id},
            ).fetchone()

            if not order:
                return {"success": False, "error": "订单不存在或未支付"}

            user_id, product_id, total_qty, used_qty = order
            remaining_qty = total_qty - used_qty

            if remaining_qty <= 0:
                return {"success": False, "error": "无可用余额"}

            # 检查是否已存在钱包
            existing = self.db.execute(
                text("""
                SELECT id FROM account_wallet 
                WHERE user_id = :user_id AND product_id = :product_id AND wallet_type = 'prepaid'
                """),
                {"user_id": user_id, "product_id": product_id},
            ).fetchone()

            if existing:
                # 更新现有钱包
                self.db.execute(
                    text("""
                    UPDATE account_wallet 
                    SET available_qty = available_qty + :qty, updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = :user_id AND product_id = :product_id AND wallet_type = 'prepaid'
                    """),
                    {
                        "user_id": user_id,
                        "product_id": product_id,
                        "qty": remaining_qty,
                    },
                )
            else:
                # 创建新钱包
                self.db.execute(
                    text("""
                    INSERT INTO account_wallet 
                    (user_id, product_id, wallet_type, available_qty, locked_qty, total_consumed, created_at, updated_at)
                    VALUES (:user_id, :product_id, 'prepaid', :qty, 0, 0, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                    """),
                    {
                        "user_id": user_id,
                        "product_id": product_id,
                        "qty": remaining_qty,
                    },
                )

            self.db.commit()

            self.stats["success"] += 1
            logger.info(
                f"✓ 同步预付订单到钱包成功：order_id={order_id}, qty={remaining_qty}"
            )
            return {"success": True, "order_id": order_id, "qty": remaining_qty}

        except Exception as e:
            self.db.rollback()
            self.stats["failed"] += 1
            logger.error(f"✗ 同步预付订单失败：order_id={order_id}, error={e}")
            return {"success": False, "error": str(e)}

    # ==================== 交易记录双写 ====================

    def sync_transaction_v2(self, transaction_id: int) -> Dict:
        """
        从旧交易记录同步到 V2 表

        Args:
            transaction_id: 旧交易记录 ID

        Returns:
            dict: 同步结果
        """
        try:
            # 获取旧交易记录
            txn = self.db.execute(
                text("""
                SELECT user_id, product_id, quantity, actual_price, mode, status, created_at
                FROM transactions
                WHERE id = :txn_id
                """),
                {"txn_id": transaction_id},
            ).fetchone()

            if not txn:
                return {"success": False, "error": "交易记录不存在"}

            user_id, product_id, quantity, actual_price, mode, status, created_at = txn

            # 转换模式
            wallet_type = "prepaid" if mode == "prepay" else "credit"
            v2_status = "settled" if status == "settled" else "pending"

            # 检查是否已存在
            existing = self.db.execute(
                text(
                    "SELECT id FROM transactions_v2 WHERE user_id = :user_id AND product_id = :product_id AND created_at = :created_at"
                ),
                {
                    "user_id": user_id,
                    "product_id": product_id,
                    "created_at": created_at,
                },
            ).fetchone()

            if existing:
                return {"success": False, "error": "交易记录已存在"}

            # 创建 V2 交易记录
            self.db.execute(
                text("""
                INSERT INTO transactions_v2 
                (user_id, product_id, quantity, unit_price, actual_price, mode, wallet_type, status, 
                 discount_desc, free_qty, created_at, updated_at)
                VALUES (:user_id, :product_id, :quantity, :unit_price, :actual_price, :mode, :wallet_type, 
                        :status, :discount_desc, :free_qty, :created_at, CURRENT_TIMESTAMP)
                """),
                {
                    "user_id": user_id,
                    "product_id": product_id,
                    "quantity": quantity,
                    "unit_price": actual_price / quantity if quantity > 0 else 0,
                    "actual_price": actual_price,
                    "mode": wallet_type,
                    "wallet_type": wallet_type,
                    "status": v2_status,
                    "discount_desc": f"从旧系统同步（{mode}）",
                    "free_qty": 0,
                    "created_at": created_at,
                },
            )

            self.db.commit()

            self.stats["success"] += 1
            logger.info(f"✓ 同步交易记录成功：txn_id={transaction_id}")
            return {"success": True, "transaction_id": transaction_id}

        except Exception as e:
            self.db.rollback()
            self.stats["failed"] += 1
            logger.error(f"✗ 同步交易记录失败：txn_id={transaction_id}, error={e}")
            return {"success": False, "error": str(e)}

    # ==================== 批量同步 ====================

    def batch_sync_users(self, limit: int = 100) -> Dict:
        """
        批量同步用户账户

        Args:
            limit: 每次同步的用户数量

        Returns:
            dict: 同步结果统计
        """
        try:
            # 获取需要同步的用户
            users = self.db.execute(
                text("""
                SELECT u.id, u.name
                FROM users u
                LEFT JOIN user_account ua ON u.id = ua.user_id
                WHERE ua.user_id IS NULL
                LIMIT :limit
                """),
                {"limit": limit},
            ).fetchall()

            results = {"success": 0, "failed": 0, "details": []}

            for user in users:
                result = self.sync_user_account(user[0])
                if result["success"]:
                    results["success"] += 1
                else:
                    results["failed"] += 1
                results["details"].append({"user_id": user[0], "result": result})

            logger.info(
                f"批量同步用户完成：成功={results['success']}, 失败={results['failed']}"
            )
            return results

        except Exception as e:
            logger.error(f"批量同步用户失败：error={e}")
            return {"success": 0, "failed": 0, "error": str(e)}

    def batch_sync_prepaid_orders(self, limit: int = 100) -> Dict:
        """
        批量同步预付订单到钱包

        Args:
            limit: 每次同步的订单数量

        Returns:
            dict: 同步结果统计
        """
        try:
            # 获取需要同步的订单
            orders = self.db.execute(
                text("""
                SELECT po.id, po.user_id, po.product_id, po.total_qty, po.used_qty
                FROM prepaid_orders po
                WHERE po.payment_status = 'paid' AND po.is_active = 1
                AND NOT EXISTS (
                    SELECT 1 FROM account_wallet aw 
                    WHERE aw.user_id = po.user_id AND aw.product_id = po.product_id AND aw.wallet_type = 'prepaid'
                )
                LIMIT :limit
                """),
                {"limit": limit},
            ).fetchall()

            results = {"success": 0, "failed": 0, "details": []}

            for order in orders:
                result = self.sync_wallet_from_prepaid_order(order[0])
                if result["success"]:
                    results["success"] += 1
                else:
                    results["failed"] += 1
                results["details"].append({"order_id": order[0], "result": result})

            logger.info(
                f"批量同步预付订单完成：成功={results['success']}, 失败={results['failed']}"
            )
            return results

        except Exception as e:
            logger.error(f"批量同步预付订单失败：error={e}")
            return {"success": 0, "failed": 0, "error": str(e)}

    def batch_sync_transactions(self, limit: int = 500) -> Dict:
        """
        批量同步交易记录到 V2 表

        Args:
            limit: 每次同步的交易数量

        Returns:
            dict: 同步结果统计
        """
        try:
            # 获取需要同步的交易
            txns = self.db.execute(
                text("""
                SELECT t.id
                FROM transactions t
                LEFT JOIN transactions_v2 tv2 ON t.id = tv2.settlement_batch_id
                WHERE tv2.id IS NULL
                LIMIT :limit
                """),
                {"limit": limit},
            ).fetchall()

            results = {"success": 0, "failed": 0}

            for txn in txns:
                result = self.sync_transaction_v2(txn[0])
                if result["success"]:
                    results["success"] += 1
                else:
                    results["failed"] += 1

            logger.info(
                f"批量同步交易记录完成：成功={results['success']}, 失败={results['failed']}"
            )
            return results

        except Exception as e:
            logger.error(f"批量同步交易记录失败：error={e}")
            return {"success": 0, "failed": 0, "error": str(e)}

    # ==================== 数据一致性校验 ====================

    def verify_data_consistency(self) -> Dict:
        """
        校验新旧系统数据一致性

        Returns:
            dict: 校验结果
        """
        try:
            issues = []

            # 1. 校验用户账户
            user_issues = self.db.execute(
                text("""
                SELECT u.id, u.name
                FROM users u
                LEFT JOIN user_account ua ON u.id = ua.user_id
                WHERE ua.user_id IS NULL
                """)
            ).fetchall()

            if user_issues:
                issues.append(
                    {
                        "type": "user_account",
                        "count": len(user_issues),
                        "details": [
                            {"user_id": r[0], "name": r[1]} for r in user_issues[:10]
                        ],
                    }
                )

            # 2. 校验钱包余额与预付订单
            wallet_issues = self.db.execute(
                text("""
                SELECT aw.user_id, aw.product_id, aw.wallet_type, aw.available_qty,
                       SUM(po.total_qty - po.used_qty) as expected_qty
                FROM account_wallet aw
                LEFT JOIN prepaid_orders po ON aw.user_id = po.user_id AND aw.product_id = po.product_id
                WHERE aw.wallet_type = 'prepaid' AND po.payment_status = 'paid' AND po.is_active = 1
                GROUP BY aw.user_id, aw.product_id, aw.wallet_type, aw.available_qty
                HAVING aw.available_qty != expected_qty
                """)
            ).fetchall()

            if wallet_issues:
                issues.append(
                    {
                        "type": "wallet_balance",
                        "count": len(wallet_issues),
                        "details": [
                            {
                                "user_id": r[0],
                                "product_id": r[1],
                                "actual": r[2],
                                "expected": r[3],
                            }
                            for r in wallet_issues[:10]
                        ],
                    }
                )

            return {
                "consistent": len(issues) == 0,
                "issues": issues,
                "checked_at": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"数据一致性校验失败：error={e}")
            return {"consistent": False, "error": str(e)}

    # ==================== 统计信息 ====================

    def get_sync_stats(self) -> Dict:
        """获取同步统计信息"""
        return {
            **self.stats,
            "last_sync": self.stats["last_sync"].isoformat()
            if self.stats["last_sync"]
            else None,
        }


def get_dual_write_service(db: Session) -> DualWriteService:
    """获取双写服务实例"""
    return DualWriteService(db)
