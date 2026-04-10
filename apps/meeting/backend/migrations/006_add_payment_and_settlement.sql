-- 会议管理支付结算功能增强
-- 创建时间: 2026-04-02

-- 1. 为预约表添加支付和结算相关字段
ALTER TABLE meeting_bookings ADD COLUMN payment_status VARCHAR(20) DEFAULT 'unpaid';
ALTER TABLE meeting_bookings ADD COLUMN payment_mode VARCHAR(20) DEFAULT 'credit';
ALTER TABLE meeting_bookings ADD COLUMN payment_amount DECIMAL(10, 2) DEFAULT 0;
ALTER TABLE meeting_bookings ADD COLUMN payment_method VARCHAR(50);
ALTER TABLE meeting_bookings ADD COLUMN payment_time DATETIME;
ALTER TABLE meeting_bookings ADD COLUMN payment_evidence TEXT;
ALTER TABLE meeting_bookings ADD COLUMN payment_remark TEXT;
ALTER TABLE meeting_bookings ADD COLUMN confirmed_by VARCHAR(100);
ALTER TABLE meeting_bookings ADD COLUMN confirmed_at DATETIME;
ALTER TABLE meeting_bookings ADD COLUMN user_type VARCHAR(20) DEFAULT 'internal';
ALTER TABLE meeting_bookings ADD COLUMN office_id INTEGER;
ALTER TABLE meeting_bookings ADD COLUMN is_free INTEGER DEFAULT 0;
ALTER TABLE meeting_bookings ADD COLUMN free_hours_used DECIMAL(4, 1) DEFAULT 0;
ALTER TABLE meeting_bookings ADD COLUMN actual_fee DECIMAL(10, 2) DEFAULT 0;
ALTER TABLE meeting_bookings ADD COLUMN discount_amount DECIMAL(10, 2) DEFAULT 0;
ALTER TABLE meeting_bookings ADD COLUMN settlement_batch_id INTEGER;
ALTER TABLE meeting_bookings ADD COLUMN is_deleted INTEGER DEFAULT 0;
ALTER TABLE meeting_bookings ADD COLUMN deleted_at DATETIME;
ALTER TABLE meeting_bookings ADD COLUMN deleted_by VARCHAR(100);
ALTER TABLE meeting_bookings ADD COLUMN delete_reason VARCHAR(500);

-- 2. 创建结算批次表
CREATE TABLE IF NOT EXISTS meeting_settlement_batches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    batch_no VARCHAR(50) UNIQUE NOT NULL,
    office_id INTEGER,
    office_name VARCHAR(100),
    user_id INTEGER,
    user_name VARCHAR(100),
    total_bookings INTEGER DEFAULT 0,
    total_hours DECIMAL(10, 2) DEFAULT 0,
    total_amount DECIMAL(10, 2) DEFAULT 0,
    paid_amount DECIMAL(10, 2) DEFAULT 0,
    free_hours DECIMAL(10, 2) DEFAULT 0,
    discount_amount DECIMAL(10, 2) DEFAULT 0,
    status VARCHAR(20) DEFAULT 'pending',
    settlement_period_start DATE,
    settlement_period_end DATE,
    applied_at DATETIME,
    applied_by VARCHAR(100),
    confirmed_at DATETIME,
    confirmed_by VARCHAR(100),
    remark TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 3. 创建结算明细表
CREATE TABLE IF NOT EXISTS meeting_settlement_details (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    batch_id INTEGER NOT NULL,
    booking_id INTEGER NOT NULL,
    booking_no VARCHAR(50),
    room_name VARCHAR(100),
    booking_date DATE,
    start_time VARCHAR(10),
    end_time VARCHAR(10),
    duration DECIMAL(4, 1),
    total_fee DECIMAL(10, 2),
    actual_fee DECIMAL(10, 2),
    discount_amount DECIMAL(10, 2),
    is_free INTEGER DEFAULT 0,
    free_hours_used DECIMAL(4, 1),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (batch_id) REFERENCES meeting_settlement_batches(id),
    FOREIGN KEY (booking_id) REFERENCES meeting_bookings(id)
);

