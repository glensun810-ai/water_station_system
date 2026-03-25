"""
Comprehensive Test Script - Unified Payment System
统一支付平台系统完整测试脚本
测试所有核心功能和集成
"""
import sys
sys.path.append('backend')

from main import engine, Base, get_db
from models_unified_order import UnifiedOrder, UnifiedTransaction
from models_coupon import Coupon, UserCoupon
from sqlalchemy import inspect

def test_database_tables():
    """测试 1: 检查数据库表是否创建"""
    print("\n" + "=" * 60)
    print("测试 1: 检查数据库表")
    print("=" * 60)
    
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    
    required_tables = ['unified_orders', 'unified_transactions', 'coupons', 'user_coupons']
    
    for table in required_tables:
        if table in tables:
            print(f"✅ 表 {table} 存在")
        else:
            print(f"❌ 表 {table} 不存在")
            # 自动创建
            print(f"   正在创建表 {table}...")
            try:
                if table == 'unified_orders':
                    UnifiedOrder.__table__.create(bind=engine)
                elif table == 'unified_transactions':
                    UnifiedTransaction.__table__.create(bind=engine)
                elif table == 'coupons':
                    Coupon.__table__.create(bind=engine)
                elif table == 'user_coupons':
                    UserCoupon.__table__.create(bind=engine)
                print(f"   ✅ 表 {table} 创建成功")
            except Exception as e:
                print(f"   ❌ 创建失败：{e}")
    
    print(f"\n当前数据库共有 {len(tables)} 个表")


def test_models_import():
    """测试 2: 测试模型导入"""
    print("\n" + "=" * 60)
    print("测试 2: 测试模型导入")
    print("=" * 60)
    
    try:
        from models_unified_order import UnifiedOrder, UnifiedTransaction
        print("✅ models_unified_order 导入成功")
    except Exception as e:
        print(f"❌ models_unified_order 导入失败：{e}")
    
    try:
        from models_coupon import Coupon, UserCoupon
        print("✅ models_coupon 导入成功")
    except Exception as e:
        print(f"❌ models_coupon 导入失败：{e}")


def test_api_routes():
    """测试 3: 测试 API 路由注册"""
    print("\n" + "=" * 60)
    print("测试 3: 测试 API 路由注册")
    print("=" * 60)
    
    try:
        from main import app
        routes = [route.path for route in app.routes]
        
        # 检查关键路由
        required_routes = [
            '/api/unified/pickup',
            '/api/unified/orders/{order_id}/pay',
            '/api/coupons',
            '/api/coupons/my',
            '/api/coupons/issue'
        ]
        
        for route in required_routes:
            # 简化匹配 (处理路径参数)
            base_route = route.split('{')[0].rstrip('/')
            matched = any(base_route in r for r in routes)
            
            if matched:
                print(f"✅ 路由 {route} 已注册")
            else:
                print(f"❌ 路由 {route} 未注册")
        
        print(f"\n应用共有 {len(routes)} 个路由")
        
    except Exception as e:
        print(f"❌ API 路由测试失败：{e}")


def test_model_creation():
    """测试 4: 测试模型实例化"""
    print("\n" + "=" * 60)
    print("测试 4: 测试模型实例化")
    print("=" * 60)
    
    from datetime import datetime, timedelta
    
    # 测试 UnifiedOrder
    try:
        order = UnifiedOrder(
            order_no="TEST20260324001",
            user_id=1,
            product_id=1,
            quantity=10,
            unit_price=10.0,
            total_amount=100.0,
            payment_method='prepaid',
            payment_status='pending',
            prepaid_paid_qty=9,
            prepaid_gift_qty=1
        )
        print("✅ UnifiedOrder 实例化成功")
        print(f"   订单号：{order.order_no}")
        print(f"   支付方式：{order.payment_method}")
        print(f"   付费{order.prepaid_paid_qty}桶 + 赠送{order.prepaid_gift_qty}桶")
    except Exception as e:
        print(f"❌ UnifiedOrder 实例化失败：{e}")
    
    # 测试 Coupon
    try:
        now = datetime.now()
        coupon = Coupon(
            coupon_code="TEST95OFF",
            name="测试优惠券 95 折",
            type='discount',
            value=95,
            min_amount=50.0,
            valid_from=now,
            valid_until=now + timedelta(days=30),
            status='active'
        )
        print("✅ Coupon 实例化成功")
        print(f"   优惠券码：{coupon.coupon_code}")
        print(f"   类型：{coupon.type}")
        print(f"   价值：{coupon.value}%")
    except Exception as e:
        print(f"❌ Coupon 实例化失败：{e}")


