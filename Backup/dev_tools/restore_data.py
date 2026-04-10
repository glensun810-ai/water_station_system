"""
从历史数据库恢复完整数据 - 修正版
"""

import sqlite3
from datetime import datetime

# 数据库路径
CURRENT_DB = "./data/app.db"
HISTORY_WATER_DB = (
    "./Backup/old_architecture_20260410_200812/Service_WaterManage/backend/waterms.db"
)
HISTORY_MEETING_DB = (
    "./Backup/old_architecture_20260410_200812/Service_MeetingRoom/backend/meeting.db"
)


def backup_current_data():
    """备份当前数据"""
    print("=" * 60)
    print("步骤1: 备份当前数据")
    print("=" * 60)

    import shutil

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = f"./Backup/current_data_backup_{timestamp}.db"
    shutil.copy(CURRENT_DB, backup_file)
    print(f"✓ 当前数据已备份到: {backup_file}")
    return backup_file


def clear_current_data():
    """清空当前数据表"""
    print("\n" + "=" * 60)
    print("步骤2: 清空当前数据表")
    print("=" * 60)

    conn = sqlite3.connect(CURRENT_DB)
    cursor = conn.cursor()

    tables = [
        "products",
        "users",
        "office",
        "office_pickup",
        "meeting_rooms",
        "meeting_bookings",
    ]

    for table in tables:
        try:
            cursor.execute(f"DELETE FROM {table}")
            print(f"✓ 已清空表: {table}")
        except Exception as e:
            print(f"✗ 清空表 {table} 失败: {str(e)}")

    conn.commit()
    conn.close()


def restore_products():
    """恢复产品数据"""
    print("\n" + "=" * 60)
    print("步骤3: 恢复产品数据")
    print("=" * 60)

    hist_conn = sqlite3.connect(HISTORY_WATER_DB)
    hist_cursor = hist_conn.cursor()

    curr_conn = sqlite3.connect(CURRENT_DB)
    curr_cursor = curr_conn.cursor()

    # 读取历史产品数据（只读取当前表有的字段）
    hist_cursor.execute("""
        SELECT id, name, specification, unit, price, stock, 
               promo_threshold, promo_gift, is_active, 
               NULL as cost_price, NULL as image_url, NULL as description,
               NULL as category_id, NULL as barcode, 0 as is_protected,
               'water' as service_type, NULL as resource_config,
               0 as booking_required, 10 as advance_booking_days
        FROM products
    """)
    products = hist_cursor.fetchall()

    print(f"历史产品数据: {len(products)} 条")

    # 插入到当前数据库
    for product in products:
        try:
            curr_cursor.execute(
                """
                INSERT INTO products 
                (id, name, specification, unit, price, stock,
                 promo_threshold, promo_gift, is_active, cost_price,
                 image_url, description, category_id, barcode, is_protected,
                 service_type, resource_config, booking_required, advance_booking_days)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                product,
            )
            print(f"  ✓ 产品: {product[1]} ({product[2]})")
        except Exception as e:
            print(f"  ✗ 产品插入失败: {str(e)}")

    curr_conn.commit()
    hist_conn.close()
    curr_conn.close()

    print(f"✓ 产品数据恢复完成")


def restore_users():
    """恢复用户数据"""
    print("\n" + "=" * 60)
    print("步骤4: 恢复用户数据")
    print("=" * 60)

    hist_conn = sqlite3.connect(HISTORY_WATER_DB)
    hist_cursor = hist_conn.cursor()

    curr_conn = sqlite3.connect(CURRENT_DB)
    curr_cursor = curr_conn.cursor()

    # 读取历史用户数据（历史表字段: id, name, department, role, password_hash...）
    hist_cursor.execute("SELECT * FROM users")
    users = hist_cursor.fetchall()

    print(f"历史用户数据: {len(users)} 条")

    # 插入到当前数据库（字段映射）
    for user in users:
        try:
            # 历史: id, name, department, role, password_hash, balance_credit, is_active, ...
            # 当前: id, username, name, department, role, password_hash, ...
            user_id = user[0]
            username = user[1]  # 历史name字段作为username
            name = user[1]  # name字段
            department = user[2]
            role = user[3]
            password_hash = user[4]
            balance_credit = user[5] if len(user) > 5 else 0.0
            is_active = user[6] if len(user) > 6 else 1
            user_type = user[7] if len(user) > 7 else "internal"
            phone = user[8] if len(user) > 8 else None
            email = user[9] if len(user) > 9 else None
            company = user[10] if len(user) > 10 else None
            last_login = user[11] if len(user) > 11 else None
            created_at = user[12] if len(user) > 12 else None
            updated_at = user[13] if len(user) > 13 else None

            curr_cursor.execute(
                """
                INSERT INTO users
                (id, username, name, department, role, password_hash,
                 balance_credit, is_active, user_type, phone, email,
                 company, last_login, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    user_id,
                    username,
                    name,
                    department,
                    role,
                    password_hash,
                    balance_credit,
                    is_active,
                    user_type,
                    phone,
                    email,
                    company,
                    last_login,
                    created_at,
                    updated_at,
                ),
            )
            print(f"  ✓ 用户: {username} ({department} - {role})")
        except Exception as e:
            print(f"  ✗ 用户插入失败: {str(e)}")

    curr_conn.commit()
    hist_conn.close()
    curr_conn.close()

    print(f"✓ 用户数据恢复完成")


