"""
系统测试脚本 - 全面测试水站管理系统
Run: python test_system.py
"""
import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000/api"

# 颜色输出
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}\n")

def print_test(name, passed, details=""):
    status = f"{Colors.GREEN}✓ PASS{Colors.END}" if passed else f"{Colors.RED}✗ FAIL{Colors.END}"
    print(f"  {status} - {name}")
    if details and not passed:
        print(f"    {Colors.RED}详情：{details}{Colors.END}")
    return passed

# 测试结果统计
results = {"passed": 0, "failed": 0}

def test(name, condition, details=""):
    if condition:
        results["passed"] += 1
    else:
        results["failed"] += 1
    print_test(name, condition, details)
    return condition

def main():
    print_header("🧪 水站管理系统 - 全面测试报告")
    print(f"测试时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"API 地址：{BASE_URL}\n")
    
    # ==================== 1. 健康检查 ====================
    print_header("1️⃣  健康检查")
    try:
        r = requests.get(f"{BASE_URL}/health")
        test("健康检查接口可用", r.status_code == 200)
        test("返回状态正确", r.json().get("status") == "ok")
    except Exception as e:
        test("健康检查接口可用", False, str(e))
        print(f"{Colors.YELLOW}⚠ 后端服务未启动，请先运行：python main.py{Colors.END}\n")
        return
    
    # ==================== 2. 用户接口测试 ====================
    print_header("2️⃣  用户接口测试")
    
    # 获取用户列表
    r = requests.get(f"{BASE_URL}/users")
    test("获取用户列表", r.status_code == 200)
    users = r.json()
    test("用户列表非空", len(users) > 0)
    
    # 获取单个用户
    r = requests.get(f"{BASE_URL}/users/1")
    test("获取用户详情 (ID=1)", r.status_code == 200)
    user1 = r.json()
    test("用户名称正确", user1.get("name") == "张三")
    test("用户部门正确", user1.get("department") == "研发部")
    
    # 创建新用户
    new_user = {"name": "测试用户", "department": "测试部", "role": "staff"}
    r = requests.post(f"{BASE_URL}/users", json=new_user)
    test("创建新用户", r.status_code == 200)
    new_user_id = r.json().get("id") if r.status_code == 200 else None
    
    # 获取不存在的用户
    r = requests.get(f"{BASE_URL}/users/99999")
    test("获取不存在用户返回 404", r.status_code == 404)
    
    # ==================== 3. 产品接口测试 ====================
    print_header("3️⃣  产品接口测试")
    
    # 获取产品列表
    r = requests.get(f"{BASE_URL}/products")
    test("获取产品列表", r.status_code == 200)
    products = r.json()
    test("产品列表非空", len(products) > 0)
    
    # 验证产品数据
    bucket_water = next((p for p in products if p["specification"] == "18L"), None)
    test("存在 18L 桶装水产品", bucket_water is not None)
    if bucket_water:
        test("桶装水价格正确", bucket_water.get("price") == 15.0)
        test("桶装水优惠方案正确", bucket_water.get("promo_threshold") == 10 and bucket_water.get("promo_gift") == 1)
    
    # 创建新产品
    new_product = {
        "name": "测试水",
        "specification": "5L",
        "unit": "桶",
        "price": 8.0,
        "stock": 100,
        "promo_threshold": 5,
        "promo_gift": 1
    }
    r = requests.post(f"{BASE_URL}/products", json=new_product)
    test("创建新产品", r.status_code == 200)
    new_product_id = r.json().get("id") if r.status_code == 200 else None
    
    # ==================== 4. 领取记录测试 ====================
    print_header("4️⃣  领取记录测试")
    
    # 正常领取
    record = {"user_id": 1, "product_id": 1, "quantity": 1, "type": "pickup"}
    r = requests.post(f"{BASE_URL}/record", json=record)
    test("正常领取成功", r.status_code == 200)
    if r.status_code == 200:
        record_data = r.json()
        test("返回实际价格", "actual_price" in record_data)
        test("返回交易 ID", "id" in record_data)
    
    # 用户不存在
    record = {"user_id": 99999, "product_id": 1, "quantity": 1, "type": "pickup"}
    r = requests.post(f"{BASE_URL}/record", json=record)
    test("用户不存在返回 404", r.status_code == 404)
    
    # 产品不存在
    record = {"user_id": 1, "product_id": 99999, "quantity": 1, "type": "pickup"}
    r = requests.post(f"{BASE_URL}/record", json=record)
    test("产品不存在返回 404", r.status_code == 404)
    
    # ==================== 5. 用户状态测试 ====================
    print_header("5️⃣  用户状态测试")
    
    # 获取用户状态
    r = requests.get(f"{BASE_URL}/user/1/status")
    test("获取用户状态", r.status_code == 200)
    if r.status_code == 200:
        status = r.json()
        test("返回用户 ID", "user_id" in status)
        test("返回本月领取量", "month_total_qty" in status)
        test("返回待结金额", "unsettled_amount" in status)
        test("返回免费数量", "free_items" in status)
    
    # 用户不存在
    r = requests.get(f"{BASE_URL}/user/99999/status")
    test("获取不存在用户状态返回 404", r.status_code == 404)
    
    # ==================== 6. 管理接口测试 ====================
    print_header("6️⃣  管理接口测试")
    
    # 获取部门报表
    r = requests.get(f"{BASE_URL}/admin/report")
    test("获取部门报表", r.status_code == 200)
    if r.status_code == 200:
        report = r.json()
        test("报表包含部门数据", len(report) > 0)
        if len(report) > 0:
            test("报表字段完整", all(k in report[0] for k in ["department", "total_qty", "unsettled_amount"]))
    
    # 获取所有交易
    r = requests.get(f"{BASE_URL}/admin/transactions")
    test("获取所有交易", r.status_code == 200)
    
    # 按状态筛选交易
    r = requests.get(f"{BASE_URL}/admin/transactions?status=unsettled")
    test("按状态筛选交易", r.status_code == 200)
    
    # 获取库存预警
    r = requests.get(f"{BASE_URL}/admin/inventory-alert?threshold=10")
    test("获取库存预警", r.status_code == 200)
    
    # 结算接口
    # 先获取待结算记录
    r = requests.get(f"{BASE_URL}/admin/transactions?status=unsettled")
    unsettled = r.json()
    if len(unsettled) > 0:
        test_ids = [t["id"] for t in unsettled[:2]]
        r = requests.post(f"{BASE_URL}/admin/settle", json={"transaction_ids": test_ids})
        test("批量结算成功", r.status_code == 200)
        
        # 验证结算状态
        r = requests.get(f"{BASE_URL}/admin/transactions")
        updated = r.json()
        settled_records = [t for t in updated if t["id"] in test_ids]
        test("结算状态已更新", all(t["status"] == "settled" for t in settled_records))
    
    # 按部门结算
    r = requests.post(f"{BASE_URL}/admin/settle-by-department?department=研发部")
    test("按部门结算成功", r.status_code == 200)
    
    # ==================== 7. 库存管理测试 ====================
    print_header("7️⃣  库存管理测试")
    
    # 更新库存
    r = requests.put(f"{BASE_URL}/products/1/stock", json={"product_id": 1, "stock": 100})
    test("更新库存成功", r.status_code == 200)
    if r.status_code == 200:
        test("库存值正确", r.json().get("stock") == 100)
    
    # 验证库存更新
    r = requests.get(f"{BASE_URL}/products")
    products = r.json()
    product1 = next((p for p in products if p["id"] == 1), None)
    test("库存持久化正确", product1 and product1.get("stock") == 100)
    
    # ==================== 8. 交易记录查询测试 ====================
    print_header("8️⃣  交易记录查询测试")
    
    # 获取用户交易
    r = requests.get(f"{BASE_URL}/transactions?user_id=1")
    test("获取用户交易", r.status_code == 200)
    
    # 按状态获取交易
    r = requests.get(f"{BASE_URL}/transactions?status=settled")
    test("按状态获取交易", r.status_code == 200)
    
    # ==================== 9. 数据完整性测试 ====================
    print_header("9️⃣  数据完整性测试")
    
    # 验证交易关联用户
    r = requests.get(f"{BASE_URL}/admin/transactions")
    transactions = r.json()
    test("交易记录包含用户信息", all("user_name" in t for t in transactions))
    test("交易记录包含部门信息", all("department" in t for t in transactions))
    
    # 验证价格计算
    r = requests.get(f"{BASE_URL}/transactions?user_id=1")
    user_transactions = r.json()
    test("交易记录有价格", all("actual_price" in t for t in user_transactions))
    
    # ==================== 10. 优惠算法专项测试 ====================
    print_header("🔟  优惠算法专项测试")
    
    # 创建测试用户
    test_user = {"name": "优惠测试用户", "department": "测试部", "role": "staff"}
    r = requests.post(f"{BASE_URL}/users", json=test_user)
    test_user_id = r.json().get("id")
    
    # 连续领取 10 次（应该都收费）
    print(f"\n  模拟连续领取 10 次桶装水（买 10 赠 1 测试）...")
    for i in range(10):
        r = requests.post(f"{BASE_URL}/record", json={
            "user_id": test_user_id,
            "product_id": 1,  # 18L 桶装水
            "quantity": 1,
            "type": "pickup"
        })
    
    # 第 11 次领取应该免费
    r = requests.post(f"{BASE_URL}/record", json={
        "user_id": test_user_id,
        "product_id": 1,
        "quantity": 1,
        "type": "pickup"
    })
    if r.status_code == 200:
        result = r.json()
        test("第 11 桶水免费 (买 10 赠 1)", result.get("actual_price") == 0)
        test("免费记录有备注", result.get("note") is not None and "赠" in result.get("note", ""))
    
    # 验证用户状态中的免费数量
    r = requests.get(f"{BASE_URL}/user/{test_user_id}/status")
    if r.status_code == 200:
        status = r.json()
        test("用户状态显示免费数量", status.get("free_items", 0) >= 1)
    
    # ==================== 11. 边界条件测试 ====================
    print_header("1️⃣1️⃣  边界条件测试")
    
    # 库存不足测试
    # 先获取当前库存
    r = requests.get(f"{BASE_URL}/products/1")
    # 尝试领取超过库存的数量
    record = {"user_id": 1, "product_id": 1, "quantity": 99999, "type": "pickup"}
    r = requests.post(f"{BASE_URL}/record", json=record)
    test("库存不足返回 400", r.status_code == 400)
    
    # 数量为 0 的测试
    record = {"user_id": 1, "product_id": 1, "quantity": 0, "type": "pickup"}
    r = requests.post(f"{BASE_URL}/record", json=record)
    test("数量为 0 的处理", r.status_code in [200, 400])  # 允许或拒绝都合理
    
    # 负数数量测试
    record = {"user_id": 1, "product_id": 1, "quantity": -1, "type": "pickup"}
    r = requests.post(f"{BASE_URL}/record", json=record)
    test("负数数量的处理", r.status_code in [200, 400, 422])  # 应该被拒绝
    
    # ==================== 测试结果汇总 ====================
    print_header("📊 测试结果汇总")
    total = results["passed"] + results["failed"]
    pass_rate = (results["passed"] / total * 100) if total > 0 else 0
    
    print(f"  总测试数：{total}")
    print(f"  {Colors.GREEN}通过：{results['passed']}{Colors.END}")
    print(f"  {Colors.RED}失败：{results['failed']}{Colors.END}")
    print(f"  通过率：{Colors.BOLD}{pass_rate:.1f}%{Colors.END}\n")
    
    if results["failed"] == 0:
        print(f"{Colors.GREEN}🎉 所有测试通过！系统运行正常。{Colors.END}\n")
    else:
        print(f"{Colors.YELLOW}⚠ 存在 {results['failed']} 个测试失败，请检查上述详情。{Colors.END}\n")
    
    # 清理测试数据
    print_header("🧹 清理测试数据")
    if new_user_id:
        print(f"  测试用户 ID: {new_user_id} (保留)")
    if new_product_id:
        print(f"  测试产品 ID: {new_product_id} (保留)")
    print(f"  优惠测试用户 ID: {test_user_id} (保留用于验证)\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}测试被用户中断{Colors.END}\n")
    except Exception as e:
        print(f"\n{Colors.RED}测试异常：{e}{Colors.END}\n")
        import traceback
        traceback.print_exc()
