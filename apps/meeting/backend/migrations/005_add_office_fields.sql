-- ============================================
-- 预约表添加办公室关联字段
-- ============================================

-- 添加办公室ID字段（关联offices表）
ALTER TABLE meeting_bookings ADD COLUMN office_id INTEGER;

-- 添加用户类型字段
ALTER TABLE meeting_bookings ADD COLUMN user_type VARCHAR(20) DEFAULT 'external';

-- 添加索引
CREATE INDEX IF NOT EXISTS idx_meeting_bookings_office_id ON meeting_bookings(office_id);

CREATE INDEX IF NOT EXISTS idx_meeting_bookings_user_type ON meeting_bookings(user_type);

-- 验证表结构
PRAGMA table_info(meeting_bookings);