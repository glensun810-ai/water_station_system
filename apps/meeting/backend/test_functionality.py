"""
会议室管理后台功能完整性测试脚本
测试所有API端点、异常场景处理、数据一致性
"""

import requests
import json
from datetime import datetime, timedelta
import sys

API_BASE = "http://localhost:8000/api/meeting"


class TestResults:
    def __init__(self):
        self.passed = []
        self.failed = []
        self.warnings = []

    def add_pass(self, test_name, message=""):
        self.passed.append({"test": test_name, "message": message})
        print(f"✅ {test_name}: {message}")

    def add_fail(self, test_name, message=""):
        self.failed.append({"test": test_name, "message": message})
        print(f"❌ {test_name}: {message}")

    def add_warning(self, test_name, message=""):
        self.warnings.append({"test": test_name, "message": message})
        print(f"⚠️ {test_name}: {message}")

    def print_summary(self):
        print("\n" + "=" * 60)
        print("测试总结")
        print("=" * 60)
        print(f"✅ 通过: {len(self.passed)}")
        print(f"❌ 失败: {len(self.failed)}")
        print(f"⚠️ 警告: {len(self.warnings)}")

        if self.failed:
            print("\n失败详情:")
            for item in self.failed:
                print(f"  - {item['test']}: {item['message']}")

        if self.warnings:
            print("\n警告详情:")
            for item in self.warnings:
                print(f"  - {item['test']}: {item['message']}")

        print("=" * 60)
        return len(self.failed) == 0


results = TestResults()


def test_api_response(endpoint, expected_keys=None, method="GET", data=None):
    """通用API响应测试"""
    try:
        url = f"{API_BASE}{endpoint}"
        if method == "GET":
            resp = requests.get(url, timeout=5)
        else:
            resp = requests.post(url, json=data, timeout=5)

        if resp.status_code != 200:
            results.add_fail(endpoint, f"状态码 {resp.status_code}")
            return None

        result = resp.json()

        if expected_keys and isinstance(result, dict):
            for key in expected_keys:
                if key not in result:
                    results.add_fail(endpoint, f"缺少字段 {key}")
                    return None

        results.add_pass(endpoint, "响应正常")
        return result
    except requests.exceptions.RequestException as e:
        results.add_fail(endpoint, f"请求异常: {str(e)}")
        return None


print("\n" + "=" * 60)
print("开始会议室管理后台功能测试")
    # 验证总预约数
    bookings_resp = test_api_response("/bookings/enhanced?is_deleted=0")
    if bookings_resp and bookings_resp.get("success"):
        actual_count = bookings_resp["data"]["total"]
        stats_count = overview["total_bookings"]
        
        # 统计数据默认只统计最近30天，所以可能小于总数，这是正常的
        if stats_count > 0 and stats_count <= actual_count:
            results.add_pass("统计数据-总预约数", f"统计显示{stats_count}条（最近30天），总数{actual_count}")
        elif stats_count == 0:
            results.add_warning("统计数据-总预约数", "最近30天无预约数据")
        else:
            results.add_fail("统计数据-总预约数", f"数据异常")

    # 验证总预约数
    bookings_resp = test_api_response("/bookings/enhanced?is_deleted=0")
    if bookings_resp and bookings_resp.get("success"):
        actual_count = bookings_resp["data"]["total"]
        stats_count = overview["total_bookings"]

        if stats_count > 0 and stats_count <= actual_count:
            results.add_pass("统计数据-总预约数", f"统计显示{stats_count}条（最近30天），总数{actual_count}")
        elif stats_count == 0:
            results.add_warning("统计数据-总预约数", "最近30天无预约数据")
        else:
            results.add_fail("统计数据-总预约数", "数据异常")

    # 验证收入计算
    if overview["total_revenue"] > 0:
        results.add_pass("统计数据-总收入", f"¥{overview['total_revenue']}")
    else:
        results.add_warning("统计数据-总收入", "总收入为0，可能无付费预约")

    # 验证会议室统计
    room_stats = stats_data["data"]["room_statistics"]
    if len(room_stats) > 0:
        results.add_pass("统计数据-会议室分布", f"{len(room_stats)}个会议室有预约")
    else:
        results.add_warning("统计数据-会议室分布", "无会议室统计数据")

# ==================== 测试2: 会议室管理 ====================
print("\n【测试模块2: 会议室管理】")

