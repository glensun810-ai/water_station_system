"""
空间服务数据迁移脚本
从原有meeting表迁移到新的space表
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sqlite3
from datetime import datetime
import json


def migrate_meeting_to_space():
    """迁移会议室数据到空间服务"""

    old_db_path = "data/app.db"
    new_db_path = "data/space.db"

    conn_old = sqlite3.connect(old_db_path)
    conn_new = sqlite3.connect(new_db_path)

    cursor_old = conn_old.cursor()
    cursor_new = conn_new.cursor()

    create_space_types_table(cursor_new)
    create_space_resources_table(cursor_new)
    create_space_bookings_table(cursor_new)

    insert_space_types_data(cursor_new)

    migrate_meeting_rooms(cursor_old, cursor_new)

    migrate_meeting_bookings(cursor_old, cursor_new)

    conn_new.commit()

    verify_migration(cursor_old, cursor_new)

    conn_old.close()
    conn_new.close()

    print("✅ 数据迁移完成")


def create_space_types_table(cursor):
    """创建空间类型表"""

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS space_types (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type_code VARCHAR(50) UNIQUE NOT NULL,
            type_name VARCHAR(100) NOT NULL,
            type_name_en VARCHAR(100),
            description TEXT,
            min_duration_unit VARCHAR(20) NOT NULL,
            min_duration_value INTEGER DEFAULT 1,
            max_duration_value INTEGER DEFAULT 24,
            advance_booking_days INTEGER DEFAULT 0,
            min_capacity INTEGER DEFAULT 1,
            max_capacity INTEGER DEFAULT 500,
            requires_approval BOOLEAN DEFAULT FALSE,
            approval_type VARCHAR(20),
            approval_deadline_hours INTEGER DEFAULT 24,
            requires_deposit BOOLEAN DEFAULT FALSE,
            deposit_percentage FLOAT DEFAULT 0,
            deposit_refund_rules TEXT,
            standard_facilities TEXT,
            optional_addons TEXT,
            is_active BOOLEAN DEFAULT TRUE,
            sort_order INTEGER DEFAULT 0,
            icon VARCHAR(50),
            color_theme VARCHAR(20),
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)


def create_space_resources_table(cursor):
    """创建空间资源表"""

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS space_resources (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type_id INTEGER NOT NULL,
            name VARCHAR(100) NOT NULL,
            name_en VARCHAR(100),
            location VARCHAR(200),
            floor VARCHAR(20),
            building VARCHAR(100),
            capacity INTEGER DEFAULT 10,
            capacity_level VARCHAR(20),
            facilities TEXT,
            facilities_status TEXT,
            base_price FLOAT DEFAULT 0,
            price_unit VARCHAR(20),
            member_price FLOAT DEFAULT 0,
            vip_price FLOAT DEFAULT 0,
            peak_time_price FLOAT,
            off_peak_price FLOAT,
            free_hours_per_month INTEGER DEFAULT 0,
            meal_standard_price FLOAT,
            meal_vip_price FLOAT,
            meal_luxury_price FLOAT,
            booth_size VARCHAR(20),
            booth_position VARCHAR(20),
            venue_level VARCHAR(20),
            setup_time_hours INTEGER DEFAULT 2,
            setup_fee_per_hour FLOAT,
            photos TEXT,
            description TEXT,
            is_active BOOLEAN DEFAULT TRUE,
            is_available BOOLEAN DEFAULT TRUE,
            maintenance_status VARCHAR(20) DEFAULT 'normal',
            maintenance_note TEXT,
            office_id INTEGER,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)


def create_space_bookings_table(cursor):
    """创建空间预约表"""

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS space_bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            booking_no VARCHAR(50) UNIQUE NOT NULL,
            resource_id INTEGER NOT NULL,
            resource_name VARCHAR(100),
            type_id INTEGER,
            type_code VARCHAR(50),
            user_id INTEGER,
            user_type VARCHAR(20) DEFAULT 'external',
            user_name VARCHAR(100) NOT NULL,
            user_phone VARCHAR(20),
            user_email VARCHAR(100),
            department VARCHAR(100),
            office_id INTEGER,
            booking_date DATE NOT NULL,
            start_time VARCHAR(10) NOT NULL,
            end_time VARCHAR(10) NOT NULL,
            duration FLOAT,
            duration_unit VARCHAR(20),
            end_date DATE,
            booking_days INTEGER DEFAULT 1,
            meal_session VARCHAR(20),
            meal_standard VARCHAR(20),
            guests_count INTEGER DEFAULT 1,
            content_type VARCHAR(50),
            content_url VARCHAR(200),
            content_approved BOOLEAN DEFAULT FALSE,
            play_frequency INTEGER DEFAULT 1,
            exhibition_type VARCHAR(50),
            exhibition_plan_url VARCHAR(200),
            purpose VARCHAR(200),
            title VARCHAR(200),
            attendees_count INTEGER DEFAULT 1,
            attendees_info TEXT,
            special_requests TEXT,
            addons_selected TEXT,
            base_fee FLOAT DEFAULT 0,
            addon_fee FLOAT DEFAULT 0,
            discount_amount FLOAT DEFAULT 0,
            total_fee FLOAT DEFAULT 0,
            actual_fee FLOAT DEFAULT 0,
            fee_unit VARCHAR(20),
            requires_deposit BOOLEAN DEFAULT FALSE,
            deposit_amount FLOAT DEFAULT 0,
            deposit_paid BOOLEAN DEFAULT FALSE,
            deposit_paid_at DATETIME,
            deposit_payment_method VARCHAR(20),
            deposit_refunded BOOLEAN DEFAULT FALSE,
            deposit_refund_amount FLOAT,
            deposit_refund_at DATETIME,
            balance_amount FLOAT DEFAULT 0,
            balance_paid BOOLEAN DEFAULT FALSE,
            balance_paid_at DATETIME,
            balance_payment_method VARCHAR(20),
            status VARCHAR(20) DEFAULT 'pending_approval',
            payment_status VARCHAR(20) DEFAULT 'unpaid',
            settlement_status VARCHAR(20) DEFAULT 'unsettled',
            approval_id INTEGER,
            approved_by VARCHAR(100),
            approved_at DATETIME,
            approval_notes TEXT,
            rejected_reason TEXT,
            rejected_at DATETIME,
            confirmed_at DATETIME,
            confirmed_by VARCHAR(100),
            cancelled_at DATETIME,
            cancelled_by VARCHAR(100),
            cancel_reason VARCHAR(500),
            cancel_type VARCHAR(20),
            checked_in_at DATETIME,
            checked_in_by VARCHAR(100),
            started_at DATETIME,
            ended_at DATETIME,
            actual_duration FLOAT,
            completed_at DATETIME,
            completion_notes TEXT,
            rated_at DATETIME,
            rating_score FLOAT,
            rating_feedback TEXT,
            invoice_requested BOOLEAN DEFAULT FALSE,
            invoice_status VARCHAR(20),
            invoice_id INTEGER,
            invoice_info TEXT,
            settlement_id INTEGER,
            settled_at DATETIME,
            can_modify BOOLEAN DEFAULT TRUE,
            can_cancel BOOLEAN DEFAULT TRUE,
            cancel_deadline DATETIME,
            modify_deadline DATETIME,
            is_deleted INTEGER DEFAULT 0,
            deleted_at DATETIME,
            deleted_by VARCHAR(100),
            delete_reason VARCHAR(500),
            booking_source VARCHAR(20),
            booking_channel VARCHAR(20),
            calendar_invite_sent BOOLEAN DEFAULT FALSE,
            calendar_invite_id VARCHAR(100),
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)


def insert_space_types_data(cursor):
    """插入预置空间类型数据"""

    space_types = [
        (
            1,
            "meeting_room",
            "会议室",
            "Meeting Room",
            "小型团队协作空间",
            "hour",
            1,
            8,
            0,
            2,
            20,
            0,
            "auto",
            0,
            0,
            0,
            None,
            '["投影仪","白板","音响","网络","空调"]',
            '["茶歇服务","直播设备"]',
            1,
            1,
            "🏢",
            "#3B82F6",
        ),
        (
            2,
            "venue",
            "会场/多功能厅",
            "Venue/Event Hall",
            "大型活动举办空间",
            "half_day",
            1,
            3,
            3,
            50,
            500,
            1,
            "manual",
            48,
            1,
            0.3,
            '{"提前7天":"100%","提前3-7天":"50%","提前1-3天":"0%","当天":"0%"}',
            '["专业音响","灯光","舞台","LED大屏"]',
            '["茶歇服务","摄影服务","直播服务","活动保险"]',
            1,
            2,
            "🎭",
            "#8B5CF6",
        ),
        (
            3,
            "lobby_screen",
            "大堂大屏",
            "Lobby Display Screen",
            "企业形象展示与广告投放",
            "hour",
            1,
            168,
            1,
            0,
            0,
            1,
            "content_review",
            24,
            0,
            0,
            None,
            '["LED大屏","播放系统","网络"]',
            '["内容制作","效果监测"]',
            1,
            3,
            "📺",
            "#F59E0B",
        ),
        (
            4,
            "lobby_booth",
            "大堂展位",
            "Lobby Exhibition Booth",
            "产品展示与品牌推广",
            "day",
            1,
            30,
            7,
            0,
            0,
            1,
            "manual",
            72,
            1,
            0.5,
            '{"提前7天":"100%","提前3-7天":"50%","提前1-3天":"0%","当天":"0%"}',
            '["展台","展架","电源","照明","网络"]',
            '["值班人员","专业布置","清洁服务"]',
            1,
            4,
            "🏪",
            "#10B981",
        ),
        (
            5,
            "vip_dining",
            "VIP餐厅包厢",
            "VIP Dining Room",
            "高端商务宴请空间",
            "meal_session",
            1,
            2,
            1,
            6,
            20,
            1,
            "manual",
            24,
            1,
            0.3,
            '{"提前24小时":"100%","当天":"0%"}',
            '["餐桌餐具","音响","空调","独立卫生间"]',
            '["生日蛋糕","专业服务团队","餐后茶歇"]',
            1,
            5,
            "🍽️",
            "#EF4444",
        ),
    ]

    for st in space_types:
        cursor.execute(
            """
            INSERT OR REPLACE INTO space_types 
            (id, type_code, type_name, type_name_en, description,
             min_duration_unit, min_duration_value, max_duration_value, advance_booking_days,
             min_capacity, max_capacity, requires_approval, approval_type, approval_deadline_hours,
             requires_deposit, deposit_percentage, deposit_refund_rules,
             standard_facilities, optional_addons,
             is_active, sort_order, icon, color_theme)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            st,
        )

    print(f"✅ 插入 {len(space_types)} 个空间类型")


