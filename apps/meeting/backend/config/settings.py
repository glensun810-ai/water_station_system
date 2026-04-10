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

        # 数据库配置 - 使用统一数据库waterms.db
        # 默认使用Service_WaterManage下的waterms.db作为统一数据库
        project_root = os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        )
        default_db_path = os.path.join(
            project_root, "Service_WaterManage", "backend", "waterms.db"
        )
        default_db_url = f"sqlite:///{os.path.abspath(default_db_path)}"
        self.DATABASE_URL: str = os.getenv("MEETING_DATABASE_URL", default_db_url)

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
