"""
添加测试数据
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime

from models.base import Base
from models import User, Office, Product, OfficePickup, MeetingRoom, MeetingBooking

engine = create_engine("sqlite:///./data/app.db")
Session = sessionmaker(bind=engine)
session = Session()

# 创建测试用户
user1 = User(
    username="admin",
    name="管理员",
    role="admin",
    department="管理部",
    is_active=1,
)
user1.password_hash = "hashed_password_123"

user2 = User(
    username="user1",
    name="张三",
    role="user",
    department="办公室A",
    is_active=1,
)
user2.password_hash = "hashed_password_456"

session.add(user1)
session.add(user2)

# 创建办公室
office1 = Office(
    name="办公室A",
    room_number="101",
    leader_name="李主任",
    is_active=1,
)
office2 = Office(
    name="办公室B",
    room_number="102",
    leader_name="王主任",
    is_active=1,
)

session.add(office1)
session.add(office2)

# 创建产品
product1 = Product(
    name="矿泉水",
    specification="18L",
    unit="桶",
    price=25.0,
    stock=100,
    promo_threshold=10,
    promo_gift=1,
    is_active=1,
)
product2 = Product(
    name="纯净水",
    specification="5L",
    unit="桶",
    price=8.0,
    stock=50,
    is_active=1,
)

session.add(product1)
session.add(product2)

# 创建领水记录
pickup1 = OfficePickup(
    office_id=1,
    office_name="办公室A",
    product_id=1,
    product_name="矿泉水",
    product_specification="18L",
    quantity=2,
    pickup_person="张三",
    pickup_person_id=2,
    pickup_time=datetime.now(),
    unit_price=25.0,
    total_amount=50.0,
    settlement_status="pending",
    is_deleted=0,
)

pickup2 = OfficePickup(
    office_id=2,
    office_name="办公室B",
    product_id=2,
    product_name="纯净水",
    product_specification="5L",
    quantity=5,
    pickup_person="李主任",
    pickup_person_id=1,
    pickup_time=datetime.now(),
    unit_price=8.0,
    total_amount=40.0,
    settlement_status="settled",
    is_deleted=0,
)

session.add(pickup1)
session.add(pickup2)

# 创建会议室
room1 = MeetingRoom(
    name="会议室1",
    location="一楼",
    capacity=20,
    price_per_hour=100.0,
    member_price_per_hour=80.0,
    is_active=True,
)

room2 = MeetingRoom(
    name="会议室2",
    location="二楼",
    capacity=10,
    price_per_hour=50.0,
    member_price_per_hour=40.0,
    is_active=True,
)

session.add(room1)
session.add(room2)

# 创建预约记录
from datetime import date

booking1 = MeetingBooking(
    booking_no="MB20260410001",
    room_id=1,
    room_name="会议室1",
    user_id=2,
    user_type="internal",
    office_id=1,
    user_name="张三",
    department="办公室A",
    booking_date=date.today(),
    start_time="09:00",
    end_time="11:00",
    duration=2.0,
    meeting_title="项目讨论会",
    attendees_count=5,
    status="confirmed",
    total_fee=200.0,
    actual_fee=200.0,
    payment_status="paid",
    is_deleted=0,
)

session.add(booking1)

session.commit()
print("测试数据添加完成")
print(f"用户: {session.query(User).count()}")
print(f"办公室: {session.query(Office).count()}")
print(f"产品: {session.query(Product).count()}")
print(f"领水记录: {session.query(OfficePickup).count()}")
print(f"会议室: {session.query(MeetingRoom).count()}")
print(f"预约记录: {session.query(MeetingBooking).count()}")
