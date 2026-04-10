"""
历史数据迁移脚本
将现有的领水记录迁移到新的结算单模型

执行时间: 2026-04-08
版本: v2.0
"""

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, date
from models.pickup import OfficePickup
from models.settlement_v2 import SettlementApplication, SettlementItem
from models.office import Office
from config.database import get_db


def generate_application_no(db: Session, office_id: int) -> str:
    """生成申请单编号"""
    count = (
        db.query(func.count(SettlementApplication.id))
        .filter(SettlementApplication.office_id == office_id)
        .scalar()
        or 0
    )

    return f"SA{datetime.now().strftime('%Y%m%d')}-{office_id:03d}-{count + 1:03d}"


def migrate_applied_pickups(db: Session):
    """迁移已申请(applied)的领水记录"""
    print("\n" + "=" * 60)
    print("迁移已申请的领水记录")
    print("=" * 60)

    applied_pickups = (
        db.query(OfficePickup)
        .filter(
            OfficePickup.settlement_status == "applied", OfficePickup.is_deleted == 0
        )
        .all()
    )

    print(f"找到 {len(applied_pickups)} 条已申请的领水记录")

    if not applied_pickups:
        print("  ⚠️  没有需要迁移的记录")
        return 0

    created_count = 0
    skipped_count = 0

    for pickup in applied_pickups:
        try:
            office = db.query(Office).filter(Office.id == pickup.office_id).first()
            if not office:
                print(f"  ⚠️  跳过记录 {pickup.id}: 办公室不存在")
                skipped_count += 1
                continue

            application_no = generate_application_no(db, pickup.office_id)

            application = SettlementApplication(
                application_no=application_no,
                office_id=pickup.office_id,
                office_name=office.name,
                office_room_number=office.room_number,
                applicant_id=pickup.pickup_person_id or 0,
                applicant_name=pickup.pickup_person or "历史数据",
                applicant_role="office_manager",
                record_count=1,
                total_amount=pickup.total_amount or 0,
                status="applied",
                applied_at=pickup.created_at or pickup.pickup_time or datetime.now(),
                note="历史数据迁移",
            )

            db.add(application)
            db.flush()

            item = SettlementItem(
                application_id=application.id,
                pickup_id=pickup.id,
                product_name=pickup.product_name,
                product_id=pickup.product_id,
                quantity=pickup.quantity,
                unit_price=pickup.unit_price,
                amount=pickup.total_amount,
                pickup_status="applied",
                pickup_time=pickup.pickup_time,
                pickup_person=pickup.pickup_person,
                pickup_person_id=pickup.pickup_person_id,
            )

            db.add(item)

            pickup.settlement_application_id = application.id

            created_count += 1
            print(f"  ✅ 迁移记录 {pickup.id} -> 申请单 {application.application_no}")

        except Exception as e:
            print(f"  ❌ 迁移记录 {pickup.id} 失败: {e}")
            skipped_count += 1
            db.rollback()
            continue

    db.commit()

    print(f"\n迁移完成:")
    print(f"  ✅ 成功: {created_count} 条")
    print(f"  ⚠️  跳过: {skipped_count} 条")

    return created_count