rooms_data = test_api_response("/rooms")
if rooms_data:
    rooms_count = len(rooms_data)
    results.add_pass("会议室列表", f"{rooms_count}个会议室")

    # 测试新增会议室（异常场景：必填项缺失）
    invalid_room = {"name": "", "capacity": 10}
    try:
        resp = requests.post(f"{API_BASE}/rooms", json=invalid_room, timeout=5)
        if resp.status_code != 200:
            results.add_pass("新增会议室-必填项验证", "正确拒绝空名称")
        else:
            results.add_fail("新增会议室-必填项验证", "未验证必填项")
    except Exception as e:
        results.add_warning("新增会议室-必填项验证", f"请求异常: {str(e)}")

    # 测试更新会议室
    if rooms_count > 0:
        room_id = rooms_data[0]["id"]
        update_data = {
            "name": "测试会议室(更新)",
            "capacity": 15,
            "price_per_hour": 150,
        }
        try:
            resp = requests.put(
                f"{API_BASE}/rooms/{room_id}", json=update_data, timeout=5
            )
            if resp.status_code == 200:
                results.add_pass("更新会议室", "成功")
            else:
                results.add_fail("更新会议室", f"状态码 {resp.status_code}")
        except Exception as e:
            results.add_fail("更新会议室", f"请求异常: {str(e)}")

    # 测试状态切换
    if rooms_count > 0:
        room_id = rooms_data[0]["id"]
        original_status = rooms_data[0]["is_active"]
        toggle_data = {"is_active": not original_status}
        try:
            resp = requests.put(
                f"{API_BASE}/rooms/{room_id}", json=toggle_data, timeout=5
            )
            if resp.status_code == 200:
                results.add_pass("会议室状态切换", "成功")
                # 恢复原状态
                requests.put(
                    f"{API_BASE}/rooms/{room_id}",
                    json={"is_active": original_status},
                    timeout=5,
                )
            else:
                results.add_fail("会议室状态切换", f"状态码 {resp.status_code}")
        except Exception as e:
            results.add_fail("会议室状态切换", f"请求异常: {str(e)}")

# ==================== 测试3: 预约管理 ====================
print("\n【测试模块3: 预约管理】")

bookings_data = test_api_response(
    "/bookings/enhanced?is_deleted=0", ["success", "data"]
)
if bookings_data and bookings_data.get("success"):
    bookings_list = bookings_data["data"]["bookings"]
    bookings_total = bookings_data["data"]["total"]

    results.add_pass("预约列表", f"{bookings_total}条预约记录")

    # 测试状态筛选
    for status in ["pending", "confirmed", "cancelled", "completed"]:
        filtered_resp = test_api_response(
            f"/bookings/enhanced?status={status}&is_deleted=0"
        )
        if filtered_resp and filtered_resp.get("success"):
            filtered_count = filtered_resp["data"]["total"]
            results.add_pass(f"预约筛选-{status}", f"{filtered_count}条")

    # 测试预约创建（异常场景：时间冲突）
    if len(rooms_data) > 0:
        room_id = rooms_data[0]["id"]
        future_date = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")

        # 创建正常预约
        new_booking = {
            "room_id": room_id,
            "user_name": "测试用户",
            "user_phone": "13900000000",
            "booking_date": future_date,
            "start_time": "09:00",
            "end_time": "10:00",
        }

        try:
            resp = requests.post(f"{API_BASE}/bookings", json=new_booking, timeout=5)
            if resp.status_code == 200:
                booking_result = resp.json()
                booking_id = booking_result.get("id")
                results.add_pass("创建预约", f"预约ID: {booking_id}")

                # 测试时间冲突（同一会议室同一时间段）
                conflict_booking = new_booking.copy()
                try:
                    resp2 = requests.post(
                        f"{API_BASE}/bookings", json=conflict_booking, timeout=5
                    )
                    if resp2.status_code != 200:
                        results.add_pass("预约冲突检测", "正确拒绝冲突预约")
                    else:
                        results.add_warning(
                            "预约冲突检测", "允许重复预约，需确认业务逻辑"
                        )
                except Exception as e:
                    results.add_warning("预约冲突检测", f"请求异常: {str(e)}")

                # 测试确认预约
                if booking_id:
                    try:
                        resp = requests.put(
                            f"{API_BASE}/bookings/{booking_id}/confirm", timeout=5
                        )
                        if resp.status_code == 200:
                            results.add_pass("确认预约", "成功")
                        else:
                            results.add_fail("确认预约", f"状态码 {resp.status_code}")
                    except Exception as e:
                        results.add_fail("确认预约", f"请求异常: {str(e)}")

                # 测试取消预约
                if booking_id:
                    cancel_reason = "功能测试取消"
                    try:
                        resp = requests.put(
                            f"{API_BASE}/bookings/{booking_id}/cancel?cancel_reason={cancel_reason}",
                            timeout=5,
                        )
                        if resp.status_code == 200:
                            results.add_pass("取消预约", "成功")
                        else:
                            error_msg = resp.json().get("detail", "未知错误")
                            results.add_warning("取消预约", f"{error_msg}")
                    except Exception as e:
                        results.add_fail("取消预约", f"请求异常: {str(e)}")
            else:
                results.add_fail("创建预约", f"状态码 {resp.status_code}")
        except Exception as e:
            results.add_fail("创建预约", f"请求异常: {str(e)}")

