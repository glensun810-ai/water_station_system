"""
Unit Tests for Unified Account System
双模式业务统一架构 - 单元测试
"""
import unittest
import os
import sys
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models_unified import Base, UserAccount, AccountWallet, SettlementBatch, TransactionV2, PromotionConfigV2
from account_service import AccountService, PickupService, SettlementService
from discount_strategy import DiscountContext, get_product


class TestUnifiedAccountSystem(unittest.TestCase):
    """统一账户系统单元测试"""
    
    def setUp(self):
        """每个测试前准备：创建新的内存数据库"""
        # 使用内存数据库进行测试，每个测试都是独立的
        self.engine = create_engine("sqlite:///:memory:", echo=False)
        
        # 先创建基础表（users, products）
        with self.engine.connect() as conn:
            conn.execute(text("""
                CREATE TABLE users (
                    id INTEGER PRIMARY KEY,
                    name VARCHAR(100),
                    department VARCHAR(100),
                    role VARCHAR(20) DEFAULT 'staff'
                )
            """))
            conn.execute(text("""
                CREATE TABLE products (
                    id INTEGER PRIMARY KEY,
                    name VARCHAR(100),
                    specification VARCHAR(50),
                    unit VARCHAR(20),
                    price FLOAT,
                    stock INTEGER DEFAULT 0,
                    is_active INTEGER DEFAULT 1
                )
            """))
            conn.execute(text("INSERT INTO users (id, name, department, role) VALUES (1, '张三', 'IT 部', 'staff')"))
            conn.execute(text("INSERT INTO users (id, name, department, role) VALUES (2, '李四', '运营部', 'staff')"))
            conn.execute(text("INSERT INTO users (id, name, department, role) VALUES (3, '管理员', '管理处', 'admin')"))
            conn.execute(text("INSERT INTO products (id, name, specification, unit, price) VALUES (1, '18L 桶装水', '18L', '桶', 10.0)"))
            conn.execute(text("INSERT INTO products (id, name, specification, unit, price) VALUES (2, '500ml 矿泉水', '500ml', '瓶', 2.0)"))
            conn.commit()
        
        # 创建新表结构
        Base.metadata.create_all(bind=self.engine)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
        # 创建优惠配置和会话
        self.db = self.SessionLocal()
        try:
            # 18L 桶装水 - 预付模式：买 10 赠 1
            self.db.add(PromotionConfigV2(product_id=1, mode='prepaid', trigger_qty=10, gift_qty=1, is_active=1))
            # 18L 桶装水 - 信用模式：标准价格
            self.db.add(PromotionConfigV2(product_id=1, mode='credit', trigger_qty=0, gift_qty=0, is_active=1))
            self.db.commit()
        finally:
            pass  # Keep session open for tests
        
        self.account_service = AccountService(self.db)
        self.pickup_service = PickupService(self.db)
        self.settlement_service = SettlementService(self.db)
    
    def tearDown(self):
        """每个测试后清理"""
        self.db.close()
        self.engine.dispose()
    
    # ==================== 账户服务测试 ====================
    
    def test_get_or_create_account(self):
        """测试获取或创建账户"""
        account = self.account_service.get_or_create_account(1)
        
        self.assertIsNotNone(account)
        self.assertEqual(account.user_id, 1)
        self.assertEqual(account.balance_credit, 0.0)
        self.assertEqual(account.balance_prepaid, 0.0)
    
    def test_add_balance(self):
        """测试增加余额"""
        # 增加信用余额
        wallet = self.account_service.add_balance(1, 1, 'credit', 50)
        
        self.assertEqual(wallet.available_qty, 50)
        self.assertEqual(wallet.wallet_type, 'credit')
        
        # 增加预付余额
        wallet = self.account_service.add_balance(1, 1, 'prepaid', 20)
        
        self.assertEqual(wallet.available_qty, 20)
        self.assertEqual(wallet.wallet_type, 'prepaid')
    
    def test_deduct_balance(self):
        """测试扣减余额"""
        # 先增加
        self.account_service.add_balance(1, 1, 'credit', 50)
        
        # 再扣减
        result = self.account_service.deduct_balance(1, 1, 'credit', 10)
        
        self.assertEqual(result['deducted_qty'], 10)
        
        # 验证剩余
        wallet = self.account_service.get_wallet(1, 1, 'credit')
        self.assertEqual(wallet.available_qty, 40)
    
    def test_deduct_balance_insufficient(self):
        """测试余额不足时抛出异常"""
        self.account_service.add_balance(1, 1, 'credit', 5)
        
        with self.assertRaises(ValueError):
            self.account_service.deduct_balance(1, 1, 'credit', 10)
    
    def test_get_total_balance(self):
        """测试获取总余额"""
        self.account_service.add_balance(1, 1, 'credit', 50)
        self.account_service.add_balance(1, 1, 'prepaid', 20)
        
        balance = self.account_service.get_total_balance(1, 1)
        
        self.assertEqual(balance['credit_available'], 50)
        self.assertEqual(balance['prepaid_available'], 20)
        self.assertEqual(balance['total_available'], 70)
    
    def test_consume_balance_priority(self):
        """测试扣款优先级：优先预付"""
        self.account_service.add_balance(1, 1, 'credit', 50)
        self.account_service.add_balance(1, 1, 'prepaid', 15)
        
        result = self.account_service.consume_balance(1, 1, 20)
        
        # 优先使用预付 15，再用信用 5
        self.assertEqual(result['prepaid_qty'], 15)
        self.assertEqual(result['credit_qty'], 5)
        self.assertEqual(result['total_qty'], 20)
    
    def test_consume_balance_all_prepaid(self):
        """测试全部使用预付"""
        self.account_service.add_balance(1, 1, 'credit', 50)
        self.account_service.add_balance(1, 1, 'prepaid', 30)
        
        result = self.account_service.consume_balance(1, 1, 20)
        
        # 全部使用预付
        self.assertEqual(result['prepaid_qty'], 20)
        self.assertEqual(result['credit_qty'], 0)
    
    def test_consume_balance_insufficient(self):
        """测试余额不足"""
        self.account_service.add_balance(1, 1, 'credit', 10)
        self.account_service.add_balance(1, 1, 'prepaid', 5)
        
        with self.assertRaises(ValueError):
            self.account_service.consume_balance(1, 1, 20)
    
    # ==================== 优惠策略测试 ====================
    
    def test_credit_discount_no_promotion(self):
        """测试信用模式无优惠"""
        discount_context = DiscountContext()
        result = discount_context.calculate_discount(self.db, 1, 10, 'credit', 1)
        
        # 信用模式：标准价格，无优惠
        self.assertEqual(result['unit_price'], 10.0)
        self.assertEqual(result['paid_qty'], 10)
        self.assertEqual(result['free_qty'], 0)
        self.assertEqual(result['total_price'], 100.0)
        self.assertIn('标准价格', result['discount_desc'])
    
    def test_prepaid_discount_buy_10_get_1_first_purchase(self):
        """测试预付模式买 10 赠 1（第一次购买）"""
        discount_context = DiscountContext()
        
        # 第一次购买 10 个
        result = discount_context.calculate_discount(self.db, 1, 10, 'prepaid', 1)
        
        # 买 10 赠 1：第 11 个才免费，所以前 10 个都付费
        self.assertEqual(result['paid_qty'], 10)
        self.assertEqual(result['free_qty'], 0)
        self.assertEqual(result['total_price'], 100.0)
    
    def test_prepaid_discount_complex(self):
        """测试复杂场景：无历史记录，购买 25 个"""
        discount_context = DiscountContext()
        
        # 一次性购买 25 个（无历史记录）
        result = discount_context.calculate_discount(self.db, 1, 25, 'prepaid', 1)
        
        # 周期 = 11，25 / 11 = 2 个周期...余 3
        # 免费数量 = 2（第 11 个和第 22 个）
        self.assertEqual(result['free_qty'], 2)
        self.assertEqual(result['paid_qty'], 23)
        self.assertEqual(result['total_price'], 230.0)  # 23 * 10.0
    
    # ==================== 领取服务测试 ====================
    
    def test_calculate_pickup(self):
        """测试计算领取详情"""
        # 准备余额
        self.account_service.add_balance(1, 1, 'credit', 50)
        self.account_service.add_balance(1, 1, 'prepaid', 15)
        
        # 计算领取 20 个
        result = self.pickup_service.calculate_pickup(1, 1, 20)
        
        self.assertEqual(result['quantity'], 20)
        self.assertEqual(result['prepaid']['qty'], 15)
        self.assertEqual(result['credit']['qty'], 5)
    
    def test_record_pickup_mixed_payment(self):
        """测试记录领取：混合支付"""
        # 准备余额
        self.account_service.add_balance(1, 1, 'credit', 50)
        self.account_service.add_balance(1, 1, 'prepaid', 15)
        
        # 领取 20 个
        result = self.pickup_service.record_pickup(1, 1, 20, '测试领取')
        
        self.assertEqual(len(result['transactions']), 2)
        
        # 验证交易记录
        modes = {t['mode']: t for t in result['transactions']}
        
        # 预付部分
        self.assertIn('prepaid', modes)
        prepaid_txn = modes['prepaid']
        self.assertEqual(prepaid_txn['quantity'], 15)
        self.assertEqual(prepaid_txn['status'], 'settled')  # 预付直接结算
        
        # 信用部分
        self.assertIn('credit', modes)
        credit_txn = modes['credit']
        self.assertEqual(credit_txn['quantity'], 5)
        self.assertEqual(credit_txn['status'], 'pending')  # 信用待结算
    
    def test_record_pickup_pure_prepaid(self):
        """测试纯预付领取"""
        self.account_service.add_balance(1, 1, 'credit', 50)
        self.account_service.add_balance(1, 1, 'prepaid', 30)
        
        # 领取 20 个（全部使用预付）
        result = self.pickup_service.record_pickup(1, 1, 20, '纯预付领取')
        
        # 应该只有 1 条预付交易记录
        self.assertEqual(len(result['transactions']), 1)
        self.assertEqual(result['transactions'][0]['mode'], 'prepaid')
        self.assertEqual(result['transactions'][0]['quantity'], 20)
    
    def test_record_pickup_insufficient_balance(self):
        """测试余额不足"""
        self.account_service.add_balance(1, 1, 'credit', 5)
        self.account_service.add_balance(1, 1, 'prepaid', 5)
        
        with self.assertRaises(ValueError):
            self.pickup_service.record_pickup(1, 1, 20, '余额不足测试')
    
    def test_get_user_pickup_balance(self):
        """测试获取用户余额"""
        self.account_service.add_balance(1, 1, 'credit', 50)
        self.account_service.add_balance(1, 1, 'prepaid', 20)
        
        result = self.pickup_service.get_user_pickup_balance(1, 1)
        
        self.assertEqual(result['user_id'], 1)
        self.assertEqual(len(result['products']), 1)
        
        product = result['products'][0]
        self.assertEqual(product['product_id'], 1)
        self.assertEqual(product['balance']['credit_available'], 50)
        self.assertEqual(product['balance']['prepaid_available'], 20)
    
    # ==================== 结算服务测试 ====================
    
    def test_apply_settlement(self):
        """测试申请结算"""
        # 先创建一些信用交易
        self.account_service.add_balance(1, 1, 'credit', 100)
        
        # 领取产生待结算交易
        pickup_result = self.pickup_service.record_pickup(1, 1, 10, '测试交易 1')
        txn_ids = [t['id'] for t in pickup_result['transactions'] if t['mode'] == 'credit']
        
        if txn_ids:
            # 申请结算
            batch = self.settlement_service.apply_settlement(1, txn_ids)
            
            self.assertIsNotNone(batch)
            self.assertEqual(batch.status, 'pending')
            self.assertIn('BATCH', batch.batch_no)
    
    def test_confirm_settlement(self):
        """测试确认结算"""
        # 先申请结算
        self.account_service.add_balance(1, 1, 'credit', 100)
        pickup_result = self.pickup_service.record_pickup(1, 1, 10, '测试交易 2')
        txn_ids = [t['id'] for t in pickup_result['transactions'] if t['mode'] == 'credit']
        
        if txn_ids:
            batch = self.settlement_service.apply_settlement(1, txn_ids)
            
            # 管理员确认
            confirmed_batch = self.settlement_service.confirm_settlement(batch.id, 3)
            
            self.assertEqual(confirmed_batch.status, 'completed')
            self.assertIsNotNone(confirmed_batch.confirmed_at)
            self.assertEqual(confirmed_batch.confirmed_by, 3)