def migrate_meeting_rooms(cursor_old, cursor_new):
    """迁移会议室数据"""

    cursor_old.execute("""
        SELECT id, name, location, capacity, facilities, 
               price_per_hour, member_price_per_hour, free_hours_per_month, is_active,
               created_at, updated_at
        FROM meeting_rooms
    """)

    rooms = cursor_old.fetchall()

    migrated_count = 0
    for room in rooms:
        (
            room_id,
            name,
            location,
            capacity,
            facilities,
            price,
            member_price,
            free_hours,
            is_active,
            created_at,
            updated_at,
        ) = room

        capacity_level = (
            "small" if capacity <= 10 else "medium" if capacity <= 20 else "large"
        )

        cursor_new.execute(
            """
            INSERT INTO space_resources 
            (id, type_id, name, location, capacity, capacity_level, facilities,
             base_price, price_unit, member_price, free_hours_per_month, is_active,
             created_at, updated_at)
            VALUES (?, 1, ?, ?, ?, ?, ?, ?, 'hour', ?, ?, ?, ?, ?)
        """,
            (
                room_id,
                name,
                location,
                capacity,
                capacity_level,
                facilities,
                price or 0,
                member_price or 0,
                free_hours or 0,
                is_active or 1,
                created_at,
                updated_at,
            ),
        )

        migrated_count += 1

    print(f"✅ 迁移 {migrated_count} 个会议室")


