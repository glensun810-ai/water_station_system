"""用餐服务配置"""

import os
from typing import List, Optional


class DiningSettings:
    """用餐服务设置"""

    def __init__(self):
        # 应用信息
        self.APP_NAME: str = "用餐服务"
        self.APP_VERSION: str = "1.0.0"
        self.ENVIRONMENT: str = "development"

        # 数据库配置
        self.DATABASE_URL: str = os.getenv(
            "DINING_DATABASE_URL", "sqlite:///./dining.db"
        )

        # CORS配置
        self.CORS_ALLOW_ORIGINS: List[str] = ["*"]
        self.CORS_ALLOW_CREDENTIALS: bool = True
        self.CORS_ALLOW_METHODS: List[str] = ["*"]
        self.CORS_ALLOW_HEADERS: List[str] = ["*"]

        # 服务器配置
        self.HOST: str = "0.0.0.0"
        self.PORT: int = 8002


settings = DiningSettings()
