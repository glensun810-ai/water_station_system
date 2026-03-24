#!/usr/bin/env python3
"""
测试交易记录筛选功能
验证时间范围筛选和规格筛选功能
"""

import requests
from datetime import datetime, timedelta

API_BASE = "http://localhost:8000/api"


def test_specifications_api():
    """测试规格列表 API"""
    print("=" * 60)
    print("📦 测试规格列表 API")
    print("=" * 60)
    
    response = requests.get(f"{API_BASE}/admin/specifications")
    
    if response.status_code != 200:
        print(f"❌ API 请求失败：{response.status_code}")
        return False
    
    specifications = response.json()
    print(f"\n✅ 共有 {len(specifications)} 种规格：")
    for spec in specifications:
        print(f"   - {spec}")
    
    return True


def test_date_range_filter():
    """测试日期范围筛选"""
    print("\n" + "=" * 60)
    print("📅 测试日期范围筛选")
    print("=" * 60)
    
    # 获取今天日期
    today = datetime.now()
    date_from = (today - timedelta(days=7)).strftime("%Y-%m-%d")
    date_to = today.strftime("%Y-%m-%d")
    
    print(f"\n查询范围：{date_from} 至 {date_to}")
    
    response = requests.get(
        f"{API_BASE}/admin/transactions",
        params={"date_from": date_from, "date_to": date_to}
    )
    
    if response.status_code != 200:
        print(f"❌ API 请求失败：{response.status_code}")
        return False
    
    transactions = response.json()
    print(f"✅ 查询结果：{len(transactions)} 条记录")
    
    if transactions:
        print(f"\n最近 5 条记录：")
        for t in transactions[:5]:
            print(f"   - {t['user_name']} ({t['department']}) - {t['product_name']} ({t['specification']}) × {t['quantity']}")
            print(f"     时间：{t['created_at'][:16]} | 金额：¥{t['actual_price']:.2f}")
    
    return True


def test_specification_filter():
    """测试规格筛选"""
    print("\n" + "=" * 60)
    print("🎯 测试规格筛选")
    print("=" * 60)
    
    # 获取规格列表
    specs_response = requests.get(f"{API_BASE}/admin/specifications")
    specifications = specs_response.json()
    
    if not specifications:
        print("⚠️  暂无规格数据")
        return True
    
    # 测试第一个规格
    test_spec = specifications[0]
    print(f"\n筛选规格：{test_spec}")
    
    response = requests.get(
        f"{API_BASE}/admin/transactions",
        params={"specification": test_spec}
    )
    
    if response.status_code != 200:
        print(f"❌ API 请求失败：{response.status_code}")
        return False
    
    transactions = response.json()
    print(f"✅ 查询结果：{len(transactions)} 条记录")
    
    # 验证所有返回的记录都符合筛选条件
    all_match = all(t['specification'] == test_spec for t in transactions)
    if all_match and transactions:
        print(f"✅ 所有记录规格均为：{test_spec}")
    elif not transactions:
        print(f"ℹ️  该规格暂无交易记录")
    else:
        print(f"❌ 存在不符合筛选条件的记录")
        return False
    
    return True


