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
        self.SECRET_KEY: str = os.getenv(
            "SECRET_KEY", "ai-industry-cluster-secret-key-change-in-production"
        )
        self.ALGORITHM: str = "HS256"
        self.ACCESS_TOKEN_EXPIRE_HOURS: int = int(
            os.getenv("ACCESS_TOKEN_EXPIRE_HOURS", "24")
        )

        # 服务器配置
        self.HOST: str = os.getenv("HOST", "0.0.0.0")
        self.PORT: int = int(os.getenv("PORT", "8000"))


settings = Settings()
