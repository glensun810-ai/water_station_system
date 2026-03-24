需求背景：
我希望做一个简单的Html5页面，希望实现的功能，是针对一间存放桶装水和瓶装水的仓库，让不同办公室的同事在进去领取用水的时候，扫码登记一下领的规格和水量，后台实现自动记录领取时间、领取人、以及领取的规格及数量。后台支持针对库存的管理、价格管理、优惠方案管理（比如买十赠一等）方案、领取情况的统计分析、预定、结算、未结算等管理功能。不同办公室的同事（用户）可以查看自己整体的领取情况，预定支付及剩余情况，结算和未结算的情况等等。请你作为国际顶级系统产品专家，帮我设计一个完整的系统，以AI Coding可以理解的描述，整理为一份详细的、完整的系统实现方案。整体风格需要足够清爽、简洁，用户使用或者后台管理足够清晰、便捷。请规划输出。


系统框架：
你好！这是一个非常典型的**微型库存与结算管理系统（Micro-Inventory & Settlement System）**。为了确保系统既能快速开发（AI Coding 友好），又能应对未来的扩展（如买十赠一等复杂逻辑），我们需要一套清晰的数据结构和模块化的前后端设计。

以下为您规划的系统实现方案，采用 **"轻量化前端 + 统一服务层 + 结构化数据库"** 的架构设计。

---

## 1. 系统核心架构
* **前端 (H5/Web):** 响应式设计，适配手机扫码与 PC 后台管理。
* **后端 (Backend):** 建议使用 Python (FastAPI/Flask) 或 Node.js，便于 AI 生成逻辑。
* **数据库 (Database):** 关系型数据库（SQLite 或 PostgreSQL），确保优惠方案与结算逻辑的准确性。

---

## 2. 数据库模型 (ERD) - AI 开发核心
这是系统的灵魂，AI 编写代码时需严格遵守此结构：

| 表名 | 关键字段 | 说明 |
| :--- | :--- | :--- |
| **Users** | `id, name, department, phone, balance, role` | 用户角色区分：Admin (管理), User (同事) |
| **Products** | `id, name, specification, unit, price, stock` | 规格如：18L 桶装、500ml 瓶装 |
| **Records** | `id, user_id, product_id, quantity, type, timestamp, status` | type: 领取/预定；status: 已支付/待结算 |
| **Promotions** | `id, product_id, trigger_qty, gift_qty, description` | 优惠规则，如：10 触发 1 赠送 |
| **Orders** | `id, user_id, total_amount, settlement_status, created_at` | 结算汇总单 |

---

## 3. 功能模块详细定义

### 3.1 移动端：扫码登记界面 (Scan & Log)
* **交互逻辑：** 同事扫描仓库二维码 -> 自动识别身份 -> 选择水规格 -> 输入数量 -> 点击确认。
* **功能点：**
    * **快速选取：** 提供大按钮卡片选择（如“大桶水 18L”、“小瓶水 500ml”）。
    * **实时反馈：** 登记成功后弹出“当前已累计领取 X 桶，剩余赠送额度 Y”。
    * **个人中心：** 查看“我的账单”，区分“已结算”和“本月待结”。

### 3.2 管理端：库存与经营看板 (Admin Dashboard)
* **库存预警：** 当库存低于阈值时，首页显著标红。
* **优惠引擎：** * **买 N 赠 M：** 系统自动计算逻辑：`if (total_received % (N+M)) >= N { next_is_free = true }`。
* **财务结算：**
    * 支持一键导出“部门月度用水统计表”。
    * 手动/自动核销：点击“结算”将状态由 `unsettled` 改为 `settled`。

---

## 4. UI/UX 设计规范 (清爽简约风格)
* **视觉风格：** 采用 **"Apple-like"** 或 **"Ant Design Mobile"** 风格。
* **色彩：** 主色调使用 **#007AFF (水蓝色)**，背景使用浅灰 **#F5F5F7**，文字使用深炭黑。
* **布局：** * **卡片化：** 所有数据项封装在圆角卡片（`border-radius: 12px`）中。
    * **无感输入：** 默认数量为 1，减少用户点击次数。

