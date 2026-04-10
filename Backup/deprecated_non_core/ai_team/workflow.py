"""
Workflow Manager
================

角色: 工作流管理器
职责: 协调各代理执行工作流，加入非功能需求校验

Workflow Stages:
    1. INIT -> PM_PENDING
    2. PM_PENDING -> PM_REVIEW
    3. PM_REVIEW -> ARCHITECT_PENDING
    4. ARCHITECT_PENDING -> ARCHITECT_REVIEW
    5. ARCHITECT_REVIEW -> DEV_PENDING
    6. DEV_PENDING -> TESTING
    7. TESTING -> COMPLETED

Non-Functional Requirements:
    - 性能: 响应时间 < 200ms
    - 安全: 无高危漏洞
    - 可扩展性: 支持横向扩展
    - 可维护性: 代码覆盖率 ≥80%

Created by: AI Architecture Team
Version: 2.0.0
"""

from typing import Dict, List
from ai_team.models import (
    ProjectContext,
    WorkflowStage,
    MvpPlanSchema,
    TechPlanSchema,
    ModulePackage,
)
from ai_team.pm_agent import PMAgent
from ai_team.architect_agent import ArchitectAgent
from ai_team.dev_agent import DevTestAgent


class WorkflowManager:
    """
    Workflow Manager - 工作流管理器

    核心职责:
    1. 协调各代理执行工作流
    2. 状态流转控制
    3. 人工确认点管理
    4. 非功能需求校验（强制）

    输入输出规范:
    - submit_requirement(requirement: str) -> None
    - process_pm_stage() -> Dict
    - process_architect_stage() -> Dict
    - process_dev_stage() -> Dict
    """

    def __init__(self):
        self.pm_agent = PMAgent()
        self.architect_agent = ArchitectAgent()
        self.dev_agent = DevTestAgent()
        self.context = ProjectContext(
            current_stage=WorkflowStage.INIT, user_requirement=""
        )
        self.nonfunctional_requirements = {
            "performance": {"response_time": "< 200ms", "throughput": "> 1000 req/s"},
            "security": {"vulnerability_scan": "无高危", "encryption": "TLS 1.2+"},
            "test_coverage": {"minimum": 0.80, "enforce_unit_tests": True},
        }

    def get_current_stage(self) -> WorkflowStage:
        """
        获取当前阶段

        Returns:
            WorkflowStage: 当前工作流阶段
        """
        return self.context.current_stage

    def submit_requirement(self, requirement: str) -> None:
        """
        提交用户需求

        Args:
            requirement: 用户需求文本
        """
        self.context.user_requirement = requirement
        self.context.current_stage = WorkflowStage.PM_PENDING

    def process_pm_stage(self) -> Dict:
        """
        处理PM阶段

        Returns:
            Dict: {
                "need_clarification": bool,
                "mvp_plan": Optional[MvpPlanSchema],
                "questions": List[str],
                "message": str
            }
        """
        if self.context.current_stage != WorkflowStage.PM_PENDING:
            return {
                "error": "当前阶段不在 PM 待处理状态",
                "current_stage": self.context.current_stage.value,
            }

        analysis = self.pm_agent.analyze_requirement(self.context.user_requirement)

        if analysis["need_clarification"]:
            self.context.questions_for_user = analysis["questions"]
            self.context.current_stage = WorkflowStage.PM_REVIEW
            return {
                "need_clarification": True,
                "questions": analysis["questions"],
                "message": self.pm_agent.format_questions(analysis["questions"]),
                "analysis_result": analysis["analysis_result"],
            }

        mvp_plan = self.pm_agent.create_mvp_plan(self.context.user_requirement)

        validation = self.pm_agent.validate_mvp_plan(mvp_plan)
        if not validation["is_valid"]:
            return {
                "error": "MVP方案验证失败",
                "validation_result": validation,
            }

        self.context.mvp_plan = mvp_plan
        self.context.current_stage = WorkflowStage.PM_REVIEW
        self.context.human_approval_required = True

        return {
            "need_clarification": False,
            "mvp_plan": mvp_plan,
            "validation": validation,
            "message": "MVP 方案已生成并通过验证，等待人工确认",
        }

    def provide_clarification(self, answers: List[str]) -> Dict:
        """
        提供需求澄清

        Args:
            answers: 澄清问题的答案

        Returns:
            Dict: 处理结果
        """
        if self.context.current_stage != WorkflowStage.PM_REVIEW:
            return {
                "error": "当前阶段不在 PM 审核状态",
                "current_stage": self.context.current_stage.value,
            }

        mvp_plan = self.pm_agent.create_mvp_plan(
            self.context.user_requirement, clarifications=answers
        )

        validation = self.pm_agent.validate_mvp_plan(mvp_plan)

        self.context.mvp_plan = mvp_plan
        self.context.human_approval_required = True

        return {
            "mvp_plan": mvp_plan,
            "validation": validation,
            "message": "MVP 方案已生成，等待人工确认",
        }

    def approve_mvp(self) -> Dict:
        """
        确认MVP方案

        Returns:
            Dict: 确认结果
        """
        if self.context.current_stage != WorkflowStage.PM_REVIEW:
            return {
                "error": "当前阶段不在 PM 审核状态",
                "current_stage": self.context.current_stage.value,
            }

        self.context.current_stage = WorkflowStage.ARCHITECT_PENDING
        self.context.human_approval_required = False
        return {
            "message": "MVP 方案已确认，流转至架构师",
            "next_stage": WorkflowStage.ARCHITECT_PENDING.value,
        }

    def process_architect_stage(self) -> Dict:
        """
        处理架构师阶段

        Returns:
            Dict: {
                "tech_plan": TechPlanSchema,
                "validation": Dict,
                "message": str
            }
        """
        if self.context.current_stage != WorkflowStage.ARCHITECT_PENDING:
            return {
                "error": "当前阶段不在架构师待处理状态",
                "current_stage": self.context.current_stage.value,
            }

        if not self.context.mvp_plan:
            return {"error": "缺少 MVP 方案"}

        tech_plan = self.architect_agent.create_tech_plan(self.context.mvp_plan)

        validation = self.architect_agent.validate_tech_plan(tech_plan)
        if not validation["is_valid"]:
            return {
                "error": "技术方案验证失败",
                "validation_result": validation,
                "missing_test_framework": True,
            }

        self.context.tech_plan = tech_plan
        self.context.current_stage = WorkflowStage.ARCHITECT_REVIEW
        self.context.human_approval_required = True

        return {
            "tech_plan": tech_plan,
            "validation": validation,
            "message": "技术方案已生成并通过验证，等待人工确认",
        }

    def approve_tech_plan(self) -> Dict:
        """
        确认技术方案

        Returns:
            Dict: 确认结果
        """
        if self.context.current_stage != WorkflowStage.ARCHITECT_REVIEW:
            return {
                "error": "当前阶段不在架构师审核状态",
                "current_stage": self.context.current_stage.value,
            }

        self.context.current_stage = WorkflowStage.DEV_PENDING
        self.context.human_approval_required = False
        return {
            "message": "技术方案已确认，流转至开发团队",
            "next_stage": WorkflowStage.DEV_PENDING.value,
        }

    def process_dev_stage(self) -> Dict:
        """
        处理开发阶段

        Returns:
            Dict: {
                "module_package": ModulePackage,
                "test_results": Dict,
                "quality_check": Dict,
                "nonfunctional_validation": Dict,
                "message": str
            }
        """
        if self.context.current_stage != WorkflowStage.DEV_PENDING:
            return {
                "error": "当前阶段不在开发待处理状态",
                "current_stage": self.context.current_stage.value,
            }

        if not self.context.tech_plan:
            return {"error": "缺少技术方案"}

        self.context.current_stage = WorkflowStage.DEV_IN_PROGRESS
        module_package = self.dev_agent.implement_module(self.context.tech_plan)

        module_validation = self.dev_agent.validate_module_package(module_package)
        if not module_validation["is_valid"]:
            return {
                "error": "模块包验证失败",
                "validation_result": module_validation,
                "missing_unit_tests": True,
            }

        test_result = self.dev_agent.run_tests(module_package)
        if not test_result["passed"]:
            return {
                "error": "测试未通过",
                "details": test_result,
                "enforce_unit_tests": True,
            }

        quality_check = self.dev_agent.quality_gate_check(module_package)
        if not quality_check["passed"]:
            return {
                "error": "质量门禁未通过",
                "details": quality_check,
                "failed_items": quality_check["failed_items"],
            }

        nonfunctional_validation = self._validate_nonfunctional_requirements(
            module_package
        )
        if not nonfunctional_validation["passed"]:
            return {
                "error": "非功能需求验证失败",
                "details": nonfunctional_validation,
                "failed_requirements": nonfunctional_validation["failed_requirements"],
            }

        self.context.module_packages.append(module_package)
        self.context.current_stage = WorkflowStage.TESTING

        return {
            "module_package": module_package,
            "test_results": test_result,
            "quality_check": quality_check,
            "nonfunctional_validation": nonfunctional_validation,
            "message": "模块开发完成，所有检查通过",
        }

    def _validate_nonfunctional_requirements(
        self, module_package: ModulePackage
    ) -> Dict:
        """
        验证非功能需求

        Args:
            module_package: 模块包

        Returns:
            Dict: 验证结果
        """
        validation_checks = {
            "performance": self._check_performance(module_package),
            "security": self._check_security(module_package),
            "test_coverage": self._check_test_coverage(module_package),
            "scalability": self._check_scalability(module_package),
        }

        all_passed = all(check["passed"] for check in validation_checks.values())

        failed_requirements = [
            key for key, check in validation_checks.items() if not check["passed"]
        ]

        return {
            "passed": all_passed,
            "checks": validation_checks,
            "failed_requirements": failed_requirements,
            "summary": "非功能需求验证通过" if all_passed else "非功能需求验证失败",
        }

    def _check_performance(self, module_package: ModulePackage) -> Dict:
        """检查性能指标"""
        performance_data = module_package.nonfunctional_validation.get(
            "performance", {}
        )
        return {
            "passed": performance_data.get("status") == "passed",
            "response_time": performance_data.get("response_time", "未定义"),
            "throughput": performance_data.get("throughput", "未定义"),
        }

    def _check_security(self, module_package: ModulePackage) -> Dict:
        """检查安全指标"""
        security_data = module_package.nonfunctional_validation.get("security", {})
        static_analysis = module_package.quality_metrics.get("static_analysis", "")

        return {
            "passed": security_data.get("status") == "passed"
            and "无高危漏洞" in static_analysis,
            "vulnerability_scan": security_data.get("vulnerability_scan", "未检查"),
            "encryption": security_data.get("encryption", "未定义"),
        }

    def _check_test_coverage(self, module_package: ModulePackage) -> Dict:
        """检查测试覆盖率"""
        coverage = module_package.quality_metrics.get("test_coverage", 0)
        threshold = self.nonfunctional_requirements["test_coverage"]["minimum"]

        return {
            "passed": coverage >= threshold,
            "current_coverage": coverage,
            "threshold": threshold,
            "has_unit_tests": module_package.has_unit_tests(),
        }

    def _check_scalability(self, module_package: ModulePackage) -> Dict:
        """检查可扩展性"""
        scalability_data = module_package.nonfunctional_validation.get(
            "scalability", {}
        )
        return {
            "passed": scalability_data.get("status") == "passed",
            "horizontal_scaling": scalability_data.get("horizontal_scaling", "未定义"),
            "load_balancing": scalability_data.get("load_balancing", "未定义"),
        }

    def complete_project(self) -> Dict:
        """
        完成项目

        Returns:
            Dict: 完成结果
        """
        self.context.current_stage = WorkflowStage.COMPLETED
        return {
            "message": "项目已完成",
            "project_summary": self.context.get_summary(),
        }

    def get_status(self) -> Dict:
        """
        获取工作流状态

        Returns:
            Dict: {
                "stage": str,
                "pm_status": str,
                "architect_status": str,
                "dev_status": str,
                "human_approval_required": bool,
                "questions_pending": bool,
                "nonfunctional_requirements": Dict
            }
        """
        return {
            "stage": self.context.current_stage.value,
            "pm_status": self.pm_agent.get_status(),
            "architect_status": self.architect_agent.get_status(),
            "dev_status": self.dev_agent.get_status(),
            "human_approval_required": self.context.human_approval_required,
            "questions_pending": len(self.context.questions_for_user) > 0,
            "nonfunctional_requirements": self.nonfunctional_requirements,
        }
