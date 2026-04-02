"""
灵活时间段选择模块单元测试
测试覆盖率目标：≥80%
"""

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from datetime import date

# 导入被测试模块
import sys

sys.path.insert(0, "/Users/sgl/PycharmProjects/AIchanyejiqun")

from Service_MeetingRoom.modules.flexible_booking.api_flexible_booking import (
    calculate_duration,
    validate_duration_constraints,
    check_time_conflicts,
    TimeSlotCheck,
    TimeSlotValidation,
)


class TestTimeCalculations:
    """时间计算功能测试"""

    def test_calculate_duration_normal(self):
        """测试正常时长计算"""
        duration_minutes, duration_hours = calculate_duration("09:00", "12:00")
        assert duration_minutes == 180
        assert duration_hours == 3.0

    def test_calculate_duration_half_hour(self):
        """测试半小时时长"""
        duration_minutes, duration_hours = calculate_duration("09:00", "09:30")
        assert duration_minutes == 30
        assert duration_hours == 0.5

    def test_calculate_duration_cross_noon(self):
        """测试跨越中午的时长"""
        duration_minutes, duration_hours = calculate_duration("11:30", "14:30")
        assert duration_minutes == 180
        assert duration_hours == 3.0

    def test_calculate_duration_full_day(self):
        """测试全天可用时长（07:00-22:00）"""
        duration_minutes, duration_hours = calculate_duration("07:00", "22:00")
        assert duration_minutes == 900
        assert duration_hours == 15.0


class TestDurationValidation:
    """时长约束验证测试"""

    def test_validate_min_duration_valid(self):
        """测试最小时长（30分钟）"""
        is_valid, message = validate_duration_constraints(30)
        assert is_valid is True
        assert message == "时长符合要求"

    def test_validate_min_duration_invalid(self):
        """测试小于最小时长"""
        is_valid, message = validate_duration_constraints(15)
        assert is_valid is False
        assert "不能少于30分钟" in message

    def test_validate_max_duration_valid(self):
        """测试最大时长（8小时）"""
        is_valid, message = validate_duration_constraints(480)
        assert is_valid is True
        assert message == "时长符合要求"

    def test_validate_max_duration_invalid(self):
        """测试超过最大时长"""
        is_valid, message = validate_duration_constraints(500)
        assert is_valid is False
        assert "不能超过" in message

    def test_validate_normal_duration(self):
        """测试正常时长范围"""
        is_valid, message = validate_duration_constraints(120)
        assert is_valid is True
        assert message == "时长符合要求"


class TestTimeSlotCheckModel:
    """时间段检查模型测试"""

    def test_valid_time_format(self):
        """测试有效时间格式"""
        data = {
            "room_id": 1,
            "booking_date": "2026-04-02",
            "start_time": "09:00",
            "end_time": "12:00",
        }
        time_slot = TimeSlotCheck(**data)
        assert time_slot.start_time == "09:00"
        assert time_slot.end_time == "12:00"

    def test_invalid_time_format(self):
        """测试无效时间格式"""
        data = {
            "room_id": 1,
            "booking_date": "2026-04-02",
            "start_time": "9:00",  # 缺少前导零
            "end_time": "12:00",
        }
        with pytest.raises(ValueError, match="时间格式必须为HH:MM"):
            TimeSlotCheck(**data)

    def test_time_out_of_range(self):
        """测试时间超出范围"""
        data = {
            "room_id": 1,
            "booking_date": "2026-04-02",
            "start_time": "06:00",  # 早于07:00
            "end_time": "12:00",
        }
        with pytest.raises(ValueError, match="时间必须在07:00-22:00范围内"):
            TimeSlotCheck(**data)

    def test_time_minute_not_multiple(self):
        """测试分钟不是30的整数倍"""
        data = {
            "room_id": 1,
            "booking_date": "2026-04-02",
            "start_time": "09:15",  # 分钟不是00或30
            "end_time": "12:00",
        }
        with pytest.raises(ValueError, match="分钟必须是30分钟的整数倍"):
            TimeSlotCheck(**data)


class TestTimeSlotValidationModel:
    """时间段验证响应模型测试"""

    def test_available_response(self):
        """测试可用时间段响应"""
        response = TimeSlotValidation(
            is_available=True,
            conflict_count=0,
            duration_minutes=180,
            duration_hours=3.0,
            is_valid=True,
            message="时间段可用",
            warnings=[],
        )
        assert response.is_available is True
        assert response.conflict_count == 0
        assert response.duration_hours == 3.0

    def test_conflict_response(self):
        """测试冲突时间段响应"""
        response = TimeSlotValidation(
            is_available=False,
            conflict_count=2,
            duration_minutes=180,
            duration_hours=3.0,
            is_valid=True,
            message="时间段冲突：已有2个预约",
            warnings=["该时间段已有2个预约冲突"],
        )
        assert response.is_available is False
        assert response.conflict_count == 2
        assert len(response.warnings) == 1

    def test_invalid_duration_response(self):
        """测试无效时长响应"""
        response = TimeSlotValidation(
            is_available=False,
            duration_minutes=15,
            duration_hours=0.25,
            is_valid=False,
            message="预约时长不能少于30分钟",
            warnings=["预约时长不能少于30分钟"],
        )
        assert response.is_valid is False
        assert response.duration_minutes == 15


