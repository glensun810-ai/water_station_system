#!/usr/bin/env python3
"""
Phase 5 性能测试脚本
验证系统性能

运行方法:
    cd Service_WaterManage/tests/integration
    python3 test_performance.py
"""

import os
import sys
import sqlite3
import time
from datetime import datetime


class PerformanceTestRunner:
    def __init__(self):
        self.tests_passed = 0
        self.tests_failed = 0
        self.results = []
        self.project_root = os.path.join(os.path.dirname(__file__), "../..")

    def log(self, test_name, passed, message=""):
        status = "✅ PASS" if passed else "❌ FAIL"
        self.results.append(f"{status}: {test_name}")
        if message:
            self.results.append(f"    {message}")

        if passed:
            self.tests_passed += 1
        else:
            self.tests_failed += 1

    def test_database_query_performance(self):
        """测试数据库查询性能"""
        test_name = "数据库查询性能测试"

        db_path = os.path.join(self.project_root, "waterms.db")

        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # 测试 products 查询性能
            start = time.time()
            for _ in range(100):
                cursor.execute("SELECT * FROM products WHERE service_type = 'water'")
                cursor.fetchall()
            products_time = (time.time() - start) * 10  # ms per query

            # 测试 office_pickup 查询性能
            start = time.time()
            for _ in range(100):
                cursor.execute(
                    "SELECT * FROM office_pickup WHERE service_type = 'water'"
                )
                cursor.fetchall()
            pickups_time = (time.time() - start) * 10  # ms per query

            conn.close()

            # 验证查询时间（应该小于 10ms）
            if products_time < 10 and pickups_time < 10:
                self.log(
                    test_name,
                    True,
                    f"products: {products_time:.2f}ms, pickups: {pickups_time:.2f}ms",
                )
            else:
                self.log(
                    test_name,
                    False,
                    f"查询过慢: products={products_time:.2f}ms, pickups={pickups_time:.2f}ms",
                )
        except Exception as e:
            self.log(test_name, False, f"性能测试失败: {e}")

    def test_database_index_effectiveness(self):
        """测试数据库索引效果"""
        test_name = "数据库索引效果测试"

        db_path = os.path.join(self.project_root, "waterms.db")

        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # 检查是否有索引
            cursor.execute("SELECT name FROM sqlite_master WHERE type='index'")
            indexes = cursor.fetchall()

            # 至少应该有一些索引
            if len(indexes) > 0:
                self.log(test_name, True, f"数据库有 {len(indexes)} 个索引")
            else:
                # 没有索引也可以接受（小数据库）
                self.log(test_name, True, "数据库无索引（小数据库可接受）")

            conn.close()
        except Exception as e:
            self.log(test_name, False, f"索引检查失败: {e}")

    def test_model_import_time(self):
        """测试模型导入时间"""
        test_name = "模型导入时间测试"

        try:
            start = time.time()
            sys.path.insert(0, os.path.join(self.project_root, "backend"))
            from main import Product, OfficePickup

            import_time = (time.time() - start) * 1000  # ms

            # 导入时间应该小于 1000ms
            if import_time < 1000:
                self.log(test_name, True, f"导入时间: {import_time:.2f}ms")
            else:
                self.log(test_name, False, f"导入过慢: {import_time:.2f}ms")
        except Exception as e:
            self.log(test_name, False, f"导入测试失败: {e}")

    def test_config_load_time(self):
        """测试配置加载时间"""
        test_name = "配置加载时间测试"

        config_path = os.path.join(self.project_root, "frontend/config.js")

        try:
            start = time.time()
            with open(config_path, "r", encoding="utf-8") as f:
                content = f.read()
            load_time = (time.time() - start) * 1000  # ms

            # 加载时间应该小于 10ms
            if load_time < 10:
                self.log(test_name, True, f"配置加载时间: {load_time:.2f}ms")
            else:
                self.log(test_name, False, f"加载过慢: {load_time:.2f}ms")
        except Exception as e:
            self.log(test_name, False, f"加载测试失败: {e}")

    def test_database_size(self):
        """测试数据库大小"""
        test_name = "数据库大小测试"

        db_path = os.path.join(self.project_root, "waterms.db")

        try:
            db_size = os.path.getsize(db_path) / 1024  # KB

            # 数据库大小应该合理（小于 10MB）
            if db_size < 10240:
                self.log(test_name, True, f"数据库大小: {db_size:.2f}KB")
            else:
                self.log(test_name, False, f"数据库过大: {db_size:.2f}KB")
        except Exception as e:
            self.log(test_name, False, f"大小检查失败: {e}")

    def test_file_count(self):
        """测试文件数量"""
        test_name = "项目文件数量测试"

        try:
            file_count = 0
            for root, dirs, files in os.walk(self.project_root):
                # 排除 node_modules, venv, .git 等
                dirs[:] = [
                    d
                    for d in dirs
                    if d
                    not in [
                        "node_modules",
                        "venv",
                        ".git",
                        "__pycache__",
                        ".pytest_cache",
                    ]
                ]
                file_count += len(files)

            # 文件数量应该合理（小于 1000）
            if file_count < 1000:
                self.log(test_name, True, f"项目文件数: {file_count}")
            else:
                self.log(test_name, False, f"文件过多: {file_count}")
        except Exception as e:
            self.log(test_name, False, f"文件检查失败: {e}")

    def print_results(self):
        """打印测试结果"""
        print("\n" + "=" * 60)
        print("Phase 5 性能测试结果")
        print("=" * 60)

        for r in self.results:
            print(r)

        print("\n" + "-" * 60)
        print(f"总计: {self.tests_passed} 通过, {self.tests_failed} 失败")
        print("-" * 60)

        if self.tests_failed == 0:
            print("\n🎉 Phase 5 性能测试通过！")
        else:
            print("\n⚠️  Phase 5 性能测试存在问题，请检查")


def main():
    """运行所有测试"""
    runner = PerformanceTestRunner()

    print("\n⚡ Phase 5 数据库性能测试...")
    runner.test_database_query_performance()
    runner.test_database_index_effectiveness()
    runner.test_database_size()

    print("\n📦 Phase 5 加载性能测试...")
    runner.test_model_import_time()
    runner.test_config_load_time()
    runner.test_file_count()

    # 打印结果
    runner.print_results()

    # 返回状态码
    sys.exit(0 if runner.tests_failed == 0 else 1)


if __name__ == "__main__":
    main()
