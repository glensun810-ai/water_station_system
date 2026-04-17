-- 空间预约支付结算系统完整迁移脚本
-- 执行时间：2026-04-17
-- 目标：支持记账模式、余额抵扣模式、预付模式

-- ============================================
-- 1. 修复用户类型数据
-- ============================================
UPDATE users SET user_type='internal' WHERE user_type NOT IN ('internal', 'external') OR user_type IS NULL;

-- ============================================
-- 2. 创建用户余额账户表
-- ============================================
CREATE TABLE IF NOT EXISTS user_balance_accounts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER UNIQUE NOT NULL,
    membership_balance DECIMAL(10,2) DEFAULT 0,      -- 会员充值余额
    service_balance DECIMAL(10,2) DEFAULT 0,         -- 服务充值余额
    gift_balance DECIMAL(10,2) DEFAULT 0,            -- 赠送余额
    total_balance DECIMAL(10,2) DEFAULT 0,           -- 总余额
    membership_expire_date DATE,                     -- 会员余额过期日期
    frozen_membership_balance DECIMAL(10,2) DEFAULT 0,
    frozen_service_balance DECIMAL(10,2) DEFAULT 0,
    total_membership_charged DECIMAL(10,2) DEFAULT 0,
    total_service_charged DECIMAL(10,2) DEFAULT 0,
    total_deducted DECIMAL(10,2) DEFAULT 0,
    total_refunded DECIMAL(10,2) DEFAULT 0,
    last_transaction_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- ============================================
-- 3. 创建余额交易记录表
-- ============================================
CREATE TABLE IF NOT EXISTS balance_transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    transaction_no VARCHAR(64) UNIQUE NOT NULL,
    user_id INTEGER NOT NULL,
    transaction_type VARCHAR(20) NOT NULL,           -- membership_charge/service_charge/deduct/refund/gift/adjust/transfer
    amount DECIMAL(10,2) NOT NULL,
    balance_type VARCHAR(20),                        -- membership/service
    before_membership_balance DECIMAL(10,2),
    before_service_balance DECIMAL(10,2),
    before_gift_balance DECIMAL(10,2),
    before_total_balance DECIMAL(10,2),
    after_membership_balance DECIMAL(10,2),
    after_service_balance DECIMAL(10,2),
    after_gift_balance DECIMAL(10,2),
    after_total_balance DECIMAL(10,2),
    reference_type VARCHAR(50),                      -- membership_order/space_booking/credit_note
    reference_id INTEGER,
    reference_no VARCHAR(64),
    description TEXT,
    admin_id INTEGER,
    expire_date DATE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (admin_id) REFERENCES users(id)
);

-- ============================================
-- 4. 创建余额抵扣记录表
-- ============================================
CREATE TABLE IF NOT EXISTS balance_deduct_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    deduct_no VARCHAR(64) UNIQUE NOT NULL,
    user_id INTEGER NOT NULL,
    order_type VARCHAR(50) NOT NULL,                 -- space_booking/...
    order_id INTEGER NOT NULL,
    order_no VARCHAR(64),
    total_amount DECIMAL(10,2) NOT NULL,
    member_discount DECIMAL(10,2) DEFAULT 0,
    membership_deduct DECIMAL(10,2) DEFAULT 0,
    service_deduct DECIMAL(10,2) DEFAULT 0,
    gift_deduct DECIMAL(10,2) DEFAULT 0,
    cash_amount DECIMAL(10,2) DEFAULT 0,
    description TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- ============================================
-- 5. 创建记账账单表（月度账单）
-- ============================================
CREATE TABLE IF NOT EXISTS credit_notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    note_no VARCHAR(50) UNIQUE NOT NULL,             -- 账单编号 CN202604001
    user_id INTEGER NOT NULL,
    user_name VARCHAR(100),
    department VARCHAR(100),
    month VARCHAR(10) NOT NULL,                      -- 账单月份 2026-04
    total_amount DECIMAL(10,2) DEFAULT 0,            -- 账单总金额
    paid_amount DECIMAL(10,2) DEFAULT 0,             -- 已支付金额
    booking_count INTEGER DEFAULT 0,                 -- 预约次数
    status VARCHAR(20) DEFAULT 'pending',            -- pending/partially_paid/paid/settled
    due_date DATE,                                   -- 应付截止日期
    paid_at DATETIME,
    settled_at DATETIME,
    settled_by VARCHAR(100),
    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- ============================================
