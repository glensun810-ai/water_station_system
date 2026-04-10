-- ============================================
-- 会议室表添加会员价格字段
-- ============================================

-- 添加会员价格字段
ALTER TABLE meeting_rooms ADD COLUMN member_price_per_hour DECIMAL(10, 2) DEFAULT 0.00;

UPDATE meeting_rooms SET member_price_per_hour = price_per_hour * 0.8;

SELECT 
    id,
    name,
    price_per_hour as standard_price,
    member_price_per_hour as member_price,
    ROUND(member_price_per_hour / price_per_hour * 100, 0) as discount_rate
FROM meeting_rooms;