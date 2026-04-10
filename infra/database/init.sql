-- AI产业集群空间服务系统数据库初始化脚本

-- 创建数据库用户和权限
CREATE USER water WITH PASSWORD 'water_secure_password_2026';
CREATE USER meeting WITH PASSWORD 'meeting_secure_password_2026';
CREATE USER unified WITH PASSWORD 'unified_secure_password_2026';
CREATE USER system WITH PASSWORD 'system_secure_password_2026';

-- 创建统一数据库
CREATE DATABASE ai_cluster_db OWNER ai_cluster;

-- 连接到目标数据库
\c ai_cluster_db;

-- 创建扩展
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 统一用户表
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255),
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'user',
    department_id INTEGER,
    is_active BOOLEAN DEFAULT true,
    last_login_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 办公室表
CREATE TABLE offices (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    leader_name VARCHAR(100),
    manager_name VARCHAR(100),
    contact_person VARCHAR(100),
    phone VARCHAR(20),
    room_number VARCHAR(50),
    address TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 产品表（支持多服务类型）
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    specification TEXT,
    unit VARCHAR(20) DEFAULT '桶',
    price DECIMAL(10,2) NOT NULL,
    stock INTEGER DEFAULT 0,
    stock_alert INTEGER DEFAULT 10,
    is_active BOOLEAN DEFAULT true,
    service_type VARCHAR(50) DEFAULT 'water',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 水站 - 用户账户表
CREATE TABLE water_user_accounts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    balance_prepaid DECIMAL(10,2) DEFAULT 0.00,
    balance_credit DECIMAL(10,2) DEFAULT 0.00,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id)
);

-- 水站 - 钱包表
CREATE TABLE water_wallets (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    product_id INTEGER NOT NULL REFERENCES products(id),
    wallet_type VARCHAR(20) NOT NULL, -- 'prepaid', 'credit'
    paid_qty INTEGER DEFAULT 0,       -- 付费数量（仅预付钱包）
    free_qty INTEGER DEFAULT 0,       -- 赠送数量（仅预付钱包）
    available_qty INTEGER DEFAULT 0,   -- 可用数量
    locked_qty INTEGER DEFAULT 0,      -- 锁定数量
    total_consumed INTEGER DEFAULT 0,  -- 已消费总数
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, product_id, wallet_type)
);

-- 水站 - 交易记录表
CREATE TABLE water_transactions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    product_id INTEGER NOT NULL REFERENCES products(id),
    office_id INTEGER REFERENCES offices(id),
    quantity INTEGER NOT NULL,
    paid_qty_deducted INTEGER DEFAULT 0,   -- 扣减的付费数量
    gift_qty_deducted INTEGER DEFAULT 0,   -- 扣减的赠送数量
    unit_price DECIMAL(10,2) NOT NULL,
    total_price DECIMAL(10,2) NOT NULL,
    actual_price DECIMAL(10,2) NOT NULL,
    financial_amount DECIMAL(10,2) NOT NULL,
    mode VARCHAR(20) NOT NULL,             -- 'prepaid', 'credit'
    status VARCHAR(20) NOT NULL,           -- 'pending', 'applied', 'settled', 'cancelled'
    settlement_status VARCHAR(20) DEFAULT 'unsettled',
    pickup_person VARCHAR(100),
    pickup_time TIMESTAMP,
    note TEXT,
    discount_desc VARCHAR(200),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 水站 - 结算批次表
