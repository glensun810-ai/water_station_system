#!/usr/bin/env python3
"""
管理员安全增强迁移脚本
- 添加 is_hidden 列到 users 表
- 创建 sgl810 隐藏超级管理员账户
- 幂等：可安全重复执行
"""

import sqlite3
import os
import sys
from datetime import datetime


def get_db_path():
    """获取数据库路径（兼容 DATABASE_URL 环境变量）"""
    db_url = os.getenv("DATABASE_URL", "sqlite:///./data/app.db")
    if db_url.startswith("sqlite:///"):
        return db_url.replace("sqlite:///", "")
    print(f"非 SQLite 数据库: {db_url}")
    print("请手动执行以下 SQL:")
    print("  ALTER TABLE users ADD COLUMN IF NOT EXISTS is_hidden INTEGER DEFAULT 0;")
    print("  INSERT INTO users (username, name, role, password_hash, is_active, is_hidden, created_at, updated_at)")
    print("  VALUES ('sgl810', 'sgl810', 'super_admin', '<BCRYPT_HASH>', 1, 1, NOW(), NOW())")
    print("  ON CONFLICT (username) DO UPDATE SET role='super_admin', is_hidden=1, is_active=1;")
    sys.exit(0)


def migrate(db_path: str):
    """执行迁移"""
    if not os.path.exists(db_path):
        print(f"数据库不存在: {db_path}")
        sys.exit(1)

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    # 1. 添加 is_hidden 列（如果不存在）
    try:
        cur.execute("ALTER TABLE users ADD COLUMN is_hidden INTEGER DEFAULT 0")
        print("[OK] 添加 is_hidden 列")
    except sqlite3.OperationalError as e:
        if "duplicate column" in str(e).lower():
            print("[SKIP] is_hidden 列已存在")
        else:
            raise

    # 2. 创建/更新 sgl810 超级管理员
    password_hash = "$2b$12$zvXDe2Mp3mVuBmHz5c78UulfyQullHpjvl4fel/saKDzKeBhnQ7e."

    cur.execute("SELECT id, role, is_hidden FROM users WHERE username = 'sgl810'")
    existing = cur.fetchone()

    if existing:
        cur.execute(
            "UPDATE users SET role='super_admin', is_hidden=1, is_active=1 WHERE username='sgl810'"
        )
        print(f"[OK] 更新 sgl810: role=super_admin, is_hidden=1")
    else:
        cur.execute(
            """
            INSERT INTO users (username, name, role, password_hash, is_active, is_hidden, created_at, updated_at)
            VALUES ('sgl810', 'sgl810', 'super_admin', ?, 1, 1, ?, ?)
            """,
            (password_hash, datetime.now().isoformat(), datetime.now().isoformat()),
        )
        print(f"[OK] 创建 sgl810 超级管理员 (is_hidden=1)")

    conn.commit()

    # 验证
    cur.execute("SELECT id, username, role, is_hidden, is_active FROM users WHERE username IN ('sgl810', 'admin')")
    for row in cur.fetchall():
        print(f"[VERIFY] id={row[0]}, username={row[1]}, role={row[2]}, is_hidden={row[3]}, is_active={row[4]}")

    conn.close()
    print("[DONE] 迁移完成")


if __name__ == "__main__":
    db_path = get_db_path()
    print(f"数据库路径: {db_path}")
    migrate(db_path)
