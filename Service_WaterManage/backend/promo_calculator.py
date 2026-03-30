"""
买 N 赠 M 优惠计算器

正确逻辑（按周期计算）：
- 买 10 赠 1：每 11 件为一个周期，其中 10 件付费，1 件免费
  - 数量 1-10：付费 1-10，免费 0
  - 数量 11：付费 10，免费 1（完整周期）
  - 数量 12：付费 11，免费 1（12=11+1，第一个周期 10+1，第二周期 1 件付费）
  - 数量 22：付费 20，免费 2（2 个完整周期）
  - 数量 23：付费 21，免费 2（23=22+1，两个周期 20+2，第三周期 1 件付费）

计算公式：
周期长度 = 买 N + 赠 M
完整周期数 = floor(数量 / 周期长度)
免费数量 = 完整周期数 × 赠 M
剩余数量 = 数量 % 周期长度
付费数量 = (完整周期数 × 买 N) + min(剩余数量，买 N)
"""

from typing import Dict


def calculate_promo_amount(
    quantity: int,
    unit_price: float,
    promo_threshold: int = 0,
    promo_gift: int = 0
) -> Dict:
    """
    计算买 N 赠 M 优惠后的金额
    """
    # 无优惠配置或不满足优惠条件
    if promo_threshold <= 0 or promo_gift <= 0 or quantity < promo_threshold:
        return {
            'quantity': quantity,
            'paid_qty': quantity,
            'free_qty': 0,
            'unit_price': unit_price,
            'total_amount': unit_price * quantity,
            'original_amount': unit_price * quantity,
            'savings': 0,
            'discount_desc': '标准价格'
        }
    
    # 每个周期的总数量（买 N + 赠 M）
    cycle_length = promo_threshold + promo_gift
    
    # 计算完整周期数
    full_cycles = quantity // cycle_length
    
    # 计算剩余数量
    remainder = quantity % cycle_length
    
    # 免费数量 = 完整周期数 × 赠 M
    free_qty = full_cycles * promo_gift
    
    # 付费数量 = (完整周期数 × 买 N) + min(剩余数量，买 N)
    paid_qty = (full_cycles * promo_threshold) + min(remainder, promo_threshold)
    
    # 计算金额
    total_amount = paid_qty * unit_price
    original_amount = quantity * unit_price
    savings = original_amount - total_amount
    
    # 构建优惠描述
    if free_qty > 0:
        discount_desc = f'买{promo_threshold}赠{promo_gift}: {free_qty}件免费'
    else:
        discount_desc = f'买{promo_threshold}赠{promo_gift}优惠中'
    
    return {
        'quantity': quantity,
        'paid_qty': paid_qty,
        'free_qty': free_qty,
        'unit_price': unit_price,
        'total_amount': total_amount,
        'original_amount': original_amount,
        'savings': savings,
        'discount_desc': discount_desc
    }


# 测试
if __name__ == '__main__':
    print("测试买 10 赠 1 优惠计算（周期算法）：")
    print("=" * 60)
    
    # 正确的测试用例（按周期算法）
    test_cases = [
        (10, 150.0, 0, "未满 10 件，无优惠"),
        (11, 150.0, 1, "刚好 1 个周期：10 付费 +1 免费"),
        (12, 165.0, 1, "1 个周期 +1 件：10+1 付费 +1 免费"),
        (20, 285.0, 1, "1 个周期 +9 件：10+9 付费 +1 免费"),
        (21, 300.0, 1, "1 个周期 +10 件：10+10 付费 +1 免费"),
        (22, 300.0, 2, "2 个周期：20 付费 +2 免费"),
        (33, 450.0, 3, "3 个周期：30 付费 +3 免费"),
    ]
    
    all_passed = True
    for qty, expected_amount, expected_free, description in test_cases:
        result = calculate_promo_amount(qty, 15.0, 10, 1)
        passed = (result['total_amount'] == expected_amount and 
                  result['free_qty'] == expected_free)
        status = "✅" if passed else "❌"
        print(f"{status} 数量{qty}: {description}")
        if not passed:
            print(f"   实际：付费{result['paid_qty']}件，免费{result['free_qty']}件，金额{result['total_amount']}元")
            print(f"   期望：免费{expected_free}件，金额{expected_amount}元")
            all_passed = False
    
    print("=" * 60)
    
    # 测试买 20 赠 2
    print("\n测试买 20 赠 2 优惠计算：")
    print("=" * 60)
    
    result = calculate_promo_amount(22, 10.0, 20, 2)
    print(f"数量 22: 付费{result['paid_qty']}件，免费{result['free_qty']}件，金额{result['total_amount']}元")
    assert result['free_qty'] == 2 and result['total_amount'] == 200.0, "买 20 赠 2 测试失败"
    print("✅ 买 20 赠 2 测试通过")
    
    print("=" * 60)
    
    if all_passed:
        print("\n✅ 所有测试通过！")
    else:
        print("\n❌ 部分测试失败")
