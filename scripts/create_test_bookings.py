"""
创建测试预约数据
"""

import sys

sys.path.insert(0, "/Users/sgl/PycharmProjects/AIchanyejiqun")

from datetime import date, timedelta
from sqlalchemy.orm import Session
from config.database import SessionLocal
from shared.models.space.space_booking import SpaceBooking
from shared.models.space.space_resource import SpaceResource
from shared.models.space.space_type import SpaceType
from models.user import User


def create_test_bookings():
    db: Session = SessionLocal()

    try:
        # 获取测试用户
        user = db.query(User).filter(User.id == 1).first()
        if not user:
            print("找不到测试用户，创建测试用户...")
            user = User(
                id=1,
                username="test_user",
                name="测试用户",
                email="test@example.com",
                role="user",
                is_active=True,
            )
            db.add(user)
            db.commit()

        # 获取资源和类型
        resources = (
            db.query(SpaceResource).filter(SpaceResource.is_active == True).all()
        )
        types = db.query(SpaceType).filter(SpaceType.is_active == True).all()

        if not resources:
            print("没有找到资源，请先运行 init_space_types.py")
            return

        print(f"找到 {len(resources)} 个资源")
        print(f"找到 {len(types)} 个类型")

        # 创建测试预约数据
        test_bookings = [
            # 会议室预约 - 不同状态
            {
                "resource_id": 1,
                "type_id": 1,
                "type_code": "meeting_room",
                "user_id": user.id,
                "user_name": user.name,
                "title": "产品团队周会",
                "booking_date": date.today() + timedelta(days=1),
                "start_time": "09:00",
                "end_time": "11:00",
                "duration": 2,
                "attendees_count": 10,
                "base_fee": 160,
                "addon_fee": 0,
                "actual_fee": 160,
                "status": "pending_approval",
                "payment_status": "unpaid",
                "special_requests": "需要投影仪和茶水服务",
            },
            {
                "resource_id": 2,
                "type_id": 1,
                "type_code": "meeting_room",
                "user_id": user.id,
                "user_name": user.name,
                "title": "客户洽谈会",
                "booking_date": date.today() + timedelta(days=2),
                "start_time": "14:00",
                "end_time": "16:00",
                "duration": 2,
                "attendees_count": 6,
                "base_fee": 160,
                "addon_fee": 0,
                "actual_fee": 160,
                "status": "approved",
                "payment_status": "unpaid",
                "special_requests": "",
            },
            {
                "resource_id": 3,
                "type_id": 1,
                "type_code": "meeting_room",
                "user_id": user.id,
                "user_name": user.name,
                "title": "VIP客户接待",
                "booking_date": date.today() - timedelta(days=1),
                "start_time": "10:00",
                "end_time": "12:00",
                "duration": 2,
                "attendees_count": 8,
                "base_fee": 240,
                "addon_fee": 50,
                "actual_fee": 290,
                "status": "completed",
                "payment_status": "fully_paid",
                "special_requests": "需要高端茶歇服务",
            },
            # 会场预约
            {
                "resource_id": 4,
                "type_id": 2,
                "type_code": "auditorium",
                "user_id": user.id,
                "user_name": user.name,
                "title": "季度总结大会",
                "booking_date": date.today() + timedelta(days=5),
                "start_time": "09:00",
                "end_time": "17:00",
                "duration": 8,
                "attendees_count": 100,
                "base_fee": 4000,
                "addon_fee": 500,
                "actual_fee": 4500,
                "status": "pending_approval",
                "payment_status": "deposit_paid",
                "special_requests": "需要舞台设备和音响系统",
            },
            {
                "resource_id": 5,
                "type_id": 2,
                "type_code": "auditorium",
                "user_id": user.id,
                "user_name": user.name,
                "title": "技术分享会",
                "booking_date": date.today() - timedelta(days=3),
                "start_time": "14:00",
                "end_time": "18:00",
                "duration": 4,
                "attendees_count": 50,
                "base_fee": 2000,
                "addon_fee": 200,
                "actual_fee": 2200,
                "status": "completed",
                "payment_status": "fully_paid",
                "special_requests": "",
            },
            # 大屏预约
            {
                "resource_id": 6,
                "type_id": 3,
                "type_code": "lobby_screen",
                "user_id": user.id,
                "user_name": user.name,
                "title": "公司宣传视频播放",
                "booking_date": date.today() + timedelta(days=1),
                "start_time": "08:00",
                "end_time": "18:00",
                "duration": 10,
                "attendees_count": 0,
                "base_fee": 1000,
                "addon_fee": 0,
                "actual_fee": 1000,
                "status": "approved",
                "payment_status": "unpaid",
                "special_requests": "",
            },
            # 展位预约
            {
                "resource_id": 10,
                "type_id": 4,
                "type_code": "lobby_booth",
                "user_id": user.id,
                "user_name": user.name,
                "title": "新产品展示",
                "booking_date": date.today() + timedelta(days=3),
                "start_time": "09:00",
                "end_time": "18:00",
                "duration": 9,
                "attendees_count": 0,
                "base_fee": 450,
                "addon_fee": 0,
                "actual_fee": 450,
                "status": "pending_approval",
                "payment_status": "unpaid",
                "special_requests": "需要3x3米展示空间",
            },
            # VIP餐厅预约
            {
                "resource_id": 16,
                "type_id": 5,
                "type_code": "vip_dining",
                "user_id": user.id,
                "user_name": user.name,
                "title": "高管午餐会",
                "booking_date": date.today() + timedelta(days=2),
                "start_time": "12:00",
                "end_time": "14:00",
                "duration": 2,
                "attendees_count": 12,
                "base_fee": 600,
                "addon_fee": 100,
                "actual_fee": 700,
                "status": "approved",
                "payment_status": "deposit_paid",
                "special_requests": "需要VIP套餐",
            },
            # 历史预约（已完成）
            {
                "resource_id": 1,
                "type_id": 1,
                "type_code": "meeting_room",
                "user_id": user.id,
                "user_name": user.name,
                "title": "项目复盘会",
                "booking_date": date.today() - timedelta(days=7),
                "start_time": "15:00",
                "end_time": "17:00",
                "duration": 2,
                "attendees_count": 8,
                "base_fee": 160,
                "addon_fee": 0,
                "actual_fee": 160,
                "status": "completed",
                "payment_status": "fully_paid",
                "special_requests": "",
            },
            {
                "resource_id": 1,
                "type_id": 1,
                "type_code": "meeting_room",
                "user_id": user.id,
                "user_name": user.name,
                "title": "周例会",
                "booking_date": date.today() - timedelta(days=14),
                "start_time": "09:00",
                "end_time": "11:00",
                "duration": 2,
                "attendees_count": 10,
                "base_fee": 160,
                "addon_fee": 0,
                "actual_fee": 160,
                "status": "completed",
                "payment_status": "fully_paid",
                "special_requests": "",
            },
            # 已取消预约
            {
                "resource_id": 2,
                "type_id": 1,
                "type_code": "meeting_room",
                "user_id": user.id,
                "user_name": user.name,
                "title": "临时会议（已取消）",
                "booking_date": date.today() - timedelta(days=5),
                "start_time": "10:00",
                "end_time": "12:00",
                "duration": 2,
                "attendees_count": 5,
                "base_fee": 160,
                "addon_fee": 0,
                "actual_fee": 0,
                "status": "cancelled",
                "payment_status": "refunded",
                "special_requests": "",
            },
            # 已拒绝预约
            {
                "resource_id": 4,
                "type_id": 2,
                "type_code": "auditorium",
                "user_id": user.id,
                "user_name": user.name,
                "title": "私人聚会（已拒绝）",
                "booking_date": date.today() - timedelta(days=10),
                "start_time": "18:00",
                "end_time": "22:00",
                "duration": 4,
                "attendees_count": 200,
                "base_fee": 2000,
                "addon_fee": 0,
                "actual_fee": 0,
                "status": "rejected",
                "payment_status": "unpaid",
                "special_requests": "私人聚会活动",
            },
        ]

        # 生成预约编号并插入数据
        booking_no_counter = 1
        for booking_data in test_bookings:
            booking_data["booking_no"] = (
                f"BK{date.today().strftime('%Y%m%d')}{booking_no_counter:04d}"
            )
            booking_no_counter += 1

            # 获取资源名称
            resource = (
                db.query(SpaceResource)
                .filter(SpaceResource.id == booking_data["resource_id"])
                .first()
            )
            if resource:
                booking_data["resource_name"] = resource.name

            booking = SpaceBooking(**booking_data)
            db.add(booking)

        db.commit()

        # 验证插入结果
        total_bookings = (
            db.query(SpaceBooking).filter(SpaceBooking.is_deleted == 0).count()
        )
        print(f"\n✅ 成功创建 {len(test_bookings)} 条测试预约数据")
        print(f"📊 数据库中共有 {total_bookings} 条预约记录")

        # 统计各状态数量
        statuses = [
            "pending_approval",
            "approved",
            "completed",
            "cancelled",
            "rejected",
        ]
        print("\n预约状态分布:")
        for status in statuses:
            count = (
                db.query(SpaceBooking)
                .filter(SpaceBooking.status == status, SpaceBooking.is_deleted == 0)
                .count()
            )
            print(f"  - {status}: {count}")

        # 统计总收入
        from sqlalchemy import func

        total_revenue = (
            db.query(func.sum(SpaceBooking.actual_fee))
            .filter(
                SpaceBooking.status.in_(["completed", "settled"]),
                SpaceBooking.is_deleted == 0,
            )
            .scalar()
            or 0
        )
        print(f"\n💰 已完成预约总收入: ¥{total_revenue:.2f}")

    except Exception as e:
        print(f"❌ 创建测试数据失败: {e}")
        import traceback

        traceback.print_exc()
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    create_test_bookings()