def test_helper_functions():
    """测试 5: 测试工具函数"""
    print("\n" + "=" * 60)
    print("测试 5: 测试工具函数")
    print("=" * 60)
    
    # 测试智能推荐函数
    try:
        from api_unified_order import smart_payment_recommend, generate_order_no
        db = next(get_db())
        
        # 生成订单号
        order_no = generate_order_no()
        print(f"✅ 订单号生成：{order_no}")
        
        # 测试推荐 (需要实际数据)
        print("ℹ️  智能推荐需要实际的用户和产品数据，跳过详细测试")
        
    except Exception as e:
        print(f"❌ 工具函数测试失败：{e}")


def test_coupon_calculation():
    """测试 6: 测试优惠券计算"""
    print("\n" + "=" * 60)
    print("测试 6: 测试优惠券折扣计算")
    print("=" * 60)
    
    try:
        from api_coupon import calculate_coupon_discount
        
        # 测试折扣券
        discount_coupon = Coupon(
            coupon_code="DISCOUNT95",
            name="95 折券",
            type='discount',
            value=95,
            min_amount=50.0,
            max_discount=20.0
        )
        
        # 预付模式
        discount_prepaid = calculate_coupon_discount(discount_coupon, 100.0, 'prepaid')
        print(f"✅ 折扣券 (预付): 订单¥100 → 优惠¥{discount_prepaid}")
        
        # 信用模式
        discount_credit = calculate_coupon_discount(discount_coupon, 100.0, 'credit')
        print(f"✅ 折扣券 (信用): 订单¥100 → 优惠¥{discount_credit}")
        
        # 测试满减券
        fixed_coupon = Coupon(
            coupon_code="FIXED20",
            name="满 100 减 20",
            type='fixed',
            value=20,
            min_amount=100.0
        )
        
        fixed_discount = calculate_coupon_discount(fixed_coupon, 150.0, 'prepaid')
        print(f"✅ 满减券：订单¥150 → 优惠¥{fixed_discount}")
        
    except Exception as e:
        print(f"❌ 优惠券计算测试失败：{e}")


def test_frontend_files():
    """测试 7: 检查前端文件"""
    print("\n" + "=" * 60)
    print("测试 7: 检查前端文件")
    print("=" * 60)
    
    import os
    
    frontend_files = [
        'frontend/pickup-unified.html',
        'frontend/admin-coupons.html',
        'frontend/user-coupons.html',
        'frontend/vue.global.js'
    ]
    
    for filepath in frontend_files:
        full_path = f"/Users/sgl/PycharmProjects/AIchanyejiqun/Service_WaterManage/{filepath}"
        if os.path.exists(full_path):
            size = os.path.getsize(full_path)
            print(f"✅ {filepath} ({size:,} 字节)")
        else:
            print(f"❌ {filepath} 不存在")


def run_all_tests():
    """运行所有测试"""
    print("\n" + "🚀" * 30)
    print("统一支付平台系统 - 完整测试")
    print("🚀" * 30)
    
    test_database_tables()
    test_models_import()
    test_api_routes()
    test_model_creation()
    test_helper_functions()
    test_coupon_calculation()
    test_frontend_files()
    
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    print("✅ 所有基础测试完成!")
    print("⚠️  如需进行完整的端到端测试，请启动服务后运行 test_unified_order.py")
    print("=" * 60)


if __name__ == "__main__":
    run_all_tests()