def migrate_meeting_bookings(cursor_old, cursor_new):
    """迁移预约数据"""

    cursor_old.execute("""
        SELECT id, booking_no, room_id, room_name, user_id, user_type,
               user_name, user_phone, department, office_id,
               booking_date, start_time, end_time, duration,
               meeting_title, attendees_count, status,
               total_fee, actual_fee, payment_status, payment_method,
               cancel_reason, cancelled_at, created_at, updated_at
        FROM meeting_bookings
        WHERE is_deleted = 0 OR is_deleted IS NULL
    """)

    bookings = cursor_old.fetchall()

    migrated_count = 0
    for booking in bookings:
        (
            id_,
            booking_no,
            room_id,
            room_name,
            user_id,
            user_type,
            user_name,
            user_phone,
            department,
            office_id,
            booking_date,
            start_time,
            end_time,
            duration,
            title,
            attendees_count,
            status,
            total_fee,
            actual_fee,
            payment_status,
            payment_method,
            cancel_reason,
            cancelled_at,
            created_at,
            updated_at,
        ) = booking

        new_status = map_status(status)

        cursor_new.execute(
            """
            INSERT INTO space_bookings 
            (id, booking_no, resource_id, resource_name, type_id, type_code,
             user_id, user_type, user_name, user_phone, department, office_id,
             booking_date, start_time, end_time, duration, duration_unit,
             title, attendees_count, status,
             total_fee, actual_fee, payment_status, payment_method,
             cancel_reason, cancelled_at,
             created_at, updated_at)
            VALUES (?, ?, ?, ?, 1, 'meeting_room',
                    ?, ?, ?, ?, ?, ?,
                    ?, ?, ?, ?, 'hour',
                    ?, ?, ?,
                    ?, ?, ?, ?,
                    ?, ?,
                    ?, ?)
        """,
            (
                id_,
                booking_no,
                room_id,
                room_name,
                user_id,
                user_type or "external",
                user_name,
                user_phone,
                department,
                office_id,
                booking_date,
                start_time,
                end_time,
                duration,
                title,
                attendees_count or 1,
                new_status,
                total_fee or 0,
                actual_fee or 0,
                payment_status or "unpaid",
                payment_method,
                cancel_reason,
                cancelled_at,
                created_at,
                updated_at,
            ),
        )

        migrated_count += 1

    print(f"✅ 迁移 {migrated_count} 个预约记录")


