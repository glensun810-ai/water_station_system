"""
统一配置管理
所有配置项统一管理，支持环境变量覆盖
"""

from typing import Optional
import os

# 尝试加载.env文件
try:
    from dotenv import load_dotenv

    # 加载.env文件
    env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
    if os.path.exists(env_path):
        load_dotenv(env_path)
except ImportError:
    # 如果没有安装python-dotenv，跳过
    pass


class Settings:
    """应用配置"""

    def __init__(self):
        # 应用配置
        self.APP_NAME: str = "Enterprise Service Platform"
        self.APP_VERSION: str = "2.0.0"
        self.DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
        self.ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")

        # 数据库配置 - 主数据库
        self.DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./waterms.db")
        self.DATABASE_POOL_SIZE: int = int(os.getenv("DATABASE_POOL_SIZE", "10"))
        self.DATABASE_MAX_OVERFLOW: int = int(os.getenv("DATABASE_MAX_OVERFLOW", "20"))
        self.DATABASE_POOL_PRE_PING: bool = True

        self._is_sqlite: bool = self.DATABASE_URL.startswith("sqlite")

        # 数据库配置 - 会议室数据库
        self.MEETING_DATABASE_URL: Optional[str] = self._get_meeting_db_url()

        # 安全配置
        self.SECRET_KEY: str = self._get_secret_key()
        self.ALGORITHM: str = "HS256"
        self.ACCESS_TOKEN_EXPIRE_HOURS: int = 24

        # JWT配置
        self.JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", self.SECRET_KEY)
        self.JWT_ALGORITHM: str = "HS256"
        self.JWT_EXPIRE_HOURS: int = 2

        # 密码策略
        self.MIN_PASSWORD_LENGTH: int = int(os.getenv("MIN_PASSWORD_LENGTH", "8"))
        self.REQUIRE_SPECIAL_CHAR: bool = (
            os.getenv("REQUIRE_SPECIAL_CHAR", "false").lower() == "true"
        )
        self.REQUIRE_NUMBER: bool = (
            os.getenv("REQUIRE_NUMBER", "false").lower() == "true"
        )

        # 默认管理员配置
        self.DEFAULT_ADMIN_USERNAME: str = "admin"
        self.DEFAULT_ADMIN_PASSWORD: str = "admin123"

        # CORS配置
        self.CORS_ALLOW_ORIGINS: list = [
            "http://jhw-ai.com",
            "https://jhw-ai.com",
            "http://www.jhw-ai.com",
            "https://www.jhw-ai.com",
            "http://localhost",
            "http://localhost:8080",
            "http://localhost:8000",
            "http://127.0.0.1",
            "http://127.0.0.1:8080",
            "http://127.0.0.1:8000",
        ]
        self.CORS_ALLOW_CREDENTIALS: bool = True
        self.CORS_ALLOW_METHODS: list = ["*"]
        self.CORS_ALLOW_HEADERS: list = ["*"]

        # 日志配置
        self.LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
        self.LOG_FILE: str = "logs/app.log"
        self.LOG_MAX_BYTES: int = 10485760  # 10MB
        self.LOG_BACKUP_COUNT: int = 10

        # 业务配置
        self.DEFAULT_CREDIT_BALANCE: float = 0.0
        self.PROMOTION_DEFAULT_TRIGGER_QTY: int = 10
        self.PROMOTION_DEFAULT_GIFT_QTY: int = 1

        # 服务器配置
        self.HOST: str = "0.0.0.0"
        self.PORT: int = int(os.getenv("PORT", "8000"))

    def _get_secret_key(self) -> str:
        """获取密钥"""
        secret_key = os.getenv("SECRET_KEY")
        if not secret_key:
            if self.ENVIRONMENT == "development":
                secret_key = "dev-secret-key-change-in-production-2026"
            else:
                raise ValueError(
                    "SECRET_KEY environment variable must be set in production"
                )
        return secret_key

    def _get_meeting_db_url(self) -> str:
        """获取会议室数据库URL"""
        meeting_db_url = os.getenv("MEETING_DATABASE_URL")
        if not meeting_db_url:
            backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            meeting_db = os.path.join(
                backend_dir, "../../Service_MeetingRoom/backend/meeting.db"
            )
            meeting_db = os.path.abspath(meeting_db)
            meeting_db_url = f"sqlite:///{meeting_db}"
        return meeting_db_url


# 全局配置实例
_settings = None


def get_settings() -> Settings:
    """获取配置实例（单例模式）"""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


# 便捷访问
settings = get_settings()
