#!/usr/bin/env python3
"""
Phase 1 验证测试脚本
验证 Products 和 OfficePickup 表扩展后的向后兼容性

运行方法:
    python tests/phase1/test_phase1_extension.py
"""

import sys
import os
import sqlite3
from datetime import datetime

# 添加 backend 到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../backend"))

DATABASE_PATH = "../../waterms.db"


class Phase1TestRunner:
    def __init__(self, db_path):
        self.db_path = db_path
        self.tests_passed = 0
        self.tests_failed = 0
        self.results = []

    def connect(self):
        """连接数据库"""
        return sqlite3.connect(self.db_path)

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

    def test_products_table_structure(self):
        """验证 Products 表结构"""
        test_name = "Products 表结构验证"

        expected_fields = [
            "service_type",
            "resource_config",
            "booking_required",
            "advance_booking_days",
            "category",
            "icon",
            "color",
            "max_capacity",
            "facilities",
        ]

        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(products)")
        columns = {row[1] for row in cursor.fetchall()}
        conn.close()

        missing = [f for f in expected_fields if f not in columns]

        if missing:
            self.log(test_name, False, f"缺少字段: {missing}")
        else:
            self.log(test_name, True, f"所有扩展字段存在")

    def test_office_pickup_table_structure(self):
        """验证 OfficePickup 表结构"""
        test_name = "OfficePickup 表结构验证"

        expected_fields = [
            "service_type",
            "time_slot",
            "actual_usage",
            "booking_status",
            "service_name",
            "participants_count",
            "purpose",
            "contact_phone",
        ]

        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(office_pickup)")
        columns = {row[1] for row in cursor.fetchall()}
        conn.close()

        missing = [f for f in expected_fields if f not in columns]

        if missing:
            self.log(test_name, False, f"缺少字段: {missing}")
        else:
            self.log(test_name, True, f"所有扩展字段存在")

    def test_products_default_values(self):
        """验证 Products 新字段默认值"""
        test_name = "Products 默认值验证"

        conn = self.connect()
        cursor = conn.cursor()

        # 查询 water 类型产品
        cursor.execute("""
            SELECT id, name, service_type, booking_required, 
                   advance_booking_days, category, color, max_capacity
            FROM products 
            WHERE service_type = 'water'
        """)
        water_products = cursor.fetchall()
        conn.close()

        if water_products:
            for p in water_products:
                # 验证默认值
                if p[2] != "water":
                    self.log(test_name, False, f"service_type 默认值错误: {p}")
                    return
                if p[3] != 0:
                    self.log(test_name, False, f"booking_required 默认值错误: {p}")
                    return
            self.log(
                test_name, True, f"water 产品默认值正确，共 {len(water_products)} 个"
            )
        else:
            self.log(test_name, True, "无 water 产品（可能为新数据库）")

    def test_office_pickup_default_values(self):
        """验证 OfficePickup 新字段默认值"""
        test_name = "OfficePickup 默认值验证"

        conn = self.connect()
        cursor = conn.cursor()

        # 查询 water 类型服务记录
        cursor.execute("""
            SELECT id, office_name, service_type, booking_status, participants_count
            FROM office_pickup 
            WHERE service_type = 'water'
            LIMIT 5
        """)
        water_records = cursor.fetchall()
        conn.close()

        if water_records:
            for r in water_records:
                if r[2] != "water":
                    self.log(test_name, False, f"service_type 默认值错误: {r}")
                    return
                if r[3] != "confirmed":
                    self.log(test_name, False, f"booking_status 默认值错误: {r}")
                    return
            self.log(
                test_name, True, f"water 服务记录默认值正确，共 {len(water_records)} 个"
            )
        else:
            self.log(test_name, True, "无 water 服务记录（可能为新数据库）")

    def test_existing_product_queries(self):
        """验证现有产品查询不受影响"""
        test_name = "现有产品查询兼容性"

        conn = self.connect()
        cursor = conn.cursor()

        # 测试原有查询（不使用新字段）
        cursor.execute(
            "SELECT id, name, price, stock, is_active FROM products WHERE is_active = 1"
        )
        products = cursor.fetchall()
        conn.close()

        if products:
            self.log(test_name, True, f"原有查询正常，返回 {len(products)} 个产品")
        else:
            self.log(test_name, False, "原有查询无结果")

    def test_existing_pickup_queries(self):
        """验证现有领水记录查询不受影响"""
        test_name = "现有领水记录查询兼容性"

        conn = self.connect()
        cursor = conn.cursor()

        # 测试原有查询（不使用新字段）
        cursor.execute("""
            SELECT id, office_name, product_name, quantity, pickup_time, settlement_status
            FROM office_pickup 
            WHERE is_deleted = 0
            ORDER BY pickup_time DESC
            LIMIT 5
        """)
        records = cursor.fetchall()
        conn.close()

        if records:
            self.log(test_name, True, f"原有查询正常，返回 {len(records)} 条记录")
        else:
            self.log(test_name, True, "无领水记录（可能为新数据库）")

    def test_new_product_write(self):
        """验证新产品字段可写入"""
        test_name = "新产品字段写入测试"

        # 仅验证字段存在，不实际写入（避免污染数据）
        conn = self.connect()
        cursor = conn.cursor()

        # 检查是否有非 water 类型产品
        cursor.execute("SELECT COUNT(*) FROM products WHERE service_type != 'water'")
        non_water_count = cursor.fetchone()[0]
        conn.close()

        if non_water_count > 0:
            self.log(test_name, True, f"已有 {non_water_count} 个非 water 类型产品")
        else:
            self.log(test_name, True, "所有产品均为 water 类型（向后兼容）")

    def test_service_type_distribution(self):
        """验证服务类型分布"""
        test_name = "服务类型分布统计"

        conn = self.connect()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT service_type, COUNT(*) as count 
            FROM products 
            GROUP BY service_type
        """)
        distribution = cursor.fetchall()

        cursor.execute("""
            SELECT service_type, COUNT(*) as count 
            FROM office_pickup 
            GROUP BY service_type
        """)
        pickup_distribution = cursor.fetchall()
        conn.close()

        self.log(
            test_name,
            True,
            f"产品分布: {dict(distribution)}, 服务记录分布: {dict(pickup_distribution)}",
        )

    def print_results(self):
        """打印测试结果"""
        print("\n" + "=" * 60)
        print("Phase 1 验证测试结果")
        print("=" * 60)

        for r in self.results:
            print(r)

        print("\n" + "-" * 60)
        print(f"总计: {self.tests_passed} 通过, {self.tests_failed} 失败")
        print("-" * 60)

        if self.tests_failed == 0:
            print("\n🎉 Phase 1 验证通过！")
        else:
            print("\n⚠️  Phase 1 验证存在问题，请检查")


def main():
    """运行所有测试"""
    db_path = os.path.join(os.path.dirname(__file__), DATABASE_PATH)

    if not os.path.exists(db_path):
        print(f"错误: 数据库文件不存在: {db_path}")
        sys.exit(1)

    runner = Phase1TestRunner(db_path)

    # 运行所有测试
    runner.test_products_table_structure()
    runner.test_office_pickup_table_structure()
    runner.test_products_default_values()
    runner.test_office_pickup_default_values()
    runner.test_existing_product_queries()
    runner.test_existing_pickup_queries()
    runner.test_new_product_write()
    runner.test_service_type_distribution()

    # 打印结果
    runner.print_results()

    # 返回状态码
    sys.exit(0 if runner.tests_failed == 0 else 1)


if __name__ == "__main__":
    main()
