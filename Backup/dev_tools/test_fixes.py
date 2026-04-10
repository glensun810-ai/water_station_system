#!/usr/bin/env python3
"""
测试修复后的页面功能
"""

import requests
import json


def test_pages():
    """测试三个关键页面的API调用"""

    base_url = "http://127.0.0.1:8007"
    api_base = "http://127.0.0.1:8000/api/v1"

    print("🔍 测试领水记录页面 API...")
    try:
        # 测试办公室列表
        response = requests.get(f"{api_base}/system/offices")
        print(f"  办公室列表: {response.status_code}")

        # 测试产品列表
        response = requests.get(f"{api_base}/water/products")
        print(f"  产品列表: {response.status_code}")

        # 测试领水记录
        response = requests.get(f"{api_base}/water/pickups")
        print(f"  领水记录: {response.status_code}")

    except Exception as e:
        print(f"  领水记录页面测试失败: {e}")

    print("\n🔍 测试结算管理页面 API...")
    try:
        # 测试结算申请列表
        response = requests.get(f"{api_base}/water/settlements/applications")
        print(f"  结算申请: {response.status_code}")

    except Exception as e:
        print(f"  结算管理页面测试失败: {e}")

    print("\n🔍 测试会议室预约页面 API...")
    try:
        # 测试会议室列表
        response = requests.get(f"{api_base}/meeting/rooms")
        print(f"  会议室列表: {response.status_code}")

        # 测试预约列表
        response = requests.get(f"{api_base}/meeting/bookings")
        print(f"  预约列表: {response.status_code}")

    except Exception as e:
        print(f"  会议室页面测试失败: {e}")


if __name__ == "__main__":
    test_pages()
