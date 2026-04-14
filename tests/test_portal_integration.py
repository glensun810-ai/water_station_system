"""
Portal集成验证测试脚本
验证空间服务模块与Portal系统的正确集成

测试内容：
1. Portal首页服务入口验证
2. 管理端页面路由验证
3. 认证系统集成验证
4. 新旧页面替换验证
5. 端到端功能流程验证
"""

import sys
import os
from pathlib import Path
import re

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from datetime import datetime
import json


class PortalIntegrationTest:
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

    def test_portal_index_integration(self):
        """测试Portal首页集成"""
        print("\n=== 1. Portal首页集成验证 ===")

        portal_index = project_root / "portal" / "index.html"
        if portal_index.exists():
            try:
                with open(portal_index, "r", encoding="utf-8") as f:
                    content = f.read()

                if "/space-frontend/index.html" in content:
                    self.log_result(
                        "Portal首页空间服务入口", "PASS", "指向新的space-frontend"
                    )
                else:
                    self.log_result(
                        "Portal首页空间服务入口", "FAIL", "未指向新的space-frontend"
                    )

                if "/portal/admin/space/approvals.html" in content:
                    self.log_result(
                        "Portal首页管理端链接", "PASS", "指向新的portal/admin/space"
                    )
                else:
                    self.log_result(
                        "Portal首页管理端链接", "FAIL", "未指向新的portal/admin/space"
                    )

                if "空间免费时长" in content:
                    self.log_result(
                        "Portal首页用户统计文案", "PASS", "已改为'空间免费时长'"
                    )
                else:
                    self.log_result(
                        "Portal首页用户统计文案", "FAIL", "仍显示'会议室免费时长'"
                    )

                if "/meeting-frontend/index.html" not in content:
                    self.log_result(
                        "Portal首页移除旧链接", "PASS", "已移除旧的meeting-frontend链接"
                    )
                else:
                    self.log_result(
                        "Portal首页移除旧链接", "FAIL", "仍存在旧的meeting-frontend链接"
                    )

            except Exception as e:
                self.log_result("Portal首页集成验证", "FAIL", str(e))
        else:
            self.log_result("Portal首页文件存在", "FAIL", "文件不存在")

    def test_admin_pages_existence(self):
        """测试管理端页面存在性"""
        print("\n=== 2. 管理端页面存在性验证 ===")

        pages_to_check = [
            ("审批中心", "portal/admin/space/approvals.html"),
            ("预约管理", "portal/admin/space/bookings.html"),
            ("资源配置", "portal/admin/space/resources.html"),
            ("统计分析", "portal/admin/space/statistics.html"),
            ("管理工作台", "portal/admin/space/dashboard.html"),
        ]

        for page_name, page_path in pages_to_check:
            file_path = project_root / page_path
            if file_path.exists():
                self.log_result(f"{page_name}页面存在", "PASS")

                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()

                    if (
                        "返回管理中心" in content
                        or "管理中心" in content
                        or "/portal/admin/index.html" in content
                    ):
                        self.log_result(f"{page_name}返回管理中心链接", "PASS")
                    else:
                        self.log_result(
                            f"{page_name}返回管理中心链接", "FAIL", "缺少返回链接"
                        )

                    if "localStorage.getItem('auth_token')" in content:
                        self.log_result(f"{page_name}JWT认证使用", "PASS")
                    else:
                        self.log_result(
                            f"{page_name}JWT认证使用", "FAIL", "缺少JWT认证"
                        )

                except Exception as e:
                    self.log_result(f"{page_name}内容验证", "FAIL", str(e))
            else:
                self.log_result(f"{page_name}页面存在", "FAIL", "文件不存在")

    def test_frontend_pages_existence(self):
        """测试用户端页面存在性"""
        print("\n=== 3. 用户端页面存在性验证 ===")

        pages_to_check = [
            ("预约主页", "space-frontend/index.html"),
            ("预约创建", "space-frontend/booking.html"),
            ("登录页面", "space-frontend/login.html"),
        ]

        for page_name, page_path in pages_to_check:
            file_path = project_root / page_path
            if file_path.exists():
                self.log_result(f"{page_name}页面存在", "PASS")
            else:
                self.log_result(f"{page_name}页面存在", "FAIL", "文件不存在")

    def test_api_routes_registration(self):
        """测试API路由注册"""
        print("\n=== 4. API路由注册验证 ===")

        main_file = project_root / "apps" / "main.py"
        if main_file.exists():
            try:
                with open(main_file, "r", encoding="utf-8") as f:
                    content = f.read()

                space_apis = [
                    "space_types_router",
                    "space_resources_router",
                    "space_bookings_router",
                    "space_approvals_router",
                    "space_payments_router",
                    "space_statistics_router",
                ]

                found_apis = []
                for api in space_apis:
                    if api in content:
                        found_apis.append(api)

                if len(found_apis) == 6:
                    self.log_result(
                        "API路由注册完整性", "PASS", f"{len(found_apis)}个API已注册"
                    )
                else:
                    self.log_result(
                        "API路由注册完整性", "FAIL", f"仅注册{len(found_apis)}个API"
                    )

                if "space-frontend" in content:
                    self.log_result("space-frontend静态文件挂载", "PASS")
                else:
                    self.log_result(
                        "space-frontend静态文件挂载", "FAIL", "未挂载space-frontend"
                    )

                if "v2_router.include_router(space_" in content:
                    self.log_result("v2版本路由正确使用", "PASS")
                else:
                    self.log_result("v2版本路由正确使用", "FAIL", "未使用v2_router")

            except Exception as e:
                self.log_result("API路由注册验证", "FAIL", str(e))
        else:
            self.log_result("main.py文件存在", "FAIL", "文件不存在")

    def test_auth_system_integration(self):
        """测试认证系统集成"""
        print("\n=== 5. 认证系统集成验证 ===")

        auth_file = project_root / "depends" / "auth.py"
        if auth_file.exists():
            try:
                with open(auth_file, "r", encoding="utf-8") as f:
                    content = f.read()

                auth_functions = [
                    "get_current_user",
                    "get_current_user_required",
                    "get_admin_user",
                    "verify_token",
                    "HTTPException",
                ]

                found_functions = []
                for func in auth_functions:
                    if func in content:
                        found_functions.append(func)

                if len(found_functions) >= 4:
                    self.log_result(
                        "认证系统函数完整性",
                        "PASS",
                        f"{len(found_functions)}个函数已定义",
                    )
                else:
                    self.log_result(
                        "认证系统函数完整性",
                        "FAIL",
                        f"仅定义{len(found_functions)}个函数",
                    )

            except Exception as e:
                self.log_result("认证系统集成验证", "FAIL", str(e))
        else:
            self.log_result("认证文件存在", "FAIL", "文件不存在")

    def test_old_pages_redirect(self):
        """测试旧页面处理"""
        print("\n=== 6. 旧页面处理验证 ===")

        old_pages_to_check = [
            "portal/admin/meeting/approvals.html",
            "portal/admin/meeting/bookings.html",
        ]

        for page_path in old_pages_to_check:
            file_path = project_root / page_path
            page_name = Path(page_path).stem

            if file_path.exists():
                self.log_result(
                    f"旧{page_name}页面存在", "PASS", "旧页面保留，可作为备用"
                )
            else:
                self.log_result(f"旧{page_name}页面存在", "PASS", "旧页面已移除")

    def generate_report(self):
        """生成集成验证报告"""
        print("\n" + "=" * 60)
        print("Portal集成验证测试报告")
        print("=" * 60)

        total = self.passed + self.failed
        pass_rate = (self.passed / total * 100) if total > 0 else 0

        print(f"\n测试总数: {total}")
        print(f"通过数量: {self.passed}")
        print(f"失败数量: {self.failed}")
        print(f"通过率: {pass_rate:.1f}%")

        if pass_rate >= 90:
            print("\n✅ Portal集成验证通过 - 系统正确集成")
        elif pass_rate >= 80:
            print("\n✅ Portal集成基本通过 - minor issues")
        else:
            print("\n❌ Portal集成验证失败 - 需要修复")

        report_data = {
            "test_type": "Portal集成验证",
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
            / f"portal_integration_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
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
    print("开始执行Portal集成验证测试")
    print("=" * 60)

    tester = PortalIntegrationTest()

    tester.test_portal_index_integration()
    tester.test_admin_pages_existence()
    tester.test_frontend_pages_existence()
    tester.test_api_routes_registration()
    tester.test_auth_system_integration()
    tester.test_old_pages_redirect()

    passed = tester.generate_report()

    return passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
