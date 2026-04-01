#!/usr/bin/env python3
"""
Phase 5 集成测试脚本
端到端测试 - 验证整个系统的完整性

运行方法:
    cd Service_WaterManage/tests/integration
    python3 test_e2e.py
"""

import os
import sys
import sqlite3
import subprocess
import time
import json
from datetime import datetime

# 添加 backend 到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../backend"))


class E2ETestRunner:
    def __init__(self):
        self.tests_passed = 0
        self.tests_failed = 0
        self.results = []
        self.project_root = os.path.join(os.path.dirname(__file__), "../..")

    def log(self, test_name, passed, message=""):
        """记录测试结果"""
        status = "✅ PASS" if passed else "❌ FAIL"
        self.results.append(f"{status}: {test_name}")
        if message:
            self.results.append(f"    {message}")

        if passed:
            self.tests_passed += 1
        else:
            self.tests_failed += 1

    def test_database_schema(self):
        """测试数据库架构"""
        test_name = "数据库架构测试"

        db_path = os.path.join(self.project_root, "waterms.db")

        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # 检查 products 表结构
            cursor.execute("PRAGMA table_info(products)")
            products_columns = {row[1] for row in cursor.fetchall()}

            required_products_fields = {
                "service_type",
                "resource_config",
                "booking_required",
                "advance_booking_days",
                "category",
                "icon",
                "color",
                "max_capacity",
                "facilities",
            }

            missing = required_products_fields - products_columns

            if missing:
                self.log(test_name, False, f"products 表缺少字段: {missing}")
            else:
                # 检查 office_pickup 表结构
                cursor.execute("PRAGMA table_info(office_pickup)")
                pickup_columns = {row[1] for row in cursor.fetchall()}

                required_pickup_fields = {
                    "service_type",
                    "time_slot",
                    "actual_usage",
                    "booking_status",
                    "service_name",
                    "participants_count",
                    "purpose",
                    "contact_phone",
                }

                missing_pickup = required_pickup_fields - pickup_columns

                if missing_pickup:
                    self.log(
                        test_name, False, f"office_pickup 表缺少字段: {missing_pickup}"
                    )
                else:
                    self.log(test_name, True, "数据库架构完整")

            conn.close()
        except Exception as e:
            self.log(test_name, False, f"数据库检查失败: {e}")

    def test_backend_models(self):
        """测试后端模型定义"""
        test_name = "后端模型定义测试"

        try:
            from main import Product, OfficePickup

            # 检查 Product 模型属性
            product_attrs = [attr for attr in dir(Product) if not attr.startswith("_")]
            required_attrs = ["service_type", "booking_required", "category"]

            found = [attr for attr in required_attrs if attr in product_attrs]

            if len(found) == len(required_attrs):
                self.log(test_name, True, f"Product 模型包含扩展字段: {found}")
            else:
                self.log(
                    test_name,
                    False,
                    f"Product 模型缺少字段: {set(required_attrs) - set(found)}",
                )
        except Exception as e:
            self.log(test_name, False, f"模型检查失败: {e}")

    def test_api_services_module(self):
        """测试 API 服务模块"""
        test_name = "API 服务模块测试"

        try:
            from api_services import router, SERVICE_CONFIGS

            # 检查服务配置
            required_services = [
                "water",
                "meeting_room",
                "dining",
                "cleaning",
                "tea_break",
            ]
            found_services = [s for s in required_services if s in SERVICE_CONFIGS]

            if len(found_services) >= 5:
                # 检查路由前缀
                if router.prefix == "/api/services":
                    self.log(
                        test_name,
                        True,
                        f"API 服务模块正常，包含 {len(found_services)} 种服务类型",
                    )
                else:
                    self.log(test_name, False, f"路由前缀错误: {router.prefix}")
            else:
                self.log(test_name, False, f"服务类型不足: {found_services}")
        except Exception as e:
            self.log(test_name, False, f"API 模块检查失败: {e}")

    def test_config_files(self):
        """测试配置文件完整性"""
        test_name = "配置文件完整性测试"

        config_path = os.path.join(self.project_root, "frontend/config.js")
        loader_path = os.path.join(self.project_root, "frontend/config-loader.js")

        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config_content = f.read()

            with open(loader_path, "r", encoding="utf-8") as f:
                loader_content = f.read()

            checks = [
                ("config.js 有 serviceTypes", "serviceTypes" in config_content),
                ("config.js 有 10 种服务", config_content.count("value:") >= 10),
                ("config-loader.js 有 getConfig", "getConfig" in loader_content),
                (
                    "config-loader.js 有 API 支持",
                    "API_BASE" in loader_content or "loadFromApi" in loader_content,
                ),
            ]

            passed = sum(1 for _, check in checks if check)

            if passed == len(checks):
                self.log(test_name, True, "配置文件完整")
            else:
                failed = [name for name, check in checks if not check]
                self.log(test_name, False, f"配置问题: {failed}")
        except Exception as e:
            self.log(test_name, False, f"配置检查失败: {e}")

    def test_frontend_pages(self):
        """测试前端页面"""
        test_name = "前端页面测试"

        pages = [("services.html", "服务管理"), ("bookings.html", "服务预约")]

        try:
            for page_file, page_name in pages:
                page_path = os.path.join(self.project_root, "frontend", page_file)

                if not os.path.exists(page_path):
                    self.log(test_name, False, f"{page_name} 页面不存在")
                    return

                with open(page_path, "r", encoding="utf-8") as f:
                    content = f.read()

                # 检查关键元素
                if "createApp" not in content:
                    self.log(test_name, False, f"{page_name} 页面缺少 Vue")
                    return

            self.log(test_name, True, "前端页面完整")
        except Exception as e:
            self.log(test_name, False, f"页面检查失败: {e}")

    def test_rollback_scripts(self):
        """测试回滚脚本"""
        test_name = "回滚脚本测试"

        scripts = ["scripts/rollback_phase_1.sh", "scripts/rollback_phase_2.sh"]

        try:
            for script in scripts:
                script_path = os.path.join(self.project_root, script)

                if not os.path.exists(script_path):
                    self.log(test_name, False, f"回滚脚本不存在: {script}")
                    return

                # 检查是否可执行
                if not os.access(script_path, os.X_OK):
                    self.log(test_name, False, f"回滚脚本不可执行: {script}")
                    return

            self.log(test_name, True, "回滚脚本就绪")
        except Exception as e:
            self.log(test_name, False, f"回滚脚本检查失败: {e}")

    def test_backward_compatibility(self):
        """测试向后兼容性"""
        test_name = "向后兼容性测试"

        try:
            # 检查原有文件未被破坏性修改
            admin_path = os.path.join(self.project_root, "frontend/admin.html")
            index_path = os.path.join(self.project_root, "frontend/index.html")

            admin_size = os.path.getsize(admin_path)
            index_size = os.path.getsize(index_path)

            # admin.html 应该在 500KB-600KB 之间
            # index.html 应该在 90KB-110KB 之间
            if 500000 < admin_size < 600000 and 90000 < index_size < 110000:
                self.log(test_name, True, "原有页面保持兼容")
            else:
                self.log(
                    test_name,
                    False,
                    f"原有页面大小异常: admin={admin_size}, index={index_size}",
                )
        except Exception as e:
            self.log(test_name, False, f"兼容性检查失败: {e}")

    def test_data_integrity(self):
        """测试数据完整性"""
        test_name = "数据完整性测试"

        db_path = os.path.join(self.project_root, "waterms.db")

        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # 检查数据是否存在
            cursor.execute("SELECT COUNT(*) FROM products")
            products_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM office_pickup")
            pickups_count = cursor.fetchone()[0]

            # 检查 service_type 字段是否有默认值
            cursor.execute(
                "SELECT COUNT(*) FROM products WHERE service_type IS NULL OR service_type = ''"
            )
            null_service_type = cursor.fetchone()[0]

            conn.close()

            if products_count > 0 and pickups_count > 0 and null_service_type == 0:
                self.log(
                    test_name,
                    True,
                    f"数据完整: {products_count} 产品, {pickups_count} 记录",
                )
            else:
                self.log(
                    test_name,
                    False,
                    f"数据问题: 产品={products_count}, 记录={pickups_count}, 空类型={null_service_type}",
                )
        except Exception as e:
            self.log(test_name, False, f"数据检查失败: {e}")

    def test_all_phases_reports(self):
        """测试所有阶段报告"""
        test_name = "阶段报告完整性测试"

        reports = [
            "scripts/PHASE_0_COMPLETION_REPORT.md",
            "scripts/PHASE_1_COMPLETION_REPORT.md",
            "scripts/PHASE_2_COMPLETION_REPORT.md",
            "scripts/PHASE_3_COMPLETION_REPORT.md",
            "scripts/PHASE_4_COMPLETION_REPORT.md",
        ]

        try:
            missing = []
            for report in reports:
                report_path = os.path.join(self.project_root, report)
                if not os.path.exists(report_path):
                    missing.append(report)

            if missing:
                self.log(test_name, False, f"缺少报告: {missing}")
            else:
                self.log(test_name, True, f"所有阶段报告完整 ({len(reports)} 个)")
        except Exception as e:
            self.log(test_name, False, f"报告检查失败: {e}")

    def print_results(self):
        """打印测试结果"""
        print("\n" + "=" * 60)
        print("Phase 5 端到端测试结果")
        print("=" * 60)

        for r in self.results:
            print(r)

        print("\n" + "-" * 60)
        print(f"总计: {self.tests_passed} 通过, {self.tests_failed} 失败")
        print("-" * 60)

        if self.tests_failed == 0:
            print("\n🎉 Phase 5 端到端测试通过！")
        else:
            print("\n⚠️  Phase 5 端到端测试存在问题，请检查")


def main():
    """运行所有测试"""
    runner = E2ETestRunner()

    print("\n📊 Phase 5 数据库测试...")
    runner.test_database_schema()
    runner.test_data_integrity()

    print("\n🔧 Phase 5 后端测试...")
    runner.test_backend_models()
    runner.test_api_services_module()

    print("\ Phase 5 前端测试...")
    runner.test_config_files()
    runner.test_frontend_pages()

    print("\n🔗 Phase 5 兼容性测试...")
    runner.test_backward_compatibility()
    runner.test_rollback_scripts()
    runner.test_all_phases_reports()

    # 打印结果
    runner.print_results()

    # 返回状态码
    sys.exit(0 if runner.tests_failed == 0 else 1)


if __name__ == "__main__":
    main()
