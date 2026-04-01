#!/usr/bin/env python3
"""
预约日历视图测试
"""

import os
import sys


class CalendarTestRunner:
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

    def test_calendar_page_exists(self):
        """测试日历页面存在"""
        test_name = "日历页面存在性测试"

        calendar_path = os.path.join(self.frontend_dir, "calendar.html")

        if os.path.exists(calendar_path):
            size = os.path.getsize(calendar_path)
            self.log(test_name, True, f"calendar.html 存在 ({size} bytes)")
        else:
            self.log(test_name, False, "calendar.html 不存在")

    def test_calendar_features(self):
        """测试日历功能完整性"""
        test_name = "日历功能完整性测试"

        calendar_path = os.path.join(self.frontend_dir, "calendar.html")

        try:
            with open(calendar_path, "r", encoding="utf-8") as f:
                content = f.read()

            checks = [
                ("月视图", "viewMode === 'month'"),
                ("周视图", "viewMode === 'week'"),
                ("日历网格", "calendarDays"),
                ("时间格子", "hours"),
                ("预约标记", "getDayBookings"),
                ("新建预约", "showBookingModal"),
                ("预约详情", "showDetailModal"),
                ("月份导航", "previousMonth"),
                ("服务筛选", "filterServiceType"),
                ("点击创建", "selectDate"),
            ]

            found = sum(1 for name, check in checks if check in content)
            total = len(checks)

            if found >= total * 0.8:
                self.log(test_name, True, f"功能完整 ({found}/{total})")
            else:
                self.log(test_name, False, f"功能不完整 ({found}/{total})")
        except Exception as e:
            self.log(test_name, False, f"检查失败: {e}")

    def test_vue_structure(self):
        """测试 Vue 结构"""
        test_name = "Vue 组件结构测试"

        calendar_path = os.path.join(self.frontend_dir, "calendar.html")

        try:
            with open(calendar_path, "r", encoding="utf-8") as f:
                content = f.read()

            checks = [
                "createApp" in content,
                "setup()" in content,
                "return {" in content,
            ]

            if all(checks):
                self.log(test_name, True, "Vue 结构正确")
            else:
                self.log(test_name, False, "Vue 结构问题")
        except Exception as e:
            self.log(test_name, False, f"检查失败: {e}")

    def print_results(self):
        """打印测试结果"""
        print("\n" + "=" * 60)
        print("预约日历视图测试结果")
        print("=" * 60)

        for r in self.results:
            print(r)

        print("\n" + "-" * 60)
        print(f"总计: {self.tests_passed} 通过, {self.tests_failed} 失败")
        print("-" * 60)

        if self.tests_failed == 0:
            print("\n🎉 日历视图测试通过！")
        else:
            print("\n⚠️  日历视图测试存在问题")


def main():
    runner = CalendarTestRunner()

    print("\n📅 预约日历视图测试...")
    runner.test_calendar_page_exists()
    runner.test_calendar_features()
    runner.test_vue_structure()

    runner.print_results()

    sys.exit(0 if runner.tests_failed == 0 else 1)


if __name__ == "__main__":
    main()
