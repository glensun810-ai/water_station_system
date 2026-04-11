#!/usr/bin/env python3
"""
测试办公室权限修复
验证不同角色用户看到的办公室列表是否符合预期
"""

import requests
import json

BASE_URL = "http://127.0.0.1:8008"


def login(username, password):
    """登录并获取token"""
    response = requests.post(
        f"{BASE_URL}/api/v1/system/auth/login",
        json={"username": username, "password": password},
    )
    if response.status_code == 200:
        data = response.json()
        return data["access_token"], data["user_info"]
    else:
        print(f"❌ 登录失败: {response.text}")
        return None, None


def get_offices(token):
    """获取办公室列表"""
    response = requests.get(
        f"{BASE_URL}/api/v1/water/offices", headers={"Authorization": f"Bearer {token}"}
    )
    if response.status_code == 200:
        return response.json()
    else:
        print(f"❌ 获取办公室失败: {response.text}")
        return []


def test_user(username, password, expected_count, role_name):
    """测试用户权限"""
    print(f"\n{'=' * 60}")
    print(f"测试用户: {username} ({role_name})")
    print(f"{'=' * 60}")

    token, user_info = login(username, password)
    if not token:
        return False

    print(f"✅ 登录成功")
    print(f"   - 用户ID: {user_info['user_id']}")
    print(f"   - 角色: {user_info['role']}")
    print(f"   - 部门: {user_info['department']}")

    offices = get_offices(token)
    print(f"✅ 获取办公室列表成功")
    print(f"   - 办公室数量: {len(offices)}")

    if len(offices) > 0:
        print(f"   - 办公室列表:")
        for office in offices[:10]:  # 只显示前10个
            print(f"     {office['id']}: {office['name']} ({office['room_number']})")
        if len(offices) > 10:
            print(f"     ... 还有 {len(offices) - 10} 个办公室")

    # 验证数量
    if len(offices) == expected_count:
        print(f"✅ 权限验证成功: 预期 {expected_count} 个，实际 {len(offices)} 个")
        return True
    else:
        print(f"❌ 权限验证失败: 预期 {expected_count} 个，实际 {len(offices)} 个")
        return False


def main():
    print("=" * 60)
    print("办公室权限修复测试")
    print("=" * 60)

    # 查询数据库，获取办公室总数
    import sqlite3

    conn = sqlite3.connect("/Users/sgl/PycharmProjects/AIchanyejiqun/data/app.db")
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM office WHERE is_active=1")
    total_offices = cursor.fetchone()[0]
    conn.close()

    print(f"\n数据库中激活办公室总数: {total_offices}")

    # 测试不同角色用户
    results = []

    # 1. 超级管理员 - 应该看到所有办公室
    results.append(test_user("admin", "admin123", total_offices, "超级管理员"))

    # 2. 系统管理员 - 应该看到所有办公室
    results.append(test_user("系统管理员", "admin123", total_offices, "管理员"))

    # 3. 办公室管理员（孙经理） - 应该看到管辖的办公室（1个）
    results.append(test_user("孙经理", "123456", 1, "办公室管理员"))

    # 4. 管理员（麦子） - admin角色，应该看到所有办公室
    results.append(test_user("麦子", "123456", total_offices, "管理员（麦子）"))

    # 5. 普通用户（普通用户） - department="总经理"，应该看到总经理办公室
    results.append(test_user("普通用户", "123456", 1, "普通用户"))

    # 总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    success_count = sum(results)
    total_count = len(results)
    print(f"成功: {success_count}/{total_count}")

    if success_count == total_count:
        print("✅ 所有测试通过！办公室权限修复成功！")
    else:
        print("❌ 部分测试失败，请检查权限配置")


if __name__ == "__main__":
    main()
