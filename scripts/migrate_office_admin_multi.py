"""
数据库迁移脚本：支持办公室管理员管理多个办公室
迁移现有的office_admin用户的department字段到office_admin_relations表
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from config.database import get_db_url
from datetime import datetime


def migrate():
    engine = create_engine(get_db_url())
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        print("开始迁移...")

        result = session.execute(
            text("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='office_admin_relations'
        """)
        )

        if not result.fetchone():
            print("创建 office_admin_relations 表...")
            session.execute(
                text("""
                CREATE TABLE office_admin_relations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    office_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    is_primary INTEGER DEFAULT 0,
                    role_type INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(office_id, user_id)
                )
            """)
            )
            session.commit()
            print("表创建成功")

        session.execute(
            text(
                "CREATE INDEX IF NOT EXISTS idx_office_admin_office ON office_admin_relations(office_id)"
            )
        )
        session.execute(
            text(
                "CREATE INDEX IF NOT EXISTS idx_office_admin_user ON office_admin_relations(user_id)"
            )
        )
        session.commit()

        print("迁移现有office_admin用户数据...")
        office_admins = session.execute(
            text("""
            SELECT id, department FROM users 
            WHERE role = 'office_admin' AND department IS NOT NULL AND department != ''
        """)
        ).fetchall()

        migrated_count = 0
        for user in office_admins:
            office = session.execute(
                text("""
                SELECT id FROM office WHERE name = :name
            """),
                {"name": user.department},
            ).fetchone()

            if office:
                existing = session.execute(
                    text("""
                    SELECT id FROM office_admin_relations 
                    WHERE office_id = :office_id AND user_id = :user_id
                """),
                    {"office_id": office.id, "user_id": user.id},
                ).fetchone()

                if not existing:
                    session.execute(
                        text("""
                        INSERT INTO office_admin_relations (office_id, user_id, is_primary, role_type, created_at)
                        VALUES (:office_id, :user_id, 1, 1, :created_at)
                    """),
                        {
                            "office_id": office.id,
                            "user_id": user.id,
                            "is_primary": 1,
                            "created_at": datetime.now().isoformat(),
                        },
                    )
                    migrated_count += 1
                    print(f"  用户 {user.id} -> 办公室 {office.id} ({user.department})")

        session.commit()
        print(f"\n迁移完成！共迁移 {migrated_count} 条记录")

        count_result = session.execute(
            text("SELECT COUNT(*) FROM office_admin_relations")
        )
        total = count_result.fetchone()[0]
        print(f"office_admin_relations 表现有 {total} 条记录")

    except Exception as e:
        print(f"迁移失败: {e}")
        session.rollback()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    migrate()
