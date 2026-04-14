"""
Phase 2验收测试脚本
验证核心API实现和定价引擎功能

测试内容：
1. 定价引擎导入验证
2. 定价引擎功能测试
3. API增强功能验证
4. 服务层模块完整性验证
"""

import sys
import os
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from datetime import datetime, date
import json


class Phase2AcceptanceTest:
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

    def test_pricing_engine_import(self):
        """测试定价引擎导入"""
        print("\n=== 1. 定价引擎模块验证 ===")

        try:
            from services.pricing.engine import PricingEngine

            self.log_result("导入 PricingEngine", "PASS")

            try:
                engine = PricingEngine(None)
                self.log_result("创建 PricingEngine实例", "PASS")

                try:
                    duration = engine._calculate_duration("09:00", "11:00")
                    if duration == 2.0:
                        self.log_result("时长计算功能", "PASS", "2小时")
                    else:
                        self.log_result("时长计算功能", "FAIL", f"计算错误: {duration}")
                except Exception as e:
                    self.log_result("时长计算功能", "FAIL", str(e))

            except Exception as e:
                self.log_result("创建 PricingEngine实例", "FAIL", str(e))

        except Exception as e:
            self.log_result("导入 PricingEngine", "FAIL", str(e))

    def test_service_modules_import(self):
        """测试服务模块导入"""
        print("\n=== 2. 服务层模块验证 ===")

        modules_to_test = [
            ("services.pricing", "定价服务"),
            ("services.booking", "预约服务"),
            ("services.approval", "审批服务"),
            ("services.notification", "通知服务"),
        ]

        for module_path, module_name in modules_to_test:
            try:
                __import__(module_path)
                self.log_result(f"导入 {module_name}模块", "PASS")
            except Exception as e:
                self.log_result(f"导入 {module_name}模块", "FAIL", str(e))

    def test_api_enhancements(self):
        """测试API增强功能"""
        print("\n=== 3. API增强功能验证 ===")

        try:
            from apps.api.v2.space_bookings import router

            routes = [route.path for route in router.routes]

            required_routes = [
                "",
                "/my",
                "/{booking_id}",
                "/{booking_id}/cancel",
                "/calculate-fee",
            ]

            missing_routes = []
            for required in required_routes:
                if not any(required in route for route in routes):
                    missing_routes.append(required)

            if len(missing_routes) == 0:
                self.log_result("预约API路由完整性", "PASS", f"包含{len(routes)}个路由")
            else:
                self.log_result(
                    "预约API路由完整性",
                    "FAIL",
                    f"缺少路由: {', '.join(missing_routes)}",
                )
        except Exception as e:
            self.log_result("预约API路由完整性", "FAIL", str(e))

    def test_approval_reject_api(self):
        """测试审批拒绝API"""
        print("\n=== 4. 审批拒绝功能验证 ===")

        try:
            from apps.api.v2.space_approvals import router, reject_approval

            routes = [route.path for route in router.routes]

            if "/{approval_id}/reject" in routes or any(
                "reject" in route for route in routes
            ):
                self.log_result("审批拒绝API路由", "PASS")
            else:
                self.log_result("审批拒绝API路由", "FAIL", "未找到拒绝路由")

            try:
                from shared.schemas.space.space_approval import SpaceApprovalReject

                schema_fields = [
                    "rejection_reason",
                    "rejection_detail",
                    "suggest_alternatives",
                    "allow_resubmit",
                ]

                missing_fields = []
                for field in schema_fields:
                    if not hasattr(SpaceApprovalReject, field):
                        try:
                            SpaceApprovalReject.__fields__[field]
                        except:
                            missing_fields.append(field)

                if len(missing_fields) == 0:
                    self.log_result("拒绝Schema完整性", "PASS", "包含所有拒绝字段")
                else:
                    self.log_result(
                        "拒绝Schema完整性",
                        "FAIL",
                        f"缺少字段: {', '.join(missing_fields)}",
                    )
            except Exception as e:
                self.log_result("拒绝Schema完整性", "FAIL", str(e))

        except Exception as e:
            self.log_result("审批拒绝功能", "FAIL", str(e))

    def test_fee_calculation_features(self):
        """测试费用计算特性"""
        print("\n=== 5. 费用计算特性验证 ===")

        try:
            from apps.api.v2.space_bookings import calculate_fee

            self.log_result("费用计算API存在", "PASS")

            try:
                from shared.schemas.space.space_booking import (
                    FeeCalculationRequest,
                    FeeCalculationResponse,
                )

                self.log_result("费用计算Schema存在", "PASS")

            except Exception as e:
                self.log_result("费用计算Schema存在", "FAIL", str(e))

        except Exception as e:
            self.log_result("费用计算API存在", "FAIL", str(e))

    def test_pricing_models_import(self):
        """测试定价模型导入"""
        print("\n=== 6. 定价模型验证 ===")

        models_to_test = [
            ("PricingRule", "shared.models.space.pricing.pricing_rule"),
            ("PricingTimeSlot", "shared.models.space.pricing.pricing_time_slot"),
            ("PricingAddon", "shared.models.space.pricing.pricing_addon"),
            ("PricingDiscount", "shared.models.space.pricing.pricing_discount"),
        ]

        for model_name, module_path in models_to_test:
            try:
                module = __import__(module_path, fromlist=[model_name])
                model_class = getattr(module, model_name)
                self.log_result(f"导入 {model_name}", "PASS")
            except Exception as e:
                self.log_result(f"导入 {model_name}", "FAIL", str(e))

    def test_batch_approval_api(self):
        """测试批量审批功能"""
        print("\n=== 7. 批量审批功能验证 ===")

        try:
            from apps.api.v2.space_approvals import router

            routes = [route.path for route in router.routes]

            if "/batch-approve" in routes or any("batch" in route for route in routes):
                self.log_result("批量审批API路由", "PASS")
            else:
                self.log_result("批量审批API路由", "FAIL", "未找到批量审批路由")

        except Exception as e:
            self.log_result("批量审批功能", "FAIL", str(e))

    def generate_report(self):
        """生成验收报告"""
        print("\n" + "=" * 60)
        print("Phase 2验收测试报告")
        print("=" * 60)

        total = self.passed + self.failed
        pass_rate = (self.passed / total * 100) if total > 0 else 0

        print(f"\n测试总数: {total}")
        print(f"通过数量: {self.passed}")
        print(f"失败数量: {self.failed}")
        print(f"通过率: {pass_rate:.1f}%")

        if pass_rate >= 80:
            print("\n✅ Phase 2验收通过")
        elif pass_rate >= 60:
            print("\n⚠️ Phase 2部分通过，需要修复部分问题")
        else:
            print("\n❌ Phase 2验收失败，需要重新实施")

        report_data = {
            "phase": "Phase 2",
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
            / f"phase2_acceptance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
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
    print("开始执行 Phase 2验收测试")
    print("=" * 60)

    tester = Phase2AcceptanceTest()

    tester.test_pricing_engine_import()
    tester.test_service_modules_import()
    tester.test_api_enhancements()
    tester.test_approval_reject_api()
    tester.test_fee_calculation_features()
    tester.test_pricing_models_import()
    tester.test_batch_approval_api()

    passed = tester.generate_report()

    return passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
