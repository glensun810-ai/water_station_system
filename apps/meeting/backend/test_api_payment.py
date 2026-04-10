#!/usr/bin/env python3
"""
会议室管理支付结算API测试脚本
用于测试所有新增的支付和结算接口
"""

import requests
import json
from datetime import datetime, timedelta

# API基础URL
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/meeting"

# 测试数据
test_data = {
    "user_name": "测试用户",
    "user_phone": "13800138000",
    "user_type": "internal",
    "office_id": 1,
    "room_id": 1,
    "booking_date": (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d"),
    "start_time": "09:00",
    "end_time": "12:00",
    "meeting_title": "API测试会议",
    "attendees_count": 5,
}


def print_response(response, title="Response"):
    """打印响应结果"""
    print(f"\n{'=' * 60}")
    print(f"{title}")
    print(f"{'=' * 60}")
    print(f"状态码: {response.status_code}")
    try:
        data = response.json()
        print(f"响应数据: {json.dumps(data, indent=2, ensure_ascii=False)}")
        return data
    except:
        print(f"响应内容: {response.text}")
        return None


def test_api():
    """测试所有API接口"""

    print("\n" + "=" * 60)
    print("会议室管理支付结算API测试开始")
    print("=" * 60)

    # 1. 测试创建预约
    print("\n[测试1] 创建预约")
    booking_data = {
        "room_id": test_data["room_id"],
        "user_type": test_data["user_type"],
        "user_name": test_data["user_name"],
        "user_phone": test_data["user_phone"],
        "office_id": test_data["office_id"],
        "booking_date": test_data["booking_date"],
        "start_time": test_data["start_time"],
        "end_time": test_data["end_time"],
        "meeting_title": test_data["meeting_title"],
        "attendees_count": test_data["attendees_count"],
        "payment_mode": "credit",
        "actual_fee": 240.00,
        "discount_amount": 60.00,
    }

    response = requests.post(f"{API_BASE}/bookings", json=booking_data)
    result = print_response(response, "创建预约")

    if not result or not result.get("success"):
        print("❌ 创建预约失败")
        return

    booking_id = result.get("id")
    booking_no = result.get("booking_no")
    print(f"✅ 创建预约成功: {booking_no}")

    # 2. 测试获取预约列表
    print("\n[测试2] 获取预约列表（增强版）")
    response = requests.get(
        f"{API_BASE}/bookings/enhanced?is_deleted=0&page=1&page_size=10"
    )
    result = print_response(response, "获取预约列表")

    if result and result.get("success"):
        print(f"✅ 获取预约列表成功，共 {result['data']['total']} 条记录")

    # 3. 测试提交支付申请
    print("\n[测试3] 提交支付申请")
    payment_data = {
        "booking_id": booking_id,
        "payment_method": "微信支付",
        "payment_evidence": "转账截图测试数据",
        "payment_remark": "API测试支付",
    }

    response = requests.post(f"{API_BASE}/payment/submit", json=payment_data)
    result = print_response(response, "提交支付申请")

    if not result or not result.get("success"):
        print("❌ 提交支付申请失败")
        return

    payment_id = result.get("data", {}).get("payment_id")
    payment_no = result.get("data", {}).get("payment_no")
    print(f"✅ 提交支付申请成功: {payment_no}")

    # 4. 测试获取支付记录
    print("\n[测试4] 获取支付记录")
    response = requests.get(f"{API_BASE}/payments?status=pending&page=1&page_size=10")
    result = print_response(response, "获取支付记录")

    if result and result.get("success"):
        print(f"✅ 获取支付记录成功，共 {result['data']['total']} 条记录")

    # 5. 测试确认收款
    print("\n[测试5] 确认收款")
    confirm_data = {"payment_id": payment_id, "remark": "API测试确认收款"}

    response = requests.post(f"{API_BASE}/payment/confirm", json=confirm_data)
    result = print_response(response, "确认收款")

    if result and result.get("success"):
        print("✅ 确认收款成功")

    # 6. 测试批量提交支付
    print("\n[测试6] 批量提交支付")
    # 先创建几个测试预约
    booking_ids = []
    for i in range(3):
        booking_data["meeting_title"] = f"批量测试会议{i + 1}"
        booking_data["start_time"] = f"{14 + i * 3}:00"
        booking_data["end_time"] = f"{15 + i * 3}:00"

        response = requests.post(f"{API_BASE}/bookings", json=booking_data)
        result = response.json()
        if result.get("success"):
            booking_ids.append(result.get("id"))

    if booking_ids:
        batch_payment_data = {
            "booking_ids": booking_ids,
            "payment_method": "支付宝",
            "payment_remark": "批量测试支付",
        }

        response = requests.post(
            f"{API_BASE}/payment/batch-submit", json=batch_payment_data
        )
        result = print_response(response, "批量提交支付")

        if result and result.get("success"):
            print(f"✅ 批量提交支付成功，成功 {result.get('message')}")

    # 7. 测试创建结算批次
    print("\n[测试7] 创建结算批次")
    if booking_ids:
        settlement_data = {
            "office_id": test_data["office_id"],
            "booking_ids": booking_ids,
            "settlement_period_start": datetime.now().strftime("%Y-%m-01"),
            "settlement_period_end": datetime.now().strftime("%Y-%m-31"),
            "remark": "API测试结算批次",
        }

        response = requests.post(f"{API_BASE}/settlement/create", json=settlement_data)
        result = print_response(response, "创建结算批次")

        if result and result.get("success"):
            batch_id = result.get("data", {}).get("batch_id")
            batch_no = result.get("data", {}).get("batch_no")
            print(f"✅ 创建结算批次成功: {batch_no}")

    # 8. 测试获取结算批次列表
    print("\n[测试8] 获取结算批次列表")
    response = requests.get(f"{API_BASE}/settlements?page=1&page_size=10")
    result = print_response(response, "获取结算批次列表")

    if result and result.get("success"):
        print(f"✅ 获取结算批次列表成功，共 {result['data']['total']} 条记录")

    # 9. 测试获取结算明细
    print("\n[测试9] 获取结算明细")
    if batch_id:
        response = requests.get(f"{API_BASE}/settlement/{batch_id}")
        result = print_response(response, "获取结算明细")

        if result and result.get("success"):
            print(f"✅ 获取结算明细成功，共 {len(result['data']['details'])} 条明细")

    # 10. 测试增强统计
    print("\n[测试10] 获取增强统计数据")
    start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    end_date = datetime.now().strftime("%Y-%m-%d")

    response = requests.get(
        f"{API_BASE}/statistics/enhanced?start_date={start_date}&end_date={end_date}"
    )
    result = print_response(response, "获取增强统计数据")

    if result and result.get("success"):
        print("✅ 获取增强统计数据成功")
        print(f"   总预约数: {result['data']['overview']['total_bookings']}")
        print(f"   总时长: {result['data']['overview']['total_hours']}小时")
        print(f"   实际收入: ¥{result['data']['overview']['actual_revenue']}")

    # 11. 测试操作日志
    print("\n[测试11] 获取操作日志")
    response = requests.get(f"{API_BASE}/operation-logs?page=1&page_size=10")
    result = print_response(response, "获取操作日志")

    if result and result.get("success"):
        print(f"✅ 获取操作日志成功，共 {result['data']['total']} 条记录")

    # 12. 测试软删除
    print("\n[测试12] 软删除预约记录")
    if booking_id:
        response = requests.delete(f"{API_BASE}/booking/{booking_id}?operator=API测试")
        result = print_response(response, "软删除预约记录")

        if result and result.get("success"):
            print("✅ 软删除预约记录成功")

    # 13. 测试批量删除
    print("\n[测试13] 批量软删除预约记录")
    if booking_ids:
        batch_delete_data = {
            "booking_ids": booking_ids[:2]  # 删除前2个
        }

        response = requests.post(
            f"{API_BASE}/bookings/batch-delete?operator=API测试", json=batch_delete_data
        )
        result = print_response(response, "批量软删除预约记录")

        if result and result.get("success"):
            print(f"✅ 批量软删除成功: {result.get('message')}")

    print("\n" + "=" * 60)
    print("所有API测试完成！")
    print("=" * 60)


if __name__ == "__main__":
    try:
        test_api()
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {str(e)}")
        import traceback

        traceback.print_exc()