---

## 5. AI Coding 实现指令 (Prompt 示例)

你可以将以下这段话直接发给 AI 助手（如 Cursor 或 Claude）来生成代码：

> "请根据以下逻辑编写一个 H5 饮用水管理系统：
> 1. **前端：** 使用 Vue3 或 React + TailwindCSS。包含两个视图：`/scan` (用户领水) 和 `/admin` (管理后台)。
> 2. **后端：** 使用 Python FastAPI。实现以下 API 接口：
>    - `POST /record`: 登记领取，需自动计算是否满足 `Promotions` 表中的赠送条件。
>    - `GET /user/status`: 返回用户累计领取量、剩余预定额度及结算状态。
>    - `PUT /admin/settle`: 修改指定记录的结算状态。
> 3. **核心逻辑：** 领取时，若满足‘买十赠一’，该笔记录价格记为 0，并备注‘赠送’。
> 4. **风格：** 界面要求极其简约，使用大量留白和清晰的投影效果。"

---

## 6. 进阶建议：自动化与通知
为了提升“便捷性”，我建议加入以下两个小功能：
* **微信/飞书通知：** 当同事领取后，后台自动推送到管理者的即时通讯软件。
* **库存阈值提醒：** 当桶装水少于 10 桶时，自动给采购人员发消息。

**您希望我针对其中哪一个模块（例如具体的优惠算法，或者是前端界面的 Mockup 图）进行更深入的细节设计吗？**


针对您的需求，作为系统架构师与产品经理，我将该“水资源管理系统（WaterMS）”拆解为**三个核心阶段**。

这种分步实施法能够确保系统从“核心记账”到“复杂逻辑（优惠/结算）”平稳过度，且每一阶段的描述都遵循 **AI Coding (如 Cursor/Claude/GPT-4)** 的指令逻辑。

---

## 第一阶段：MVP 核心链路（扫码、登记、基础库存）
**目标：** 实现最基础的“扫码 -> 选水 -> 记录”流程，替代纸笔。

### 1. 数据库定义 (Schema) - 供 AI 生成 Migration
```sql
-- 用户表：同事与管理员
Table users {
  id integer [primary key]
  username varchar -- 姓名
  dept varchar     -- 部门
  role varchar     -- 'admin' 或 'staff'
}

-- 规格表：桶装水、瓶装水
Table products {
  id integer [primary key]
  name varchar     -- 如：18L桶装水
  price decimal    -- 单价
  stock integer    -- 当前库存
}

-- 领取流水：记录每一次动作
Table transactions {
  id integer [primary key]
  user_id integer
  product_id integer
  quantity integer
  type varchar     -- 'pickup' (领取), 'reserve' (预定)
  status varchar   -- 'unsettled' (未结算), 'settled' (已结算)
  created_at timestamp
}
```

### 2. 核心 API 指令 (Backend Prompt)
> "请基于 FastAPI 和 SQLAlchemy 编写后端：实现 `POST /transactions` 接口。逻辑：用户扫码提交 user_id, product_id, quantity。提交时需同步减少 `products` 表中的 `stock` 数量。返回当前用户的历史领取总额。"

### 3. 前端交互指令 (Frontend Prompt)
> "使用 Vue3 + TailwindCSS 编写一个 H5 页面。页面中心是一个大卡片，包含：1. 顶部用户姓名显示；2. 中间商品选择（用大的图标按钮展示 18L/500ml）；3. 简单的数量加减组件；4. 底部的‘确认领取’蓝色大按钮。整体风格参考 iOS 17 设置界面，纯白背景，圆角 16px。"

---

## 第二阶段：财务逻辑增强（优惠方案、结算管理）
**目标：** 处理您提到的“买十赠一”等促销逻辑及账务对账。

