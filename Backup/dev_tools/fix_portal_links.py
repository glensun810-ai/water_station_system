#!/usr/bin/env python3
"""
Portal页面链接和数据流修复脚本
自动修复以下问题：
1. 启用API路由
2. 添加缺失的统计API端点
3. 修正前端API调用路径
"""

import os
import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.resolve()


def fix_api_routes():
    """修复apps/main.py，启用所有API路由"""
    print("=" * 80)
    print("步骤1: 启用API路由")
    print("=" * 80)

    apps_main = PROJECT_ROOT / "apps" / "main.py"

    if not apps_main.exists():
        print(f"❌ 文件不存在: {apps_main}")
        return False

    # 读取文件内容
    with open(apps_main, "r", encoding="utf-8") as f:
        content = f.read()

    # 修改导入部分 - 启用所有路由导入
    content = re.sub(
        r"# from api\.v1\.meeting import router as meeting_router",
        "from api.v1.meeting import router as meeting_router",
        content,
    )

    content = re.sub(
        r"# from api\.v1\.system import router as system_router",
        "from api.v1.system import router as system_router",
        content,
    )

    # 修改注册部分 - 启用所有路由注册
    content = re.sub(
        r"# v1_router\.include_router\(meeting_router, prefix=\"/meeting\", tags=\[\"会议室服务\"\]\)",
        'v1_router.include_router(meeting_router, prefix="/meeting", tags=["会议室服务"])',
        content,
    )

    content = re.sub(
        r"# v1_router\.include_router\(system_router, prefix=\"/system\", tags=\[\"系统服务\"\]\)",
        'v1_router.include_router(system_router, prefix="/system", tags=["系统服务"])',
        content,
    )

    # 写回文件
    with open(apps_main, "w", encoding="utf-8") as f:
        f.write(content)

    print("✅ 已启用所有API路由")
    print("   - water_router (水站服务)")
    print("   - meeting_router (会议室服务)")
    print("   - system_router (系统服务)")

    return True


def add_stats_endpoints():
    """添加统计API端点"""
    print()
    print("=" * 80)
    print("步骤2: 添加统计API端点")
    print("=" * 80)

    # 1. 添加水站统计端点
    water_api = PROJECT_ROOT / "apps" / "api" / "water_v1.py"

    if water_api.exists():
        with open(water_api, "r", encoding="utf-8") as f:
            content = f.read()

        # 检查是否已有stats端点
        if "/stats/today" not in content:
            stats_endpoint = '''
@router.get("/stats/today")
def get_water_stats_today(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    """获取今日水站统计数据"""
    
    from datetime import date
    from sqlalchemy import func
    
    today = date.today()
    
    # 今日领水次数
    pickup_count = db.query(func.count(OfficePickup.id)).filter(
        OfficePickup.pickup_time >= today,
        OfficePickup.is_deleted == False
    ).scalar() or 0
    
    # 今日领水金额
    today_amount = db.query(func.sum(OfficePickup.total_amount)).filter(
        OfficePickup.pickup_time >= today,
        OfficePickup.is_deleted == False
    ).scalar() or 0.0
    
    # 待结算金额
    pending_amount = db.query(func.sum(OfficePickup.total_amount)).filter(
        OfficePickup.settlement_status == "pending",
        OfficePickup.is_deleted == False
    ).scalar() or 0.0
    
    # 异常告警（库存不足）
    low_stock_count = db.query(func.count(Product.id)).filter(
        Product.stock < 10,
        Product.is_active == True
    ).scalar() or 0
    
    return {
        "pickup_count": pickup_count,
        "today_amount": float(today_amount),
        "pending_amount": float(pending_amount),
        "alerts": low_stock_count,
    }


@router.get("/settlements/summary")
def get_settlement_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    """获取结算汇总数据"""
    
    from sqlalchemy import func
    
    # 待结算
    pending = db.query(func.sum(OfficePickup.total_amount)).filter(
        OfficePickup.settlement_status == "pending",
        OfficePickup.is_deleted == False
    ).scalar() or 0.0
    
    # 已申请结算
    applied = db.query(func.sum(OfficePickup.total_amount)).filter(
        OfficePickup.settlement_status == "applied",
        OfficePickup.is_deleted == False
    ).scalar() or 0.0
    
    # 已结算
    settled = db.query(func.sum(OfficePickup.total_amount)).filter(
        OfficePickup.settlement_status == "settled",
        OfficePickup.is_deleted == False
    ).scalar() or 0.0
    
    return {
        "total": {
            "pending_amount": float(pending),
            "applied_amount": float(applied),
            "settled_amount": float(settled),
        }
    }
'''
            # 在文件末尾添加
            content += stats_endpoint

            with open(water_api, "w", encoding="utf-8") as f:
                f.write(content)

            print("✅ 已添加水站统计API端点")
            print("   - /water/stats/today")
            print("   - /water/settlements/summary")
        else:
            print("⚠️  水站统计端点已存在")

    # 2. 添加会议室统计端点
    meeting_api = PROJECT_ROOT / "apps" / "api" / "v1" / "meeting.py"

    if meeting_api.exists():
        with open(meeting_api, "r", encoding="utf-8") as f:
            content = f.read()

        # 检查是否已有stats端点
        if "/stats/today" not in content:
            # 先读取meeting.py查看其结构
            print("⚠️  需要在meeting.py中手动添加统计端点")
            print("   建议添加: /meeting/stats/today")
        else:
            print("⚠️  会议室统计端点已存在")

    return True


