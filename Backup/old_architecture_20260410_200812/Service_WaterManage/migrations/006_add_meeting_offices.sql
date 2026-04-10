-- 补充办公室测试数据
-- 为内部用户会议室预约提供更多选择

INSERT INTO office (name, room_number, leader_name, is_active, created_at, updated_at) VALUES
('总经理', '001', '邓总', 1, datetime('now'), datetime('now')),
('副总经理', '002', '王副总', 1, datetime('now'), datetime('now')),
('天使成长营', '004', '张经理', 1, datetime('now'), datetime('now')),
('Way to AGI', '006', '李总监', 1, datetime('now'), datetime('now')),
('创新实验室', 'B201', '赵博士', 1, datetime('now'), datetime('now')),
('市场部', 'B202', '刘总监', 1, datetime('now'), datetime('now')),
('技术部', 'C301', '陈经理', 1, datetime('now'), datetime('now')),
('产品设计部', 'C302', '周经理', 1, datetime('now'), datetime('now'));