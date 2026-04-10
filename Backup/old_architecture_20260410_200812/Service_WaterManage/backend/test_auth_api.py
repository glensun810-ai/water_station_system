#!/usr/bin/env python3
"""
认证API对比测试
对比main.py和模块化版本的行为是否一致
"""

import requests
import json

BASE_URL = "http://localhost:8000"


def test_login():
    """测试登录API"""
    print("\n" + "=" * 60)
    print("测试登录API")
    print("=" * 60)

    # 测试数据
    login_data = {"name": "admin", "password": "admin123"}

    try:
        response = requests.post(f"{BASE_URL}/api/auth/login", json=login_data)

        print(f"状态码: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"✅ 登录成功")
            print(f"   Token: {data['access_token'][:50]}...")
            print(f"   用户: {data['user']['name']}")
            return data["access_token"]
        else:
            print(f"❌ 登录失败: {response.text}")
            return None

    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return None


def test_get_me(token):
    """测试获取当前用户API"""
    print("\n" + "=" * 60)
    print("测试获取当前用户API")
    print("=" * 60)

    if not token:
        print("⚠️ 没有Token，跳过测试")
        return

    try:
        response = requests.get(
            f"{BASE_URL}/api/auth/me", headers={"Authorization": f"Bearer {token}"}
        )

        print(f"状态码: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"✅ 获取成功")
            print(f"   用户ID: {data['id']}")
            print(f"   用户名: {data['name']}")
            print(f"   部门: {data['department']}")
            print(f"   角色: {data['role']}")
        else:
            print(f"❌ 获取失败: {response.text}")

    except Exception as e:
        print(f"❌ 请求失败: {e}")


def test_change_password(token):
    """测试修改密码API"""
    print("\n" + "=" * 60)
    print("测试修改密码API（不实际修改）")
    print("=" * 60)

    if not token:
        print("⚠️ 没有Token，跳过测试")
        return

    # 测试数据（使用原密码，不会实际修改）
    password_data = {
        "old_password": "admin123",
        "new_password": "admin123",  # 保持不变
    }

    try:
        response = requests.post(
            f"{BASE_URL}/api/auth/change-password",
            headers={"Authorization": f"Bearer {token}"},
            json=password_data,
        )

        print(f"状态码: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"✅ API调用成功: {data['message']}")
        else:
            print(f"❌ 修改失败: {response.text}")

    except Exception as e:
        print(f"❌ 请求失败: {e}")


def test_health():
    """测试健康检查"""
    print("\n" + "=" * 60)
    print("测试健康检查")
    print("=" * 60)

    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            print(f"✅ 服务正常: {response.json()}")
        else:
            print(f"❌ 服务异常")
    except Exception as e:
        print(f"❌ 请求失败: {e}")


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("认证API测试开始")
    print("=" * 60)

    # 测试健康检查
    test_health()

    # 测试登录
    token = test_login()

    # 测试获取当前用户
    test_get_me(token)

    # 测试修改密码
    test_change_password(token)

    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)
