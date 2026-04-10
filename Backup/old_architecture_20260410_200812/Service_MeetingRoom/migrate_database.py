"""
会议室管理模块数据库迁移脚本
添加灵活时间段选择所需字段和管理员权限表
"""

import sqlite3
import os
from datetime import datetime

# 数据库路径
DB_PATH = (
    "/Users/sgl/PycharmProjects/AIchanyejiqun/Service_MeetingRoom/backend/meeting.db"
)


def backup_database():
    """备份数据库"""
    backup_path = DB_PATH + ".backup_" + datetime.now().strftime("%Y%m%d_%H%M%S")
    if os.path.exists(DB_PATH):
        import shutil

        shutil.copy2(DB_PATH, backup_path)
        print(f"✓ 数据库已备份到: {backup_path}")
        return backup_path
    return None


def migrate_database():
    """执行数据库迁移"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("=" * 70)
    print("会议室管理模块数据库迁移")
    print("=" * 70)

    try:
        # 1. 备份数据库
        backup_database()

        # 2. 检查并添加 meeting_bookings 表的新字段
        print("\n步骤1: 检查 meeting_bookings 表字段...")

        # 获取现有字段
        cursor.execute("PRAGMA table_info(meeting_bookings)")
        existing_columns = {row[1] for row in cursor.fetchall()}

        # 需要添加的字段
        new_columns = {
            "start_time": "VARCHAR(10)",
            "end_time": "VARCHAR(10)",
            "can_modify": "BOOLEAN DEFAULT 1",
            "can_cancel": "BOOLEAN DEFAULT 1",
            "cancel_deadline": "VARCHAR(20)",
            "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
            "updated_at": "TIMESTAMP",
            "reviewer_id": "INTEGER",
            "reviewed_at": "TIMESTAMP",
        }

        for column_name, column_type in new_columns.items():
            if column_name not in existing_columns:
                try:
                    cursor.execute(
                        f"ALTER TABLE meeting_bookings ADD COLUMN {column_name} {column_type}"
                    )
                    print(f"  ✓ 添加字段: {column_name}")
                except Exception as e:
                    print(f"  ⚠ 字段 {column_name} 可能已存在: {e}")

        conn.commit()

        # 3. 创建管理员相关表
        print("\n步骤2: 创建管理员权限表...")

        # 创建角色表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS admin_roles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                role_name VARCHAR(50) UNIQUE NOT NULL,
                permissions TEXT,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("  ✓ 创建表: admin_roles")

        # 创建用户表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS admin_users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username VARCHAR(50) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                email VARCHAR(100),
                role_id INTEGER,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP,
                FOREIGN KEY (role_id) REFERENCES admin_roles(id)
            )
        """)
        print("  ✓ 创建表: admin_users")

        # 创建操作日志表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS admin_operation_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                operation_type VARCHAR(50),
                operation_content TEXT,
                operation_result VARCHAR(20),
                ip_address VARCHAR(50),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES admin_users(id)
            )
        """)
        print("  ✓ 创建表: admin_operation_logs")

        # 4. 初始化默认角色
        print("\n步骤3: 初始化默认角色...")

        roles = [
            (1, "超级管理员", '["all"]', "拥有所有权限"),
            (
                2,
                "会议室管理员",
                '["booking_manage", "room_manage", "stats_view"]',
                "管理预约和会议室",
            ),
            (
                3,
                "财务人员",
                '["booking_view", "stats_view", "finance_report"]',
                "查看预约和财务报表",
            ),
            (4, "普通员工", '["booking_view"]', "仅查看预约"),
        ]

        for role_id, role_name, permissions, description in roles:
            try:
                cursor.execute(
                    "INSERT OR IGNORE INTO admin_roles (id, role_name, permissions, description) VALUES (?, ?, ?, ?)",
                    (role_id, role_name, permissions, description),
                )
                if cursor.rowcount > 0:
                    print(f"  ✓ 创建角色: {role_name}")
            except Exception as e:
                print(f"  ⚠ 角色 {role_name} 已存在")

        # 5. 创建默认超级管理员
        print("\n步骤4: 创建默认超级管理员账号...")

        from passlib.context import CryptContext

        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        hashed_password = pwd_context.hash("admin123")

        try:
            cursor.execute(
                "INSERT OR IGNORE INTO admin_users (username, password_hash, role_id, is_active) VALUES (?, ?, ?, ?)",
                ("admin", hashed_password, 1, 1),
            )
            if cursor.rowcount > 0:
                print("  ✓ 创建管理员账号: admin/admin123")
                print("  ⚠ 请在生产环境中修改默认密码！")
        except Exception as e:
            print("  ⚠ 管理员账号已存在")

        conn.commit()

        # 6. 数据迁移：更新现有预约记录的时间字段
        print("\n步骤5: 迁移现有预约数据...")

        # 检查是否有需要迁移的数据
        cursor.execute("""
            SELECT id, time_slot FROM meeting_bookings 
            WHERE start_time IS NULL OR end_time IS NULL
        """)

        bookings_to_migrate = cursor.fetchall()

        if bookings_to_migrate:
            print(f"  发现 {len(bookings_to_migrate)} 条预约记录需要迁移")

            time_slot_map = {
                "09:00-12:00": ("09:00", "12:00"),
                "14:00-18:00": ("14:00", "18:00"),
                "19:00-21:00": ("19:00", "21:00"),
            }

            for booking_id, time_slot in bookings_to_migrate:
                if time_slot in time_slot_map:
                    start_time, end_time = time_slot_map[time_slot]
                    cursor.execute(
                        """
                        UPDATE meeting_bookings 
                        SET start_time = ?, end_time = ?, updated_at = ?
                        WHERE id = ?
                    """,
                        (
                            start_time,
                            end_time,
                            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            booking_id,
                        ),
                    )

            conn.commit()
            print(f"  ✓ 迁移了 {len(bookings_to_migrate)} 条预约记录")
        else:
            print("  ✓ 无需迁移数据")

        # 7. 验证迁移结果
        print("\n步骤6: 验证迁移结果...")

        # 检查表结构
        cursor.execute("PRAGMA table_info(meeting_bookings)")
        columns = cursor.fetchall()
        print(f"  meeting_bookings 表字段数: {len(columns)}")

        cursor.execute("SELECT COUNT(*) FROM admin_roles")
        role_count = cursor.fetchone()[0]
        print(f"  admin_roles 表记录数: {role_count}")

        cursor.execute("SELECT COUNT(*) FROM admin_users")
        user_count = cursor.fetchone()[0]
        print(f"  admin_users 表记录数: {user_count}")

        print("\n" + "=" * 70)
        print("✓ 数据库迁移成功完成！")
        print("=" * 70)
        print("\n默认管理员账号:")
        print("  用户名: admin")
        print("  密码: admin123")
        print("  ⚠ 请立即修改默认密码！")

        return True

    except Exception as e:
        conn.rollback()
        print(f"\n✗ 迁移失败: {e}")
        import traceback

        traceback.print_exc()
        return False
    finally:
        conn.close()


if __name__ == "__main__":
    # 检查数据库是否存在
    if not os.path.exists(DB_PATH):
        print(f"✗ 数据库文件不存在: {DB_PATH}")
        print("请先确保数据库已创建")
    else:
        migrate_database()
