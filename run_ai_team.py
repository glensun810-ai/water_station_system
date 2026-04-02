#!/usr/bin/env python3
"""运行 AI 团队处理会议室管理模块优化需求"""

from start_ai_team import main

# 阶段一：核心体验优化（P0级别）
phase1_requirement = """
# 会议室管理模块优化需求 - 阶段一（P0级别）

## 项目背景
会议室管理系统当前存在严重的用户体验和管理效率问题，需要进行核心功能优化。

## 核心需求

### 1. 用户侧优化

#### 1.1 灵活时间段选择（P0）
**现状问题**：
- 只有3个固定时间段选项：上午09:00-12:00、下午14:00-18:00、晚上19:00-21:00
- 用户无法自定义时间段
- 无法跨时段预约
- 无法进行短时预约（如30分钟）

**需求描述**：
- 提供时间选择器，允许用户自定义开始时间和结束时间
- 最小预约时长：30分钟
- 最大预约时长：8小时
- 可选时段：07:00-22:00
- 实时校验时间段是否可用（避免冲突）
- 保留快捷时段选项（上午/下午/晚上）供用户快速选择

**验证逻辑**：
- 开始时间必须早于结束时间
- 时长范围：30分钟 ≤ 时长 ≤ 8小时
- 不能跨越已预约时段
- 必须在可预约时间范围内（07:00-22:00）

#### 1.2 "我的预约"功能（P0）
**现状问题**：
- 用户无法查看自己的预约历史
- 无法修改已提交的预约
- 无法主动取消预约
- 预约成功后无凭证

**需求描述**：
- 新增"我的预约"页面，展示用户所有预约记录
- 支持按状态筛选（待确认/已确认/已完成/已取消）
- 支持按日期范围筛选
- 每条预约记录显示：
  - 预约编号
  - 会议室名称
  - 预约日期
  - 时间段
  - 会议主题
  - 参会人数
  - 费用
  - 状态
- 操作功能：
  - 查看详情（独立详情页）
  - 修改预约（时间/人数/主题）
  - 取消预约（需填写原因）
- 修改/取消规则：
  - 只能修改/取消"待确认"或"已确认"状态的预约
  - 会议开始前2小时内不可取消

**数据结构**：
```javascript
{
  "id": 1,
  "booking_no": "MT20260401001",
  "room_name": "小型会议室A",
  "booking_date": "2026-04-02",
  "start_time": "09:00",
  "end_time": "12:00",
  "status": "confirmed",
  "can_modify": true,
  "can_cancel": true,
  "cancel_deadline": "2026-04-01 18:00"
}
```

#### 1.3 预约详情页/凭证（P0）
**现状问题**：
- 预约成功后仅显示 alert 弹窗
- 信息无法复制
- 关闭后无法再次查看
- 无分享功能

**需求描述**：
- 预约成功后跳转到独立详情页
- 详情页包含：
  - 完整预约信息
  - 预约编号（可复制）
  - 二维码（扫码查看详情）
  - 分享链接
  - 操作按钮（修改/取消）
  - 打印功能
- 二维码功能：
  - 扫码跳转到详情页
  - 可保存到手机
  - 可打印
- 通知机制：
  - 预约创建成功通知
  - 预约确认通知
  - 预约取消通知
  - 会议前1小时提醒

### 2. 管理员侧优化

#### 2.1 权限登录验证（P0）
**现状问题**：
- 后台无登录验证
- 任何用户都可以访问 admin.html
- 无角色区分
- 无操作日志

**需求描述**：
- 实现管理员登录功能
- 角色体系：
  - 超级管理员：所有权限
  - 会议室管理员：预约管理、会议室管理
  - 财务人员：预约查看、财务报表
  - 普通员工：仅查看
- 登录验证：
  - 必须登录才能访问后台
  - JWT Token 验证
  - 自动登出（超时时间：2小时）
- 权限控制：
  - 功能级权限（菜单显示控制）
  - 操作级权限（按钮显示控制）
- 操作日志：
  - 记录所有管理员操作
  - 包含：操作人、操作时间、操作内容、操作结果

#### 2.2 真实统计数据（P0）
**现状问题**：
- 使用率是随机数模拟
- 周统计是比例估算
- 数据不准确
- 统计维度单一

**需求描述**：
- 时间维度统计：
  - 今日预约数/收入
  - 本周预约数/收入（周一至周日）
  - 本月预约数/收入
  - 自定义日期范围统计
- 会议室维度统计：
  - 各会议室预约数排名
  - 各会议室使用率（真实计算）
  - 各会议室收入排名
  - 热门时段分析
- 用户维度统计：
  - 内部用户使用统计
  - 外部用户使用统计
  - 高频用户排名
- 趋势分析：
  - 预约量趋势图（折线图）
  - 收入趋势图（折线图）
  - 使用率趋势图（折线图）
  - 同比/环比分析

**使用率计算公式**：
```python
usage_rate = (实际使用小时数 / 可用总小时数) * 100
# 示例：某会议室本月
# 可用时段：每天07:00-22:00（15小时）× 30天 = 450小时
# 实际预约：累计180小时
# 使用率 = 180 / 450 * 100 = 40%
```

## 技术要求

### 前端技术栈
- Vue.js 3（现有）
- 时间选择器组件
- 图表库（用于统计）

### 后端技术栈
- Python FastAPI（现有）
- SQLite 数据库（现有）
- JWT 认证
- 参数化 SQL 查询（避免注入）

### 数据库变更
需要新增/修改的字段：
- meeting_bookings 表：
  - 添加 start_time 字段（具体时间）
  - 添加 end_time 字段（具体时间）
  - 添加 can_modify 字段
  - 添加 can_cancel 字段
  - 添加 cancel_deadline 字段
  - 添加 created_at 字段
  - 添加 updated_at 字段
  - 添加 reviewer_id 字段（审核人）
  - 添加 reviewed_at 字段（审核时间）
  
- 新增表：
  - admin_users 表（管理员用户）
  - admin_roles 表（角色）
  - admin_operation_logs 表（操作日志）

## 验收标准
- 用户可以在2-3步内完成预约（原6-7步）
- 用户可自主查看、修改、取消预约
- 管理员必须登录才能访问后台
- 统计数据必须真实准确
- 所有新功能需包含单元测试，覆盖率≥80%

## 预期收益
- 预约完成率：60% → 85%（↑25%）
- 预约平均耗时：3-5分钟 → 1-2分钟（↓60%）
- 用户自主管理率：0% → 80%（↑80%）
- 管理员处理效率：↑67%
"""

