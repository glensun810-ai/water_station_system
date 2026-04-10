-- Migration: 003_create_dining_tables.sql
-- VIP餐厅服务数据库表创建
-- 创建时间: 2026-04-01
-- 说明: 支持VIP餐厅包间管理、套餐管理、预约管理

-- ============================================
-- VIP餐厅包间表
-- ============================================
CREATE TABLE IF NOT EXISTS dining_rooms (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    
    -- 容量信息
    min_capacity INTEGER DEFAULT 2,
    max_capacity INTEGER DEFAULT 20,
    
    -- 价格信息
    room_price DECIMAL(10, 2) NOT NULL,
    service_charge_rate DECIMAL(5, 2) DEFAULT 10.00,
    
    -- 设施配置
    facilities TEXT,
    images TEXT,
    
    -- 状态管理
    status VARCHAR(20) DEFAULT 'available',
    sort_order INTEGER DEFAULT 0,
    
    -- 时间戳
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_dining_rooms_status ON dining_rooms(status);
CREATE INDEX IF NOT EXISTS idx_dining_rooms_sort ON dining_rooms(sort_order);

-- ============================================
-- VIP餐厅套餐表
-- ============================================
CREATE TABLE IF NOT EXISTS dining_packages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    category VARCHAR(50) DEFAULT 'standard',
    
    -- 价格信息
    price_per_person DECIMAL(10, 2) NOT NULL,
    min_people INTEGER DEFAULT 2,
    max_people INTEGER DEFAULT 20,
    
    -- 套餐内容
    menu_items TEXT,
    includes TEXT,
    
    -- 时长
    dining_duration INTEGER DEFAULT 2,
    
    -- 状态管理
    status VARCHAR(20) DEFAULT 'active',
    sort_order INTEGER DEFAULT 0,
    
    -- 时间戳
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_dining_packages_category ON dining_packages(category);
CREATE INDEX IF NOT EXISTS idx_dining_packages_status ON dining_packages(status);

-- ============================================
-- VIP餐厅预约表
-- ============================================
CREATE TABLE IF NOT EXISTS dining_bookings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    booking_no VARCHAR(50) UNIQUE,
    
    -- 包间信息
    room_id INTEGER NOT NULL,
    room_name VARCHAR(100),
    
    -- 套餐信息
    package_id INTEGER,
    package_name VARCHAR(200),
    
    -- 预约时间
    booking_date DATE NOT NULL,
    start_time VARCHAR(20) NOT NULL,
    end_time VARCHAR(20),
    duration INTEGER DEFAULT 2,
    
    -- 用餐人数
    people_count INTEGER NOT NULL,
    
    -- 费用信息
    room_fee DECIMAL(10, 2),
    package_fee DECIMAL(10, 2),
    service_charge DECIMAL(10, 2),
    total_fee DECIMAL(10, 2),
    
    -- 联系信息
    contact_person VARCHAR(100) NOT NULL,
    contact_phone VARCHAR(20) NOT NULL,
    company_name VARCHAR(200),
    
    -- 用餐目的
    purpose VARCHAR(200),
    special_requirements TEXT,
    
    -- 状态管理
    status VARCHAR(20) DEFAULT 'pending',
    cancel_reason VARCHAR(500),
    
    -- 操作记录
    confirmed_by VARCHAR(100),
    confirmed_at DATETIME,
    cancelled_by VARCHAR(100),
    cancelled_at DATETIME,
    
    -- 审计字段
    office_id INTEGER,
    created_by VARCHAR(100),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    -- 外键
    FOREIGN KEY (room_id) REFERENCES dining_rooms(id),
    FOREIGN KEY (package_id) REFERENCES dining_packages(id)
);

CREATE INDEX IF NOT EXISTS idx_dining_bookings_room ON dining_bookings(room_id);
CREATE INDEX IF NOT EXISTS idx_dining_bookings_date ON dining_bookings(booking_date);
CREATE INDEX IF NOT EXISTS idx_dining_bookings_status ON dining_bookings(status);
CREATE INDEX IF NOT EXISTS idx_dining_bookings_office ON dining_bookings(office_id);

-- ============================================
-- 插入示例数据
-- ============================================

-- 示例包间
INSERT INTO dining_rooms (name, description, min_capacity, max_capacity, room_price, facilities, status, sort_order)
VALUES 
('牡丹厅', '豪华包间，配备独立卫生间和休息区', 8, 16, 800.00, '["投影仪", "音响", "卡拉OK", "独立卫生间", "休息区"]', 'available', 1),
('荷花厅', '中型包间，适合商务宴请', 6, 12, 500.00, '["投影仪", "音响", "卡拉OK"]', 'available', 2),
('梅花厅', '小型包间，适合家庭聚餐', 4, 8, 300.00, '["音响", "卡拉OK"]', 'available', 3),
('竹韵厅', '精致小包间，私密性好', 2, 6, 200.00, '["音响"]', 'available', 4);

-- 示例套餐
INSERT INTO dining_packages (name, description, category, price_per_person, min_people, max_people, includes, dining_duration, status, sort_order)
VALUES 
('商务宴请套餐', '适合商务接待，菜品精致丰富', 'business', 288.00, 4, 12, '["凉菜4道", "热菜8道", "汤品2道", "甜点2道", "水果拼盘"]', 2, 'active', 1),
('豪华宴席套餐', '高端宴请首选，顶级食材', 'luxury', 488.00, 6, 16, '["凉菜6道", "热菜10道", "海鲜拼盘", "汤品2道", "甜点4道", "水果拼盘", "红酒2瓶"]', 3, 'active', 2),
('家庭聚会套餐', '温馨家庭聚餐，性价比高', 'standard', 188.00, 2, 8, '["凉菜3道", "热菜6道", "汤品1道", "甜点2道", "水果"]', 2, 'active', 3),
('精致小聚套餐', '适合小范围聚餐', 'standard', 168.00, 2, 6, '["凉菜2道", "热菜4道", "汤品1道", "甜点1道"]', 1.5, 'active', 4);

-- ============================================
-- 验证数据
-- ============================================
SELECT 'dining_rooms' as table_name, COUNT(*) as count FROM dining_rooms
UNION ALL
SELECT 'dining_packages', COUNT(*) FROM dining_packages
UNION ALL
SELECT 'dining_bookings', COUNT(*) FROM dining_bookings;