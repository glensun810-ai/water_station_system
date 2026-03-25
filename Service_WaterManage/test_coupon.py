"""
Test Script - Coupon System
优惠券系统功能测试脚本
"""
import sys
sys.path.append('backend')

import requests
from datetime import datetime

BASE_URL = "http://localhost:8000"

def test_coupon_system():
    """测试优惠券系统核心功能"""
    
    print("\n" + "=" * 60)
    print("优惠券系统功能测试")
    print("=" * 60)
    
    # 1. 登录获取 token (管理员)
    print("\n[1] 登录管理员账号...")
    login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "name": "admin",
        "password": "admin123"
    })
    
    if login_response.status_code != 200:
        print(f"❌ 登录失败：{login_response.text}")
        return
    
    admin_token = login_response.json()["access_token"]
    print("✅ 管理员登录成功")
    
    admin_headers = {
        "Authorization": f"Bearer {admin_token}",
        "Content-Type": "application/json"
    }
    
    # 2. 创建折扣券 (95 折)
    print("\n[2] 创建折扣券 (95 折，满 100 可用)...")
    discount_coupon = {
        "name": "春日特惠 95 折券",
        "type": "discount",
        "value": 95,
        "min_amount": 100.0,
        "max_discount": 50.0,  # 最大优惠 50 元
        "applicable_modes": ["prepaid", "credit"],  # 两种模式都可用
        "valid_days": 30,
        "total_quantity": 100
    }
    
    create_response = requests.post(
        f"{BASE_URL}/api/coupons",
        json=discount_coupon,
        headers=admin_headers
    )
    
    if create_response.status_code == 200:
        coupon_data = create_response.json()
        print("✅ 优惠券创建成功")
        print(f"   优惠券码：{coupon_data['coupon']['coupon_code']}")
        print(f"   类型：{coupon_data['coupon']['type']}")
        print(f"   价值：{coupon_data['coupon']['value']}%")
        
        coupon_id = coupon_data['coupon']['id']
        coupon_code = coupon_data['coupon']['coupon_code']
    else:
        print(f"❌ 创建优惠券失败：{create_response.text}")
        return
    
    # 3. 创建满减券 (满 200 减 20)
    print("\n[3] 创建满减券 (满 200 减 20)...")
    fixed_coupon = {
        "name": "满 200 减 20 券",
        "type": "fixed",
        "value": 20,
        "min_amount": 200.0,
        "applicable_modes": ["prepaid"],  # 仅限预付模式
        "valid_days": 15,
        "total_quantity": 50
    }
    
    create_fixed_response = requests.post(
        f"{BASE_URL}/api/coupons",
        json=fixed_coupon,
        headers=admin_headers
    )
    
    if create_fixed_response.status_code == 200:
        fixed_data = create_fixed_response.json()
        print("✅ 满减券创建成功")
        print(f"   优惠券码：{fixed_data['coupon']['coupon_code']}")
    else:
        print(f"❌ 创建满减券失败：{create_fixed_response.text}")
    
    # 4. 查询优惠券列表
    print("\n[4] 查询优惠券列表...")
    list_response = requests.get(
        f"{BASE_URL}/api/coupons",
        headers=admin_headers
    )
    
    if list_response.status_code == 200:
        coupons_data = list_response.json()
        print(f"✅ 找到 {coupons_data['total']} 个优惠券")
        for c in coupons_data['coupons'][:3]:
            print(f"   - {c['name']} ({c['type']}) 剩余：{c['total_quantity'] - c['issued_quantity']}")
    else:
        print(f"❌ 查询优惠券失败：{list_response.text}")
    
    # 5. 登录普通用户
    print("\n[5] 登录普通用户账号...")
    user_login = requests.post(f"{BASE_URL}/api/auth/login", json={
        "name": "张三",
        "password": "admin123"
    })
    
    if user_login.status_code != 200:
        print("⚠️  用户'张三'不存在，尝试创建测试用户...")
        # 这里简化处理，实际应该先创建用户
        print("跳过用户测试")
        return
    
    user_token = user_login.json()["access_token"]
    print("✅ 用户登录成功")
    
    user_headers = {
        "Authorization": f"Bearer {user_token}",
        "Content-Type": "application/json"
    }
    
    # 6. 向用户发放优惠券
    print(f"\n[6] 向用户发放优惠券...")
    issue_request = {
        "user_ids": [2],  # 假设用户 ID 为 2
        "coupon_id": coupon_id
    }
    
    issue_response = requests.post(
        f"{BASE_URL}/api/coupons/issue",
        json=issue_request,
        headers=admin_headers
    )
    
    if issue_response.status_code == 200:
        issue_data = issue_response.json()
        print(f"✅ {issue_data['message']}")
    else:
        print(f"❌ 发放优惠券失败：{issue_response.text}")
    
    # 7. 用户查询我的优惠券
    print("\n[7] 查询我的优惠券...")
    my_coupons_response = requests.get(
        f"{BASE_URL}/api/coupons/my",
        headers=user_headers
    )
    
    if my_coupons_response.status_code == 200:
        my_coupons_data = my_coupons_response.json()
        print(f"✅ 我有 {my_coupons_data['total']} 张优惠券")
        for uc in my_coupons_data['coupons']:
            coupon_info = uc.get('coupon', {})
            print(f"   - {coupon_info.get('name')} ({coupon_info.get('type')}) 过期：{uc['expires_at']}")
    else:
        print(f"❌ 查询我的优惠券失败：{my_coupons_response.text}")
    
    # 8. 计算最优优惠券
    print("\n[8] 计算最优优惠券 (订单金额 150 元，预付模式)...")
    calculate_request = {
        "order_amount": 150.0,
        "payment_method": "prepaid",
        "product_id": 1
    }
    
    calculate_response = requests.post(
        f"{BASE_URL}/api/coupons/calculate-best",
        json=calculate_request,
        headers=user_headers
    )
    
    if calculate_response.status_code == 200:
        calc_data = calculate_response.json()
        if calc_data['recommended_coupon']:
            print("✅ 推荐优惠券:")
            print(f"   名称：{calc_data['recommended_coupon']['name']}")
            print(f"   类型：{calc_data['recommended_coupon']['type']}")
            print(f"   折扣金额：¥{calc_data['discount_amount']}")
            print(f"   最终金额：¥{calc_data['final_amount']}")
        else:
            print(f"ℹ️  {calc_data.get('message', '没有可用的优惠券')}")
    else:
        print(f"❌ 计算最优优惠券失败：{calculate_response.text}")
    
    print("\n" + "=" * 60)
    print("测试完成!")
    print("=" * 60)


if __name__ == "__main__":
    try:
        test_coupon_system()
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误：{str(e)}")
        import traceback
        traceback.print_exc()