CREATE TABLE water_settlement_batches (
    id SERIAL PRIMARY KEY,
    batch_no VARCHAR(50) UNIQUE NOT NULL,
    user_id INTEGER NOT NULL REFERENCES users(id),
    transaction_ids JSONB NOT NULL,
    total_amount DECIMAL(10,2) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'applied', -- 'applied', 'approved', 'settled', 'cancelled'
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    approved_at TIMESTAMP,
    settled_at TIMESTAMP,
    confirmed_by INTEGER REFERENCES users(id),
    note TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 会议室 - 会议室表
CREATE TABLE meeting_rooms (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    capacity INTEGER NOT NULL,
    equipment TEXT,                    -- 设备列表，JSON格式
    price_per_hour DECIMAL(10,2) DEFAULT 0.00,
    status VARCHAR(20) DEFAULT 'available', -- 'available', 'occupied', 'maintenance'
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 会议室 - 预约表
CREATE TABLE meeting_bookings (
    id SERIAL PRIMARY KEY,
    room_id INTEGER NOT NULL REFERENCES meeting_rooms(id),
    user_id INTEGER NOT NULL REFERENCES users(id),
    date DATE NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    purpose VARCHAR(200),
    attendees INTEGER DEFAULT 1,
    amount DECIMAL(10,2) DEFAULT 0.00,
    status VARCHAR(20) DEFAULT 'booked', -- 'booked', 'pending', 'approved', 'rejected', 'completed', 'cancelled'
    approved_by INTEGER REFERENCES users(id),
    approved_at TIMESTAMP,
    note TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 系统 - 操作日志表
CREATE TABLE system_audit_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50) NOT NULL,
    resource_id INTEGER,
    details JSONB,
    ip_address VARCHAR(45),
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 索引优化
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_users_department ON users(department_id);
CREATE INDEX idx_water_transactions_user ON water_transactions(user_id);
CREATE INDEX idx_water_transactions_product ON water_transactions(product_id);
CREATE INDEX idx_water_transactions_status ON water_transactions(status);
CREATE INDEX idx_water_transactions_created ON water_transactions(created_at);
CREATE INDEX idx_meeting_bookings_user ON meeting_bookings(user_id);
CREATE INDEX idx_meeting_bookings_room ON meeting_bookings(room_id);
CREATE INDEX idx_meeting_bookings_date ON meeting_bookings(date);
CREATE INDEX idx_meeting_bookings_status ON meeting_bookings(status);

-- 插入初始数据
INSERT INTO offices (name, leader_name, room_number, is_active) VALUES
('超级管理员办公室', '系统管理员', 'A001', true),
('技术部办公室', '技术负责人', 'B101', true),
('市场部办公室', '市场负责人', 'B102', true);

INSERT INTO users (username, email, password_hash, role, department_id, is_active) VALUES
('admin', 'admin@ai-cluster.com', '$2b$12$KIXqY8vJ8X3V9QZ7X3V9QeO3V9QZ7X3V9QZ7X3V9QZ7X3V9QZ7X3V', 'super_admin', 1, true),
('water_admin', 'water@ai-cluster.com', '$2b$12$KIXqY8vJ8X3V9QZ7X3V9QeO3V9QZ7X3V9QZ7X3V9QZ7X3V9QZ7X3V', 'admin', 1, true),
('meeting_admin', 'meeting@ai-cluster.com', '$2b$12$KIXqY8vJ8X3V9QZ7X3V9QeO3V9QZ7X3V9QZ7X3V9QZ7X3V9QZ7X3V', 'admin', 1, true);

INSERT INTO products (name, specification, unit, price, stock, service_type, is_active) VALUES
('桶装饮用水', '18.9L/桶', '桶', 15.00, 100, 'water', true),
('瓶装矿泉水', '550ml/瓶', '瓶', 2.00, 500, 'water', true),
('小桶装水', '10L/桶', '桶', 10.00, 50, 'water', true);

INSERT INTO meeting_rooms (name, capacity, price_per_hour, status) VALUES
('会议室A', 20, 100.00, 'available'),
('会议室B', 10, 60.00, 'available'),
('大会议厅', 50, 300.00, 'available');

-- 创建视图
CREATE VIEW water_user_balance_summary AS
SELECT 
    u.id as user_id,
    u.username,
    o.name as office_name,
    COALESCE(SUM(CASE WHEN w.wallet_type = 'prepaid' THEN w.available_qty ELSE 0 END), 0) as prepaid_balance,
    COALESCE(SUM(CASE WHEN w.wallet_type = 'credit' THEN w.available_qty ELSE 0 END), 0) as credit_balance,
    COALESCE(SUM(CASE WHEN t.status = 'pending' THEN t.actual_price ELSE 0 END), 0) as pending_amount
FROM users u
LEFT JOIN offices o ON u.department_id = o.id
LEFT JOIN water_wallets w ON u.id = w.user_id
LEFT JOIN water_transactions t ON u.id = t.user_id AND t.mode = 'credit'
WHERE u.is_active = true
GROUP BY u.id, u.username, o.name;

-- 授权用户访问权限
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO water;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO meeting;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO unified;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO system;

GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO water;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO meeting;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO unified;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO system;

-- 设置默认权限
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO water;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO meeting;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO unified;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO system;

ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE, SELECT ON SEQUENCES TO water;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE, SELECT ON SEQUENCES TO meeting;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE, SELECT ON SEQUENCES TO unified;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE, SELECT ON SEQUENCES TO system;

-- 输出完成信息
SELECT 'Database initialization completed successfully!' as status;