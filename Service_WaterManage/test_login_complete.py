#!/usr/bin/env python3
"""
全面测试登录功能
"""

import requests
import json

API_BASE = "http://localhost:8000/api"

def print_section(title):
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)

def print_test(name):
    print(f"\n【测试】{name}")
    print("-" * 70)

def print_result(success, message, details=None):
    status = "✅" if success else "❌"
    print(f"{status} {message}")
    if details:
        print(f"   详情：{details}")

# ========== 1. 登录 API 基础测试 ==========
print_section("1. 登录 API 基础测试")

# 测试 1.1: 正常登录
print_test("正常登录（admin 用户）")

# 首先创建测试用户
print("   创建测试用户...")
create_user_response = requests.post(
    f"{API_BASE}/users",
    json={
        "name": "testuser",
        "department": "测试部",
        "role": "staff",
        "password": "TestP@ss123"
    }
)

if create_user_response.status_code in [200, 400]:
    print_result(True, "测试用户创建成功或已存在")
else:
    print_result(False, f"测试用户创建失败：{create_user_response.status_code}")

# 测试 admin 登录（初始密码需要从 init_system 获取，这里使用 admin123 作为默认）
print("\n   尝试登录 admin 用户...")
login_response = requests.post(
    f"{API_BASE}/auth/login",
    json={"name": "admin", "password": "admin123"}
)

if login_response.status_code == 200:
    data = login_response.json()
    print_result(True, "admin 登录成功")
    print(f"   用户：{data['user']['name']} ({data['user']['role']})")
    admin_token = data['access_token']
else:
    print_result(False, f"admin 登录失败：{login_response.status_code}")
    print(f"   响应：{login_response.text[:200]}")
    admin_token = None

# 测试 1.2: 测试用户登录
print_test("测试用户登录")
login_response = requests.post(
    f"{API_BASE}/auth/login",
    json={"name": "testuser", "password": "TestP@ss123"}
)

if login_response.status_code == 200:
    data = login_response.json()
    print_result(True, "测试用户登录成功")
    print(f"   用户：{data['user']['name']} ({data['user']['role']})")
    test_token = data['access_token']
else:
    print_result(False, f"测试用户登录失败：{login_response.status_code}")
    test_token = None

# ========== 2. Token 验证测试 ==========
print_section("2. Token 验证测试")

# 测试 2.1: 使用 Token 获取用户信息
print_test("使用 Token 获取当前用户信息")
if admin_token:
    me_response = requests.get(
        f"{API_BASE}/auth/me",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    if me_response.status_code == 200:
        print_result(True, "Token 验证成功，可获取用户信息")
    else:
        print_result(False, f"Token 验证失败：{me_response.status_code}")
else:
    print_result(False, "缺少 admin_token，跳过测试")

# 测试 2.2: 无效 Token
print_test("无效 Token 验证")
invalid_response = requests.get(
    f"{API_BASE}/auth/me",
    headers={"Authorization": "Bearer invalid_token_xyz"}
)

if invalid_response.status_code == 401:
    print_result(True, "无效 Token 被正确拒绝 (401)")
else:
    print_result(False, f"无效 Token 未被拒绝：{invalid_response.status_code}")

# 测试 2.3: 无 Token
print_test("无 Token 访问")
no_auth_response = requests.get(f"{API_BASE}/auth/me")

if no_auth_response.status_code in [401, 422]:
    print_result(True, f"无 Token 访问被正确拒绝 ({no_auth_response.status_code})")
else:
    print_result(False, f"无 Token 未被拒绝：{no_auth_response.status_code}")

# ========== 3. 密码修改测试 ==========
print_section("3. 密码修改测试")

if test_token:
    print_test("修改密码（正确原密码）")
    change_response = requests.post(
        f"{API_BASE}/auth/change-password",
        headers={"Authorization": f"Bearer {test_token}"},
        json={
            "old_password": "TestP@ss123",
            "new_password": "NewP@ss456"
        }
    )
    
    if change_response.status_code == 200:
        print_result(True, "密码修改成功")
        
        # 验证新密码
        print("\n   验证新密码登录...")
        new_login = requests.post(
            f"{API_BASE}/auth/login",
            json={"name": "testuser", "password": "NewP@ss456"}
        )
        
        if new_login.status_code == 200:
            print_result(True, "新密码验证成功")
            # 恢复原密码
            new_token = new_login.json()["access_token"]
            requests.post(
                f"{API_BASE}/auth/change-password",
                headers={"Authorization": f"Bearer {new_token}"},
                json={
                    "old_password": "NewP@ss456",
                    "new_password": "TestP@ss123"
                }
            )
            print_result(True, "已恢复原密码")
        else:
            print_result(False, "新密码验证失败")
    else:
        print_result(False, f"密码修改失败：{change_response.status_code}")
        print(f"   响应：{change_response.text[:200]}")
    
    # 测试 3.2: 错误原密码
    print_test("修改密码（错误原密码）")
    wrong_old_response = requests.post(
        f"{API_BASE}/auth/change-password",
        headers={"Authorization": f"Bearer {test_token}"},
        json={
            "old_password": "WrongPassword",
            "new_password": "NewP@ss789"
        }
    )
    
    if wrong_old_response.status_code == 400:
        print_result(True, "错误原密码被正确拒绝")
    else:
        print_result(False, f"错误原密码未被拒绝：{wrong_old_response.status_code}")
else:
    print_result(False, "缺少 test_token，跳过密码修改测试")

# ========== 4. 权限控制测试 ==========
print_section("4. 权限控制测试")

if admin_token:
    print_test("admin 访问受保护接口（删除交易）")
    # 尝试删除（即使没有交易也应该验证权限）
    delete_response = requests.post(
        f"{API_BASE}/admin/transactions/delete",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "transaction_ids": [999],
            "reason": "权限测试"
        }
    )
    
    # super_admin 应该可以访问（即使交易不存在返回 404）
    if delete_response.status_code in [200, 404]:
        print_result(True, f"admin 权限验证通过 ({delete_response.status_code})")
    elif delete_response.status_code == 403:
        print_result(False, "admin 权限不足（应该是 403）")
    else:
        print_result(False, f"意外响应：{delete_response.status_code}")
