#!/usr/bin/env python3
"""启动 AI 全栈开发团队"""

from ai_team.main_agent import MainAgent


def main():
    main_agent = MainAgent()
    main_agent.start()

    print("\n💡 提示:")
    print("  - PM 团队已待命，随时准备接收产品需求")
    print("  - 请输入具体的产品需求以开始工作流")
    print("  - 工作流遵循: 需求 → MVP方案 → 技术方案 → 开发 → 测试 → 交付")
    print("\n使用方法:")
    print("  main_agent.receive_requirement('你的产品需求')")
    print("  main_agent.approve_and_continue()  # 确认方案并继续")
    print("  main_agent.show_team_status()      # 查看团队状态")

    return main_agent


if __name__ == "__main__":
    agent = main()