def restore_offices():
    """恢复办公室数据"""
    print("\n" + "=" * 60)
    print("步骤5: 恢复办公室数据")
    print("=" * 60)

    hist_conn = sqlite3.connect(HISTORY_WATER_DB)
    hist_cursor = hist_conn.cursor()

    curr_conn = sqlite3.connect(CURRENT_DB)
    curr_cursor = curr_conn.cursor()

    # 读取历史办公室数据
    hist_cursor.execute("SELECT * FROM office")
    offices = hist_cursor.fetchall()

    print(f"历史办公室数据: {len(offices)} 条")

    # 插入到当前数据库
    for office in offices:
        try:
            # 字段数量应该匹配
            placeholders = ",".join(["?" for _ in office])
            curr_cursor.execute(f"INSERT INTO office VALUES ({placeholders})", office)
            print(f"  ✓ 办公室: {office[1]} ({office[2]})")
        except Exception as e:
            print(f"  ✗ 办公室插入失败: {str(e)}")

    curr_conn.commit()
    hist_conn.close()
    curr_conn.close()

    print(f"✓ 办公室数据恢复完成")


def restore_pickups():
    """恢复领水记录"""
    print("\n" + "=" * 60)
    print("步骤6: 恢复领水记录")
    print("=" * 60)

    hist_conn = sqlite3.connect(HISTORY_WATER_DB)
    hist_cursor = hist_conn.cursor()

    curr_conn = sqlite3.connect(CURRENT_DB)
    curr_cursor = curr_conn.cursor()

    # 读取历史领水记录
    hist_cursor.execute("SELECT * FROM office_pickup")
    pickups = hist_cursor.fetchall()

    print(f"历史领水记录: {len(pickups)} 条")

    # 插入到当前数据库
    for pickup in pickups:
        try:
            placeholders = ",".join(["?" for _ in pickup])
            curr_cursor.execute(
                f"INSERT INTO office_pickup VALUES ({placeholders})", pickup
            )
        except Exception as e:
            print(f"  ✗ 领水记录插入失败: {str(e)}")

    curr_conn.commit()
    hist_conn.close()
    curr_conn.close()

    print(f"✓ 领水记录恢复完成: {len(pickups)} 条")


def restore_meeting_rooms():
    """恢复会议室数据"""
    print("\n" + "=" * 60)
    print("步骤7: 恢复会议室数据")
    print("=" * 60)

    hist_conn = sqlite3.connect(HISTORY_MEETING_DB)
    hist_cursor = hist_conn.cursor()

    curr_conn = sqlite3.connect(CURRENT_DB)
    curr_cursor = curr_conn.cursor()

    # 读取历史会议室数据
    hist_cursor.execute("SELECT * FROM meeting_rooms")
    rooms = hist_cursor.fetchall()

    print(f"历史会议室数据: {len(rooms)} 条")

    # 插入到当前数据库
    for room in rooms:
        try:
            placeholders = ",".join(["?" for _ in room])
            curr_cursor.execute(
                f"INSERT INTO meeting_rooms VALUES ({placeholders})", room
            )
            print(f"  ✓ 会议室: {room[1]} ({room[2]}, 容纳{room[3]}人)")
        except Exception as e:
            print(f"  ✗ 会议室插入失败: {str(e)}")

    curr_conn.commit()
    hist_conn.close()
    curr_conn.close()

    print(f"✓ 会议室数据恢复完成")


