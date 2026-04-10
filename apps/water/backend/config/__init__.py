"""
配置管理包
统一管理所有配置项
"""

from config.settings import settings, get_settings
from config.database import db_manager, get_db, get_meeting_db

__all__ = [
    "settings",
    "get_settings",
    "db_manager",
    "get_db",
    "get_meeting_db",
]
