"""
Water Service Centralized Database Module
统一水服务数据库连接 — 所有水服务模块共享此数据库连接

注意: 水服务当前使用独立的 waterms.db，与主应用 app.db 物理隔离。
未来可将唯一的水服务表迁移至主数据库，重叠表使用主应用模型替代。
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
import os

# 水服务独立数据库 URL
# 与主应用 data/app.db 物理隔离
_WATER_DB_PATH = os.path.join(os.path.dirname(__file__), "waterms.db")
SQLALCHEMY_DATABASE_URL = f"sqlite:///{_WATER_DB_PATH}"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """获取水服务数据库会话（依赖注入）"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
