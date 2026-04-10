#!/usr/bin/env python3
"""
AI产业集群空间服务系统 - 数据库配置更新脚本

更新应用程序配置以使用PostgreSQL而不是SQLite
"""

import os
import re
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class DatabaseConfigUpdater:
    """数据库配置更新器"""

    def __init__(self):
        self.water_backend_dir = "apps/water/backend"
        self.meeting_backend_dir = "apps/meeting/backend"

    def update_water_database_config(self):
        """更新水站服务的数据库配置"""
        logger.info("Updating water service database configuration...")

        # 查找并更新包含数据库URL的文件
        files_to_update = ["main.py", "core/config.py", "api_unified.py", "run.py"]

        for filename in files_to_update:
            filepath = os.path.join(self.water_backend_dir, filename)
            if os.path.exists(filepath):
                self._update_file_database_url(filepath)

        logger.info("Water service database configuration updated successfully!")

    def update_meeting_database_config(self):
        """更新会议室服务的数据库配置"""
        logger.info("Updating meeting service database configuration...")

        # 查找并更新包含数据库URL的文件
        files_to_update = ["main.py", "core/config.py", "run.py"]

        for filename in files_to_update:
            filepath = os.path.join(self.meeting_backend_dir, filename)
            if os.path.exists(filepath):
                self._update_file_database_url(filepath)

        logger.info("Meeting service database configuration updated successfully!")

    def _update_file_database_url(self, filepath: str):
        """更新单个文件中的数据库URL"""
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()

            # 替换SQLite URL为PostgreSQL URL
            original_content = content

            # 匹配各种可能的SQLite URL格式
            sqlite_patterns = [
                r"sqlite:///\.\/waterms\.db",
                r"sqlite:///waterms\.db",
                r'"sqlite:///.*?waterms\.db"',
                r"'sqlite:///.*?waterms\.db'",
                r'SQLALCHEMY_DATABASE_URL.*?=.*?"sqlite:///',
                r'database_url.*?=.*?"sqlite:///',
            ]

            postgres_url = "postgresql://ai_cluster:secure_password_2026@localhost:5432/ai_cluster_db"

            updated = False
            for pattern in sqlite_patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    # 替换为PostgreSQL URL
                    content = re.sub(
                        pattern,
                        f'SQLALCHEMY_DATABASE_URL = "{postgres_url}"',
                        content,
                        flags=re.IGNORECASE,
                    )
                    updated = True

            # 如果文件中没有找到SQLite URL，但包含engine创建代码，也进行更新
            if not updated and "create_engine" in content:
                # 查找create_engine调用
                engine_pattern = r"create_engine\([^)]*sqlite[^)]*\)"
                if re.search(engine_pattern, content):
                    content = re.sub(
                        engine_pattern,
                        f'create_engine("{postgres_url}", pool_pre_ping=True, pool_size=10, max_overflow=20)',
                        content,
                    )
                    updated = True

            if updated and content != original_content:
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(content)
                logger.info(f"Updated database URL in {filepath}")
            elif updated:
                logger.info(f"No changes needed in {filepath}")
            else:
                logger.debug(f"No SQLite URLs found in {filepath}")

        except Exception as e:
            logger.error(f"Failed to update {filepath}: {e}")

    def create_database_connection_module(self):
        """创建统一的数据库连接模块"""
        logger.info("Creating unified database connection module...")

        db_module_content = '''
"""
统一数据库连接模块
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool

# PostgreSQL数据库配置
DATABASE_URL = "postgresql://ai_cluster:secure_password_2026@localhost:5432/ai_cluster_db"

# 创建引擎（带连接池）
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=False  # 生产环境设为False
)

# 创建会话工厂
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False, 
    bind=engine
)

def get_db():
    """
    数据库会话依赖注入
    使用方式: db: Session = Depends(get_db)
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 导出常用对象
__all__ = ['engine', 'SessionLocal', 'get_db', 'DATABASE_URL']
'''

        # 为水站服务创建
        water_db_module = os.path.join(self.water_backend_dir, "database.py")
        with open(water_db_module, "w") as f:
            f.write(db_module_content)

        # 为会议室服务创建
        meeting_db_module = os.path.join(self.meeting_backend_dir, "database.py")
        with open(meeting_db_module, "w") as f:
            f.write(db_module_content)

        logger.info("Unified database connection modules created!")

    def update_requirements(self):
        """更新依赖包要求"""
        logger.info("Updating requirements.txt files...")

        # 水站服务
        water_requirements = os.path.join(
            self.water_backend_dir, "..", "..", "backend", "requirements.txt"
        )
        if os.path.exists(water_requirements):
            self._update_requirements_file(water_requirements)

        # 会议室服务
        meeting_requirements = os.path.join(
            self.meeting_backend_dir, "..", "..", "backend", "requirements.txt"
        )
        if os.path.exists(meeting_requirements):
            self._update_requirements_file(meeting_requirements)

        logger.info("Requirements files updated successfully!")

    def _update_requirements_file(self, filepath: str):
        """更新requirements.txt文件"""
        try:
            with open(filepath, "r") as f:
                lines = f.readlines()

            # 确保包含PostgreSQL驱动
            has_psycopg2 = any("psycopg2" in line for line in lines)
            has_sqlalchemy = any("sqlalchemy" in line for line in lines)

            if not has_psycopg2:
                # 移除sqlite3相关依赖（如果有）
                lines = [line for line in lines if "sqlite" not in line.lower()]
                # 添加PostgreSQL依赖
                lines.append("psycopg2-binary>=2.9.0\n")

            if not has_sqlalchemy:
                lines.append("SQLAlchemy>=1.4.0\n")

            with open(filepath, "w") as f:
                f.writelines(lines)

            logger.info(f"Updated requirements file: {filepath}")

        except Exception as e:
            logger.error(f"Failed to update {filepath}: {e}")

    def run_updates(self):
        """执行所有配置更新"""
        try:
            logger.info("Starting database configuration updates...")

            self.update_water_database_config()
            self.update_meeting_database_config()
            self.create_database_connection_module()
            self.update_requirements()

            logger.info("All database configuration updates completed successfully!")

        except Exception as e:
            logger.error(f"Database configuration updates failed: {e}")
            raise


def main():
    """主函数"""
    updater = DatabaseConfigUpdater()
    updater.run_updates()


if __name__ == "__main__":
    main()
