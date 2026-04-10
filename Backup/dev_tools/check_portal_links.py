#!/usr/bin/env python3
"""
Portal页面链接完整性检查脚本
检查所有一级、二级链接是否指向正确的文件
"""

import os
import json
from pathlib import Path
from urllib.parse import urlparse, parse_qs

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.resolve()

# Portal index.html中提取的链接
PORTAL_LINKS = {
    "一级链接": [
        {
            "label": "水站服务",
            "href": "/water/index.html",
            "expected_file": "portal/water/index.html",
        },
        {
            "label": "空间服务（会议室）",
            "href": "/meeting-frontend/index.html",
            "expected_file": "apps/meeting/frontend/index.html",
        },
    ],
    "二级链接": [
        # 水站相关
        {
            "label": "水站查看记录",
            "href": "/water/index.html?tab=records",
            "expected_file": "portal/water/index.html",
        },
        # 会议室相关
        {
            "label": "会议室预约",
            "href": "/meeting-frontend/index.html",
            "expected_file": "apps/meeting/frontend/index.html",
        },
        {
            "label": "我的预约",
            "href": "/meeting-frontend/my_bookings.html",
            "expected_file": "apps/meeting/frontend/my_bookings.html",
        },
        {
            "label": "会议室日历",
            "href": "/meeting-frontend/calendar.html",
            "expected_file": "apps/meeting/frontend/calendar.html",
        },
        # 登录相关
        {
            "label": "登录页面",
            "href": "/portal/admin/login.html",
            "expected_file": "portal/admin/login.html",
        },
        # 管理后台相关
        {
            "label": "管理后台入口",
            "href": "/portal/admin/index.html",
            "expected_file": "portal/admin/index.html",
        },
        {
            "label": "水站工作台",
            "href": "/portal/admin/water/dashboard.html",
            "expected_file": "portal/admin/water/dashboard.html",
        },
        {
            "label": "领水记录管理",
            "href": "/portal/admin/water/pickups.html",
            "expected_file": "portal/admin/water/pickups.html",
        },
        {
            "label": "结算管理",
            "href": "/portal/admin/water/settlement_v3.html",
            "expected_file": "portal/admin/water/settlement_v3.html",
        },
        {
            "label": "产品管理",
            "href": "/portal/admin/water/products.html",
            "expected_file": "portal/admin/water/products.html",
        },
        {
            "label": "预付账户",
            "href": "/portal/admin/water/accounts.html",
            "expected_file": "portal/admin/water/accounts.html",
        },
        # 会议室管理相关
        {
            "label": "预约管理",
            "href": "/portal/admin/index.html?module=meeting",
            "expected_file": "portal/admin/index.html",
        },
        {
            "label": "审批中心",
            "href": "/portal/admin/index.html?module=meeting&tab=approvals",
            "expected_file": "portal/admin/index.html",
        },
        {
            "label": "会议室管理",
            "href": "/portal/admin/index.html?module=meeting&tab=rooms",
            "expected_file": "portal/admin/index.html",
        },
        # 系统管理相关
        {
            "label": "办公室列表",
            "href": "/portal/admin/offices.html",
            "expected_file": "portal/admin/offices.html",
        },
        {
            "label": "新增办公室",
            "href": "/portal/admin/offices.html?action=add",
            "expected_file": "portal/admin/offices.html",
        },
        {
            "label": "用户列表",
            "href": "/portal/admin/users.html",
            "expected_file": "portal/admin/users.html",
        },
        {
            "label": "管理员列表",
            "href": "/portal/admin/users.html?role=admin",
            "expected_file": "portal/admin/users.html",
        },
        {
            "label": "结算列表",
            "href": "/portal/admin/settlements.html",
            "expected_file": "portal/admin/settlements.html",
        },
        {
            "label": "结算汇总",
            "href": "/portal/admin/settlements.html?tab=summary",
            "expected_file": "portal/admin/settlements.html",
        },
        # 用户功能
        {
            "label": "我的余额",
            "href": "/portal/settlement.html",
            "expected_file": "portal/settlement.html",
        },
        # 底部导航
        {
            "label": "水站管理（管理员）",
            "href": "/portal/admin/water/dashboard.html",
            "expected_file": "portal/admin/water/dashboard.html",
            "note": "管理员视角",
        },
        {
            "label": "水站服务（普通用户）",
            "href": "/portal/water/index.html",
            "expected_file": "portal/water/index.html",
            "note": "用户视角",
        },
    ],
}