class TestAccountServiceEdgeCases(unittest.TestCase):
    """边界条件测试"""
    
    def setUp(self):
        """准备测试环境"""
        self.engine = create_engine("sqlite:///:memory:", echo=False)
        
        # 创建基础表
        with self.engine.connect() as conn:
            conn.execute(text("CREATE TABLE users (id INTEGER PRIMARY KEY, name VARCHAR)"))
            conn.execute(text("CREATE TABLE products (id INTEGER PRIMARY KEY, name VARCHAR, price FLOAT)"))
            conn.execute(text("INSERT INTO users (id, name) VALUES (1, '测试用户')"))
            conn.execute(text("INSERT INTO products (id, name, price) VALUES (1, '测试产品', 10.0)"))
            conn.commit()
        
        Base.metadata.create_all(bind=self.engine)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.db = self.SessionLocal()
        self.account_service = AccountService(self.db)
    
    def tearDown(self):
        self.db.close()
        self.engine.dispose()
    
    def test_zero_quantity(self):
        """测试零数量"""
        self.account_service.add_balance(1, 1, 'credit', 10)
        
        # 扣减 0 应该成功但不改变余额
        result = self.account_service.deduct_balance(1, 1, 'credit', 0)
        self.assertEqual(result['deducted_qty'], 0)
        
        wallet = self.account_service.get_wallet(1, 1, 'credit')
        self.assertEqual(wallet.available_qty, 10)
    
    def test_repeated_account_creation(self):
        """测试重复创建账户"""
        account1 = self.account_service.get_or_create_account(1)
        account2 = self.account_service.get_or_create_account(1)
        
        # 应该是同一个账户
        self.assertEqual(account1.id, account2.id)


def run_tests():
    """运行所有测试"""
    # 创建测试套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 添加测试
    suite.addTests(loader.loadTestsFromTestCase(TestUnifiedAccountSystem))
    suite.addTests(loader.loadTestsFromTestCase(TestAccountServiceEdgeCases))
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 返回结果
    return result.wasSuccessful()


if __name__ == "__main__":
    print("=" * 60)
    print("统一账户系统单元测试")
    print("=" * 60)
    
    success = run_tests()
    
    print("\n" + "=" * 60)
    if success:
        print("✓ 所有测试通过！")
    else:
        print("✗ 部分测试失败")
    print("=" * 60)
    
    sys.exit(0 if success else 1)