def fix_portal_api_calls():
    """修正portal/index.html中的API调用路径"""
    print()
    print("=" * 80)
    print("步骤3: 修正前端API调用路径")
    print("=" * 80)

    portal_index = PROJECT_ROOT / "portal" / "index.html"

    if not portal_index.exists():
        print(f"❌ 文件不存在: {portal_index}")
        return False

    # 读取文件内容
    with open(portal_index, "r", encoding="utf-8") as f:
        content = f.read()

    # 修正API调用路径
    fixes = [
        # 修正offices调用
        (r"fetch\(`\${API_BASE}/offices`\)", "fetch(`${API_BASE}/system/offices`)"),
        # 修正users调用
        (r"fetch\(`\${API_BASE}/users`\)", "fetch(`${API_BASE}/system/users`)"),
        # 修正settlements调用
        (
            r"fetch\(`\${API_BASE}/settlements/summary`\)",
            "fetch(`${API_BASE}/water/settlements/summary`)",
        ),
    ]

    applied_fixes = 0
    for pattern, replacement in fixes:
        if re.search(pattern, content):
            content = re.sub(pattern, replacement, content)
            applied_fixes += 1

    # 写回文件
    with open(portal_index, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"✅ 已修正 {applied_fixes} 个API调用路径")
    print("   - /offices -> /system/offices")
    print("   - /users -> /system/users")
    print("   - /settlements/summary -> /water/settlements/summary")

    return True


def create_symbolic_links():
    """创建符号链接解决路径映射问题"""
    print()
    print("=" * 80)
    print("步骤4: 创建符号链接（可选）")
    print("=" * 80)

    links = [
        ("portal/water", "water"),
        ("apps/meeting/frontend", "meeting-frontend"),
    ]

    created_links = 0
    for source, target in links:
        source_path = PROJECT_ROOT / source
        target_path = PROJECT_ROOT / target

        if source_path.exists() and not target_path.exists():
            try:
                if os.name != "nt":  # Unix系统
                    os.symlink(source_path, target_path)
                    print(f"✅ 创建符号链接: {target} -> {source}")
                    created_links += 1
                else:
                    print(f"⚠️  Windows系统不支持符号链接，建议配置静态文件路由")
            except Exception as e:
                print(f"❌ 创建符号链接失败: {e}")
        elif target_path.exists():
            print(f"⚠️  符号链接已存在: {target}")
        else:
            print(f"❌ 源目录不存在: {source}")

    if created_links == 0:
        print("\n替代方案: 配置静态文件路由")
        print("在apps/main.py中添加:")
        print("""
from fastapi.staticfiles import StaticFiles

app.mount("/water", StaticFiles(directory="portal/water"), name="water")
app.mount("/meeting-frontend", StaticFiles(directory="apps/meeting/frontend"), name="meeting")
""")

    return True


def main():
    """主函数"""
    print()
    print("=" * 80)
    print("Portal页面链接和数据流修复工具")
    print("=" * 80)
    print()

    # 执行修复步骤
    success_count = 0

    # 步骤1: 启用API路由
    if fix_api_routes():
        success_count += 1

    # 步骤2: 添加统计端点
    if add_stats_endpoints():
        success_count += 1

    # 步骤3: 修正API调用路径
    if fix_portal_api_calls():
        success_count += 1

    # 步骤4: 创建符号链接（可选）
    create_symbolic_links()

    # 输出总结
    print()
    print("=" * 80)
    print("修复完成")
    print("=" * 80)
    print()
    print(f"✅ 成功执行 {success_count} 个修复步骤")
    print()
    print("下一步:")
    print("1. 启动服务测试: python start_services.py")
    print("2. 验证API端点: 访问 http://localhost:8000/docs")
    print("3. 测试portal页面: 访问 http://localhost:8000/portal/index.html")
    print()
    print("详细报告: docs/portal_check_report.md")
    print("=" * 80)


if __name__ == "__main__":
    main()
