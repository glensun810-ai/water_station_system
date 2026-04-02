# 技术方案 - 阶段一：核心体验优化（P0）

## 模块划分图

```
会议室管理模块优化架构
│
├── 新增模块（独立目录）
│   ├── Service_MeetingRoom/modules/flexible_booking/      # 灵活预约模块
│   │   ├── api_flexible_booking.py                        # 时间段验证API
│   │   ├── time_validator.py                              # 时间冲突检测逻辑
│   │   └── templates/booking_time_picker.html              # 时间选择器组件
│   │
│   ├── Service_MeetingRoom/modules/my_bookings/            # 我的预约模块
│   │   ├── api_my_bookings.py                              # 预约管理API
│   │   ├── templates/my_bookings.html                      # 预约列表页
│   │   └── templates/booking_detail.html                   # 详情页
│   │
│   ├── Service_MeetingRoom/modules/admin_auth/             # 管理员权限模块
│   │   ├── api_admin_auth.py                               # 登录验证API
│   │   ├── jwt_handler.py                                  # JWT生成/验证
│   │   ├── models/admin_user.py                            # 管理员数据模型
│   │   └── models/admin_role.py                            # 角色权限模型
│   │   └── models/admin_operation_log.py                   # 操作日志模型
│   │
│   └── Service_MeetingRoom/modules/stats/                  # 统计模块
│   │   ├── api_stats.py                                    # 统计数据API
│   │   ├── usage_calculator.py                             # 使用率计算逻辑
│   │   └── templates/stats_dashboard.html                  # 统计仪表盘
│   │
│   └── tests/                                              # 单元测试目录
│   │   ├── test_flexible_booking.py
│   │   ├── test_my_bookings.py
│   │   ├── test_admin_auth.py
│   │   └── test_stats.py
│
└── 历史代码改动（需输出改动方案）
    ├── Service_MeetingRoom/frontend/index.html              # 添加时间选择器集成
    ├── Service_WaterManage/backend/api_meeting.py           # 添加新API路由
    ├── Service_MeetingRoom/backend/meeting.db               # 数据库迁移脚本
```

## 接口定义

### RESTful API Version 1.0

| 接口路径 | 方法 | 功能 | 权限 |
|---------|------|------|------|
| `/api/meeting/bookings/check-time` | POST | 检查时间段可用性 | 公开 |
| `/api/meeting/bookings/flexible` | POST | 创建灵活时间预约 | 公开 |
| `/api/meeting/my-bookings` | GET | 获取我的预约列表 | 用户 |
| `/api/meeting/my-bookings/{id}` | GET | 获取预约详情 | 用户 |
| `/api/meeting/my-bookings/{id}` | PUT | 修改预约 | 用户 |
| `/api/meeting/my-bookings/{id}` | DELETE | 取消预约 | 用户 |
| `/api/meeting/bookings/{id}/qrcode` | GET | 获取预约二维码 | 用户 |
| `/api/admin/login` | POST | 管理员登录 | 公开 |
| `/api/admin/stats` | GET | 获取统计数据 | 管理员 |
| `/api/admin/logs` | GET | 获取操作日志 | 超管 |

### 数据模型

**meeting_bookings表扩展字段**：
```sql
ALTER TABLE meeting_bookings ADD COLUMN start_time VARCHAR(10);
ALTER TABLE meeting_bookings ADD COLUMN end_time VARCHAR(10);
ALTER TABLE meeting_bookings ADD COLUMN can_modify BOOLEAN DEFAULT 1;
ALTER TABLE meeting_bookings ADD COLUMN can_cancel BOOLEAN DEFAULT 1;
ALTER TABLE meeting_bookings ADD COLUMN cancel_deadline VARCHAR(20);
ALTER TABLE meeting_bookings ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE meeting_bookings ADD COLUMN updated_at TIMESTAMP;
ALTER TABLE meeting_bookings ADD COLUMN reviewer_id INTEGER;
ALTER TABLE meeting_bookings ADD COLUMN reviewed_at TIMESTAMP;
```

**新增表**：
```sql
CREATE TABLE admin_users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role_id INTEGER,
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE admin_roles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    role_name VARCHAR(50) UNIQUE NOT NULL,
    permissions TEXT,  -- JSON格式权限列表
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE admin_operation_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    operation_type VARCHAR(50),
    operation_content TEXT,
    operation_result VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## 技术栈选型

| 技术 | 版本 | 作用 | 集成方式 |
|-----|------|------|---------|
| Vue.js 3 | 3.x | 前端框架 | 现有 |
| FastAPI | 0.68+ | 后端API框架 | 现有 |
| SQLite | 3.x | 数据库 | 现有 |
| python-jose | 3.3.0 | JWT认证 | pip安装 |
| qrcode | 7.3 | 二维码生成 | pip安装 |
| pytest | 7.0+ | 单元测试 | pip安装 |
| ECharts | 5.x | 统计图表 | CDN引入 |

## 开发排期

| 阶段 | 任务 | 工时 | 负责人 |
|-----|------|------|--------|
| 第1周 | 灵活预约模块开发 | 3天 | 开发1 |
| 第1周 | 我的预约模块开发 | 2天 | 开发2 |
| 第1周 | 数据库迁移脚本 | 1天 | 开发1 |
| 第1周 | 单元测试编写（覆盖率80%） | 1天 | 测试 |
| 第2周 | 管理员权限模块开发 | 3天 | 开发1 |
| 第2周 | 统计模块开发 | 2天 | 开发2 |
| 第2周 | 前端集成与优化 | 1天 | 开发2 |
| 第2周 | 质量门禁检查 | 1天 | 测试 |

## 质量门禁标准

| 检查项 | 标准 | 工具 |
|--------|------|------|
| 测试覆盖率 | ≥80% | pytest-cov |
| 静态分析 | 无高危漏洞 | pylint, bandit |
| 安全检查 | SQL参数化, XSS防护 | bandit |
| 性能测试 | API响应<200ms | pytest-benchmark |

---
*所有模块必须包含单元测试，测试覆盖率≥80%*