"""测试会议室预约删除功能"""

import pytest
from fastapi.testclient import TestClient
from apps.meeting.backend.api.meeting import router
from fastapi import FastAPI
from config.database import get_db
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.base import Base
from models.meeting import MeetingRoom
from models.booking import MeetingBooking, BookingStatus
import random

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_meeting_delete.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app = FastAPI()
app.include_router(router)
app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


@pytest.fixture
def db_session():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def test_room(db_session):
    room = MeetingRoom(
        name="测试会议室", location="测试楼1层", capacity=10, price_per_hour=100.0
    )
    db_session.add(room)
    db_session.commit()
    db_session.refresh(room)
    return room


@pytest.fixture
def test_booking(db_session, test_room):
    from datetime import date

    booking_no = f"MB{date.today().strftime('%Y%m%d')}{random.randint(10000, 99999)}"
    booking = MeetingBooking(
        booking_no=booking_no,
        room_id=test_room.id,
        room_name=test_room.name,
        user_name="测试用户",
        booking_date=date.today(),
        start_time="09:00",
        end_time="11:00",
        status=BookingStatus.pending.value,
    )
    db_session.add(booking)
    db_session.commit()
    db_session.refresh(booking)
    return booking


@pytest.fixture
def test_booking_deleted(db_session, test_room):
    from datetime import date

    booking_no = f"MB{date.today().strftime('%Y%m%d')}{random.randint(10000, 99999)}"
    booking = MeetingBooking(
        booking_no=booking_no,
        room_id=test_room.id,
        room_name=test_room.name,
        user_name="测试用户2",
        booking_date=date.today(),
        start_time="10:00",
        end_time="12:00",
        status=BookingStatus.pending.value,
        is_deleted=1,
    )
    db_session.add(booking)
    db_session.commit()
    db_session.refresh(booking)
    return booking


def test_delete_booking_success(db_session, test_booking):
    """测试成功删除预约"""
    response = client.delete(
        f"/api/meeting/bookings/{test_booking.id}",
        params={"deleted_by": "管理员", "delete_reason": "测试删除"},
    )

    assert response.status_code == 200
    assert response.json()["message"] == "预约记录已删除"

    db_session.refresh(test_booking)
    assert test_booking.is_deleted == 1
    assert test_booking.deleted_by == "管理员"


def test_delete_booking_not_found():
    """测试删除不存在的预约"""
    response = client.delete("/api/meeting/bookings/99999")

    assert response.status_code == 404
    assert response.json()["detail"] == "预约不存在"


def test_delete_booking_already_deleted(test_booking_deleted):
    """测试删除已删除的预约"""
    response = client.delete(f"/api/meeting/bookings/{test_booking_deleted.id}")

    assert response.status_code == 400
    assert response.json()["detail"] == "该预约已被删除"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
