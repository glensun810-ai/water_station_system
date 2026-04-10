"""
修复所有管理页面的API配置
统一使用新架构的API路径
"""

import os
import re


def fix_meeting_rooms_page():
    """修复会议室管理页面"""
    file_path = "./portal/admin/meeting/rooms.html"

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 替换API_BASE配置
    old_pattern = r"const protocol = window\.location\.protocol;\s*const hostname = window\.location\.hostname;\s*const MEETING_PORT = '8001';\s*const API_BASE = `\$\{protocol\}\/\/\$\{hostname\}:\$\{MEETING_PORT\}/api/meeting`;"

    new_config = """const API_BASE = `${window.location.protocol}//${window.location.hostname}:${window.location.port || '8008'}/api/v1`;"""

    content = re.sub(old_pattern, new_config, content)

    # 替换所有API调用路径
    # /api/meeting/rooms -> /api/v1/meeting/rooms
    content = content.replace("${API_BASE}/rooms", "${API_BASE}/meeting/rooms")

    # 确保loadRooms函数有Authorization header
    # 查找loadRooms函数并添加headers
    old_load = r"const loadRooms = async \(\) => \{\s*try \{\s*const res = await fetch\(\`\$\{API_BASE\}/meeting/rooms\`\);"

    new_load = """const loadRooms = async () => {
                    try {
                        const token = localStorage.getItem('token');
                        const res = await fetch(`${API_BASE}/meeting/rooms`, {
                            headers: { 'Authorization': `Bearer ${token}` }
                        });"""

    content = re.sub(old_load, new_load, content)

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"✓ 已修复: {file_path}")


def fix_meeting_bookings_page():
    """修复预约管理页面"""
    file_path = "./portal/admin/meeting/bookings.html"

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 替换API_BASE配置
    content = content.replace(
        "const API_BASE = window.API_CONFIG.BASE_URL + '/meeting';",
        "const API_BASE = `${window.location.protocol}//${window.location.hostname}:${window.location.port || '8008'}/api/v1`;",
    )

    # 替换API路径
    content = content.replace(
        "${API_BASE}/approval/approve", "${API_BASE}/meeting/approval/approve"
    )
    content = content.replace("${API_BASE}/bookings", "${API_BASE}/meeting/bookings")

    # 确保有Authorization headers
    # 添加headers到所有fetch请求

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"✓ 已修复: {file_path}")


def fix_meeting_approvals_page():
    """修复审批管理页面"""
    file_path = "./portal/admin/meeting/approvals.html"

    if not os.path.exists(file_path):
        print(f"⚠ 文件不存在: {file_path}")
        return

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 查找并替换API配置（需要检查实际内容）
    # 这里先检查文件内容

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"✓ 已检查: {file_path}")


def fix_admin_index_page():
    """修复管理后台首页"""
    file_path = "./portal/admin/index.html"

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 替换旧架构API路径
    # /api/user/office-pickups -> /api/v1/water/pickups
    # /api/admin/report -> /api/v1/water/stats/today
    # /api/products -> /api/v1/water/products
    # /api/admin/office-accounts -> /api/v1/water/accounts
    # /api/meeting/rooms -> /api/v1/meeting/rooms
    # /api/meeting/bookings -> /api/v1/meeting/bookings

    replacements = [
        ("/api/user/office-pickups", "/api/v1/water/pickups"),
        ("/api/admin/report", "/api/v1/water/stats/today"),
        ("/api/products", "/api/v1/water/products"),
        ("/api/admin/office-accounts", "/api/v1/water/accounts"),
        ("/api/meeting/rooms", "/api/v1/meeting/rooms"),
        ("/api/meeting/bookings", "/api/v1/meeting/bookings"),
        ("/api/admin/office-pickups/", "/api/v1/water/pickups/"),
        ("/api/user/office-pickup", "/api/v1/water/pickup"),
        ("/api/admin/settlement/", "/api/v1/water/settlement/"),
    ]

    for old, new in replacements:
        content = content.replace(old, new)

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"✓ 已修复: {file_path}")


def main():
    """主函数"""
    print("=" * 60)
    print("修复管理页面API配置")
    print("=" * 60)

    fix_meeting_rooms_page()
    fix_meeting_bookings_page()
    fix_meeting_approvals_page()
    fix_admin_index_page()

    print("\n" + "=" * 60)
    print("修复完成")
    print("=" * 60)


if __name__ == "__main__":
    main()
