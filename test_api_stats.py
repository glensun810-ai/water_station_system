"""
API统计端点测试脚本
验证 /api/v1/water/stats/today 和 /api/v1/meeting/stats/today 端点
"""

import requests
import sys

BASE_URL = "http://127.0.0.1:8008"


def test_stats_endpoints():
    """测试统计API端点"""

    print("=" * 60)
    print("API统计端点测试")
    print("=" * 60)

    tests = [
        {
            "name": "水站今日统计",
            "url": f"{BASE_URL}/api/v1/water/stats/today",
            "expected_fields": ["pickup_count", "pending_amount", "alerts"],
        },
        {
            "name": "会议室今日统计",
            "url": f"{BASE_URL}/api/v1/meeting/stats/today",
            "expected_fields": ["booking_count", "pending_approvals", "alerts"],
        },
    ]

    for test in tests:
        print(f"\n测试: {test['name']}")
        print(f"URL: {test['url']}")

        try:
            response = requests.get(test["url"], timeout=5)

            print(f"状态码: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                print(f"返回数据: {data}")

                # 检查必需字段
                missing_fields = []
                for field in test["expected_fields"]:
                    if field not in data:
                        missing_fields.append(field)

                if missing_fields:
                    print(f"❌ 缺少字段: {missing_fields}")
                else:
                    print(f"✓ 所有必需字段都存在")

            elif response.status_code == 401:
                print("⚠️  需要认证（这是预期的行为，因为需要管理员权限）")
                print("✓ API端点存在，需要认证才能访问")

            elif response.status_code == 404:
                print("❌ API端点不存在 - 404错误")

            else:
                print(f"⚠️  其他状态码: {response.status_code}")

        except requests.exceptions.ConnectionError:
            print("❌ 无法连接到服务器")
            print("   请确保服务器正在运行: http://127.0.0.1:8008")

        except Exception as e:
            print(f"❌ 测试失败: {e}")

    print("\n" + "=" * 60)
    print("测试说明:")
    print("- 401错误表示API端点存在但需要认证")
    print("- 404错误表示API端点不存在，需要修复")
    print("- 200成功表示API工作正常")
    print("=" * 60)


if __name__ == "__main__":
    test_stats_endpoints()
