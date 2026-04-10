#!/usr/bin/env python3
"""
数据库迁移脚本 - 将会议室数据迁移到统一数据库
将 Service_MeetingRoom/backend/meeting.db 中的数据迁移到 Service_WaterManage/backend/waterms.db

使用方法: python migrate_meeting_to_unified.py
"""

import sqlite3
import os
from datetime import datetime

# 数据库路径
SOURCE_DB = os.path.join(
    os.path.dirname(__file__),
    "..",
    "..",
    "Service_MeetingRoom",
    "backend",
    "meeting.db",
)
SOURCE_DB = os.path.abspath(SOURCE_DB)

TARGET_DB = os.path.join(os.path.dirname(__file__), "waterms.db")
TARGET_DB = os.path.abspath(TARGET_DB)


def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")


def create_meeting_tables(source_conn):
    """从源数据库复制表结构"""
    log("复制会议室相关表结构...")

    source_cursor = source_conn.cursor()

    # 获取源数据库所有表
    source_cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'meeting_%'"
    )
    tables = [row[0] for row in source_cursor.fetchall()]

    target_conn = sqlite3.connect(TARGET_DB)
    target_cursor = target_conn.cursor()

    for table_name in tables:
        # 复制表结构
        source_cursor.execute(
            f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{table_name}'"
        )
        create_sql = source_cursor.fetchone()[0]

        try:
            target_cursor.execute(create_sql)
            log(f"已创建表: {table_name}")
        except Exception as e:
            if "already exists" in str(e):
                log(f"表已存在: {table_name}")
            else:
                log(f"创建表 {table_name} 时出错: {e}")

    target_conn.commit()
    target_conn.close()


def migrate_all_tables(source_conn):
    """迁移所有会议室相关表"""
    log("迁移所有会议室数据...")

    source_cursor = source_conn.cursor()

    # 获取源数据库所有会议室相关表
    source_cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'meeting_%'"
    )
    tables = [row[0] for row in source_cursor.fetchall()]

    target_conn = sqlite3.connect(TARGET_DB)

    for table_name in tables:
        target_cursor = target_conn.cursor()

        # 检查目标表是否已有数据
        try:
            target_cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = target_cursor.fetchone()[0]
            if count > 0:
                log(f"{table_name} 已有 {count} 条记录，跳过迁移")
                continue
        except Exception as e:
            log(f"检查 {table_name} 时出错: {e}")
            continue

        # 读取源表数据
        source_cursor.execute(f"SELECT * FROM {table_name}")
        columns = [description[0] for description in source_cursor.description]
        rows = source_cursor.fetchall()

        if not rows:
            log(f"{table_name} 无数据，跳过")
            continue

        # 迁移数据
        columns_str = ", ".join(columns)
        placeholders = ", ".join(["?" for _ in columns])

        for row in rows:
            try:
                target_cursor.execute(
                    f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})",
                    row,
                )
            except Exception as e:
                log(f"迁移 {table_name} 数据时出错: {e}")
                continue

        target_conn.commit()
        log(f"已迁移 {table_name}: {len(rows)} 条记录")

    target_conn.close()


def verify_migration(target_conn):
    """验证迁移结果"""
    log("\n========== 迁移验证 ==========")

    cursor = target_conn.cursor()

    try:
        cursor.execute("SELECT COUNT(*) FROM meeting_rooms")
        rooms_count = cursor.fetchone()[0]
        log(f"会议室数量: {rooms_count}")
    except:
        rooms_count = 0
        log("会议室表不存在")

    try:
        cursor.execute("SELECT COUNT(*) FROM meeting_bookings")
        bookings_count = cursor.fetchone()[0]
        log(f"预约数量: {bookings_count}")
    except:
        bookings_count = 0

    try:
        cursor.execute("SELECT COUNT(*) FROM meeting_approval_requests")
        approvals_count = cursor.fetchone()[0]
        log(f"审批数量: {approvals_count}")
    except:
        approvals_count = 0

    try:
        cursor.execute("SELECT COUNT(*) FROM meeting_payment_records")
        payments_count = cursor.fetchone()[0]
        log(f"支付记录: {payments_count}")
    except:
        payments_count = 0

    log("\n会议室列表:")
    try:
        cursor.execute(
            "SELECT id, name, location, capacity, price_per_hour FROM meeting_rooms"
        )
        for row in cursor.fetchall():
            log(f"  [{row[0]}] {row[1]} - {row[2]} - {row[3]}人 - ¥{row[4]}/小时")
    except Exception as e:
        log(f"无法读取会议室列表: {e}")

    return rooms_count > 0 and bookings_count > 0


def main():
    log("=" * 50)
    log("开始会议室数据迁移")
    log(f"源数据库: {SOURCE_DB}")
    log(f"目标数据库: {TARGET_DB}")
    log("=" * 50)

    # 检查源数据库
    if not os.path.exists(SOURCE_DB):
        log(f"错误: 源数据库不存在 - {SOURCE_DB}")
        return False

    # 连接源数据库
    try:
        source_conn = sqlite3.connect(SOURCE_DB)
        log("已连接到源数据库")
    except Exception as e:
        log(f"连接源数据库失败: {e}")
        return False

    try:
        # 创建表结构
        create_meeting_tables(source_conn)

        # 迁移数据
        migrate_all_tables(source_conn)

        # 验证
        target_conn = sqlite3.connect(TARGET_DB)
        success = verify_migration(target_conn)
        target_conn.close()

        if success:
            log("\n" + "=" * 50)
            log("迁移完成!")
            log("=" * 50)
        else:
            log("\n迁移验证失败!")

        return success

    except Exception as e:
        log(f"迁移过程出错: {e}")
        import traceback

        traceback.print_exc()
        return False
    finally:
        source_conn.close()


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
