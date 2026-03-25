"""
Test Buy-Gift Logic - 买赠优惠计算测试
验证买 N 赠 M 的计算逻辑是否正确
"""
import sys
sys.path.append('backend')

from main import get_db
from api_unified_order import calculate_gift_quantity
from models_unified import PromotionConfig

def test_buy_gift_calculation():
    """测试买赠计算逻辑"""
    
    print("\n" + "=" * 60)
    print("买赠优惠计算逻辑测试")
    print("=" * 60)
    
    # 创建测试配置：买 10 赠 1
    config = PromotionConfig(
        product_id=1,
        promotion_type='prepaid',
        trigger_qty=10,  # 买 10
        gift_qty=1,      # 赠 1
        is_active=True
    )
    
    print("\n优惠配置：买 10 赠 1")
    print("-" * 60)
    
    # 测试用例
    test_cases = [
        (5, 0),      # 5 桶：不赠送
        (9, 0),      # 9 桶：不赠送
        (10, 1),     # 10 桶：赠 1
        (11, 1),     # 11 桶：赠 1
        (15, 1),     # 15 桶：赠 1
        (19, 1),     # 19 桶：赠 1
        (20, 2),     # 20 桶：赠 2
        (25, 2),     # 25 桶：赠 2
        (29, 2),     # 29 桶：赠 2
        (30, 3),     # 30 桶：赠 3
        (50, 5),     # 50 桶：赠 5
        (99, 9),     # 99 桶：赠 9
        (100, 10),   # 100 桶：赠 10
    ]
    
    all_passed = True
    
    for quantity, expected_gift in test_cases:
        actual_gift = calculate_gift_quantity(quantity, config)
        
        # 计算预期结果
        expected_cycles = quantity // 10
        expected_gift_calculated = expected_cycles * 1
        
        status = "✅" if actual_gift == expected_gift else "❌"
        
        if actual_gift != expected_gift:
            all_passed = False
        
        print(f"{status} 数量：{quantity:3d} 桶 → 赠送：{actual_gift} 桶 (期望：{expected_gift} 桶，周期数：{expected_cycles})")
    
    print("\n" + "=" * 60)
    
    if all_passed:
        print("✅ 所有测试通过！买赠计算逻辑正确。")
    else:
        print("❌ 部分测试失败！请检查计算逻辑。")
    
    print("=" * 60)
    
    # 详细示例
    print("\n详细计算示例:")
    print("-" * 60)
    
    examples = [10, 15, 20, 25, 30]
    
    for qty in examples:
        gift = calculate_gift_quantity(qty, config)
        paid = qty - gift
        savings = gift * 10  # 假设单价 10 元
        
        print(f"\n购买 {qty} 桶:")
        print(f"  • 付费：{paid} 桶")
        print(f"  • 赠送：{gift} 桶")
        print(f"  • 总计：{qty} 桶")
        print(f"  • 节省：¥{savings}")
        print(f"  • 计算：{qty} ÷ {config.trigger_qty} = {qty // config.trigger_qty} 个周期 × {config.gift_qty} = 赠{gift}桶")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    test_buy_gift_calculation()
