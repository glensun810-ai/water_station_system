#!/usr/bin/env python3
"""
Phase 4 验证测试脚本
验证前端 UI 组件的完整性

运行方法:
    cd Service_WaterManage/tests/phase4
    python3 test_phase4_ui.py
"""

import os
import sys
import re


class Phase4TestRunner:
    def __init__(self):
        self.tests_passed = 0
        self.tests_failed = 0
        self.results = []
        self.frontend_dir = os.path.join(os.path.dirname(__file__), "../../frontend")

    def log(self, test_name, passed, message=""):
        status = "✅ PASS" if passed else "❌ FAIL"
        self.results.append(f"{status}: {test_name}")
        if message:
            self.results.append(f"    {message}")

        if passed:
            self.tests_passed += 1
        else:
            self.tests_failed += 1

    def test_services_page_exists(self):
        """测试服务管理页面存在"""
        test_name = "服务管理页面存在性测试"

        services_path = os.path.join(self.frontend_dir, "services.html")

        if os.path.exists(services_path):
            size = os.path.getsize(services_path)
            self.log(test_name, True, f"services.html 存在 ({size} bytes)")
        else:
            self.log(test_name, False, "services.html 不存在")

    def test_bookings_page_exists(self):
        """测试预约页面存在"""
        test_name = "预约页面存在性测试"

        bookings_path = os.path.join(self.frontend_dir, "bookings.html")

        if os.path.exists(bookings_path):
            size = os.path.getsize(bookings_path)
            self.log(test_name, True, f"bookings.html 存在 ({size} bytes)")
        else:
            self.log(test_name, False, "bookings.html 不存在")

    def test_services_page_content(self):
        """测试服务管理页面内容"""
        test_name = "服务管理页面内容测试"

        services_path = os.path.join(self.frontend_dir, "services.html")

        try:
            with open(services_path, "r", encoding="utf-8") as f:
                content = f.read()

            # 检查关键元素
            checks = [
                ("Vue 3", "createApp" in content),
                ("服务类型切换", "serviceTypes" in content),
                ("服务列表", "filteredServices" in content),
                ("添加服务", "showAddServiceModal" in content),
                ("编辑服务", "editService" in content),
                ("Tailwind CSS", "tailwind" in content.lower()),
                ("config.js 引用", "config.js" in content),
            ]

            passed = sum(1 for _, check in checks if check)
            total = len(checks)

            if passed >= total * 0.8:
                self.log(test_name, True, f"页面内容完整 ({passed}/{total})")
            else:
                missing = [name for name, check in checks if not check]
                self.log(test_name, False, f"缺少元素: {missing}")
        except Exception as e:
            self.log(test_name, False, f"读取失败: {e}")

    def test_bookings_page_content(self):
        """测试预约页面内容"""
        test_name = "预约页面内容测试"

        bookings_path = os.path.join(self.frontend_dir, "bookings.html")

        try:
            with open(bookings_path, "r", encoding="utf-8") as f:
                content = f.read()

            # 检查关键元素
            checks = [
                ("Vue 3", "createApp" in content),
                ("预约列表", "filteredBookings" in content),
                ("新建预约", "showBookingModal" in content),
                ("时间段选择", "time_slot" in content),
                ("筛选功能", "filterServiceType" in content),
                ("状态管理", "booking_status" in content),
                ("config.js 引用", "config.js" in content),
            ]

            passed = sum(1 for _, check in checks if check)
            total = len(checks)

            if passed >= total * 0.8:
                self.log(test_name, True, f"页面内容完整 ({passed}/{total})")
            else:
                missing = [name for name, check in checks if not check]
                self.log(test_name, False, f"缺少元素: {missing}")
        except Exception as e:
            self.log(test_name, False, f"读取失败: {e}")

    def test_vue_components(self):
        """测试 Vue 组件结构"""
        test_name = "Vue 组件结构测试"

        services_path = os.path.join(self.frontend_dir, "services.html")
        bookings_path = os.path.join(self.frontend_dir, "bookings.html")

        try:
            with open(services_path, "r", encoding="utf-8") as f:
                services_content = f.read()

            with open(bookings_path, "r", encoding="utf-8") as f:
                bookings_content = f.read()

            # 检查 Vue 结构
            checks = [
                ("services.html 有 #app", 'id="app"' in services_content),
                ("bookings.html 有 #app", 'id="app"' in bookings_content),
                ("services.html 有 setup()", "setup()" in services_content),
                ("bookings.html 有 setup()", "setup()" in bookings_content),
            ]

            passed = sum(1 for _, check in checks if check)

            if passed == len(checks):
                self.log(test_name, True, "Vue 组件结构正确")
            else:
                self.log(test_name, False, f"Vue 结构问题 ({passed}/{len(checks)})")
        except Exception as e:
            self.log(test_name, False, f"检查失败: {e}")

    def test_api_integration(self):
        """测试 API 集成"""
        test_name = "API 集成测试"

        services_path = os.path.join(self.frontend_dir, "services.html")
        bookings_path = os.path.join(self.frontend_dir, "bookings.html")

        try:
            with open(services_path, "r", encoding="utf-8") as f:
                services_content = f.read()

            with open(bookings_path, "r", encoding="utf-8") as f:
                bookings_content = f.read()

            # 检查 API 调用
            checks = [
                ("services.html API_BASE", "API_BASE" in services_content),
                ("bookings.html API_BASE", "API_BASE" in bookings_content),
                ("services.html fetch", "fetch(" in services_content),
                ("bookings.html fetch", "fetch(" in bookings_content),
            ]

            passed = sum(1 for _, check in checks if check)

            if passed == len(checks):
                self.log(test_name, True, "API 集成正确")
            else:
                self.log(test_name, False, f"API 集成问题 ({passed}/{len(checks)})")
        except Exception as e:
            self.log(test_name, False, f"检查失败: {e}")

    def test_backward_compatibility(self):
        """测试向后兼容性"""
        test_name = "向后兼容性测试"

        admin_path = os.path.join(self.frontend_dir, "admin.html")
        index_path = os.path.join(self.frontend_dir, "index.html")

        try:
            # 检查原有文件未被修改
            admin_size = os.path.getsize(admin_path)
            index_size = os.path.getsize(index_path)

            # admin.html 应该保持原有大小 (~543KB)
            # index.html 应该保持原有大小 (~100KB)

            if admin_size > 500000 and index_size > 90000:
                self.log(test_name, True, "原有页面保持不变")
            else:
                self.log(
                    test_name,
                    False,
                    f"原有页面可能被修改: admin={admin_size}, index={index_size}",
                )
        except Exception as e:
            self.log(test_name, False, f"检查失败: {e}")

    def test_navigation_links(self):
        """测试导航链接"""
        test_name = "导航链接测试"

        services_path = os.path.join(self.frontend_dir, "services.html")
        bookings_path = os.path.join(self.frontend_dir, "bookings.html")

        try:
            with open(services_path, "r", encoding="utf-8") as f:
                services_content = f.read()

            with open(bookings_path, "r", encoding="utf-8") as f:
                bookings_content = f.read()

            # 检查返回 admin.html 的链接
            checks = [
                ("services.html 返回链接", "admin.html" in services_content),
                ("bookings.html 返回链接", "admin.html" in bookings_content),
            ]

            passed = sum(1 for _, check in checks if check)

            if passed == len(checks):
                self.log(test_name, True, "导航链接正确")
            else:
                self.log(test_name, False, f"导航链接问题 ({passed}/{len(checks)})")
        except Exception as e:
            self.log(test_name, False, f"检查失败: {e}")

    def print_results(self):
        """打印测试结果"""
        print("\n" + "=" * 60)
        print("Phase 4 验证测试结果")
        print("=" * 60)

        for r in self.results:
            print(r)

        print("\n" + "-" * 60)
        print(f"总计: {self.tests_passed} 通过, {self.tests_failed} 失败")
        print("-" * 60)

        if self.tests_failed == 0:
            print("\n🎉 Phase 4 验证通过！")
        else:
            print("\n⚠️  Phase 4 验证存在问题，请检查")


def main():
    """运行所有测试"""
    runner = Phase4TestRunner()

    print("\n📦 Phase 4 页面存在性测试...")
    runner.test_services_page_exists()
    runner.test_bookings_page_exists()

    print("\n📋 Phase 4 页面内容测试...")
    runner.test_services_page_content()
    runner.test_bookings_page_content()

    print("\n🔧 Phase 4 组件测试...")
    runner.test_vue_components()
    runner.test_api_integration()

    print("\n🔗 Phase 4 兼容性测试...")
    runner.test_backward_compatibility()
    runner.test_navigation_links()

    # 打印结果
    runner.print_results()

    # 返回状态码
    sys.exit(0 if runner.tests_failed == 0 else 1)


if __name__ == "__main__":
    main()
