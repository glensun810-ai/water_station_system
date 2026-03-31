"""
系统集成测试 - 端到端验证
System Integration Test
"""

import requests
import json
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8001"


def test_health():
    """测试健康检查"""
    resp = requests.get(f"{BASE_URL}/api/health")
    assert resp.status_code == 200
    print("✅ 健康检查通过")


def test_service_registry():
    """测试服务注册中心"""
    resp = requests.get(f"{BASE_URL}/api/services")
    assert resp.status_code == 200
    data = resp.json()
    assert data["code"] == 200
    services = data["data"]["services"]
    assert len(services) == 5
    service_codes = [s["code"] for s in services]
    assert "water" in service_codes
    assert "meeting" in service_codes
    assert "dining" in service_codes
    assert "office" in service_codes
    assert "screen" in service_codes
    print(f"✅ 服务注册中心通过 (5 个服务：{', '.join(service_codes)})")


def test_auth_login():
    """测试用户登录"""
    resp = requests.post(
        f"{BASE_URL}/api/auth/login",
        params={"username": "admin", "password": "admin123"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["code"] == 200
    token = data["data"]["access_token"]
    print("✅ 用户登录通过")
    return token


def test_meeting_rooms(token):
    """测试会议室列表"""
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(f"{BASE_URL}/api/meeting/rooms", headers=headers)
    assert resp.status_code == 200
    print("✅ 会议室列表 API 通过")


def test_dining_resources(token):
    """测试餐厅茶室列表"""
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(f"{BASE_URL}/api/dining/resources", headers=headers)
    assert resp.status_code == 200
    print("✅ 餐厅茶室列表 API 通过")


def test_office_resources(token):
    """测试办公空间列表"""
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(f"{BASE_URL}/api/office/resources", headers=headers)
    assert resp.status_code == 200
    print("✅ 办公空间列表 API 通过")


def test_screen_list(token):
    """测试大屏列表"""
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(f"{BASE_URL}/api/screen/screens", headers=headers)
    assert resp.status_code == 200
    print("✅ 前台大屏列表 API 通过")


def test_dashboard(token):
    """测试仪表盘"""
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(f"{BASE_URL}/api/dashboard/stats", headers=headers)
    assert resp.status_code == 200
    print("✅ 仪表盘 API 通过")


def run_all_tests():
    """运行所有测试"""
    print("=" * 50)
    print("🧪 系统集成测试开始")
    print("=" * 50)

    try:
        test_health()
        test_service_registry()
        token = test_auth_login()
        test_meeting_rooms(token)
        test_dining_resources(token)
        test_office_resources(token)
        test_screen_list(token)
        test_dashboard(token)

        print("=" * 50)
        print("✅ 所有测试通过！系统运行正常")
        print("=" * 50)
        return True

    except AssertionError as e:
        print("=" * 50)
        print(f"❌ 测试失败：{e}")
        print("=" * 50)
        return False
    except requests.exceptions.ConnectionError:
        print("=" * 50)
        print("❌ 无法连接到服务器，请先启动应用：python main.py")
        print("=" * 50)
        return False


if __name__ == "__main__":
    run_all_tests()
