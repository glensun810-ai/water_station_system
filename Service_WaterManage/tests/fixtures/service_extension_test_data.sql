-- ============================================================
-- Phase 1 测试数据集 - 服务扩展测试数据
-- ============================================================
-- 用途：用于测试数据库扩展后的功能验证
-- 环境：测试数据库（与生产隔离）
-- ============================================================

-- 1. 清理现有测试数据（如有）
DELETE FROM office_pickup WHERE office_name LIKE '测试%' OR pickup_person LIKE '测试%';
DELETE FROM products WHERE name LIKE '测试%';

-- 2. 插入测试产品（水服务 - 原有业务）
INSERT INTO products (name, specification, unit, price, stock, is_active) VALUES
('测试桶装水 18L', '18L', '桶', 20.00, 100, 1),
('测试瓶装水 500ml', '500ml', '瓶', 2.00, 500, 1),
('测试桶装水 12L', '12L', '桶', 15.00, 80, 1);

-- 3. 插入测试产品（新服务类型）
-- 会议室服务
INSERT INTO products (name, specification, unit, price, stock, service_type, resource_config, booking_required, advance_booking_days, is_active) VALUES
('测试会议室 A', '容纳 10 人', '小时', 100.00, 1, 'meeting_room', 
 '{"time_slots": ["09:00-12:00", "14:00-18:00"], "capacity": 10, "facilities": ["投影仪", "白板"]}', 
 1, 7, 1),
('测试会议室 B', '容纳 20 人', '小时', 200.00, 1, 'meeting_room',
 '{"time_slots": ["09:00-12:00", "14:00-18:00", "19:00-21:00"], "capacity": 20}',
 1, 7, 1);

-- VIP 餐厅服务
INSERT INTO products (name, specification, unit, price, stock, service_type, resource_config, booking_required, advance_booking_days, is_active) VALUES
('测试 VIP 包间', '容纳 12 人', '包间', 800.00, 1, 'vip_dining',
 '{"time_slots": ["11:00-14:00", "17:00-21:00"], "capacity": 12, "min_charge": 2000}',
 1, 3, 1);

-- 保洁服务
INSERT INTO products (name, specification, unit, price, stock, service_type, booking_required, is_active) VALUES
('测试日常保洁', '100 平方米', '次', 150.00, 999, 'cleaning', 0, 1),
('测试深度清洁', '全屋', '次', 500.00, 999, 'cleaning', 1, 1);

-- 茶歇服务
INSERT INTO products (name, specification, unit, price, stock, service_type, resource_config, booking_required, advance_booking_days, is_active) VALUES
('测试茶歇套餐 A', '10 人份', '套', 300.00, 50, 'tea_break',
 '{"includes": ["咖啡", "茶", "点心", "水果"], "min_people": 10}',
 1, 2, 1);

-- 4. 插入测试领水/服务记录
-- 原有水业务记录（验证向后兼容）
INSERT INTO office_pickup (office_id, office_name, product_id, product_name, quantity, pickup_person, pickup_time, settlement_status, unit_price, total_amount) VALUES
(1, '测试办公室 A', 1, '测试桶装水 18L', 2, '测试用户 1', NOW(), 'pending', 20.00, 40.00),
(1, '测试办公室 A', 2, '测试瓶装水 500ml', 10, '测试用户 2', NOW(), 'pending', 2.00, 20.00);

-- 新服务类型记录
INSERT INTO office_pickup (office_id, office_name, product_id, product_name, quantity, pickup_person, pickup_time, settlement_status, unit_price, total_amount, service_type, time_slot) VALUES
(1, '测试办公室 A', 4, '测试会议室 A', 4, '测试用户 3', NOW(), 'pending', 100.00, 400.00, 'meeting_room', '2026-04-01 14:00-18:00'),
(1, '测试办公室 A', 6, '测试 VIP 包间', 1, '测试用户 4', NOW(), 'pending', 800.00, 800.00, 'vip_dining', '2026-04-02 18:00-20:00'),
(1, '测试办公室 A', 8, '测试日常保洁', 1, '测试用户 5', NOW(), 'pending', 150.00, 150.00, 'cleaning', NULL),
(1, '测试办公室 A', 10, '测试茶歇套餐 A', 2, '测试用户 6', NOW(), 'pending', 300.00, 600.00, 'tea_break', '2026-04-03 14:00-16:00');

-- 5. 验证数据插入
SELECT '===== 产品总数 =====' AS '';
SELECT COUNT(*) AS total_products FROM products;

SELECT '===== 各服务类型产品数 =====' AS '';
SELECT service_type, COUNT(*) AS count 
FROM products 
GROUP BY service_type;

SELECT '===== 服务记录总数 =====' AS '';
SELECT COUNT(*) AS total_pickups FROM office_pickup;

SELECT '===== 各服务类型记录数 =====' AS '';
SELECT service_type, COUNT(*) AS count 
FROM office_pickup 
WHERE service_type IS NOT NULL
GROUP BY service_type;

SELECT '===== 测试数据插入完成 =====' AS '';
