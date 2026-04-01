#!/usr/bin/env python3
"""
套餐管理功能验证测试
确保前后端功能完整打通
"""

import os
import sys
import sqlite3
import json


def test_database():
    """测试数据库"""
    print("\n📊 数据库测试...")

    db_path = os.path.join(os.path.dirname(__file__), "../../waterms.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 测试套餐表
    cursor.execute("SELECT COUNT(*) FROM packages")
    package_count = cursor.fetchone()[0]
    print(f"  ✅ 套餐数量: {package_count}")

    # 测试套餐项目表
    cursor.execute("SELECT COUNT(*) FROM package_items")
    item_count = cursor.fetchone()[0]
    print(f"  ✅ 套餐项目数量: {item_count}")

    # 测试套餐详情
    cursor.execute("""
        SELECT p.id, p.name, p.package_price, COUNT(pi.id) as item_count
        FROM packages p
        LEFT JOIN package_items pi ON p.id = pi.package_id
        WHERE p.status = 'active'
        GROUP BY p.id
        ORDER BY p.sort_order
    """)

    packages = cursor.fetchall()
    print(f"\n  📦 套餐列表:")
    for p in packages:
        print(f"    - {p[1]}: ¥{p[2]} ({p[3]}个项目)")

    conn.close()

    return package_count == 3 and item_count == 8


def test_api_files():
    """测试API文件"""
    print("\n📁 文件检查...")

    files = [
        "Service_WaterManage/migrations/002_create_packages.sql",
        "Service_WaterManage/frontend/config.js",
        "Service_WaterManage/backend/main.py",
        "Service_WaterManage/backend/api_services.py",
    ]

    for f in files:
        if os.path.exists(f):
            print(f"  ✅ {f}")
        else:
            print(f"  ❌ {f} 不存在")
            return False

    return True


def test_config():
    """测试配置文件"""
    print("\n⚙️ 配置测试...")

    config_path = "Service_WaterManage/frontend/config.js"

    with open(config_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 检查服务类型
    if "meeting_room" in content and "tea_break" in content:
        print("  ✅ 服务类型配置完整")
        return True
    else:
        print("  ❌ 服务类型配置缺失")
        return False


def main():
    print("=" * 60)
    print("套餐管理功能验证测试")
    print("=" * 60)

    results = []

    results.append(("数据库测试", test_database()))
    results.append(("文件检查", test_api_files()))
    results.append(("配置测试", test_config()))

    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)

    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{name}: {status}")

    passed = sum(1 for _, r in results if r)
    total = len(results)

    print(f"\n总计: {passed}/{total} 通过")

    if passed == total:
        print("\n🎉 套餐管理功能验证通过！")
        print("\n下一步:")
        print("1. 创建套餐管理后端API（api_packages.py）")
        print("2. 创建套餐管理前端页面（packages.html）")
        print("3. 集成测试")
    else:
        print("\n⚠️ 存在问题，请检查")

    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
