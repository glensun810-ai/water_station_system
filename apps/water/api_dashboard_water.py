"""
管理中心Dashboard API
提供今日数据统计功能
"""

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session
from datetime import date
from typing import Dict

router = APIRouter(prefix="/api/water/stats", tags=["water_dashboard"])


def get_db():
    """获取数据库会话"""
    from api_meeting import MeetingSessionLocal

    db = MeetingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/today")
async def get_today_water_stats(db: Session = Depends(get_db)) -> Dict:
    """
    获取水站今日统计数据

    Returns:
        {
            "pickup_count": 今日领水次数,
            "pending_amount": 待结算金额,
            "alerts": 库存预警数量,
            "date": 日期
        }
    """
    try:
        today = date.today()

        # 今日领水次数
        result = db.execute(
            text("""
            SELECT COUNT(*) as count
            FROM office_pickups
            WHERE DATE(created_at) = :today
        """),
            {"today": today},
        )
        pickup_count = result.fetchone()
        pickup_count = pickup_count.count if pickup_count else 0

        # 待结算金额
        result = db.execute(
            text("""
            SELECT COALESCE(SUM(total_price), 0) as amount
            FROM office_pickups
            WHERE status = 'pending'
        """)
        )
        pending_amount = result.fetchone()
        pending_amount = float(pending_amount.amount) if pending_amount else 0.0

        # 库存预警数量
        try:
            result = db.execute(
                text("""
                SELECT COUNT(*) as count
                FROM products
                WHERE stock_quantity <= min_stock_threshold
            """)
            )
            alerts = result.fetchone()
            alerts = alerts.count if alerts else 0
        except:
            # 如果products表不存在或没有库存字段，返回0
            alerts = 0

        return {
            "pickup_count": pickup_count,
            "pending_amount": pending_amount,
            "alerts": alerts,
            "date": str(today),
        }

    except Exception as e:
        # 如果出错，返回默认值
        return {
            "pickup_count": 0,
            "pending_amount": 0.0,
            "alerts": 0,
            "date": str(date.today()),
            "error": str(e),
        }
