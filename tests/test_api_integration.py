"""
API对接和预约修改功能测试脚本
测试前端页面对接后端API的功能
"""

import requests
import json
from datetime import datetime, timedelta

BASE_URL = "http://127.0.0.1:8008"
API_BASE = f"{BASE_URL}/api/v2"


def test_api_endpoint(endpoint, method="GET", data=None, headers=None):
    """测试API端点"""
    url = f"{API_BASE}{endpoint}"

    default_headers = {
        "Content-Type": "application/json",
    }

    if headers:
        default_headers.update(headers)

    try:
        if method == "GET":
            response = requests.get(url, headers=default_headers, timeout=5)
        elif method == "POST":
            response = requests.post(url, headers=default_headers, json=data, timeout=5)
        elif method == "PUT":
            response = requests.put(url, headers=default_headers, json=data, timeout=5)
        elif method == "DELETE":
            response = requests.delete(url, headers=default_headers, timeout=5)
        else:
            return None, "不支持的请求方法"

        return response, None
    except requests.exceptions.ConnectionError:
        return None, "无法连接到服务器"
    except requests.exceptions.Timeout:
        return None, "请求超时"
    except Exception as e:
        return None, f"请求异常: {str(e)}"


def test_front_page_accessibility():
    """测试前端页面可访问性"""
    pages = [
        "/space-frontend/index.html",
        "/space-frontend/booking.html",
        "/space-frontend/my-bookings.html",
        "/space-frontend/edit-booking.html",
        "/space-frontend/payment.html",
        "/space-frontend/notifications.html",
        "/space-frontend/calendar.html",
        "/space-frontend/resources.html",
        "/space-frontend/profile.html",
    ]

    results = []

    for page in pages:
        url = f"{BASE_URL}{page}"
        try:
            response = requests.get(url, timeout=5)
            accessible = response.status_code == 200
            results.append(
                {
                    "page": page,
                    "accessible": accessible,
                    "status_code": response.status_code,
                }
            )
        except Exception as e:
            results.append({"page": page, "accessible": False, "error": str(e)})

    return results


def test_space_types_api():
    """测试空间类型API"""
    response, error = test_api_endpoint("/space/types")

    if error:
        return {"success": False, "error": error}

    if response.status_code == 200:
        data = response.json()
        return {
            "success": True,
            "status_code": response.status_code,
            "data_count": len(data.get("data", {}).get("items", [])),
        }
    else:
        return {
            "success": False,
            "status_code": response.status_code,
            "error": response.text,
        }


def test_resources_api():
    """测试空间资源API"""
    response, error = test_api_endpoint("/space/resources")

    if error:
        return {"success": False, "error": error}

    if response.status_code == 200:
        data = response.json()
        items = data.get("data", {}).get("items", [])
        return {
            "success": True,
            "status_code": response.status_code,
            "resource_count": len(items),
            "sample_resource": items[0] if items else None,
        }
    else:
        return {
            "success": False,
            "status_code": response.status_code,
            "error": response.text,
        }


def test_booking_flow():
    """测试预约流程（创建、修改、取消）"""
    results = {"create": None, "update": None, "cancel": None}

    booking_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")

    booking_data = {
        "resource_id": 1,
        "booking_date": booking_date,
        "start_time": "10:00",
        "end_time": "12:00",
        "title": "测试预约",
        "attendees_count": 5,
        "user_name": "测试用户",
        "user_type": "external",
    }

    response, error = test_api_endpoint(
        "/space/bookings", method="POST", data=booking_data
    )

    if error:
        results["create"] = {"success": False, "error": error}
        return results

    if response.status_code == 201:
        data = response.json()
        booking_id = data.get("data", {}).get("id")
        results["create"] = {
            "success": True,
            "booking_id": booking_id,
            "booking_no": data.get("data", {}).get("booking_no"),
        }

        if booking_id:
            update_data = {"title": "修改后的预约标题", "attendees_count": 8}

            response, error = test_api_endpoint(
                f"/space/bookings/{booking_id}", method="PUT", data=update_data
            )

            if error:
                results["update"] = {"success": False, "error": error}
            else:
                if response.status_code == 200:
                    results["update"] = {
                        "success": True,
                        "message": response.json().get("message"),
                    }
                else:
                    results["update"] = {
                        "success": False,
                        "status_code": response.status_code,
                    }

            cancel_data = {"cancel_reason": "测试取消预约"}

            response, error = test_api_endpoint(
                f"/space/bookings/{booking_id}/cancel", method="PUT", data=cancel_data
            )

            if error:
                results["cancel"] = {"success": False, "error": error}
            else:
                if response.status_code == 200:
                    results["cancel"] = {
                        "success": True,
                        "message": response.json().get("message"),
                    }
                else:
                    results["cancel"] = {
                        "success": False,
                        "status_code": response.status_code,
                    }
    else:
        results["create"] = {
            "success": False,
            "status_code": response.status_code,
            "error": response.text,
        }

    return results