def map_status(old_status):
    """映射预约状态"""

    status_map = {
        "pending": "pending_approval",
        "confirmed": "confirmed",
        "completed": "completed",
        "cancelled": "cancelled",
        "rejected": "rejected",
    }

    return status_map.get(old_status, "pending_approval")


def verify_migration(cursor_old, cursor_new):
    """验证迁移数据"""

    cursor_old.execute("SELECT COUNT(*) FROM meeting_rooms")
    old_rooms = cursor_old.fetchone()[0]

    cursor_new.execute("SELECT COUNT(*) FROM space_resources WHERE type_id = 1")
    new_rooms = cursor_new.fetchone()[0]

    if old_rooms == new_rooms:
        print(f"✅ 会议室数据验证通过: {old_rooms} == {new_rooms}")
    else:
        print(f"❌ 会议室数据验证失败: {old_rooms} != {new_rooms}")

    cursor_old.execute(
        "SELECT COUNT(*) FROM meeting_bookings WHERE is_deleted = 0 OR is_deleted IS NULL"
    )
    old_bookings = cursor_old.fetchone()[0]

    cursor_new.execute(
        "SELECT COUNT(*) FROM space_bookings WHERE type_code = 'meeting_room' AND is_deleted = 0"
    )
    new_bookings = cursor_new.fetchone()[0]

    if old_bookings == new_bookings:
        print(f"✅ 预约数据验证通过: {old_bookings} == {new_bookings}")
    else:
        print(f"❌ 预约数据验证失败: {old_bookings} != {new_bookings}")


if __name__ == "__main__":
    migrate_meeting_to_space()