def migrate_settled_pickups(db: Session):
    """迁移已结算(settled)的领水记录"""
    print("\n" + "=" * 60)
    print("迁移已结算的领水记录")
    print("=" * 60)

    settled_pickups = (
        db.query(OfficePickup)
        .filter(
            OfficePickup.settlement_status == "settled", OfficePickup.is_deleted == 0
        )
        .all()
    )

    print(f"找到 {len(settled_pickups)} 条已结算的领水记录")

    if not settled_pickups:
        print("  ⚠️  没有需要迁移的记录")
        return 0

    created_count = 0
    skipped_count = 0

    for pickup in settled_pickups:
        try:
            office = db.query(Office).filter(Office.id == pickup.office_id).first()
            if not office:
                print(f"  ⚠️  跳过记录 {pickup.id}: 办公室不存在")
                skipped_count += 1
                continue

            application_no = generate_application_no(db, pickup.office_id)

            application = SettlementApplication(
                application_no=application_no,
                office_id=pickup.office_id,
                office_name=office.name,
                office_room_number=office.room_number,
                applicant_id=pickup.pickup_person_id or 0,
                applicant_name=pickup.pickup_person or "历史数据",
                applicant_role="office_manager",
                record_count=1,
                total_amount=pickup.total_amount or 0,
                status="settled",
                applied_at=pickup.created_at or pickup.pickup_time or datetime.now(),
                settled_at=pickup.created_at or pickup.pickup_time or datetime.now(),
                settled_by_name="历史数据",
                note="历史数据迁移",
            )

            db.add(application)
            db.flush()

            item = SettlementItem(
                application_id=application.id,
                pickup_id=pickup.id,
                product_name=pickup.product_name,
                product_id=pickup.product_id,
                quantity=pickup.quantity,
                unit_price=pickup.unit_price,
                amount=pickup.total_amount,
                pickup_status="settled",
                pickup_time=pickup.pickup_time,
                pickup_person=pickup.pickup_person,
                pickup_person_id=pickup.pickup_person_id,
            )

            db.add(item)

            pickup.settlement_application_id = application.id

            created_count += 1
            print(f"  ✅ 迁移记录 {pickup.id} -> 申请单 {application.application_no}")

        except Exception as e:
            print(f"  ❌ 迁移记录 {pickup.id} 失败: {e}")
            skipped_count += 1
            db.rollback()
            continue

    db.commit()

    print(f"\n迁移完成:")
    print(f"  ✅ 成功: {created_count} 条")
    print(f"  ⚠️  跳过: {skipped_count} 条")

    return created_count


def validate_migration(db: Session):
    """验证迁移结果"""
    print("\n" + "=" * 60)
    print("验证迁移结果")
    print("=" * 60)

    try:
        total_applications = (
            db.query(func.count(SettlementApplication.id)).scalar() or 0
        )
        total_items = db.query(func.count(SettlementItem.id)).scalar() or 0

        applied_count = (
            db.query(func.count(SettlementApplication.id))
            .filter(SettlementApplication.status == "applied")
            .scalar()
            or 0
        )

        settled_count = (
            db.query(func.count(SettlementApplication.id))
            .filter(SettlementApplication.status == "settled")
            .scalar()
            or 0
        )

        print(f"申请单统计:")
        print(f"  总数: {total_applications}")
        print(f"  已申请: {applied_count}")
        print(f"  已结算: {settled_count}")
        print(f"  明细总数: {total_items}")

        if total_applications == total_items:
            print(f"  ✅ 申请单数量与明细数量一致")
        else:
            print(
                f"  ❌ 申请单数量({total_applications})与明细数量({total_items})不一致"
            )
            return False

        return True

    except Exception as e:
        print(f"❌ 验证失败: {e}")
        return False


def main():
    """主函数"""
    print("=" * 60)
    print("历史数据迁移 - 结算模块v2")
    print("=" * 60)

    db = next(get_db())

    try:
        print("\n开始迁移...")

        applied_count = migrate_applied_pickups(db)
        settled_count = migrate_settled_pickups(db)

        print("\n" + "=" * 60)
        print("迁移汇总")
        print("=" * 60)
        print(f"已申请记录: {applied_count} 条")
        print(f"已结算记录: {settled_count} 条")
        print(f"总计: {applied_count + settled_count} 条")

        if not validate_migration(db):
            print("\n❌ 验证失败,请检查数据")
            return False

        print("\n✅ 迁移完成!")
        print("\n下一步:")
        print("  1. 使用新的结算申请API")
        print("  2. 实现月度结算单生成功能")
        print("  3. 更新前端页面使用新API")

        return True

    except Exception as e:
        print(f"\n❌ 迁移过程中发生错误: {e}")
        import traceback

        traceback.print_exc()
        db.rollback()
        return False

    finally:
        db.close()


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