def restore_bookings():
    """恢复预约数据"""
    print("\n" + "=" * 60)
    print("步骤8: 恢复预约数据")
    print("=" * 60)

    hist_conn = sqlite3.connect(HISTORY_MEETING_DB)
    hist_cursor = hist_conn.cursor()

    curr_conn = sqlite3.connect(CURRENT_DB)
    curr_cursor = curr_conn.cursor()

    # 读取历史预约数据
    hist_cursor.execute("SELECT * FROM meeting_bookings")
    bookings = hist_cursor.fetchall()

    print(f"历史预约数据: {len(bookings)} 条")

    # 插入到当前数据库
    for booking in bookings:
        try:
            placeholders = ",".join(["?" for _ in booking])
            curr_cursor.execute(
                f"INSERT INTO meeting_bookings VALUES ({placeholders})", booking
            )
        except Exception as e:
            print(f"  ✗ 预约记录插入失败: {str(e)}")

    curr_conn.commit()
    hist_conn.close()
    curr_conn.close()

    print(f"✓ 预约数据恢复完成: {len(bookings)} 条")


def verify_restored_data():
    """验证恢复的数据"""
    print("\n" + "=" * 60)
    print("步骤9: 验证恢复数据")
    print("=" * 60)

    conn = sqlite3.connect(CURRENT_DB)
    cursor = conn.cursor()

    tables = {
        "products": "产品",
        "users": "用户",
        "office": "办公室",
        "office_pickup": "领水记录",
        "meeting_rooms": "会议室",
        "meeting_bookings": "预约记录",
    }

    print("\n数据统计:")
    for table, name in tables.items():
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        print(f"  {name}: {count} 条")

    print("\n数据示例:")

    # 产品示例
    cursor.execute("SELECT id, name, specification, price FROM products LIMIT 3")
    print("\n  产品:")
    for row in cursor.fetchall():
        print(f"    - {row[1]} ({row[2]}): ¥{row[3]}")

    # 用户示例
    cursor.execute("SELECT id, username, name, role FROM users LIMIT 5")
    print("\n  用户:")
    for row in cursor.fetchall():
        print(f"    - {row[1]} ({row[2]}): {row[3]}")

    # 办公室示例
    cursor.execute("SELECT id, name, room_number, leader_name FROM office LIMIT 5")
    print("\n  办公室:")
    for row in cursor.fetchall():
        print(f"    - {row[1]} ({row[2]}): {row[3]}")

    # 会议室示例
    cursor.execute("SELECT id, name, location, capacity FROM meeting_rooms LIMIT 3")
    print("\n  会议室:")
    for row in cursor.fetchall():
        print(f"    - {row[1]} ({row[2]}): 容纳{row[3]}人")

    # 预约示例
    cursor.execute(
        "SELECT id, room_id, booking_date, user_name, meeting_title FROM meeting_bookings LIMIT 5"
    )
    print("\n  预约记录:")
    for row in cursor.fetchall():
        print(f"    - {row[4]} ({row[2]}): {row[3]}")

    conn.close()

    print("\n✓ 数据验证完成")


def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("AI产业集群空间服务系统 - 数据恢复")
    print("=" * 60)
    print(f"执行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    try:
        # 1. 备份当前数据
        backup_file = backup_current_data()

        # 2. 清空当前数据表
        clear_current_data()

        # 3. 恢复各类数据
        restore_products()
        restore_users()
        restore_offices()
        restore_pickups()
        restore_meeting_rooms()
        restore_bookings()

        # 4. 验证恢复结果
        verify_restored_data()

        print("\n" + "=" * 60)
        print("数据恢复完成！")
        print("=" * 60)
        print(f"备份文件: {backup_file}")
        print("如需回滚，请使用备份文件恢复")
        print("=" * 60)

    except Exception as e:
        print(f"\n✗ 数据恢复失败: {str(e)}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