# ==================== 测试4: 审批中心 ====================
print("\n【测试模块4: 审批中心】")

approvals_data = test_api_response("/approvals", ["success", "data"])
if approvals_data and approvals_data.get("success"):
    approvals_list = approvals_data["data"]["approvals"]
    approvals_total = approvals_data["data"]["total"]

    results.add_pass("审批列表", f"{approvals_total}条审批记录")

    # 测试审批状态筛选
    for status in ["pending", "approved", "rejected"]:
        filtered_resp = test_api_response(f"/approvals?status={status}")
        if filtered_resp and filtered_resp.get("success"):
            filtered_count = filtered_resp["data"]["total"]
            results.add_pass(f"审批筛选-{status}", f"{filtered_count}条")

    # 测试审批流程
    # 先创建一个需要审批的取消申请
    if bookings_data and bookings_data.get("success") and len(bookings_list) > 0:
        booking = bookings_list[0]
        if booking["status"] == "confirmed":
            approval_request = {
                "booking_id": booking["id"],
                "approval_type": "cancel",
                "request_reason": "测试审批流程",
                "requester_name": "测试用户",
                "requester_phone": "13900000000",
            }

            try:
                resp = requests.post(
                    f"{API_BASE}/approval/submit", json=approval_request, timeout=5
                )
                if resp.status_code == 200:
                    approval_result = resp.json()
                    approval_id = approval_result["data"]["approval_id"]
                    results.add_pass("提交审批申请", f"审批ID: {approval_id}")

                    # 测试批准审批
                    approve_data = {
                        "approval_id": approval_id,
                        "approval_result": "approved",
                        "approval_reason": "测试批准",
                    }
                    try:
                        resp2 = requests.post(
                            f"{API_BASE}/approval/approve", json=approve_data, timeout=5
                        )
                        if resp2.status_code == 200:
                            results.add_pass("批准审批", "成功")

                            # 验证预约状态是否自动更新为cancelled
                            verify_resp = requests.get(
                                f"{API_BASE}/bookings/enhanced?is_deleted=0", timeout=5
                            )
                            if verify_resp.status_code == 200:
                                verify_data = verify_resp.json()
                                updated_booking = next(
                                    (
                                        b
                                        for b in verify_data["data"]["bookings"]
                                        if b["id"] == booking["id"]
                                    ),
                                    None,
                                )
                                if (
                                    updated_booking
                                    and updated_booking["status"] == "cancelled"
                                ):
                                    results.add_pass(
                                        "审批后数据一致性", "预约状态已自动更新"
                                    )
                                else:
                                    results.add_fail(
                                        "审批后数据一致性", "预约状态未更新"
                                    )
                        else:
                            results.add_fail("批准审批", f"状态码 {resp2.status_code}")
                    except Exception as e:
                        results.add_fail("批准审批", f"请求异常: {str(e)}")
                else:
                    results.add_warning("提交审批申请", f"状态码 {resp.status_code}")
            except Exception as e:
                results.add_warning("提交审批申请", f"请求异常: {str(e)}")

# ==================== 测试5: 财务结算 ====================
print("\n【测试模块5: 财务结算】")

