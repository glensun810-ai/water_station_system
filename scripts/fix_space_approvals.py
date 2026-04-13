"""
修复空间审批数据一致性
解决：
1. pending_approval状态的预约没有对应的审批记录
2. 不需要审批的空间类型预约状态错误
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import random

from models.base import Base
from shared.models.space.space_booking import SpaceBooking
from shared.models.space.space_approval import SpaceApproval
from shared.models.space.space_type import SpaceType

engine = create_engine("sqlite:///./data/app.db", echo=False)
SessionLocal = sessionmaker(bind=engine)


def fix_approval_data():
    db = SessionLocal()

    try:
        print("=" * 60)
        print("空间审批数据修复脚本")
        print("=" * 60)

        # 1. 获取所有空间类型及其审批要求
        space_types = db.query(SpaceType).all()
        type_approval_map = {t.type_code: t.requires_approval for t in space_types}
        print("\n空间类型审批要求:")
        for t in space_types:
            print(
                f"  {t.type_name} ({t.type_code}): requires_approval={t.requires_approval}"
            )

        # 2. 查找所有pending_approval状态的预约
        pending_bookings = (
            db.query(SpaceBooking)
            .filter(
                SpaceBooking.status == "pending_approval", SpaceBooking.is_deleted == 0
            )
            .all()
        )

        print(f"\n发现 {len(pending_bookings)} 条 pending_approval 状态的预约:")

        fixed_count = 0
        approval_created_count = 0
        status_fixed_count = 0

        for booking in pending_bookings:
            print(f"\n预约 #{booking.id}: {booking.booking_no}")
            print(f"  标题: {booking.title}")
            print(f"  类型: {booking.type_code}")
            print(f"  approval_id: {booking.approval_id}")

            requires_approval = type_approval_map.get(booking.type_code, False)

            if not requires_approval:
                # 不需要审批的空间类型，状态应该是confirmed
                print(f"  >>> 该空间类型不需要审批，修复状态为 confirmed")
                booking.status = "confirmed"
                booking.confirmed_at = datetime.now()
                booking.confirmed_by = "system_fix"
                status_fixed_count += 1
            else:
                # 需要审批的空间类型，检查是否有审批记录
                existing_approval = (
                    db.query(SpaceApproval)
                    .filter(SpaceApproval.booking_id == booking.id)
                    .first()
                )

                if not existing_approval:
                    # 创建审批记录
                    approval_no = f"SA{datetime.now().strftime('%Y%m%d%H%M%S')}{random.randint(1000, 9999)}"

                    approval = SpaceApproval(
                        approval_no=approval_no,
                        booking_id=booking.id,
                        booking_no=booking.booking_no,
                        approval_type="booking_approval",
                        approval_stage="initial",
                        approval_content=f"空间预约审批：{booking.title}",
                        status="pending",
                        submitted_at=datetime.now()
                        if not booking.created_at
                        else booking.created_at,
                    )

                    db.add(approval)
                    db.flush()
                    booking.approval_id = approval.id

                    print(f"  >>> 创建审批记录: {approval_no}")
                    approval_created_count += 1
                else:
                    print(f"  >>> 已有审批记录: {existing_approval.approval_no}")

            fixed_count += 1

        db.commit()

        print("\n" + "=" * 60)
        print("修复完成!")
        print(f"  处理预约数: {fixed_count}")
        print(f"  状态修正数 (不需要审批但pending_approval): {status_fixed_count}")
        print(f"  创建审批记录数: {approval_created_count}")
        print("=" * 60)

        # 3. 验证修复结果
        print("\n验证修复结果:")

        # 检查审批记录
        approvals = db.query(SpaceApproval).all()
        print(f"  审批记录总数: {len(approvals)}")
        for a in approvals:
            print(f"    {a.approval_no} - status={a.status}")

        # 检查预约状态
        pending_after = (
            db.query(SpaceBooking)
            .filter(SpaceBooking.status == "pending_approval")
            .count()
        )
        print(f"  pending_approval 预约数(修复后): {pending_after}")

        # 检查confirmed状态
        confirmed = (
            db.query(SpaceBooking).filter(SpaceBooking.status == "confirmed").count()
        )
        print(f"  confirmed 预约数: {confirmed}")

    except Exception as e:
        print(f"修复失败: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    fix_approval_data()
