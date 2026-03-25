"""
测试充值/授信完整流程
验证充值后额度正确保存和使用
"""
import sys
from pathlib import Path

# 添加路径
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.models_unified import UserAccount, AccountWallet, Product, PromotionConfigV2, init_unified_db
from backend.account_service import AccountService, PickupService
from backend.exceptions import InsufficientBalanceError


def test_topup_and_pickup_flow():
    """测试充值和领取完整流程"""
    print("=" * 60)
    print("  水站管理系统 - 充值/授信完整流程测试")
    print("=" * 60)
    
    # 初始化测试数据库
    engine = create_engine("sqlite:///./test_topup.db", echo=False)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        # 创建表
        init_unified_db()
        
        # ========== 准备测试数据 ==========
        print("\n1️⃣ 准备测试数据")
        
        # 创建测试产品
        product = Product(
            name="12L 桶装水",
            specification="12L",
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
        
        # 配置买 10 赠 1 优惠
        promo_config = PromotionConfigV2(
            product_id=product_id,
            mode='prepaid',
            trigger_qty=10,
            gift_qty=1,
            discount_rate=100.0,
            is_active=1,
            description="买 10 赠 1"
        )
        db.add(promo_config)
        db.commit()
        
        # 创建测试用户
        user_id = 888
        account = UserAccount(user_id=user_id)
        db.add(account)
        db.commit()
        
        print(f"✓ 产品：{product.name}，价格：¥{product.price}/{product.unit}")
        print(f"✓ 优惠配置：买{promo_config.trigger_qty}赠{promo_config.gift_qty}")
        print(f"✓ 用户 ID: {user_id}")
        
        service = AccountService(db)
        pickup_service = PickupService(db)
        
        # ========== 测试场景 1: 预付充值（享受买赠优惠）==========
        print("\n" + "-" * 60)
        print("测试场景 1: 预付充值（买 10 赠 1）")
        print("-" * 60)
        
        # 充值 10 个，应该获得 10 个付费桶 + 1 个赠送桶
        paid_quantity = 10
        free_quantity = (paid_quantity // promo_config.trigger_qty) * promo_config.gift_qty
        
        result = service.add_prepaid_balance(
            user_id=user_id,
            product_id=product_id,
            paid_quantity=paid_quantity,
            free_quantity=free_quantity,
            unit_price=product.price
        )
        
        print(f"充值操作:")
        print(f"  - 付费数量：{result['paid_qty']} 个")
        print(f"  - 赠送数量：{result['free_qty']} 个")
        print(f"  - 总数量：{result['total_qty']} 个")
        print(f"  - 总金额：¥{result['total_amount']:.2f}")
        
        assert result['paid_qty'] == 10, "付费桶应该是 10 个"
        assert result['free_qty'] == 1, "赠送桶应该是 1 个"
        assert result['total_qty'] == 11, "总数量应该是 11 个"
        assert result['total_amount'] == 100.0, "总金额应该是 100 元"
        
        print(f"✓ 充值成功，余额已正确保存")
        
        # ========== 测试场景 2: 查询余额验证 ==========
        print("\n" + "-" * 60)
        print("测试场景 2: 查询余额验证")
        print("-" * 60)
        
        balance_info = pickup_service.get_user_pickup_balance(user_id, product_id)
        
        if balance_info['products']:
            product_balance = balance_info['products'][0]
            
            if 'balance_detail' in product_balance:
                prepaid = product_balance['balance_detail']['prepaid']
                print(f"余额详情:")
                print(f"  - 付费桶：{prepaid['paid']} 个")
                print(f"  - 赠送桶：{prepaid['gift']} 个")
                print(f"  - 总余额：{prepaid['total']} 个")
                
                assert prepaid['paid'] == 10, "付费桶应该是 10 个"
                assert prepaid['gift'] == 1, "赠送桶应该是 1 个"
                assert prepaid['total'] == 11, "总余额应该是 11 个"
                
                print(f"✓ 余额信息正确")
            else:
                print(f"❌ 未返回 balance_detail 信息")
                return False
        else:
            print(f"❌ 未查询到余额信息")
            return False
        
        # ========== 测试场景 3: 领取测试（先扣付费桶）==========
        print("\n" + "-" * 60)
        print("测试场景 3: 领取测试（验证扣款顺序）")
        print("-" * 60)
        
        # 领取 5 个 - 应该全部从付费桶扣除
        print("领取 5 个（应全部从付费桶扣除）...")
        result = pickup_service.record_pickup(user_id, product_id, 5)
        
        assert result['consume_result']['paid_qty'] == 5, "应该扣除 5 个付费桶"
        assert result['consume_result']['gift_qty'] == 0, "不应该扣除赠送桶"
        
        print(f"✓ 领取 5 个成功:")
        print(f"  - 扣除付费桶：{result['consume_result']['paid_qty']} 个")
        print(f"  - 扣除赠送桶：{result['consume_result']['gift_qty']} 个")
        
        # 检查交易记录明细
        for txn in result['transactions']:
            print(f"  - 交易{txn['id']}: 数量{txn['quantity']}, "
                  f"付费{txn['paid_qty_deducted']}, 赠送{txn['gift_qty_deducted']}, "
                  f"金额¥{txn['financial_amount']}")
        
        # 再次领取 6 个 - 应该 5 个付费桶 + 1 个赠送桶
        print("\n领取 6 个（应 5 个付费 +1 个赠送）...")
        result = pickup_service.record_pickup(user_id, product_id, 6)
        
        assert result['consume_result']['paid_qty'] == 5, "应该扣除 5 个付费桶"
        assert result['consume_result']['gift_qty'] == 1, "应该扣除 1 个赠送桶"
        
        print(f"✓ 领取 6 个成功:")
        print(f"  - 扣除付费桶：{result['consume_result']['paid_qty']} 个")
        print(f"  - 扣除赠送桶：{result['consume_result']['gift_qty']} 个")
        
        # 检查交易记录明细
        for txn in result['transactions']:
            print(f"  - 交易{txn['id']}: 数量{txn['quantity']}, "
                  f"付费{txn['paid_qty_deducted']}, 赠送{txn['gift_qty_deducted']}, "
                  f"金额¥{txn['financial_amount']}")
        
        # ========== 测试场景 4: 最终余额验证 ==========
        print("\n" + "-" * 60)
        print("测试场景 4: 最终余额验证")
        print("-" * 60)
        
        balance_info = pickup_service.get_user_pickup_balance(user_id, product_id)
        product_balance = balance_info['products'][0]
        prepaid = product_balance['balance_detail']['prepaid']
        
        print(f"最终余额:")
        print(f"  - 付费桶：{prepaid['paid']} 个")
        print(f"  - 赠送桶：{prepaid['gift']} 个")
        print(f"  - 总余额：{prepaid['total']} 个")
        
        # 初始 10 个付费桶 + 1 个赠送桶
        # 第一次领取 5 个付费桶
        # 第二次领取 5 个付费桶 + 1 个赠送桶
        # 剩余：0 个付费桶 + 0 个赠送桶
        assert prepaid['paid'] == 0, "付费桶应该已全部用完"
        assert prepaid['gift'] == 0, "赠送桶应该已全部用完"
        assert prepaid['total'] == 0, "总余额应该为 0"
        
        print(f"✓ 余额已正确扣减")
        
        # ========== 测试场景 5: 信用授信测试 ==========
        print("\n" + "-" * 60)
        print("测试场景 5: 信用授信测试")
        print("-" * 60)
        
        # 授信 20 个
        credit_result = service.add_credit_balance(
            user_id=user_id,
            product_id=product_id,
            quantity=20
        )
        
        print(f"信用授信:")
        print(f"  - 授信数量：{credit_result['quantity']} 个")
        print(f"  - 可用余额：{credit_result['available_qty']} 个")
        
        assert credit_result['quantity'] == 20, "授信应该是 20 个"
        assert credit_result['available_qty'] == 20, "可用余额应该是 20 个"
        
        print(f"✓ 信用授信成功")
        
        # ========== 测试场景 6: 使用信用余额领取 ==========
        print("\n" + "-" * 60)
        print("测试场景 6: 使用信用余额领取")
        print("-" * 60)
        
        # 领取 3 个 - 应该使用信用余额
        print("领取 3 个（使用信用余额）...")
        result = pickup_service.record_pickup(user_id, product_id, 3)
        
        assert result['consume_result']['credit_qty'] == 3, "应该扣除 3 个信用桶"
        
        print(f"✓ 领取 3 个成功:")
        print(f"  - 扣除信用桶：{result['consume_result']['credit_qty']} 个")
        
        # 检查交易记录
        for txn in result['transactions']:
            print(f"  - 交易{txn['id']}: 模式{txn['mode']}, "
                  f"数量{txn['quantity']}, 金额¥{txn['actual_price']}, "
                  f"状态{txn['status']}")
        
        # ========== 总结 ==========
        print("\n" + "=" * 60)
        print("✅ 所有测试通过!")
        print("=" * 60)
        print("\n功能验证清单:")
        print("  ✓ 预付充值并应用买赠优惠")
        print("  ✓ 充值后额度正确保存（区分付费桶和赠送桶）")
        print("  ✓ 查询余额返回详细分类信息")
        print("  ✓ 领取时先扣付费桶，后扣赠送桶")
        print("  ✓ 领用记录详细记录付费桶和赠送桶数量及金额")
        print("  ✓ 信用授信功能正常")
        print("  ✓ 信用余额领取功能正常")
        
        return True
        
    except Exception as e:
        print(f"\n❌ 测试失败：{e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        db.close()


if __name__ == "__main__":
    success = test_topup_and_pickup_flow()
    sys.exit(0 if success else 1)