### 1. 优惠引擎逻辑 (Promotion Engine)
我们需要引入一个**策略模式**的计算逻辑。
* **AI 逻辑描述：** > "在 `transactions` 写入前，检查该用户的历史领取记录。如果 `product_id` 为 1（大桶水），统计该用户 status='unsettled' 且 price > 0 的记录总数。若总数每满 10 桶，则当前这第 11 桶的实付金额 `amount` 自动设为 0，并在 `note` 字段标记为‘买十赠一优惠’。"

### 2. 管理后台功能模块
* **库存管理：** 增删改规格，手动补货。
* **结算看板：** * **按部门聚合：** `SELECT dept, SUM(amount) FROM transactions WHERE status='unsettled' GROUP BY dept`。
    * **一键清账：** 后台管理员勾选某个办公室的所有记录，点击“已结算”，批量更新 `status='settled'`。

---

## 第三阶段：用户自助与预定（闭环管理）
**目标：** 让同事能看自己的账单，并实现“先付后取”或“预定”功能。

### 1. 用户自助端功能
* **我的账单：** 区分显示“本月已领”、“累计赠送”、“待结算金额”。
* **预定功能：** * 用户在办公室发起 `type='reserve'` 的请求。
    * 管理员端收到 WebSocket 弹窗（或简单轮询），准备好水后，点击“已出库”，状态转为 `pickup`。

### 2. 部署与环境建议 (Ops)
* **前端环境：** 建议使用 Vite 部署，适配各种手机浏览器。
* **身份识别：** 初始版本可使用 URL 参数（如 `?user_id=123`）模拟扫码，后期集成企业微信/钉钉扫码获取 OpenID。

---

## 实施路线图总结

| 步骤 | 开发重点 | AI 指令关键词 |
| :--- | :--- | :--- |
| **Step 1** | 基础 CRUD & 数据库 | `FastAPI`, `SQLite`, `Stock subtraction logic` |
| **Step 2** | 优惠计算逻辑 | `Promotion Rule: 10+1`, `Conditional price calculation` |
| **Step 3** | 后台报表与结算 | `Group by Dept`, `Bulk update status`, `Data Export` |
| **Step 4** | UI 优化与部署 | `Tailwind Cards`, `Responsive H5`, `Vercel/Docker` |



太棒了，我们这就从**第一阶段（Step 1）的底层架构**开始。为了让 AI Coding 工具（如 Cursor, Windsurf 或 Claude）能够直接生成可运行的代码，我将为您输出一份符合**生产级规范**的初始协议。

这份协议包含：**数据库建模脚本**、**核心业务逻辑 API** 以及 **H5 极简登记页面的 UI 逻辑**。

---

## 1. 数据库建模 (SQL 脚本)
**AI 指令：** "请根据以下 SQL 结构，使用 SQLAlchemy 构建 Python 数据模型，并支持自动创建 SQLite 数据库文件。"

```sql
-- 1. 用户表 (User)
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,          -- 姓名
    department TEXT NOT NULL,    -- 办公室/部门
    role TEXT DEFAULT 'staff',   -- 角色: staff/admin
    balance_credit INTEGER DEFAULT 0 -- 预存/预定剩余额度
);

-- 2. 水规格表 (WaterType)
CREATE TABLE water_types (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,          -- 18L桶装 / 500ml瓶装
    price REAL NOT NULL,         -- 单价
    stock INTEGER DEFAULT 0,     -- 实时库存
    promo_threshold INTEGER DEFAULT 10, -- 优惠门槛（买N）
    promo_gift INTEGER DEFAULT 1       -- 优惠赠送（赠M）
);

-- 3. 交易/领取流水表 (Transaction)
CREATE TABLE transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    water_type_id INTEGER,
    quantity INTEGER DEFAULT 1,
    actual_price REAL,           -- 实际发生价格（考虑优惠后）
    status TEXT DEFAULT 'unsettled', -- unsettled(待结), settled(已结), reserved(预定)
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id),
    FOREIGN KEY(water_type_id) REFERENCES water_types(id)
);
```

---

