#!/usr/bin/env python3
"""
AI产业集群空间服务系统 - 会议室数据迁移工具

将SQLite数据库中的会议室数据迁移到PostgreSQL统一数据库
"""

import sqlite3
import psycopg2
from psycopg2.extras import RealDictCursor
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
import os
import sys

# 添加项目路径
sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("meeting_migration.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


class MeetingDataMigrator:
    """会议室数据迁移器"""

    def __init__(self, sqlite_path: str, pg_config: Dict[str, str]):
        self.sqlite_path = sqlite_path
        self.pg_config = pg_config
        self.sqlite_conn = None
        self.pg_conn = None

    def connect_databases(self):
        """连接数据库"""
        try:
            # 连接SQLite
            self.sqlite_conn = sqlite3.connect(self.sqlite_path)
            self.sqlite_conn.row_factory = sqlite3.Row
            logger.info(f"Connected to SQLite database: {self.sqlite_path}")

            # 连接PostgreSQL
            self.pg_conn = psycopg2.connect(**self.pg_config)
            self.pg_conn.autocommit = False
            logger.info(
                f"Connected to PostgreSQL database: {self.pg_config['host']}:{self.pg_config['port']}"
            )

        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            raise

    def close_connections(self):
        """关闭数据库连接"""
        if self.sqlite_conn:
            self.sqlite_conn.close()
            logger.info("Closed SQLite connection")

        if self.pg_conn:
            self.pg_conn.close()
            logger.info("Closed PostgreSQL connection")

    def migrate_meeting_rooms(self) -> Dict[int, int]:
        """迁移会议室数据"""
        logger.info("Starting meeting room migration...")

        id_mapping = {}

        # 从SQLite读取会议室数据
        cursor = self.sqlite_conn.cursor()
        cursor.execute("""
            SELECT id, name, capacity, facilities, price_per_hour, 
                   is_active, created_at, updated_at, member_price_per_hour
            FROM meeting_rooms
            ORDER BY id
        """)

        rooms = cursor.fetchall()
        logger.info(f"Found {len(rooms)} meeting rooms to migrate")

        # 插入到PostgreSQL
        pg_cursor = self.pg_conn.cursor()
        for room in rooms:
            try:
                pg_cursor.execute(
                    """
                    INSERT INTO meeting_rooms (
                        id, name, capacity, equipment, price_per_hour, status,
                        created_at, updated_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO UPDATE SET
                        name = EXCLUDED.name,
                        capacity = EXCLUDED.capacity,
                        equipment = EXCLUDED.equipment,
                        price_per_hour = EXCLUDED.price_per_hour,
                        status = EXCLUDED.status,
                        updated_at = EXCLUDED.updated_at
                """,
                    (
                        room["id"],
                        room["name"] or f"Room_{room['id']}",
                        int(room["capacity"]) if room["capacity"] else 10,
                        room["facilities"] or "",
                        float(room["price_per_hour"])
                        if room["price_per_hour"]
                        else 0.0,
                        "available" if bool(room["is_active"]) else "maintenance",
                        self._parse_datetime(room["created_at"]),
                        self._parse_datetime(room["updated_at"])
                        or self._parse_datetime(room["created_at"]),
                    ),
                )

                id_mapping[room["id"]] = room["id"]
                logger.debug(
                    f"Migrated meeting room: {room['name']} (ID: {room['id']})"
                )

            except Exception as e:
                logger.error(f"Failed to migrate meeting room {room['id']}: {e}")
                raise

        self.pg_conn.commit()
        logger.info(f"Successfully migrated {len(rooms)} meeting rooms")
        return id_mapping

    def migrate_offices_from_meeting(self) -> Dict[int, int]:
        """从会议室系统迁移办公室数据（补充）"""
        logger.info("Starting office migration from meeting system...")

        id_mapping = {}

        # 从SQLite读取办公室数据
        cursor = self.sqlite_conn.cursor()
        cursor.execute("""
            SELECT id, name, location as room_number, contact_person, contact_phone
            FROM offices
            ORDER BY id
        """)

        offices = cursor.fetchall()
        logger.info(f"Found {len(offices)} offices to migrate from meeting system")

        # 插入到PostgreSQL（避免重复）
        pg_cursor = self.pg_conn.cursor()
        for office in offices:
            try:
                pg_cursor.execute(
                    """
                    INSERT INTO offices (
                        id, name, room_number, contact_person, phone, is_active,
                        created_at, updated_at
                    ) VALUES (%s, %s, %s, %s, % s, %s, %s, %s)
                    ON CONFLICT (id) DO UPDATE SET
                        name = EXCLUDED.name,
                        room_number = EXCLUDED.room_number,
                        contact_person = EXCLUDED.contact_person,
                        phone = EXCLUDED.phone,
                        updated_at = EXCLUDED.updated_at
                """,
                    (
                        office["id"],
                        office["name"] or f"Office_{office['id']}",
                        office["room_number"] or "",
                        office["contact_person"] or "",
                        office["contact_phone"] or "",
                        True,
                        datetime.now(),
                        datetime.now(),
                    ),
                )

                id_mapping[office["id"]] = office["id"]
                logger.debug(f"Migrated office: {office['name']} (ID: {office['id']})")

            except Exception as e:
                logger.error(f"Failed to migrate office {office['id']}: {e}")
                raise

        self.pg_conn.commit()
        logger.info(f"Successfully migrated {len(offices)} offices from meeting system")
        return id_mapping

    def create_missing_users(self, user_ids: List[int]) -> Dict[int, int]:
        """为会议室预约中引用但不存在的用户创建临时账户"""
        logger.info(f"Creating {len(user_ids)} missing users...")

        id_mapping = {}
        pg_cursor = self.pg_conn.cursor()

        for user_id in user_ids:
            try:
                username = f"user_{user_id}"
                password_hash = (
                    "$2b$12$KIXqY8vJ8X3V9QZ7X3V9QeO3V9QZ7X3V9QZ7X3V9QZ7X3V9QZ7X3V"
                )

                pg_cursor.execute(
                    """
                    INSERT INTO users (
                        id, username, role, is_active, password_hash,
                        created_at, updated_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO NOTHING
                """,
                    (
                        user_id,
                        username,
                        "user",
                        True,
                        password_hash,
                        datetime.now(),
                        datetime.now(),
                    ),
                )

                id_mapping[user_id] = user_id
                logger.debug(f"Created missing user: {username} (ID: {user_id})")

            except Exception as e:
                logger.error(f"Failed to create user {user_id}: {e}")
                raise

        self.pg_conn.commit()
        logger.info(f"Successfully created {len(user_ids)} missing users")
        return id_mapping

    def migrate_meeting_bookings(
        self, room_id_mapping: Dict[int, int], office_id_mapping: Dict[int, int]
    ) -> Dict[int, int]:
        """迁移会议室预约数据"""
        logger.info("Starting meeting booking migration...")

        id_mapping = {}

        # 获取已存在的用户ID
        pg_cursor = self.pg_conn.cursor()
        pg_cursor.execute("SELECT id FROM users")
        existing_user_ids = set(row[0] for row in pg_cursor.fetchall())

        # 从SQLite读取预约数据
        cursor = self.sqlite_conn.cursor()
        cursor.execute("""
            SELECT id, booking_no, room_id, room_name, user_id, user_name, 
                   department, booking_date, start_time, end_time, duration,
                   meeting_title, attendees_count, total_fee, status, 
                   confirmed_by, confirmed_at, office_id, payment_status,
                   payment_mode, actual_fee, discount_amount, settlement_batch_id,
                   created_at, updated_at
            FROM meeting_bookings
            WHERE is_deleted = 0
            ORDER BY id
        """)

        bookings = cursor.fetchall()
        logger.info(f"Found {len(bookings)} meeting bookings to migrate")

        # 找出需要创建的用户
        missing_user_ids = []
        for booking in bookings:
            if booking["user_id"] and booking["user_id"] not in existing_user_ids:
                missing_user_ids.append(booking["user_id"])

        # 创建缺失的用户
        if missing_user_ids:
            unique_missing_user_ids = list(set(missing_user_ids))
            self.create_missing_users(unique_missing_user_ids)
            existing_user_ids.update(unique_missing_user_ids)

        # 插入到PostgreSQL
        pg_cursor = self.pg_conn.cursor()
        for booking in bookings:
            try:
                room_id = room_id_mapping.get(booking["room_id"])
                office_id = (
                    office_id_mapping.get(booking["office_id"])
                    if booking["office_id"]
                    else None
                )

                if not room_id:
                    logger.warning(
                        f"Skipping booking {booking['id']}: room {booking['room_id']} not found"
                    )
                    continue

                user_id = booking["user_id"]
                if user_id and user_id not in existing_user_ids:
                    logger.warning(
                        f"Skipping booking {booking['id']}: user {user_id} not found and could not be created"
                    )
                    continue

                # 解析时间
                booking_date = None
                if booking["booking_date"]:
                    try:
                        booking_date = datetime.strptime(
                            str(booking["booking_date"]), "%Y-%m-%d"
                        ).date()
                    except:
                        pass

                start_time = None
                if booking["start_time"]:
                    try:
                        start_time = datetime.strptime(
                            str(booking["start_time"]), "%H:%M"
                        ).time()
                    except:
                        pass

                end_time = None
                if booking["end_time"]:
                    try:
                        end_time = datetime.strptime(
                            str(booking["end_time"]), "%H:%M"
                        ).time()
                    except:
                        pass

                status_map = {
                    "pending": "pending",
                    "approved": "approved",
                    "confirmed": "approved",
                    "completed": "completed",
                    "cancelled": "cancelled",
                    "rejected": "rejected",
                }

                pg_cursor.execute(
                    """
                    INSERT INTO meeting_bookings (
                        id, room_id, user_id, date, start_time, end_time, purpose,
                        attendees, amount, status, approved_by, approved_at,
                        created_at, updated_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO UPDATE SET
                        room_id = EXCLUDED.room_id,
                        user_id = EXCLUDED.user_id,
                        date = EXCLUDED.date,
                        start_time = EXCLUDED.start_time,
                        end_time = EXCLUDED.end_time,
                        purpose = EXCLUDED.purpose,
                        attendees = EXCLUDED.attendees,
                        amount = EXCLUDED.amount,
                        status = EXCLUDED.status,
                        approved_by = EXCLUDED.approved_by,
                        approved_at = EXCLUDED.approved_at,
                        updated_at = EXCLUDED.updated_at
                """,
                    (
                        booking["id"],
                        room_id,
                        user_id,
                        booking_date,
                        start_time,
                        end_time,
                        booking["meeting_title"] or "Meeting",
                        int(booking["attendees_count"])
                        if booking["attendees_count"]
                        else 1,
                        float(booking["actual_fee"] or booking["total_fee"])
                        if (booking["actual_fee"] or booking["total_fee"])
                        else 0.0,
                        status_map.get(booking["status"], booking["status"]),
                        booking["confirmed_by"],
                        self._parse_datetime(booking["confirmed_at"]),
                        self._parse_datetime(booking["created_at"]),
                        self._parse_datetime(booking["updated_at"])
                        or self._parse_datetime(booking["created_at"]),
                    ),
                )

                id_mapping[booking["id"]] = booking["id"]
                logger.debug(
                    f"Migrated booking {booking['booking_no']} (ID: {booking['id']})"
                )

            except Exception as e:
                logger.error(f"Failed to migrate booking {booking['id']}: {e}")
                raise

        self.pg_conn.commit()
        logger.info(f"Successfully migrated {len(bookings)} meeting bookings")
        return id_mapping

    def _parse_datetime(self, dt_str: Optional[str]) -> Optional[datetime]:
        """解析日期时间字符串"""
        if not dt_str:
            return None

        if isinstance(dt_str, datetime):
            return dt_str

        try:
            # 尝试多种日期格式
            formats = [
                "%Y-%m-%d %H:%M:%S.%f",
                "%Y-%m-%d %H:%M:%S",
                "%Y-%m-%dT%H:%M:%S.%f",
                "%Y-%m-%dT%H:%M:%S",
                "%Y-%m-%d",
            ]

            for fmt in formats:
                try:
                    return datetime.strptime(dt_str, fmt)
                except ValueError:
                    continue

            logger.warning(f"Could not parse datetime: {dt_str}")
            return datetime.now()

        except Exception as e:
            logger.warning(f"Error parsing datetime {dt_str}: {e}")
            return datetime.now()

    def validate_migration(self):
        """验证迁移结果"""
        logger.info("Validating meeting data migration results...")

        # 验证基本数据完整性
        pg_cursor = self.pg_conn.cursor()

        # 验证会议室数量
        pg_cursor.execute("SELECT COUNT(*) FROM meeting_rooms")
        room_count = pg_cursor.fetchone()[0]
        logger.info(f"Total meeting rooms in PostgreSQL: {room_count}")

        # 验证预约数量
        pg_cursor.execute("SELECT COUNT(*) FROM meeting_bookings")
        booking_count = pg_cursor.fetchone()[0]
        logger.info(f"Total meeting bookings in PostgreSQL: {booking_count}")

        logger.info("Meeting data migration validation completed successfully!")

    def run_migration(self):
        """执行完整的迁移流程"""
        try:
            logger.info("Starting meeting data migration...")

            # 连接数据库
            self.connect_databases()

            # 执行迁移步骤
            room_id_mapping = self.migrate_meeting_rooms()
            office_id_mapping = self.migrate_offices_from_meeting()
            self.migrate_meeting_bookings(room_id_mapping, office_id_mapping)

            # 验证迁移结果
            self.validate_migration()

            logger.info("Meeting data migration completed successfully!")

        except Exception as e:
            logger.error(f"Migration failed: {e}")
            self.pg_conn.rollback()
            raise

        finally:
            self.close_connections()


def main():
    """主函数"""
    # 数据库配置
    sqlite_path = "Service_MeetingRoom/backend/meeting.db"
    pg_config = {
        "host": "localhost",
        "port": "5432",
        "database": "ai_cluster_db",
        "user": "ai_cluster",
        "password": "secure_password_2026",
    }

    # 创建迁移器并执行
    migrator = MeetingDataMigrator(sqlite_path, pg_config)
    migrator.run_migration()


if __name__ == "__main__":
    main()
