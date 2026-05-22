"""统一应用配置"""

import os
from typing import List, Optional


class Settings:
    """统一应用设置"""

    def __init__(self):
        # 应用信息
        self.APP_NAME: str = "AI产业集群空间服务系统"
        self.APP_VERSION: str = "1.0.0"
        self.ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")

        # 数据库配置 - 使用统一数据库
        self.DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./data/app.db")

        # CORS配置
        self.CORS_ALLOW_ORIGINS: List[str] = os.getenv("CORS_ALLOW_ORIGINS", "*").split(
            ","
        )
        if len(self.CORS_ALLOW_ORIGINS) == 1 and self.CORS_ALLOW_ORIGINS[0] == "*":
            self.CORS_ALLOW_ORIGINS = ["*"]

        self.CORS_ALLOW_CREDENTIALS: bool = (
            os.getenv("CORS_ALLOW_CREDENTIALS", "true").lower() == "true"
        )
        self.CORS_ALLOW_METHODS: List[str] = os.getenv("CORS_ALLOW_METHODS", "*").split(
            ","
        )
        if len(self.CORS_ALLOW_METHODS) == 1 and self.CORS_ALLOW_METHODS[0] == "*":
            self.CORS_ALLOW_METHODS = ["*"]

        self.CORS_ALLOW_HEADERS: List[str] = os.getenv("CORS_ALLOW_HEADERS", "*").split(
            ","
        )
        if len(self.CORS_ALLOW_HEADERS) == 1 and self.CORS_ALLOW_HEADERS[0] == "*":
            self.CORS_ALLOW_HEADERS = ["*"]

        # JWT配置
        secret_key = os.getenv("SECRET_KEY")
        if not secret_key:
            if self.ENVIRONMENT == "production":
                raise ValueError(
                    "SECRET_KEY 环境变量未设置！生产环境必须通过环境变量设置 SECRET_KEY"
                )
            import secrets
            secret_key = secrets.token_urlsafe(32)
            print(f"[DEV] 开发环境使用随机SECRET_KEY: {secret_key[:8]}...（服务重启后改变）")
        self.SECRET_KEY: str = secret_key
        self.ALGORITHM: str = "HS256"
        self.ACCESS_TOKEN_EXPIRE_HOURS: int = int(
            os.getenv("ACCESS_TOKEN_EXPIRE_HOURS", "24")
        )
        self.REFRESH_TOKEN_EXPIRE_DAYS: int = int(
            os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7")
        )

        # 密码安全配置
        self.MIN_PASSWORD_LENGTH: int = int(os.getenv("MIN_PASSWORD_LENGTH", "8"))
        self.MAX_PASSWORD_LENGTH: int = int(os.getenv("MAX_PASSWORD_LENGTH", "128"))
        self.REQUIRE_SPECIAL_CHAR: bool = (
            os.getenv("REQUIRE_SPECIAL_CHAR", "true").lower() == "true"
        )
        self.REQUIRE_NUMBER: bool = (
            os.getenv("REQUIRE_NUMBER", "true").lower() == "true"
        )
        self.REQUIRE_UPPERCASE: bool = (
            os.getenv("REQUIRE_UPPERCASE", "true").lower() == "true"
        )
        self.REQUIRE_LOWERCASE: bool = (
            os.getenv("REQUIRE_LOWERCASE", "true").lower() == "true"
        )
        self.DEFAULT_ADMIN_PASSWORD: str = os.getenv(
            "DEFAULT_ADMIN_PASSWORD", ""
        )

        # 登录安全配置
        self.MAX_LOGIN_ATTEMPTS: int = int(os.getenv("MAX_LOGIN_ATTEMPTS", "5"))
        self.LOGIN_LOCKOUT_DURATION_MINUTES: int = int(
            os.getenv("LOGIN_LOCKOUT_DURATION_MINUTES", "30")
        )
        self.LOGIN_ATTEMPT_WINDOW_MINUTES: int = int(
            os.getenv("LOGIN_ATTEMPT_WINDOW_MINUTES", "15")
        )

        # Token黑名单配置
        self.TOKEN_BLACKLIST_ENABLED: bool = (
            os.getenv("TOKEN_BLACKLIST_ENABLED", "true").lower() == "true"
        )
        self.TOKEN_BLACKLIST_CLEANUP_INTERVAL_HOURS: int = int(
            os.getenv("TOKEN_BLACKLIST_CLEANUP_INTERVAL_HOURS", "24")
        )

        # 会话安全配置
        self.MAX_CONCURRENT_SESSIONS: int = int(
            os.getenv("MAX_CONCURRENT_SESSIONS", "5")
        )
        self.SESSION_BINDING_ENABLED: bool = (
            os.getenv("SESSION_BINDING_ENABLED", "false").lower() == "true"
        )

        # 服务器配置
        self.HOST: str = os.getenv("HOST", "0.0.0.0")
        self.PORT: int = int(os.getenv("PORT", "8000"))

        # 日志配置
        self.LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
        self.LOG_FILE: str = os.getenv("LOG_FILE", "data/logs/app.log")
        self.LOG_MAX_BYTES: int = int(os.getenv("LOG_MAX_BYTES", str(10 * 1024 * 1024)))
        self.LOG_BACKUP_COUNT: int = int(os.getenv("LOG_BACKUP_COUNT", "5"))


settings = Settings()
