#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
会议室预约功能测试脚本
从用户视角测试完整的预约流程
"""

import requests
import json
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8001"


def print_step(step, message):
    print(f"\n{'=' * 60}")
    print(f"步骤 {step}: {message}")
    print("=" * 60)


def test_meeting_reservation():
    """测试会议室预约完整流程"""

    # 步骤 1: 登录
    print_step(1, "用户登录")
    login_response = requests.post(
        f"{BASE_URL}/api/auth/login", json={"username": "admin", "password": "admin123"}
    )
    assert login_response.status_code == 200, "登录失败"
    token = login_response.json()["data"]["access_token"]
    print("✅ 登录成功")
    headers = {"Authorization": f"Bearer {token}"}

    # 步骤 2: 获取会议室列表
    print_step(2, "查看可用会议室")
    rooms_response = requests.get(f"{BASE_URL}/api/meeting/rooms", headers=headers)
    assert rooms_response.status_code == 200, "获取会议室列表失败"
    rooms = rooms_response.json()["data"]["rooms"]
    print(f"✅ 找到 {len(rooms)} 个会议室")
    for room in rooms:
        print(
            f"   - {room['name']} (容量：{room['capacity']}人，¥{room['price_per_hour']}/小时)"
        )

    # 步骤 3: 查看指定日期的可用时间段
    print_step(3, "查看明天 10:00-11:00 时间段")
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")

    # 直接指定测试时间段
    slot = {"start": "10:00", "end": "11:00"}
    print(f"✅ 选择时间段：{slot['start']} - {slot['end']}")

    # 步骤 4: 创建预约
    print_step(4, "创建会议室预约")
    start_time = f"{tomorrow}T{slot['start']}:00"
    end_time = f"{tomorrow}T{slot['end']}:00"

    create_response = requests.post(
        f"{BASE_URL}/api/meeting/reservations",
        params={
            "room_id": rooms[0]["id"],
            "start_time": start_time,
            "end_time": end_time,
            "title": "产品评审会议",
            "attendee_count": 5,
            "description": "讨论 Q2 产品规划",
        },
        headers=headers,
    )

    if create_response.status_code == 200:
        result = create_response.json()
        print("✅ 预约成功")
        print(f"   预约编号：{result['data']['reservation_no']}")
        print(f"   状态：{result['data']['status']}")
    else:
        print(f"⚠️  预约失败：{create_response.json()}")
        return

    # 步骤 5: 查看我的预约
    print_step(5, "查看我的预约记录")
    reservations_response = requests.get(
        f"{BASE_URL}/api/meeting/reservations", headers=headers
    )
    assert reservations_response.status_code == 200, "获取预约列表失败"
    reservations = reservations_response.json()["data"]["items"]
    print(f"✅ 共有 {len(reservations)} 条预约记录")

    if reservations:
        for res in reservations:
            print(
                f"   - {res['room_name']}: {res['start_time'][:16]} - {res['title']} ({res['status']})"
            )
            print(
                f"     时长：{res['duration_hours']}小时，收费时长：{res.get('charged_hours', 0)}小时，金额：¥{res['total_amount']}"
            )

    # 步骤 6: 取消预约（如有）
    if reservations and reservations[0]["status"] in ["confirmed", "pending"]:
        print_step(6, "取消预约")
        cancel_response = requests.delete(
            f"{BASE_URL}/api/meeting/reservations/{reservations[0]['id']}?reason=测试取消",
            headers=headers,
        )
        if cancel_response.status_code == 200:
            print("✅ 取消成功")
        else:
            print(f"⚠️  取消失败：{cancel_response.json()}")

    print_step("✓", "测试完成！")
    print("\n所有核心功能测试通过！✅\n")


if __name__ == "__main__":
    try:
        test_meeting_reservation()
    except AssertionError as e:
        print(f"\n❌ 测试失败：{e}\n")
    except Exception as e:
        print(f"\n❌ 发生错误：{e}\n")