def check_file_exists(file_path):
    """检查文件是否存在"""
    full_path = PROJECT_ROOT / file_path
    return full_path.exists(), str(full_path)


def check_all_links():
    """检查所有链接"""
    results = {
        "一级链接": {"total": 0, "passed": 0, "failed": [], "warnings": []},
        "二级链接": {"total": 0, "passed": 0, "failed": [], "warnings": []},
    }

    print("=" * 80)
    print("Portal页面链接完整性检查")
    print("=" * 80)
    print()

    # 检查一级链接
    print("【一级链接检查】")
    print("-" * 80)
    for link in PORTAL_LINKS["一级链接"]:
        results["一级链接"]["total"] += 1

        # 检查href路径和实际文件路径是否匹配
        href_path = link["href"].lstrip("/")
        expected_file = link["expected_file"]

        # 检查文件是否存在
        file_exists, file_full_path = check_file_exists(expected_file)

        # 检查href路径是否正确
        href_file_exists, href_file_path = check_file_exists(href_path)

        status_symbol = "✅" if file_exists else "❌"

        if file_exists:
            if not href_file_exists:
                # href路径不存在，但expected_file存在 - 需要路径映射
                results["一级链接"]["passed"] += 1
                results["一级链接"]["warnings"].append(
                    {
                        "label": link["label"],
                        "href": link["href"],
                        "expected_file": expected_file,
                        "issue": "链接路径需要服务器路由映射",
                        "actual_file": file_full_path,
                    }
                )
                print(f"{status_symbol} {link['label']}")
                print(f"   链接路径: {link['href']}")
                print(f"   实际文件: {expected_file} ✓")
                print(f"   ⚠️  需要路由映射: href路径 '{href_path}' 不存在")
            else:
                # href路径和expected_file都存在且相同
                results["一级链接"]["passed"] += 1
                print(f"{status_symbol} {link['label']}")
                print(f"   链接路径: {link['href']}")
                print(f"   实际文件: {expected_file} ✓")
        else:
            results["一级链接"]["failed"].append(
                {
                    "label": link["label"],
                    "href": link["href"],
                    "expected_file": expected_file,
                    "issue": "文件不存在",
                }
            )
            print(f"{status_symbol} {link['label']}")
            print(f"   链接路径: {link['href']}")
            print(f"   ❌ 文件不存在: {expected_file}")

        print()

    # 检查二级链接
    print()
    print("【二级链接检查】")
    print("-" * 80)
    for link in PORTAL_LINKS["二级链接"]:
        results["二级链接"]["total"] += 1

        href_path = link["href"].lstrip("/")
        expected_file = link["expected_file"]

        # 解析查询参数（不影响文件检查）
        parsed = urlparse(link["href"])
        base_path = parsed.path.lstrip("/")

        # 检查文件是否存在
        file_exists, file_full_path = check_file_exists(expected_file)
        href_file_exists, href_file_path = check_file_exists(base_path)

        status_symbol = "✅" if file_exists else "❌"

        if file_exists:
            if not href_file_exists:
                results["二级链接"]["passed"] += 1
                results["二级链接"]["warnings"].append(
                    {
                        "label": link["label"],
                        "href": link["href"],
                        "expected_file": expected_file,
                        "issue": "链接路径需要服务器路由映射",
                        "actual_file": file_full_path,
                    }
                )
                print(f"{status_symbol} {link['label']}")
                print(f"   链接路径: {link['href']}")
                print(f"   实际文件: {expected_file} ✓")
                if link.get("note"):
                    print(f"   备注: {link['note']}")
                print(f"   ⚠️  需要路由映射: href路径 '{base_path}' 不存在")
            else:
                results["二级链接"]["passed"] += 1
                print(f"{status_symbol} {link['label']}")
                print(f"   链接路径: {link['href']}")
                print(f"   实际文件: {expected_file} ✓")
                if link.get("note"):
                    print(f"   备注: {link['note']}")
        else:
            results["二级链接"]["failed"].append(
                {
                    "label": link["label"],
                    "href": link["href"],
                    "expected_file": expected_file,
                    "issue": "文件不存在",
                }
            )
            print(f"{status_symbol} {link['label']}")
            print(f"   链接路径: {link['href']}")
            print(f"   ❌ 文件不存在: {expected_file}")
            if link.get("note"):
                print(f"   备注: {link['note']}")

        print()

    # 输出汇总结果
    print()
    print("=" * 80)
    print("检查汇总")
    print("=" * 80)

    for category in ["一级链接", "二级链接"]:
        stats = results[category]
        print(f"\n{category}:")
        print(f"  总数: {stats['total']}")
        print(f"  通过: {stats['passed']}")
        print(f"  失败: {len(stats['failed'])}")
        print(f"  警告: {len(stats['warnings'])}")

        if stats["failed"]:
            print(f"\n  ❌ 失败的链接:")
            for item in stats["failed"]:
                print(f"     - {item['label']}: {item['issue']}")

        if stats["warnings"]:
            print(f"\n  ⚠️  需要注意的链接:")
            for item in stats["warnings"]:
                print(f"     - {item['label']}: {item['issue']}")

    # 保存详细报告
    report_file = PROJECT_ROOT / "docs" / "portal_link_check_report.json"
    report_file.parent.mkdir(parents=True, exist_ok=True)

    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print()
    print(f"详细报告已保存到: {report_file}")

    # 返回总体结果
    all_passed = (
        len(results["一级链接"]["failed"]) == 0
        and len(results["二级链接"]["failed"]) == 0
    )
    has_warnings = (
        len(results["一级链接"]["warnings"]) > 0
        or len(results["二级链接"]["warnings"]) > 0
    )

    return all_passed, has_warnings


