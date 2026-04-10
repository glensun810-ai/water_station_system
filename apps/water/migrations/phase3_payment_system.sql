-- Phase 3: 会员支付系统数据库迁移
-- 执行时间: 2026-04-07
-- 说明: 创建会员套餐、支付订单、退款记录、发票相关表

USE ai_chanyejiqun;

-- 1. 会员套餐表
CREATE TABLE IF NOT EXISTS membership_plans (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL COMMENT '套餐名称',
    description TEXT COMMENT '套餐描述',
    price DECIMAL(10,2) NOT NULL COMMENT '价格（元）',
    original_price DECIMAL(10,2) COMMENT '原价（元）',
    duration_months INT NOT NULL COMMENT '有效期（月）',
    features JSON COMMENT '套餐权益',
    is_active BOOLEAN DEFAULT TRUE COMMENT '是否启用',
    sort_order INT DEFAULT 0 COMMENT '排序',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='会员套餐表';

-- 2. 支付订单表
CREATE TABLE IF NOT EXISTS payment_orders (
    id INT PRIMARY KEY AUTO_INCREMENT,
    order_no VARCHAR(64) UNIQUE NOT NULL COMMENT '订单号',
    user_id INT NOT NULL COMMENT '用户ID',
    plan_id INT NOT NULL COMMENT '会员套餐ID',
    amount DECIMAL(10,2) NOT NULL COMMENT '订单金额',
    payment_method ENUM('alipay', 'wechat') COMMENT '支付方式',
    status ENUM('pending', 'paid', 'cancelled', 'refunded') DEFAULT 'pending' COMMENT '订单状态',
    paid_at TIMESTAMP NULL COMMENT '支付时间',
    trade_no VARCHAR(128) COMMENT '第三方交易号',
    cancel_reason VARCHAR(500) COMMENT '取消原因',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_user_id (user_id),
    INDEX idx_order_no (order_no),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (plan_id) REFERENCES membership_plans(id) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='支付订单表';

-- 3. 退款记录表
CREATE TABLE IF NOT EXISTS refund_records (
    id INT PRIMARY KEY AUTO_INCREMENT,
    refund_no VARCHAR(64) UNIQUE NOT NULL COMMENT '退款单号',
    order_id INT NOT NULL COMMENT '订单ID',
    user_id INT NOT NULL COMMENT '用户ID',
    original_amount DECIMAL(10,2) NOT NULL COMMENT '原订单金额',
    refund_amount DECIMAL(10,2) NOT NULL COMMENT '退款金额',
    used_days INT COMMENT '已使用天数',
    reason VARCHAR(500) COMMENT '退款原因',
    status ENUM('pending', 'success', 'failed') DEFAULT 'pending' COMMENT '退款状态',
    refund_at TIMESTAMP NULL COMMENT '退款时间',
    refund_trade_no VARCHAR(128) COMMENT '第三方退款交易号',
    reject_reason VARCHAR(500) COMMENT '拒绝原因',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_order_id (order_id),
    INDEX idx_user_id (user_id),
    INDEX idx_status (status),
    FOREIGN KEY (order_id) REFERENCES payment_orders(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='退款记录表';

-- 4. 发票表
CREATE TABLE IF NOT EXISTS invoices (
    id INT PRIMARY KEY AUTO_INCREMENT,
    invoice_no VARCHAR(64) UNIQUE NOT NULL COMMENT '发票号码',
    order_id INT NOT NULL COMMENT '订单ID',
    user_id INT NOT NULL COMMENT '用户ID',
    invoice_type ENUM('individual', 'company') NOT NULL COMMENT '发票类型：个人/企业',
    title VARCHAR(200) NOT NULL COMMENT '发票抬头',
    tax_no VARCHAR(50) COMMENT '税号（企业必填）',
    address VARCHAR(200) COMMENT '地址',
    phone VARCHAR(50) COMMENT '电话',
    bank_name VARCHAR(100) COMMENT '开户银行',
    bank_account VARCHAR(50) COMMENT '银行账号',
    amount DECIMAL(10,2) NOT NULL COMMENT '金额',
    email VARCHAR(100) COMMENT '接收邮箱',
    file_path VARCHAR(255) COMMENT '发票文件路径',
    status ENUM('pending', 'issued', 'sent') DEFAULT 'pending' COMMENT '状态',
    issued_at TIMESTAMP NULL COMMENT '开具时间',
    issued_by INT COMMENT '开具人ID',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_order_id (order_id),
    INDEX idx_user_id (user_id),
    INDEX idx_status (status),
    FOREIGN KEY (order_id) REFERENCES payment_orders(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='发票表';

-- 5. 扩展会员表 (如果字段不存在则添加)
-- 检查并添加 plan_id 字段
SET @col_exists = (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS 
                   WHERE TABLE_SCHEMA = 'ai_chanyejiqun' 
                   AND TABLE_NAME = 'memberships' 
                   AND COLUMN_NAME = 'plan_id');

SET @sql = IF(@col_exists = 0, 
              'ALTER TABLE memberships ADD COLUMN plan_id INT COMMENT "会员套餐ID"',
              'SELECT "plan_id already exists"');

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 检查并添加 payment_order_id 字段
SET @col_exists = (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS 
                   WHERE TABLE_SCHEMA = 'ai_chanyejiqun' 
                   AND TABLE_NAME = 'memberships' 
                   AND COLUMN_NAME = 'payment_order_id');

SET @sql = IF(@col_exists = 0, 
              'ALTER TABLE memberships ADD COLUMN payment_order_id INT COMMENT "支付订单ID"',
              'SELECT "payment_order_id already exists"');

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 检查并添加 start_date 字段
SET @col_exists = (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS 
                   WHERE TABLE_SCHEMA = 'ai_chanyejiqun' 
                   AND TABLE_NAME = 'memberships' 
                   AND COLUMN_NAME = 'start_date');

SET @sql = IF(@col_exists = 0, 
              'ALTER TABLE memberships ADD COLUMN start_date DATE COMMENT "会员开始日期"',
              'SELECT "start_date already exists"');

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 检查并添加 end_date 字段
SET @col_exists = (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS 
                   WHERE TABLE_SCHEMA = 'ai_chanyejiqun' 
                   AND TABLE_NAME = 'memberships' 
                   AND COLUMN_NAME = 'end_date');

SET @sql = IF(@col_exists = 0, 
              'ALTER TABLE memberships ADD COLUMN end_date DATE COMMENT "会员结束日期"',
              'SELECT "end_date already exists"');

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 检查并添加 auto_renew 字段
SET @col_exists = (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS 
                   WHERE TABLE_SCHEMA = 'ai_chanyejiqun' 
                   AND TABLE_NAME = 'memberships' 
                   AND COLUMN_NAME = 'auto_renew');

SET @sql = IF(@col_exists = 0, 
              'ALTER TABLE memberships ADD COLUMN auto_renew BOOLEAN DEFAULT FALSE COMMENT "自动续费"',
              'SELECT "auto_renew already exists"');

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 6. 插入初始会员套餐数据
INSERT INTO membership_plans (name, description, price, original_price, duration_months, features, is_active, sort_order) VALUES
('月度会员', '适合短期体验，灵活便捷', 99.00, 129.00, 1, 
 '["会议室预约9折优惠", "专属客服支持", "活动优先报名", "资料下载权限"]', 
 TRUE, 1),

('季度会员', '最受欢迎的选择，性价比高', 259.00, 387.00, 3, 
 '["会议室预约8.5折优惠", "专属客服支持", "活动优先报名", "资料下载权限", "免费停车位3次/月"]', 
 TRUE, 2),

('年度会员', '最划算的方案，尊享更多权益', 899.00, 1548.00, 12, 
 '["会议室预约8折优惠", "专属客服支持", "活动优先报名", "资料下载权限", "免费停车位5次/月", "企业培训课程", "行业资源对接"]', 
 TRUE, 3)

ON DUPLICATE KEY UPDATE updated_at = CURRENT_TIMESTAMP;

-- 7. 创建支付日志表（用于记录支付过程）
CREATE TABLE IF NOT EXISTS payment_logs (
    id INT PRIMARY KEY AUTO_INCREMENT,
    order_no VARCHAR(64) COMMENT '订单号',
    action VARCHAR(50) NOT NULL COMMENT '操作类型',
    request_data TEXT COMMENT '请求数据',
    response_data TEXT COMMENT '响应数据',
    ip_address VARCHAR(50) COMMENT 'IP地址',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_order_no (order_no),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='支付日志表';

-- 完成提示
SELECT 'Phase 3 数据库迁移完成' AS status;