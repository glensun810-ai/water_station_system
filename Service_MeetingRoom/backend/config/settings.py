"""会议室服务配置"""

import os
from typing import List, Optional


class MeetingSettings:
    """会议室服务设置"""

    def __init__(self):
        # 应用信息
        self.APP_NAME: str = "会议室预约服务"
        self.APP_VERSION: str = "1.0.0"
        self.ENVIRONMENT: str = "development"

        # 数据库配置
        self.DATABASE_URL: str = os.getenv(
            "MEETING_DATABASE_URL", "sqlite:///./meeting.db"
        )

        # CORS配置
        self.CORS_ALLOW_ORIGINS: List[str] = ["*"]
        self.CORS_ALLOW_CREDENTIALS: bool = True
        self.CORS_ALLOW_METHODS: List[str] = ["*"]
        self.CORS_ALLOW_HEADERS: List[str] = ["*"]

        # JWT配置
        self.SECRET_KEY: str = os.getenv(
            "SECRET_KEY", "meeting-secret-key-change-in-production"
        )
        self.ALGORITHM: str = "HS256"
        self.ACCESS_TOKEN_EXPIRE_HOURS: int = 24

        # 服务器配置
        self.HOST: str = "0.0.0.0"
        self.PORT: int = 8001


settings = MeetingSettings()
