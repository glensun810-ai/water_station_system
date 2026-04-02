"""
Unit Tests for PM Agent
=======================

测试PM代理的功能和输入输出格式
"""

import pytest
from ai_team.pm_agent import PMAgent
from ai_team.models import MvpPlanSchema, PriorityLevel


class TestPMAgent:
    """测试PM代理"""

    def setup_method(self):
        """测试前初始化"""
        self.agent = PMAgent()

    def test_agent_attributes(self):
        """测试代理属性命名"""
        assert hasattr(self.agent, "agent_name")
        assert hasattr(self.agent, "agent_role")
        assert hasattr(self.agent, "agent_status")

    def test_analyze_requirement_too_short(self):
        """测试需求过短的分析"""
        result = self.agent.analyze_requirement("短需求")

        assert result["need_clarification"] is True
        assert len(result["questions"]) > 0
        assert "analysis_result" in result

    def test_analyze_requirement_vague(self):
        """测试模糊需求分析"""
        result = self.agent.analyze_requirement("优化系统性能")

        assert result["need_clarification"] is True
        assert "具体要优化哪个环节?" in result["questions"]

    def test_analyze_requirement_clear(self):
        """测试明确需求分析"""
        result = self.agent.analyze_requirement(
            "开发一个用户登录系统，支持用户名密码登录和手机验证码登录，"
            "需要考虑安全性，登录成功后跳转到首页"
        )

        assert result["need_clarification"] is False
        assert len(result["questions"]) == 0

    def test_create_mvp_plan(self):
        """测试创建MVP方案"""
        mvp = self.agent.create_mvp_plan(
            "开发用户管理系统", clarifications=["支持多种登录方式"]
        )

        assert isinstance(mvp, MvpPlanSchema)
        assert len(mvp.user_stories) > 0
        assert len(mvp.feature_items) > 0
        assert mvp.clarification_questions is not None

    def test_validate_mvp_plan(self):
        """测试MVP方案验证"""
        mvp = self.agent.create_mvp_plan("测试需求")
        validation = self.agent.validate_mvp_plan(mvp)

        assert "is_valid" in validation
        assert "word_count" in validation
        assert "user_stories_count" in validation

    def test_format_questions(self):
        """测试问题格式化"""
        formatted = self.agent.format_questions(["问题1", "问题2"])

        assert "1. 问题1" in formatted
        assert "2. 问题2" in formatted
        assert "不超过30字" in formatted

    def test_status_management(self):
        """测试状态管理"""
        assert self.agent.get_status() == "待命"

        self.agent.set_status("工作中")
        assert self.agent.get_status() == "工作中"

    def test_output_format(self):
        """测试输出格式"""
        mvp = self.agent.create_mvp_plan("测试需求")

        # 验证输出包含必要字段
        assert hasattr(mvp, "user_stories")
        assert hasattr(mvp, "feature_items")
        assert hasattr(mvp, "tech_dependencies")
        assert hasattr(mvp, "acceptance_criteria")
        assert hasattr(mvp, "raw_content")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
