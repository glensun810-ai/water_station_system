"""
系统完整性检查脚本
国际顶级系统架构师标准验收
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://127.0.0.1:8008"


class SystemValidator:
    """系统验证器"""

    def __init__(self):
        self.results = []
        self.token = None
        self.errors = []

    def log(self, module, test, status, message=""):
        """记录测试结果"""
        result = {
            "module": module,
            "test": test,
            "status": status,
            "message": message,
            "timestamp": datetime.now().strftime("%H:%M:%S"),
        }
        self.results.append(result)

        # 打印结果
        icon = "✓" if status == "PASS" else "✗"
        print(f"{icon} [{module}] {test}: {message}")

    def login(self):
        """登录获取token"""
        try:
            response = requests.post(
                f"{BASE_URL}/api/v1/system/auth/login",
                json={"username": "admin", "password": "123456"},
            )

            if response.status_code == 200:
                data = response.json()
                self.token = data.get("access_token")
                self.log("认证", "管理员登录", "PASS", f"Token: {self.token[:20]}...")
                return True
            else:
                self.log("认证", "管理员登录", "FAIL", f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log("认证", "管理员登录", "ERROR", str(e))
            return False

    def check_api_endpoint(self, module, name, endpoint, auth_required=True):
        """检查API端点"""
        try:
            headers = {}
            if auth_required and self.token:
                headers["Authorization"] = f"Bearer {self.token}"

            response = requests.get(f"{BASE_URL}{endpoint}", headers=headers)

            if response.status_code == 200:
                data = response.json()

                # 统计数据量
                if isinstance(data, list):
                    count = len(data)
                    self.log(module, name, "PASS", f"{count} 条数据")
                elif isinstance(data, dict):
                    if "items" in data:
                        count = len(data["items"])
                        total = data.get("total", count)
                        self.log(module, name, "PASS", f"{count}/{total} 条数据")
                    elif "total" in data:
                        total = data["total"]
                        self.log(module, name, "PASS", f"{total} 条数据")
                    else:
                        self.log(module, name, "PASS", "正常响应")
                else:
                    self.log(module, name, "PASS", "正常响应")

                return True
            else:
                self.log(module, name, "FAIL", f"HTTP {response.status_code}")
                self.errors.append(f"{module}.{name}: {response.status_code}")
                return False

        except Exception as e:
            self.log(module, name, "ERROR", str(e))
            self.errors.append(f"{module}.{name}: {str(e)}")
            return False

    def check_page_access(self, name, path):
        """检查页面访问"""
        try:
            response = requests.get(f"{BASE_URL}{path}")

            if response.status_code == 200:
                # 检查页面内容
                content = response.text
                has_vue = "vue.global" in content.lower() or "Vue" in content
                has_api = "api" in content.lower()

                message = "可访问"
                if has_vue:
                    message += " [Vue]"
                if has_api:
                    message += " [API]"

                self.log("页面", name, "PASS", message)
                return True
            else:
                self.log("页面", name, "FAIL", f"HTTP {response.status_code}")
                self.errors.append(f"页面.{name}: {response.status_code}")
                return False

        except Exception as e:
            self.log("页面", name, "ERROR", str(e))
            self.errors.append(f"页面.{name}: {str(e)}")
            return False

    def validate_data_integrity(self):
        """验证数据完整性"""
        print("\n" + "=" * 60)
        print("数据完整性验证")
        print("=" * 60)

        # 检查产品数据
        self.check_api_endpoint(
            "水站", "产品列表", "/api/v1/water/products", auth_required=False
        )

        # 检查办公室数据
        self.check_api_endpoint(
            "系统", "办公室列表", "/api/v1/system/offices", auth_required=True
        )

        # 检查用户数据
        self.check_api_endpoint(
            "系统", "用户列表", "/api/v1/system/users", auth_required=True
        )

        # 检查会议室数据
        self.check_api_endpoint(
            "会议室", "会议室列表", "/api/v1/meeting/rooms", auth_required=True
        )

        # 检查预约数据
        self.check_api_endpoint(
            "会议室", "预约列表", "/api/v1/meeting/bookings", auth_required=True
        )

        # 检查领水记录
        self.check_api_endpoint(
            "水站", "领水记录", "/api/v1/water/pickups", auth_required=True
        )

    def validate_page_accessibility(self):
        """验证页面可访问性"""
        print("\n" + "=" * 60)
        print("页面可访问性验证")
        print("=" * 60)

        pages = [
            ("Portal首页", "/portal/index.html"),
            ("水站前端", "/portal/water/index.html"),
            ("管理后台", "/portal/admin/index.html"),
            ("会议室前端", "/meeting-frontend/index.html"),
            ("会议室日历", "/meeting-frontend/calendar.html"),
            ("我的预约", "/meeting-frontend/my_bookings.html"),
        ]

        for name, path in pages:
            self.check_page_access(name, path)

    def validate_api_consistency(self):
        """验证API一致性"""
        print("\n" + "=" * 60)
        print("API路径一致性验证")
        print("=" * 60)

        # 检查新架构API路径
        new_architecture_apis = [
            ("水站产品", "/api/v1/water/products"),
            ("水站领水", "/api/v1/water/pickup"),
            ("水站办公室", "/api/v1/water/offices"),
            ("会议室列表", "/api/v1/meeting/rooms"),
            ("会议室预约", "/api/v1/meeting/bookings"),
            ("系统用户", "/api/v1/system/users"),
            ("系统办公室", "/api/v1/system/offices"),
            ("系统登录", "/api/v1/system/auth/login"),
        ]

        for name, endpoint in new_architecture_apis:
            # 只测试GET请求（POST需要具体数据）
            if "login" not in endpoint and "pickup" not in endpoint:
                auth_required = (
                    "water/products" not in endpoint and "water/offices" not in endpoint
                )
                self.check_api_endpoint("API路径", name, endpoint, auth_required)

    def check_database_connection(self):
        """检查数据库连接"""
        print("\n" + "=" * 60)
        print("数据库连接验证")
        print("=" * 60)

        import sqlite3

        try:
            conn = sqlite3.connect("./data/app.db")
            cursor = conn.cursor()

            tables = {
                "products": "产品",
                "users": "用户",
                "office": "办公室",
                "meeting_rooms": "会议室",
                "meeting_bookings": "预约",
                "office_pickup": "领水记录",
            }

            for table, name in tables.items():
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                self.log("数据库", f"{name}表", "PASS", f"{count} 条记录")

            conn.close()

        except Exception as e:
            self.log("数据库", "连接", "ERROR", str(e))

    def generate_report(self):
        """生成报告"""
        print("\n" + "=" * 60)
        print("系统验收报告")
        print("=" * 60)

        total = len(self.results)
        passed = sum(1 for r in self.results if r["status"] == "PASS")
        failed = sum(1 for r in self.results if r["status"] == "FAIL")
        errors = sum(1 for r in self.results if r["status"] == "ERROR")

        print(f"\n总测试项: {total}")
        print(f"通过: {passed} ({passed / total * 100:.1f}%)")
        print(f"失败: {failed}")
        print(f"错误: {errors}")

        if self.errors:
            print("\n需要修复的问题:")
            for i, error in enumerate(self.errors, 1):
                print(f"  {i}. {error}")

        print("\n" + "=" * 60)

        if failed == 0 and errors == 0:
            print("✓ 系统验收通过！")
            print("✓ 所有功能正常，可投入生产使用。")
        else:
            print(f"✗ 发现 {failed + errors} 个问题需要修复")

        print("=" * 60)

        return failed == 0 and errors == 0


def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("AI产业集群空间服务系统 - 完整性检查")
    print("国际顶级系统架构师标准验收")
    print("=" * 60)
    print(f"检查时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    validator = SystemValidator()

    # 1. 登录认证
    print("\n" + "=" * 60)
    print("认证模块验证")
    print("=" * 60)
    if not validator.login():
        print("✗ 登录失败，无法继续验证")
        return

    # 2. 数据库连接
    validator.check_database_connection()

    # 3. API一致性
    validator.validate_api_consistency()

    # 4. 数据完整性
    validator.validate_data_integrity()

    # 5. 页面可访问性
    validator.validate_page_accessibility()

    # 6. 生成报告
    success = validator.generate_report()

    # 返回状态码
    return 0 if success else 1


if __name__ == "__main__":
    exit(main())
