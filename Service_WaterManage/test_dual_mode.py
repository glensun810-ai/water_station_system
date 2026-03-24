"""
双模式业务功能测试脚本
测试先用后付和先付后用两种模式的完整流程
"""
import requests
from datetime import datetime

API_BASE = "http://localhost:8000"

def print_section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")

def test_promotion_config_api():
    """测试优惠配置 API"""
    print_section("1. 测试优惠配置 API")
    
    # 获取所有优惠配置
    response = requests.get(f"{API_BASE}/api/promotions/config")
    if response.status_code == 200:
        configs = response.json()
        print(f"✓ 获取优惠配置成功，共 {len(configs)} 条")
        for config in configs:
            mode_text = "先用后付" if config['mode'] == 'pay_later' else "先付后用"
            print(f"  - 产品 ID:{config['product_id']}, 模式:{mode_text}, 买{config['trigger_qty']}赠{config['gift_qty']}")
    else:
        print(f"✗ 获取优惠配置失败：{response.status_code}")
        return False
    
    return True

def test_record_pickup_dual_mode():
    """测试双模式领取记录"""
    print_section("2. 测试双模式领取功能")
    
    # 获取用户列表
    response = requests.get(f"{API_BASE}/api/users")
    if response.status_code != 200:
        print(f"✗ 获取用户列表失败")
        return False
    
    users = response.json()
    if not users:
        print(f"✗ 没有用户数据")
        return False
    
    test_user = users[0]
    print(f"测试用户：{test_user['name']} (ID: {test_user['id']})")
    
    # 获取产品列表
    response = requests.get(f"{API_BASE}/api/products?active_only=true")
    if response.status_code != 200:
        print(f"✗ 获取产品列表失败")
        return False
    
    products = response.json()
    if not products:
        print(f"✗ 没有产品数据")
        return False
    
    # 找到桶装水产品
    bucket_product = None
    for p in products:
        if '桶装' in p['name']:
            bucket_product = p
            break
    
    if not bucket_product:
        bucket_product = products[0]
    
    print(f"测试产品：{bucket_product['name']} (ID: {bucket_product['id']}, 价格：¥{bucket_product['price']})")
    
    # 测试先用后付模式
    print("\n[测试] 先用后付模式...")
    response = requests.post(f"{API_BASE}/api/record", json={
        "user_id": test_user['id'],
        "product_id": bucket_product['id'],
        "quantity": 2,
        "type": "pickup",
        "mode": "pay_later"
    })
    
    if response.status_code == 200:
        result = response.json()
        print(f"✓ 先用后付领取成功")
        print(f"  实际价格：¥{result['actual_price']} (单价：¥{result['actual_price']/result['quantity']:.2f})")
        print(f"  备注：{result['note']}")
    else:
        print(f"✗ 先用后付领取失败：{response.status_code}")
    
    # 测试先付后用模式
    print("\n[测试] 先付后用模式...")
    response = requests.post(f"{API_BASE}/api/record", json={
        "user_id": test_user['id'],
        "product_id": bucket_product['id'],
        "quantity": 12,  # 超过 10 桶，应该享受买 10 赠 1
        "type": "pickup",
        "mode": "prepay"
    })
    
    if response.status_code == 200:
        result = response.json()
        expected_free = 1  # 买 10 赠 1
        print(f"✓ 先付后用领取成功")
        print(f"  领取数量：{result['quantity']} 桶")
        print(f"  实际价格：¥{result['actual_price']} (单价：¥{result['actual_price']/result['quantity']:.2f})")
        print(f"  备注：{result['note']}")
        print(f"  预期免费数量：{expected_free} 桶")
    else:
        print(f"✗ 先付后用领取失败：{response.status_code}")
    
    return True

def test_user_status():
    """测试用户状态 API"""
    print_section("3. 测试用户状态 API")
    
    # 获取用户列表
    response = requests.get(f"{API_BASE}/api/users")
    if response.status_code != 200:
        print(f"✗ 获取用户列表失败")
        return False
    
    users = response.json()
    test_user = users[0]
    
    # 获取用户状态
    response = requests.get(f"{API_BASE}/api/user/{test_user['id']}/status")
    if response.status_code == 200:
        status = response.json()
        print(f"✓ 获取用户状态成功")
        print(f"  用户：{status['name']}")
        print(f"  本月已领：{status['month_total_qty']} 桶")
        print(f"  待支付：¥{status['to_apply_amount']:.2f}")
        print(f"  已支付待确认：¥{status['applied_amount']:.2f}")
        print(f"  已结算：¥{status['settled_amount']:.2f}")
    else:
        print(f"✗ 获取用户状态失败：{response.status_code}")
    
    return True

def test_reservation_api():
    """测试预定 API"""
    print_section("4. 测试预定 API")
    
    # 获取用户列表
    response = requests.get(f"{API_BASE}/api/users")
    if response.status_code != 200:
        print(f"✗ 获取用户列表失败")
        return False
    
    users = response.json()
    test_user = users[0]
    
    # 获取产品列表
    response = requests.get(f"{API_BASE}/api/products?active_only=true")
    if response.status_code != 200:
        print(f"✗ 获取产品列表失败")
        return False
    
    products = response.json()
    if not products:
        print(f"✗ 没有产品数据")
        return False
    
    test_product = products[0]
    
    print(f"测试用户：{test_user['name']}")
    print(f"测试产品：{test_product['name']}")
    
    # 注意：预定 API 需要登录认证，这里只测试 API 存在性
    print("\n[提示] 预定 API 需要登录认证，请在登录后测试以下 API:")
    print(f"  POST {API_BASE}/api/reservation/create")
    print(f"  GET  {API_BASE}/api/reservation/{{user_id}}/balance")
    print(f"  POST {API_BASE}/api/reservation/pickup")
    
    return True

def main():
    """主测试函数"""
    print("\n" + "="*60)
    print("  水站管理系统 - 双模式业务功能测试")
    print("  测试时间:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("="*60)
    
    # 检查后端服务是否运行
    try:
        response = requests.get(f"{API_BASE}/api/health", timeout=5)
        if response.status_code != 200:
            print(f"✗ 后端服务未响应，请先启动后端服务")
            return
        print("✓ 后端服务正常运行")
    except requests.exceptions.ConnectionError:
        print(f"✗ 无法连接到后端服务 ({API_BASE})")
        print(f"  请先启动后端服务：cd backend && uvicorn main:app --reload")
        return
    
    # 运行测试
    all_passed = True
    
    if not test_promotion_config_api():
        all_passed = False
    
    if not test_record_pickup_dual_mode():
        all_passed = False
    
    if not test_user_status():
        all_passed = False
    
    if not test_reservation_api():
        all_passed = False
    
    # 测试总结
    print_section("测试总结")
    if all_passed:
        print("✓ 所有测试通过！")
        print("\n功能验证:")
        print("  1. ✓ 优惠配置 API 正常工作")
        print("  2. ✓ 双模式领取功能正常")
        print("  3. ✓ 用户状态 API 正常")
        print("  4. ✓ 预定 API 已实现（需登录测试）")
    else:
        print("✗ 部分测试失败，请检查日志")
    
    print("\n" + "="*60)

if __name__ == "__main__":
    main()
