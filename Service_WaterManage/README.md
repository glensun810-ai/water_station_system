# 智能水站管理系统 (Water Management System)

一个简洁清爽的桶装水/瓶装水仓库领取管理系统，支持扫码登记、库存管理、价格管理、优惠方案（买十赠一）、统计分析、结算管理等功能。

## 系统特点

- 🎨 **清爽简洁** - Apple-like 设计风格，蓝白配色
- 📱 **移动端优先** - H5 页面适配手机扫码
- 🔧 **自动优惠** - 买 N 赠 M 自动计算
- 📊 **实时统计** - 部门用水统计、库存预警
- 💰 **结算管理** - 用户申请结算 → 管理员确认收款 → 完成结算
- 🔔 **提醒功能** - 支持提醒长期未结算用户

## 项目结构

```
Service_WaterManage/
├── backend/
│   ├── main.py          # FastAPI 后端服务
│   ├── seed.py          # 初始化演示数据脚本
│   ├── migrate.py       # 数据库迁移脚本
│   ├── test_system.py   # 系统测试脚本
│   └── requirements.txt # Python 依赖
├── frontend/
│   ├── index.html       # 用户端 H5 页面（扫码领水、个人记录、结算申请）
│   └── admin.html       # 管理后台页面（库存、结算申请、提醒）
└── README.md            # 项目说明
```

## 快速开始

### 1. 安装依赖

```bash
cd backend
pip install -r requirements.txt
```

### 2. 初始化数据库

```bash
python seed.py
```

### 3. 数据库迁移（如有更新）

```bash
python migrate.py
```

### 4. 启动后端服务

```bash
python main.py
```

服务将运行在 `http://localhost:8000`

### 5. 访问页面

- **用户端**: 用浏览器打开 `frontend/index.html`
- **管理端**: 用浏览器打开 `frontend/admin.html`

## 功能说明

### 用户端功能

1. **领水** - 选择水规格和数量，一键登记领取
   - ⚠️ 库存为 0 的产品自动隐藏，不显示
   - 显示优惠方案（买 N 赠 M）
2. **我的记录** - 查看个人领取历史，包含：
   - 已结算记录
   - 待结算记录
   - 已申请待确认记录
3. **结算管理** - 管理个人结算：
   - 待申请结算：显示未申请结算的记录，支持批量申请
   - 已申请待确认：显示已提交申请等待管理员确认的记录
   - 已结算历史：查看历史结算记录

### 管理端功能

1. **数据看板** - 总览系统状态：
   - 本月总领取量
   - 待结算总额
   - 已申请待确认金额
   - 库存预警

2. **结算申请** - 处理用户结算申请：
   - 查看所有待确认的结算申请
   - 单条或批量确认收款
   - 确认后自动完成结算

3. **交易记录** - 管理所有交易：
   - 按状态/部门筛选
   - 批量结算
   - 查看结算申请状态

4. **库存管理** - 管理水规格和库存：
   - 实时修改库存
   - 添加新产品
   - 编辑产品信息

5. **提醒结算** - 提醒长期未结算用户：
   - 按天数筛选（7/15/30 天）
   - 查看待结算金额和笔数
   - 单条或批量发送提醒

## API 接口

### 用户接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/user/{user_id}/status` | GET | 获取用户统计（含 applied_amount 和 to_apply_amount） |
| `/api/transactions?user_id={id}` | GET | 获取用户交易记录（含 settlement_applied 字段） |
| `/api/user/settlement-apply` | POST | 提交结算申请 |

### 管理接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/admin/settlement-applications` | GET | 获取待确认结算申请列表 |
| `/api/admin/confirm-settlement` | POST | 确认收款，完成结算 |
| `/api/admin/remind-unsettled?days=30` | GET | 获取超过指定天数未结算的用户 |
| `/api/admin/settle` | POST | 批量结算 |
| `/api/admin/settle-by-department` | POST | 按部门结算 |

## 结算流程

```
用户领取 → 待结算 → 用户申请结算 → 已申请待确认 → 管理员确认收款 → 已结算
```

1. 用户领取水后，记录状态为 `unsettled`（待结算）
2. 用户在"结算"页面勾选记录，提交结算申请
3. 申请后，记录标记为 `settlement_applied=1`（已申请待确认）
4. 管理员在"结算申请"页面看到申请，点击"确认收款"
5. 确认后，记录状态变为 `settled`（已结算）

## 优惠算法

系统支持"买 N 赠 M"优惠方案：

- 桶装水：买 10 赠 1（每第 11 桶免费）
- 瓶装水：买 20 赠 2（每第 21-22 瓶免费）
- 中桶水：买 15 赠 1（每第 16 桶免费）

优惠按用户维度累计，仅针对"待结算"状态的有效记录。

## 技术栈

- **后端**: FastAPI + SQLAlchemy + SQLite
- **前端**: Vue 3 + TailwindCSS (CDN 方式，无需构建)
- **API**: RESTful JSON

## 测试

```bash
cd backend
python test_system.py
```
