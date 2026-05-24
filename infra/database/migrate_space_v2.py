"""
空间服务 v2 数据迁移脚本
- 新增 resource_time_slots 表
- space_types 添加 supported_duration_units, time_slot_preset 列
- space_bookings 添加 time_slot_key, booking_unit 列
- 回填已有数据的安全默认值
"""

import sqlite3
import os
import sys

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data", "app.db")


def migrate():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 1. Create resource_time_slots table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS resource_time_slots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            resource_id INTEGER NOT NULL,
            slot_key VARCHAR(50) NOT NULL,
            slot_name VARCHAR(50),
            slot_type VARCHAR(20) NOT NULL DEFAULT 'fixed_time',
            start_time VARCHAR(10),
            end_time VARCHAR(10),
            duration_value FLOAT DEFAULT 1,
            duration_unit VARCHAR(20) DEFAULT 'hour',
            max_bookings_per_slot INTEGER DEFAULT 1,
            applicable_days VARCHAR(50),
            price_override FLOAT,
            is_active BOOLEAN DEFAULT 1,
            sort_order INTEGER DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (resource_id) REFERENCES space_resources(id)
        )
    """)
    print("✅ resource_time_slots 表已创建")

    # 2. Add columns to space_types
    try:
        cursor.execute("ALTER TABLE space_types ADD COLUMN supported_duration_units TEXT DEFAULT '[\"hour\"]'")
        print("✅ space_types.supported_duration_units 列已添加")
    except sqlite3.OperationalError as e:
        if "duplicate column" in str(e).lower():
            print("⏭️  space_types.supported_duration_units 列已存在，跳过")
        else:
            raise

    try:
        cursor.execute("ALTER TABLE space_types ADD COLUMN time_slot_preset TEXT")
        print("✅ space_types.time_slot_preset 列已添加")
    except sqlite3.OperationalError as e:
        if "duplicate column" in str(e).lower():
            print("⏭️  space_types.time_slot_preset 列已存在，跳过")
        else:
            raise

    # 3. Add columns to space_bookings
    try:
        cursor.execute("ALTER TABLE space_bookings ADD COLUMN time_slot_key VARCHAR(50)")
        print("✅ space_bookings.time_slot_key 列已添加")
    except sqlite3.OperationalError as e:
        if "duplicate column" in str(e).lower():
            print("⏭️  space_bookings.time_slot_key 列已存在，跳过")
        else:
            raise

    try:
        cursor.execute("ALTER TABLE space_bookings ADD COLUMN booking_unit VARCHAR(20) DEFAULT 'hour'")
        print("✅ space_bookings.booking_unit 列已添加")
    except sqlite3.OperationalError as e:
        if "duplicate column" in str(e).lower():
            print("⏭️  space_bookings.booking_unit 列已存在，跳过")
        else:
            raise

    # 4. Backfill existing data
    cursor.execute("UPDATE space_bookings SET booking_unit = 'hour' WHERE booking_unit IS NULL")

    cursor.execute("UPDATE space_types SET supported_duration_units = '[\"hour\"]' WHERE supported_duration_units IS NULL")

    # 5. Insert seed space types for new categories
    seed_space_types(cursor)

    conn.commit()
    conn.close()
    print("✅ 空间服务 v2 迁移完成")


def seed_space_types(cursor):
    """插入新的空间类型种子数据"""
    seed_types = [
        (
            "booth", "展位/展览", "Booth/Exhibition",
            "day", 1, 90, 30,
            '["day","week","month"]', None,
            "🎪", "amber", 10,
        ),
        (
            "venue", "会场/活动场地", "Venue/Event Space",
            "half_day", 1, 7, 14,
            '["half_day","day"]',
            '[{"slot_key":"morning","slot_name":"上午场 (09:00-12:00)","slot_type":"fixed_time","start_time":"09:00","end_time":"12:00","duration_value":0.5,"duration_unit":"half_day"},{"slot_key":"afternoon","slot_name":"下午场 (14:00-18:00)","slot_type":"fixed_time","start_time":"14:00","end_time":"18:00","duration_value":0.5,"duration_unit":"half_day"},{"slot_key":"evening","slot_name":"晚场 (19:00-22:00)","slot_type":"fixed_time","start_time":"19:00","end_time":"22:00","duration_value":0.5,"duration_unit":"half_day"},{"slot_key":"full_day","slot_name":"全天 (09:00-22:00)","slot_type":"fixed_time","start_time":"09:00","end_time":"22:00","duration_value":1,"duration_unit":"day"}]',
            "🏟️", "indigo", 11,
        ),
        (
            "dining_room", "餐厅/包间", "Dining Room",
            "meal", 1, 3, 7,
            '["meal"]',
            '[{"slot_key":"breakfast","slot_name":"早餐 (07:00-09:00)","slot_type":"session","start_time":"07:00","end_time":"09:00","duration_value":1,"duration_unit":"meal"},{"slot_key":"lunch","slot_name":"午餐 (11:30-13:30)","slot_type":"session","start_time":"11:30","end_time":"13:30","duration_value":1,"duration_unit":"meal"},{"slot_key":"dinner","slot_name":"晚餐 (17:30-21:00)","slot_type":"session","start_time":"17:30","end_time":"21:00","duration_value":1,"duration_unit":"meal"}]',
            "🍽️", "orange", 12,
        ),
        (
            "office_desk", "办公位共享", "Office Desk Sharing",
            "hour", 1, 8, 7,
            '["hour"]', None,
            "🪑", "teal", 20,
        ),
    ]

    for t in seed_types:
        cursor.execute(
            "SELECT id FROM space_types WHERE type_code = ?", (t[0],)
        )
        if cursor.fetchone() is None:
            cursor.execute(
                """INSERT INTO space_types
                   (type_code, type_name, type_name_en, min_duration_unit, min_duration_value,
                    max_duration_value, advance_booking_days, supported_duration_units, time_slot_preset,
                    icon, color_theme, sort_order, is_active, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)""",
                t,
            )
            print(f"✅ 种子数据已插入: {t[0]}")
        else:
            print(f"⏭️  空间类型已存在: {t[0]}")


if __name__ == "__main__":
    migrate()
