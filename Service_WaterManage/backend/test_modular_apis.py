#!/usr/bin/env python3
"""
方案A步骤2: 完整测试模块化API功能
验证 auth/products/water 路由是否正常工作
"""

import requests
import json
import sys
from datetime import datetime

BASE_URL = "http://localhost:8000"


class TestResult:
    def __init__(self):
        self.passed = []
        self.failed = []
        self.token = None

    def add_pass(self, name):
        self.passed.append(name)
        print(f"✅ {name}")

    def add_fail(self, name, error=""):
        self.failed.append((name, error))
        print(f"❌ {name}: {error}")

    def summary(self):
        print("\n" + "=" * 60)
        print(f"测试结果: {len(self.passed)} 通过, {len(self.failed)} 失败")
        if self.failed:
            print("\n失败项目:")
            for name, error in self.failed:
                print(f"  - {name}: {error}")
        return len(self.failed) == 0


def test_auth_api(result):
    """测试认证API"""
    print("\n=== 认证API测试 ===")

    # 测试登录
    try:
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"name": "admin", "password": "admin123"},
            timeout=5,
        )
        if response.status_code == 200:
            data = response.json()
            result.token = data.get("access_token")
            if result.token:
                result.add_pass("POST /api/auth/login")
            else:
                result.add_fail("POST /api/auth/login", "无token返回")
        else:
            result.add_fail("POST /api/auth/login", f"HTTP {response.status_code}")
    except Exception as e:
        result.add_fail("POST /api/auth/login", str(e))
        return

    if not result.token:
        print("⚠️  无token，跳过后续认证测试")
        return

    headers = {"Authorization": f"Bearer {result.token}"}

    # 测试获取当前用户
    try:
        response = requests.get(f"{BASE_URL}/api/auth/me", headers=headers, timeout=5)
        if response.status_code == 200:
            result.add_pass("GET /api/auth/me")
        else:
            result.add_fail("GET /api/auth/me", f"HTTP {response.status_code}")
    except Exception as e:
        result.add_fail("GET /api/auth/me", str(e))


def test_products_api(result):
    """测试产品API"""
    print("\n=== 产品API测试 ===")

    if not result.token:
        print("⚠️  无token，跳过产品测试")
        return

    headers = {"Authorization": f"Bearer {result.token}"}

    # 测试获取产品列表
    try:
        response = requests.get(f"{BASE_URL}/api/products", headers=headers, timeout=5)
        if response.status_code == 200:
            products = response.json()
            result.add_pass(f"GET /api/products ({len(products)}条)")
        else:
            result.add_fail("GET /api/products", f"HTTP {response.status_code}")
    except Exception as e:
        result.add_fail("GET /api/products", str(e))

    # 测试获取分类
    try:
        response = requests.get(
            f"{BASE_URL}/api/admin/product-categories", headers=headers, timeout=5
        )
        if response.status_code == 200:
            categories = response.json()
            result.add_pass(f"GET /api/admin/product-categories ({len(categories)}条)")
        else:
            result.add_fail(
                "GET /api/admin/product-categories", f"HTTP {response.status_code}"
            )
    except Exception as e:
        result.add_fail("GET /api/admin/product-categories", str(e))


def test_water_api(result):
    """测试领水API"""
    print("\n=== 领水API测试 ===")

    if not result.token:
        print("⚠️  无token，跳过领水测试")
        return

    headers = {"Authorization": f"Bearer {result.token}"}

    tests = [
        ("GET /api/user/offices", "/api/user/offices"),
        ("GET /api/user/office-pickups", "/api/user/office-pickups"),
        ("GET /api/user/office-pickup-summary", "/api/user/office-pickup-summary"),
        ("GET /api/admin/office-pickups/trash", "/api/admin/office-pickups/trash"),
    ]

    for name, endpoint in tests:
        try:
            response = requests.get(f"{BASE_URL}{endpoint}", headers=headers, timeout=5)
            if response.status_code == 200:
                data = response.json()
                count = len(data) if isinstance(data, list) else 1
                result.add_pass(f"{name} ({count}条)")
            else:
                result.add_fail(name, f"HTTP {response.status_code}")
        except Exception as e:
            result.add_fail(name, str(e))


def test_route_priorities(result):
    """测试路由优先级 - 确认使用模块化路由"""
    print("\n=== 路由优先级测试 ===")

    # 检查API文档中的路由数量
    try:
        response = requests.get(f"{BASE_URL}/openapi.json", timeout=5)
        if response.status_code == 200:
            spec = response.json()
            paths = spec.get("paths", {})

            # 检查关键路由是否存在
            critical_routes = [
                "/api/auth/login",
                "/api/products",
                "/api/user/offices",
                "/api/user/office-pickup",
            ]

            for route in critical_routes:
                if route in paths:
                    result.add_pass(f"路由注册: {route}")
                else:
                    result.add_fail(f"路由注册: {route}", "未找到")

            print(f"\n总路由数: {len(paths)}")
        else:
            result.add_fail("获取OpenAPI文档", f"HTTP {response.status_code}")
    except Exception as e:
        result.add_fail("获取OpenAPI文档", str(e))


def main():
    print("=" * 60)
    print("方案A - 步骤2: 模块化API完整测试")
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    result = TestResult()

    # 测试前端访问
    print("\n=== 前端访问测试 ===")
    pages = [
        ("Portal首页", "/portal/index.html"),
        ("API文档", "/docs"),
    ]

    for name, path in pages:
        try:
            response = requests.get(f"{BASE_URL}{path}", timeout=5)
            if response.status_code == 200:
                result.add_pass(f"前端访问: {name}")
            else:
                result.add_fail(f"前端访问: {name}", f"HTTP {response.status_code}")
        except Exception as e:
            result.add_fail(f"前端访问: {name}", str(e))

    # 运行所有API测试
    test_auth_api(result)
    test_products_api(result)
    test_water_api(result)
    test_route_priorities(result)

    # 输出结果
    if result.summary():
        print("\n✅ 所有测试通过！可以安全删除main.py中的重复路由")
        return 0
    else:
        print("\n❌ 存在失败测试，请检查模块化路由")
        return 1


if __name__ == "__main__":
    sys.exit(main())
