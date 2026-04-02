"""
灵活时间段选择模块
功能：时间选择器、时长验证、冲突检测
Created by: AI Development Team
Version: 1.0.0
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session
from datetime import datetime, date
from typing import Optional
from pydantic import BaseModel, validator
import re

router = APIRouter(prefix="/api/meeting/flexible", tags=["flexible_booking"])


class TimeSlotCheck(BaseModel):
    """时间段检查请求"""

    room_id: int
    booking_date: date
    start_time: str
    end_time: str

    @validator("start_time", "end_time")
    def validate_time_format(cls, v):
        """验证时间格式（HH:MM）"""
        if not re.match(r"^[0-9]{2}:[0-9]{2}$", v):
            raise ValueError("时间格式必须为HH:MM（如09:00）")

        hour, minute = int(v.split(":")[0]), int(v.split(":")[1])
        if hour < 7 or hour > 22:
            raise ValueError("时间必须在07:00-22:00范围内")
        if minute % 30 != 0:
            raise ValueError("分钟必须是30分钟的整数倍（如00或30）")

        return v


class TimeSlotValidation(BaseModel):
    """时间段验证响应"""

    is_available: bool
    conflict_count: int = 0
    duration_minutes: int
    duration_hours: float
    is_valid: bool
    message: str
    warnings: list = []


def get_db():
    """获取数据库会话（从父模块导入）"""
    from Service_WaterManage.backend.api_meeting import MeetingSessionLocal

    db = MeetingSessionLocal()
    try:
        yield db
    finally:
        db.close()


def calculate_duration(start_time: str, end_time: str) -> tuple:
    """
    计算时间段时长

    Args:
        start_time: 开始时间（HH:MM）
        end_time: 结束时间（HH:MM）

    Returns:
        (duration_minutes, duration_hours)
    """
    start_hour, start_minute = (
        int(start_time.split(":")[0]),
        int(start_time.split(":")[1]),
    )
    end_hour, end_minute = int(end_time.split(":")[0]), int(end_time.split(":")[1])

    start_total_minutes = start_hour * 60 + start_minute
    end_total_minutes = end_hour * 60 + end_minute

    duration_minutes = end_total_minutes - start_total_minutes
    duration_hours = duration_minutes / 60.0

    return duration_minutes, duration_hours


def validate_duration_constraints(duration_minutes: int) -> tuple:
    """
    验证时长约束

    Args:
        duration_minutes: 时长（分钟）

    Returns:
        (is_valid, message)
    """
    min_duration = 30
    max_duration = 480

    if duration_minutes < min_duration:
        return False, f"预约时长不能少于{min_duration}分钟"

    if duration_minutes > max_duration:
        return False, f"预约时长不能超过{max_duration}分钟（{max_duration // 60}小时）"

    return True, "时长符合要求"


def check_time_conflicts(
    db: Session, room_id: int, booking_date: date, start_time: str, end_time: str
) -> int:
    """
    检查时间段冲突（参数化查询，避免SQL注入）

    Args:
        db: 数据库会话
        room_id: 会议室ID
        booking_date: 预约日期
        start_time: 开始时间
        end_time: 结束时间

    Returns:
        冲突预约数量
    """
    query = text("""
        SELECT COUNT(*) as conflict_count
        FROM meeting_bookings
        WHERE room_id = :room_id
        AND booking_date = :booking_date
        AND status IN ('pending', 'confirmed')
        AND (
            (start_time <= :start_time AND end_time > :start_time)
            OR (start_time < :end_time AND end_time >= :end_time)
            OR (start_time >= :start_time AND end_time <= :end_time)
        )
    """)

    result = db.execute(
        query,
        {
            "room_id": room_id,
            "booking_date": str(booking_date),
            "start_time": start_time,
            "end_time": end_time,
        },
    )

    row = result.fetchone()
    return row.conflict_count if row else 0


@router.post("/check-time-slot", response_model=TimeSlotValidation)
async def check_time_slot(request: TimeSlotCheck, db: Session = Depends(get_db)):
    """
    检查时间段可用性

    功能：
    1. 验证时间格式和范围（07:00-22:00）
    2. 验证时长约束（30分钟-8小时）
    3. 检查时间段冲突
    4. 返回详细的验证结果
    """
    try:
        # 验证时间逻辑（开始时间必须早于结束时间）
        start_minutes = int(request.start_time.split(":")[0]) * 60 + int(
            request.start_time.split(":")[1]
        )
        end_minutes = int(request.end_time.split(":")[0]) * 60 + int(
            request.end_time.split(":")[1]
        )

        if start_minutes >= end_minutes:
            return TimeSlotValidation(
                is_available=False,
                duration_minutes=0,
                duration_hours=0.0,
                is_valid=False,
                message="开始时间必须早于结束时间",
                warnings=["请调整时间选择"],
            )

        # 计算时长
        duration_minutes, duration_hours = calculate_duration(
            request.start_time, request.end_time
        )

        # 验证时长约束
        duration_valid, duration_message = validate_duration_constraints(
            duration_minutes
        )

        if not duration_valid:
            return TimeSlotValidation(
                is_available=False,
                duration_minutes=duration_minutes,
                duration_hours=duration_hours,
                is_valid=False,
                message=duration_message,
                warnings=[duration_message],
            )

        # 检查时间段冲突
        conflict_count = check_time_conflicts(
            db,
            request.room_id,
            request.booking_date,
            request.start_time,
            request.end_time,
        )

        # 构建响应
        warnings = []
        if conflict_count > 0:
            warnings.append(f"该时间段已有{conflict_count}个预约冲突")

        is_available = conflict_count == 0
        message = (
            "时间段可用" if is_available else f"时间段冲突：已有{conflict_count}个预约"
        )

        return TimeSlotValidation(
            is_available=is_available,
            conflict_count=conflict_count,
            duration_minutes=duration_minutes,
            duration_hours=duration_hours,
            is_valid=True,
            message=message,
            warnings=warnings,
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"检查时间段失败: {str(e)}")


@router.get("/available-slots/{room_id}/{booking_date}")
async def get_available_slots(
    room_id: int, booking_date: date, db: Session = Depends(get_db)
):
    """
    获取会议室某天的可用时间段

    功能：
    1. 查询该会议室当天所有已预约时段
    2. 计算可用时段（07:00-22:00范围内）
    3. 返回可视化空闲时段列表
    """
    try:
        # 查询已预约时段（参数化查询）
        query = text("""
            SELECT start_time, end_time
            FROM meeting_bookings
            WHERE room_id = :room_id
            AND booking_date = :booking_date
            AND status IN ('pending', 'confirmed')
            ORDER BY start_time
        """)

        result = db.execute(
            query, {"room_id": room_id, "booking_date": str(booking_date)}
        )

        booked_slots = [(row.start_time, row.end_time) for row in result]

        # 计算可用时段（07:00-22:00，每30分钟为一个时段）
        available_slots = []
        start_hour = 7
        end_hour = 22

        for hour in range(start_hour, end_hour):
            for minute in [0, 30]:
                time_str = f"{hour:02d}:{minute:02d}"
                next_time_str = (
                    f"{hour:02d}:{minute + 30:02d}"
                    if minute == 0
                    else f"{hour + 1:02d}:00"
                )

                # 检查该时段是否被占用
                is_available = True
                for booked_start, booked_end in booked_slots:
                    # 时间段重叠判断
                    if (
                        (time_str >= booked_start and time_str < booked_end)
                        or (
                            next_time_str > booked_start and next_time_str <= booked_end
                        )
                        or (time_str <= booked_start and next_time_str >= booked_end)
                    ):
                        is_available = False
                        break

                available_slots.append(
                    {
                        "time": time_str,
                        "end_time": next_time_str,
                        "is_available": is_available,
                        "duration": 30,  # 分钟
                    }
                )

        return {
            "room_id": room_id,
            "booking_date": str(booking_date),
            "available_slots": available_slots,
            "booked_slots": booked_slots,
            "total_slots": len(available_slots),
            "available_count": sum(
                1 for slot in available_slots if slot["is_available"]
            ),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取可用时段失败: {str(e)}")


# 快捷时段选项（供前端使用）
QUICK_TIME_SLOTS = [
    {"label": "上午（09:00-12:00）", "start": "09:00", "end": "12:00"},
    {"label": "下午（14:00-18:00）", "start": "14:00", "end": "18:00"},
    {"label": "晚上（19:00-21:00）", "start": "19:00", "end": "21:00"},
]


@router.get("/quick-slots")
async def get_quick_slots():
    """获取快捷时段选项"""
    return {
        "quick_slots": QUICK_TIME_SLOTS,
        "message": "快捷时段选项，用户可快速选择常用时间段",
    }
