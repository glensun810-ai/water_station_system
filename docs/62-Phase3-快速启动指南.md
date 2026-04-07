# Phase 3: 快速启动指南

## 一、数据库迁移

### 方法1：使用MySQL命令行
```bash
# 登录MySQL
mysql -u root -p

# 选择数据库
use ai_chanyejiqun;

# 执行迁移脚本
source Service_WaterManage/backend/migrations/phase3_payment_system.sql;

# 验证表是否创建成功
show tables;

# 查看套餐数据
SELECT * FROM membership_plans;
```

### 方法2：使用SQL文件导入
```bash
# 直接导入SQL文件
mysql -u root -p ai_chanyejiqun < Service_WaterManage/backend/migrations/phase3_payment_system.sql
```

### 验证数据库迁移
执行以下SQL验证：
```sql
-- 查看会员套餐表
SELECT * FROM membership_plans;

-- 查看支付订单表结构
DESC payment_orders;

-- 查看退款记录表结构
DESC refund_records;

-- 查看发票表结构
DESC invoices;
```

预期结果：
- membership_plans表包含3个初始套餐
- payment_orders表已创建
- refund_records表已创建
- invoices表已创建
- payment_logs表已创建

---

## 二、支付配置

### 2.1 沙箱环境配置（推荐先使用）

#### 步骤1：获取沙箱配置
1. 登录支付宝开放平台：https://openhome.alipay.com/platform/appDaily.htm
2. 获取沙箱APP_ID
3. 下载沙箱RSA2密钥
4. 获取沙箱买家账号

#### 步骤2：创建密钥文件
```bash
# 创建密钥目录
mkdir -p Service_WaterManage/backend/config/keys

# 将私钥保存为文件
# 复制支付宝提供的私钥内容到文件
touch Service_WaterManage/backend/config/keys/app_private_key.pem
touch Service_WaterManage/backend/config/keys/alipay_public_key.pem

# 编辑文件，粘贴密钥内容
```

#### 步骤3：修改配置文件
编辑 `Service_WaterManage/backend/config/payment_config.py`：
```python
ALIPAY_CONFIG = {
    'app_id': '2021000116120012',  # 替换为你的沙箱APP_ID
    'private_key_path': 'Service_WaterManage/backend/config/keys/app_private_key.pem',
    'alipay_public_key_path': 'Service_WaterManage/backend/config/keys/alipay_public_key.pem',
    'debug': True,  # 沙箱环境
    'notify_url': 'http://localhost:8000/api/payment/callback/alipay',
    'return_url': 'http://localhost:8000/portal/payment/result.html'
}
```

### 2.2 生产环境配置

#### 前置要求
- 支付宝企业账号
- 完成企业资质认证
- ICP备案
- HTTPS域名

#### 步骤1：创建应用
1. 登录支付宝开放平台：https://open.alipay.com
2. 创建"网页/移动应用"
3. 添加"电脑网站支付"能力
4. 签约并审核

#### 步骤2：生成密钥
使用支付宝密钥生成工具或openssl：
```bash
# 生成应用私钥
openssl genrsa -out app_private_key.pem 2048

# 导出应用公钥
openssl rsa -in app_private_key.pem -pubout -out app_public_key.pem
```

#### 步骤3：配置密钥
1. 上传应用公钥到支付宝平台
2. 下载支付宝公钥
3. 将两个密钥文件保存到服务器

#### 步骤4：配置回调URL
1. 在支付宝平台设置回调URL
2. URL必须是HTTPS地址
3. URL必须能被外网访问

#### 步骤5：修改配置
```python
ALIPAY_CONFIG = {
    'app_id': 'YOUR_PRODUCTION_APP_ID',
    'private_key_path': '/path/to/app_private_key.pem',
    'alipay_public_key_path': '/path/to/alipay_public_key.pem',
    'debug': False,  # 生产环境
    'notify_url': 'https://yourdomain.com/api/payment/callback/alipay',
    'return_url': 'https://yourdomain.com/portal/payment/result.html'
}
```

---

## 三、启动服务

### 3.1 安装依赖
已安装：
- alipay-sdk-python ✅
- pycryptodome ✅

### 3.2 启动后端服务
```bash
cd Service_WaterManage/backend
python main.py
```

服务将在端口8000启动（或配置的端口）

### 3.3 访问前端页面
- Portal首页：http://localhost:8000/portal/index.html
- 会员套餐：http://localhost:8000/portal/membership-plans.html
- 订单管理：http://localhost:8000/portal/orders.html
- 发票管理：http://localhost:8000/portal/invoices.html

---

## 四、功能测试

### 4.1 测试流程

#### 1. 注册外部用户
- 访问：http://localhost:8000/portal/register.html
- 选择"外部用户"
- 填写信息并注册

#### 2. 查看套餐
- 登录后访问：http://localhost:8000/portal/membership-plans.html
- 查看套餐列表和权益

#### 3. 购买套餐（沙箱测试）
- 点击"立即购买"
- 选择支付宝支付
- 使用沙箱买家账号支付
- 支付成功后自动跳转

#### 4. 查看订单
- 访问：http://localhost:8000/portal/orders.html
- 查看订单状态
- 测试继续支付、取消订单

#### 5. 申请发票
- 在订单页面点击"申请发票"
- 填写发票信息
- 提交申请

#### 6. 申请退款
- 在订单页面点击"申请退款"
- 填写退款原因
- 查看退款金额（按比例计算）

### 4.2 沙箱测试账号
从支付宝沙箱环境获取：
- 沙箱买家账号
- 沙箱买家密码
- 沙箱支付密码

---

## 五、API测试

### 5.1 使用API文档
访问：http://localhost:8000/docs

### 5.2 测试主要接口

#### 获取套餐列表
```bash
curl http://localhost:8000/api/membership/plans
```

#### 创建订单（需要登录）
```bash
curl -X POST http://localhost:8000/api/payment/orders \
  -H "Content-Type: application/json" \
  -H "X-User-Id: 1" \
  -d '{"plan_id": 1, "payment_method": "alipay"}'
```

#### 查询订单
```bash
curl http://localhost:8000/api/payment/orders/MP20260407123456ABCD1234 \
  -H "X-User-Id: 1"
```

---

## 六、常见问题

### Q1: 数据库迁移失败？
检查：
- MySQL是否启动
- 用户是否有权限
- 数据库是否存在

### Q2: 支付配置报错？
检查：
- 密钥文件路径是否正确
- 密钥格式是否正确（RSA2）
- APP_ID是否正确

### Q3: 支付回调失败？
检查：
- 回调URL是否可访问
- 是否设置了CORS
- 签名验证是否正确

### Q4: 前端页面无法访问？
检查：
- portal目录是否存在
- 静态文件是否挂载
- 路由是否正确

---

## 七、下一步优化

完成基础功能后，建议：

1. **微信支付集成**
   - 安装wechatpay-python
   - 配置微信支付参数
   - 实现微信支付API

2. **会员权益实现**
   - 会议室预约折扣
   - 免费停车次数
   - 活动优先报名

3. **发票生成服务**
   - 集成电子发票平台
   - 自动生成PDF
   - 自动发送邮件

4. **性能优化**
   - WebSocket支付状态推送
   - 支付日志异步记录
   - 数据库查询优化

---

## 八、技术支持

- 支付宝开放平台：https://open.alipay.com
- 支付宝文档：https://opendocs.alipay.com
- 支付宝沙箱：https://openhome.alipay.com/platform/appDaily.htm
- 项目文档：docs/60-Phase3-会员支付系统实施计划.md
- 完成报告：docs/61-Phase3-会员支付系统完成报告.md