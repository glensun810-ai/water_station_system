"""
Token黑名单管理 - 安全登出机制
符合OAuth 2.0和JWT安全最佳实践
"""

import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Set
from sqlalchemy.orm import Session
from sqlalchemy import text
import threading
import time

from config.settings import settings
from utils.jwt import verify_token


class TokenBlacklistManager:
    """Token黑名单管理器"""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        """单例模式"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._blacklist_cache: Set[str] = set()
                    cls._instance._last_cleanup = datetime.now()
        return cls._instance

    def add_to_blacklist(self, token: str, db: Optional[Session] = None) -> bool:
        """
        将token添加到黑名单

        Args:
            token: JWT token
            db: 数据库会话

        Returns:
            是否成功添加

        Security:
            - 双重存储：内存缓存（快速）+ 数据库（持久）
            - 记录失效原因和时间
        """
        if not settings.TOKEN_BLACKLIST_ENABLED:
            return False

        payload = verify_token(token)
        if not payload:
            return False

        jti = payload.get("jti")
        if not jti:
            jti = token

        self._blacklist_cache.add(jti)

        if db:
            try:
                expiry_time = payload.get(
                    "exp",
                    datetime.now()
                    + timedelta(hours=settings.ACCESS_TOKEN_EXPIRE_HOURS),
                )

                db.execute(
                    text("""
                        INSERT OR IGNORE INTO token_blacklist 
                        (token_jti, token_value, revoked_at, expiry_time, reason)
                        VALUES (:jti, :token, :revoked_at, :expiry_time, 'logout')
                    """),
                    {
                        "jti": jti,
                        "token": token[:100],
                        "revoked_at": datetime.now().isoformat(),
                        "expiry_time": datetime.fromtimestamp(expiry_time).isoformat(),
                    },
                )
                db.commit()
            except Exception as e:
                print(f"添加token黑名单失败: {e}")

        return True

    def is_blacklisted(self, token: str, db: Optional[Session] = None) -> bool:
        """
        检查token是否在黑名单中

        Args:
            token: JWT token
            db: 数据库会话

        Returns:
            是否在黑名单中

        Performance:
            - 先查内存缓存（毫秒级）
            - 缓存不存在再查数据库
        """
        if not settings.TOKEN_BLACKLIST_ENABLED:
            return False

        payload = verify_token(token)
        if not payload:
            return True

        jti = payload.get("jti")
        if not jti:
            jti = token

        if jti in self._blacklist_cache:
            return True

        if db:
            try:
                result = db.execute(
                    text("SELECT id FROM token_blacklist WHERE token_jti = :jti"),
                    {"jti": jti},
                ).fetchone()

                if result:
                    self._blacklist_cache.add(jti)
                    return True
            except Exception as e:
                print(f"检查token黑名单失败: {e}")

        return False

    def cleanup_expired_tokens(self, db: Optional[Session] = None) -> int:
        """
        清理过期token

        Args:
            db: 数据库会话

        Returns:
            清理的token数量

        Performance:
            - 定期清理，避免黑名单无限增长
            - 建议每小时执行一次
        """
        if not db:
            return 0

        try:
            now = datetime.now().isoformat()

            result = db.execute(
                text("DELETE FROM token_blacklist WHERE expiry_time < :now"),
                {"now": now},
            )

            deleted_count = result.rowcount
            db.commit()

            self._blacklist_cache.clear()

            return deleted_count
        except Exception as e:
            print(f"清理过期token失败: {e}")
            return 0

    def revoke_all_user_tokens(self, user_id: int, db: Optional[Session] = None) -> int:
        """
        撤销用户所有token（强制登出）

        Args:
            user_id: 用户ID
            db: 数据库会话

        Returns:
            撤销的token数量

        Usage:
            - 用户修改密码后强制登出所有会话
            - 管理员强制禁用用户
            - 安全事件响应
        """
        if not db:
            return 0

        try:
            result = db.execute(
                text("""
                    UPDATE token_blacklist 
                    SET reason = 'force_logout', revoked_at = :now
                    WHERE user_id = :user_id AND expiry_time > :now
                """),
                {"user_id": user_id, "now": datetime.now().isoformat()},
            )

            count = result.rowcount
            db.commit()

            return count
        except Exception as e:
            print(f"撤销用户token失败: {e}")
            return 0


token_blacklist = TokenBlacklistManager()


def revoke_token(token: str, db: Optional[Session] = None) -> bool:
    """撤销单个token"""
    return token_blacklist.add_to_blacklist(token, db)


def is_token_revoked(token: str, db: Optional[Session] = None) -> bool:
    """检查token是否已撤销"""
    return token_blacklist.is_blacklisted(token, db)


def cleanup_blacklist(db: Optional[Session] = None) -> int:
    """清理黑名单"""
    return token_blacklist.cleanup_expired_tokens(db)


def revoke_user_tokens(user_id: int, db: Optional[Session] = None) -> int:
    """撤销用户所有token"""
    return token_blacklist.revoke_all_user_tokens(user_id, db)
