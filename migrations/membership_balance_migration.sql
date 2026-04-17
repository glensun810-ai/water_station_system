-- 会员订单系统数据库迁移脚本
-- 创建会员订单表、余额账户表、交易记录表
-- 执行日期: 2026-04-17

-- 1. 会员订单表
CREATE TABLE IF NOT EXISTS membership_orders (
    id INT PRIMARY KEY AUTO_INCREMENT,
    order_no VARCHAR(64) UNIQUE NOT NULL COMMENT '订单号',
    user_id INT NOT NULL COMMENT '用户ID',
    plan_id INT NOT NULL COMMENT '会员套餐ID',
    
    amount DECIMAL(10, 2) NOT NULL COMMENT '订单金额',
    original_amount DECIMAL(10, 2) NULL COMMENT '原价金额',
    discount_amount DECIMAL(10, 2) DEFAULT 0 COMMENT '优惠金额',
    
    payment_type ENUM('online', 'offline') DEFAULT 'offline' COMMENT '支付类型',
    payment_method VARCHAR(50) NULL COMMENT '支付方式',
    payment_proof VARCHAR(255) NULL COMMENT '支付凭证文件路径',
    
    status ENUM('pending_review', 'approved', 'rejected', 'cancelled', 'expired') DEFAULT 'pending_review' COMMENT '订单状态',
    
    admin_id INT NULL COMMENT '审核管理员ID',
    review_note TEXT NULL COMMENT '审核备注',
    reviewed_at DATETIME NULL COMMENT '审核时间',
    
    balance_added DECIMAL(10, 2) DEFAULT 0 COMMENT '入账余额金额',
    member_start_date DATE NULL COMMENT '会员开始日期',
    member_end_date DATE NULL COMMENT '会员结束日期',
    member_days INT DEFAULT 0 COMMENT '会员天数',
    
    apply_note TEXT NULL COMMENT '申请备注',
    cancel_reason TEXT NULL COMMENT '取消原因',
    
    paid_at DATETIME NULL COMMENT '支付确认时间',
    trade_no VARCHAR(128) NULL COMMENT '第三方交易号',
    
    is_renewal BOOLEAN DEFAULT FALSE COMMENT '是否续费订单',
    previous_order_id INT NULL COMMENT '前一次订单ID(续费)',
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_user_id (user_id),
    INDEX idx_plan_id (plan_id),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at),
    INDEX idx_order_no (order_no),
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (plan_id) REFERENCES membership_plans(id) ON DELETE CASCADE,
    FOREIGN KEY (admin_id) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='会员订单表';

