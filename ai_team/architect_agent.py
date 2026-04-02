"""
Architect Agent
===============

角色: 架构师
职责: 输出可落地技术方案，负责技术栈选型与模块划分

Input Format:
    - mvp_plan: MvpPlanSchema (PM输出的MVP方案)

Output Format:
    - TechPlanSchema: 技术方案（含模块划分图、接口定义、开发排期）

Design Standards:
    - 模块划分: 清晰的模块边界
    - 接口定义: RESTful API规范
    - 技术栈选型: 明确版本要求
    - 开发排期: 分阶段实施计划

Created by: AI Architecture Team
Version: 2.0.0
"""

from typing import List, Dict
from ai_team.models import TechPlanSchema, ModuleDesign, TechDependency


class ArchitectAgent:
    """
    Architect Agent - 架构师代理

    核心职责:
    1. 基于MVP方案设计技术架构
    2. 模块划分与接口定义
    3. 技术栈选型
    4. 开发排期规划

    输入输出规范:
    - create_tech_plan(mvp_plan: MvpPlanSchema) -> TechPlanSchema
    - review_code_change(change_description: str) -> Dict
    """

    def __init__(self):
        self.agent_name = "Architect Agent"
        self.agent_role = "架构师"
        self.agent_status = "待命"
        self.tech_stack_requirements = {
            "language": "Python 3.8+",
            "framework": "FastAPI/Flask",
            "database": "PostgreSQL/MySQL",
        }

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

    def create_tech_plan(self, mvp_plan) -> TechPlanSchema:
        """
        创建技术方案

        Args:
            mvp_plan: MVP方案

        Returns:
            TechPlanSchema: 技术方案
        """
        self.set_status("架构设计中")

        modules = [
            ModuleDesign(
                module_name="core_module",
                description="核心业务模块",
                interfaces=["POST /api/v1/core/action", "GET /api/v1/core/status"],
                dependencies=["基础框架", "数据库连接"],
            ),
            ModuleDesign(
                module_name="data_layer",
                description="数据访问层",
                interfaces=["数据库CRUD接口"],
                dependencies=["ORM框架"],
            ),
        ]

        tech_stack = [
            TechDependency(
                name="Python",
                dependency_type="language",
                version="3.8+",
                description="主要开发语言",
            ),
            TechDependency(
                name="FastAPI",
                dependency_type="framework",
                version="0.68+",
                description="Web框架",
            ),
            TechDependency(
                name="pytest",
                dependency_type="testing_tool",
                version="7.0+",
                description="单元测试框架（强制要求）",
            ),
        ]

        tech_plan = TechPlanSchema(
            architecture_diagram=self._generate_architecture_diagram(),
            modules=modules,
            api_definitions=["RESTful API - Version 1.0"],
            development_schedule=[
                "第一阶段: 核心模块开发（2周）",
                "第二阶段: 功能完善（1周）",
                "第三阶段: 测试与优化（1周）",
            ],
            tech_stack=tech_stack,
            raw_content=self._generate_tech_markdown(mvp_plan),
        )

        self.set_status("方案已完成")
        return tech_plan

    def _generate_architecture_diagram(self) -> str:
        """
        生成架构图描述

        Returns:
            str: 架构图文本描述
        """
        return """
架构分层:
┌─────────────────┐
│   Presentation  │  API Layer
├─────────────────┤
│   Business      │  Core Module
├─────────────────┤
│   Data Access   │  Data Layer
├─────────────────┤
│   Infrastructure│  DB/Cache
└─────────────────┘
"""

    def _generate_tech_markdown(self, mvp_plan) -> str:
        """
        生成技术方案Markdown文档

        Args:
            mvp_plan: MVP方案

        Returns:
            str: Markdown格式的技术方案
        """
        mvp_content = (
            mvp_plan.raw_content if hasattr(mvp_plan, "raw_content") else "待补充"
        )

        markdown_template = f"""# 技术方案

## 模块划分
### 核心模块
- `core_module`: 核心业务逻辑
- `data_layer`: 数据访问层

## 接口定义
- RESTful API Version 1.0
- 规范: OpenAPI 3.0

## 技术栈
- Python 3.8+
- FastAPI 0.68+
- pytest 7.0+ （强制单元测试）

## 开发排期
1. 第一阶段: 核心模块开发（2周）
2. 第二阶段: 功能完善（1周）
3. 第三阶段: 测试与优化（1周）

## 基于 MVP 方案
{mvp_content}

---
*所有模块必须包含单元测试，测试覆盖率≥80%*
"""
        return markdown_template

    def review_code_change(self, change_description: str) -> Dict:
        """
        审查代码变更

        Args:
            change_description: 变更描述

        Returns:
            Dict: {
                "approved": bool,
                "comments": List[str],
                "requirements": List[str]
            }
        """
        review_result = {
            "approved": True,
            "comments": ["符合架构设计"],
            "requirements": [
                "必须包含单元测试",
                "遵循RESTful API规范",
                "代码覆盖率≥80%",
            ],
        }

        return review_result

    def validate_tech_plan(self, tech_plan: TechPlanSchema) -> Dict:
        """
        验证技术方案完整性

        Args:
            tech_plan: 技术方案

        Returns:
            Dict: 验证结果
        """
        validation_result = {
            "is_valid": True,
            "modules_count": len(tech_plan.modules),
            "tech_stack_complete": len(tech_plan.tech_stack) >= 3,
            "has_schedule": len(tech_plan.development_schedule) > 0,
        }

        has_test_framework = any(
            "test" in td.dependency_type.lower() for td in tech_plan.tech_stack
        )

        if not has_test_framework:
            validation_result["is_valid"] = False
            validation_result["warning"] = "技术栈缺少测试框架（强制要求）"

        return validation_result
