"""
会员套餐表添加icon字段迁移脚本
执行方式: python add_icon_to_membership_plans.py
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import text
from config.database import db_manager


def migrate():
    """添加icon字段到membership_plans表"""
    print("开始迁移: 添加icon字段到membership_plans表...")

    engine = db_manager.main_engine

    with engine.connect() as conn:
        try:
            # 检查字段是否已存在
            if db_manager._main_engine.dialect.name == "sqlite":
                result = conn.execute(text("PRAGMA table_info(membership_plans)"))
                columns = [row[1] for row in result.fetchall()]
            else:
                result = conn.execute(
                    text("""
                    SELECT COLUMN_NAME 
                    FROM INFORMATION_SCHEMA.COLUMNS 
                    WHERE TABLE_NAME = 'membership_plans'
                """)
                )
                columns = [row[0] for row in result.fetchall()]

            if "icon" in columns:
                print("字段 'icon' 已存在，跳过迁移")
                return

            # 添加icon字段
            if db_manager._main_engine.dialect.name == "sqlite":
                conn.execute(
                    text("""
                    ALTER TABLE membership_plans 
                    ADD COLUMN icon VARCHAR(50) DEFAULT '👑'
                """)
                )
            else:
                conn.execute(
                    text("""
                    ALTER TABLE membership_plans 
                    ADD COLUMN icon VARCHAR(50) DEFAULT '👑' COMMENT '套餐图标'
                """)
                )

            conn.commit()
            print("迁移完成: icon字段已添加")

            # 更新现有记录的icon
            conn.execute(
                text("""
                UPDATE membership_plans 
                SET icon = '👑' 
                WHERE icon IS NULL
            """)
            )
            conn.commit()
            print("已更新现有记录的icon默认值")

        except Exception as e:
            print(f"迁移失败: {e}")
            raise


if __name__ == "__main__":
    migrate()
