"""
Unit Tests for AI Team Data Models
===================================

测试数据模型的完整性和命名规范
"""

import pytest
from ai_team.models import (
    UserStory,
    FeatureItem,
    TechDependency,
    AcceptanceCriteria,
    MvpPlanSchema,
    TechPlanSchema,
    ModulePackage,
    CodeChange,
    ProjectContext,
    PriorityLevel,
    WorkflowStage,
)


class TestModelsNaming:
    """测试模型命名规范（下划线命名法）"""

    def test_user_story_attributes(self):
        """测试UserStory属性命名"""
        story = UserStory(
            title="测试标题", description="测试描述", acceptance_criteria=["标准1"]
        )
        assert hasattr(story, "title")
        assert hasattr(story, "description")
        assert hasattr(story, "acceptance_criteria")

    def test_feature_item_attributes(self):
        """测试FeatureItem属性命名"""
        feature = FeatureItem(
            name="测试功能",
            description="描述",
            priority_level=PriorityLevel.P0,
            dependencies=[],
        )
        assert hasattr(feature, "priority_level")
        assert hasattr(feature, "dependencies")

    def test_tech_dependency_attributes(self):
        """测试TechDependency属性命名"""
        dep = TechDependency(name="Python", dependency_type="language", version="3.8+")
        assert hasattr(dep, "dependency_type")

    def test_mvp_plan_schema_attributes(self):
        """测试MvpPlanSchema属性命名"""
        mvp = MvpPlanSchema(
            user_stories=[],
            feature_items=[],
            tech_dependencies=[],
            acceptance_criteria=[],
            clarification_questions=[],
        )
        assert hasattr(mvp, "feature_items")
        assert hasattr(mvp, "clarification_questions")

    def test_tech_plan_schema_attributes(self):
        """测试TechPlanSchema属性命名"""
        plan = TechPlanSchema(
            architecture_diagram="test",
            modules=[],
            api_definitions=[],
            development_schedule=[],
            tech_stack=[],
        )
        assert hasattr(plan, "development_schedule")

    def test_module_package_attributes(self):
        """测试ModulePackage属性命名"""
        package = ModulePackage(
            package_name="test",
            code_changes=[],
            test_results=[],
            documentation="",
            nonfunctional_validation={},
        )
        assert hasattr(package, "package_name")
        assert hasattr(package, "nonfunctional_validation")

    def test_project_context_attributes(self):
        """测试ProjectContext属性命名"""
        context = ProjectContext(
            current_stage=WorkflowStage.INIT, user_requirement="test"
        )
        assert hasattr(context, "current_stage")


class TestModelsFunctionality:
    """测试模型功能"""

    def test_mvp_to_dict(self):
        """测试MVP方案字典转换"""
        mvp = MvpPlanSchema(
            user_stories=[UserStory(title="测试", description="描述")],
            feature_items=[
                FeatureItem(
                    name="功能", description="描述", priority_level=PriorityLevel.P0
                )
            ],
            tech_dependencies=[],
            acceptance_criteria=[],
        )

        result = mvp.to_dict()
        assert isinstance(result, dict)
        assert "user_stories" in result
        assert "feature_items" in result

    def test_module_package_has_unit_tests(self):
        """测试模块包单元测试检测"""
        package_with_tests = ModulePackage(
            package_name="test",
            code_changes=[
                CodeChange(
                    file_path="test.py",
                    change_type="new",
                    description="test",
                    has_unit_test=True,
                )
            ],
            test_results=[],
            documentation="",
        )
        assert package_with_tests.has_unit_tests() is True

        package_without_tests = ModulePackage(
            package_name="test",
            code_changes=[
                CodeChange(
                    file_path="test.py",
                    change_type="new",
                    description="test",
                    has_unit_test=False,
                )
            ],
            test_results=[],
            documentation="",
        )
        assert package_without_tests.has_unit_tests() is False

    def test_tech_plan_validation(self):
        """测试技术方案验证"""
        valid_plan = TechPlanSchema(
            architecture_diagram="test",
            modules=[],
            api_definitions=[],
            development_schedule=[],
            tech_stack=[TechDependency(name="Python", dependency_type="language")],
        )
        assert valid_plan.validate_requirements() is True

    def test_project_context_summary(self):
        """测试项目上下文摘要"""
        context = ProjectContext(
            current_stage=WorkflowStage.INIT, user_requirement="测试需求"
        )

        summary = context.get_summary()
        assert isinstance(summary, dict)
        assert summary["stage"] == "init"
        assert summary["requirement_length"] == 4


class TestEnums:
    """测试枚举类"""

    def test_priority_level(self):
        """测试优先级枚举"""
        assert PriorityLevel.P0.value == "P0"
        assert PriorityLevel.P1.value == "P1"
        assert PriorityLevel.P2.value == "P2"

    def test_workflow_stage(self):
        """测试工作流阶段枚举"""
        assert WorkflowStage.INIT.value == "init"
        assert WorkflowStage.PM_PENDING.value == "pm_pending"
        assert WorkflowStage.COMPLETED.value == "completed"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
