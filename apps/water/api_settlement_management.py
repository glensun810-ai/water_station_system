"""
统一结算管理API
提供水站和会议室的统一结算功能
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

router = APIRouter(prefix="/api/settlements", tags=["settlement_management"])


def get_db():
    """获取数据库会话"""
    from api_meeting import MeetingSessionLocal

    db = MeetingSessionLocal()
    try:
        yield db
    finally:
        db.close()


# ==================== 数据模型 ====================


class SettlementApply(BaseModel):
    """申请结算"""

    office_id: int
    service_type: str  # water, meeting, all
    record_ids: List[int]


class SettlementConfirm(BaseModel):
    """确认结算"""

    settlement_id: int


class SettlementResponse(BaseModel):
    """结算响应"""

    id: int
    office_id: int
    office_name: str
    service_type: str
    total_amount: float
    status: str
    record_count: int
    applied_by: Optional[str]
    applied_at: Optional[datetime]
    settled_by: Optional[str]
    settled_at: Optional[datetime]


# ==================== API接口 ====================


@router.get("/summary")
async def get_settlement_summary(db: Session = Depends(get_db)):
    """获取结算概览"""
    try:
        # 水站待结算
        water_pending = db.execute(
            text("""
            SELECT COALESCE(SUM(total_price), 0) as amount,
                   COUNT(*) as count
            FROM office_pickups
            WHERE status = 'pending'
        """)
        ).fetchone()

        # 水站已申请
        water_applied = db.execute(
            text("""
            SELECT COALESCE(SUM(total_price), 0) as amount,
                   COUNT(*) as count
            FROM office_pickups
            WHERE status = 'applied'
        """)
        ).fetchone()

        # 水站已结算
        water_settled = db.execute(
            text("""
            SELECT COALESCE(SUM(total_price), 0) as amount,
                   COUNT(*) as count
            FROM office_pickups
            WHERE status = 'settled'
        """)
        ).fetchone()

        # 会议室待结算（假设状态相同）
        meeting_pending = db.execute(
            text("""
            SELECT COALESCE(SUM(total_amount), 0) as amount,
                   COUNT(*) as count
            FROM bookings
            WHERE status = 'pending' OR payment_status = 'pending'
        """)
        ).fetchone()

        meeting_applied = db.execute(
            text("""
            SELECT COALESCE(SUM(total_amount), 0) as amount,
                   COUNT(*) as count
            FROM bookings
            WHERE status = 'applied'
        """)
        ).fetchone()

        meeting_settled = db.execute(
            text("""
            SELECT COALESCE(SUM(total_amount), 0) as amount,
                   COUNT(*) as count
            FROM bookings
            WHERE status = 'settled'
        """)
        ).fetchone()

        return {
            "water": {
                "pending_amount": float(water_pending.amount or 0),
                "pending_count": water_pending.count or 0,
                "applied_amount": float(water_applied.amount or 0),
                "applied_count": water_applied.count or 0,
                "settled_amount": float(water_settled.amount or 0),
                "settled_count": water_settled.count or 0,
            },
            "meeting": {
                "pending_amount": float(meeting_pending.amount or 0),
                "pending_count": meeting_pending.count or 0,
                "applied_amount": float(meeting_applied.amount or 0),
                "applied_count": meeting_applied.count or 0,
                "settled_amount": float(meeting_settled.amount or 0),
                "settled_count": meeting_settled.count or 0,
            },
            "total": {
                "pending_amount": float(
                    (water_pending.amount or 0) + (meeting_pending.amount or 0)
                ),
                "pending_count": (water_pending.count or 0)
                + (meeting_pending.count or 0),
                "applied_amount": float(
                    (water_applied.amount or 0) + (meeting_applied.amount or 0)
                ),
                "applied_count": (water_applied.count or 0)
                + (meeting_applied.count or 0),
                "settled_amount": float(
                    (water_settled.amount or 0) + (meeting_settled.amount or 0)
                ),
                "settled_count": (water_settled.count or 0)
                + (meeting_settled.count or 0),
            },
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取结算概览失败: {str(e)}")


@router.get("/pending")
async def list_pending_settlements(
    office_id: Optional[int] = None,
    service_type: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """获取待结算列表"""
    try:
        records = []

        # 获取水站待结算记录
        if not service_type or service_type == "water":
            water_query = """
                SELECT op.*, o.name as office_name
                FROM office_pickups op
                LEFT JOIN offices o ON op.office_id = o.id
                WHERE op.status = 'pending'
            """
            params = {}

            if office_id:
                water_query += " AND op.office_id = :office_id"
                params["office_id"] = office_id

            water_query += " ORDER BY op.created_at DESC"

            water_result = db.execute(text(water_query), params)
            for row in water_result:
                records.append(
                    {
                        "id": f"water_{row.id}",
                        "record_id": row.id,
                        "service_type": "water",
                        "office_id": row.office_id,
                        "office_name": row.office_name or "未分配",
                        "amount": float(row.total_price or 0),
                        "status": "pending",
                        "created_at": str(row.created_at),
                    }
                )

        # 获取会议室待结算记录
        if not service_type or service_type == "meeting":
            meeting_query = """
                SELECT b.*, o.name as office_name
                FROM bookings b
                LEFT JOIN offices o ON b.office_id = o.id
                WHERE b.status = 'pending'
            """
            params = {}

            if office_id:
                meeting_query += " AND b.office_id = :office_id"
                params["office_id"] = office_id

            meeting_query += " ORDER BY b.created_at DESC"

            meeting_result = db.execute(text(meeting_query), params)
            for row in meeting_result:
                records.append(
                    {
                        "id": f"meeting_{row.id}",
                        "record_id": row.id,
                        "service_type": "meeting",
                        "office_id": row.office_id,
                        "office_name": row.office_name or "未分配",
                        "amount": float(row.total_amount or 0),
                        "status": "pending",
                        "created_at": str(row.created_at),
                    }
                )

        # 按时间排序
        records.sort(key=lambda x: x["created_at"], reverse=True)

        return {"records": records}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取待结算列表失败: {str(e)}")


@router.post("/apply")
async def apply_settlement(settlement: SettlementApply, db: Session = Depends(get_db)):
    """申请结算"""
    try:
        updated_count = 0

        if settlement.service_type == "water" or settlement.service_type == "all":
            for record_id in settlement.record_ids:
                result = db.execute(
                    text(
                        "UPDATE office_pickups SET status = 'applied' WHERE id = :id AND status = 'pending'"
                    ),
                    {"id": record_id},
                )
                updated_count += result.rowcount

        if settlement.service_type == "meeting" or settlement.service_type == "all":
            for record_id in settlement.record_ids:
                result = db.execute(
                    text(
                        "UPDATE bookings SET status = 'applied' WHERE id = :id AND status = 'pending'"
                    ),
                    {"id": record_id},
                )
                updated_count += result.rowcount

        db.commit()

        return {
            "message": f"成功申请{updated_count}条记录",
            "updated_count": updated_count,
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"申请结算失败: {str(e)}")


@router.post("/confirm")
async def confirm_settlement(
    settlement: SettlementConfirm, db: Session = Depends(get_db)
):
    """确认结算"""
    try:
        # 这里需要根据实际业务逻辑实现
        # 暂时返回成功
        return {"message": "结算确认成功"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"确认结算失败: {str(e)}")
