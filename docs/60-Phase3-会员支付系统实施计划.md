# Phase 3: 会员支付系统实施计划

## 一、功能概述

实现企业服务平台Portal的会员支付系统，支持外部用户购买会员服务，包含支付、发票、退款等完整流程。

### 用户确认的支付偏好
- **支付方式**: 微信支付 + 支付宝
- **服务商**: 支付宝官方SDK
- **发票管理**: 需要
- **退款策略**: 按比例退款

---

## 二、技术架构

### 2.1 支付流程设计

```
用户选择会员套餐 → 创建订单 → 发起支付 → 支付回调 → 更新会员状态 → 开具发票（可选）
```

### 2.2 退款流程设计

```
用户申请退款 → 验证会员状态 → 计算退款金额（按比例） → 发起退款 → 退款回调 → 更新状态
```

### 2.3 技术选型

- **支付宝**: 使用官方SDK (alipay-sdk-python)
- **微信支付**: 使用官方SDK (wechatpay-python)
- **发票管理**: 电子发票，PDF格式
- **数据库**: MySQL

---

## 三、数据库设计

### 3.1 会员套餐表 (membership_plans)

```sql
CREATE TABLE membership_plans (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL COMMENT '套餐名称',
    description TEXT COMMENT '套餐描述',
    price DECIMAL(10,2) NOT NULL COMMENT '价格（元）',
    duration_months INT NOT NULL COMMENT '有效期（月）',
    features JSON COMMENT '套餐权益',
    is_active BOOLEAN DEFAULT TRUE COMMENT '是否启用',
    sort_order INT DEFAULT 0 COMMENT '排序',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

### 3.2 支付订单表 (payment_orders)

```sql
CREATE TABLE payment_orders (
    id INT PRIMARY KEY AUTO_INCREMENT,
    order_no VARCHAR(64) UNIQUE NOT NULL COMMENT '订单号',
    user_id INT NOT NULL COMMENT '用户ID',
    plan_id INT NOT NULL COMMENT '会员套餐ID',
    amount DECIMAL(10,2) NOT NULL COMMENT '订单金额',
    payment_method ENUM('alipay', 'wechat') COMMENT '支付方式',
    status ENUM('pending', 'paid', 'cancelled', 'refunded') DEFAULT 'pending' COMMENT '订单状态',
    paid_at TIMESTAMP NULL COMMENT '支付时间',
    trade_no VARCHAR(128) COMMENT '第三方交易号',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_user_id (user_id),
    INDEX idx_order_no (order_no),
    INDEX idx_status (status)
);
```

### 3.3 退款记录表 (refund_records)

```sql
CREATE TABLE refund_records (
    id INT PRIMARY KEY AUTO_INCREMENT,
    refund_no VARCHAR(64) UNIQUE NOT NULL COMMENT '退款单号',
    order_id INT NOT NULL COMMENT '订单ID',
    user_id INT NOT NULL COMMENT '用户ID',
    original_amount DECIMAL(10,2) NOT NULL COMMENT '原订单金额',
    refund_amount DECIMAL(10,2) NOT NULL COMMENT '退款金额',
    reason VARCHAR(500) COMMENT '退款原因',
    status ENUM('pending', 'success', 'failed') DEFAULT 'pending' COMMENT '退款状态',
    refund_at TIMESTAMP NULL COMMENT '退款时间',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_order_id (order_id),
    INDEX idx_user_id (user_id)
);
```

### 3.4 发票表 (invoices)

```sql
CREATE TABLE invoices (
    id INT PRIMARY KEY AUTO_INCREMENT,
    invoice_no VARCHAR(64) UNIQUE NOT NULL COMMENT '发票号码',
    order_id INT NOT NULL COMMENT '订单ID',
    user_id INT NOT NULL COMMENT '用户ID',
    invoice_type ENUM('individual', 'company') NOT NULL COMMENT '发票类型',
    title VARCHAR(200) NOT NULL COMMENT '发票抬头',
    tax_no VARCHAR(50) COMMENT '税号',
    amount DECIMAL(10,2) NOT NULL COMMENT '金额',
    email VARCHAR(100) COMMENT '接收邮箱',
    file_path VARCHAR(255) COMMENT '发票文件路径',
    status ENUM('pending', 'issued', 'sent') DEFAULT 'pending' COMMENT '状态',
    issued_at TIMESTAMP NULL COMMENT '开具时间',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_order_id (order_id),
    INDEX idx_user_id (user_id)
);
```

### 3.5 扩展会员表 (修改现有 memberships 表)

```sql
ALTER TABLE memberships 
ADD COLUMN plan_id INT COMMENT '会员套餐ID',
ADD COLUMN payment_order_id INT COMMENT '支付订单ID',
ADD COLUMN start_date DATE COMMENT '会员开始日期',
ADD COLUMN end_date DATE COMMENT '会员结束日期',
ADD COLUMN auto_renew BOOLEAN DEFAULT FALSE COMMENT '自动续费';
```

---

## 四、后端API设计

### 4.1 会员套餐API

**获取套餐列表**
- 路径: `GET /api/membership/plans`
- 描述: 获取所有可用的会员套餐

**获取套餐详情**
- 路径: `GET /api/membership/plans/:id`
- 描述: 获取指定套餐的详细信息

### 4.2 支付订单API

**创建订单**
- 路径: `POST /api/payment/orders`
- 参数: `{ plan_id, payment_method }`
- 返回: `{ order_no, pay_url }`

**查询订单**
- 路径: `GET /api/payment/orders/:order_no`
- 返回: 订单详情

**获取用户订单列表**
- 路径: `GET /api/payment/orders/user/:user_id`
- 返回: 用户所有订单

### 4.3 支付回调API

**支付宝回调**
- 路径: `POST /api/payment/callback/alipay`
- 描述: 处理支付宝支付结果通知

**微信支付回调**
- 路径: `POST /api/payment/callback/wechat`
- 描述: 处理微信支付结果通知

### 4.4 退款API

**申请退款**
- 路径: `POST /api/payment/refund`
- 参数: `{ order_no, reason }`
- 返回: 退款申请结果

**查询退款状态**
- 路径: `GET /api/payment/refund/:refund_no`
- 返回: 退款详情

### 4.5 发票API

**申请发票**
- 路径: `POST /api/invoices`
- 参数: `{ order_no, invoice_type, title, tax_no, email }`
- 返回: 发票申请结果

**获取发票列表**
- 路径: `GET /api/invoices/user/:user_id`
- 返回: 用户发票列表

**下载发票**
- 路径: `GET /api/invoices/:invoice_no/download`
- 返回: 发票PDF文件

---

## 五、前端页面设计

### 5.1 会员套餐页面 (/portal/membership-plans.html)

- 展示所有可用套餐
- 支持价格对比
- 显示套餐权益
- 立即购买按钮

### 5.2 支付页面 (/portal/payment.html)

- 订单信息确认
- 支付方式选择（支付宝/微信）
- 支付二维码展示
- 支付状态轮询

### 5.3 订单管理页面 (/portal/orders.html)

- 订单列表展示
- 订单详情查看
- 申请退款入口
- 申请发票入口

### 5.4 发票管理页面 (/portal/invoices.html)

- 发票申请表单
- 发票列表查看
- 发票下载功能

### 5.5 会员中心增强 (/portal/membership.html)

- 显示当前会员状态
- 会员到期提醒
- 续费入口
- 套餐升级提示

---

## 六、实施步骤

### 步骤1: 数据库迁移 ✅
- 创建会员套餐表
- 创建支付订单表
- 创建退款记录表
- 创建发票表
- 修改会员表结构

### 步骤2: 后端实现
- 安装支付SDK依赖
- 创建支付相关API
- 实现支付回调处理
- 实现退款逻辑
- 实现发票管理

### 步骤3: 前端实现
- 创建会员套餐页面
- 创建支付流程页面
- 创建订单管理页面
- 创建发票管理页面
- 增强会员中心页面

### 步骤4: 测试与上线
- 沙箱环境测试
- 支付流程测试
- 退款流程测试
- 发票流程测试
- 生产环境部署

---

## 七、配置说明

### 7.1 支付宝配置 (config.py)

```python
ALIPAY_CONFIG = {
    'app_id': 'YOUR_APP_ID',
    'private_key_path': 'path/to/private_key.pem',
    'public_key_path': 'path/to/alipay_public_key.pem',
    'debug': False,  # 生产环境设为False
    'notify_url': 'https://yourdomain.com/api/payment/callback/alipay',
    'return_url': 'https://yourdomain.com/payment/result'
}
```

### 7.2 微信支付配置 (config.py)

```python
WECHATPAY_CONFIG = {
    'appid': 'YOUR_APP_ID',
    'mch_id': 'YOUR_MCH_ID',
    'api_key': 'YOUR_API_KEY',
    'cert_path': 'path/to/cert.pem',
    'key_path': 'path/to/key.pem',
    'notify_url': 'https://yourdomain.com/api/payment/callback/wechat'
}
```

---

## 八、安全考虑

1. **支付安全**
   - 验证回调签名
   - 防止重复支付
   - 订单金额校验
   - 超时订单自动取消

2. **数据安全**
   - 敏感信息加密存储
   - 订单号唯一性校验
   - SQL注入防护

3. **业务安全**
   - 退款金额上限控制
   - 发票开具次数限制
   - 订单状态校验

---

## 九、监控与日志

1. **支付日志**
   - 记录所有支付请求
   - 记录支付回调
   - 记录异常情况

2. **业务监控**
   - 支付成功率
   - 退款率
   - 订单转化率

---

## 十、预计工作量

- 数据库设计与迁移: 0.5天
- 后端API开发: 2天
- 前端页面开发: 2天
- 测试与调试: 1天
- 文档编写: 0.5天

**总计**: 约6个工作日

---

## 十一、风险提示

1. 支付接口申请周期较长（约7-15个工作日）
2. 需要企业资质认证
3. 需要ICP备案
4. 测试环境与生产环境配置不同