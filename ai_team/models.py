"""
AI Team Data Models
===================

数据模型定义 - 统一使用下划线命名法

命名规范:
- 类名: PascalCase (如 UserStory)
- 属性名: snake_case (如 user_stories)
- 方法名: snake_case (如 get_mvp_plan)

Created by: AI Architecture Team
Version: 2.0.0
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict
from enum import Enum


class PriorityLevel(Enum):
    """功能优先级枚举"""

    P0 = "P0"  # 核心功能
    P1 = "P1"  # 重要功能
    P2 = "P2"  # 辅助功能


class WorkflowStage(Enum):
    """工作流阶段枚举"""

    INIT = "init"
    PM_PENDING = "pm_pending"
    PM_REVIEW = "pm_review"
    ARCHITECT_PENDING = "architect_pending"
    ARCHITECT_REVIEW = "architect_review"
    DEV_PENDING = "dev_pending"
    DEV_IN_PROGRESS = "dev_in_progress"
    TESTING = "testing"
    COMPLETED = "completed"


@dataclass
class UserStory:
    """
    用户故事模型

    Attributes:
        title: 用户故事标题
        description: 详细描述
        acceptance_criteria: 验收标准列表
    """

    title: str
    description: str
    acceptance_criteria: List[str] = field(default_factory=list)


@dataclass
class FeatureItem:
    """
    功能项模型

    Attributes:
        name: 功能名称
        description: 功能描述
        priority_level: 优先级
        dependencies: 依赖项列表
    """

    name: str
    description: str
    priority_level: PriorityLevel
    dependencies: List[str] = field(default_factory=list)


@dataclass
class TechDependency:
    """
    技术依赖项

    Attributes:
        name: 技术名称
        dependency_type: 依赖类型 (framework/library/service)
        version: 版本号
        description: 描述
    """

    name: str
    dependency_type: str
    version: Optional[str] = None
    description: Optional[str] = None


@dataclass
class AcceptanceCriteria:
    """
    验收标准

    Attributes:
        metric_name: 指标名称
        target_value: 目标值
        measurement_method: 测量方法
    """

    metric_name: str
    target_value: str
    measurement_method: str


@dataclass
class MvpPlanSchema:
    """
    MVP方案数据结构

    Attributes:
        user_stories: 用户故事列表
        feature_items: 功能项列表
        tech_dependencies: 技术依赖列表
        acceptance_criteria: 验收标准列表
        clarification_questions: 澄清问题列表
        raw_content: 原始Markdown内容
    """

    user_stories: List[UserStory]
    feature_items: List[FeatureItem]
    tech_dependencies: List[TechDependency]
    acceptance_criteria: List[AcceptanceCriteria]
    clarification_questions: Optional[List[str]] = None
    raw_content: str = ""

    def to_dict(self) -> Dict:
        """转换为字典格式"""
        return {
            "user_stories": [
                {"title": us.title, "description": us.description}
                for us in self.user_stories
            ],
            "feature_items": [
                {"name": f.name, "priority": f.priority_level.value}
                for f in self.feature_items
            ],
            "tech_dependencies": [
                {"name": td.name, "type": td.dependency_type}
                for td in self.tech_dependencies
            ],
            "acceptance_criteria": [
                {"metric": ac.metric_name, "target": ac.target_value}
                for ac in self.acceptance_criteria
            ],
        }


@dataclass
class ModuleDesign:
    """
    模块设计

    Attributes:
        module_name: 模块名称
        description: 模块描述
        interfaces: 接口列表
        dependencies: 依赖列表
    """

    module_name: str
    description: str
    interfaces: List[str]
    dependencies: List[str]


@dataclass
class TechPlanSchema:
    """
    技术方案数据结构

    Attributes:
        architecture_diagram: 架构图描述
        modules: 模块列表
        api_definitions: API定义列表
        development_schedule: 开发排期
        tech_stack: 技术栈列表
        raw_content: 原始Markdown内容
    """

    architecture_diagram: str
    modules: List[ModuleDesign]
    api_definitions: List[str]
    development_schedule: List[str]
    tech_stack: List[TechDependency]
    raw_content: str = ""

    def validate_requirements(self) -> bool:
        """验证技术方案完整性"""
        return len(self.modules) > 0 and len(self.tech_stack) > 0


@dataclass
class CodeChange:
    """
    代码变更记录

    Attributes:
        file_path: 文件路径
        change_type: 变更类型 (new/modify/delete)
        description: 变更描述
        test_coverage: 测试覆盖率
        has_unit_test: 是否包含单元测试
    """

    file_path: str
    change_type: str
    description: str
    test_coverage: float = 0.0
    has_unit_test: bool = False


@dataclass
class ModulePackage:
    """
    模块交付包

    Attributes:
        package_name: 包名称
        code_changes: 代码变更列表
        test_results: 测试结果列表
        documentation: 文档内容
        quality_metrics: 质量指标字典
        nonfunctional_validation: 非功能需求验证结果
    """

    package_name: str
    code_changes: List[CodeChange]
    test_results: List[str]
    documentation: str
    quality_metrics: Dict = field(default_factory=dict)
    nonfunctional_validation: Dict = field(default_factory=dict)

    def has_unit_tests(self) -> bool:
        """检查是否包含单元测试"""
        return any(change.has_unit_test for change in self.code_changes)


@dataclass
class ProjectContext:
    """
    项目上下文

    Attributes:
        current_stage: 当前阶段
        user_requirement: 用户需求
        mvp_plan: MVP方案
        tech_plan: 技术方案
        module_packages: 模块包列表
        human_approval_required: 需要人工确认
        questions_for_user: 待用户回答问题
    """

    current_stage: WorkflowStage
    user_requirement: str
    mvp_plan: Optional[MvpPlanSchema] = None
    tech_plan: Optional[TechPlanSchema] = None
    module_packages: List[ModulePackage] = field(default_factory=list)
    human_approval_required: bool = False
    questions_for_user: List[str] = field(default_factory=list)

    def get_summary(self) -> Dict:
        """获取项目摘要"""
        return {
            "stage": self.current_stage.value,
            "requirement_length": len(self.user_requirement),
            "has_mvp": self.mvp_plan is not None,
            "has_tech_plan": self.tech_plan is not None,
            "modules_count": len(self.module_packages),
        }
