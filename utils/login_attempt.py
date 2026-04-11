"""
防暴力破解系统 - 登录失败限制
符合OWASP Authentication Cheat Sheet安全标准
"""

from datetime import datetime, timedelta
from typing import Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import text
import threading

from config.settings import settings


class LoginAttemptManager:
    """登录尝试管理器"""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        """单例模式"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def check_login_allowed(
        self, username: str, ip_address: str, db: Session
    ) -> Tuple[bool, Optional[str]]:
        """
        检查是否允许登录

        Args:
            username: 用户名
            ip_address: IP地址
            db: 数据库会话

        Returns:
            (是否允许, 错误信息)

        Security:
            - 账号级别锁定：防止账号暴力破解
            - IP级别限制：防止分布式攻击
            - 滑动窗口计数：记录最近N分钟的失败次数
        """
        now = datetime.now()
        window_start = now - timedelta(minutes=settings.LOGIN_ATTEMPT_WINDOW_MINUTES)

        try:
            # 检查账号锁定状态
            account_locked = db.execute(
                text("""
                    SELECT lockout_until FROM account_lockouts
                    WHERE username = :username
                    AND lockout_until > :now
                """),
                {"username": username, "now": now.isoformat()},
            ).fetchone()

            if account_locked:
                remaining_time = (
                    datetime.fromisoformat(account_locked.lockout_until) - now
                ).seconds // 60
                return False, f"账号已锁定，请{remaining_time}分钟后重试"

            # 检查账号失败次数
            account_failures = db.execute(
                text("""
                    SELECT COUNT(*) as count FROM login_attempts
                    WHERE username = :username
                    AND attempt_time > :window_start
                    AND status = 'failure'
                """),
                {"username": username, "window_start": window_start.isoformat()},
            ).fetchone()

            if (
                account_failures
                and account_failures.count >= settings.MAX_LOGIN_ATTEMPTS
            ):
                self.lock_account(username, db)
                return (
                    False,
                    f"登录失败次数过多，账号已锁定{settings.LOGIN_LOCKOUT_DURATION_MINUTES}分钟",
                )

            # 检查IP限制（防止分布式攻击）
            ip_failures = db.execute(
                text("""
                    SELECT COUNT(*) as count FROM login_attempts
                    WHERE ip_address = :ip_address
                    AND attempt_time > :window_start
                    AND status = 'failure'
                """),
                {"ip_address": ip_address, "window_start": window_start.isoformat()},
            ).fetchone()

            # IP级别更宽松的限制（账号限制的3倍）
            max_ip_attempts = settings.MAX_LOGIN_ATTEMPTS * 3
            if ip_failures and ip_failures.count >= max_ip_attempts:
                return False, "该IP登录失败次数过多，请稍后重试"

            return True, None

        except Exception as e:
            print(f"检查登录限制失败: {e}")
            return True, None

    def record_login_attempt(
        self,
        username: str,
        ip_address: str,
        status: str,
        db: Session,
        user_id: Optional[int] = None,
        failure_reason: Optional[str] = None,
    ) -> bool:
        """
        记录登录尝试

        Args:
            username: 用户名
            ip_address: IP地址
            status: 状态（success/failure）
            db: 数据库会话
            user_id: 用户ID（可选）
            failure_reason: 失败原因（可选）

        Returns:
            是否成功记录
        """
        try:
            db.execute(
                text("""
                    INSERT INTO login_attempts 
                    (username, ip_address, user_id, attempt_time, status, failure_reason)
                    VALUES (:username, :ip_address, :user_id, :attempt_time, :status, :failure_reason)
                """),
                {
                    "username": username,
                    "ip_address": ip_address,
                    "user_id": user_id or 0,
                    "attempt_time": datetime.now().isoformat(),
                    "status": status,
                    "failure_reason": failure_reason,
                },
            )

            if status == "success":
                self.unlock_account(username, db)

            db.commit()
            return True

        except Exception as e:
            print(f"记录登录尝试失败: {e}")
            return False

    def lock_account(self, username: str, db: Session) -> bool:
        """
        锁定账号

        Args:
            username: 用户名
            db: 数据库会话

        Returns:
            是否成功锁定
        """
        try:
            lockout_until = datetime.now() + timedelta(
                minutes=settings.LOGIN_LOCKOUT_DURATION_MINUTES
            )

            db.execute(
                text("""
                    INSERT OR REPLACE INTO account_lockouts 
                    (username, lockout_until, lockout_reason)
                    VALUES (:username, :lockout_until, 'excessive_failed_attempts')
                """),
                {"username": username, "lockout_until": lockout_until.isoformat()},
            )
            db.commit()
            return True

        except Exception as e:
            print(f"锁定账号失败: {e}")
            return False

    def unlock_account(self, username: str, db: Session) -> bool:
        """
        解锁账号

        Args:
            username: 用户名
            db: 数据库会话

        Returns:
            是否成功解锁
        """
        try:
            db.execute(
                text("DELETE FROM account_lockouts WHERE username = :username"),
                {"username": username},
            )
            db.commit()
            return True

        except Exception as e:
            print(f"解锁账号失败: {e}")
            return False

    def get_remaining_attempts(self, username: str, db: Session) -> int:
        """
        获取剩余尝试次数

        Args:
            username: 用户名
            db: 数据库会话

        Returns:
            剩余次数
        """
        now = datetime.now()
        window_start = now - timedelta(minutes=settings.LOGIN_ATTEMPT_WINDOW_MINUTES)

        try:
            result = db.execute(
                text("""
                    SELECT COUNT(*) as count FROM login_attempts
                    WHERE username = :username
                    AND attempt_time > :window_start
                    AND status = 'failure'
                """),
                {"username": username, "window_start": window_start.isoformat()},
            ).fetchone()

            if result:
                return max(0, settings.MAX_LOGIN_ATTEMPTS - result.count)
            return settings.MAX_LOGIN_ATTEMPTS

        except Exception as e:
            print(f"获取剩余尝试次数失败: {e}")
            return settings.MAX_LOGIN_ATTEMPTS

    def cleanup_old_attempts(self, db: Session) -> int:
        """
        清理旧的登录尝试记录

        Args:
            db: 数据库会话

        Returns:
            清理的记录数
        """
        try:
            cutoff_time = datetime.now() - timedelta(hours=1)

            result = db.execute(
                text("DELETE FROM login_attempts WHERE attempt_time < :cutoff_time"),
                {"cutoff_time": cutoff_time.isoformat()},
            )

            # 清理已过期的账号锁定
            db.execute(
                text("DELETE FROM account_lockouts WHERE lockout_until < :now"),
                {"now": datetime.now().isoformat()},
            )

            deleted = result.rowcount
            db.commit()

            return deleted

        except Exception as e:
            print(f"清理登录尝试记录失败: {e}")
            return 0


login_attempt_manager = LoginAttemptManager()


def check_login_allowed(
    username: str, ip_address: str, db: Session
) -> Tuple[bool, Optional[str]]:
    """检查是否允许登录"""
    return login_attempt_manager.check_login_allowed(username, ip_address, db)


def record_attempt(
    username: str, ip_address: str, status: str, db: Session, **kwargs
) -> bool:
    """记录登录尝试"""
    return login_attempt_manager.record_login_attempt(
        username, ip_address, status, db, **kwargs
    )


def get_remaining_attempts(username: str, db: Session) -> int:
    """获取剩余尝试次数"""
    return login_attempt_manager.get_remaining_attempts(username, db)


def cleanup_attempts(db: Session) -> int:
    """清理旧记录"""
    return login_attempt_manager.cleanup_old_attempts(db)