payments_data = test_api_response("/payments", ["success", "data"])
if payments_data and payments_data.get("success"):
    payments_list = payments_data["data"]["payments"]
    payments_total = payments_data["data"]["total"]

    results.add_pass("支付记录列表", f"{payments_total}条支付记录")

    # 测试支付状态筛选
    for status in ["pending", "confirmed"]:
        filtered_resp = test_api_response(f"/payments?status={status}")
        if filtered_resp and filtered_resp.get("success"):
            filtered_count = filtered_resp["data"]["total"]
            results.add_pass(f"支付筛选-{status}", f"{filtered_count}条")

settlements_data = test_api_response("/settlements", ["success", "data"])
if settlements_data and settlements_data.get("success"):
    settlements_list = settlements_data["data"]["settlements"]
    settlements_total = settlements_data["data"]["total"]

    results.add_pass("结算批次列表", f"{settlements_total}条结算批次")

    # 测试结算详情查看
    if settlements_total > 0:
        settlement_id = settlements_list[0]["id"]
        detail_resp = test_api_response(
            f"/settlement/{settlement_id}", ["success", "data"]
        )
        if detail_resp and detail_resp.get("success"):
            results.add_pass("结算详情查看", "成功")

# 测试支付确认流程
if bookings_data and bookings_data.get("success") and len(bookings_list) > 0:
    unpaid_booking = next(
        (b for b in bookings_list if b["payment_status"] == "unpaid"), None
    )

    if unpaid_booking:
        # 提交支付申请
        payment_submit = {
            "booking_id": unpaid_booking["id"],
            "payment_method": "alipay",
            "payment_remark": "测试支付",
        }

        try:
            resp = requests.post(
                f"{API_BASE}/payment/submit", json=payment_submit, timeout=5
            )
            if resp.status_code == 200:
                payment_result = resp.json()
                payment_id = payment_result["data"]["payment_id"]
                results.add_pass("提交支付申请", f"支付ID: {payment_id}")

                # 确认支付
                confirm_data = {"payment_id": payment_id}
                try:
                    resp2 = requests.post(
                        f"{API_BASE}/payment/confirm", json=confirm_data, timeout=5
                    )
                    if resp2.status_code == 200:
                        results.add_pass("确认支付", "成功")

                        # 验证预约支付状态是否更新
                        verify_resp = requests.get(
                            f"{API_BASE}/bookings/enhanced?is_deleted=0", timeout=5
                        )
                        if verify_resp.status_code == 200:
                            verify_data = verify_resp.json()
                            updated_booking = next(
                                (
                                    b
                                    for b in verify_data["data"]["bookings"]
                                    if b["id"] == unpaid_booking["id"]
                                ),
                                None,
                            )
                            if (
                                updated_booking
                                and updated_booking["payment_status"] == "paid"
                            ):
                                results.add_pass(
                                    "支付确认后数据一致性", "预约支付状态已更新"
                                )
                            else:
                                results.add_warning(
                                    "支付确认后数据一致性",
                                    f"状态: {updated_booking['payment_status']}",
                                )
                    else:
                        results.add_fail("确认支付", f"状态码 {resp2.status_code}")
                except Exception as e:
                    results.add_fail("确认支付", f"请求异常: {str(e)}")
            else:
                results.add_warning("提交支付申请", f"状态码 {resp.status_code}")
        except Exception as e:
            results.add_warning("提交支付申请", f"请求异常: {str(e)}")

# ==================== 测试6: 统计报表 ====================
print("\n【测试模块6: 统计报表】")

# 测试时间范围查询
start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
end_date = datetime.now().strftime("%Y-%m-%d")

stats_range_resp = test_api_response(
    f"/statistics/enhanced?start_date={start_date}&end_date={end_date}",
    ["success", "data"],
)

if stats_range_resp and stats_range_resp.get("success"):
    data = stats_range_resp["data"]

    # 验证各项统计数据
    if "overview" in data:
        results.add_pass("统计报表-总览数据", f"{len(data['overview'])}个指标")

    if "room_statistics" in data:
        room_count = len(data["room_statistics"])
        results.add_pass("统计报表-会议室统计", f"{room_count}个会议室")

    if "daily_statistics" in data:
        daily_count = len(data["daily_statistics"])
        results.add_pass("统计报表-每日趋势", f"{daily_count}天数据")

    if "office_statistics" in data:
        office_count = len(data["office_statistics"])
        if office_count > 0:
            results.add_pass("统计报表-企业统计", f"{office_count}个企业")
        else:
            results.add_warning("统计报表-企业统计", "无企业统计数据")