## 2. 后端核心逻辑 (FastAPI 示例)
**AI 指令：** "编写一个 FastAPI 接口 `POST /api/record`。当用户扫码提交领水申请时，自动执行以下‘买十赠一’逻辑：统计该用户该规格下 `status='unsettled'` 且 `actual_price > 0` 的记录。若满 10 条，则本条 `actual_price` 设为 0。同时扣减 `water_types` 表的库存。"

```python
# 核心逻辑伪代码 (Logic Logic)
@app.post("/api/record")
async def record_pickup(user_id: int, water_id: int, qty: int):
    # 1. 获取规格信息
    water = db.query(WaterType).filter_id(water_id).first()
    
    # 2. 检查优惠逻辑 (买十赠一)
    count = db.query(Transaction).filter(
        user_id=user_id, 
        water_type_id=water_id, 
        status='unsettled', 
        actual_price > 0
    ).count()
    
    # 判定：如果是第11瓶，则免费
    final_price = 0 if (count > 0 and (count + 1) % 11 == 0) else water.price
    
    # 3. 扣减库存并写入流水
    water.stock -= qty
    new_rec = Transaction(
        user_id=user_id, 
        water_type_id=water_id, 
        actual_price=final_price, 
        quantity=qty
    )
    db.add(new_rec)
    db.commit()
    return {"msg": "领取成功", "is_free": final_price == 0}
```

---

## 3. H5 前端界面设计 (UI/UX 描述)
**AI 指令：** "使用 Vue3 和 TailwindCSS 创建一个移动端优先的领水登记页面。要求如下："

### 视觉元素：
* **主体卡片：** 页面顶部显示“**福山智造学院 - 共享水站**”字样。
* **状态概览：** 显示当前用户“**本月已领：X 桶**”、“**待结算：￥Y**”。
* **领取选择：**
    * [卡片 A]：大桶水 (18L) - 剩余库存: 25 桶。
    * [卡片 B]：小瓶水 (500ml) - 剩余库存: 120 瓶。
* **交互：** 点击卡片直接选中，下方出现“**确认领取**”大按钮（高饱和度蓝色）。

### 响应式布局建议：
* 背景色：`#F8FAFC` (淡灰蓝)
* 卡片圆角：`1.25rem`
* 按钮动画：点击时缩放 `active:scale-95`。

---

## 4. 后台管理面板需求 (Admin)
**AI 指令：** "为管理员生成一个表格视图，包含以下功能："
1.  **实时监控：** 列出所有 `unsettled` 的记录，按部门排序。
2.  **结算按钮：** 每一行末尾有一个“结算”按钮，点击后将该记录 `status` 改为 `settled`。
3.  **库存编辑：** 顶部提供两个输入框，快速修改当前大桶/小瓶水的库存数值。

---


太棒了，我们这就从**第一阶段（Step 1）的底层架构**开始。为了让 AI Coding 工具（如 Cursor, Windsurf 或 Claude）能够直接生成可运行的代码，我将为您输出一份符合**生产级规范**的初始协议。

这份协议包含：**数据库建模脚本**、**核心业务逻辑 API** 以及 **H5 极简登记页面的 UI 逻辑**。

---

## 1. 数据库建模 (SQL 脚本)
**AI 指令：** "请根据以下 SQL 结构，使用 SQLAlchemy 构建 Python 数据模型，并支持自动创建 SQLite 数据库文件。"

```sql
-- 1. 用户表 (User)
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,          -- 姓名
    department TEXT NOT NULL,    -- 办公室/部门
    role TEXT DEFAULT 'staff',   -- 角色: staff/admin
    balance_credit INTEGER DEFAULT 0 -- 预存/预定剩余额度
);

-- 2. 水规格表 (WaterType)
CREATE TABLE water_types (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,          -- 18L桶装 / 500ml瓶装
    price REAL NOT NULL,         -- 单价
    stock INTEGER DEFAULT 0,     -- 实时库存
    promo_threshold INTEGER DEFAULT 10, -- 优惠门槛（买N）
    promo_gift INTEGER DEFAULT 1       -- 优惠赠送（赠M）
);

-- 3. 交易/领取流水表 (Transaction)
CREATE TABLE transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    water_type_id INTEGER,
    quantity INTEGER DEFAULT 1,
    actual_price REAL,           -- 实际发生价格（考虑优惠后）
    status TEXT DEFAULT 'unsettled', -- unsettled(待结), settled(已结), reserved(预定)
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id),
    FOREIGN KEY(water_type_id) REFERENCES water_types(id)
);
```

