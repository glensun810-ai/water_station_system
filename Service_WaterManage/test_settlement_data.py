"""
测试结算管理功能 - 添加测试数据
Run: python test_settlement_data.py
"""

import sys

sys.path.insert(0, "backend")

from main import engine, Base
from models_unified import (
    Office,
    OfficePickup,
    OfficeSettlement,
    Product,
    OfficeAccount,
    OfficeRecharge,
)
from main import SessionLocal
from datetime import datetime, timedelta
import json


def init_tables():
    """确保表存在"""
    Base.metadata.create_all(bind=engine)
    print("✓ 数据库表已就绪")


def add_test_data():
    """添加结算测试数据"""
    db = SessionLocal()

    try:
        # 获取或创建测试产品
        product = db.query(Product).filter(Product.name == "桶装水").first()
        if not product:
            product = Product(
                name="桶装水",
                specification="18L",
                unit="桶",
                price=15.0,
                stock=1000,
                is_active=1,
            )
            db.add(product)
            db.commit()
            db.refresh(product)

        # 获取或创建测试办公室
        office = db.query(Office).filter(Office.name == "测试办公室A").first()
        if not office:
            office = Office(
                name="测试办公室A", room_number="301", is_common=1, is_active=1
            )
            db.add(office)
            db.commit()
            db.refresh(office)
            print(f"✓ 已创建办公室: {office.name}")

        # 创建预付账户
        account = (
            db.query(OfficeAccount)
            .filter(
                OfficeAccount.office_id == office.id,
                OfficeAccount.product_id == product.id,
            )
            .first()
        )
        if not account:
            account = OfficeAccount(
                office_id=office.id,
                product_id=product.id,
                total_qty=20,
                remaining_qty=15,
                reserved_qty=5,
            )
            db.add(account)
            db.commit()
            print(f"✓ 已创建预付账户，余额: 15桶")

        # 创建测试领水记录（待付款状态 - pending）
        now = datetime.now()
        pending_pickups = []
        for i in range(3):
            pickup = OfficePickup(
                office_id=office.id,
                office_name=office.name,
                office_room_number=office.room_number,
                product_id=product.id,
                product_name=product.name,
                quantity=5,
                unit_price=product.price,
                total_amount=product.price * 5,
                pickup_person=f"员工{chr(65 + i)}",
                pickup_person_id=None,
                pickup_time=now - timedelta(days=i + 1),
                settlement_status="pending",
                payment_mode="credit",
                created_at=now - timedelta(days=i + 1),
            )
            db.add(pickup)
            pending_pickups.append(pickup)

        db.commit()
        for p in pending_pickups:
            db.refresh(p)
        print(f"✓ 已创建 {len(pending_pickups)} 条待付款领水记录")

        # 创建测试领水记录（已申请待确认 - applied）
        applied_pickup = OfficePickup(
            office_id=office.id,
            office_name=office.name,
            office_room_number=office.room_number,
            product_id=product.id,
            product_name=product.name,
            quantity=3,
            unit_price=product.price,
            total_amount=product.price * 3,
            pickup_person="员工D",
            pickup_person_id=None,
            pickup_time=now - timedelta(days=5),
            settlement_status="applied",
            payment_mode="credit",
            created_at=now - timedelta(days=5),
        )
        db.add(applied_pickup)
        db.commit()
        db.refresh(applied_pickup)

        # 创建已申请待确认的结算单
        settlement_applied = OfficeSettlement(
            settlement_no=f"ST{datetime.now().strftime('%Y%m%d%H%M%S')}A01",
            office_id=office.id,
            office_name=office.name,
            office_room_number=office.room_number,
            total_quantity=3,
            total_amount=product.price * 3,
            status="applied",
            applied_by="测试用户",
            applied_at=now - timedelta(days=1),
            pickup_ids=json.dumps([applied_pickup.id]),
            created_at=now - timedelta(days=1),
        )
        db.add(settlement_applied)
        print(f"✓ 已创建1条付款待确认结算单")

        # 创建已结清结算单
        settled_pickup = OfficePickup(
            office_id=office.id,
            office_name=office.name,
            office_room_number=office.room_number,
            product_id=product.id,
            product_name=product.name,
            quantity=2,
            unit_price=product.price,
            total_amount=product.price * 2,
            pickup_person="员工E",
            pickup_person_id=None,
            pickup_time=now - timedelta(days=10),
            settlement_status="settled",
            payment_mode="credit",
            created_at=now - timedelta(days=10),
        )
        db.add(settled_pickup)
        db.commit()
        db.refresh(settled_pickup)

        settlement_confirmed = OfficeSettlement(
            settlement_no=f"ST{datetime.now().strftime('%Y%m%d%H%M%S')}B02",
            office_id=office.id,
            office_name=office.name,
            office_room_number=office.room_number,
            total_quantity=2,
            total_amount=product.price * 2,
            status="confirmed",
            applied_by="测试用户",
            applied_at=now - timedelta(days=8),
            confirmed_by="管理员",
            confirmed_at=now - timedelta(days=7),
            pickup_ids=json.dumps([settled_pickup.id]),
            created_at=now - timedelta(days=8),
        )
        db.add(settlement_confirmed)
        print(f"✓ 已创建1条已结清结算单")

        # 创建另一个已结清结算单
        settled_pickup2 = OfficePickup(
            office_id=office.id,
            office_name=office.name,
            office_room_number=office.room_number,
            product_id=product.id,
            product_name=product.name,
            quantity=4,
            unit_price=product.price,
            total_amount=product.price * 4,
            pickup_person="员工F",
            pickup_person_id=None,
            pickup_time=now - timedelta(days=15),
            settlement_status="settled",
            payment_mode="credit",
            created_at=now - timedelta(days=15),
        )
        db.add(settled_pickup2)
        db.commit()
        db.refresh(settled_pickup2)

        settlement_confirmed2 = OfficeSettlement(
            settlement_no=f"ST{datetime.now().strftime('%Y%m%d%H%M%S')}C03",
            office_id=office.id,
            office_name=office.name,
            office_room_number=office.room_number,
            total_quantity=4,
            total_amount=product.price * 4,
            status="confirmed",
            applied_by="测试用户",
            applied_at=now - timedelta(days=12),
            confirmed_by="管理员",
            confirmed_at=now - timedelta(days=11),
            pickup_ids=json.dumps([settled_pickup2.id]),
            created_at=now - timedelta(days=12),
        )
        db.add(settlement_confirmed2)

        db.commit()
        print(f"✓ 已创建1条已结清结算单")

        # 创建充值记录
        recharge = OfficeRecharge(
            office_id=office.id,
            product_id=product.id,
            quantity=20,
            unit_price=product.price,
            total_amount=product.price * 20,
            recharge_person="管理员",
            note="测试充值",
            status="pending",
        )
        db.add(recharge)
        db.commit()
        print(f"✓ 已创建1条待审核充值记录")

        print("\n" + "=" * 50)
        print("🎉 结算测试数据添加完成！")
        print("=" * 50)
        print("\n测试数据概览:")
        print(f"  办公室: {office.name} ({office.room_number})")
        print(f"  预付余额: 15桶")
        print(f"  待付款领水记录: 3笔 (共 ¥{product.price * 5 * 3})")
        print(f"  付款待确认结算单: 1笔 (¥{product.price * 3})")
        print(f"  已结清结算单: 2笔 (共 ¥{product.price * 2 + product.price * 4})")
        print(f"  待审核充值: 1笔")

    except Exception as e:
        db.rollback()
        print(f"✗ 添加测试数据失败: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    init_tables()
    add_test_data()