class TestTimeConflictLogic:
    """时间冲突检测逻辑测试"""

    @pytest.fixture
    def db_session(self):
        """创建测试数据库会话"""
        # 使用内存数据库进行测试
        engine = create_engine(
            "sqlite:///:memory:", connect_args={"check_same_thread": False}
        )
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

        # 创建测试表结构
        with engine.connect() as conn:
            conn.execute(
                text("""
                CREATE TABLE meeting_bookings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    room_id INTEGER,
                    booking_date TEXT,
                    start_time TEXT,
                    end_time TEXT,
                    status TEXT
                )
            """)
            )
            conn.commit()

        db = SessionLocal()
        yield db
        db.close()

    def test_no_conflict(self, db_session):
        """测试无冲突情况"""
        # 插入一个已存在的预约
        db_session.execute(
            text("""
            INSERT INTO meeting_bookings (room_id, booking_date, start_time, end_time, status)
            VALUES (1, '2026-04-02', '14:00', '16:00', 'confirmed')
        """)
        )
        db_session.commit()

        # 检查不同时间段
        conflict_count = check_time_conflicts(
            db_session, 1, date(2026, 4, 2), "09:00", "12:00"
        )
        assert conflict_count == 0

    def test_partial_conflict_start(self, db_session):
        """测试部分冲突（开始时间重叠）"""
        # 插入一个已存在的预约
        db_session.execute(
            text("""
            INSERT INTO meeting_bookings (room_id, booking_date, start_time, end_time, status)
            VALUES (1, '2026-04-02', '10:00', '12:00', 'confirmed')
        """)
        )
        db_session.commit()

        # 检查冲突时间段
        conflict_count = check_time_conflicts(
            db_session, 1, date(2026, 4, 2), "09:00", "11:00"
        )
        assert conflict_count == 1

    def test_partial_conflict_end(self, db_session):
        """测试部分冲突（结束时间重叠）"""
        # 插入一个已存在的预约
        db_session.execute(
            text("""
            INSERT INTO meeting_bookings (room_id, booking_date, start_time, end_time, status)
            VALUES (1, '2026-04-02', '10:00', '12:00', 'confirmed')
        """)
        )
        db_session.commit()

        # 检查冲突时间段
        conflict_count = check_time_conflicts(
            db_session, 1, date(2026, 4, 2), "11:00", "13:00"
        )
        assert conflict_count == 1

    def test_complete_overlap(self, db_session):
        """测试完全重叠"""
        # 插入一个已存在的预约
        db_session.execute(
            text("""
            INSERT INTO meeting_bookings (room_id, booking_date, start_time, end_time, status)
            VALUES (1, '2026-04-02', '10:00', '12:00', 'confirmed')
        """)
        )
        db_session.commit()

        # 检查完全重叠的时间段
        conflict_count = check_time_conflicts(
            db_session, 1, date(2026, 4, 2), "09:00", "13:00"
        )
        assert conflict_count == 1

    def test_multiple_conflicts(self, db_session):
        """测试多个冲突"""
        # 插入多个已存在的预约
        db_session.execute(
            text("""
            INSERT INTO meeting_bookings (room_id, booking_date, start_time, end_time, status)
            VALUES 
                (1, '2026-04-02', '09:00', '10:00', 'confirmed'),
                (1, '2026-04-02', '11:00', '12:00', 'pending')
        """)
        )
        db_session.commit()

        # 检查跨越多个预约的时间段
        conflict_count = check_time_conflicts(
            db_session, 1, date(2026, 4, 2), "09:30", "11:30"
        )
        assert conflict_count == 2

    def test_different_room_no_conflict(self, db_session):
        """测试不同会议室无冲突"""
        # 插入会议室1的预约
        db_session.execute(
            text("""
            INSERT INTO meeting_bookings (room_id, booking_date, start_time, end_time, status)
            VALUES (1, '2026-04-02', '09:00', '12:00', 'confirmed')
        """)
        )
        db_session.commit()

        # 检查会议室2的相同时段
        conflict_count = check_time_conflicts(
            db_session, 2, date(2026, 4, 2), "09:00", "12:00"
        )
        assert conflict_count == 0

    def test_different_date_no_conflict(self, db_session):
        """测试不同日期无冲突"""
        # 插入4月2日的预约
        db_session.execute(
            text("""
            INSERT INTO meeting_bookings (room_id, booking_date, start_time, end_time, status)
            VALUES (1, '2026-04-02', '09:00', '12:00', 'confirmed')
        """)
        )
        db_session.commit()

        # 检查4月3日的相同时段
        conflict_count = check_time_conflicts(
            db_session, 1, date(2026, 4, 3), "09:00", "12:00"
        )
        assert conflict_count == 0

    def test_cancelled_booking_no_conflict(self, db_session):
        """测试已取消的预约不产生冲突"""
        # 插入已取消的预约
        db_session.execute(
            text("""
            INSERT INTO meeting_bookings (room_id, booking_date, start_time, end_time, status)
            VALUES (1, '2026-04-02', '09:00', '12:00', 'cancelled')
        """)
        )
        db_session.commit()

        # 检查相同时段
        conflict_count = check_time_conflicts(
            db_session, 1, date(2026, 4, 2), "09:00", "12:00"
        )
        assert conflict_count == 0


# 运行测试
if __name__ == "__main__":
    pytest.main(
        [
            __file__,
            "-v",
            "--cov=Service_MeetingRoom.modules.flexible_booking",
            "--cov-report=term-missing",
        ]
    )