---

## 2. 后端核心逻辑 (FastAPI 示例)
**AI 指令：** "编写一个 FastAPI 接口 `POST /api/record`。当用户扫码提交领水申请时，自动执行以下‘买十赠一’逻辑：统计该用户该规格下 `status='unsettled'` 且 `actual_price > 0` 的记录。若满 10 条，则本条 `actual_price` 设为 0。同时扣减 `water_types` 表的库存。"

```python
# 核心逻辑伪代码 (Logic Logic)
@app.post("/api/record")
async def record_pickup(user_id: int, water_id: int, qty: int):
    # 1. 获取规格信息
    water = db.query(WaterType).filter_id(water_id).first()
    
    # 2. 检查优惠逻辑 (买十赠一)
    count = db.query(Transaction).filter(
        user_id=user_id, 
        water_type_id=water_id, 
        status='unsettled', 
        actual_price > 0
    ).count()
    
    # 判定：如果是第11瓶，则免费
    final_price = 0 if (count > 0 and (count + 1) % 11 == 0) else water.price
    
    # 3. 扣减库存并写入流水
    water.stock -= qty
    new_rec = Transaction(
        user_id=user_id, 
        water_type_id=water_id, 
        actual_price=final_price, 
        quantity=qty
    )
    db.add(new_rec)
    db.commit()
    return {"msg": "领取成功", "is_free": final_price == 0}
```

---

## 3. H5 前端界面设计 (UI/UX 描述)
**AI 指令：** "使用 Vue3 和 TailwindCSS 创建一个移动端优先的领水登记页面。要求如下："

### 视觉元素：
* **主体卡片：** 页面顶部显示“**福山智造学院 - 共享水站**”字样。
* **状态概览：** 显示当前用户“**本月已领：X 桶**”、“**待结算：￥Y**”。
* **领取选择：**
    * [卡片 A]：大桶水 (18L) - 剩余库存: 25 桶。
    * [卡片 B]：小瓶水 (500ml) - 剩余库存: 120 瓶。
* **交互：** 点击卡片直接选中，下方出现“**确认领取**”大按钮（高饱和度蓝色）。

### 响应式布局建议：
* 背景色：`#F8FAFC` (淡灰蓝)
* 卡片圆角：`1.25rem`
* 按钮动画：点击时缩放 `active:scale-95`。

---

## 4. 后台管理面板需求 (Admin)
**AI 指令：** "为管理员生成一个表格视图，包含以下功能："
1.  **实时监控：** 列出所有 `unsettled` 的记录，按部门排序。
2.  **结算按钮：** 每一行末尾有一个“结算”按钮，点击后将该记录 `status` 改为 `settled`。
3.  **库存编辑：** 顶部提供两个输入框，快速修改当前大桶/小瓶水的库存数值。

---


既然基础架构已经明晰，为了让你能直接投喂给 AI (如 Cursor/Claude) 快速出成果，我为你准备了 **Step 1 的前端 Vue3 组件代码** 和 **初始化数据的 Mock 脚本**。

你可以直接复制以下内容进行项目初始化。

---

## 1. 前端：H5 领取页面组件 (Vue3 + TailwindCSS)
**AI 指令：** "创建一个名为 `WaterPickup.vue` 的组件，要求：适配移动端，风格清爽，包含水规格选择卡片和领取按钮。使用侧重于‘水’的蓝色调 (#007AFF)。"

