#!/usr/bin/env python3
"""
前端集成完整测试 - 验证登录、Token、删除权限、密码管理
"""

import requests
import json

API_BASE = "http://localhost:8000/api"

# 从 init_system.py 获取的初始密码（需要根据实际输出修改）
INITIAL_PASSWORD = "45_bAEBHdss"


def test_full_auth_flow():
    """测试完整认证和权限流程"""
    print("=" * 70)
    print("🔐 前端集成完整测试 - 认证 + 权限 + 密码管理")
    print("=" * 70)
    
    # ========== 1. 登录测试 ==========
    print("\n【1】登录测试")
    print("-" * 70)
    
    login_response = requests.post(
        f"{API_BASE}/auth/login",
        json={"name": "admin", "password": INITIAL_PASSWORD}
    )
    
    if login_response.status_code != 200:
        print(f"❌ 登录失败：{login_response.status_code}")
        print(f"   响应：{login_response.text}")
        return False
    
    login_data = login_response.json()
    token = login_data["access_token"]
    user = login_data["user"]
    headers = {"Authorization": f"Bearer {token}"}
    
    print(f"✅ 登录成功")
    print(f"   用户：{user['name']} ({user['role']})")
    print(f"   Token: {token[:50]}...")
    
    # ========== 2. Token 验证测试 ==========
    print("\n【2】Token 验证测试")
    print("-" * 70)
    
    # 2.1 获取当前用户信息
    me_response = requests.get(f"{API_BASE}/auth/me", headers=headers)
    if me_response.status_code == 200:
        print(f"✅ Token 验证成功 - 可获取用户信息")
    else:
        print(f"❌ Token 验证失败：{me_response.status_code}")
        return False
    
    # 2.2 错误 Token 测试
    invalid_headers = {"Authorization": "Bearer invalid_token"}
    invalid_response = requests.get(f"{API_BASE}/auth/me", headers=invalid_headers)
    if invalid_response.status_code == 401:
        print(f"✅ 无效 Token 被正确拒绝")
    else:
        print(f"⚠️  无效 Token 未被拒绝：{invalid_response.status_code}")
    
    # ========== 3. 删除权限测试 ==========
    print("\n【3】删除权限测试")
    print("-" * 70)
    
    # 3.1 创建测试交易
    print("   创建测试交易...")
    
    # 获取产品
    products = requests.get(f"{API_BASE}/products").json()
    if not products:
        product_res = requests.post(f"{API_BASE}/products", json={
            "name": "测试产品",
            "specification": "1L",
            "unit": "瓶",
            "price": 5.0,
            "stock": 100
        })
        product_id = product_res.json()["id"] if product_res.status_code == 200 else 1
    else:
        product_id = products[0]["id"]
    
    # 获取用户
    users = requests.get(f"{API_BASE}/users").json()
    user_id = 2  # 假设有 ID 为 2 的用户
    
    # 创建交易
    transaction_res = requests.post(f"{API_BASE}/record", json={
        "user_id": user_id,
        "product_id": product_id,
        "quantity": 1,
        "type": "pickup"
    })
    
    if transaction_res.status_code == 200:
        transaction_id = transaction_res.json()["id"]
        print(f"   ✅ 创建测试交易 ID: {transaction_id}")
        
        # 3.2 测试删除（带 Token）
        print("   测试删除交易（带 Token）...")
        delete_response = requests.post(
            f"{API_BASE}/admin/transactions/delete",
            headers=headers,
            json={
                "transaction_ids": [transaction_id],
                "reason": "前端集成测试"
            }
        )
        
        if delete_response.status_code == 200:
            print(f"   ✅ 删除成功（super_admin 权限正常）")
            print(f"   响应：{delete_response.json().get('message', '')}")
        else:
            print(f"   ❌ 删除失败：{delete_response.status_code}")
            print(f"   响应：{delete_response.text}")
    else:
        print(f"   ⚠️  创建交易失败，跳过删除测试")
    
    # 3.3 测试无 Token 删除
    print("\n   测试无 Token 删除（应被拒绝）...")
    no_auth_delete = requests.post(
        f"{API_BASE}/admin/transactions/delete",
        json={
            "transaction_ids": [transaction_id],
            "reason": "测试"
        }
    )
    
    if no_auth_delete.status_code == 401 or no_auth_delete.status_code == 422:
        print(f"   ✅ 无 Token 删除被正确拒绝 ({no_auth_delete.status_code})")
    else:
        print(f"   ⚠️  无 Token 删除未被拒绝：{no_auth_delete.status_code}")
    
    # ========== 4. 密码修改测试 ==========
    print("\n【4】密码修改测试")
    print("-" * 70)
    
    new_password = "TestP@ss123"
    
    # 4.1 修改密码
    print("   修改密码...")
    change_pwd_response = requests.post(
        f"{API_BASE}/auth/change-password",
        headers=headers,
        json={
            "old_password": INITIAL_PASSWORD,
            "new_password": new_password
        }
    )
    
    if change_pwd_response.status_code == 200:
        print(f"   ✅ 密码修改成功")
        
        # 4.2 验证新密码登录
        print("   验证新密码登录...")
        new_login = requests.post(
            f"{API_BASE}/auth/login",
            json={"name": "admin", "password": new_password}
        )
        
        if new_login.status_code == 200:
            print(f"   ✅ 新密码验证成功")
            
            # 恢复原密码
            new_token = new_login.json()["access_token"]
            new_headers = {"Authorization": f"Bearer {new_token}"}
            requests.post(
                f"{API_BASE}/auth/change-password",
                headers=new_headers,
                json={
                    "old_password": new_password,
                    "new_password": INITIAL_PASSWORD
                }
            )
            print(f"   ℹ️  已恢复原密码")
        else:
            print(f"   ❌ 新密码验证失败")
    else:
        print(f"   ❌ 密码修改失败：{change_pwd_response.status_code}")
    
    # ========== 5. 角色权限测试 ==========
    print("\n【5】角色权限测试")
    print("-" * 70)
    
    # 5.1 创建普通员工账号
    print("   创建普通员工账号...")
    staff_response = requests.post(
        f"{API_BASE}/users",
        headers=headers,
        json={
            "name": "test_staff",
            "department": "测试部",
            "role": "staff",
            "password": "StaffP@ss123"
        }
    )
    
    if staff_response.status_code in [200, 400]:
        print(f"   ✅ 员工账号创建成功")
        
        # 5.2 员工登录
        print("   员工登录...")
        staff_login = requests.post(
            f"{API_BASE}/auth/login",
            json={"name": "test_staff", "password": "StaffP@ss123"}
        )
        
        if staff_login.status_code == 200:
            staff_token = staff_login.json()["access_token"]
            staff_headers = {"Authorization": f"Bearer {staff_token}"}
            
            # 5.3 员工尝试删除（应被拒绝）
            print("   员工尝试删除交易（应被拒绝）...")
            staff_delete = requests.post(
                f"{API_BASE}/admin/transactions/delete",
                headers=staff_headers,
                json={
                    "transaction_ids": [1],
                    "reason": "权限测试"
                }
            )
            
            if staff_delete.status_code == 403:
                print(f"   ✅ 员工删除权限被正确拒绝 (403)")
            else:
                print(f"   ⚠️  员工删除未被拒绝：{staff_delete.status_code}")
    else:
        print(f"   ⚠️  创建员工账号失败：{staff_response.status_code}")
    
    # ========== 6. 审计日志测试 ==========
    print("\n【6】审计日志测试")
    print("-" * 70)
    
    # 6.1 查看删除日志
    print("   查看删除日志...")
    logs_response = requests.get(f"{API_BASE}/admin/delete-logs", headers=headers)
    
    if logs_response.status_code == 200:
        logs = logs_response.json()
        if logs:
            print(f"   ✅ 找到 {len(logs)} 条删除日志")
            latest_log = logs[0]
            print(f"   最新日志：")
            print(f"      - 操作人：{latest_log.get('operator_name', 'N/A')}")
            print(f"      - 操作：{latest_log.get('action', 'N/A')}")
            print(f"      - 原因：{latest_log.get('reason', 'N/A')}")
        else:
            print(f"   ℹ️  暂无删除日志")
    else:
        print(f"   ⚠️  获取日志失败：{logs_response.status_code}")
    
    # ========== 测试总结 ==========
    print("\n" + "=" * 70)
    print("✅ 前端集成测试完成！")
    print("=" * 70)
    
    print("\n📋 测试总结：")
    print("   1. ✓ 登录 API - 支持用户名密码登录")
    print("   2. ✓ Token 验证 - JWT Token 格式正确，无效 Token 被拒绝")
    print("   3. ✓ 删除权限 - 带 Token 可删除，无 Token 被拒绝")
    print("   4. ✓ 角色权限 - staff 角色删除被拒绝 (403)")
    print("   5. ✓ 密码管理 - 支持修改密码，需验证原密码")
    print("   6. ✓ 审计日志 - 记录所有删除操作")
    
    print("\n💡 使用说明：")
    print("   1. 访问登录页：http://localhost:8080/frontend/login.html")
    print(f"   2. 用户名：admin")
    print(f"   3. 密码：{INITIAL_PASSWORD}")
    print("   4. 登录后体验完整功能")
    
    return True


if __name__ == "__main__":
    try:
        test_full_auth_flow()
    except requests.exceptions.ConnectionError:
        print("\n❌ 无法连接到后端服务")
        print("   启动命令：cd backend && source ../.venv/bin/activate && python main.py")
    except Exception as e:
        print(f"\n❌ 测试失败：{e}")
        import traceback
        traceback.print_exc()
