"""
测试核心核销算法 - 验证"先扣付费，后扣赠送"逻辑
"""
import sys
from pathlib import Path

# 添加路径
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models_unified import UserAccount, AccountWallet, TransactionV2, Product, init_unified_db
from account_service import AccountService, PickupService
from exceptions import InsufficientBalanceError


def test_consume_order():
    """测试扣款顺序"""
    print("=" * 60)
    print("  水站管理系统 - 核心核销算法测试")
    print("=" * 60)
    
    # 初始化测试数据库
    engine = create_engine("sqlite:///./test_waterms.db", echo=False)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        # 创建表
        init_unified_db()
        
        # 创建测试产品
        product = Product(
            name="测试产品",
            specification="18L",
            unit="桶",
            price=10.0,
            stock=100,
            promo_threshold=10,
            promo_gift=1,
            is_active=1
        )
        db.add(product)
        db.commit()
        product_id = product.id
        
        # 创建测试用户钱包：付费桶 5 个，赠送桶 3 个
        user_id = 999
        wallet = AccountWallet(
            user_id=user_id,
            product_id=product_id,
            wallet_type='prepaid',
            paid_qty=5,
            free_qty=3,
            available_qty=8,
            total_consumed=0
        )
        db.add(wallet)
        db.commit()
        
        print(f"\n✓ 测试数据准备完成")
        print(f"  用户 ID: {user_id}")
        print(f"  产品 ID: {product_id}")
        print(f"  初始余额：付费桶 5 个，赠送桶 3 个，共 8 个")
        
        service = PickupService(db)
        
        # ========== 测试 1: 领取 3 桶 - 应该全部从付费桶扣除 ==========
        print("\n" + "-" * 60)
        print("测试 1: 领取 3 桶 (应全部从付费桶扣除)")
        print("-" * 60)
        
        result = service.record_pickup(user_id, product_id, 3)
        
        assert result['consume_result']['paid_qty'] == 3, "应该扣除 3 个付费桶"
        assert result['consume_result']['gift_qty'] == 0, "不应该扣除赠送桶"
        
        print(f"✓ 测试通过:")
        print(f"  - 扣除付费桶：{result['consume_result']['paid_qty']} 个")
        print(f"  - 扣除赠送桶：{result['consume_result']['gift_qty']} 个")
        
        # 检查交易记录
        for txn in result['transactions']:
            print(f"  - 交易{txn['id']}: 数量{txn['quantity']}, "
                  f"付费{txn['paid_qty_deducted']}, 赠送{txn['gift_qty_deducted']}, "
                  f"金额¥{txn['financial_amount']}")
        
        # ========== 测试 2: 领取 4 桶 - 应该 2 个付费桶 + 2 个赠送桶 ==========
        print("\n" + "-" * 60)
        print("测试 2: 领取 4 桶 (应 2 个付费 +2 个赠送)")
        print("-" * 60)
        
        result = service.record_pickup(user_id, product_id, 4)
        
        assert result['consume_result']['paid_qty'] == 2, "应该扣除 2 个付费桶"
        assert result['consume_result']['gift_qty'] == 2, "应该扣除 2 个赠送桶"
        
        print(f"✓ 测试通过:")
        print(f"  - 扣除付费桶：{result['consume_result']['paid_qty']} 个")
        print(f"  - 扣除赠送桶：{result['consume_result']['gift_qty']} 个")
        
        # 检查交易记录
        for txn in result['transactions']:
            print(f"  - 交易{txn['id']}: 数量{txn['quantity']}, "
                  f"付费{txn['paid_qty_deducted']}, 赠送{txn['gift_qty_deducted']}, "
                  f"金额¥{txn['financial_amount']}")
        
        # ========== 测试 3: 领取 5 桶 - 余额不足，抛出异常 ==========
        print("\n" + "-" * 60)
        print("测试 3: 领取 5 桶 (余额不足，应抛出异常)")
        print("-" * 60)
        
        try:
            service.record_pickup(user_id, product_id, 5)
            print("❌ 测试失败：应该抛出余额不足异常")
            assert False, "应该抛出余额不足异常"
        except InsufficientBalanceError as e:
            print(f"✓ 测试通过：正确抛出异常")
            print(f"  错误信息：{e.message}")
        
        # ========== 查询最终余额 ==========
        print("\n" + "-" * 60)
        print("最终余额查询")
        print("-" * 60)
        
        balance_info = service.get_user_pickup_balance(user_id, product_id)
        if balance_info['products']:
            product_balance = balance_info['products'][0]
            if 'balance_detail' in product_balance:
                prepaid = product_balance['balance_detail']['prepaid']
                print(f"  剩余付费桶：{prepaid['paid']} 个")
                print(f"  剩余赠送桶：{prepaid['gift']} 个")
                print(f"  预付总余额：{prepaid['total']} 个")
        
        print("\n" + "=" * 60)
        print("✅ 所有测试通过!")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ 测试失败：{e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        db.close()


if __name__ == "__main__":
    success = test_consume_order()
    sys.exit(0 if success else 1)
