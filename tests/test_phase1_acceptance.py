"""
Phase 1验收测试脚本
验证数据层重构和基础API实现的完整性

测试内容：
1. 数据模型导入验证
2. 数据库表创建验证
3. 基础API功能验证
4. Schema定义验证
"""

import sys
import os
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from datetime import datetime
import json


class Phase1AcceptanceTest:
    def __init__(self):
        self.results = []
        self.passed = 0
        self.failed = 0

    def log_result(self, test_name, status, message=""):
        result = {
            "test": test_name,
            "status": status,
            "message": message,
            "timestamp": datetime.now().isoformat(),
        }
        self.results.append(result)
        if status == "PASS":
            self.passed += 1
            print(f"✅ {test_name}: PASS")
        else:
            self.failed += 1
            print(f"❌ {test_name}: FAIL - {message}")

    def test_data_models_import(self):
        """测试数据模型是否能正确导入"""
        print("\n=== 1. 数据模型导入验证 ===")

        models_to_test = [
            ("SpaceType", "shared.models.space.space_type"),
            ("SpaceResource", "shared.models.space.space_resource"),
            ("SpaceBooking", "shared.models.space.space_booking"),
            ("SpaceApproval", "shared.models.space.space_approval"),
            ("SpacePayment", "shared.models.space.space_payment"),
            ("SpaceSettlement", "shared.models.space.space_settlement"),
            ("Notification", "shared.models.space.notification"),
            ("UserSpaceQuota", "shared.models.space.user_space_quota"),
            ("UserMemberInfo", "shared.models.space.user_member_info"),
        ]

        pricing_models = [
            ("PricingRule", "shared.models.space.pricing.pricing_rule"),
            ("PricingTimeSlot", "shared.models.space.pricing.pricing_time_slot"),
            ("PricingAddon", "shared.models.space.pricing.pricing_addon"),
            ("PricingDiscount", "shared.models.space.pricing.pricing_discount"),
        ]

        all_models = models_to_test + pricing_models

        for model_name, module_path in all_models:
            try:
                module = __import__(module_path, fromlist=[model_name])
                model_class = getattr(module, model_name)
                self.log_result(
                    f"导入 {model_name}", "PASS", f"从 {module_path} 成功导入"
                )
            except Exception as e:
                self.log_result(f"导入 {model_name}", "FAIL", str(e))

    def test_schema_import(self):
        """测试Schema定义是否能正确导入"""
        print("\n=== 2. Schema定义验证 ===")

        schemas_to_test = [
            ("SpaceTypeBase", "shared.schemas.space.space_type"),
            ("SpaceResourceBase", "shared.schemas.space.space_resource"),
            ("SpaceBookingBase", "shared.schemas.space.space_booking"),
            ("SpaceApprovalBase", "shared.schemas.space.space_approval"),
            ("SpacePaymentBase", "shared.schemas.space.space_payment"),
        ]

        for schema_name, module_path in schemas_to_test:
            try:
                module = __import__(module_path, fromlist=[schema_name])
                schema_class = getattr(module, schema_name)
                self.log_result(f"导入 {schema_name}", "PASS")
            except Exception as e:
                self.log_result(f"导入 {schema_name}", "FAIL", str(e))

    def test_api_modules_import(self):
        """测试API模块是否能正确导入"""
        print("\n=== 3. API模块验证 ===")

        apis_to_test = [
            ("space_types", "apps.api.v2.space_types"),
            ("space_resources", "apps.api.v2.space_resources"),
            ("space_bookings", "apps.api.v2.space_bookings"),
            ("space_approvals", "apps.api.v2.space_approvals"),
            ("space_payments", "apps.api.v2.space_payments"),
            ("space_statistics", "apps.api.v2.space_statistics"),
        ]

        for api_name, module_path in apis_to_test:
            try:
                module = __import__(module_path, fromlist=[api_name])
                self.log_result(f"导入 {api_name} API", "PASS")
            except Exception as e:
                self.log_result(f"导入 {api_name} API", "FAIL", str(e))

    def test_booking_status_enum(self):
        """测试预约状态枚举完整性"""
        print("\n=== 4. 预约状态机验证 ===")

        try:
            from shared.models.space.space_booking import BookingStatus

            expected_statuses = [
                "pending_approval",
                "approved",
                "rejected",
                "deposit_paid",
                "confirmed",
                "cancelled",
                "in_use",
                "completed",
                "settled",
            ]

            actual_statuses = [s.value for s in BookingStatus]

            missing = [s for s in expected_statuses if s not in actual_statuses]

            if len(missing) == 0:
                self.log_result(
                    "预约状态枚举完整性",
                    "PASS",
                    f"包含所有9个状态: {', '.join(actual_statuses)}",
                )
            else:
                self.log_result(
                    "预约状态枚举完整性", "FAIL", f"缺少状态: {', '.join(missing)}"
                )
        except Exception as e:
            self.log_result("预约状态枚举完整性", "FAIL", str(e))

    def test_data_model_fields(self):
        """测试关键数据模型字段完整性"""
        print("\n=== 5. 数据模型字段验证 ===")

        try:
            from shared.models.space.space_booking import SpaceBooking

            booking = SpaceBooking()

            critical_fields = [
                "booking_no",
                "resource_id",
                "user_id",
                "booking_date",
                "start_time",
                "end_time",
                "status",
                "payment_status",
                "total_fee",
                "requires_deposit",
                "deposit_amount",
            ]

            missing_fields = []
            for field in critical_fields:
                if not hasattr(booking, field):
                    missing_fields.append(field)

            if len(missing_fields) == 0:
                self.log_result(
                    "SpaceBooking关键字段",
                    "PASS",
                    f"包含所有{len(critical_fields)}个关键字段",
                )
            else:
                self.log_result(
                    "SpaceBooking关键字段",
                    "FAIL",
                    f"缺少字段: {', '.join(missing_fields)}",
                )
        except Exception as e:
            self.log_result("SpaceBooking关键字段", "FAIL", str(e))

    def test_migration_script(self):
        """测试数据迁移脚本是否存在"""
        print("\n=== 6. 数据迁移脚本验证 ===")

        migration_file = project_root / "infra" / "database" / "migrate_to_space.py"

        if migration_file.exists():
            self.log_result("数据迁移脚本存在", "PASS", f"路径: {migration_file}")

            try:
                module = __import__(
                    "infra.database.migrate_to_space",
                    fromlist=["migrate_meeting_rooms"],
                )
                self.log_result("数据迁移脚本导入", "PASS")
            except Exception as e:
                self.log_result("数据迁移脚本导入", "FAIL", str(e))
        else:
            self.log_result("数据迁移脚本存在", "FAIL", f"文件不存在: {migration_file}")

    def test_frontend_login_page(self):
        """测试前端登录页面是否存在"""
        print("\n=== 7. 前端登录页面验证 ===")

        login_file = project_root / "space-frontend" / "login.html"

        if login_file.exists():
            self.log_result("前端登录页面存在", "PASS")

            try:
                with open(login_file, "r", encoding="utf-8") as f:
                    content = f.read()

                if "JWT" in content or "token" in content:
                    self.log_result("登录页面包含JWT认证", "PASS")
                else:
                    self.log_result(
                        "登录页面包含JWT认证", "FAIL", "未找到JWT认证相关代码"
                    )

                if "login" in content.lower():
                    self.log_result("登录页面包含登录表单", "PASS")
                else:
                    self.log_result("登录页面包含登录表单", "FAIL", "未找到登录表单")
            except Exception as e:
                self.log_result("登录页面内容检查", "FAIL", str(e))
        else:
            self.log_result("前端登录页面存在", "FAIL", f"文件不存在: {login_file}")

    def generate_report(self):
        """生成验收报告"""
        print("\n" + "=" * 60)
        print("Phase 1验收测试报告")
        print("=" * 60)

        total = self.passed + self.failed
        pass_rate = (self.passed / total * 100) if total > 0 else 0

        print(f"\n测试总数: {total}")
        print(f"通过数量: {self.passed}")
        print(f"失败数量: {self.failed}")
        print(f"通过率: {pass_rate:.1f}%")

        if pass_rate >= 80:
            print("\n✅ Phase 1验收通过")
        elif pass_rate >= 60:
            print("\n⚠️ Phase 1部分通过，需要修复部分问题")
        else:
            print("\n❌ Phase 1验收失败，需要重新实施")

        report_data = {
            "phase": "Phase 1",
            "test_date": datetime.now().isoformat(),
            "summary": {
                "total_tests": total,
                "passed": self.passed,
                "failed": self.failed,
                "pass_rate": pass_rate,
            },
            "results": self.results,
        }

        report_file = (
            project_root
            / "docs"
            / "space-service-refactor"
            / f"phase1_acceptance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )

        try:
            with open(report_file, "w", encoding="utf-8") as f:
                json.dump(report_data, f, ensure_ascii=False, indent=2)
            print(f"\n详细报告已保存: {report_file}")
        except Exception as e:
            print(f"\n报告保存失败: {e}")

        return pass_rate >= 80


def main():
    print("=" * 60)
    print("开始执行 Phase 1验收测试")
    print("=" * 60)

    tester = Phase1AcceptanceTest()

    tester.test_data_models_import()
    tester.test_schema_import()
    tester.test_api_modules_import()
    tester.test_booking_status_enum()
    tester.test_data_model_fields()
    tester.test_migration_script()
    tester.test_frontend_login_page()

    passed = tester.generate_report()

    return passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
