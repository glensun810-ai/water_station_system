"""
重新正确导入会议室和预约数据
"""

import sqlite3
from datetime import datetime


def reimport_meeting_data():
    """重新正确导入会议室和预约数据"""

    # 连接数据库
    hist_conn = sqlite3.connect(
        "./Backup/old_architecture_20260410_200812/Service_MeetingRoom/backend/meeting.db"
    )
    hist_cursor = hist_conn.cursor()

    curr_conn = sqlite3.connect("./data/app.db")
    curr_cursor = curr_conn.cursor()

    print("=" * 60)
    print("重新导入会议室数据")
    print("=" * 60)

    # 清空当前会议室数据
    curr_cursor.execute("DELETE FROM meeting_rooms")
    print("✓ 已清空会议室数据")

    # 读取历史会议室数据
    hist_cursor.execute("SELECT * FROM meeting_rooms")
    rooms = hist_cursor.fetchall()

    print(f"历史会议室数据: {len(rooms)} 条")

    # 按照当前数据库字段顺序插入
    # 当前字段: id, name, location, capacity, facilities, price_per_hour,
    #          member_price_per_hour, free_hours_per_month, is_active, created_at, updated_at
    for room in rooms:
        try:
            # 历史字段: id, name, location, capacity, facilities, price_per_hour,
            #          free_hours_per_month, is_active, created_at, updated_at, member_price_per_hour

            id = room[0]
            name = room[1]
            location = room[2]
            capacity = room[3]
            facilities = room[4]
            price_per_hour = room[5]
            free_hours_per_month = room[6] if room[6] else 5
            is_active = room[7] if room[7] is not None else True
            created_at = (
                room[8] if room[8] else datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )
            updated_at = (
                room[9] if room[9] else datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )
            member_price_per_hour = room[10] if room[10] else price_per_hour * 0.8

            curr_cursor.execute(
                """
                INSERT INTO meeting_rooms
                (id, name, location, capacity, facilities, price_per_hour,
                 member_price_per_hour, free_hours_per_month, is_active, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    id,
                    name,
                    location,
                    capacity,
                    facilities,
                    price_per_hour,
                    member_price_per_hour,
                    free_hours_per_month,
                    is_active,
                    created_at,
                    updated_at,
                ),
            )

            print(
                f"  ✓ {name}: ¥{price_per_hour}/小时, 会员¥{member_price_per_hour}/小时"
            )

        except Exception as e:
            print(f"  ✗ 插入失败: {str(e)}")

    print("\n" + "=" * 60)
    print("重新导入预约数据")
    print("=" * 60)

    # 清空当前预约数据
    curr_cursor.execute("DELETE FROM meeting_bookings")
    print("✓ 已清空预约数据")

    # 读取历史预约数据
    hist_cursor.execute("SELECT * FROM meeting_bookings")
    bookings = hist_cursor.fetchall()

    print(f"历史预约数据: {len(bookings)} 条")

    # 获取当前预约表字段
    curr_cursor.execute("PRAGMA table_info(meeting_bookings)")
    curr_fields = [row[1] for row in curr_cursor.fetchall()]

    inserted = 0
    for booking in bookings:
        try:
            # 使用默认值填充缺失的必填字段
            placeholders = []
            values = []

            for i, field in enumerate(curr_fields):
                if i < len(booking) and booking[i] is not None:
                    values.append(booking[i])
                else:
                    # 提供默认值
                    if field == "user_name":
                        values.append("测试用户")
                    elif field == "created_at":
                        values.append(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                    elif field == "updated_at":
                        values.append(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                    elif field == "status":
                        values.append("pending")
                    elif field == "payment_status":
                        values.append("unpaid")
                    elif field == "is_deleted":
                        values.append(0)
                    else:
                        values.append(None)

                placeholders.append("?")

            curr_cursor.execute(
                f"INSERT INTO meeting_bookings VALUES ({','.join(placeholders)})",
                values,
            )
            inserted += 1

        except Exception as e:
            pass  # 忽略个别错误

    print(f"✓ 成功导入预约数据: {inserted} 条")

    curr_conn.commit()
    hist_conn.close()
    curr_conn.close()

    print("\n" + "=" * 60)
    print("数据导入完成")
    print("=" * 60)

    # 验证数据
    verify_data()


def verify_data():
    """验证导入的数据"""

    conn = sqlite3.connect("./data/app.db")
    cursor = conn.cursor()

    print("\n数据验证:")

    # 验证会议室
    cursor.execute("SELECT COUNT(*) FROM meeting_rooms")
    room_count = cursor.fetchone()[0]
    print(f"  会议室: {room_count} 条")

    cursor.execute(
        "SELECT id, name, price_per_hour, member_price_per_hour, free_hours_per_month FROM meeting_rooms LIMIT 3"
    )
    for row in cursor.fetchall():
        print(
            f"    - {row[1]}: ¥{row[2]}/小时, 会员¥{row[3]}/小时, 免费{row[4]}小时/月"
        )

    # 验证预约
    cursor.execute("SELECT COUNT(*) FROM meeting_bookings")
    booking_count = cursor.fetchone()[0]
    print(f"  预约: {booking_count} 条")

    conn.close()


if __name__ == "__main__":
    reimport_meeting_data()