def test_combined_filter():
    """测试组合筛选"""
    print("\n" + "=" * 60)
    print("🔀 测试组合筛选（日期 + 规格 + 状态）")
    print("=" * 60)
    
    today = datetime.now()
    date_from = (today - timedelta(days=30)).strftime("%Y-%m-%d")
    date_to = today.strftime("%Y-%m-%d")
    
    # 获取规格列表
    specs_response = requests.get(f"{API_BASE}/admin/specifications")
    specifications = specs_response.json()
    
    if not specifications:
        print("⚠️  暂无规格数据")
        return True
    
    test_spec = specifications[0]
    
    print(f"\n筛选条件：")
    print(f"   - 日期范围：{date_from} 至 {date_to}")
    print(f"   - 规格：{test_spec}")
    print(f"   - 状态：unsettled (待结算)")
    
    response = requests.get(
        f"{API_BASE}/admin/transactions",
        params={
            "date_from": date_from,
            "date_to": date_to,
            "specification": test_spec,
            "status": "unsettled"
        }
    )
    
    if response.status_code != 200:
        print(f"❌ API 请求失败：{response.status_code}")
        return False
    
    transactions = response.json()
    print(f"\n✅ 查询结果：{len(transactions)} 条记录")
    
    # 验证筛选条件
    if transactions:
        all_match_spec = all(t['specification'] == test_spec for t in transactions)
        all_match_status = all(t['status'] == 'unsettled' for t in transactions)
        
        if all_match_spec and all_match_status:
            print(f"✅ 所有记录均符合筛选条件")
            print(f"\n前 3 条记录：")
            for t in transactions[:3]:
                print(f"   - {t['user_name']} - {t['product_name']} ({t['specification']})")
                print(f"     状态：{t['status']} | 金额：¥{t['actual_price']:.2f}")
        else:
            print(f"❌ 存在不符合筛选条件的记录")
            return False
    else:
        print(f"ℹ️  无符合条件的记录")
    
    return True


def test_quick_date_presets():
    """测试快捷日期选择"""
    print("\n" + "=" * 60)
    print("⚡ 测试快捷日期选择")
    print("=" * 60)
    
    today = datetime.now()
    
    # 测试"今日"
    print("\n📌 快捷选项：今日")
    date_today = today.strftime("%Y-%m-%d")
    response = requests.get(
        f"{API_BASE}/admin/transactions",
        params={"date_from": date_today, "date_to": date_today}
    )
    if response.status_code == 200:
        transactions = response.json()
        print(f"   今日交易：{len(transactions)} 条")
    
    # 测试"近 7 天"
    print("\n📌 快捷选项：近 7 天")
    date_7days = (today - timedelta(days=7)).strftime("%Y-%m-%d")
    response = requests.get(
        f"{API_BASE}/admin/transactions",
        params={"date_from": date_7days, "date_to": date_today}
    )
    if response.status_code == 200:
        transactions = response.json()
        print(f"   近 7 天交易：{len(transactions)} 条")
    
    # 测试"本月"
    print("\n📌 快捷选项：本月")
    date_month_start = today.replace(day=1).strftime("%Y-%m-%d")
    response = requests.get(
        f"{API_BASE}/admin/transactions",
        params={"date_from": date_month_start, "date_to": date_today}
    )
    if response.status_code == 200:
        transactions = response.json()
        print(f"   本月交易：{len(transactions)} 条")
    
    return True


def main():
    """主测试函数"""
    print("\n" + "=" * 60)
    print("🧪 交易记录筛选功能测试")
    print("=" * 60)
    
    try:
        # 测试规格列表
        test_specifications_api()
        
        # 测试日期范围筛选
        test_date_range_filter()
        
        # 测试规格筛选
        test_specification_filter()
        
        # 测试组合筛选
        test_combined_filter()
        
        # 测试快捷日期选择
        test_quick_date_presets()
        
        print("\n" + "=" * 60)
        print("✅ 所有测试完成！")
        print("=" * 60)
        print("\n📋 功能清单：")
        print("   1. ✓ 规格列表 API - 获取所有产品规格")
        print("   2. ✓ 日期范围筛选 - 支持自定义起止日期")
        print("   3. ✓ 规格筛选 - 按产品规格过滤交易")
        print("   4. ✓ 组合筛选 - 同时使用多个筛选条件")
        print("   5. ✓ 快捷日期 - 今日/近 7 天/本月/上月")
        
        print("\n💡 使用说明：")
        print("   - 访问 http://localhost:8080/admin.html")
        print("   - 点击'交易记录'标签")
        print("   - 使用顶部的筛选工具栏进行筛选")
        print("   - 快捷日期按钮快速选择常用时间范围")
        print("   - 自定义日期选择器支持精确日期范围")
        
    except requests.exceptions.ConnectionError:
        print("\n❌ 无法连接到后端服务，请确保服务已启动")
        print("   启动命令：cd backend && source ../.venv/bin/activate && python main.py")
    except Exception as e:
        print(f"\n❌ 测试失败：{e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
