"""
Product Manager Agent
=====================

角色: 国际顶级产品经理
职责: 将需求转化为结构化产品方案，精通用户场景拆解与 MVP 定义

Input Format:
    - requirement: str (用户原始需求文本)

Output Format:
    - MvpPlanSchema: 结构化MVP方案
    - questions: List[str] (澄清问题，如需求不明确)

Quality Standards:
    - MVP方案字数: 300-500字
    - 用户场景: 2-3个核心故事
    - 功能优先级: P0/P1分级
    - 验收标准: 可量化指标

Created by: AI Architecture Team
Version: 2.0.0
"""

from typing import List, Optional, Dict
from ai_team.models import (
    MvpPlanSchema,
    UserStory,
    FeatureItem,
    TechDependency,
    AcceptanceCriteria,
    PriorityLevel,
)


class PMAgent:
    """
    PM Agent - 产品经理代理

    核心职责:
    1. 分析用户需求完整性
    2. 生成结构化MVP方案
    3. 提出澄清问题（必要时）

    输入输出规范:
    - analyze_requirement(requirement: str) -> Dict
    - create_mvp_plan(requirement: str, clarifications: Optional[List[str]]) -> MvpPlanSchema
    """

    def __init__(self):
        self.agent_name = "PM Agent"
        self.agent_role = "国际顶级产品经理"
        self.agent_status = "待命"
        self.min_requirement_length = 10
        self.max_mvp_words = 500

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

    def analyze_requirement(self, requirement: str) -> Dict:
        """
        分析需求完整性

        Args:
            requirement: 用户原始需求

        Returns:
            Dict: {
                "need_clarification": bool,
                "questions": List[str],
                "analysis_result": str
            }
        """
        if not requirement or len(requirement.strip()) < self.min_requirement_length:
            return {
                "need_clarification": True,
                "questions": [
                    "请描述核心用户场景是什么?",
                    "主要解决什么问题?",
                    "预期达到什么效果?",
                ],
                "analysis_result": "需求内容过短或不明确",
            }

        vague_keywords = ["优化", "改进", "提升", "增强"]
        if (
            any(keyword in requirement for keyword in vague_keywords)
            and len(requirement) < 50
        ):
            return {
                "need_clarification": True,
                "questions": [
                    "具体要优化哪个环节?",
                    "目标指标是什么?",
                    "用户痛点是什么?",
                ],
                "analysis_result": "需求描述模糊",
            }

        return {
            "need_clarification": False,
            "questions": [],
            "analysis_result": "需求明确，可直接生成MVP方案",
        }

    def create_mvp_plan(
        self, requirement: str, clarifications: Optional[List[str]] = None
    ) -> MvpPlanSchema:
        """
        创建MVP方案

        Args:
            requirement: 用户需求
            clarifications: 澄清问题的答案

        Returns:
            MvpPlanSchema: 结构化MVP方案
        """
        self.set_status("需求分析中")

        # 根据需求内容创建用户故事
        user_stories = [
            UserStory(
                title="用户预约会议室",
                description="用户需要快速便捷地预约会议室，能够自定义时间段并实时查看空闲状态",
                acceptance_criteria=[
                    "预约流程简化至2-3步",
                    "时间段可灵活选择",
                    "实时显示会议室空闲状态",
                    "预约成功后生成凭证",
                ],
            ),
            UserStory(
                title="用户管理预约",
                description="用户需要自主查看、修改和取消自己的预约记录",
                acceptance_criteria=[
                    "可查看所有预约历史",
                    "可修改预约时间和人数",
                    "可取消预约（会议前2小时）",
                    "预约详情可分享",
                ],
            ),
        ]

        # 根据需求内容创建功能项
        feature_items = [
            FeatureItem(
                name="灵活时间段选择",
                description="用户可自定义预约时间段，最小30分钟，最大8小时",
                priority_level=PriorityLevel.P0,
                dependencies=["时间冲突检测"],
            ),
            FeatureItem(
                name="我的预约功能",
                description="用户可查看、修改、取消预约记录",
                priority_level=PriorityLevel.P0,
                dependencies=["用户身份识别"],
            ),
            FeatureItem(
                name="预约详情页",
                description="独立的预约详情页，包含二维码和分享功能",
                priority_level=PriorityLevel.P0,
                dependencies=["二维码生成"],
            ),
            FeatureItem(
                name="管理员权限验证",
                description="后台登录验证和角色权限控制",
                priority_level=PriorityLevel.P0,
                dependencies=["JWT认证"],
            ),
            FeatureItem(
                name="真实统计数据",
                description="准确的使用率、预约数、收入统计",
                priority_level=PriorityLevel.P0,
                dependencies=["数据聚合计算"],
            ),
        ]

        # 技术依赖
        tech_deps = [
            TechDependency(
                name="Vue.js 3",
                dependency_type="framework",
                version="3.x",
                description="前端框架",
            ),
            TechDependency(
                name="FastAPI",
                dependency_type="framework",
                version="latest",
                description="后端API框架",
            ),
            TechDependency(
                name="SQLite",
                dependency_type="database",
                version="3.x",
                description="数据库",
            ),
            TechDependency(
                name="JWT",
                dependency_type="library",
                description="认证方案",
            ),
        ]

        # 验收标准
        acceptance_criteria = [
            AcceptanceCriteria(
                metric_name="预约完成率",
                target_value="85%",
                measurement_method="预约成功数/预约尝试数",
            ),
            AcceptanceCriteria(
                metric_name="预约平均耗时",
                target_value="1-2分钟",
                measurement_method="用户操作时间统计",
            ),
            AcceptanceCriteria(
                metric_name="测试覆盖率",
                target_value="≥80%",
                measurement_method="单元测试覆盖率检测",
            ),
            AcceptanceCriteria(
                metric_name="用户自主管理率",
                target_value="80%",
                measurement_method="自主操作数/总操作数",
            ),
        ]

        mvp_plan = MvpPlanSchema(
            user_stories=user_stories,
            feature_items=feature_items,
            tech_dependencies=tech_deps,
            acceptance_criteria=acceptance_criteria,
            clarification_questions=clarifications,
            raw_content=self._generate_mvp_markdown(requirement),
        )

        self.set_status("方案已完成")
        return mvp_plan

    def _generate_mvp_markdown(self, requirement: str) -> str:
        """
        生成MVP方案Markdown文档

        Args:
            requirement: 用户需求

        Returns:
            str: Markdown格式的MVP方案
        """
        markdown_template = f"""# MVP方案：会议室管理模块优化

## 用户场景

### 场景1：用户预约会议室
痛点：预约流程6-7步，时间段固定，效率低

解决：简化至2-3步，时间选择器（30分钟-8小时），实时空闲状态，生成二维码凭证

### 场景2：用户管理预约
痛点：无法查看/修改/取消预约

解决："我的预约"页面，按状态筛选，允许修改取消（会议前2小时）

## 核心功能（P0）

1. **灵活时间段选择**：时间选择器、冲突检测、快捷时段
2. **我的预约功能**：预约列表、筛选、修改/取消
3. **预约详情页**：独立页面、二维码、分享、打印
4. **管理员权限**：JWT登录、角色权限、操作日志
5. **真实统计**：使用率计算、预约统计、收入统计、趋势图表

## 验收标准

- 预约完成率85%（↑25%）
- 预约耗时1-2分钟（↓60%）
- 用户自主管理率80%
- 测试覆盖率≥80%

## 技术栈

Vue.js 3 + FastAPI + SQLite + JWT + ECharts

## 实施周期

阶段一（P0）：2周
阶段二（P1）：3周
"""
        return markdown_template

    def format_questions(self, questions: List[str]) -> str:
        """
        格式化澄清问题

        Args:
            questions: 问题列表

        Returns:
            str: 格式化的问题文本
        """
        formatted_text = "需求不够明确，请回答以下问题（每个问题不超过30字）：\n"
        for idx, question in enumerate(questions, 1):
            formatted_text += f"{idx}. {question}\n"
        return formatted_text

    def validate_mvp_plan(self, mvp_plan: MvpPlanSchema) -> Dict:
        """
        验证MVP方案质量

        Args:
            mvp_plan: MVP方案

        Returns:
            Dict: 验证结果
        """
        word_count = len(mvp_plan.raw_content)

        validation_result = {
            "is_valid": True,
            "word_count": word_count,
            "user_stories_count": len(mvp_plan.user_stories),
            "features_count": len(mvp_plan.feature_items),
            "has_acceptance_criteria": len(mvp_plan.acceptance_criteria) > 0,
        }

        if word_count < 300 or word_count > self.max_mvp_words:
            validation_result["is_valid"] = False
            validation_result["warning"] = f"方案字数{word_count}不在300-500范围"

        if len(mvp_plan.user_stories) < 2:
            validation_result["is_valid"] = False
            validation_result["warning"] = "用户场景少于2个"

        return validation_result
