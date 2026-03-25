"""
Test Script - Unified Order System
统一订单系统功能测试脚本
"""
import sys
sys.path.append('backend')

import requests
from datetime import datetime

BASE_URL = "http://localhost:8000"

def test_unified_order_system():
    """测试统一订单系统核心功能"""
    
    print("\n" + "=" * 60)
    print("统一订单系统功能测试")
    print("=" * 60)
    
    # 1. 登录获取 token
    print("\n[1] 登录管理员账号...")
    login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "name": "admin",
        "password": "admin123"
    })
    
    if login_response.status_code != 200:
        print(f"❌ 登录失败：{login_response.text}")
        return
    
    token = login_response.json()["access_token"]
    print("✅ 登录成功")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # 2. 获取产品列表
    print("\n[2] 获取产品列表...")
    products_response = requests.get(f"{BASE_URL}/api/products?active_only=true")
    
    if products_response.status_code != 200:
        print(f"❌ 获取产品失败：{products_response.text}")
        return
    
    products = products_response.json()
    if not products:
        print("❌ 没有可用产品")
        return
    
    print(f"✅ 找到 {len(products)} 个产品")
    for p in products:
        print(f"   - ID:{p['id']} {p['name']}({p['specification']}) ¥{p['price']} 库存:{p['stock']}")
    
    # 选择第一个产品进行测试
    test_product = products[0]
    product_id = test_product['id']
    
    # 3. 获取用户列表
    print("\n[3] 获取用户列表...")
    users_response = requests.get(f"{BASE_URL}/api/users", headers=headers)
    
    if users_response.status_code != 200:
        print(f"❌ 获取用户失败：{users_response.text}")
        return
    
    users = users_response.json()
    if not users:
        print("❌ 没有可用用户")
        return
    
    print(f"✅ 找到 {len(users)} 个用户")
    test_user = users[0]
    user_id = test_user['id']
    print(f"   测试用户：{test_user['name']} (ID: {user_id})")
    
    # 4. 创建领水订单 (先用后付模式)
    print("\n[4] 测试：创建先用后付订单...")
    pickup_request = {
        "product_id": product_id,
        "quantity": 5,
        "preferred_payment": "credit"
    }
    
    order_response = requests.post(
        f"{BASE_URL}/api/unified/pickup",
        json=pickup_request,
        headers=headers
    )
    
    if order_response.status_code == 200:
        order_data = order_response.json()
        print("✅ 订单创建成功")
        print(f"   订单号：{order_data['order']['order_no']}")
        print(f"   支付方式：{order_data['order']['payment_method']}")
        print(f"   总金额：¥{order_data['order']['total_amount']}")
        print(f"   推荐说明：{order_data['recommendation'].get('reason', 'N/A')}")
        
        order_id = order_data['order']['id']
        
        # 5. 支付订单
        print("\n[5] 测试：支付订单...")
        pay_response = requests.post(
            f"{BASE_URL}/api/unified/orders/{order_id}/pay",
            json={"use_coupon": False},
            headers=headers
        )
        
        if pay_response.status_code == 200:
            pay_data = pay_response.json()
            print("✅ 支付成功")
            print(f"   支付方式：{pay_data['payment_method']}")
            print(f"   金额：¥{pay_data['amount']}")
        else:
            print(f"❌ 支付失败：{pay_response.text}")
    else:
        print(f"❌ 创建订单失败：{order_response.text}")
    
    # 6. 查询订单列表
    print("\n[6] 查询订单列表...")
    orders_response = requests.get(
        f"{BASE_URL}/api/unified/orders",
        headers=headers
    )
    
    if orders_response.status_code == 200:
        orders_data = orders_response.json()
        print(f"✅ 找到 {orders_data.get('total', 0)} 个订单")
        if orders_data.get('orders'):
            for order in orders_data['orders'][:3]:
                print(f"   - {order['order_no']} ¥{order['total_amount']} ({order['payment_method']})")
    else:
        print(f"❌ 查询订单失败：{orders_response.text}")
    
    # 7. 查询交易记录
    print("\n[7] 查询交易记录...")
    transactions_response = requests.get(
        f"{BASE_URL}/api/unified/transactions",
        headers=headers
    )
    
    if transactions_response.status_code == 200:
        trans_data = transactions_response.json()
        print(f"✅ 找到 {trans_data.get('total', 0)} 条交易记录")
        if trans_data.get('transactions'):
            for trans in trans_data['transactions'][:3]:
                print(f"   - {trans['created_at']} ¥{trans['actual_amount']} ({trans['payment_method']})")
    else:
        print(f"❌ 查询交易失败：{transactions_response.text}")
    
    print("\n" + "=" * 60)
    print("测试完成!")
    print("=" * 60)


if __name__ == "__main__":
    try:
        test_unified_order_system()
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误：{str(e)}")
        import traceback
        traceback.print_exc()
