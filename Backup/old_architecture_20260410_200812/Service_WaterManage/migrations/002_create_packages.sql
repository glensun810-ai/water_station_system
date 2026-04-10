-- 套餐管理数据库迁移脚本
-- 创建时间: 2026-04-01
-- 说明: 支持服务套餐组合销售

-- ============================================
-- 套餐定义表
-- ============================================
CREATE TABLE IF NOT EXISTS packages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    
    -- 价格信息
    original_price DECIMAL(10, 2) NOT NULL,
    package_price DECIMAL(10, 2) NOT NULL,
    discount_rate DECIMAL(5, 2) DEFAULT 100,
    
    -- 套餐配置
    service_types TEXT,
    valid_days INTEGER DEFAULT 30,
    max_usage INTEGER DEFAULT 0,
    
    -- 状态管理
    status VARCHAR(20) DEFAULT 'active',
    sort_order INTEGER DEFAULT 0,
    
    -- 时间戳
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_packages_status ON packages(status);
CREATE INDEX IF NOT EXISTS idx_packages_sort_order ON packages(sort_order);

-- ============================================
-- 套餐项目表（套餐包含的服务项目）
-- ============================================
CREATE TABLE IF NOT EXISTS package_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    package_id INTEGER NOT NULL,
    
    -- 服务项目
    service_type VARCHAR(50) NOT NULL,
    product_id INTEGER,
    product_name VARCHAR(200),
    
    -- 数量和单位
    quantity INTEGER NOT NULL DEFAULT 1,
    unit VARCHAR(50),
    
    -- 价格
    unit_price DECIMAL(10, 2),
    subtotal DECIMAL(10, 2),
    
    -- 备注
    note TEXT,
    
    -- 时间戳
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    -- 外键
    FOREIGN KEY (package_id) REFERENCES packages(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_package_items_package_id ON package_items(package_id);
CREATE INDEX IF NOT EXISTS idx_package_items_service_type ON package_items(service_type);

-- ============================================
-- 套餐订单表（套餐预订记录）
-- ============================================
CREATE TABLE IF NOT EXISTS package_orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- 套餐信息
    package_id INTEGER NOT NULL,
    package_name VARCHAR(200),
    
    -- 订购信息
    office_id INTEGER NOT NULL,
    office_name VARCHAR(200),
    order_user_id INTEGER,
    order_user_name VARCHAR(200),
    
    -- 价格信息
    original_price DECIMAL(10, 2),
    package_price DECIMAL(10, 2),
    saved_amount DECIMAL(10, 2),
    
    -- 使用状态
    status VARCHAR(20) DEFAULT 'pending',
    used_count INTEGER DEFAULT 0,
    total_count INTEGER DEFAULT 1,
    
    -- 有效期
    valid_from DATE,
    valid_until DATE,
    
    -- 备注
    note TEXT,
    
    -- 时间戳
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    -- 外键
    FOREIGN KEY (package_id) REFERENCES packages(id)
);

CREATE INDEX IF NOT EXISTS idx_package_orders_package_id ON package_orders(package_id);
CREATE INDEX IF NOT EXISTS idx_package_orders_office_id ON package_orders(office_id);
CREATE INDEX IF NOT EXISTS idx_package_orders_status ON package_orders(status);

-- ============================================
-- 插入示例套餐数据
-- ============================================

-- 示例1: 会议套餐
INSERT INTO packages (name, description, original_price, package_price, discount_rate, service_types, valid_days, status, sort_order)
VALUES (
    '商务会议套餐',
    '会议室4小时 + 茶歇20人次，适合部门例会',
    800.00,
    600.00,
    75.00,
    '["meeting_room", "tea_break"]',
    30,
    'active',
    1
);

-- 插入套餐项目
INSERT INTO package_items (package_id, service_type, product_name, quantity, unit, unit_price, subtotal)
VALUES 
(1, 'meeting_room', '会议室', 4, '小时', 100.00, 400.00),
(1, 'tea_break', '茶歇服务', 20, '人次', 20.00, 400.00);

-- 示例2: 接待套餐
INSERT INTO packages (name, description, original_price, package_price, discount_rate, service_types, valid_days, status, sort_order)
VALUES (
    'VIP接待套餐',
    '接待室3小时 + VIP餐厅用餐 + 茶歇，商务接待首选',
    2500.00,
    1800.00,
    72.00,
    '["reception_room", "vip_dining", "tea_break"]',
    30,
    'active',
    2
);

INSERT INTO package_items (package_id, service_type, product_name, quantity, unit, unit_price, subtotal)
VALUES 
(2, 'reception_room', '接待室', 3, '小时', 300.00, 900.00),
(2, 'vip_dining', 'VIP餐厅', 1, '次', 1200.00, 1200.00),
(2, 'tea_break', '茶歇服务', 20, '人次', 20.00, 400.00);

-- 示例3: 活动套餐
INSERT INTO packages (name, description, original_price, package_price, discount_rate, service_types, valid_days, status, sort_order)
VALUES (
    '企业活动套餐',
    '会场半天 + 前台大屏展示 + 茶歇50人次，适合企业活动',
    3000.00,
    2200.00,
    73.33,
    '["auditorium", "large_screen", "tea_break"]',
    30,
    'active',
    3
);

INSERT INTO package_items (package_id, service_type, product_name, quantity, unit, unit_price, subtotal)
VALUES 
(3, 'auditorium', '会场', 0.5, '天', 4000.00, 2000.00),
(3, 'large_screen', '前台大屏', 4, '小时', 100.00, 400.00),
(3, 'tea_break', '茶歇服务', 50, '人次', 20.00, 1000.00);

-- ============================================
-- 验证数据
-- ============================================
SELECT 'packages' as table_name, COUNT(*) as count FROM packages
UNION ALL
SELECT 'package_items', COUNT(*) FROM package_items
UNION ALL
SELECT 'package_orders', COUNT(*) FROM package_orders;