```vue
<template>
  <div class="min-h-screen bg-slate-50 p-4 font-sans text-slate-900">
    <header class="mb-6 mt-4">
      <h1 class="text-2xl font-bold text-slate-800">智能水站登记</h1>
      <p class="text-sm text-slate-500">办公室领水自助服务系统</p>
    </header>

    <div class="mb-6 rounded-3xl bg-blue-600 p-6 text-white shadow-xl shadow-blue-100">
      <div class="flex justify-between items-center mb-4">
        <span class="opacity-80">当前用户：张三 (研发部)</span>
        <span class="bg-white/20 px-2 py-1 rounded-lg text-xs">个人中心</span>
      </div>
      <div class="grid grid-cols-2 gap-4">
        <div>
          <p class="text-xs opacity-70">本月已领</p>
          <p class="text-xl font-semibold">12 桶</p>
        </div>
        <div>
          <p class="text-xs opacity-70">待结金额</p>
          <p class="text-xl font-semibold">￥180.00</p>
        </div>
      </div>
    </div>

    <div class="space-y-4">
      <h2 class="text-sm font-bold text-slate-400 uppercase tracking-wider">选择领取规格</h2>
      
      <div 
        @click="selected = 1"
        :class="['relative overflow-hidden rounded-2xl border-2 p-4 transition-all', 
                 selected === 1 ? 'border-blue-500 bg-blue-50' : 'border-white bg-white']"
      >
        <div class="flex justify-between items-center">
          <div>
            <h3 class="font-bold text-lg">18L 桶装水</h3>
            <p class="text-sm text-slate-500">库存: 24 桶</p>
          </div>
          <div class="text-right">
            <p class="text-blue-600 font-bold">￥15/桶</p>
            <p class="text-[10px] text-orange-500">买10赠1中</p>
          </div>
        </div>
      </div>

      <div 
        @click="selected = 2"
        :class="['relative overflow-hidden rounded-2xl border-2 p-4 transition-all', 
                 selected === 2 ? 'border-blue-500 bg-blue-50' : 'border-white bg-white']"
      >
        <div class="flex justify-between items-center">
          <div>
            <h3 class="font-bold text-lg">500ml 瓶装水</h3>
            <p class="text-sm text-slate-500">库存: 156 瓶</p>
          </div>
          <div class="text-right">
            <p class="text-blue-600 font-bold">￥2/瓶</p>
          </div>
        </div>
      </div>
    </div>

    <div class="fixed bottom-8 left-4 right-4">
      <button 
        @click="handleSubmit"
        class="w-full rounded-2xl bg-blue-600 py-4 text-lg font-bold text-white shadow-lg shadow-blue-200 active:scale-95 transition-transform"
      >
        确认登记领取
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
const selected = ref(1)
const handleSubmit = () => {
  alert(`提交成功！规格ID: ${selected.value}`)
}
</script>
```

---

## 2. 初始化 Mock 数据脚本 (Python)
**AI 指令：** "编写一个 Python 脚本，使用 SQLAlchemy 往刚才定义的表中插入基础演示数据，包括两个部门的员工和两种水规格。"

```python
# seed.py
from database import SessionLocal, User, WaterType, engine, Base

# 初始化数据库表
Base.metadata.create_all(bind=engine)

def seed_data():
    db = SessionLocal()
    
    # 1. 插入初始规格
    types = [
        WaterType(name="18L桶装水", price=15.0, stock=50, promo_threshold=10, promo_gift=1),
        WaterType(name="500ml瓶装水", price=2.0, stock=200)
    ]
    
    # 2. 插入演示用户
    users = [
        User(name="张三", department="研发部", role="staff"),
        User(name="李四", department="行政部", role="staff"),
        User(name="管理员A", department="后勤部", role="admin")
    ]
    
    db.add_all(types)
    db.add_all(users)
    db.commit()
    print("演示数据初始化成功！")

if __name__ == "__main__":
    seed_data()
```

---

## 3. 后续实施建议：后台管理系统的“懒人方案”
考虑到“清爽、便捷”的要求，管理后台不一定非要从零写复杂的 UI，我建议：