-- 6. 创建记账账单明细表
-- ============================================
CREATE TABLE IF NOT EXISTS credit_note_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    note_id INTEGER NOT NULL,
    booking_id INTEGER NOT NULL,
    booking_no VARCHAR(50),
    booking_date DATE,
    space_name VARCHAR(100),
    time_slot VARCHAR(20),
    amount DECIMAL(10,2) NOT NULL,
    settled_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (note_id) REFERENCES credit_notes(id),
    FOREIGN KEY (booking_id) REFERENCES space_bookings(id)
);

-- ============================================
-- 7. 预约表新增支付模式字段
-- ============================================
ALTER TABLE space_bookings ADD COLUMN payment_mode VARCHAR(20) DEFAULT 'credit';
-- payment_mode: credit(记账)/balance_deduct(余额抵扣)/prepay(预付)/free(免费)

ALTER TABLE space_bookings ADD COLUMN credit_note_id INTEGER;
-- credit_note_id: 关联的记账账单ID

ALTER TABLE space_bookings ADD COLUMN deduct_record_id INTEGER;
-- deduct_record_id: 关联的抵扣记录ID

-- ============================================
-- 8. 更新payment_status枚举支持记账
-- ============================================
-- SQLite不支持ALTER COLUMN，但值已经可以存储
-- 新增状态值：credit(记账)/deducted(已抵扣)

-- ============================================
-- 9. 为现有预约设置默认支付模式
-- ============================================
-- 内部员工的pending记录设为记账模式
UPDATE space_bookings 
SET payment_mode='credit', payment_status='credit' 
WHERE user_type='internal' AND payment_status='pending';

-- ============================================
-- 10. 创建索引优化查询
-- ============================================
CREATE INDEX IF NOT EXISTS idx_balance_user ON user_balance_accounts(user_id);
CREATE INDEX IF NOT EXISTS idx_transaction_user ON balance_transactions(user_id);
CREATE INDEX IF NOT EXISTS idx_transaction_ref ON balance_transactions(reference_type, reference_id);
CREATE INDEX IF NOT EXISTS idx_deduct_user ON balance_deduct_records(user_id);
CREATE INDEX IF NOT EXISTS idx_deduct_order ON balance_deduct_records(order_type, order_id);
CREATE INDEX IF NOT EXISTS idx_credit_note_user ON credit_notes(user_id);
CREATE INDEX IF NOT EXISTS idx_credit_note_month ON credit_notes(month);
CREATE INDEX IF NOT EXISTS idx_booking_payment ON space_bookings(payment_mode, payment_status);

-- ============================================
-- 11. 初始化用户余额账户（为内部员工）
-- ============================================
INSERT OR IGNORE INTO user_balance_accounts (user_id, membership_balance, service_balance, gift_balance, total_balance)
SELECT id, 0, 0, 0, 0 FROM users WHERE user_type='internal';

-- ============================================
-- 12. 示例数据：给测试用户充值
-- ============================================
-- 给admin用户充值1000元服务余额（用于测试）
INSERT OR REPLACE INTO user_balance_accounts (user_id, service_balance, total_balance, total_service_charged)
VALUES (1, 1000.00, 1000.00, 1000.00);

INSERT INTO balance_transactions (transaction_no, user_id, transaction_type, amount, balance_type, before_service_balance, before_total_balance, after_service_balance, after_total_balance, description)
VALUES ('TX202604171000001', 1, 'service_charge', 1000.00, 'service', 0, 0, 1000.00, 1000.00, '测试充值-服务余额');

-- ============================================
-- 完成
-- ============================================
SELECT 'Payment system migration completed successfully!' as result;