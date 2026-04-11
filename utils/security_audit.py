"""
安全审计日志系统 - 符合ISO 27001标准
记录所有关键安全事件，支持审计和合规
"""

from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import text
from enum import Enum


class SecurityEventType(Enum):
    """安全事件类型"""

    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILURE = "login_failure"
    LOGOUT = "logout"
    PASSWORD_CHANGE = "password_change"
    ACCOUNT_LOCKOUT = "account_lockout"
    ACCOUNT_UNLOCK = "account_unlock"
    TOKEN_REVOKED = "token_revoked"
    SESSION_REVOKED = "session_revoked"
    PERMISSION_DENIED = "permission_denied"
    USER_CREATED = "user_created"
    USER_DELETED = "user_deleted"
    USER_UPDATED = "user_updated"
    ROLE_CHANGED = "role_changed"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"


class SecurityAuditLogger:
    """安全审计日志记录器"""

    @staticmethod
    def log_security_event(
        db: Session,
        event_type: SecurityEventType,
        user_id: Optional[int] = None,
        username: Optional[str] = None,
        ip_address: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        severity: str = "info",
    ):
        """
        记录安全事件

        Args:
            db: 数据库会话
            event_type: 事件类型
            user_id: 用户ID
            username: 用户名
            ip_address: IP地址
            details: 详细信息
            severity: 严重程度（info/warning/critical）

        Compliance:
            - ISO 27001 A.12.4: 事件日志
            - GDPR Article 30: 处理活动记录
        """
        try:
            details_json = str(details) if details else ""

            db.execute(
                text("""
                    INSERT INTO security_audit_log 
                    (event_type, user_id, username, ip_address, event_time, 
                     details, severity, created_at)
                    VALUES (:event_type, :user_id, :username, :ip_address, 
                            :event_time, :details, :severity, :created_at)
                """),
                {
                    "event_type": event_type.value,
                    "user_id": user_id or 0,
                    "username": username or "unknown",
                    "ip_address": ip_address or "unknown",
                    "event_time": datetime.now().isoformat(),
                    "details": details_json,
                    "severity": severity,
                    "created_at": datetime.now().isoformat(),
                },
            )
            db.commit()

        except Exception as e:
            print(f"记录安全审计日志失败: {e}")

    @staticmethod
    def log_login_success(
        db: Session,
        user_id: int,
        username: str,
        ip_address: str,
        device_type: str,
        browser: str,
    ):
        """记录登录成功"""
        SecurityAuditLogger.log_security_event(
            db=db,
            event_type=SecurityEventType.LOGIN_SUCCESS,
            user_id=user_id,
            username=username,
            ip_address=ip_address,
            details={"device_type": device_type, "browser": browser},
            severity="info",
        )

    @staticmethod
    def log_login_failure(
        db: Session,
        username: str,
        ip_address: str,
        failure_reason: str,
        user_id: Optional[int] = None,
    ):
        """记录登录失败"""
        SecurityAuditLogger.log_security_event(
            db=db,
            event_type=SecurityEventType.LOGIN_FAILURE,
            user_id=user_id,
            username=username,
            ip_address=ip_address,
            details={"failure_reason": failure_reason},
            severity="warning",
        )

    @staticmethod
    def log_password_change(db: Session, user_id: int, username: str, ip_address: str):
        """记录密码修改"""
        SecurityAuditLogger.log_security_event(
            db=db,
            event_type=SecurityEventType.PASSWORD_CHANGE,
            user_id=user_id,
            username=username,
            ip_address=ip_address,
            severity="info",
        )

    @staticmethod
    def log_account_lockout(db: Session, username: str, ip_address: str, reason: str):
        """记录账号锁定"""
        SecurityAuditLogger.log_security_event(
            db=db,
            event_type=SecurityEventType.ACCOUNT_LOCKOUT,
            username=username,
            ip_address=ip_address,
            details={"lockout_reason": reason},
            severity="warning",
        )

    @staticmethod
    def log_permission_denied(
        db: Session,
        user_id: int,
        username: str,
        ip_address: str,
        resource: str,
        required_permission: str,
    ):
        """记录权限拒绝"""
        SecurityAuditLogger.log_security_event(
            db=db,
            event_type=SecurityEventType.PERMISSION_DENIED,
            user_id=user_id,
            username=username,
            ip_address=ip_address,
            details={"resource": resource, "required_permission": required_permission},
            severity="warning",
        )

    @staticmethod
    def log_suspicious_activity(
        db: Session, ip_address: str, activity_type: str, details: Dict[str, Any]
    ):
        """记录可疑活动"""
        SecurityAuditLogger.log_security_event(
            db=db,
            event_type=SecurityEventType.SUSPICIOUS_ACTIVITY,
            ip_address=ip_address,
            details={"activity_type": activity_type, **details},
            severity="critical",
        )

    @staticmethod
    def get_user_security_events(db: Session, user_id: int, limit: int = 100):
        """获取用户安全事件历史"""
        try:
            events = db.execute(
                text("""
                    SELECT event_type, event_time, ip_address, details, severity
                    FROM security_audit_log
                    WHERE user_id = :user_id
                    ORDER BY event_time DESC
                    LIMIT :limit
                """),
                {"user_id": user_id, "limit": limit},
            ).fetchall()

            return [
                {
                    "event_type": e.event_type,
                    "event_time": e.event_time,
                    "ip_address": e.ip_address,
                    "details": e.details,
                    "severity": e.severity,
                }
                for e in events
            ]

        except Exception as e:
            print(f"获取安全事件失败: {e}")
            return []

    @staticmethod
    def ensure_audit_table_exists(db: Session):
        """确保审计表存在"""
        try:
            db.execute(
                text("""
                CREATE TABLE IF NOT EXISTS security_audit_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type VARCHAR(50) NOT NULL,
                    user_id INTEGER,
                    username VARCHAR(100),
                    ip_address VARCHAR(50),
                    event_time TIMESTAMP NOT NULL,
                    details TEXT,
                    severity VARCHAR(20) DEFAULT 'info',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            )

            db.execute(
                text("""
                CREATE INDEX IF NOT EXISTS idx_audit_user_id 
                ON security_audit_log(user_id)
            """)
            )

            db.execute(
                text("""
                CREATE INDEX IF NOT EXISTS idx_audit_event_time 
                ON security_audit_log(event_time)
            """)
            )

            db.execute(
                text("""
                CREATE INDEX IF NOT EXISTS idx_audit_event_type 
                ON security_audit_log(event_type)
            """)
            )

            db.commit()

        except Exception as e:
            print(f"创建审计表失败: {e}")


security_audit_logger = SecurityAuditLogger()


def log_event(db: Session, event_type: SecurityEventType, **kwargs):
    """记录安全事件"""
    security_audit_logger.log_security_event(db, event_type, **kwargs)


def ensure_audit_tables(db: Session):
    """确保审计表存在"""
    security_audit_logger.ensure_audit_table_exists(db)
