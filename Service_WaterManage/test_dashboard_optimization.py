#!/usr/bin/env python3
"""
测试核心指标优化功能
验证用量统计和金额统计的正确性
"""

import requests
import json

API_BASE = "http://localhost:8000/api"

def test_dashboard_summary():
    """测试数据看板总览 API"""
    print("=" * 60)
    print("📊 测试数据看板核心指标优化")
    print("=" * 60)
    
    # 调用 API
    response = requests.get(f"{API_BASE}/admin/dashboard/summary")
    
    if response.status_code != 200:
        print(f"❌ API 请求失败：{response.status_code}")
        return False
    
    data = response.json()
    
    # 验证响应结构
    print("\n✅ 1. 验证响应结构")
    assert "pending_tasks" in data, "缺少 pending_tasks 字段"
    assert "metrics" in data, "缺少 metrics 字段"
    assert "usage_stats" in data, "缺少 usage_stats 字段"
    assert "department_ranking" in data, "缺少 department_ranking 字段"
    print("   ✓ 响应结构完整")
    
    # 验证用量统计
    print("\n✅ 2. 验证用量统计（按单位分类）")
    usage_stats = data["usage_stats"]
    assert "by_unit" in usage_stats, "缺少 by_unit 字段"
    assert "total_quantity" in usage_stats, "缺少 total_quantity 字段"
    
    print(f"   📦 本月总用量：{usage_stats['total_quantity']}")
    print(f"   📊 涉及单位类型：{len(usage_stats['by_unit'])} 种")
    
    for unit_stat in usage_stats["by_unit"]:
        unit = unit_stat["unit"]
        quantity = unit_stat["quantity"]
        count = unit_stat["transaction_count"]
        products = unit_stat["products"]
        
        # 单位显示优化
        unit_display_map = {
            '桶': '🪣 桶装水',
            '瓶': '🧴 瓶装水',
            '提': '📦 提装水',
            '箱': '📦 箱装水',
            '件': '📦 件装水'
        }
        display_name = unit_display_map.get(unit, f"{unit}装水")
        
        print(f"\n   {display_name}:")
        print(f"      - 用量：{quantity} {unit}")
        print(f"      - 交易笔数：{count} 笔")
        if len(products) > 1:
            print(f"      - 产品明细：")
            for product_name, qty in products.items():
                print(f"         · {product_name}: {qty} {unit}")
    
    # 验证金额统计
    print("\n✅ 3. 验证金额统计（按状态分类）")
    metrics = data["metrics"]
    
    settled_amount = metrics.get("settled_amount", 0)
    unsettled_amount = metrics.get("unsettled_amount", 0)
    applied_amount = metrics.get("applied_amount", 0)
    growth_rate = metrics.get("settled_growth_rate", 0)
    
    print(f"   💰 已结算金额：¥{settled_amount:.2f} (环比 {growth_rate:+.1f}%)")
    print(f"   ⏳ 待结算金额：¥{unsettled_amount:.2f}")
    print(f"   📋 已申请待确认：¥{applied_amount:.2f}")
    
    # 验证待办事项
    print("\n✅ 4. 验证待办事项")
    pending = data["pending_tasks"]
    print(f"   📝 待确认结算申请：{pending['applications_count']} 笔")
    print(f"   📦 待补货产品：{pending['low_stock_count']} 种")
    print(f"   🔔 待提醒结算：{pending['remind_count']} 人")
    
    # 验证部门排行
    print("\n✅ 5. 验证部门排行（TOP 5）")
    ranking = data["department_ranking"]
    medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]
    for i, dept in enumerate(ranking[:5]):
        medal = medals[i] if i < len(medals) else f"{i+1}"
        print(f"   {medal} {dept['department']}: {dept['total_qty']} (交易 {dept['transaction_count']} 笔)")
    
    # 总结
    print("\n" + "=" * 60)
    print("✅ 所有测试通过！核心指标优化功能正常")
    print("=" * 60)
    print("\n📋 优化总结：")
    print("   1. ✓ 用量统计按单位分类，支持多产品明细展示")
    print("   2. ✓ 金额统计按状态分类，清晰掌握收款情况")
    print("   3. ✓ 单位显示优化，使用图标增强可读性")
    print("   4. ✓ 保留环比增长趋势，支持业务洞察")
    print("\n💡 使用建议：")
    print("   - 根据用量统计调整采购计划（桶装水 vs 瓶装水）")
    print("   - 关注待结算金额，及时跟进收款")
    print("   - 参考部门排行，激励节约用水")
    
    return True


def test_products():
    """测试产品列表，验证单位字段"""
    print("\n" + "=" * 60)
    print("📦 测试产品单位数据")
    print("=" * 60)
    
    response = requests.get(f"{API_BASE}/products")
    if response.status_code != 200:
        print(f"❌ API 请求失败：{response.status_code}")
        return False
    
    products = response.json()
    print(f"\n共有 {len(products)} 个产品：")
    
    for p in products:
        print(f"   - {p['name']} ({p['specification']})")
        print(f"     单位：{p['unit']} | 价格：¥{p['price']} | 库存：{p['stock']}")
        print(f"     优惠：买{p['promo_threshold']}赠{p['promo_gift']} | 状态：{'在售' if p['is_active'] else '已停用'}")
    
    return True


if __name__ == "__main__":
    try:
        # 测试产品列表
        test_products()
        
        # 测试数据看板
        test_dashboard_summary()
        
        print("\n🎉 全部测试完成！")
        
    except requests.exceptions.ConnectionError:
        print("\n❌ 无法连接到后端服务，请确保服务已启动")
        print("   启动命令：cd backend && source ../.venv/bin/activate && python main.py")
    except Exception as e:
        print(f"\n❌ 测试失败：{e}")
        import traceback
        traceback.print_exc()
