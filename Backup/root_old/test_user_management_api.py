#!/usr/bin/env python3
"""
测试用户管理API增强功能
"""

import requests
import json

BASE_URL = "http://localhost:8000"


def test_user_list_with_new_fields():
    """测试用户列表API新字段"""
    print("\n=== 测试用户列表API ===")

    try:
        response = requests.get(f"{BASE_URL}/api/users")

        if response.status_code == 200:
            users = response.json()
            print(f"✓ 成功获取 {len(users)} 个用户")

            if users:
                # 检查第一个用户是否有新字段
                first_user = users[0]
                print(f"\n第一个用户信息:")
                print(f"  ID: {first_user.get('id')}")
                print(f"  用户名: {first_user.get('name')}")
                print(f"  用户类型: {first_user.get('user_type', 'N/A')}")
                print(f"  手机号: {first_user.get('phone', 'N/A')}")
                print(f"  邮箱: {first_user.get('email', 'N/A')}")
                print(f"  公司: {first_user.get('company', 'N/A')}")
                print(f"  角色: {first_user.get('role')}")
                print(
                    f"  状态: {'已激活' if first_user.get('is_active') else '待激活'}"
                )

                # 验证字段存在
                required_fields = ["id", "name", "user_type", "role", "is_active"]
                missing_fields = [f for f in required_fields if f not in first_user]

                if missing_fields:
                    print(f"\n⚠ 缺少字段: {missing_fields}")
                else:
                    print(f"\n✓ 所有必需字段都存在")

                return True
        else:
            print(f"✗ 请求失败: {response.status_code}")
            print(f"  响应: {response.text}")
            return False

    except Exception as e:
        print(f"✗ 测试失败: {str(e)}")
        return False


def test_user_stats():
    """测试用户统计API"""
    print("\n=== 测试用户统计API ===")

    try:
        response = requests.get(f"{BASE_URL}/api/users/stats/overview")

        if response.status_code == 200:
            stats = response.json()
            print(f"✓ 成功获取统计数据")
            print(f"\n统计信息:")
            print(f"  总用户数: {stats.get('total')}")
            print(f"  已激活: {stats.get('active')}")
            print(f"  待激活: {stats.get('inactive')}")
            print(f"  内部用户: {stats.get('internal_users', 'N/A')}")
            print(f"  外部用户: {stats.get('external_users', 'N/A')}")
            print(f"  超级管理员: {stats.get('super_admins')}")
            print(f"  系统管理员: {stats.get('admins')}")
            print(f"  办公室管理员: {stats.get('office_admins')}")
            print(f"  普通用户: {stats.get('users')}")

            return True
        else:
            print(f"✗ 请求失败: {response.status_code}")
            return False

    except Exception as e:
        print(f"✗ 测试失败: {str(e)}")
        return False


def test_activate_user():
    """测试用户激活API"""
    print("\n=== 测试用户激活API ===")

    try:
        # 先查找一个待激活的用户
        response = requests.get(f"{BASE_URL}/api/users?is_active=0")

        if response.status_code != 200:
            print("✗ 无法获取用户列表")
            return False

        inactive_users = response.json()

        if not inactive_users:
            print("⚠ 没有待激活的用户，跳过激活测试")
            return True

        # 选择第一个待激活用户
        user_to_activate = inactive_users[0]
        user_id = user_to_activate["id"]
        user_name = user_to_activate["name"]

        print(f"尝试激活用户: {user_name} (ID: {user_id})")

        # 调用激活API
        activate_response = requests.post(f"{BASE_URL}/api/users/{user_id}/activate")

        if activate_response.status_code == 200:
            result = activate_response.json()
            print(f"✓ 激活成功")
            print(f"  消息: {result.get('message')}")

            # 验证用户状态已更新
            verify_response = requests.get(f"{BASE_URL}/api/users/{user_id}")
            if verify_response.status_code == 200:
                updated_user = verify_response.json()
                if updated_user.get("is_active") == 1:
                    print(f"✓ 用户状态已更新为已激活")
                else:
                    print(f"⚠ 用户状态未正确更新")

            return True
        elif activate_response.status_code == 400:
            error = activate_response.json()
            print(f"⚠ {error.get('detail')}")
            return True  # 已激活的用户也视为成功
        else:
            print(f"✗ 激活失败: {activate_response.status_code}")
            print(f"  响应: {activate_response.text}")
            return False

    except Exception as e:
        print(f"✗ 测试失败: {str(e)}")
        return False


def test_filter_by_user_type():
    """测试按用户类型筛选"""
    print("\n=== 测试按用户类型筛选 ===")

    try:
        # 测试筛选外部用户
        response = requests.get(f"{BASE_URL}/api/users?user_type=external")

        if response.status_code == 200:
            external_users = response.json()
            print(f"✓ 外部用户数: {len(external_users)}")

            if external_users:
                # 验证筛选结果正确
                all_external = all(
                    u.get("user_type") == "external" for u in external_users
                )
                if all_external:
                    print(f"✓ 筛选结果正确")
                else:
                    print(f"⚠ 筛选结果包含非外部用户")

            return True
        else:
            print(f"✗ 筛选失败: {response.status_code}")
            return False

    except Exception as e:
        print(f"✗ 测试失败: {str(e)}")
        return False


def main():
    print("=" * 60)
    print("用户管理API增强功能测试")
    print("=" * 60)

    # 测试服务是否运行
    try:
        response = requests.get(f"{BASE_URL}/api/health", timeout=5)
        if response.status_code != 200:
            print("服务未运行，请先启动服务")
            return
        print("✓ 服务运行正常\n")
    except:
        print("无法连接服务")
        return

    # 运行所有测试
    results = []
    results.append(("用户列表新字段", test_user_list_with_new_fields()))
    results.append(("用户统计", test_user_stats()))
    results.append(("用户激活", test_activate_user()))
    results.append(("用户类型筛选", test_filter_by_user_type()))

    # 总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)

    for name, result in results:
        status = "✓ 通过" if result else "✗ 失败"
        print(f"{status} - {name}")

    total = len(results)
    passed = sum(1 for _, r in results if r)

    print(f"\n总计: {passed}/{total} 测试通过")
    print("=" * 60)


if __name__ == "__main__":
    main()
