"""会议室数据库配置"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator

from config.settings import settings


# 创建数据库引擎
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False},
    pool_pre_ping=True,
    echo=settings.ENVIRONMENT == "development",
)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """获取数据库会话（依赖注入）"""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


# 向后兼容导出
Base = None  # Base应在models/base中定义