-- 2. 会员订单审核记录表
CREATE TABLE IF NOT EXISTS membership_order_audits (
    id INT PRIMARY KEY AUTO_INCREMENT,
    order_id INT NOT NULL COMMENT '订单ID',
    
    action VARCHAR(20) NOT NULL COMMENT '操作类型(approve/reject/cancel)',
    admin_id INT NOT NULL COMMENT '操作管理员ID',
    
    before_status ENUM('pending_review', 'approved', 'rejected', 'cancelled', 'expired') NULL COMMENT '操作前状态',
    after_status ENUM('pending_review', 'approved', 'rejected', 'cancelled', 'expired') NULL COMMENT '操作后状态',
    
    note TEXT NULL COMMENT '操作备注',
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_order_id (order_id),
    INDEX idx_admin_id (admin_id),
    
    FOREIGN KEY (order_id) REFERENCES membership_orders(id) ON DELETE CASCADE,
    FOREIGN KEY (admin_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='会员订单审核记录表';

-- 3. 用户余额账户表
CREATE TABLE IF NOT EXISTS user_balance_accounts (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT UNIQUE NOT NULL COMMENT '用户ID',
    
    membership_balance DECIMAL(10, 2) DEFAULT 0 COMMENT '会员充值余额',
    service_balance DECIMAL(10, 2) DEFAULT 0 COMMENT '服务充值余额',
    gift_balance DECIMAL(10, 2) DEFAULT 0 COMMENT '赠送余额',
    total_balance DECIMAL(10, 2) DEFAULT 0 COMMENT '总余额',
    
    membership_expire_date DATE NULL COMMENT '会员余额过期日期',
    
    frozen_membership_balance DECIMAL(10, 2) DEFAULT 0 COMMENT '冻结会员余额',
    frozen_service_balance DECIMAL(10, 2) DEFAULT 0 COMMENT '冻结服务余额',
    
    total_membership_charged DECIMAL(10, 2) DEFAULT 0 COMMENT '累计会员充值',
    total_service_charged DECIMAL(10, 2) DEFAULT 0 COMMENT '累计服务充值',
    total_deducted DECIMAL(10, 2) DEFAULT 0 COMMENT '累计抵扣',
    total_refunded DECIMAL(10, 2) DEFAULT 0 COMMENT '累计退款',
    
    last_transaction_at DATETIME NULL COMMENT '最后交易时间',
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_user_id (user_id),
    INDEX idx_total_balance (total_balance),
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户余额账户表';

-- 4. 余额变动记录表
CREATE TABLE IF NOT EXISTS balance_transactions (
    id INT PRIMARY KEY AUTO_INCREMENT,
    transaction_no VARCHAR(64) UNIQUE NOT NULL COMMENT '交易流水号',
    user_id INT NOT NULL COMMENT '用户ID',
    
    transaction_type ENUM('membership_charge', 'service_charge', 'deduct', 'refund', 'gift', 'adjust', 'transfer') NOT NULL COMMENT '交易类型',
    
    amount DECIMAL(10, 2) NOT NULL COMMENT '变动金额',
    
    balance_type ENUM('membership', 'service') NULL COMMENT '余额类型',
    
    before_membership_balance DECIMAL(10, 2) NULL COMMENT '变动前会员余额',
    before_service_balance DECIMAL(10, 2) NULL COMMENT '变动前服务余额',
    before_gift_balance DECIMAL(10, 2) NULL COMMENT '变动前赠送余额',
    before_total_balance DECIMAL(10, 2) NULL COMMENT '变动前总余额',
    
    after_membership_balance DECIMAL(10, 2) NULL COMMENT '变动后会员余额',
    after_service_balance DECIMAL(10, 2) NULL COMMENT '变动后服务余额',
    after_gift_balance DECIMAL(10, 2) NULL COMMENT '变动后赠送余额',
    after_total_balance DECIMAL(10, 2) NULL COMMENT '变动后总余额',
    
    reference_type VARCHAR(50) NULL COMMENT '关联类型',
    reference_id INT NULL COMMENT '关联记录ID',
    reference_no VARCHAR(64) NULL COMMENT '关联记录编号',
    
    description TEXT NULL COMMENT '交易描述',
    
    admin_id INT NULL COMMENT '操作管理员ID',
    
    expire_date DATE NULL COMMENT '余额过期日期',
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_user_id (user_id),
    INDEX idx_transaction_type (transaction_type),
    INDEX idx_created_at (created_at),
    INDEX idx_transaction_no (transaction_no),
    INDEX idx_reference (reference_type, reference_id),
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (admin_id) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='余额变动记录表';

-- 5. 余额抵扣记录表
CREATE TABLE IF NOT EXISTS balance_deduct_records (
    id INT PRIMARY KEY AUTO_INCREMENT,
    deduct_no VARCHAR(64) UNIQUE NOT NULL COMMENT '抵扣流水号',
    user_id INT NOT NULL COMMENT '用户ID',
    
    order_type VARCHAR(50) NOT NULL COMMENT '订单类型',
    order_id INT NOT NULL COMMENT '订单ID',
    order_no VARCHAR(64) NULL COMMENT '订单编号',
    
    total_amount DECIMAL(10, 2) NOT NULL COMMENT '订单总金额',
    member_discount DECIMAL(10, 2) DEFAULT 0 COMMENT '会员折扣金额',
    member_free_amount DECIMAL(10, 2) DEFAULT 0 COMMENT '会员免费金额',
    
    membership_deduct DECIMAL(10, 2) DEFAULT 0 COMMENT '会员余额抵扣',
    service_deduct DECIMAL(10, 2) DEFAULT 0 COMMENT '服务余额抵扣',
    gift_deduct DECIMAL(10, 2) DEFAULT 0 COMMENT '赠送余额抵扣',
    
    cash_amount DECIMAL(10, 2) DEFAULT 0 COMMENT '现金支付金额',
    
    description TEXT NULL COMMENT '抵扣说明',
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_user_id (user_id),
    INDEX idx_order_type (order_type),
    INDEX idx_created_at (created_at),
    INDEX idx_deduct_no (deduct_no),
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='余额抵扣记录表';

-- 6. 为现有用户创建余额账户（如果不存在）
INSERT INTO user_balance_accounts (user_id, membership_balance, service_balance, gift_balance, total_balance)
SELECT id, 0, 0, 0, 0 FROM users WHERE id NOT IN (SELECT user_id FROM user_balance_accounts)
ON DUPLICATE KEY UPDATE user_id = user_id;

-- 完成
SELECT 'Migration completed successfully!' AS message;