-- 4. 创建月度免费时长额度表
CREATE TABLE IF NOT EXISTS meeting_free_quota (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    office_id INTEGER NOT NULL,
    office_name VARCHAR(100),
    room_id INTEGER NOT NULL,
    room_name VARCHAR(100),
    year_month VARCHAR(7) NOT NULL,
    total_free_hours DECIMAL(10, 2) DEFAULT 0,
    used_free_hours DECIMAL(10, 2) DEFAULT 0,
    remaining_free_hours DECIMAL(10, 2) DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(office_id, room_id, year_month)
);

-- 5. 创建支付记录表
CREATE TABLE IF NOT EXISTS meeting_payment_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    payment_no VARCHAR(50) UNIQUE NOT NULL,
    booking_id INTEGER NOT NULL,
    booking_no VARCHAR(50),
    user_id INTEGER,
    user_name VARCHAR(100),
    office_id INTEGER,
    office_name VARCHAR(100),
    amount DECIMAL(10, 2) NOT NULL,
    payment_method VARCHAR(50),
    payment_evidence TEXT,
    payment_remark TEXT,
    status VARCHAR(20) DEFAULT 'pending',
    paid_at DATETIME,
    confirmed_at DATETIME,
    confirmed_by VARCHAR(100),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (booking_id) REFERENCES meeting_bookings(id)
);

-- 6. 创建会议室使用统计表
CREATE TABLE IF NOT EXISTS meeting_room_statistics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    room_id INTEGER NOT NULL,
    room_name VARCHAR(100),
    stat_date DATE NOT NULL,
    total_bookings INTEGER DEFAULT 0,
    total_hours DECIMAL(10, 2) DEFAULT 0,
    total_revenue DECIMAL(10, 2) DEFAULT 0,
    paid_bookings INTEGER DEFAULT 0,
    free_bookings INTEGER DEFAULT 0,
    internal_bookings INTEGER DEFAULT 0,
    external_bookings INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(room_id, stat_date)
);

-- 7. 创建操作日志表
CREATE TABLE IF NOT EXISTS meeting_operation_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    operation_type VARCHAR(50) NOT NULL,
    operation_desc VARCHAR(200),
    target_type VARCHAR(50),
    target_id INTEGER,
    target_no VARCHAR(50),
    operator VARCHAR(100),
    operator_role VARCHAR(20),
    detail TEXT,
    ip_address VARCHAR(50),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 8. 创建索引优化查询
CREATE INDEX IF NOT EXISTS idx_booking_status ON meeting_bookings(status);
CREATE INDEX IF NOT EXISTS idx_booking_payment_status ON meeting_bookings(payment_status);
CREATE INDEX IF NOT EXISTS idx_booking_office ON meeting_bookings(office_id);
CREATE INDEX IF NOT EXISTS idx_booking_date ON meeting_bookings(booking_date);
CREATE INDEX IF NOT EXISTS idx_booking_user ON meeting_bookings(user_id);
CREATE INDEX IF NOT EXISTS idx_settlement_status ON meeting_settlement_batches(status);
CREATE INDEX IF NOT EXISTS idx_settlement_office ON meeting_settlement_batches(office_id);
CREATE INDEX IF NOT EXISTS idx_payment_status ON meeting_payment_records(status);
CREATE INDEX IF NOT EXISTS idx_payment_booking ON meeting_payment_records(booking_id);

-- 9. 更新现有数据
UPDATE meeting_bookings 
SET payment_status = 'unpaid',
    payment_mode = 'credit',
    payment_amount = total_fee,
    actual_fee = total_fee,
    user_type = 'internal'
WHERE payment_status IS NULL;