"""
修复审批数据同步问题
解决Dashboard和Approvals页面数据不一致的问题
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import random

from shared.models.space.space_booking import SpaceBooking
from shared.models.space.space_approval import SpaceApproval
from shared.models.space.space_type import SpaceType

engine = create_engine("sqlite:///./data/app.db", echo=False)
SessionLocal = sessionmaker(bind=engine)


def fix_approvals_sync():
    """修复审批数据同步"""

    db = SessionLocal()

    try:
        print("=" * 60)
        print("空间预约审批数据同步修复")
        print("=" * 60)

        # 1. 检查需要审批的空间类型
        types_requiring_approval = (
            db.query(SpaceType).filter(SpaceType.requires_approval == True).all()
        )

        print(f"\n需要审批的空间类型:")
        for t in types_requiring_approval:
            print(f"  - {t.type_name} ({t.type_code})")

        type_codes_requiring_approval = [t.type_code for t in types_requiring_approval]

        # 2. 检查pending_approval状态的预约
        pending_bookings = (
            db.query(SpaceBooking)
            .filter(
                SpaceBooking.status == "pending_approval", SpaceBooking.is_deleted == 0
            )
            .all()
        )

        print(f"\n发现 {len(pending_bookings)} 条pending_approval状态的预约")

        # 3. 为需要审批的预约创建审批记录，修复不需要审批的预约状态
        created_count = 0
        fixed_status_count = 0

        for booking in pending_bookings:
            # 检查是否已有审批记录
            existing_approval = (
                db.query(SpaceApproval)
                .filter(SpaceApproval.booking_id == booking.id)
                .first()
            )

            if booking.type_code in type_codes_requiring_approval:
                # 需要审批的类型，但缺少审批记录
                if not existing_approval:
                    approval_no = f"SA{datetime.now().strftime('%Y%m%d%H%M%S')}{random.randint(1000, 9999)}"

                    approval = SpaceApproval(
                        approval_no=approval_no,
                        booking_id=booking.id,
                        booking_no=booking.booking_no,
                        approval_type="booking_approval",
                        approval_stage="initial",
                        approval_content=f"空间预约审批：{booking.title}",
                        status="pending",
                        submitted_at=datetime.now(),
                    )

                    db.add(approval)
                    db.flush()
                    booking.approval_id = approval.id
                    created_count += 1
                    print(f"  ✓ 创建审批记录: {booking.booking_no} - {booking.title}")
                else:
                    print(f"  - 已有审批记录: {booking.booking_no}")
            else:
                # 不需要审批的类型（如会议室），状态应该是confirmed
                booking.status = "confirmed"
                booking.confirmed_at = datetime.now()
                booking.confirmed_by = "system_auto"
                fixed_status_count += 1
                print(
                    f"  ✓ 修复状态(无需审批): {booking.booking_no} - {booking.title} -> confirmed"
                )

        db.commit()

        print(f"\n修复结果:")
        print(f"  - 创建审批记录: {created_count} 条")
        print(f"  - 修复预约状态: {fixed_status_count} 条")

        # 4. 验证修复结果
        print("\n验证修复结果:")

        final_pending_approvals = (
            db.query(SpaceBooking)
            .filter(SpaceBooking.status == "pending_approval")
            .count()
        )

        final_pending_approvals_in_table = (
            db.query(SpaceApproval).filter(SpaceApproval.status == "pending").count()
        )

        print(f"  - pending_approval预约: {final_pending_approvals} 条")
        print(f"  - pending审批记录: {final_pending_approvals_in_table} 条")

        if final_pending_approvals == final_pending_approvals_in_table:
            print("\n✅ 数据已同步!")
        else:
            print(
                f"\n⚠️ 数据仍有差异: 预约{final_pending_approvals} vs 审批{final_pending_approvals_in_table}"
            )

        # 5. 显示所有审批记录
        print("\n当前审批记录:")
        approvals = db.query(SpaceApproval).all()
        for a in approvals:
            print(f"  {a.approval_no} | booking: {a.booking_no} | status: {a.status}")

    except Exception as e:
        print(f"\n✗ 修复失败: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    fix_approvals_sync()