* **使用现成组件库：** 如果 AI 生成，让它用 `Element Plus` (Vue) 或 `Ant Design` (React) 的 `Table` 组件。
* **关键报表逻辑：** 务必让 AI 写一个 **“一键导出 Excel”** 的功能，这在月底办公室结算时是核心刚需。


既然基础数据和前端界面已经初步就绪，我们现在进入**核心管理层面的“对账逻辑”**。

对于管理员来说，最核心的需求是：**“这个月每个办公室领了多少？谁还没给钱？一键结算。”**

以下是为您设计的**管理端对账报表 API 逻辑**，以及**“买十赠一”优惠方案的详细算法实现**。你可以将这些逻辑直接发给 AI，让它补全后端代码。

---

### 1. 核心结算 API (后端逻辑)
**AI 指令：** "请在 FastAPI 中实现一个 `GET /api/admin/report` 接口。要求：
1. 按 `department` (部门) 分组统计。
2. 计算每个部门的：`total_qty` (总领水量)、`unsettled_amount` (待结算金额)、`settled_amount` (已结算金额)。
3. 返回一个 JSON 数组，供前端表格渲染。"

```python
@app.get("/api/admin/report")
def get_monthly_report(db: Session = Depends(get_db)):
    # 使用 SQLAlchemy 的 func 聚合功能
    report = db.query(
        User.department,
        func.sum(Transaction.quantity).label("total_qty"),
        func.sum(case((Transaction.status == 'unsettled', Transaction.actual_price), else_=0)).label("unsettled_amount"),
        func.sum(case((Transaction.status == 'settled', Transaction.actual_price), else_=0)).label("settled_amount")
    ).join(Transaction, User.id == Transaction.user_id) \
     .group_by(User.department).all()
    
    return [dict(row) for row in report]
```

---

### 2. “买十赠一”算法深度完善
为了防止作弊（例如分多次领取小量来规避计数），我们需要一个**严谨的优惠触发检查器**。

**AI 指令：** "完善 `create_transaction` 逻辑。规则：
1. 仅针对‘18L 桶装水’（id=1）。
2. 查询该用户所有 `status='unsettled'` 且 `actual_price > 0` 的记录数。
3. 如果 `(count + 1) % 11 == 0`，则将本次交易的 `actual_price` 设为 0，并在备注中写明‘系统赠送’。
4. 这种方式支持‘买十赠一’的循环触发。"

---

### 3. 管理后台 UI 建议 (Admin Dashboard)
**AI 指令：** "为管理端设计一个简洁的对账页面。要求：
1. **统计卡片：** 顶部显示三个大卡片：[今日领取总量]、[全院待结总额]、[库存预警点]。
2. **结算列表：** 每一行是一个部门。点击‘查看明细’可展开该部门所有员工的领取清单。
3. **批量操作：** 提供一个‘本月已线下收款，一键平账’的按钮，点击后将该部门本月所有记录状态改为 `settled`。"

---

### 4. 实施路线图建议 (Final Roadmap)

1.  **第一步 (基础搭建)：** 让 AI 生成基于 SQLite 的 FastAPI 后端和 Vue3 前端脚手架。
2.  **第二步 (业务联调)：** 重点测试“扫码后库存是否减少”和“第 11 桶是否自动变 0 元”。
3.  **第三步 (管理增强)：** 增加 Excel 导出功能。对于仓库管理，Excel 依然是财务对接最稳妥的方式。
4.  **第四步 (部署)：** * **前端：** 部署在 Vercel 或直接作为静态文件由后端托管。
    * **后端：** 运行在学院内部服务器或云服务器上。
    * **入口：** 将页面 URL 生成二维码，贴在仓库饮水机旁。

**系统贴心小技巧：**
在 H5 页面中，你可以让 AI 增加一个 **“长按二维码保存”** 的功能，方便同事将领取页面收藏到微信浮窗，下次领水不用再找二维码。


