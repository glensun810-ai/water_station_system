"""
Main Agent
==========

角色: 主代理
职责: 协调整个AI开发团队，管理用户交互

Input Format:
    - requirement: str (用户需求)

Output Format:
    - Dict: 处理结果和状态信息

Interaction Pattern:
    1. 启动团队
    2. 接收需求
    3. 澄清需求（必要时）
    4. 确认方案并继续

Created by: AI Architecture Team
Version: 2.0.0
"""

from ai_team.workflow import WorkflowManager
from ai_team.models import WorkflowStage


class MainAgent:
    """
    Main Agent - 主代理

    核心职责:
    1. 启动AI开发团队
    2. 接收用户需求
    3. 协调工作流执行
    4. 提供用户交互界面

    输入输出规范:
    - receive_requirement(requirement: str) -> Dict
    - approve_and_continue() -> Dict
    - show_team_status() -> None
    """

    def __init__(self):
        self.agent_name = "Main Agent"
        self.agent_role = "主代理"
        self.workflow = WorkflowManager()
        self.agent_status = "已启动"

    def start(self) -> None:
        """
        启动AI团队

        Displays:
            团队启动信息和状态
        """
        print("=" * 70)
        print("AI 全栈开发团队（优化版 v2.0）已启动")
        print("=" * 70)
        print(f"\n主代理: {self.agent_name}")
        print(f"状态: {self.agent_status}")
        print("\n团队成员:")
        print("  - PM Agent (产品经理): 待命")
        print("  - Architect Agent (架构师): 待命")
        print("  - Dev/Test Agent (开发/测试): 待命")
        print("\n当前阶段: 初始化完成，等待产品需求输入")
        print("\n质量标准:")
        print("  ✓ 测试覆盖率 ≥80%（强制）")
        print("  ✓ 所有模块必须包含单元测试")
        print("  ✓ 非功能需求验证（性能/安全/可扩展性）")
        print("=" * 70)

    def receive_requirement(self, requirement: str) -> dict:
        """
        接收产品需求

        Args:
            requirement: 用户需求

        Returns:
            Dict: 处理结果
        """
        print("\n" + "=" * 70)
        print("接收产品需求")
        print("=" * 70)
        print(f"\n需求内容: {requirement}")

        self.workflow.submit_requirement(requirement)
        print("\n需求已提交给 PM 团队...")

        result = self.workflow.process_pm_stage()

        if result.get("need_clarification"):
            print("\n" + "=" * 70)
            print("PM 团队反馈")
            print("=" * 70)
            print(result["message"])
            return {
                "status": "need_clarification",
                "questions": result["questions"],
                "analysis_result": result.get("analysis_result"),
            }
        else:
            print("\n" + "=" * 70)
            print("MVP 方案已生成")
            print("=" * 70)
            print("\n方案内容:")
            print(result["mvp_plan"].raw_content)

            if "validation" in result:
                print("\n验证结果:")
                for key, value in result["validation"].items():
                    print(f"  {key}: {value}")

            print("\n等待人工确认...")
            return {
                "status": "pending_approval",
                "mvp_plan": result["mvp_plan"],
                "validation": result.get("validation"),
            }

    def provide_clarification(self, answers: list) -> dict:
        """
        提供需求澄清

        Args:
            answers: 澄清问题的答案

        Returns:
            Dict: 处理结果
        """
        print("\n" + "=" * 70)
        print("接收需求澄清")
        print("=" * 70)

        result = self.workflow.provide_clarification(answers)
        print("\nMVP 方案已更新:")
        print(result["mvp_plan"].raw_content)

        if "validation" in result:
            print("\n验证结果:")
            for key, value in result["validation"].items():
                print(f"  {key}: {value}")

        print("\n等待人工确认...")
        return result

    def approve_and_continue(self) -> dict:
        """
        确认方案并继续工作流

        Returns:
            Dict: 处理结果
        """
        status = self.workflow.get_status()

        if status["stage"] == WorkflowStage.PM_REVIEW.value:
            print("\n" + "=" * 70)
            print("MVP 方案确认")
            print("=" * 70)

            result = self.workflow.approve_mvp()
            print(result["message"])

            print("\n流转至架构师...")
            tech_result = self.workflow.process_architect_stage()

            if "error" in tech_result:
                print("\n错误:")
                print(tech_result["error"])
                if "validation_result" in tech_result:
                    print("验证结果:", tech_result["validation_result"])
                return tech_result

            print("\n" + "=" * 70)
            print("技术方案已生成")
            print("=" * 70)
            print("\n方案内容:")
            print(tech_result["tech_plan"].raw_content)

            if "validation" in tech_result:
                print("\n验证结果:")
                for key, value in tech_result["validation"].items():
                    print(f"  {key}: {value}")

            print("\n等待人工确认...")
            return tech_result

        elif status["stage"] == WorkflowStage.ARCHITECT_REVIEW.value:
            print("\n" + "=" * 70)
            print("技术方案确认")
            print("=" * 70)

            result = self.workflow.approve_tech_plan()
            print(result["message"])

            print("\n流转至开发团队...")
            dev_result = self.workflow.process_dev_stage()

            if "error" in dev_result:
                print("\n开发过程出错:")
                print(dev_result["error"])
                if "details" in dev_result:
                    print("详细信息:", dev_result["details"])
                return dev_result

            print("\n" + "=" * 70)
            print("功能模块包已交付")
            print("=" * 70)
            print(f"\n模块名称: {dev_result['module_package'].package_name}")

            print("\n代码变更:")
            for change in dev_result["module_package"].code_changes:
                print(f"  - {change.file_path} ({change.change_type})")
                print(f"    单元测试: {'✓' if change.has_unit_test else '✗'}")
                print(f"    测试覆盖率: {change.test_coverage:.0%}")

            print("\n测试结果:")
            for test_result in dev_result["test_results"]["results"]:
                print(f"  ✓ {test_result}")

            print("\n质量门禁检查:")
            for check, passed in dev_result["quality_check"]["checks"].items():
                status_mark = "✓" if passed else "✗"
                print(f"  [{status_mark}] {check}")

            print("\n非功能需求验证:")
            nonfunc_val = dev_result["nonfunctional_validation"]
            for req_type, check_data in nonfunc_val["checks"].items():
                status_mark = "✓" if check_data["passed"] else "✗"
                print(f"  [{status_mark}] {req_type}")

            return dev_result

        else:
            return {
                "error": f"当前阶段 {status['stage']} 无法执行确认操作",
                "current_stage": status["stage"],
            }

    def get_status(self) -> dict:
        """
        获取团队状态

        Returns:
            Dict: 状态信息
        """
        return self.workflow.get_status()

    def show_team_status(self) -> None:
        """
        显示团队状态

        Displays:
            团队各成员状态
        """
        status = self.workflow.get_status()
        print("\n" + "=" * 70)
        print("团队状态")
        print("=" * 70)
        print(f"\n当前阶段: {status['stage']}")
        print(f"PM 团队: {status['pm_status']}")
        print(f"架构师: {status['architect_status']}")
        print(f"开发/测试: {status['dev_status']}")
        print(f"需要人工确认: {'是' if status['human_approval_required'] else '否'}")

        print("\n非功能需求标准:")
        for req_type, req_data in status["nonfunctional_requirements"].items():
            print(f"  {req_type}: {req_data}")

        print("=" * 70)