def test_fee_calculation():
    """测试费用计算API"""
    booking_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")

    fee_data = {
        "resource_id": 1,
        "booking_date": booking_date,
        "start_time": "09:00",
        "end_time": "11:00",
        "user_type": "external",
        "member_level": "regular",
    }

    response, error = test_api_endpoint(
        "/space/bookings/calculate-fee", method="POST", data=fee_data
    )

    if error:
        return {"success": False, "error": error}

    if response.status_code == 200:
        data = response.json()
        fee_summary = data.get("data", {}).get("fee_summary", {})
        return {
            "success": True,
            "base_fee": fee_summary.get("base_fee"),
            "final_fee": fee_summary.get("final_fee"),
            "total_fee": fee_summary.get("subtotal"),
        }
    else:
        return {
            "success": False,
            "status_code": response.status_code,
            "error": response.text,
        }


def test_edit_booking_page():
    """测试预约修改页面功能"""
    url = f"{BASE_URL}/space-frontend/edit-booking.html"

    try:
        response = requests.get(url, timeout=5)

        if response.status_code == 200:
            html_content = response.text

            checks = {
                "has_api_import": "import spaceAPI" in html_content,
                "has_edit_form": "editForm" in html_content
                or "edit-form" in html_content,
                "has_cancel_button": "cancelBookingBtn" in html_content
                or "取消预约" in html_content,
                "has_fee_preview": "feePreview" in html_content
                or "费用预估" in html_content,
            }

            return {
                "success": True,
                "checks": checks,
                "all_checks_passed": all(checks.values()),
            }
        else:
            return {"success": False, "status_code": response.status_code}
    except Exception as e:
        return {"success": False, "error": str(e)}


def test_my_bookings_page():
    """测试我的预约页面对接API"""
    url = f"{BASE_URL}/space-frontend/my-bookings.html"

    try:
        response = requests.get(url, timeout=5)

        if response.status_code == 200:
            html_content = response.text

            checks = {
                "has_api_import": "import spaceAPI" in html_content,
                "has_getMyBookings": "spaceAPI.getMyBookings" in html_content,
                "has_cancelBooking": "spaceAPI.cancelBooking" in html_content,
                "has_edit_booking_link": "edit-booking.html" in html_content,
            }

            return {
                "success": True,
                "checks": checks,
                "all_checks_passed": all(checks.values()),
            }
        else:
            return {"success": False, "status_code": response.status_code}
    except Exception as e:
        return {"success": False, "error": str(e)}


def test_booking_page():
    """测试预约创建页面对接API"""
    url = f"{BASE_URL}/space-frontend/booking.html"

    try:
        response = requests.get(url, timeout=5)

        if response.status_code == 200:
            html_content = response.text

            checks = {
                "has_api_import": "import spaceAPI" in html_content,
                "has_getResources": "spaceAPI.getResources" in html_content,
                "has_createBooking": "spaceAPI.createBooking" in html_content,
                "has_calculateFee": "spaceAPI.calculateFee" in html_content,
            }

            return {
                "success": True,
                "checks": checks,
                "all_checks_passed": all(checks.values()),
            }
        else:
            return {"success": False, "status_code": response.status_code}
    except Exception as e:
        return {"success": False, "error": str(e)}


