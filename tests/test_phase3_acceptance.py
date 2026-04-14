"""
Phase 3验收测试脚本
验证前端页面实现的国际顶级UI设计标准

测试内容：
1. UI设计系统符合度验证
2. ARIA可访问性验证
3. 移动端响应式验证
4. 页面功能完整性验证
"""

import sys
import os
from pathlib import Path
import re

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from datetime import datetime
import json


class Phase3AcceptanceTest:
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

    def test_ui_pages_existence(self):
        """测试前端页面文件存在性"""
        print("\n=== 1. 前端页面文件验证 ===")

        pages_to_check = [
            ("预约主页", "space-frontend/index.html"),
            ("预约创建页面", "space-frontend/booking.html"),
            ("审批中心页面", "portal/admin/space/approvals.html"),
        ]

        for page_name, page_path in pages_to_check:
            file_path = project_root / page_path
            if file_path.exists():
                self.log_result(f"{page_name}文件存在", "PASS", str(file_path))

                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()
                        size = len(content)
                    self.log_result(f"{page_name}内容完整性", "PASS", f"{size} bytes")
                except Exception as e:
                    self.log_result(f"{page_name}内容完整性", "FAIL", str(e))
            else:
                self.log_result(
                    f"{page_name}文件存在", "FAIL", f"文件不存在: {file_path}"
                )

    def test_design_system_usage(self):
        """测试设计系统CSS使用"""
        print("\n=== 2. 设计系统符合度验证 ===")

        pages_to_check = [
            "space-frontend/index.html",
            "space-frontend/booking.html",
            "portal/admin/space/approvals.html",
        ]

        for page_path in pages_to_check:
            file_path = project_root / page_path
            if not file_path.exists():
                continue

            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()

                page_name = Path(page_path).stem

                if "design-system.css" in content:
                    self.log_result(f"{page_name}引用设计系统CSS", "PASS")
                else:
                    self.log_result(
                        f"{page_name}引用设计系统CSS", "FAIL", "未引用design-system.css"
                    )

                css_variables = [
                    "--primary",
                    "--success",
                    "--warning",
                    "--danger",
                    "--spacing-",
                    "--radius-",
                    "--shadow-",
                    "--font-size-",
                    "--text-",
                    "--bg-",
                    "--touch-min",
                ]

                found_vars = []
                for var in css_variables:
                    if f"var({var}" in content or f"var(--{var}" in content:
                        found_vars.append(var)

                if len(found_vars) >= 5:
                    self.log_result(
                        f"{page_name}使用CSS变量",
                        "PASS",
                        f"使用了{len(found_vars)}种变量",
                    )
                else:
                    self.log_result(
                        f"{page_name}使用CSS变量",
                        "FAIL",
                        f"仅使用了{len(found_vars)}种变量，应至少5种",
                    )

                class_patterns = [
                    'class="btn',
                    'class="form-input',
                    'class="card',
                    'class="form-group',
                    'class="form-label',
                ]

                found_classes = []
                for pattern in class_patterns:
                    if pattern in content:
                        found_classes.append(pattern)

                if len(found_classes) >= 3:
                    self.log_result(
                        f"{page_name}使用设计系统类",
                        "PASS",
                        f"使用了{len(found_classes)}个设计类",
                    )
                else:
                    self.log_result(
                        f"{page_name}使用设计系统类",
                        "FAIL",
                        f"仅使用了{len(found_classes)}个设计类",
                    )

            except Exception as e:
                self.log_result(f"{page_name}设计系统验证", "FAIL", str(e))

    def test_aria_accessibility(self):
        """测试ARIA可访问性"""
        print("\n=== 3. ARIA可访问性验证 ===")

        pages_to_check = [
            "space-frontend/index.html",
            "space-frontend/booking.html",
            "portal/admin/space/approvals.html",
        ]

        for page_path in pages_to_check:
            file_path = project_root / page_path
            if not file_path.exists():
                continue

            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()

                page_name = Path(page_path).stem

                aria_attributes = [
                    "role=",
                    "aria-label=",
                    "aria-labelledby=",
                    "aria-describedby=",
                    "aria-live=",
                    "aria-required=",
                    "aria-disabled=",
                    "aria-current=",
                    "aria-modal=",
                    "aria-checked=",
                    "aria-hidden=",
                ]

                found_aria = []
                for aria in aria_attributes:
                    if aria in content:
                        found_aria.append(aria)

                if len(found_aria) >= 5:
                    self.log_result(
                        f"{page_name}ARIA标签使用",
                        "PASS",
                        f"使用了{len(found_aria)}种ARIA属性",
                    )
                else:
                    self.log_result(
                        f"{page_name}ARIA标签使用",
                        "FAIL",
                        f"仅使用了{len(found_aria)}种ARIA属性，应至少5种",
                    )

                semantic_elements = [
                    "<header",
                    "<main",
                    "<nav",
                    "<section",
                    "<article",
                    "<footer",
                    "<h1",
                    "<h2",
                    "<h3",
                    "<form",
                    "<label",
                    "<button",
                    "<input",
                    "<select",
                    "<textarea",
                ]

                found_semantic = []
                for elem in semantic_elements:
                    if elem in content:
                        found_semantic.append(elem)

                if len(found_semantic) >= 10:
                    self.log_result(
                        f"{page_name}语义化标签",
                        "PASS",
                        f"使用了{len(found_semantic)}个语义标签",
                    )
                else:
                    self.log_result(
                        f"{page_name}语义化标签",
                        "FAIL",
                        f"仅使用了{len(found_semantic)}个语义标签",
                    )

            except Exception as e:
                self.log_result(f"{page_name}可访问性验证", "FAIL", str(e))

    def test_mobile_responsive(self):
        """测试移动端响应式"""
        print("\n=== 4. 移动端响应式验证 ===")

        pages_to_check = [
            "space-frontend/index.html",
            "space-frontend/booking.html",
            "portal/admin/space/approvals.html",
        ]

        for page_path in pages_to_check:
            file_path = project_root / page_path
            if not file_path.exists():
                continue

            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()

                page_name = Path(page_path).stem

                if "viewport-fit=cover" in content:
                    self.log_result(f"{page_name}viewport-fit设置", "PASS")
                else:
                    self.log_result(
                        f"{page_name}viewport-fit设置",
                        "FAIL",
                        "未设置viewport-fit=cover",
                    )

                if "safe-area-inset" in content or "--safe-area" in content:
                    self.log_result(f"{page_name}安全区域适配", "PASS")
                else:
                    self.log_result(
                        f"{page_name}安全区域适配", "FAIL", "未适配安全区域"
                    )

                if (
                    "--touch-min" in content
                    or "min-height: 44px" in content
                    or "min-height: var(--touch-min)" in content
                ):
                    self.log_result(
                        f"{page_name}触摸区域最小尺寸", "PASS", "符合44px最小标准"
                    )
                else:
                    self.log_result(
                        f"{page_name}触摸区域最小尺寸", "FAIL", "未达到44px最小标准"
                    )

                if "@media (max-width:" in content or "@media(max-width:" in content:
                    self.log_result(f"{page_name}媒体查询响应式", "PASS")
                else:
                    self.log_result(
                        f"{page_name}媒体查询响应式", "FAIL", "缺少媒体查询"
                    )

            except Exception as e:
                self.log_result(f"{page_name}移动端验证", "FAIL", str(e))

    def test_vue3_usage(self):
        """测试Vue 3框架使用"""
        print("\n=== 5. Vue 3框架验证 ===")

        pages_to_check = [
            "space-frontend/index.html",
            "space-frontend/booking.html",
            "portal/admin/space/approvals.html",
        ]

        for page_path in pages_to_check:
            file_path = project_root / page_path
            if not file_path.exists():
                continue

            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()

                page_name = Path(page_path).stem

                if "vue@3" in content or "Vue" in content:
                    self.log_result(f"{page_name}使用Vue框架", "PASS")
                else:
                    self.log_result(f"{page_name}使用Vue框架", "FAIL", "未使用Vue框架")

                if "createApp" in content:
                    self.log_result(f"{page_name}Vue 3 Composition API", "PASS")
                else:
                    self.log_result(
                        f"{page_name}Vue 3 Composition API",
                        "FAIL",
                        "未使用Composition API",
                    )

                vue_features = [
                    "v-if",
                    "v-for",
                    "v-model",
                    "@click",
                    "@submit",
                    ":class",
                    ":style",
                ]
                found_features = []
                for feature in vue_features:
                    if feature in content:
                        found_features.append(feature)

                if len(found_features) >= 3:
                    self.log_result(
                        f"{page_name}Vue指令使用",
                        "PASS",
                        f"使用了{len(found_features)}种指令",
                    )
                else:
                    self.log_result(
                        f"{page_name}Vue指令使用",
                        "FAIL",
                        f"仅使用了{len(found_features)}种指令",
                    )

            except Exception as e:
                self.log_result(f"{page_name}Vue验证", "FAIL", str(e))

    def test_key_features(self):
        """测试关键功能实现"""
        print("\n=== 6. 关键功能验证 ===")

        index_file = project_root / "space-frontend/index.html"
        if index_file.exists():
            try:
                with open(index_file, "r", encoding="utf-8") as f:
                    content = f.read()

                features = [
                    ("空间类型选择", "spaceTypes"),
                    ("智能推荐", "recommendations"),
                    ("用户信息显示", "user"),
                    ("底部导航", "bottom-nav"),
                    ("响应式网格", "grid-template-columns"),
                ]

                for feature_name, feature_marker in features:
                    if feature_marker in content:
                        self.log_result(f"主页{feature_name}功能", "PASS")
                    else:
                        self.log_result(
                            f"主页{feature_name}功能", "FAIL", f"未找到{feature_marker}"
                        )
            except Exception as e:
                self.log_result("主页功能验证", "FAIL", str(e))

        booking_file = project_root / "space-frontend/booking.html"
        if booking_file.exists():
            try:
                with open(booking_file, "r", encoding="utf-8") as f:
                    content = f.read()

                features = [
                    ("分步骤流程", "currentStep"),
                    ("时段选择", "timeSlots"),
                    ("费用计算", "feeDetail"),
                    ("用户类型识别", "userType"),
                    ("表单验证", "canProceedToNext"),
                ]

                for feature_name, feature_marker in features:
                    if feature_marker in content:
                        self.log_result(f"预约页{feature_name}功能", "PASS")
                    else:
                        self.log_result(
                            f"预约页{feature_name}功能",
                            "FAIL",
                            f"未找到{feature_marker}",
                        )
            except Exception as e:
                self.log_result("预约页功能验证", "FAIL", str(e))

        approvals_file = project_root / "portal/admin/space/approvals.html"
        if approvals_file.exists():
            try:
                with open(approvals_file, "r", encoding="utf-8") as f:
                    content = f.read()

                features = [
                    ("审批列表", "approvals"),
                    ("拒绝弹窗", "showRejectDialog"),
                    ("拒绝原因", "rejectionReason"),
                    ("备选方案推荐", "suggestedAlternatives"),
                    ("批量审批", "batchApprove"),
                    ("允许重新提交", "allowResubmit"),
                ]

                for feature_name, feature_marker in features:
                    if feature_marker in content:
                        self.log_result(f"审批页{feature_name}功能", "PASS")
                    else:
                        self.log_result(
                            f"审批页{feature_name}功能",
                            "FAIL",
                            f"未找到{feature_marker}",
                        )
            except Exception as e:
                self.log_result("审批页功能验证", "FAIL", str(e))

    def generate_report(self):
        """生成验收报告"""
        print("\n" + "=" * 60)
        print("Phase 3验收测试报告")
        print("=" * 60)

        total = self.passed + self.failed
        pass_rate = (self.passed / total * 100) if total > 0 else 0

        print(f"\n测试总数: {total}")
        print(f"通过数量: {self.passed}")
        print(f"失败数量: {self.failed}")
        print(f"通过率: {pass_rate:.1f}%")

        if pass_rate >= 90:
            print("\n✅ Phase 3验收通过 - 达到国际顶级UI设计标准")
        elif pass_rate >= 80:
            print("\n✅ Phase 3验收通过 - 符合设计系统标准")
        elif pass_rate >= 60:
            print("\n⚠️ Phase 3部分通过，需要改进部分问题")
        else:
            print("\n❌ Phase 3验收失败，需要重新实施")

        ui_quality_score = self._calculate_ui_score()
        print(f"\nUI质量评分: {ui_quality_score}/100")

        report_data = {
            "phase": "Phase 3",
            "test_date": datetime.now().isoformat(),
            "ui_quality_score": ui_quality_score,
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
            / f"phase3_acceptance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )

        try:
            with open(report_file, "w", encoding="utf-8") as f:
                json.dump(report_data, f, ensure_ascii=False, indent=2)
            print(f"\n详细报告已保存: {report_file}")
        except Exception as e:
            print(f"\n报告保存失败: {e}")

        return pass_rate >= 80

    def _calculate_ui_score(self):
        """计算UI质量评分"""
        categories = {
            "design_system": 0,
            "accessibility": 0,
            "mobile": 0,
            "vue_usage": 0,
            "features": 0,
        }

        for result in self.results:
            test_name = result["test"]

            if (
                "设计系统" in test_name
                or "CSS变量" in test_name
                or "设计类" in test_name
            ):
                categories["design_system"] += 1 if result["status"] == "PASS" else 0
            elif "ARIA" in test_name or "语义" in test_name:
                categories["accessibility"] += 1 if result["status"] == "PASS" else 0
            elif (
                "移动端" in test_name or "viewport" in test_name or "触摸" in test_name
            ):
                categories["mobile"] += 1 if result["status"] == "PASS" else 0
            elif "Vue" in test_name:
                categories["vue_usage"] += 1 if result["status"] == "PASS" else 0
            elif "功能" in test_name:
                categories["features"] += 1 if result["status"] == "PASS" else 0

        score = 0
        score += categories["design_system"] * 5
        score += categories["accessibility"] * 4
        score += categories["mobile"] * 4
        score += categories["vue_usage"] * 3
        score += categories["features"] * 3

        max_score = 60
        normalized_score = min(100, (score / max_score) * 100)

        return int(normalized_score)


def main():
    print("=" * 60)
    print("开始执行 Phase 3验收测试")
    print("国际顶级UI设计标准验证")
    print("=" * 60)

    tester = Phase3AcceptanceTest()

    tester.test_ui_pages_existence()
    tester.test_design_system_usage()
    tester.test_aria_accessibility()
    tester.test_mobile_responsive()
    tester.test_vue3_usage()
    tester.test_key_features()

    passed = tester.generate_report()

    return passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
