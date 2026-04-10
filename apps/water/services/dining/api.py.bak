"""
VIP餐厅服务 API Routes
支持包间管理、套餐管理、预约管理

Author: 首席架构师
Date: 2026-04-01
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from datetime import datetime, date, timedelta
from typing import List, Optional
from pydantic import BaseModel, ConfigDict
import json
import random
import string

# 导入数据库依赖
try:
    from main import get_db
except ImportError:
    # 独立运行时的备用导入
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    engine = create_engine(
        "sqlite:///./waterms.db", connect_args={"check_same_thread": False}
    )
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    def get_db():
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()


router = APIRouter(prefix="/api/dining", tags=["dining"])


# ==================== Pydantic Schemas ====================


class DiningRoomBase(BaseModel):
    name: str
    description: Optional[str] = None
    min_capacity: int = 2
    max_capacity: int = 20
    room_price: float
    service_charge_rate: float = 10.0
    facilities: Optional[str] = None
    images: Optional[str] = None
    status: str = "available"
    sort_order: int = 0


class DiningRoomCreate(DiningRoomBase):
    pass


class DiningRoomResponse(DiningRoomBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DiningPackageBase(BaseModel):
    name: str
    description: Optional[str] = None
    category: str = "standard"
    price_per_person: float
    min_people: int = 2
    max_people: int = 20
    menu_items: Optional[str] = None
    includes: Optional[str] = None
    dining_duration: int = 2
    status: str = "active"
    sort_order: int = 0


class DiningPackageCreate(DiningPackageBase):
    pass


class DiningPackageResponse(DiningPackageBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DiningBookingBase(BaseModel):
    room_id: int
    package_id: Optional[int] = None
    booking_date: date
    start_time: str
    duration: int = 2
    people_count: int
    contact_person: str
    contact_phone: str
    company_name: Optional[str] = None
    purpose: Optional[str] = None
    special_requirements: Optional[str] = None
    office_id: Optional[int] = None


class DiningBookingCreate(DiningBookingBase):
    pass


class DiningBookingResponse(DiningBookingBase):
    id: int
    booking_no: str
    room_name: Optional[str] = None
    package_name: Optional[str] = None
    end_time: Optional[str] = None
    room_fee: Optional[float] = None
    package_fee: Optional[float] = None
    service_charge: Optional[float] = None
    total_fee: Optional[float] = None
    status: str = "pending"
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==================== 包间管理 API ====================


@router.get("/rooms", response_model=List[DiningRoomResponse])
def get_dining_rooms(
    status: Optional[str] = Query(
        None, description="筛选状态: available/occupied/maintenance"
    ),
    db: Session = Depends(get_db),
):
    """获取包间列表"""
    try:
        from models_unified import Base
        from sqlalchemy import Table, MetaData

        # 动态获取表
        metadata = MetaData()
        metadata.reflect(bind=db.get_bind())
        dining_rooms_table = metadata.tables["dining_rooms"]

        query = db.query(dining_rooms_table)

        if status:
            query = query.filter(dining_rooms_table.c.status == status)

        rooms = query.order_by(dining_rooms_table.c.sort_order).all()

        # 转换为字典列表
        result = []
        for room in rooms:
            result.append(
                {
                    "id": room.id,
                    "name": room.name,
                    "description": room.description,
                    "min_capacity": room.min_capacity,
                    "max_capacity": room.max_capacity,
                    "room_price": float(room.room_price) if room.room_price else 0.0,
                    "service_charge_rate": float(room.service_charge_rate)
                    if room.service_charge_rate
                    else 10.0,
                    "facilities": room.facilities,
                    "images": room.images,
                    "status": room.status,
                    "sort_order": room.sort_order,
                    "created_at": room.created_at or datetime.now(),
                    "updated_at": room.updated_at or datetime.now(),
                }
            )

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取包间列表失败: {str(e)}")


@router.get("/rooms/{room_id}", response_model=DiningRoomResponse)
def get_dining_room(room_id: int, db: Session = Depends(get_db)):
    """获取包间详情"""
    try:
        from sqlalchemy import Table, MetaData

        metadata = MetaData()
        metadata.reflect(bind=db.get_bind())
        dining_rooms_table = metadata.tables["dining_rooms"]

        room = (
            db.query(dining_rooms_table)
            .filter(dining_rooms_table.c.id == room_id)
            .first()
        )

        if not room:
            raise HTTPException(status_code=404, detail="包间不存在")

        return {
            "id": room.id,
            "name": room.name,
            "description": room.description,
            "min_capacity": room.min_capacity,
            "max_capacity": room.max_capacity,
            "room_price": float(room.room_price) if room.room_price else 0.0,
            "service_charge_rate": float(room.service_charge_rate)
            if room.service_charge_rate
            else 10.0,
            "facilities": room.facilities,
            "images": room.images,
            "status": room.status,
            "sort_order": room.sort_order,
            "created_at": room.created_at or datetime.now(),
            "updated_at": room.updated_at or datetime.now(),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取包间详情失败: {str(e)}")


# ==================== 套餐管理 API ====================


@router.get("/packages", response_model=List[DiningPackageResponse])
def get_dining_packages(
    category: Optional[str] = Query(
        None, description="套餐类型: standard/business/luxury/custom"
    ),
    db: Session = Depends(get_db),
):
    """获取套餐列表"""
    try:
        from sqlalchemy import Table, MetaData

        metadata = MetaData()
        metadata.reflect(bind=db.get_bind())
        dining_packages_table = metadata.tables["dining_packages"]

        query = db.query(dining_packages_table).filter(
            dining_packages_table.c.status == "active"
        )

        if category:
            query = query.filter(dining_packages_table.c.category == category)

        packages = query.order_by(dining_packages_table.c.sort_order).all()

        result = []
        for pkg in packages:
            result.append(
                {
                    "id": pkg.id,
                    "name": pkg.name,
                    "description": pkg.description,
                    "category": pkg.category,
                    "price_per_person": float(pkg.price_per_person)
                    if pkg.price_per_person
                    else 0.0,
                    "min_people": pkg.min_people,
                    "max_people": pkg.max_people,
                    "menu_items": pkg.menu_items,
                    "includes": pkg.includes,
                    "dining_duration": pkg.dining_duration,
                    "status": pkg.status,
                    "sort_order": pkg.sort_order,
                    "created_at": pkg.created_at or datetime.now(),
                    "updated_at": pkg.updated_at or datetime.now(),
                }
            )

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取套餐列表失败: {str(e)}")


@router.get("/packages/{package_id}", response_model=DiningPackageResponse)
def get_dining_package(package_id: int, db: Session = Depends(get_db)):
    """获取套餐详情"""
    try:
        from sqlalchemy import Table, MetaData

        metadata = MetaData()
        metadata.reflect(bind=db.get_bind())
        dining_packages_table = metadata.tables["dining_packages"]

        pkg = (
            db.query(dining_packages_table)
            .filter(dining_packages_table.c.id == package_id)
            .first()
        )

        if not pkg:
            raise HTTPException(status_code=404, detail="套餐不存在")

        return {
            "id": pkg.id,
            "name": pkg.name,
            "description": pkg.description,
            "category": pkg.category,
            "price_per_person": float(pkg.price_per_person)
            if pkg.price_per_person
            else 0.0,
            "min_people": pkg.min_people,
            "max_people": pkg.max_people,
            "menu_items": pkg.menu_items,
            "includes": pkg.includes,
            "dining_duration": pkg.dining_duration,
            "status": pkg.status,
            "sort_order": pkg.sort_order,
            "created_at": pkg.created_at or datetime.now(),
            "updated_at": pkg.updated_at or datetime.now(),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取套餐详情失败: {str(e)}")


# ==================== 预约管理 API ====================


def generate_booking_no():
    """生成预约编号: DY20260401001"""
    date_str = datetime.now().strftime("%Y%m%d")
    random_str = "".join(random.choices(string.digits, k=3))
    return f"DY{date_str}{random_str}"


def check_booking_conflict(
    db,
    room_id: int,
    booking_date: date,
    start_time: str,
    duration: int,
    exclude_booking_id: int = None,
):
    """检查预约冲突"""
    from sqlalchemy import Table, MetaData

    metadata = MetaData()
    metadata.reflect(bind=db.get_bind())
    dining_bookings_table = metadata.tables["dining_bookings"]

    # 计算结束时间
    start_hour = int(start_time.split(":")[0])
    end_hour = start_hour + duration
    end_time = f"{end_hour:02d}:00"

    # 查询同一天的预约
    query = db.query(dining_bookings_table).filter(
        and_(
            dining_bookings_table.c.room_id == room_id,
            dining_bookings_table.c.booking_date == booking_date,
            dining_bookings_table.c.status.in_(["pending", "confirmed"]),
        )
    )

    if exclude_booking_id:
        query = query.filter(dining_bookings_table.c.id != exclude_booking_id)

    existing_bookings = query.all()

    # 检查时间冲突
    for booking in existing_bookings:
        existing_start = int(booking.start_time.split(":")[0])
        existing_end = (
            int(booking.end_time.split(":")[0])
            if booking.end_time
            else existing_start + booking.duration
        )

        # 检查时间段重叠
        if not (end_hour <= existing_start or start_hour >= existing_end):
            return (
                True,
                f"时间冲突: {booking.start_time}-{booking.end_time or f'{existing_end}:00'} 已被预约",
            )

    return False, ""


@router.post("/bookings", response_model=DiningBookingResponse)
def create_dining_booking(booking: DiningBookingCreate, db: Session = Depends(get_db)):
    """创建餐厅预约"""
    try:
        from sqlalchemy import Table, MetaData, insert

        metadata = MetaData()
        metadata.reflect(bind=db.get_bind())
        dining_rooms_table = metadata.tables["dining_rooms"]
        dining_packages_table = metadata.tables["dining_packages"]
        dining_bookings_table = metadata.tables["dining_bookings"]

        # 1. 验证包间
        room = (
            db.query(dining_rooms_table)
            .filter(dining_rooms_table.c.id == booking.room_id)
            .first()
        )
        if not room:
            raise HTTPException(status_code=404, detail="包间不存在")

        if room.status != "available":
            raise HTTPException(
                status_code=400, detail=f"包间当前状态为 {room.status}，不可预约"
            )

        # 2. 验证人数
        if (
            booking.people_count < room.min_capacity
            or booking.people_count > room.max_capacity
        ):
            raise HTTPException(
                status_code=400,
                detail=f"人数不符合要求，该包间容纳 {room.min_capacity}-{room.max_capacity} 人",
            )

        # 3. 验证套餐（如果选择了套餐）
        package = None
        if booking.package_id:
            package = (
                db.query(dining_packages_table)
                .filter(dining_packages_table.c.id == booking.package_id)
                .first()
            )
            if not package:
                raise HTTPException(status_code=404, detail="套餐不存在")

            if (
                booking.people_count < package.min_people
                or booking.people_count > package.max_people
            ):
                raise HTTPException(
                    status_code=400,
                    detail=f"人数不符合套餐要求，该套餐适用 {package.min_people}-{package.max_people} 人",
                )

        # 4. 检查预约冲突
        has_conflict, conflict_msg = check_booking_conflict(
            db,
            booking.room_id,
            booking.booking_date,
            booking.start_time,
            booking.duration,
        )
        if has_conflict:
            raise HTTPException(status_code=400, detail=conflict_msg)

        # 5. 计算费用
        start_hour = int(booking.start_time.split(":")[0])
        end_hour = start_hour + booking.duration
        end_time = f"{end_hour:02d}:00"

        room_fee = float(room.room_price)
        package_fee = (
            float(package.price_per_person) * booking.people_count if package else 0.0
        )
        service_charge = (
            (room_fee + package_fee) * float(room.service_charge_rate) / 100
        )
        total_fee = room_fee + package_fee + service_charge

        # 6. 创建预约
        booking_no = generate_booking_no()

        stmt = insert(dining_bookings_table).values(
            booking_no=booking_no,
            room_id=booking.room_id,
            room_name=room.name,
            package_id=booking.package_id,
            package_name=package.name if package else None,
            booking_date=booking.booking_date,
            start_time=booking.start_time,
            end_time=end_time,
            duration=booking.duration,
            people_count=booking.people_count,
            room_fee=room_fee,
            package_fee=package_fee,
            service_charge=service_charge,
            total_fee=total_fee,
            contact_person=booking.contact_person,
            contact_phone=booking.contact_phone,
            company_name=booking.company_name,
            purpose=booking.purpose,
            special_requirements=booking.special_requirements,
            office_id=booking.office_id,
            status="pending",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        result = db.execute(stmt)
        db.commit()

        booking_id = result.lastrowid

        # 7. 返回预约详情
        return {
            "id": booking_id,
            "booking_no": booking_no,
            "room_id": booking.room_id,
            "room_name": room.name,
            "package_id": booking.package_id,
            "package_name": package.name if package else None,
            "booking_date": booking.booking_date,
            "start_time": booking.start_time,
            "end_time": end_time,
            "duration": booking.duration,
            "people_count": booking.people_count,
            "room_fee": room_fee,
            "package_fee": package_fee,
            "service_charge": service_charge,
            "total_fee": total_fee,
            "contact_person": booking.contact_person,
            "contact_phone": booking.contact_phone,
            "company_name": booking.company_name,
            "purpose": booking.purpose,
            "special_requirements": booking.special_requirements,
            "office_id": booking.office_id,
            "status": "pending",
            "created_at": datetime.now(),
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"创建预约失败: {str(e)}")


@router.get("/bookings", response_model=List[DiningBookingResponse])
def get_dining_bookings(
    status: Optional[str] = Query(None),
    booking_date: Optional[date] = Query(None),
    room_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
):
    """获取预约列表"""
    try:
        from sqlalchemy import Table, MetaData

        metadata = MetaData()
        metadata.reflect(bind=db.get_bind())
        dining_bookings_table = metadata.tables["dining_bookings"]

        query = db.query(dining_bookings_table)

        if status:
            query = query.filter(dining_bookings_table.c.status == status)

        if booking_date:
            query = query.filter(dining_bookings_table.c.booking_date == booking_date)

        if room_id:
            query = query.filter(dining_bookings_table.c.room_id == room_id)

        bookings = query.order_by(
            dining_bookings_table.c.booking_date.desc(),
            dining_bookings_table.c.start_time,
        ).all()

        result = []
        for b in bookings:
            result.append(
                {
                    "id": b.id,
                    "booking_no": b.booking_no,
                    "room_id": b.room_id,
                    "room_name": b.room_name,
                    "package_id": b.package_id,
                    "package_name": b.package_name,
                    "booking_date": b.booking_date,
                    "start_time": b.start_time,
                    "end_time": b.end_time,
                    "duration": b.duration,
                    "people_count": b.people_count,
                    "room_fee": float(b.room_fee) if b.room_fee else 0.0,
                    "package_fee": float(b.package_fee) if b.package_fee else 0.0,
                    "service_charge": float(b.service_charge)
                    if b.service_charge
                    else 0.0,
                    "total_fee": float(b.total_fee) if b.total_fee else 0.0,
                    "contact_person": b.contact_person,
                    "contact_phone": b.contact_phone,
                    "company_name": b.company_name,
                    "purpose": b.purpose,
                    "special_requirements": b.special_requirements,
                    "office_id": b.office_id,
                    "status": b.status,
                    "created_at": b.created_at or datetime.now(),
                }
            )

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取预约列表失败: {str(e)}")


@router.get("/bookings/{booking_id}", response_model=DiningBookingResponse)
def get_dining_booking(booking_id: int, db: Session = Depends(get_db)):
    """获取预约详情"""
    try:
        from sqlalchemy import Table, MetaData

        metadata = MetaData()
        metadata.reflect(bind=db.get_bind())
        dining_bookings_table = metadata.tables["dining_bookings"]

        b = (
            db.query(dining_bookings_table)
            .filter(dining_bookings_table.c.id == booking_id)
            .first()
        )

        if not b:
            raise HTTPException(status_code=404, detail="预约不存在")

        return {
            "id": b.id,
            "booking_no": b.booking_no,
            "room_id": b.room_id,
            "room_name": b.room_name,
            "package_id": b.package_id,
            "package_name": b.package_name,
            "booking_date": b.booking_date,
            "start_time": b.start_time,
            "end_time": b.end_time,
            "duration": b.duration,
            "people_count": b.people_count,
            "room_fee": float(b.room_fee) if b.room_fee else 0.0,
            "package_fee": float(b.package_fee) if b.package_fee else 0.0,
            "service_charge": float(b.service_charge) if b.service_charge else 0.0,
            "total_fee": float(b.total_fee) if b.total_fee else 0.0,
            "contact_person": b.contact_person,
            "contact_phone": b.contact_phone,
            "company_name": b.company_name,
            "purpose": b.purpose,
            "special_requirements": b.special_requirements,
            "office_id": b.office_id,
            "status": b.status,
            "created_at": b.created_at or datetime.now(),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取预约详情失败: {str(e)}")


@router.put("/bookings/{booking_id}/confirm")
def confirm_dining_booking(booking_id: int, db: Session = Depends(get_db)):
    """确认预约"""
    try:
        from sqlalchemy import Table, MetaData, update

        metadata = MetaData()
        metadata.reflect(bind=db.get_bind())
        dining_bookings_table = metadata.tables["dining_bookings"]

        b = (
            db.query(dining_bookings_table)
            .filter(dining_bookings_table.c.id == booking_id)
            .first()
        )

        if not b:
            raise HTTPException(status_code=404, detail="预约不存在")

        if b.status != "pending":
            raise HTTPException(
                status_code=400, detail=f"当前状态为 {b.status}，无法确认"
            )

        stmt = (
            update(dining_bookings_table)
            .where(dining_bookings_table.c.id == booking_id)
            .values(
                status="confirmed",
                confirmed_at=datetime.now(),
                updated_at=datetime.now(),
            )
        )

        db.execute(stmt)
        db.commit()

        return {"success": True, "message": "预约已确认"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"确认预约失败: {str(e)}")


@router.put("/bookings/{booking_id}/cancel")
def cancel_dining_booking(
    booking_id: int, reason: str = Query(None), db: Session = Depends(get_db)
):
    """取消预约"""
    try:
        from sqlalchemy import Table, MetaData, update

        metadata = MetaData()
        metadata.reflect(bind=db.get_bind())
        dining_bookings_table = metadata.tables["dining_bookings"]

        b = (
            db.query(dining_bookings_table)
            .filter(dining_bookings_table.c.id == booking_id)
            .first()
        )

        if not b:
            raise HTTPException(status_code=404, detail="预约不存在")

        if b.status in ["cancelled", "completed"]:
            raise HTTPException(
                status_code=400, detail=f"当前状态为 {b.status}，无法取消"
            )

        stmt = (
            update(dining_bookings_table)
            .where(dining_bookings_table.c.id == booking_id)
            .values(
                status="cancelled",
                cancel_reason=reason,
                cancelled_at=datetime.now(),
                updated_at=datetime.now(),
            )
        )

        db.execute(stmt)
        db.commit()

        return {"success": True, "message": "预约已取消"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"取消预约失败: {str(e)}")


@router.get("/availability")
def check_availability(room_id: int, booking_date: date, db: Session = Depends(get_db)):
    """检查包间可用时间"""
    try:
        from sqlalchemy import Table, MetaData

        metadata = MetaData()
        metadata.reflect(bind=db.get_bind())
        dining_bookings_table = metadata.tables["dining_bookings"]

        # 查询该包间当天的所有预约
        bookings = (
            db.query(dining_bookings_table)
            .filter(
                and_(
                    dining_bookings_table.c.room_id == room_id,
                    dining_bookings_table.c.booking_date == booking_date,
                    dining_bookings_table.c.status.in_(["pending", "confirmed"]),
                )
            )
            .all()
        )

        # 定义可用时段
        all_slots = [
            {"start": "11:00", "end": "13:00", "label": "午餐时段(11:00-13:00)"},
            {"start": "17:00", "end": "19:00", "label": "晚餐时段(17:00-19:00)"},
            {"start": "19:00", "end": "21:00", "label": "晚宴时段(19:00-21:00)"},
        ]

        # 检查每个时段是否可用
        available_slots = []
        for slot in all_slots:
            is_available = True
            for b in bookings:
                existing_start = int(b.start_time.split(":")[0])
                existing_end = (
                    int(b.end_time.split(":")[0])
                    if b.end_time
                    else existing_start + b.duration
                )
                slot_start = int(slot["start"].split(":")[0])
                slot_end = int(slot["end"].split(":")[0])

                # 检查时间重叠
                if not (slot_end <= existing_start or slot_start >= existing_end):
                    is_available = False
                    break

            available_slots.append({**slot, "available": is_available})

        return {
            "room_id": room_id,
            "booking_date": booking_date,
            "available_slots": available_slots,
            "booked_count": len(bookings),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询可用时间失败: {str(e)}")


@router.get("/health")
def dining_health_check():
    """健康检查"""
    return {
        "status": "ok",
        "module": "dining-service",
        "timestamp": datetime.now().isoformat(),
        "features": [
            "/api/dining/rooms - 包间管理",
            "/api/dining/packages - 套餐管理",
            "/api/dining/bookings - 预约管理",
            "/api/dining/availability - 可用性检查",
        ],
    }


# ==================== 注册路由说明 ====================
"""
在 main.py 中引入此 router（仅增加 1 行）：

from api_dining import router as dining_router
app.include_router(dining_router)
"""
