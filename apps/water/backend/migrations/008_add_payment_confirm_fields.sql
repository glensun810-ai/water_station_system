-- 008: 添加付款和确认相关字段
-- 执行时间: 2026-04-12
-- 说明: 优化领水业务流程，添加付款时间、付款方式、确认时间、确认人等字段

-- 添加付款时间字段
ALTER TABLE office_pickup ADD COLUMN IF NOT EXISTS payment_time DATETIME NULL;
ALTER TABLE office_pickup ADD COLUMN IF NOT EXISTS payment_method VARCHAR(20) NULL;
ALTER TABLE office_pickup ADD COLUMN IF NOT EXISTS payment_note VARCHAR(200) NULL;

-- 添加确认信息字段
ALTER TABLE office_pickup ADD COLUMN IF NOT EXISTS confirmed_time DATETIME NULL;
ALTER TABLE office_pickup ADD COLUMN IF NOT EXISTS confirmed_by INTEGER NULL;
ALTER TABLE office_pickup ADD COLUMN IF NOT EXISTS confirmed_by_name VARCHAR(100) NULL;
ALTER TABLE office_pickup ADD COLUMN IF NOT EXISTS confirm_note VARCHAR(200) NULL;

-- 创建索引以提升查询性能
CREATE INDEX IF NOT EXISTS idx_payment_time ON office_pickup(payment_time);
CREATE INDEX IF NOT EXISTS idx_payment_method ON office_pickup(payment_method);
CREATE INDEX IF NOT EXISTS idx_confirmed_time ON office_pickup(confirmed_time);

-- 数据迁移：将 applied 状态迁移为 paid 状态（保持兼容）
-- UPDATE office_pickup SET settlement_status = 'paid' WHERE settlement_status = 'applied';

-- 验证字段添加成功
SELECT COUNT(*) as field_count FROM pragma_table_info('office_pickup') WHERE name IN ('payment_time', 'payment_method', 'confirmed_time', 'confirmed_by');
