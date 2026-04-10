#!/usr/bin/env python3
"""
前端功能完整性验证脚本
测试关键API端点和前端访问
"""

import requests
import json
import sys

BASE_URL = "http://localhost:8000"


def test_frontend_access():
    """测试前端页面访问"""
    print("\n=== 测试前端页面访问 ===")

    pages = {
        "Portal首页": "/portal/index.html",
        "水站前端": "/frontend/index.html",
        "水站管理后台": "/water-admin/admin.html",
        "会议室前端": "/meeting-frontend/index.html",
        "API文档": "/docs",
    }

    results = []
    for name, path in pages.items():
        url = BASE_URL + path
        try:
            response = requests.get(url, timeout=5)
            status = "✅" if response.status_code == 200 else "❌"
            results.append(f"{status} {name}: {path} (HTTP {response.status_code})")
        except Exception as e:
            results.append(f"❌ {name}: {path} (错误: {str(e)})")

    for r in results:
        print(r)

    return all("✅" in r for r in results)


def test_auth_api():
    """测试认证API"""
    print("\n=== 测试认证API ===")

    login_url = BASE_URL + "/api/auth/login"
    login_data = {"name": "admin", "password": "admin123"}

    try:
        response = requests.post(login_url, json=login_data, timeout=5)

        if response.status_code == 200:
            data = response.json()
            token = data.get("access_token")
            print(f"✅ 登录成功")
            print(f"   Token: {token[:30]}...")
            print(f"   用户: {data.get('user', {}).get('name', 'Unknown')}")
            return token
        else:
            print(f"❌ 登录失败: HTTP {response.status_code}")
            print(f"   响应: {response.text}")
            return None
    except Exception as e:
        print(f"❌ 登录请求失败: {str(e)}")
        return None


def test_water_api(token):
    """测试领水API"""
    print("\n=== 测试领水API ===")

    if not token:
        print("❌ 没有token，跳过API测试")
        return False

    headers = {"Authorization": f"Bearer {token}"}

    tests = [
        {
            "name": "获取办公室列表",
            "url": BASE_URL + "/api/user/offices",
            "method": "GET",
        },
        {
            "name": "获取领水记录",
            "url": BASE_URL + "/api/user/office-pickups",
            "method": "GET",
        },
        {
            "name": "获取领水汇总",
            "url": BASE_URL + "/api/user/office-pickup-summary",
            "method": "GET",
        },
    ]

    results = []
    for test in tests:
        try:
            if test["method"] == "GET":
                response = requests.get(test["url"], headers=headers, timeout=5)

            if response.status_code == 200:
                data = response.json()
                count = len(data) if isinstance(data, list) else 1
                results.append(
                    f"✅ {test['name']}: HTTP {response.status_code} (数据: {count})"
                )
            else:
                results.append(f"❌ {test['name']}: HTTP {response.status_code}")
        except Exception as e:
            results.append(f"❌ {test['name']}: {str(e)}")

    for r in results:
        print(r)

    return all("✅" in r for r in results)


def main():
    """主测试流程"""
    print("=" * 60)
    print("前端功能完整性验证")
    print("=" * 60)

    frontend_ok = test_frontend_access()
    token = test_auth_api()
    api_ok = test_water_api(token)

    print("\n" + "=" * 60)
    print("验证结果汇总")
    print("=" * 60)

    print(f"前端访问: {'✅ 通过' if frontend_ok else '❌ 失败'}")
    print(f"认证API: {'✅ 通过' if token else '❌ 失败'}")
    print(f"领水API: {'✅ 通过' if api_ok else '❌ 失败'}")

    overall = frontend_ok and token and api_ok
    print(f"\n总体结果: {'✅ 所有测试通过' if overall else '❌ 存在失败项'}")

    if overall:
        print("\n产品经理验证地址:")
        print(f"  - Portal首页: {BASE_URL}/portal/index.html")
        print(f"  - API文档: {BASE_URL}/docs")

    return 0 if overall else 1


if __name__ == "__main__":
    sys.exit(main())