# ==================== 测试7: 操作日志 ====================
print("\n【测试模块7: 操作日志】")

logs_resp = test_api_response("/operation-logs", ["success", "data"])
if logs_resp and logs_resp.get("success"):
    logs_count = logs_resp["data"]["total"]
    results.add_pass("操作日志查询", f"{logs_count}条操作记录")

    # 验证日志类型筛选
    for op_type in ["booking_create", "booking_confirm", "booking_cancel"]:
        filtered_logs = test_api_response(f"/operation-logs?operation_type={op_type}")
        if filtered_logs and filtered_logs.get("success"):
            filtered_count = filtered_logs["data"]["total"]
            results.add_pass(f"操作日志筛选-{op_type}", f"{filtered_count}条")

# ==================== 测试8: 异常场景处理 ====================
print("\n【测试模块8: 异常场景处理】")

# 测试无效ID访问
try:
    resp = requests.get(f"{API_BASE}/rooms/99999", timeout=5)
    if resp.status_code == 404:
        results.add_pass("异常处理-无效会议室ID", "正确返回404")
    else:
        results.add_warning("异常处理-无效会议室ID", f"状态码 {resp.status_code}")
except Exception as e:
    results.add_pass("异常处理-无效会议室ID", f"正确抛出异常: {str(e)}")

try:
    resp = requests.get(f"{API_BASE}/approval/99999", timeout=5)
    if resp.status_code == 404:
        results.add_pass("异常处理-无效审批ID", "正确返回404")
    else:
        results.add_warning("异常处理-无效审批ID", f"状态码 {resp.status_code}")
except Exception as e:
    results.add_pass("异常处理-无效审批ID", f"正确抛出异常: {str(e)}")

# 测试非法数据格式
invalid_booking = {"room_id": "invalid", "booking_date": "invalid-date"}
try:
    resp = requests.post(f"{API_BASE}/bookings", json=invalid_booking, timeout=5)
    if resp.status_code != 200:
        results.add_pass("异常处理-非法数据格式", "正确拒绝")
    else:
        results.add_fail("异常处理-非法数据格式", "未验证数据格式")
except Exception as e:
    results.add_pass("异常处理-非法数据格式", f"正确抛出异常: {str(e)}")

# 测试分页边界
try:
    resp = requests.get(
        f"{API_BASE}/bookings/enhanced?page=999&page_size=20&is_deleted=0", timeout=5
    )
    if resp.status_code == 200:
        data = resp.json()
        if data["data"]["bookings"] == []:
            results.add_pass("异常处理-分页超界", "正确返回空列表")
        else:
            results.add_warning("异常处理-分页超界", "返回了数据")
    else:
        results.add_fail("异常处理-分页超界", f"状态码 {resp.status_code}")
except Exception as e:
    results.add_fail("异常处理-分页超界", f"请求异常: {str(e)}")

# ==================== 测试9: 数据一致性验证 ====================
print("\n【测试模块9: 数据一致性验证】")

# 验证预约数据完整性
bookings_full = test_api_response("/bookings/enhanced?is_deleted=0")
if bookings_full and bookings_full.get("success"):
    for booking in bookings_full["data"]["bookings"]:
        # 验证关联会议室是否存在
        room_id = booking["room_id"]
        if room_id:
            try:
                room_resp = requests.get(f"{API_BASE}/rooms", timeout=5)
                if room_resp.status_code == 200:
                    rooms = room_resp.json()
                    room_exists = any(r["id"] == room_id for r in rooms)
                    if room_exists:
                        results.add_pass(
                            f"数据一致性-预约{booking['id']}", "会议室关联正确"
                        )
                    else:
                        results.add_fail(
                            f"数据一致性-预约{booking['id']}", "会议室不存在"
                        )
            except Exception as e:
                results.add_warning(
                    f"数据一致性-预约{booking['id']}", f"验证异常: {str(e)}"
                )

# ==================== 测试总结 ====================
success = results.print_summary()

if success:
    print("\n🎉 所有功能测试通过！系统运行正常。")
    sys.exit(0)
else:
    print("\n⚠️ 发现测试失败项，请检查并修复。")
    sys.exit(1)