if __name__ == "__main__":
    # 启动 AI 团队
    main_agent = main()

    # 提交需求
    print("\n\n正在提交阶段一需求...")
    result = main_agent.receive_requirement(phase1_requirement)

    # 显示详细结果
    print("\n\n=== 详细结果 ===")
    print(f"状态: {result.get('status', '未知')}")
    print(f"完整结果键: {result.keys()}")

    # 如果需要澄清
    if result.get("status") == "need_clarification":
        print("\n需要澄清的问题：")
        for i, question in enumerate(result.get("questions", []), 1):
            print(f"{i}. {question}")

    # 如果有错误
    elif "error" in result:
        print(f"\n错误: {result['error']}")
        if "validation_result" in result:
            print(f"验证结果: {result['validation_result']}")

    # 如果方案生成成功
    elif result.get("status") == "pending_approval":
        print("\n方案已生成，等待确认")
        if "mvp_plan" in result:
            print("\nMVP方案内容:")
            print(result["mvp_plan"].raw_content)

            # 自动确认并继续到技术方案阶段
            print("\n\n=== 自动确认 MVP 方案并继续 ===")
            tech_result = main_agent.approve_and_continue()

            # 显示技术方案结果
            print("\n\n=== 技术方案详情 ===")
            if "error" in tech_result:
                print(f"错误: {tech_result['error']}")
                if "validation_result" in tech_result:
                    print(f"验证结果: {tech_result['validation_result']}")
            elif "tech_plan" in tech_result:
                print("\n技术方案内容:")
                print(tech_result["tech_plan"].raw_content)

                # 自动确认技术方案并继续到开发阶段
                print("\n\n=== 自动确认技术方案并继续开发 ===")
                dev_result = main_agent.approve_and_continue()

                # 显示开发结果
                print("\n\n=== 开发完成详情 ===")
                if "error" in dev_result:
                    print(f"错误: {dev_result['error']}")
                    if "details" in dev_result:
                        print(f"详细信息: {dev_result['details']}")
                elif "module_package" in dev_result:
                    print(f"\n模块名称: {dev_result['module_package'].package_name}")
                    print("\n代码变更:")
                    for change in dev_result["module_package"].code_changes:
                        print(f"  - {change.file_path} ({change.change_type})")
                    print("\n质量检查:")
                    for check, passed in dev_result["quality_check"]["checks"].items():
                        print(f"  [{('✓' if passed else '✗')}] {check}")

    # 显示团队状态
    print("\n\n=== 团队状态 ===")
    main_agent.show_team_status()
