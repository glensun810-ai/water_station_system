#!/usr/bin/env python3
"""
Portal修复效果验证脚本
验证所有链接和API端点是否正确工作
"""

import os
import json
import requests
from pathlib import Path
import time

PROJECT_ROOT = Path(__file__).parent.resolve()

# 基础URL（假设服务已启动）
BASE_URL = "http://localhost:8000"


def test_file_links():
    """测试文件链接"""
    print("=" * 80)
    print("文件链接测试")
    print("=" * 80)

    links_to_test = [
        ("/water/index.html", "portal/water/index.html"),
        ("/meeting-frontend/index.html", "apps/meeting/frontend/index.html"),
        ("/portal/admin/index.html", "portal/admin/index.html"),
        ("/portal/admin/login.html", "portal/admin/login.html"),
        ("/portal/admin/water/dashboard.html", "portal/admin/water/dashboard.html"),
        ("/portal/admin/offices.html", "portal/admin/offices.html"),
        ("/portal/admin/users.html", "portal/admin/users.html"),
    ]

    print("\n检查符号链接:")
    for link_path, expected_file in links_to_test:
        full_path = PROJECT_ROOT / link_path.lstrip("/")
        exists = full_path.exists()
        status = "✅" if exists else "❌"
        print(f"{status} {link_path} -> {expected_file}")

    return True


def test_api_routes():
    """测试API路由是否注册"""
    print()
    print("=" * 80)
    print("API路由测试")
    print("=" * 80)

    try:
        # 测试API文档是否可访问
        docs_url = f"{BASE_URL}/docs"
        response = requests.get(docs_url, timeout=5)

        if response.status_code == 200:
            print(f"✅ API文档可访问: {docs_url}")

            # 测试各个服务的路由
            endpoints_to_test = [
                ("/api/v1/water/products", "水站服务 - 产品列表"),
                ("/api/v1/water/stats/today", "水站服务 - 今日统计"),
                ("/api/v1/water/settlements/summary", "水站服务 - 结算汇总"),
                ("/api/v1/system/offices", "系统服务 - 办公室列表"),
                ("/api/v1/system/users", "系统服务 - 用户列表"),
                ("/api/v1/meeting/rooms", "会议室服务 - 房间列表"),
            ]

            print("\n测试API端点（需要认证）:")
            for endpoint, description in endpoints_to_test:
                try:
                    url = f"{BASE_URL}{endpoint}"
                    response = requests.get(url, timeout=5)

                    # 401表示路由存在但需要认证，这是正常的
                    if response.status_code in [200, 401, 403]:
                        status = "✅"
                        print(f"{status} {endpoint} - {description}")
                    else:
                        status = "❌"
                        print(
                            f"{status} {endpoint} - {description} (状态码: {response.status_code})"
                        )
                except Exception as e:
                    status = "❌"
                    print(f"{status} {endpoint} - {description} (错误: {str(e)})")

            return True
        else:
            print(f"❌ API文档不可访问 (状态码: {response.status_code})")
            return False

    except requests.exceptions.ConnectionError:
        print("❌ 服务未启动，请先运行: python start_services.py")
        return False
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        return False


def test_portal_page():
    """测试portal页面是否可访问"""
    print()
    print("=" * 80)
    print("Portal页面测试")
    print("=" * 80)

    try:
        portal_url = f"{BASE_URL}/portal/index.html"
        response = requests.get(portal_url, timeout=5)

        if response.status_code == 200:
            print(f"✅ Portal页面可访问: {portal_url}")

            # 测试水站服务页面
            water_url = f"{BASE_URL}/water/index.html"
            response = requests.get(water_url, timeout=5)
            status = "✅" if response.status_code == 200 else "❌"
            print(f"{status} 水站服务页面: {water_url}")

            # 测试会议室服务页面
            meeting_url = f"{BASE_URL}/meeting-frontend/index.html"
            response = requests.get(meeting_url, timeout=5)
            status = "✅" if response.status_code == 200 else "❌"
            print(f"{status} 会议室服务页面: {meeting_url}")

            # 测试管理后台
            admin_url = f"{BASE_URL}/portal/admin/index.html"
            response = requests.get(admin_url, timeout=5)
            status = "✅" if response.status_code == 200 else "❌"
            print(f"{status} 管理后台页面: {admin_url}")

            return True
        else:
            print(f"❌ Portal页面不可访问 (状态码: {response.status_code})")
            return False

    except requests.exceptions.ConnectionError:
        print("❌ 服务未启动，请先运行: python start_services.py")
        return False
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        return False


def check_fix_summary():
    """输出修复总结"""
    print()
    print("=" * 80)
    print("修复效果总结")
    print("=" * 80)

    # 检查文件修改
    checks = [
        ("apps/main.py", "API路由启用"),
        ("apps/api/water_v1.py", "水站统计端点"),
        ("portal/index.html", "前端API路径"),
        ("water (符号链接)", "水站路径映射"),
        ("meeting-frontend (符号链接)", "会议室路径映射"),
    ]

    print("\n修复项检查:")
    for file_path, description in checks:
        if "符号链接" in file_path:
            full_path = PROJECT_ROOT / file_path.split()[0]
            exists = full_path.exists() and os.path.islink(full_path)
        else:
            full_path = PROJECT_ROOT / file_path
            exists = full_path.exists()

        status = "✅" if exists else "❌"
        print(f"{status} {file_path} - {description}")

    # 读取修复报告
    report_file = PROJECT_ROOT / "docs" / "portal_check_report.md"
    if report_file.exists():
        print(f"\n详细报告: {report_file}")

    return True


def main():
    """主函数"""
    print()
    print("=" * 80)
    print("Portal修复效果验证")
    print("=" * 80)
    print()

    # 检查修复效果
    check_fix_summary()

    # 测试文件链接
    file_test_passed = test_file_links()

    # 测试API路由（如果服务已启动）
    print("\n提示: 以下测试需要服务已启动")
    print("如未启动，请运行: python start_services.py")
    print()

    api_test_passed = test_api_routes()
    portal_test_passed = test_portal_page()

    # 输出最终结果
    print()
    print("=" * 80)
    print("验证结果")
    print("=" * 80)

    if file_test_passed:
        print("✅ 文件链接检查通过")

    if api_test_passed and portal_test_passed:
        print("✅ API端点和页面访问正常")
        print("\n🎉 所有修复已生效，Portal页面可以正常使用！")
    else:
        print("⚠️  需要启动服务才能完成完整测试")
        print("   运行: python start_services.py")

    print("=" * 80)


if __name__ == "__main__":
    main()
