-- Migration: 001_add_service_fields.sql
-- Phase 1: Products 和 OfficePickup 表扩展
-- 零风险策略：只增加字段，不修改现有字段，所有新字段 nullable 有默认值

-- ============================================
-- Products 表扩展
-- ============================================

-- 添加 service_type 字段（默认值 water，向后兼容）
ALTER TABLE products 
ADD COLUMN service_type VARCHAR(50) DEFAULT 'water' COMMENT '服务类型：water/meeting_room/dining/cleaning/tea_break';

-- 添加 resource_config 字段（JSON 配置，nullable）
ALTER TABLE products 
ADD COLUMN resource_config TEXT COMMENT '资源配置 (JSON): {"time_slots": [...], "facilities": [...]}';

-- 添加 booking_required 字段（默认值 0，向后兼容）
ALTER TABLE products 
ADD COLUMN booking_required INTEGER DEFAULT 0 COMMENT '是否需要预约：0-不需要，1-需要';

-- 添加 advance_booking_days 字段（默认值 0，向后兼容）
ALTER TABLE products 
ADD COLUMN advance_booking_days INTEGER DEFAULT 0 COMMENT '可提前预约天数';

-- 添加 category 字段（默认值 physical，向后兼容）
ALTER TABLE products 
ADD COLUMN category VARCHAR(50) DEFAULT 'physical' COMMENT '产品分类：physical/service';

-- 添加 icon 字段（nullable）
ALTER TABLE products 
ADD COLUMN icon VARCHAR(10) COMMENT '图标';

-- 添加 color 字段（默认值 blue，向后兼容）
ALTER TABLE products 
ADD COLUMN color VARCHAR(20) DEFAULT 'blue' COMMENT '颜色';

-- 添加 max_capacity 字段（默认值 0，向后兼容）
ALTER TABLE products 
ADD COLUMN max_capacity INTEGER DEFAULT 0 COMMENT '最大容量（人数等）';

-- 添加 facilities 字段（JSON 配置，nullable）
ALTER TABLE products 
ADD COLUMN facilities TEXT COMMENT '设施配置 (JSON): ["projector", "whiteboard", ...]';

-- ============================================
-- OfficePickup 表扩展
-- ============================================

-- 添加软删除字段（如果不存在）
-- ALTER TABLE office_pickup ADD COLUMN is_deleted INTEGER DEFAULT 0;
-- ALTER TABLE office_pickup ADD COLUMN deleted_at DATETIME;
-- ALTER TABLE office_pickup ADD COLUMN deleted_by INTEGER;
-- ALTER TABLE office_pickup ADD COLUMN delete_reason VARCHAR(500);

-- 添加 service_type 字段（默认值 water，向后兼容）
ALTER TABLE office_pickup 
ADD COLUMN service_type VARCHAR(50) DEFAULT 'water' COMMENT '服务类型';

-- 添加 time_slot 字段（nullable）
ALTER TABLE office_pickup 
ADD COLUMN time_slot VARCHAR(100) COMMENT '时间段：如 "09:00-12:00"';

-- 添加 actual_usage 字段（nullable）
ALTER TABLE office_pickup 
ADD COLUMN actual_usage VARCHAR(200) COMMENT '实际使用情况';

-- 添加 booking_status 字段（默认值 confirmed，向后兼容）
ALTER TABLE office_pickup 
ADD COLUMN booking_status VARCHAR(20) DEFAULT 'confirmed' COMMENT '预约状态：confirmed/cancelled/completed';

-- 添加 service_name 字段（nullable）
ALTER TABLE office_pickup 
ADD COLUMN service_name VARCHAR(100) COMMENT '服务名称';

-- 添加 participants_count 字段（默认值 0，向后兼容）
ALTER TABLE office_pickup 
ADD COLUMN participants_count INTEGER DEFAULT 0 COMMENT '参与人数';

-- 添加 purpose 字段（nullable）
ALTER TABLE office_pickup 
ADD COLUMN purpose VARCHAR(200) COMMENT '使用目的';

-- 添加 contact_phone 字段（nullable）
ALTER TABLE office_pickup 
ADD COLUMN contact_phone VARCHAR(20) COMMENT '联系电话';

-- ============================================
-- 验证迁移结果
-- ============================================

-- 验证 Products 表字段
-- PRAGMA table_info(products);

-- 验证 OfficePickup 表字段
-- PRAGMA table_info(office_pickup);

-- 验证现有数据兼容性
-- SELECT id, name, service_type FROM products WHERE service_type = 'water';
-- SELECT id, office_name, service_type FROM office_pickup WHERE service_type = 'water';