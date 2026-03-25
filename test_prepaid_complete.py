"""
预付充值系统集成测试
测试完整的业务流程
"""
import requests
import sys

BASE_URL = "http://localhost:8000/api/unified"


def test_full_flow():
    """测试完整流程"""
    print("=" * 60)
    print("  水站管理系统 - 预付充值系统集成测试")
    print("=" * 60)
    
    try:
        # 获取 token (假设已有管理员账户)
        print("\n1️⃣ 登录获取 Token")
        login_response = requests.post(f"{BASE_URL.replace('/api/unified', '/auth/login')}", json={
            "username": "admin",
            "password": "admin123"
        })
        
        if login_response.status_code != 200:
            print(f"⚠️  登录失败，使用空 token 继续测试")
            token = ""
        else:
            token = login_response.json().get("access_token", "")
            print(f"✓ 登录成功，Token: {token[:20]}...")
        
        headers = {'Authorization': f'Bearer {token}'} if token else {}
        
        user_id = 1
        product_id = 1
        
        # ========== 步骤 1: 查询当前余额 ==========
        print(f"\n2️⃣ 查询用户{user_id}的当前余额")
        response = requests.get(f"{BASE_URL}/user/{user_id}/balance", headers=headers)
        
        if response.status_code == 200:
            balance_data = response.json()
            if balance_data['products']:
                product_info = balance_data['products'][0]
                print(f"  产品：{product_info['product_name']}")
                
                if 'balance_detail' in product_info:
                    prepaid = product_info['balance_detail']['prepaid']
                    print(f"  ✓ 付费桶：{prepaid['paid']} 个")
                    print(f"  ✓ 赠送桶：{prepaid['gift']} 个")
                    print(f"  ✓ 总预付：{prepaid['total']} 个")
                else:
                    print(f"  ⚠️  未返回 balance_detail 信息")
            else:
                print(f"  暂无产品余额")
        else:
            print(f"  ❌ 查询失败：{response.text}")
        
        # ========== 步骤 2: 领取测试（如果有余额）==========
        print(f"\n3️⃣ 领取测试")
        
        # 先查询余额
        response = requests.get(f"{BASE_URL}/user/{user_id}/balance", headers=headers)
        if response.status_code == 200:
            balance_data = response.json()
            if balance_data['products']:
                prepaid_total = balance_data['products'][0].get('balance', {}).get('prepaid_available', 0)
                
                if prepaid_total > 0:
                    pickup_qty = min(1, prepaid_total)  # 领取 1 个
                    print(f"  尝试领取 {pickup_qty} 个...")
                    
                    response = requests.post(
                        f"{BASE_URL}/pickup/record",
                        headers=headers,
                        json={
                            "user_id": user_id,
                            "product_id": product_id,
                            "quantity": pickup_qty
                        }
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        print(f"  ✓ 领取成功!")
                        print(f"    消费明细:")
                        
                        for txn in result['transactions']:
                            print(f"    - 交易{txn['id']}: 数量{txn['quantity']}, "
                                  f"付费{txn['paid_qty_deducted']}, 赠送{txn['gift_qty_deducted']}, "
                                  f"金额¥{txn['financial_amount']}")
                    else:
                        print(f"  ❌ 领取失败：{response.json()}")
                else:
                    print(f"  ⚠️  余额不足，跳过领取测试")
            else:
                print(f"  ⚠️  无产品余额，跳过领取测试")
        
        # ========== 步骤 3: 查询交易记录 ==========
        print(f"\n4️⃣ 查询用户交易记录")
        response = requests.get(
            f"{BASE_URL}/transactions/{user_id}?limit=5",
            headers=headers
        )
        
        if response.status_code == 200:
            transactions = response.json()
            if transactions:
                print(f"  最近 5 条交易记录:")
                for txn in transactions[:5]:
                    print(f"  - 交易{txn['id']}: 模式{txn['mode']}, "
                          f"数量{txn['quantity']}, 金额¥{txn['actual_price']}, "
                          f"状态{txn['status']}")
            else:
                print(f"  暂无交易记录")
        else:
            print(f"  ❌ 查询失败：{response.text}")
        
        # ========== 步骤 4: 财务报表查询 ==========
        print(f"\n5️⃣ 查询财务报表")
        from datetime import datetime
        today = datetime.now().strftime('%Y-%m-%d')
        first_day = today[:7] + '-01'
        
        response = requests.get(
            f"{BASE_URL}/report/financial?date_from={first_day}&date_to={today}",
            headers=headers
        )
        
        if response.status_code == 200:
            report = response.json()
            print(f"  统计周期：{report['period']['date_from']} 至 {report['period']['date_to']}")
            
            if 'prepaid' in report:
                prepaid = report['prepaid']
                print(f"  先付后用 (预付):")
                print(f"    - 总领取量：{prepaid.get('total_qty', 0)} 桶")
                print(f"    - 总收入：¥{prepaid.get('total_amount', 0):.2f}")
                
                # 新增的明细统计
                if 'paid_qty' in prepaid:
                    print(f"    - 付费桶领取：{prepaid['paid_qty']} 桶，金额¥{prepaid['paid_amount']:.2f}")
                    print(f"    - 赠送桶领取：{prepaid['gift_qty']} 桶，金额¥{prepaid['gift_amount']:.2f}")
            
            if 'credit' in report:
                credit = report['credit']
                print(f"  先用后付 (信用):")
                print(f"    - 总领取量：{credit.get('total_qty', 0)} 桶")
                print(f"    - 应收金额：¥{credit.get('total_amount', 0):.2f}")
        else:
            print(f"  ❌ 查询失败：{response.text}")
        
        print("\n" + "=" * 60)
        print("✅ 集成测试完成!")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ 测试异常：{e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("\n提示：请确保后端服务已启动 (uvicorn main:app --reload)")
    print("-" * 60)
    
    success = test_full_flow()
    sys.exit(0 if success else 1)
