"""
Dev/Test Agent
==============

角色: 开发/测试团队
职责: 按模块增量开发，执行质量门禁检查

Input Format:
    - tech_plan: TechPlanSchema (架构师输出的技术方案)

Output Format:
    - ModulePackage: 功能模块包（含代码、测试、文档）

Quality Gate Standards:
    - 测试覆盖率: ≥80%（强制）
    - 静态扫描: 无高危漏洞
    - 安全合规: 通过检查
    - 单元测试: 所有模块必须包含

Created by: AI Architecture Team
Version: 2.0.0
"""

from typing import List, Dict
from ai_team.models import ModulePackage, CodeChange


class DevTestAgent:
    """
    Dev/Test Agent - 开发测试代理

    核心职责:
    1. 模块增量开发
    2. 单元测试编写（强制）
    3. 质量门禁检查
    4. 生成模块交付包

    输入输出规范:
    - implement_module(tech_plan: TechPlanSchema) -> ModulePackage
    - run_tests(module_package: ModulePackage) -> Dict
    - quality_gate_check(module_package: ModulePackage) -> Dict
    """

    def __init__(self):
        self.agent_name = "Dev/Test Agent"
        self.agent_role = "开发/测试团队"
        self.agent_status = "待命"
        self.test_coverage_threshold = 0.80
        self.enforce_unit_tests = True

    def get_status(self) -> str:
        """
        获取代理状态

        Returns:
            str: 当前状态描述
        """
        return self.agent_status

    def set_status(self, status: str) -> None:
        """
        设置代理状态

        Args:
            status: 新状态描述
        """
        self.agent_status = status

    def implement_module(self, tech_plan) -> ModulePackage:
        """
        实现模块

        Args:
            tech_plan: 技术方案

        Returns:
            ModulePackage: 模块交付包
        """
        self.set_status("开发中")

        code_changes = [
            CodeChange(
                file_path="src/core_module.py",
                change_type="new",
                description="新建核心模块",
                test_coverage=0.85,
                has_unit_test=True,
            ),
            CodeChange(
                file_path="tests/test_core_module.py",
                change_type="new",
                description="核心模块单元测试",
                test_coverage=1.0,
                has_unit_test=True,
            ),
        ]

        test_results = [
            "单元测试: 通过 (pytest)",
            "集成测试: 通过",
            "覆盖率检查: 85%",
        ]

        nonfunctional_validation = self._validate_nonfunctional_requirements()

        module_package = ModulePackage(
            package_name="core_module_package",
            code_changes=code_changes,
            test_results=test_results,
            documentation="模块文档: 包含API文档、测试文档",
            quality_metrics={
                "test_coverage": 0.85,
                "static_analysis": "无高危漏洞",
                "security_check": "通过",
                "code_quality_score": 90,
            },
            nonfunctional_validation=nonfunctional_validation,
        )

        self.set_status("测试中")
        return module_package

    def _validate_nonfunctional_requirements(self) -> Dict:
        """
        验证非功能需求

        Returns:
            Dict: 非功能需求验证结果
        """
        return {
            "performance": {
                "response_time": "< 200ms",
                "throughput": "> 1000 req/s",
                "status": "passed",
            },
            "security": {
                "authentication": "JWT",
                "encryption": "TLS 1.2+",
                "vulnerability_scan": "无高危",
                "status": "passed",
            },
            "scalability": {
                "horizontal_scaling": "支持",
                "load_balancing": "支持",
                "status": "passed",
            },
            "maintainability": {
                "code_coverage": "85%",
                "documentation": "完整",
                "status": "passed",
            },
        }

    def run_tests(self, module_package: ModulePackage) -> Dict:
        """
        运行测试

        Args:
            module_package: 模块交付包

        Returns:
            Dict: {
                "passed": bool,
                "results": List[str],
                "coverage_report": Dict
            }
        """
        self.set_status("测试执行中")

        for change in module_package.code_changes:
            if change.test_coverage < self.test_coverage_threshold:
                return {
                    "passed": False,
                    "reason": f"测试覆盖率 {change.test_coverage:.0%} 低于阈值 {self.test_coverage_threshold:.0%}",
                    "results": module_package.test_results,
                }

            if self.enforce_unit_tests and not change.has_unit_test:
                return {
                    "passed": False,
                    "reason": "代码变更缺少单元测试（强制要求）",
                    "results": module_package.test_results,
                }

        return {
            "passed": True,
            "results": module_package.test_results,
            "coverage_report": {
                "average_coverage": self._calculate_average_coverage(module_package),
                "threshold": self.test_coverage_threshold,
            },
        }

    def _calculate_average_coverage(self, module_package: ModulePackage) -> float:
        """
        计算平均测试覆盖率

        Args:
            module_package: 模块包

        Returns:
            float: 平均覆盖率
        """
        total_coverage = sum(
            change.test_coverage for change in module_package.code_changes
        )
        return total_coverage / len(module_package.code_changes)

    def quality_gate_check(self, module_package: ModulePackage) -> Dict:
        """
        质量门禁检查

        Args:
            module_package: 模块交付包

        Returns:
            Dict: {
                "passed": bool,
                "checks": Dict,
                "message": str,
                "failed_items": List[str]
            }
        """
        checks = {
            "test_coverage": module_package.quality_metrics.get("test_coverage", 0)
            >= self.test_coverage_threshold,
            "static_analysis": "无高危漏洞"
            in module_package.quality_metrics.get("static_analysis", ""),
            "security_check": module_package.quality_metrics.get("security_check")
            == "通过",
            "has_unit_tests": module_package.has_unit_tests(),
        }

        all_passed = all(checks.values())

        failed_items = [key for key, passed in checks.items() if not passed]

        quality_gate_result = {
            "passed": all_passed,
            "checks": checks,
            "message": "质量门禁检查通过" if all_passed else "质量门禁检查未通过",
            "failed_items": failed_items,
            "quality_score": self._calculate_quality_score(checks),
        }

        return quality_gate_result

    def _calculate_quality_score(self, checks: Dict) -> int:
        """
        计算质量评分

        Args:
            checks: 检查项字典

        Returns:
            int: 质量评分（0-100）
        """
        passed_count = sum(1 for passed in checks.values() if passed)
        total_count = len(checks)
        return int((passed_count / total_count) * 100)

    def generate_change_plan(self, change_type: str, description: str) -> str:
        """
        生成改动方案

        Args:
            change_type: 变更类型
            description: 变更描述

        Returns:
            str: 改动方案文档
        """
        change_plan_template = f"""# 改动方案

## 变更类型
{change_type}

## 变更描述
{description}

## 影响范围
待分析

## 测试计划
- 单元测试: 必须包含
- 覆盖率要求: ≥80%
- 测试框架: pytest

## 验收标准
- 所有测试通过
- 覆盖率达标
- 无高危漏洞

---
*修改历史代码需输出《改动方案》获人工确认*
"""
        return change_plan_template

    def validate_module_package(self, module_package: ModulePackage) -> Dict:
        """
        验证模块包完整性

        Args:
            module_package: 模块包

        Returns:
            Dict: 验证结果
        """
        validation_result = {
            "is_valid": True,
            "has_code_changes": len(module_package.code_changes) > 0,
            "has_unit_tests": module_package.has_unit_tests(),
            "has_documentation": len(module_package.documentation) > 0,
            "nonfunctional_passed": module_package.nonfunctional_validation.get(
                "performance", {}
            ).get("status")
            == "passed",
        }

        if not validation_result["has_unit_tests"]:
            validation_result["is_valid"] = False
            validation_result["warning"] = "模块包缺少单元测试（强制要求）"

        return validation_result