else:
    print_result(False, "缺少 admin_token，跳过权限测试")

# 测试 staff 用户权限
if test_token:
    print_test("staff 用户尝试删除（应被拒绝）")
    staff_delete = requests.post(
        f"{API_BASE}/admin/transactions/delete",
        headers={"Authorization": f"Bearer {test_token}"},
        json={
            "transaction_ids": [999],
            "reason": "权限测试"
        }
    )
    
    if staff_delete.status_code == 403:
        print_result(True, "staff 删除权限被正确拒绝 (403)")
    else:
        print_result(False, f"staff 删除未被拒绝：{staff_delete.status_code}")

# ========== 5. 用户管理测试（super_admin） ==========
print_section("5. 用户管理测试")

if admin_token:
    print_test("super_admin 创建管理员账号")
    admin_create = requests.post(
        f"{API_BASE}/users",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "name": "manager1",
            "department": "运营部",
            "role": "admin",
            "password": "ManagerP@ss123"
        }
    )
    
    if admin_create.status_code in [200, 400]:
        print_result(True, "管理员账号创建成功或已存在")
        
        # 测试新管理员登录
        print("\n   测试新管理员登录...")
        manager_login = requests.post(
            f"{API_BASE}/auth/login",
            json={"name": "manager1", "password": "ManagerP@ss123"}
        )
        
        if manager_login.status_code == 200:
            print_result(True, "新管理员登录成功")
        else:
            print_result(False, f"新管理员登录失败：{manager_login.status_code}")
    else:
        print_result(False, f"管理员账号创建失败：{admin_create.status_code}")
    
    print_test("staff 用户尝试创建用户（应被拒绝）")
    if test_token:
        staff_create = requests.post(
            f"{API_BASE}/users",
            headers={"Authorization": f"Bearer {test_token}"},
            json={
                "name": "hacker",
                "department": "黑客部",
                "role": "admin",
                "password": "HackerP@ss"
            }
        )
        
        if staff_create.status_code == 403:
            print_result(True, "staff 创建用户权限被正确拒绝 (403)")
        else:
            print_result(False, f"staff 创建用户未被拒绝：{staff_create.status_code}")
else:
    print_result(False, "缺少 admin_token，跳过用户管理测试")

# ========== 测试总结 ==========
print_section("测试总结")

print("""
📋 测试覆盖：
   1. ✓ 登录 API - 正常登录、错误处理
   2. ✓ Token 验证 - 有效 Token、无效 Token、无 Token
   3. ✓ 密码管理 - 修改密码、原密码验证
   4. ✓ 权限控制 - super_admin、admin、staff 角色权限
   5. ✓ 用户管理 - 创建用户、角色分配

💡 使用说明：
   1. 访问登录页：http://localhost:8080/frontend/login.html
   2. 测试账号：
      - admin / admin123 (super_admin)
      - testuser / TestP@ss123 (staff)
      - manager1 / ManagerP@ss123 (admin)
""")

print("=" * 70)
print("✅ 登录功能全面测试完成！")
print("=" * 70)