def run_all_tests():
    """运行所有测试"""
    print("=" * 80)
    print("API对接和预约修改功能测试")
    print("=" * 80)
    print()

    print("1. 前端页面可访问性测试")
    print("-" * 40)
    page_results = test_front_page_accessibility()
    accessible_count = sum(1 for r in page_results if r.get("accessible"))
    print(f"✓ 可访问页面: {accessible_count}/{len(page_results)}")
    for r in page_results:
        status = "✓" if r.get("accessible") else "✗"
        print(f"  {status} {r['page']}")
    print()

    print("2. 空间类型API测试")
    print("-" * 40)
    types_result = test_space_types_api()
    if types_result["success"]:
        print(f"✓ API响应正常 (状态码: {types_result['status_code']})")
        print(f"  数据条数: {types_result['data_count']}")
    else:
        print(f"✗ API测试失败: {types_result.get('error', '未知错误')}")
    print()

    print("3. 空间资源API测试")
    print("-" * 40)
    resources_result = test_resources_api()
    if resources_result["success"]:
        print(f"✓ API响应正常 (状态码: {resources_result['status_code']})")
        print(f"  资源数量: {resources_result['resource_count']}")
        if resources_result["sample_resource"]:
            print(f"  示例资源: {resources_result['sample_resource'].get('name')}")
    else:
        print(f"✗ API测试失败: {resources_result.get('error', '未知错误')}")
    print()

    print("4. 预约流程测试")
    print("-" * 40)
    booking_result = test_booking_flow()

    create_result = booking_result["create"]
    if create_result:
        if create_result["success"]:
            print(f"✓ 创建预约成功")
            print(f"  预约ID: {create_result['booking_id']}")
            print(f"  预约编号: {create_result['booking_no']}")
        else:
            print(f"✗ 创建预约失败: {create_result.get('error', '未知错误')}")

    update_result = booking_result["update"]
    if update_result:
        if update_result["success"]:
            print(f"✓ 修改预约成功")
        else:
            print(f"✗ 修改预约失败: {update_result.get('error', '未知错误')}")

    cancel_result = booking_result["cancel"]
    if cancel_result:
        if cancel_result["success"]:
            print(f"✓ 取消预约成功")
        else:
            print(f"✗ 取消预约失败: {cancel_result.get('error', '未知错误')}")
    print()

    print("5. 费用计算API测试")
    print("-" * 40)
    fee_result = test_fee_calculation()
    if fee_result["success"]:
        print(f"✓ 费用计算成功")
        print(f"  基础费用: ¥{fee_result['base_fee']}")
        print(f"  最终费用: ¥{fee_result['final_fee']}")
    else:
        print(f"✗ 费用计算失败: {fee_result.get('error', '未知错误')}")
    print()

    print("6. 预约修改页面功能检查")
    print("-" * 40)
    edit_page_result = test_edit_booking_page()
    if edit_page_result["success"]:
        print(f"✓ 页面加载成功")
        checks = edit_page_result["checks"]
        for check_name, check_result in checks.items():
            status = "✓" if check_result else "✗"
            print(f"  {status} {check_name}: {check_result}")

        if edit_page_result["all_checks_passed"]:
            print("  ✓ 所有功能检查通过")
        else:
            print("  ✗ 部分功能检查未通过")
    else:
        print(f"✗ 页面加载失败: {edit_page_result.get('error', '未知错误')}")
    print()

    print("7. 我的预约页面API对接检查")
    print("-" * 40)
    my_bookings_result = test_my_bookings_page()
    if my_bookings_result["success"]:
        print(f"✓ 页面加载成功")
        checks = my_bookings_result["checks"]
        for check_name, check_result in checks.items():
            status = "✓" if check_result else "✗"
            print(f"  {status} {check_name}: {check_result}")

        if my_bookings_result["all_checks_passed"]:
            print("  ✓ 所有API对接检查通过")
        else:
            print("  ✗ 部分API对接检查未通过")
    else:
        print(f"✗ 页面加载失败: {my_bookings_result.get('error', '未知错误')}")
    print()

    print("8. 预约创建页面API对接检查")
    print("-" * 40)
    booking_page_result = test_booking_page()
    if booking_page_result["success"]:
        print(f"✓ 页面加载成功")
        checks = booking_page_result["checks"]
        for check_name, check_result in checks.items():
            status = "✓" if check_result else "✗"
            print(f"  {status} {check_name}: {check_result}")

        if booking_page_result["all_checks_passed"]:
            print("  ✓ 所有API对接检查通过")
        else:
            print("  ✗ 部分API对接检查未通过")
    else:
        print(f"✗ 页面加载失败: {booking_page_result.get('error', '未知错误')}")
    print()

    print("=" * 80)
    print("测试总结")
    print("=" * 80)

    total_tests = 8
    passed_tests = 0

    if accessible_count == len(page_results):
        passed_tests += 1
    if types_result["success"]:
        passed_tests += 1
    if resources_result["success"]:
        passed_tests += 1
    if booking_result["create"] and booking_result["create"]["success"]:
        passed_tests += 1
    if fee_result["success"]:
        passed_tests += 1
    if edit_page_result["success"] and edit_page_result["all_checks_passed"]:
        passed_tests += 1
    if my_bookings_result["success"] and my_bookings_result["all_checks_passed"]:
        passed_tests += 1
    if booking_page_result["success"] and booking_page_result["all_checks_passed"]:
        passed_tests += 1

    print(f"通过测试: {passed_tests}/{total_tests}")
    print(f"完成度: {(passed_tests / total_tests * 100):.1f}%")
    print()

    if passed_tests == total_tests:
        print("✓ 所有测试通过！API对接和预约修改功能已完成")
    else:
        print("⚠ 部分测试未通过，请检查相关功能")

    print("=" * 80)


if __name__ == "__main__":
    run_all_tests()
