"""
系统健康检查脚本
验证所有API端点和数据库连接
"""

import requests
import sqlite3
from datetime import datetime

BASE_URL = "http://127.0.0.1:8008"
DB_PATH = "./data/app.db"


def check_database():
    """检查数据库连接和数据"""
    print("=" * 60)
    print("数据库检查")
    print("=" * 60)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    tables = {
        "products": "产品数据",
        "meeting_rooms": "会议室数据",
        "users": "用户数据",
        "office": "办公室数据",
        "office_pickup": "领水记录",
        "meeting_bookings": "预约记录",
    }

    for table, desc in tables.items():
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"✓ {desc} ({table}): {count} 条记录")
        except Exception as e:
            print(f"✗ {desc} ({table}): 错误 - {str(e)}")

    conn.close()


def check_api_endpoints():
    """检查API端点"""
    print("\n" + "=" * 60)
    print("API端点检查")
    print("=" * 60)

    # 先获取登录token
    login_data = {"username": "admin", "password": "123456"}
    response = requests.post(f"{BASE_URL}/api/v1/system/auth/login", json=login_data)

    if response.status_code == 200:
        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print("✓ 登录认证: 成功")
    else:
        print("✗ 登录认证: 失败")
        return

    endpoints = {
        "一级功能 - 水站产品": {"url": "/api/v1/water/products", "auth": False},
        "一级功能 - 办公室": {"url": "/api/v1/water/offices", "auth": True},
        "一级功能 - 会议室": {"url": "/api/v1/meeting/rooms", "auth": True},
        "二级功能 - 领水记录": {"url": "/api/v1/water/pickups", "auth": True},
        "二级功能 - 用户管理": {"url": "/api/v1/system/users", "auth": True},
        "二级功能 - 办公室管理": {"url": "/api/v1/system/offices", "auth": True},
    }

    for name, config in endpoints.items():
        url = BASE_URL + config["url"]
        try:
            if config["auth"]:
                response = requests.get(url, headers=headers)
            else:
                response = requests.get(url)

            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    print(f"✓ {name}: {len(data)} 条数据")
                elif isinstance(data, dict) and "total" in data:
                    print(f"✓ {name}: {data['total']} 条数据")
                else:
                    print(f"✓ {name}: 正常")
            else:
                print(f"✗ {name}: HTTP {response.status_code}")
        except Exception as e:
            print(f"✗ {name}: 错误 - {str(e)}")


def check_frontend_pages():
    """检查前端页面"""
    print("\n" + "=" * 60)
    print("前端页面检查")
    print("=" * 60)

    pages = {
        "Portal首页": "/portal/index.html",
        "会议室前端": "/meeting-frontend/index.html",
    }

    for name, path in pages.items():
        url = BASE_URL + path
        try:
            response = requests.get(url)
            if response.status_code == 200:
                print(f"✓ {name}: 可访问")
            else:
                print(f"✗ {name}: HTTP {response.status_code}")
        except Exception as e:
            print(f"✗ {name}: 错误 - {str(e)}")


def main():
    """主函数"""
    print("\n" + "=" * 60)
    print(f"AI产业集群空间服务系统 - 健康检查")
    print(f"检查时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    check_database()
    check_api_endpoints()
    check_frontend_pages()

    print("\n" + "=" * 60)
    print("健康检查完成")
    print("=" * 60)


if __name__ == "__main__":
    main()
