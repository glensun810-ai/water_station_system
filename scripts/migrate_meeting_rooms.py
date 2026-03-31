#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
会议室预约表结构迁移脚本
添加缺失字段：title, attendee_count, description, charged_hours, total_hours, free_hours
"""

import sqlite3
from pathlib import Path

# 数据库路径（主应用数据库）
DB_PATH = Path(__file__).parent.parent / "waterms.db"


def migrate():
    """执行数据库迁移"""
    if not DB_PATH.exists():
        print(f"❌ 数据库文件不存在：{DB_PATH}")
        return False

    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    try:
        # 获取现有列
        cursor.execute("PRAGMA table_info(reservations)")
        existing_columns = {row[1] for row in cursor.fetchall()}

        # 需要添加的字段
        new_columns = [
            ("title", "VARCHAR(200)"),
            ("attendee_count", "INTEGER DEFAULT 0"),
            ("description", "TEXT"),
            ("charged_hours", "REAL DEFAULT 0"),
            ("total_hours", "REAL DEFAULT 0"),
            ("free_hours", "REAL DEFAULT 0"),
            ("cancelled_by", "INTEGER"),
            ("created_by", "INTEGER"),
        ]

        added = []
        for column_name, column_type in new_columns:
            if column_name not in existing_columns:
                sql = f"ALTER TABLE reservations ADD COLUMN {column_name} {column_type}"
                cursor.execute(sql)
                added.append(column_name)
                print(f"✅ 添加字段：{column_name}")
            else:
                print(f"✓ 字段已存在：{column_name}")

        if added:
            conn.commit()
            print(f"\n✅ 迁移完成！添加了 {len(added)} 个字段")
            return True
        else:
            print("\n✅ 数据库已是最新")
            return True

    except Exception as e:
        print(f"❌ 迁移失败：{e}")
        conn.rollback()
        return False
    finally:
        conn.close()


if __name__ == "__main__":
    migrate()
