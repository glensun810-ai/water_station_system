"""
测试结算模块v2模型
验证新创建的数据表和ORM模型是否正常工作
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker
from models.settlement_v2 import (
    SettlementApplication,
    SettlementItem,
    MonthlySettlement,
)
from models.base import Base
from datetime import datetime, date


def test_database_tables():
    """测试数据库表是否正确创建"""
    print("=" * 60)
    print("测试结算模块v2数据表")
    print("=" * 60)

    try:
        from config.settings import settings
        from sqlalchemy import create_engine, inspect

        engine = create_engine(settings.DATABASE_URL, echo=False)
        inspector = inspect(engine)

        tables_to_check = [
            "settlement_applications",
            "settlement_items",
            "monthly_settlements",
        ]

        print("\n检查数据表:")
        for table_name in tables_to_check:
            if table_name in inspector.get_table_names():
                print(f"  ✅ {table_name} 表存在")

                columns = [col["name"] for col in inspector.get_columns(table_name)]
                print(f"     字段数量: {len(columns)}")
            else:
                print(f"  ❌ {table_name} 表不存在")
                return False

        return True

    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        return False

        return True

    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        return False


def test_orm_models():
    """测试ORM模型"""
    print("\n" + "=" * 60)
    print("测试ORM模型")
    print("=" * 60)

    try:
        from config.settings import settings
        from config.database import get_db

        engine = create_engine(settings.DATABASE_URL, echo=False)
        SessionLocal = sessionmaker(bind=engine)
        db = SessionLocal()

        try:
            print("\n测试SettlementApplication模型:")

            application = SettlementApplication(
                application_no="TEST-001",
                office_id=1,
                office_name="测试办公室",
                applicant_id=1,
                applicant_name="测试用户",
                record_count=1,
                total_amount=100.00,
                status="applied",
                note="测试数据",
            )

            db.add(application)
            db.flush()

            print(
                f"  ✅ 创建申请单成功: ID={application.id}, No={application.application_no}"
            )

            print("\n测试SettlementItem模型:")

            item = SettlementItem(
                application_id=application.id,
                pickup_id=999,
                product_name="矿泉水",
                quantity=10,
                amount=100.00,
                pickup_status="applied",
                pickup_time=datetime.now(),
                pickup_person="测试用户",
            )

            db.add(item)
            db.flush()

            print(
                f"  ✅ 创建明细成功: ID={item.id}, Application_ID={item.application_id}"
            )

            print("\n测试MonthlySettlement模型:")

            monthly = MonthlySettlement(
                settlement_no="MS-2026-04-001",
                office_id=1,
                office_name="测试办公室",
                settlement_period="2026-04",
                start_date=date(2026, 4, 1),
                end_date=date(2026, 4, 30),
                record_count=1,
                total_amount=100.00,
                status="pending",
                note="测试数据",
            )

            db.add(monthly)
            db.flush()

            print(
                f"  ✅ 创建月度结算单成功: ID={monthly.id}, No={monthly.settlement_no}"
            )

            print("\n测试关联关系:")
            items = application.items
            print(f"  ✅ 申请单明细数量: {len(items)}")
            if items:
                print(f"     明细ID: {items[0].id}, 金额: ¥{items[0].amount}")

            print("\n清理测试数据...")
            db.delete(item)
            db.delete(application)
            db.delete(monthly)
            db.commit()

            print("  ✅ 测试数据已清理")

            return True

        except Exception as e:
            print(f"❌ ORM测试失败: {e}")
            db.rollback()
            return False

        finally:
            db.close()

    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        return False


def test_import_models():
    """测试模型导入"""
    print("\n" + "=" * 60)
    print("测试模型导入")
    print("=" * 60)

    try:
        from models import SettlementApplication, SettlementItem, MonthlySettlement

        print("  ✅ 从models包导入SettlementApplication成功")
        print("  ✅ 从models包导入SettlementItem成功")
        print("  ✅ 从models包导入MonthlySettlement成功")

        return True

    except Exception as e:
        print(f"❌ 模型导入失败: {e}")
        return False


def main():
    """主函数"""
    print("\n开始测试结算模块v2...")

    results = []

    results.append(("数据表检查", test_database_tables()))
    results.append(("模型导入", test_import_models()))
    results.append(("ORM模型", test_orm_models()))

    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)

    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  {test_name}: {status}")

    all_passed = all(result for _, result in results)

    if all_passed:
        print("\n🎉 所有测试通过!")
        return True
    else:
        print("\n❌ 部分测试失败,请检查错误信息")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
