"""
会议室管理 API
支持会议室管理、预约管理
架构修复版 - 解决硬编码路径、SQL注入、连接性能问题
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker
from datetime import datetime, date
from typing import List, Optional
from pydantic import BaseModel
import random
import string
import os

router = APIRouter(prefix="/api/meeting", tags=["meeting"])

# ==================== 数据库配置（模块级别，避免重复创建）====================
# 动态获取数据库路径（避免硬编码）
MEETING_DB_PATH = os.path.join(
    os.path.dirname(__file__), "../../Service_MeetingRoom/backend/meeting.db"
)
MEETING_DB_PATH = os.path.abspath(MEETING_DB_PATH)

# 检查数据库文件是否存在
if not os.path.exists(MEETING_DB_PATH):
    raise RuntimeError(f"会议室数据库不存在: {MEETING_DB_PATH}")

# 创建模块级别的 engine（性能优化）
meeting_engine = create_engine(
    f"sqlite:///{MEETING_DB_PATH}",
    connect_args={"check_same_thread": False},
    pool_pre_ping=True,  # 连接池健康检查
)

# 创建 Session 工厂
MeetingSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=meeting_engine
)


def get_db():
    """获取数据库会话（依赖注入）"""
    db = MeetingSessionLocal()
    try:
        yield db
    finally:
        db.close()


class MeetingRoomBase(BaseModel):
    name: str
    location: Optional[str] = None
    capacity: int = 10
    facilities: Optional[str] = None
    price_per_hour: float = 0.0
    member_price_per_hour: float = 0.0
    free_hours_per_month: int = 0
    is_active: bool = True


class MeetingRoomCreate(MeetingRoomBase):
    pass


class MeetingRoomUpdate(BaseModel):
    name: Optional[str] = None
    location: Optional[str] = None
    capacity: Optional[int] = None
    facilities: Optional[str] = None
    price_per_hour: Optional[float] = None
    member_price_per_hour: Optional[float] = None
    free_hours_per_month: Optional[int] = None
    is_active: Optional[bool] = None


class MeetingRoomResponse(MeetingRoomBase):
    id: int
    created_at: datetime
    updated_at: datetime


class MeetingBookingBase(BaseModel):
    room_id: int
    user_type: str = "external"
    office_id: Optional[int] = None
    user_name: str
    user_phone: str
    department: Optional[str] = None
    booking_date: date
    start_time: str
    end_time: str
    meeting_title: Optional[str] = None
    attendees_count: int = 1


class MeetingBookingCreate(MeetingBookingBase):
    pass


class MeetingBookingResponse(MeetingBookingBase):
    id: int
    booking_no: str
    room_name: Optional[str] = None
    duration: Optional[float] = None
    total_fee: float = 0.0
    status: str = "pending"
    created_at: datetime


@router.get("/rooms", response_model=List[MeetingRoomResponse])
def get_rooms(is_active: Optional[bool] = Query(None), db: Session = Depends(get_db)):
    try:
        from sqlalchemy import text

        query = "SELECT * FROM meeting_rooms"
        if is_active is not None:
            query += f" WHERE is_active = {1 if is_active else 0}"
        query += " ORDER BY id"

        result = db.execute(text(query))
        rooms = []
        for row in result:
            rooms.append(
                {
                    "id": row.id,
                    "name": row.name,
                    "location": row.location,
                    "capacity": row.capacity,
                    "facilities": row.facilities,
                    "price_per_hour": float(row.price_per_hour)
                    if row.price_per_hour
                    else 0.0,
                    "member_price_per_hour": float(row.member_price_per_hour)
                    if row.member_price_per_hour
                    else 0.0,
                    "free_hours_per_month": row.free_hours_per_month or 0,
                    "is_active": bool(row.is_active),
                    "created_at": row.created_at or datetime.now(),
                    "updated_at": row.updated_at or datetime.now(),
                }
            )
        return rooms
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取会议室列表失败: {str(e)}")


@router.get("/rooms/{room_id}", response_model=MeetingRoomResponse)
def get_room(room_id: int, db: Session = Depends(get_db)):
    try:
        result = db.execute(
            text("SELECT * FROM meeting_rooms WHERE id = :room_id"),
            {"room_id": room_id},
        )
        row = result.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="会议室不存在")

        return {
            "id": row.id,
            "name": row.name,
            "location": row.location,
            "capacity": row.capacity,
            "facilities": row.facilities,
            "price_per_hour": float(row.price_per_hour) if row.price_per_hour else 0.0,
            "member_price_per_hour": float(row.member_price_per_hour)
            if row.member_price_per_hour
            else 0.0,
            "free_hours_per_month": row.free_hours_per_month or 0,
            "is_active": bool(row.is_active),
            "created_at": row.created_at or datetime.now(),
            "updated_at": row.updated_at or datetime.now(),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取会议室详情失败: {str(e)}")


@router.post("/rooms", response_model=MeetingRoomResponse)
def create_room(room: MeetingRoomCreate, db: Session = Depends(get_db)):
    try:
        from sqlalchemy import text

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        query = text("""
            INSERT INTO meeting_rooms (name, location, capacity, facilities, price_per_hour, member_price_per_hour, free_hours_per_month, is_active, created_at, updated_at)
            VALUES (:name, :location, :capacity, :facilities, :price_per_hour, :member_price_per_hour, :free_hours_per_month, :is_active, :created_at, :updated_at)
        """)

        result = db.execute(
            query,
            {
                "name": room.name,
                "location": room.location,
                "capacity": room.capacity,
                "facilities": room.facilities,
                "price_per_hour": room.price_per_hour,
                "member_price_per_hour": room.member_price_per_hour,
                "free_hours_per_month": room.free_hours_per_month,
                "is_active": 1 if room.is_active else 0,
                "created_at": now,
                "updated_at": now,
            },
        )
        db.commit()

        room_id = result.lastrowid
        return {
            "id": room_id,
            "name": room.name,
            "location": room.location,
            "capacity": room.capacity,
            "facilities": room.facilities,
            "price_per_hour": room.price_per_hour,
            "member_price_per_hour": room.member_price_per_hour,
            "free_hours_per_month": room.free_hours_per_month,
            "is_active": room.is_active,
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"创建会议室失败: {str(e)}")


@router.put("/rooms/{room_id}", response_model=MeetingRoomResponse)
def update_room(room_id: int, room: MeetingRoomUpdate, db: Session = Depends(get_db)):
    try:
        from sqlalchemy import text

        existing = db.execute(
            text("SELECT * FROM meeting_rooms WHERE id = :room_id"),
            {"room_id": room_id},
        ).fetchone()
        if not existing:
            raise HTTPException(status_code=404, detail="会议室不存在")

        updates = []
        params = {"room_id": room_id}

        if room.name is not None:
            updates.append("name = :name")
            params["name"] = room.name
        if room.location is not None:
            updates.append("location = :location")
            params["location"] = room.location
        if room.capacity is not None:
            updates.append("capacity = :capacity")
            params["capacity"] = room.capacity
        if room.facilities is not None:
            updates.append("facilities = :facilities")
            params["facilities"] = room.facilities
        if room.price_per_hour is not None:
            updates.append("price_per_hour = :price_per_hour")
            params["price_per_hour"] = room.price_per_hour
        if room.member_price_per_hour is not None:
            updates.append("member_price_per_hour = :member_price_per_hour")
            params["member_price_per_hour"] = room.member_price_per_hour
        if room.free_hours_per_month is not None:
            updates.append("free_hours_per_month = :free_hours_per_month")
            params["free_hours_per_month"] = room.free_hours_per_month
        if room.is_active is not None:
            updates.append("is_active = :is_active")
            params["is_active"] = 1 if room.is_active else 0

        if updates:
            updates.append("updated_at = :updated_at")
            params["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            query = text(
                f"UPDATE meeting_rooms SET {', '.join(updates)} WHERE id = :room_id"
            )
            db.execute(query, params)
            db.commit()

        return get_room(room_id, db)
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"更新会议室失败: {str(e)}")


@router.delete("/rooms/{room_id}")
def delete_room(room_id: int, db: Session = Depends(get_db)):
    try:
        from sqlalchemy import text

        existing = db.execute(
            text("SELECT id FROM meeting_rooms WHERE id = :room_id"),
            {"room_id": room_id},
        ).fetchone()
        if not existing:
            raise HTTPException(status_code=404, detail="会议室不存在")

        db.execute(
            text("DELETE FROM meeting_rooms WHERE id = :room_id"), {"room_id": room_id}
        )
        db.commit()

        return {"success": True, "message": "会议室已删除"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"删除会议室失败: {str(e)}")


def generate_booking_no():
    date_str = datetime.now().strftime("%Y%m%d")
    random_str = "".join(random.choices(string.digits, k=3))
    return f"MT{date_str}{random_str}"


@router.get("/bookings", response_model=List[MeetingBookingResponse])
def get_bookings(
    status: Optional[str] = Query(None),
    room_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
):
    try:
        from sqlalchemy import text

        query = "SELECT * FROM meeting_bookings WHERE 1=1"
        params = {}

        if status:
            query += " AND status = :status"
            params["status"] = status
        if room_id:
            query += " AND room_id = :room_id"
            params["room_id"] = room_id

        query += " ORDER BY booking_date DESC, start_time"

        result = db.execute(text(query), params)
        bookings = []
        for row in result:
            bookings.append(
                {
                    "id": row.id,
                    "booking_no": row.booking_no,
                    "room_id": row.room_id,
                    "room_name": row.room_name,
                    "user_type": row.user_type
                    if hasattr(row, "user_type")
                    else "external",
                    "office_id": row.office_id if hasattr(row, "office_id") else None,
                    "user_name": row.user_name,
                    "user_phone": row.user_phone,
                    "department": row.department,
                    "booking_date": row.booking_date,
                    "start_time": row.start_time,
                    "end_time": row.end_time,
                    "duration": float(row.duration) if row.duration else 0.0,
                    "meeting_title": row.meeting_title,
                    "attendees_count": row.attendees_count or 1,
                    "total_fee": float(row.total_fee) if row.total_fee else 0.0,
                    "status": row.status,
                    "created_at": row.created_at or datetime.now(),
                }
            )
        return bookings
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取预约列表失败: {str(e)}")


@router.post("/bookings", response_model=MeetingBookingResponse)
def create_booking(booking: MeetingBookingCreate, db: Session = Depends(get_db)):
    try:
        from sqlalchemy import text

        if booking.user_type not in ["internal", "external"]:
            raise HTTPException(
                status_code=400, detail="用户类型必须是 internal 或 external"
            )

        if booking.user_type == "internal":
            if not booking.office_id:
                raise HTTPException(status_code=400, detail="内部用户必须选择办公室")

        room = db.execute(
            text("SELECT * FROM meeting_rooms WHERE id = :room_id"),
            {"room_id": booking.room_id},
        ).fetchone()
        if not room:
            raise HTTPException(status_code=404, detail="会议室不存在")

        conflict_query = text("""
            SELECT id FROM meeting_bookings 
            WHERE room_id = :room_id 
            AND booking_date = :booking_date
            AND status IN ('pending', 'confirmed')
            AND (
                (start_time <= :start_time AND end_time > :start_time)
                OR (start_time < :end_time AND end_time >= :end_time)
                OR (start_time >= :start_time AND end_time <= :end_time)
            )
        """)
        conflicts = db.execute(
            conflict_query,
            {
                "room_id": booking.room_id,
                "booking_date": str(booking.booking_date),
                "start_time": booking.start_time,
                "end_time": booking.end_time,
            },
        ).fetchone()

        if conflicts:
            raise HTTPException(status_code=400, detail="该时间段已被预约")

        start_hour = int(booking.start_time.split(":")[0])
        end_hour = int(booking.end_time.split(":")[0])
        duration = end_hour - start_hour

        if booking.user_type == "internal":
            price = (
                float(room.member_price_per_hour)
                if room.member_price_per_hour
                else float(room.price_per_hour) * 0.8
            )
        else:
            price = float(room.price_per_hour)

        total_fee = duration * price

        booking_no = generate_booking_no()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        query = text("""
            INSERT INTO meeting_bookings 
            (booking_no, room_id, room_name, user_type, office_id, user_name, user_phone, department, 
             booking_date, start_time, end_time, duration, meeting_title, 
             attendees_count, total_fee, status, created_at, updated_at)
            VALUES 
            (:booking_no, :room_id, :room_name, :user_type, :office_id, :user_name, :user_phone, :department,
             :booking_date, :start_time, :end_time, :duration, :meeting_title,
             :attendees_count, :total_fee, :status, :created_at, :updated_at)
        """)

        result = db.execute(
            query,
            {
                "booking_no": booking_no,
                "room_id": booking.room_id,
                "room_name": room.name,
                "user_type": booking.user_type,
                "office_id": booking.office_id,
                "user_name": booking.user_name,
                "user_phone": booking.user_phone,
                "department": booking.department,
                "booking_date": str(booking.booking_date),
                "start_time": booking.start_time,
                "end_time": booking.end_time,
                "duration": duration,
                "meeting_title": booking.meeting_title,
                "attendees_count": booking.attendees_count,
                "total_fee": total_fee,
                "status": "pending",
                "created_at": now,
                "updated_at": now,
            },
        )
        db.commit()

        booking_id = result.lastrowid

        return {
            "id": booking_id,
            "booking_no": booking_no,
            "room_id": booking.room_id,
            "room_name": room.name,
            "user_type": booking.user_type,
            "office_id": booking.office_id,
            "user_name": booking.user_name,
            "user_phone": booking.user_phone,
            "department": booking.department,
            "booking_date": booking.booking_date,
            "start_time": booking.start_time,
            "end_time": booking.end_time,
            "duration": duration,
            "meeting_title": booking.meeting_title,
            "attendees_count": booking.attendees_count,
            "total_fee": total_fee,
            "status": "pending",
            "created_at": datetime.now(),
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"创建预约失败: {str(e)}")


@router.put("/bookings/{booking_id}/confirm")
def confirm_booking(booking_id: int, db: Session = Depends(get_db)):
    try:
        from sqlalchemy import text

        existing = db.execute(
            text("SELECT id, status FROM meeting_bookings WHERE id = :booking_id"),
            {"booking_id": booking_id},
        ).fetchone()
        if not existing:
            raise HTTPException(status_code=404, detail="预约不存在")

        if existing.status not in ["pending"]:
            raise HTTPException(
                status_code=400, detail=f"当前状态为 {existing.status}，无法确认"
            )

        db.execute(
            text("""
            UPDATE meeting_bookings 
            SET status = 'confirmed', updated_at = :updated_at
            WHERE id = :booking_id
        """),
            {
                "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "booking_id": booking_id,
            },
        )
        db.commit()

        return {"success": True, "message": "预约已确认"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"确认预约失败: {str(e)}")


@router.put("/bookings/{booking_id}/cancel")
def cancel_booking(
    booking_id: int, reason: str = Query(None), db: Session = Depends(get_db)
):
    try:
        from sqlalchemy import text

        existing = db.execute(
            text("SELECT id, status FROM meeting_bookings WHERE id = :booking_id"),
            {"booking_id": booking_id},
        ).fetchone()
        if not existing:
            raise HTTPException(status_code=404, detail="预约不存在")

        if existing.status in ["cancelled", "completed"]:
            raise HTTPException(
                status_code=400, detail=f"当前状态为 {existing.status}，无法取消"
            )

        db.execute(
            text("""
            UPDATE meeting_bookings 
            SET status = 'cancelled', 
                cancel_reason = :cancel_reason,
                updated_at = :updated_at
            WHERE id = :booking_id
        """),
            {
                "cancel_reason": reason or "",
                "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "booking_id": booking_id,
            },
        )
        db.commit()

        return {"success": True, "message": "预约已取消"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"取消预约失败: {str(e)}")


@router.get("/offices")
def get_offices():
    """
    获取办公室列表（供内部用户选择）
    从水站管理系统的office表获取数据
    """
    try:
        from sqlalchemy import create_engine, text
        from sqlalchemy.orm import sessionmaker

        # 连接到水站管理数据库（office表所在）
        db_path = os.path.join(os.path.dirname(__file__), "../waterms.db")
        db_path = os.path.abspath(db_path)

        # 检查数据库文件是否存在
        if not os.path.exists(db_path):
            raise HTTPException(
                status_code=500, detail=f"水站管理数据库不存在: {db_path}"
            )

        engine = create_engine(f"sqlite:///{db_path}")
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()

        try:
            # 注意：表名是 office 而不是 offices
            query = text("""
                SELECT id, name, room_number, leader_name 
                FROM office 
                WHERE is_active = 1 
                ORDER BY name
            """)

            result = db.execute(query)
            offices = []

            for row in result:
                offices.append(
                    {
                        "id": row.id,
                        "name": row.name,
                        "room_number": row.room_number,
                        "leader_name": row.leader_name,
                        "display_name": f"{row.name} ({row.room_number})",
                    }
                )

            return offices
        finally:
            db.close()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取办公室列表失败: {str(e)}")


@router.get("/health")
def meeting_health_check():
    return {
        "status": "ok",
        "module": "meeting-service",
        "timestamp": datetime.now().isoformat(),
        "features": [
            "/api/meeting/rooms - 会议室管理",
            "/api/meeting/offices - 办公室列表",
            "/api/meeting/bookings - 预约管理",
        ],
    }
