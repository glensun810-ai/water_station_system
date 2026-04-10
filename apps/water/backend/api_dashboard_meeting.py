"""
会议室管理中心Dashboard API
提供今日数据统计功能
"""

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session
from datetime import date
from typing import Dict

router = APIRouter(prefix="/api/meeting/stats", tags=["meeting_dashboard"])


def get_db():
    """获取数据库会话"""
    from api_meeting import MeetingSessionLocal

    db = MeetingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/today")
async def get_today_meeting_stats(db: Session = Depends(get_db)) -> Dict:
    """
    获取会议室今日统计数据

    Returns:
        {
            "booking_count": 今日预约次数,
            "pending_approvals": 待审批数量,
            "alerts": 异常预约数量,
            "date": 日期
        }
    """
    try:
        today = date.today()

        # 今日预约次数
        result = db.execute(
            text("""
            SELECT COUNT(*) as count
            FROM bookings
            WHERE DATE(created_at) = :today
        """),
            {"today": today},
        )
        booking_count = result.fetchone()
        booking_count = booking_count.count if booking_count else 0

        # 待审批数量
        result = db.execute(
            text("""
            SELECT COUNT(*) as count
            FROM bookings
            WHERE status = 'pending_approval'
        """)
        )
        pending_approvals = result.fetchone()
        pending_approvals = pending_approvals.count if pending_approvals else 0

        # 异常预约数量（超时未确认等）
        try:
            result = db.execute(
                text("""
                SELECT COUNT(*) as count
                FROM bookings
                WHERE status IN ('overdue', 'abnormal')
            """)
            )
            alerts = result.fetchone()
            alerts = alerts.count if alerts else 0
        except:
            # 如果没有异常状态，返回0
            alerts = 0

        return {
            "booking_count": booking_count,
            "pending_approvals": pending_approvals,
            "alerts": alerts,
            "date": str(today),
        }

    except Exception as e:
        # 如果出错，返回默认值
        return {
            "booking_count": 0,
            "pending_approvals": 0,
            "alerts": 0,
            "date": str(date.today()),
            "error": str(e),
        }