def generate_fix_recommendations():
    """生成修复建议"""
    print()
    print("=" * 80)
    print("修复建议")
    print("=" * 80)
    print()

    print("【路径映射配置】")
    print("-" * 80)
    print("需要在服务器配置中添加以下路由映射:")
    print()
    print("1. 水站服务路径映射:")
    print("   /water/index.html -> portal/water/index.html")
    print("   /water/* -> portal/water/*")
    print()
    print("2. 会议室服务路径映射:")
    print("   /meeting-frontend/index.html -> apps/meeting/frontend/index.html")
    print("   /meeting-frontend/* -> apps/meeting/frontend/*")
    print()

    print("【可选的修复方案】")
    print("-" * 80)
    print("方案1: 更新portal/index.html中的链接路径")
    print("   将 /water/index.html 改为 /portal/water/index.html")
    print("   将 /meeting-frontend/index.html 改为需要映射的路径")
    print()
    print("方案2: 创建符号链接或实际目录")
    print("   ln -s portal/water water")
    print("   ln -s apps/meeting/frontend meeting-frontend")
    print()
    print("方案3: 配置服务器静态文件路由")
    print("   在FastAPI或HTTP服务器中配置静态文件映射")
    print()


if __name__ == "__main__":
    all_passed, has_warnings = check_all_links()
    generate_fix_recommendations()

    print()
    print("=" * 80)
    if all_passed and not has_warnings:
        print("✅ 所有链接检查通过，无需修复")
    elif all_passed and has_warnings:
        print("⚠️  所有文件存在，但需要配置路径映射")
    else:
        print("❌ 有链接指向的文件不存在，需要修复")
    print("=" * 80)
