"""
修复会议室和预约数据
"""

import sqlite3


def fix_meeting_data():
    """修复会议室和预约数据"""

    conn = sqlite3.connect("./data/app.db")
    cursor = conn.cursor()

    print("=" * 60)
    print("修复会议室数据")
    print("=" * 60)

    # 修复会议室会员价格
    cursor.execute("""
        UPDATE meeting_rooms 
        SET member_price_per_hour = price_per_hour * 0.8 
        WHERE member_price_per_hour <= 10 OR member_price_per_hour IS NULL
    """)
    print(f"✓ 修复会员价格: {cursor.rowcount} 条")

    # 修复会议室免费时长
    cursor.execute("""
        UPDATE meeting_rooms 
        SET free_hours_per_month = 5 
        WHERE free_hours_per_month IS NULL OR free_hours_per_month < 0
    """)
    print(f"✓ 修复免费时长: {cursor.rowcount} 条")

    # 查看修复结果
    cursor.execute(
        "SELECT id, name, price_per_hour, member_price_per_hour, free_hours_per_month FROM meeting_rooms"
    )
    rooms = cursor.fetchall()
    print(f"\n会议室数据（{len(rooms)}条）:")
    for room in rooms[:3]:
        print(
            f"  {room[1]}: ¥{room[2]}/小时, 会员¥{room[3]}/小时, 免费{room[4]}小时/月"
        )

    print("\n" + "=" * 60)
    print("修复预约数据")
    print("=" * 60)

    # 修复预约数据的created_at
    cursor.execute("""
        UPDATE meeting_bookings 
        SET created_at = '2026-04-10 12:00:00'
        WHERE created_at IS NULL OR created_at = '' OR created_at NOT LIKE '%-%'
    """)
    print(f"✓ 修复created_at: {cursor.rowcount} 条")

    # 修复预约数据的updated_at
    cursor.execute("""
        UPDATE meeting_bookings 
        SET updated_at = '2026-04-10 12:00:00'
        WHERE updated_at IS NULL OR updated_at = '' OR updated_at NOT LIKE '%-%'
    """)
    print(f"✓ 修复updated_at: {cursor.rowcount} 条")

    # 修复预约数据的user_name
    cursor.execute("""
        UPDATE meeting_bookings 
        SET user_name = '测试用户'
        WHERE user_name IS NULL OR user_name = ''
    """)
    print(f"✓ 修复user_name: {cursor.rowcount} 条")

    # 查看修复结果
    cursor.execute(
        "SELECT id, room_id, user_name, created_at, updated_at FROM meeting_bookings LIMIT 3"
    )
    bookings = cursor.fetchall()
    print(f"\n预约数据（已修复）:")
    for booking in bookings:
        print(
            f"  ID={booking[0]}, Room={booking[1]}, User={booking[2]}, Created={booking[3]}"
        )

    conn.commit()
    conn.close()

    print("\n" + "=" * 60)
    print("修复完成")
    print("=" * 60)


if __name__ == "__main__":
    fix_meeting_data()
