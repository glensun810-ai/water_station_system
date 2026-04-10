"""
统一结算 API
聚合水站和会议室的结算数据，提供统一的查询和操作接口
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional
from datetime import datetime, date
from pydantic import BaseModel, Field
from enum import Enum
import sqlite3
import os

from config.database import get_db
from depends.auth import get_admin_user
from models.user import User
from models.pickup import OfficePickup
from models.office import Office
from models.product import Product

router = APIRouter(prefix="/api/unified/settlement", tags=["统一结算管理"])


class ServiceType(str, Enum):
    WATER = "water"
    MEETING = "meeting"
    DINING = "dining"
    ALL = "all"


class UnifiedStatus(str, Enum):
    PENDING = "pending"
    APPLIED = "applied"
    SETTLED = "settled"


class SettlementStatus(str, Enum):
    PENDING = "pending"
    APPLIED = "applied"
    SETTLED = "settled"
    UNPAID = "unpaid"
    PAID = "paid"


STATUS_DISPLAY = {
    "pending": ("待结算", "orange"),
    "applied": ("已申请", "blue"),
    "settled": ("已结清", "green"),
    "unpaid": ("待结算", "orange"),
    "paid": ("已结清", "green"),
}

SERVICE_DISPLAY = {
    "water": ("水站领水", "💧"),
    "meeting": ("会议室预约", "📅"),
    "dining": ("餐厅用餐", "🍽️"),
}


class UnifiedSettlementRecord(BaseModel):
    id: int
    service_type: str
    service_name: str
    service_icon: str
    record_no: str
    office_id: int
    office_name: str
    product_name: Optional[str] = None
    product_specification: Optional[str] = None
    quantity: Optional[int] = None
    unit: Optional[str] = None
    room_name: Optional[str] = None
    booking_date: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    duration: Optional[float] = None
    amount: float
    status: str
    status_text: str
    status_color: str
    original_status: str
    record_date: str
    created_at: str


class ServiceStatistics(BaseModel):
    pending_count: int = 0
    pending_amount: float = 0
    applied_count: int = 0
    applied_amount: float = 0
    settled_count: int = 0
    settled_amount: float = 0


class UnifiedStatistics(BaseModel):
    water: ServiceStatistics = Field(default_factory=ServiceStatistics)
    meeting: ServiceStatistics = Field(default_factory=ServiceStatistics)
    dining: ServiceStatistics = Field(default_factory=ServiceStatistics)
    total_count: int = 0
    total_amount: float = 0


class PaginationInfo(BaseModel):
    total: int
    page: int
    page_size: int
    total_pages: int


class UnifiedSettlementListResponse(BaseModel):
    records: List[UnifiedSettlementRecord]
    pagination: PaginationInfo
    statistics: UnifiedStatistics


class UnifiedStatisticsResponse(BaseModel):
    statistics: UnifiedStatistics
    period: Optional[dict] = None


class SettlementRecordConfirm(BaseModel):
    service_type: str
    record_id: int


class BatchConfirmRequest(BaseModel):
    records: List[SettlementRecordConfirm]


class BatchConfirmResponse(BaseModel):
    success: bool
    message: str
    confirmed_count: int
    failed_count: int
    failed_records: List[dict] = []


class OfficeSummaryItem(BaseModel):
    office_id: int
    office_name: str
    water_pending_count: int = 0
    water_pending_amount: float = 0
    water_settled_count: int = 0
    water_settled_amount: float = 0
    meeting_pending_count: int = 0
    meeting_pending_amount: float = 0
    meeting_settled_count: int = 0
    meeting_settled_amount: float = 0

    @property
    def total_pending_count(self) -> int:
        return self.water_pending_count + self.meeting_pending_count

    @property
    def total_pending_amount(self) -> float:
        return self.water_pending_amount + self.meeting_pending_amount

    @property
    def total_settled_count(self) -> int:
        return self.water_settled_count + self.meeting_settled_count

    @property
    def total_settled_amount(self) -> float:
        return self.water_settled_amount + self.meeting_settled_amount


class OfficeSummaryResponse(BaseModel):
    offices: List[OfficeSummaryItem]
    total_pending: float
    total_settled: float


MEETING_DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "Service_MeetingRoom",
    "backend",
    "meeting.db",
)


def get_meeting_db():
    conn = sqlite3.connect(MEETING_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def get_water_records(
    db: Session,
    service_type: Optional[str] = None,
    status: Optional[str] = None,
    office_id: Optional[int] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    keyword: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple:
    conditions = ["p.is_deleted = 0"]
    params = {}

    if service_type and service_type != "all" and service_type != "water":
        return [], 0

    if status:
        conditions.append("p.settlement_status = :status")
        params["status"] = status

    if office_id:
        conditions.append("p.office_id = :office_id")
        params["office_id"] = office_id

    if start_date:
        conditions.append("DATE(p.pickup_time) >= :start_date")
        params["start_date"] = start_date

    if end_date:
        conditions.append("DATE(p.pickup_time) <= :end_date")
        params["end_date"] = end_date

    if keyword:
        conditions.append(
            "(p.office_name LIKE :keyword OR p.product_name LIKE :keyword OR p.pickup_person LIKE :keyword)"
        )
        params["keyword"] = f"%{keyword}%"

    where_clause = " AND ".join(conditions)

    # Use ORM instead of raw SQL to avoid SQLite/PostgreSQL mismatch
    query = db.query(OfficePickup).filter(OfficePickup.is_deleted == 0)

    if status:
        query = query.filter(OfficePickup.settlement_status == status)
    if office_id:
        query = query.filter(OfficePickup.office_id == office_id)
    if start_date:
        from datetime import datetime

        try:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            query = query.filter(OfficePickup.pickup_time >= start_dt)
        except:
            pass
    if end_date:
        from datetime import datetime

        try:
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
            query = query.filter(OfficePickup.pickup_time <= end_dt)
        except:
            pass
    if keyword:
        query = query.filter(
            (OfficePickup.office_name.contains(keyword))
            | (OfficePickup.product_name.contains(keyword))
            | (OfficePickup.pickup_person.contains(keyword))
        )

    total = query.count()

    offset = (page - 1) * page_size
    pickups = (
        query.order_by(OfficePickup.pickup_time.desc())
        .offset(offset)
        .limit(page_size)
        .all()
    )

    records = []
    for p in pickups:
        status_display = STATUS_DISPLAY.get(
            p.settlement_status, (p.settlement_status, "gray")
        )
        records.append(
            {
                "id": p.id,
                "service_type": "water",
                "service_name": "水站领水",
                "service_icon": "💧",
                "record_no": f"PK{p.id:06d}",
                "office_id": p.office_id,
                "office_name": p.office_name,
                "product_name": p.product_name,
                "product_specification": p.product_specification,
                "quantity": p.quantity,
                "unit": None,
                "room_name": None,
                "booking_date": None,
                "start_time": None,
                "end_time": None,
                "duration": None,
                "amount": float(p.total_amount) if p.total_amount else 0,
                "status": p.settlement_status,
                "status_text": status_display[0],
                "status_color": status_display[1],
                "original_status": p.settlement_status,
                "record_date": p.pickup_time.strftime("%Y-%m-%d")
                if p.pickup_time
                else "",
                "created_at": p.created_at.isoformat() if p.created_at else "",
            }
        )

    return records, total


def get_meeting_records(
    service_type: Optional[str] = None,
    status: Optional[str] = None,
    office_id: Optional[int] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    keyword: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple:
    if service_type and service_type != "all" and service_type != "meeting":
        return [], 0

    if not os.path.exists(MEETING_DB_PATH):
        return [], 0

    conn = get_meeting_db()
    cursor = conn.cursor()

    conditions = ["b.is_deleted = 0"]
    params = []

    if status:
        if status == "pending":
            conditions.append("b.payment_status IN ('unpaid', 'pending')")
        elif status == "applied":
            conditions.append("b.payment_status = 'applied'")
        elif status == "settled":
            conditions.append("b.payment_status = 'paid'")

    if office_id:
        conditions.append("b.office_id = ?")
        params.append(office_id)

    if start_date:
        conditions.append("b.booking_date >= ?")
        params.append(start_date)

    if end_date:
        conditions.append("b.booking_date <= ?")
        params.append(end_date)

    if keyword:
        conditions.append(
            "(b.department LIKE ? OR r.name LIKE ? OR b.user_name LIKE ?)"
        )
        params.extend([f"%{keyword}%", f"%{keyword}%", f"%{keyword}%"])

    where_clause = " AND ".join(conditions)

    count_query = f"SELECT COUNT(*) as total FROM meeting_bookings b LEFT JOIN meeting_rooms r ON b.room_id = r.id WHERE {where_clause}"
    cursor.execute(count_query, params)
    total = cursor.fetchone()["total"]

    offset = (page - 1) * page_size
    params.extend([page_size, offset])

    query = f"""
        SELECT 
            b.id,
            b.office_id,
            COALESCE(b.department, '未知') AS office_name,
            r.name AS room_name,
            b.booking_date,
            b.start_time,
            b.end_time,
            b.duration,
            b.actual_fee AS amount,
            b.payment_status AS status,
            b.booking_date AS record_date,
            b.created_at,
            'meeting' AS service_type,
            '会议室预约' AS service_name,
            '📅' AS service_icon
        FROM meeting_bookings b
        LEFT JOIN meeting_rooms r ON b.room_id = r.id
        WHERE {where_clause}
        ORDER BY b.created_at DESC
        LIMIT ? OFFSET ?
    """

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    records = []
    for row in rows:
        status_display = STATUS_DISPLAY.get(row["status"], (row["status"], "gray"))
        records.append(
            {
                "id": row["id"],
                "service_type": row["service_type"],
                "service_name": row["service_name"],
                "service_icon": row["service_icon"],
                "record_no": f"MT{row['id']:06d}",
                "office_id": row["office_id"] or 0,
                "office_name": row["office_name"],
                "product_name": None,
                "product_specification": None,
                "quantity": None,
                "unit": None,
                "room_name": row["room_name"],
                "booking_date": row["booking_date"],
                "start_time": row["start_time"],
                "end_time": row["end_time"],
                "duration": float(row["duration"]) if row["duration"] else 0,
                "amount": float(row["amount"]) if row["amount"] else 0,
                "status": row["status"],
                "status_text": status_display[0],
                "status_color": status_display[1],
                "original_status": row["status"],
                "record_date": row["record_date"],
                "created_at": row["created_at"]
                if isinstance(row["created_at"], str)
                else str(row["created_at"]),
            }
        )

    return records, total


def get_water_statistics(
    db: Session,
    office_id: Optional[int] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> ServiceStatistics:
    from datetime import datetime

    stats = ServiceStatistics()

    query = db.query(OfficePickup).filter(OfficePickup.is_deleted == 0)

    if office_id:
        query = query.filter(OfficePickup.office_id == office_id)
    if start_date:
        try:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            query = query.filter(OfficePickup.pickup_time >= start_dt)
        except:
            pass
    if end_date:
        try:
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
            query = query.filter(OfficePickup.pickup_time <= end_dt)
        except:
            pass

    pickups = query.all()

    for p in pickups:
        status = p.settlement_status
        amount = float(p.total_amount) if p.total_amount else 0

        if status == "pending":
            stats.pending_count += 1
            stats.pending_amount += amount
        elif status == "applied":
            stats.applied_count += 1
            stats.applied_amount += amount
        elif status == "settled":
            stats.settled_count += 1
            stats.settled_amount += amount

    return stats


def get_meeting_statistics(
    office_id: Optional[int] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> ServiceStatistics:
    stats = ServiceStatistics()

    if not os.path.exists(MEETING_DB_PATH):
        return stats

    conn = get_meeting_db()
    cursor = conn.cursor()

    conditions = ["is_deleted = 0"]
    params = []

    if office_id:
        conditions.append("office_id = ?")
        params.append(office_id)

    if start_date:
        conditions.append("booking_date >= ?")
        params.append(start_date)

    if end_date:
        conditions.append("booking_date <= ?")
        params.append(end_date)

    where_clause = " AND ".join(conditions)

    query = f"""
        SELECT 
            payment_status,
            COUNT(*) as count,
            COALESCE(SUM(actual_fee), 0) as amount
        FROM meeting_bookings
        WHERE {where_clause}
        GROUP BY payment_status
    """

    cursor.execute(query, params)
    for row in cursor.fetchall():
        status = row["payment_status"]
        count = row["count"] or 0
        amount = float(row["amount"]) if row["amount"] else 0

        if status in ("unpaid", "pending"):
            stats.pending_count += count
            stats.pending_amount += amount
        elif status == "applied":
            stats.applied_count = count
            stats.applied_amount = amount
        elif status == "paid":
            stats.settled_count = count
            stats.settled_amount = amount

    conn.close()
    return stats


def confirm_water_settlement(db: Session, pickup_id: int) -> bool:
    pickup = (
        db.query(OfficePickup)
        .filter(OfficePickup.id == pickup_id, OfficePickup.is_deleted == 0)
        .first()
    )

    if not pickup:
        raise ValueError(f"领水记录不存在: {pickup_id}")

    if pickup.settlement_status not in ["pending", "applied"]:
        raise ValueError(f"当前状态不允许确认结算: {pickup.settlement_status}")

    pickup.settlement_status = "settled"
    return True


def confirm_meeting_payment(booking_id: int) -> bool:
    if not os.path.exists(MEETING_DB_PATH):
        raise ValueError("会议室数据库不存在")

    conn = get_meeting_db()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT payment_status FROM meeting_bookings WHERE id = ? AND is_deleted = 0",
        (booking_id,),
    )
    row = cursor.fetchone()

    if not row:
        conn.close()
        raise ValueError(f"会议室预约记录不存在: {booking_id}")

    if row["payment_status"] not in ["unpaid", "pending", "applied"]:
        conn.close()
        raise ValueError(f"当前状态不允许确认: {row['payment_status']}")

    cursor.execute(
        "UPDATE meeting_bookings SET payment_status = 'paid', updated_at = ? WHERE id = ?",
        (datetime.now().isoformat(), booking_id),
    )
    conn.commit()
    conn.close()
    return True


@router.get("/summary", response_model=UnifiedStatisticsResponse)
def get_summary(
    office_id: Optional[int] = Query(None, description="办公室ID"),
    start_date: Optional[str] = Query(None, description="开始日期 YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="结束日期 YYYY-MM-DD"),
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    water_stats = get_water_statistics(db, office_id, start_date, end_date)
    meeting_stats = get_meeting_statistics(office_id, start_date, end_date)

    total_count = (
        water_stats.pending_count
        + water_stats.applied_count
        + water_stats.settled_count
        + meeting_stats.pending_count
        + meeting_stats.applied_count
        + meeting_stats.settled_count
    )
    total_amount = (
        water_stats.pending_amount
        + water_stats.applied_amount
        + water_stats.settled_amount
        + meeting_stats.pending_amount
        + meeting_stats.applied_amount
        + meeting_stats.settled_amount
    )

    return {
        "statistics": {
            "water": water_stats,
            "meeting": meeting_stats,
            "dining": ServiceStatistics(),
            "total_count": total_count,
            "total_amount": total_amount,
        },
        "period": {
            "start_date": start_date,
            "end_date": end_date,
        }
        if start_date or end_date
        else None,
    }


@router.get("/records", response_model=UnifiedSettlementListResponse)
def get_records(
    service_type: str = Query("all", description="服务类型: water/meeting/all"),
    status: Optional[str] = Query(None, description="状态: pending/applied/settled"),
    office_id: Optional[int] = Query(None, description="办公室ID"),
    start_date: Optional[str] = Query(None, description="开始日期 YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="结束日期 YYYY-MM-DD"),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页条数"),
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    water_records, water_total = get_water_records(
        db,
        service_type,
        status,
        office_id,
        start_date,
        end_date,
        keyword,
        page,
        page_size,
    )
    meeting_records, meeting_total = get_meeting_records(
        service_type, status, office_id, start_date, end_date, keyword, page, page_size
    )

    if service_type == "all":
        records = sorted(
            water_records + meeting_records,
            key=lambda x: x.get("created_at", ""),
            reverse=True,
        )
        total = water_total + meeting_total
    elif service_type == "water":
        records = water_records
        total = water_total
    elif service_type == "meeting":
        records = meeting_records
        total = meeting_total
    else:
        records = []
        total = 0

    offset = (page - 1) * page_size
    records = records[offset : offset + page_size]

    water_stats = get_water_statistics(db, office_id, start_date, end_date)
    meeting_stats = get_meeting_statistics(office_id, start_date, end_date)

    total_count = (
        water_stats.pending_count
        + water_stats.applied_count
        + water_stats.settled_count
        + meeting_stats.pending_count
        + meeting_stats.applied_count
        + meeting_stats.settled_count
    )
    total_amount = (
        water_stats.pending_amount
        + water_stats.applied_amount
        + water_stats.settled_amount
        + meeting_stats.pending_amount
        + meeting_stats.applied_amount
        + meeting_stats.settled_amount
    )

    return {
        "records": records,
        "pagination": {
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size if total > 0 else 1,
        },
        "statistics": {
            "water": water_stats,
            "meeting": meeting_stats,
            "dining": ServiceStatistics(),
            "total_count": total_count,
            "total_amount": total_amount,
        },
    }


@router.get("/by-office")
def get_by_office(
    start_date: Optional[str] = Query(None, description="开始日期 YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="结束日期 YYYY-MM-DD"),
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    offices = db.query(Office).filter(Office.is_active == 1).all()

    result = []
    total_pending = 0
    total_settled = 0

    for office in offices:
        water_stats = get_water_statistics(db, office.id, start_date, end_date)
        meeting_stats = get_meeting_statistics(office.id, start_date, end_date)

        item = OfficeSummaryItem(
            office_id=office.id,
            office_name=office.name,
            water_pending_count=water_stats.pending_count,
            water_pending_amount=water_stats.pending_amount,
            water_settled_count=water_stats.settled_count,
            water_settled_amount=water_stats.settled_amount,
            meeting_pending_count=meeting_stats.pending_count,
            meeting_pending_amount=meeting_stats.pending_amount,
            meeting_settled_count=meeting_stats.settled_count,
            meeting_settled_amount=meeting_stats.settled_amount,
        )

        if item.total_pending_count > 0 or item.total_settled_count > 0:
            result.append(item)
            total_pending += item.total_pending_amount
            total_settled += item.total_settled_amount

    result.sort(key=lambda x: x.total_pending_amount, reverse=True)

    return {
        "offices": [r.model_dump() for r in result],
        "total_pending": total_pending,
        "total_settled": total_settled,
    }


@router.post("/batch-confirm", response_model=BatchConfirmResponse)
def batch_confirm(
    request: BatchConfirmRequest,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    confirmed = 0
    failed = []

    for record in request.records:
        try:
            if record.service_type == "water":
                confirm_water_settlement(db, record.record_id)
                confirmed += 1
            elif record.service_type == "meeting":
                confirm_meeting_payment(record.record_id)
                confirmed += 1
            else:
                failed.append(
                    {
                        "service_type": record.service_type,
                        "record_id": record.record_id,
                        "reason": f"不支持的服务类型: {record.service_type}",
                    }
                )
        except Exception as e:
            failed.append(
                {
                    "service_type": record.service_type,
                    "record_id": record.record_id,
                    "reason": str(e),
                }
            )

    try:
        db.commit()
    except Exception as e:
        db.rollback()
        return {
            "success": False,
            "message": f"批量确认失败: {str(e)}",
            "confirmed_count": 0,
            "failed_count": len(request.records),
            "failed_records": [
                {
                    "service_type": r.service_type,
                    "record_id": r.record_id,
                    "reason": str(e),
                }
                for r in request.records
            ],
        }

    return {
        "success": True,
        "message": f"批量确认完成，成功 {confirmed} 条"
        + (f"，失败 {len(failed)} 条" if failed else ""),
        "confirmed_count": confirmed,
        "failed_count": len(failed),
        "failed_records": failed,
    }


@router.get("/water")
def get_water(
    status: Optional[str] = Query(None),
    office_id: Optional[int] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    keyword: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    records, total = get_water_records(
        db, "water", status, office_id, start_date, end_date, keyword, page, page_size
    )

    return {
        "records": records,
        "pagination": {
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size if total > 0 else 1,
        },
    }


@router.get("/meeting")
def get_meeting(
    status: Optional[str] = Query(None),
    office_id: Optional[int] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    keyword: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    records, total = get_meeting_records(
        "meeting", status, office_id, start_date, end_date, keyword, page, page_size
    )

    return {
        "records": records,
        "pagination": {
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size if total > 0 else 1,
        },
    }
