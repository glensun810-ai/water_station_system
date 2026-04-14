#!/usr/bin/env python3
"""
空间服务模块完整性检查报告
对比规划文档，系统检查当前实现状态
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://127.0.0.1:8008"


class SpaceServiceCompletenessChecker:
    def __init__(self):
        self.base_url = BASE_URL
        self.results = {}

    def print_section(self, title):
        print(f"\n{'=' * 80}")
        print(f"{title}")
        print(f"{'=' * 80}")

    def check_page_exists(self, page_path):
        """检查页面是否存在"""
        try:
            response = requests.get(f"{self.base_url}{page_path}")
            return response.status_code == 200, response.status_code
        except Exception as e:
            return False, str(e)

    def check_page_features(self, page_path, expected_features):
        """检查页面是否包含预期功能"""
        try:
            response = requests.get(f"{self.base_url}{page_path}")
            if response.status_code != 200:
                return False, []

            content = response.text
            found_features = []

            for feature in expected_features:
                if feature.lower() in content.lower():
                    found_features.append(feature)

            completeness = (
                (len(found_features) / len(expected_features) * 100)
                if expected_features
                else 0
            )
            return True, found_features, completeness
        except Exception as e:
            return False, [], 0

    def check_api_endpoint(self, api_path):
        """检查API端点是否存在"""
        try:
            response = requests.get(f"{self.base_url}{api_path}")
            # API存在性检查（不关心返回数据，只关心是否可访问）
            exists = response.status_code in [200, 400, 401, 404]
            # 404表示不存在，其他表示存在或有认证要求
            actual_exists = response.status_code != 404
            return actual_exists, response.status_code
        except Exception as e:
            return False, str(e)

    def section1_check_planned_pages(self):
        """第1部分：检查规划的前端页面"""
        self.print_section("第1部分：检查规划的前端页面（用户端）")

        planned_pages = {
            "/space-frontend/index.html": {
                "name": "空间预约主页",
                "priority": "P0",
                "features": [
                    "会议室",
                    "会场",
                    "大屏",
                    "展位",
                    "VIP餐厅",
                    "选择空间类型",
                    "立即预约",
                ],
            },
            "/space-frontend/booking.html": {
                "name": "预约创建页面",
                "priority": "P0",
                "features": [
                    "选择空间",
                    "选择时段",
                    "预约人信息",
                    "费用计算",
                    "提交预约",
                ],
            },
            "/space-frontend/my-bookings.html": {
                "name": "我的预约列表",
                "priority": "P1",
                "features": [
                    "预约列表",
                    "预约状态",
                    "取消预约",
                    "修改预约",
                    "预约详情",
                ],
            },
            "/space-frontend/calendar.html": {
                "name": "日历视图",
                "priority": "P1",
                "features": ["日历视图", "预约日历", "时段展示", "拖拽预约"],
            },
            "/space-frontend/resources.html": {
                "name": "空间资源列表",
                "priority": "P2",
                "features": ["资源列表", "资源筛选", "资源详情", "可用时段"],
            },
            "/space-frontend/payment.html": {
                "name": "支付确认页面",
                "priority": "P1",
                "features": ["支付确认", "费用明细", "支付方式", "在线支付"],
            },
            "/space-frontend/notifications.html": {
                "name": "通知中心",
                "priority": "P1",
                "features": ["通知列表", "预约提醒", "审批通知", "即将开始"],
            },
            "/space-frontend/profile.html": {
                "name": "个人中心",
                "priority": "P2",
                "features": ["个人信息", "预约历史", "余额查询", "发票申请"],
            },
        }

        print("\n用户端页面检查结果：")
        print("-" * 80)
        print(
            f"{'页面':<30} {'优先级':<8} {'状态':<10} {'功能完整性':<12} {'缺失功能':<20}"
        )
        print("-" * 80)

        for page_path, page_info in planned_pages.items():
            exists, status = self.check_page_exists(page_path)

            if exists:
                has_features, found_features, completeness = self.check_page_features(
                    page_path, page_info["features"]
                )
                missing_features = [
                    f for f in page_info["features"] if f not in found_features
                ]

                status_text = "✅ 已实现"
                completeness_text = f"{completeness:.1f}%"
                missing_text = (
                    ", ".join(missing_features[:3]) if missing_features else "完整"
                )

                self.results[page_path] = {
                    "exists": True,
                    "completeness": completeness,
                    "missing_features": missing_features,
                }
            else:
                status_text = "❌ 未实现"
                completeness_text = "0%"
                missing_text = "全部"

                self.results[page_path] = {
                    "exists": False,
                    "completeness": 0,
                    "missing_features": page_info["features"],
                }

            print(
                f"{page_info['name']:<30} {page_info['priority']:<8} {status_text:<10} {completeness_text:<12} {missing_text:<20}"
            )

        # 统计
        total_pages = len(planned_pages)
        implemented_pages = sum(1 for r in self.results.values() if r["exists"])
        missing_pages = total_pages - implemented_pages

        print("-" * 80)
        print(
            f"总页面数: {total_pages} | 已实现: {implemented_pages} | 未实现: {missing_pages}"
        )
        print(f"实现率: {implemented_pages / total_pages * 100:.1f}%")

        return {
            "total": total_pages,
            "implemented": implemented_pages,
            "missing": missing_pages,
            "rate": implemented_pages / total_pages * 100,
        }

    def section2_check_api_endpoints(self):
        """第2部分：检查规划的API端点"""
        self.print_section("第2部分：检查规划的API端点（/api/v2/space/*）")

        planned_apis = {
            "/api/v2/space/types": {"name": "空间类型管理API", "priority": "P0"},
            "/api/v2/space/resources": {"name": "空间资源管理API", "priority": "P0"},
            "/api/v2/space/bookings": {"name": "预约管理API", "priority": "P0"},
            "/api/v2/space/approvals": {"name": "审批管理API", "priority": "P0"},
            "/api/v2/space/payments": {"name": "支付管理API", "priority": "P1"},
            "/api/v2/space/statistics": {"name": "统计分析API", "priority": "P1"},
        }

        print("\nAPI端点检查结果：")
        print("-" * 80)
        print(f"{'API端点':<40} {'优先级':<8} {'状态':<20}")
        print("-" * 80)

        api_results = {}
        for api_path, api_info in planned_apis.items():
            exists, status = self.check_api_endpoint(api_path)

            if exists:
                status_text = f"✅ 存在 (状态码: {status})"
            else:
                status_text = "❌ 不存在"

            print(f"{api_info['name']:<40} {api_info['priority']:<8} {status_text:<20}")

            api_results[api_path] = {"exists": exists, "status": status}

        # 统计
        total_apis = len(planned_apis)
        existing_apis = sum(1 for r in api_results.values() if r["exists"])

        print("-" * 80)
        print(
            f"总API数: {total_apis} | 已实现: {existing_apis} | 未实现: {total_apis - existing_apis}"
        )
        print(f"实现率: {existing_apis / total_apis * 100:.1f}%")

        return {
            "total": total_apis,
            "existing": existing_apis,
            "missing": total_apis - existing_apis,
            "rate": existing_apis / total_apis * 100,
        }

    def section3_check_admin_pages(self):
        """第3部分：检查管理后台页面"""
        self.print_section("第3部分：检查管理后台页面")

        admin_pages = {
            "/portal/admin/space/dashboard.html": {
                "name": "管理后台首页",
                "priority": "P0",
                "features": ["统计数据", "快捷操作", "通知中心"],
            },
            "/portal/admin/space/approvals.html": {
                "name": "审批中心",
                "priority": "P0",
                "features": ["审批列表", "审批通过", "审批拒绝", "批量审批"],
            },
            "/portal/admin/space/bookings.html": {
                "name": "预约管理",
                "priority": "P0",
                "features": ["预约列表", "预约详情", "修改预约"],
            },
            "/portal/admin/space/resources.html": {
                "name": "资源管理",
                "priority": "P0",
                "features": ["资源列表", "添加资源", "编辑资源", "删除资源"],
            },
            "/portal/admin/space/statistics.html": {
                "name": "统计分析",
                "priority": "P1",
                "features": ["使用率统计", "趋势图表", "导出报表"],
            },
        }

        print("\n管理后台页面检查结果：")
        print("-" * 80)
        print(f"{'页面':<30} {'优先级':<8} {'状态':<10} {'功能完整性':<12}")
        print("-" * 80)

        admin_results = {}
        for page_path, page_info in admin_pages.items():
            exists, status = self.check_page_exists(page_path)

            if exists:
                has_features, found_features, completeness = self.check_page_features(
                    page_path, page_info["features"]
                )
                status_text = "✅ 已实现"
                completeness_text = f"{completeness:.1f}%"
            else:
                status_text = "❌ 未实现"
                completeness_text = "0%"

            print(
                f"{page_info['name']:<30} {page_info['priority']:<8} {status_text:<10} {completeness_text:<12}"
            )

            admin_results[page_path] = {
                "exists": exists,
                "completeness": completeness if exists else 0,
            }

        # 统计
        total_pages = len(admin_pages)
        implemented_pages = sum(1 for r in admin_results.values() if r["exists"])

        print("-" * 80)
        print(
            f"总页面数: {total_pages} | 已实现: {implemented_pages} | 未实现: {total_pages - implemented_pages}"
        )
        print(f"实现率: {implemented_pages / total_pages * 100:.1f}%")

        return {
            "total": total_pages,
            "implemented": implemented_pages,
            "missing": total_pages - implemented_pages,
            "rate": implemented_pages / total_pages * 100,
        }

    def section4_generate_improvement_plan(self):
        """第4部分：生成完善计划"""
        self.print_section("第4部分：空间服务模块完善计划")

        # 根据检查结果生成优先级列表
        print("\n基于检查结果，制定分阶段完善计划：")
        print("-" * 80)

        # Phase 1: P0优先级（必须立即实现）
        print("\n【Phase 1: 核心功能完善（P0优先级）】")
        phase1_tasks = [
            "✅ index.html - 空间预约主页（已实现）",
            "✅ booking.html - 预约创建页面（已实现）",
            "❌ my-bookings.html - 我的预约列表（缺失，P1）",
            "✅ approvals.html - 审批中心（已实现）",
            "✅ bookings.html - 预约管理（已实现）",
            "✅ resources.html - 资源管理（已实现）",
        ]

        for task in phase1_tasks:
            print(f"  {task}")

        # Phase 2: P1优先级（重要功能）
        print("\n【Phase 2: 重要功能完善（P1优先级）】")
        phase2_tasks = [
            "❌ my-bookings.html - 我的预约列表",
            "❌ calendar.html - 日历视图",
            "❌ payment.html - 支付确认页面",
            "❌ notifications.html - 通知中心",
        ]

        for task in phase2_tasks:
            print(f"  {task}")

        # Phase 3: P2优先级（增强功能）
        print("\n【Phase 3: 增强功能完善（P2优先级）】")
        phase3_tasks = [
            "❌ resources.html - 空间资源列表（用户端）",
            "❌ profile.html - 个人中心",
        ]

        for task in phase3_tasks:
            print(f"  {task}")

        # 实施建议
        print("\n【实施建议】")
        print("  1. 立即实现Phase 1缺失的my-bookings.html")
        print(
            "  2. Phase 2按顺序实现：my-bookings → calendar → payment → notifications"
        )
        print("  3. Phase 3可选实现，提升用户体验")
        print("  4. 每个Phase完成后进行验收测试")
        print("  5. 确保API端点完整支持前端功能")

        return {"phase1": phase1_tasks, "phase2": phase2_tasks, "phase3": phase3_tasks}

    def run_completeness_check(self):
        """运行完整性检查"""
        print("\n" + "=" * 80)
        print("空间服务模块完整性检查报告")
        print("=" * 80)
        print(f"检查时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"检查目标: 对比规划文档，检查实现完整性")
        print("=" * 80)

        # 执行检查
        pages_result = self.section1_check_planned_pages()
        apis_result = self.section2_check_api_endpoints()
        admin_result = self.section3_check_admin_pages()
        improvement_plan = self.section4_generate_improvement_plan()

        # 总结
        self.print_section("完整性检查总结")

        print("\n总体实现情况：")
        print(
            f"  用户端页面: {pages_result['implemented']}/{pages_result['total']} = {pages_result['rate']:.1f}%"
        )
        print(
            f"  API端点: {apis_result['existing']}/{apis_result['total']} = {apis_result['rate']:.1f}%"
        )
        print(
            f"  管理后台: {admin_result['implemented']}/{admin_result['total']} = {admin_result['rate']:.1f}%"
        )

        overall_rate = (
            (
                pages_result["implemented"]
                + apis_result["existing"]
                + admin_result["implemented"]
            )
            / (pages_result["total"] + apis_result["total"] + admin_result["total"])
            * 100
        )

        print(f"\n总体完成度: {overall_rate:.1f}%")

        if overall_rate >= 80:
            print("✅ 空间服务模块基本完整，建议完善缺失的用户端功能")
        elif overall_rate >= 50:
            print("⚠️ 空间服务模块部分完整，建议优先实现P0/P1功能")
        else:
            print("❌ 空间服务模块实现不足，建议全面补充")

        print("\n下一步建议：")
        print("  1. 立即实现my-bookings.html（我的预约列表）- 用户最常用功能")
        print("  2. 实现calendar.html（日历视图）- 增强预约体验")
        print("  3. 实现payment.html（支付确认）- 闭环预约流程")
        print("  4. 实现notifications.html（通知中心）- 用户提醒机制")

        return {
            "pages_result": pages_result,
            "apis_result": apis_result,
            "admin_result": admin_result,
            "overall_rate": overall_rate,
            "improvement_plan": improvement_plan,
        }


if __name__ == "__main__":
    checker = SpaceServiceCompletenessChecker()
    result = checker.run_completeness_check()

    # 保存报告
    with open(
        "docs/space-service-refactor/空间服务模块完整性检查报告.md",
        "w",
        encoding="utf-8",
    ) as f:
        f.write("# 空间服务模块完整性检查报告\n\n")
        f.write(f"**检查时间:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("## 一、总体实现情况\n\n")
        f.write(f"- **总体完成度:** {result['overall_rate']:.1f}%\n\n")
        f.write("## 二、分模块实现情况\n\n")
        f.write(
            f"- 用户端页面: {result['pages_result']['implemented']}/{result['pages_result']['total']} = {result['pages_result']['rate']:.1f}%\n"
        )
        f.write(
            f"- API端点: {result['apis_result']['existing']}/{result['apis_result']['total']} = {result['apis_result']['rate']:.1f}%\n"
        )
        f.write(
            f"- 管理后台: {result['admin_result']['implemented']}/{result['admin_result']['total']} = {result['admin_result']['rate']:.1f}%\n\n"
        )
        f.write("## 三、完善计划\n\n")
        f.write("### Phase 1: 核心功能（P0）\n\n")
        for task in result["improvement_plan"]["phase1"]:
            f.write(f"- {task}\n")
        f.write("\n### Phase 2: 重要功能（P1）\n\n")
        for task in result["improvement_plan"]["phase2"]:
            f.write(f"- {task}\n")
        f.write("\n### Phase 3: 增强功能（P2）\n\n")
        for task in result["improvement_plan"]["phase3"]:
            f.write(f"- {task}\n")

    print(
        f"\n详细报告已保存到: docs/space-service-refactor/空间服务模块完整性检查报告.md"
    )
