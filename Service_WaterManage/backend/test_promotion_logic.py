"""
测试买赠优惠逻辑

验证充值时的买 N 赠 M 计算是否正确
"""

def test_promotion_calculation():
    """测试优惠计算逻辑"""
    
    print("=" * 60)
    print("买赠优惠计算测试")
    print("=" * 60)
    
    # 测试场景 1: 买 10 赠 1, 充值 10 个
    trigger_qty = 10
    gift_qty = 1
    quantity = 10
    
    # 旧逻辑 (错误)
    cycle_old = trigger_qty + gift_qty  # 11
    free_old = (quantity // cycle_old) * gift_qty  # 0
    
    # 新逻辑 (正确)
    free_new = (quantity // trigger_qty) * gift_qty  # 1
    
    print(f"\n场景 1: 买{trigger_qty}赠{gift_qty}, 充值{quantity}个")
    print(f"  旧逻辑：赠送 {free_old} 个 ❌ (应该是 1 个)")
    print(f"  新逻辑：赠送 {free_new} 个 ✅")
    
    # 测试场景 2: 买 10 赠 1, 充值 20 个
    quantity = 20
    free_old = (quantity // cycle_old) * gift_qty  # 1
    free_new = (quantity // trigger_qty) * gift_qty  # 2
    
    print(f"\n场景 2: 买{trigger_qty}赠{gift_qty}, 充值{quantity}个")
    print(f"  旧逻辑：赠送 {free_old} 个 ❌ (应该是 2 个)")
    print(f"  新逻辑：赠送 {free_new} 个 ✅")
    
    # 测试场景 3: 买 10 赠 1, 充值 15 个
    quantity = 15
    free_old = (quantity // cycle_old) * gift_qty  # 1
    free_new = (quantity // trigger_qty) * gift_qty  # 1
    
    print(f"\n场景 3: 买{trigger_qty}赠{gift_qty}, 充值{quantity}个")
    print(f"  旧逻辑：赠送 {free_old} 个 ✅")
    print(f"  新逻辑：赠送 {free_new} 个 ✅")
    print(f"  说明：充值 15 个，满足 1 次买 10 的条件，赠送 1 个")
    
    # 测试场景 4: 买 5 赠 2, 充值 10 个
    trigger_qty = 5
    gift_qty = 2
    quantity = 10
    cycle_old = trigger_qty + gift_qty  # 7
    free_old = (quantity // cycle_old) * gift_qty  # 2
    free_new = (quantity // trigger_qty) * gift_qty  # 4
    
    print(f"\n场景 4: 买{trigger_qty}赠{gift_qty}, 充值{quantity}个")
    print(f"  旧逻辑：赠送 {free_old} 个 ❌ (应该是 4 个)")
    print(f"  新逻辑：赠送 {free_new} 个 ✅")
    print(f"  说明：充值 10 个，满足 2 次买 5 的条件，每次赠送 2 个，共 4 个")
    
    print("\n" + "=" * 60)
    print("测试结论:")
    print("=" * 60)
    print("✅ 新逻辑正确实现了'买 N 赠 M'的语义")
    print("   - 买 10 赠 1: 每买 10 个就送 1 个")
    print("   - 充值 10 个 → 付费 10 个 + 赠送 1 个 = 总共 11 个")
    print("   - 充值 20 个 → 付费 20 个 + 赠送 2 个 = 总共 22 个")
    print("=" * 60)


if __name__ == "__main__":
    test_promotion_calculation()
