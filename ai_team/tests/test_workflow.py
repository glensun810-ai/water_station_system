"""
Unit Tests for Workflow Manager
================================

测试工作流管理器和非功能需求校验
"""

import pytest
from ai_team.workflow import WorkflowManager
from ai_team.models import WorkflowStage


class TestWorkflowManager:
    """测试工作流管理器"""

    def setup_method(self):
        """测试前初始化"""
        self.manager = WorkflowManager()

    def test_initial_state(self):
        """测试初始状态"""
        assert self.manager.get_current_stage() == WorkflowStage.INIT

    def test_nonfunctional_requirements_defined(self):
        """测试非功能需求已定义"""
        status = self.manager.get_status()

        assert "nonfunctional_requirements" in status
        assert "performance" in status["nonfunctional_requirements"]
        assert "security" in status["nonfunctional_requirements"]
        assert "test_coverage" in status["nonfunctional_requirements"]

    def test_submit_requirement(self):
        """测试提交需求"""
        self.manager.submit_requirement("测试需求")

        assert self.manager.context.user_requirement == "测试需求"
        assert self.manager.get_current_stage() == WorkflowStage.PM_PENDING

    def test_process_pm_stage_with_clarification(self):
        """测试PM阶段处理（需要澄清）"""
        self.manager.submit_requirement("短需求")
        result = self.manager.process_pm_stage()

        assert result["need_clarification"] is True
        assert len(result["questions"]) > 0
        assert self.manager.get_current_stage() == WorkflowStage.PM_REVIEW

    def test_process_pm_stage_without_clarification(self):
        """测试PM阶段处理（不需要澄清）"""
        self.manager.submit_requirement(
            "开发一个完整的用户管理系统，包括用户注册、登录、权限管理等功能，"
            "需要支持高并发访问，保证数据安全"
        )
        result = self.manager.process_pm_stage()

        assert result["need_clarification"] is False
        assert "mvp_plan" in result
        assert "validation" in result

    def test_provide_clarification(self):
        """测试提供澄清"""
        self.manager.submit_requirement("短需求")
        self.manager.process_pm_stage()

        result = self.manager.provide_clarification(["支持用户登录", "需要权限管理"])

        assert "mvp_plan" in result

    def test_approve_mvp(self):
        """测试确认MVP方案"""
        self.manager.submit_requirement("完整的需求描述，包含详细的功能说明")
        self.manager.process_pm_stage()

        result = self.manager.approve_mvp()

        assert result["message"] == "MVP 方案已确认，流转至架构师"
        assert self.manager.get_current_stage() == WorkflowStage.ARCHITECT_PENDING

    def test_process_architect_stage(self):
        """测试架构师阶段处理"""
        # 完成PM阶段
        self.manager.submit_requirement("完整的需求描述，包含详细的功能说明")
        self.manager.process_pm_stage()
        self.manager.approve_mvp()

        # 处理架构师阶段
        result = self.manager.process_architect_stage()

        assert "tech_plan" in result
        assert "validation" in result
        assert self.manager.get_current_stage() == WorkflowStage.ARCHITECT_REVIEW

    def test_process_dev_stage_enforces_unit_tests(self):
        """测试开发阶段强制单元测试"""
        # 准备完整工作流
        self.manager.submit_requirement("完整的需求描述，包含详细的功能说明")
        self.manager.process_pm_stage()
        self.manager.approve_mvp()
        self.manager.process_architect_stage()
        self.manager.approve_tech_plan()

        # 处理开发阶段
        result = self.manager.process_dev_stage()

        # 验证非功能需求校验
        assert "nonfunctional_validation" in result
        assert "module_package" in result

        # 验证单元测试存在
        module_package = result["module_package"]
        assert module_package.has_unit_tests() is True

    def test_nonfunctional_validation_performance(self):
        """测试性能非功能需求校验"""
        self.manager.submit_requirement("完整的需求描述，包含详细的功能说明")
        self.manager.process_pm_stage()
        self.manager.approve_mvp()
        self.manager.process_architect_stage()
        self.manager.approve_tech_plan()

        result = self.manager.process_dev_stage()

        nonfunc_val = result["nonfunctional_validation"]
        assert "checks" in nonfunc_val
        assert "performance" in nonfunc_val["checks"]
        assert nonfunc_val["checks"]["performance"]["passed"] is True

    def test_nonfunctional_validation_security(self):
        """测试安全非功能需求校验"""
        self.manager.submit_requirement("完整的需求描述，包含详细的功能说明")
        self.manager.process_pm_stage()
        self.manager.approve_mvp()
        self.manager.process_architect_stage()
        self.manager.approve_tech_plan()

        result = self.manager.process_dev_stage()

        nonfunc_val = result["nonfunctional_validation"]
        assert "security" in nonfunc_val["checks"]
        assert nonfunc_val["checks"]["security"]["passed"] is True

    def test_nonfunctional_validation_test_coverage(self):
        """测试覆盖率非功能需求校验"""
        self.manager.submit_requirement("完整的需求描述，包含详细的功能说明")
        self.manager.process_pm_stage()
        self.manager.approve_mvp()
        self.manager.process_architect_stage()
        self.manager.approve_tech_plan()

        result = self.manager.process_dev_stage()

        nonfunc_val = result["nonfunctional_validation"]
        assert "test_coverage" in nonfunc_val["checks"]
        assert nonfunc_val["checks"]["test_coverage"]["passed"] is True
        assert nonfunc_val["checks"]["test_coverage"]["has_unit_tests"] is True


class TestWorkflowStages:
    """测试工作流阶段转换"""

    def setup_method(self):
        self.manager = WorkflowManager()

    def test_stage_transitions(self):
        """测试完整工作流阶段转换"""
        # INIT -> PM_PENDING
        self.manager.submit_requirement("完整的需求描述，包含详细的功能说明")
        assert self.manager.get_current_stage() == WorkflowStage.PM_PENDING

        # PM_PENDING -> PM_REVIEW
        self.manager.process_pm_stage()
        assert self.manager.get_current_stage() == WorkflowStage.PM_REVIEW

        # PM_REVIEW -> ARCHITECT_PENDING
        self.manager.approve_mvp()
        assert self.manager.get_current_stage() == WorkflowStage.ARCHITECT_PENDING

        # ARCHITECT_PENDING -> ARCHITECT_REVIEW
        self.manager.process_architect_stage()
        assert self.manager.get_current_stage() == WorkflowStage.ARCHITECT_REVIEW

        # ARCHITECT_REVIEW -> DEV_PENDING
        self.manager.approve_tech_plan()
        assert self.manager.get_current_stage() == WorkflowStage.DEV_PENDING

        # DEV_PENDING -> TESTING
        self.manager.process_dev_stage()
        assert self.manager.get_current_stage() == WorkflowStage.TESTING

        # TESTING -> COMPLETED
        self.manager.complete_project()
        assert self.manager.get_current_stage() == WorkflowStage.COMPLETED


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
