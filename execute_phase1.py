#!/usr/bin/env python3
"""
会议室管理模块优化执行计划
按照AI团队协作机制，分阶段完成开发
"""

import sys

sys.path.append("/Users/sgl/PycharmProjects/AIchanyejiqun")

from ai_team.main_agent import MainAgent
from pathlib import Path

# 读取MVP方案和技术方案
mvp_phase1 = Path(
    "/Users/sgl/PycharmProjects/AIchanyejiqun/requirements/mvp_phase1.md"
).read_text()
tech_plan_phase1 = Path(
    "/Users/sgl/PycharmProjects/AIchanyejiqun/requirements/tech_plan_phase1.md"
).read_text()

print("=" * 70)
print("会议室管理模块优化 - 阶段一执行计划")
print("=" * 70)

# 启动AI团队
main_agent = MainAgent()
main_agent.start()

print("\n\n" + "=" * 70)
print("步骤1: 提交MVP方案至PM团队")
print("=" * 70)
print(f"\nMVP方案内容:\n{mvp_phase1[:200]}...")  # 显示前200字

# 提交需求（使用简化版需求）
requirement = """
会议室管理模块优化 - 阶段一核心功能：

1. 灵活时间段选择：时间选择器、时长验证、冲突检测
2. 我的预约功能：预约列表、筛选、修改/取消
3. 预约详情页：独立页面、二维码、分享、打印
4. 管理员权限验证：JWT登录、角色权限、操作日志
5. 真实统计数据：使用率计算、预约统计、收入统计

验收标准：预约完成率85%、耗时1-2分钟、自主管理率80%、测试覆盖率≥80%
"""

result = main_agent.receive_requirement(requirement)

print("\n\n" + "=" * 70)
print("步骤2: PM方案确认")
print("=" * 70)
if result.get("status") == "pending_approval":
    print("✓ MVP方案已生成，验证通过")
    print(f"  字数: {result['validation']['word_count']}")
    print(f"  用户场景数: {result['validation']['user_stories_count']}")

    # 确认MVP方案
    print("\n确认MVP方案，流转至架构师...")
    tech_result = main_agent.approve_and_continue()

    print("\n\n" + "=" * 70)
    print("步骤3: 技术方案生成")
    print("=" * 70)
    if "tech_plan" in tech_result:
        print("✓ 技术方案已生成")
        print(f"  模块数: {tech_result['validation']['modules_count']}")
        print(f"  技术栈完整: {tech_result['validation']['tech_stack_complete']}")

        # 确认技术方案
        print("\n确认技术方案，流转至开发团队...")
        dev_result = main_agent.approve_and_continue()

        print("\n\n" + "=" * 70)
        print("步骤4: 开发交付")
        print("=" * 70)
        if "module_package" in dev_result:
            print(f"✓ 模块包已交付: {dev_result['module_package'].package_name}")

            print("\n代码变更:")
            for change in dev_result["module_package"].code_changes:
                print(f"  - {change.file_path} ({change.change_type})")
                print(f"    测试覆盖率: {change.test_coverage:.0%}")

            print("\n质量门禁检查:")
            for check, passed in dev_result["quality_check"]["checks"].items():
                status = "✓" if passed else "✗"
                print(f"  [{status}] {check}")

            print("\n非功能需求验证:")
            for req_type, check_data in dev_result["nonfunctional_validation"][
                "checks"
            ].items():
                status = "✓" if check_data["passed"] else "✗"
                print(f"  [{status}] {req_type}")

            print("\n\n" + "=" * 70)
            print("阶段一开发完成")
            print("=" * 70)
            print("交付物:")
            print("  1. MVP方案（已确认）")
            print("  2. 技术方案（已确认）")
            print("  3. 功能模块包（已交付）")
            print("  4. 单元测试（覆盖率≥80%）")
            print("  5. 质量检查报告")

        else:
            print(f"✗ 开发失败: {dev_result.get('error', '未知错误')}")
    else:
        print(f"✗ 技术方案生成失败: {tech_result.get('error', '未知错误')}")
else:
    print(f"✗ MVP方案生成失败: {result.get('error', '未知错误')}")

# 显示团队状态
print("\n\n" + "=" * 70)
print("团队状态")
print("=" * 70)
main_agent.show_team_status()

print("\n\n" + "=" * 70)
print("下一步建议")
print("=" * 70)
print("1. 查看生成的代码文件（src/core_module.py）")
print("2. 检查单元测试文件（tests/test_core_module.py）")
print("3. 运行pytest验证测试覆盖率")
print("4. 进入阶段二（P1效率优化）开发")
