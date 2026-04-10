-- 会议管理审批功能增强
-- 创建时间: 2026-04-03
-- 说明: 添加审批流程表，用于处理预约取消申请、特殊预约审批等

-- 1. 创建审批流程表
CREATE TABLE IF NOT EXISTS meeting_approval_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    approval_no VARCHAR(50) UNIQUE NOT NULL,
    approval_type VARCHAR(20) NOT NULL,
    booking_id INTEGER NOT NULL,
    booking_no VARCHAR(50),
    requester_id INTEGER,
    requester_name VARCHAR(100),
    requester_phone VARCHAR(20),
    request_reason TEXT,
    request_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    -- 审批信息
    status VARCHAR(20) DEFAULT 'pending',
    approver_id INTEGER,
    approver_name VARCHAR(100),
    approval_time DATETIME,
    approval_result VARCHAR(20),
    approval_reason TEXT,
    
    -- 关联信息
    room_id INTEGER,
    room_name VARCHAR(100),
    booking_date DATE,
    start_time VARCHAR(10),
    end_time VARCHAR(10),
    total_fee DECIMAL(10, 2),
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (booking_id) REFERENCES meeting_bookings(id)
);

-- 2. 创建审批历史记录表
CREATE TABLE IF NOT EXISTS meeting_approval_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    approval_id INTEGER NOT NULL,
    action_type VARCHAR(20) NOT NULL,
    action_by VARCHAR(100),
    action_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    action_reason TEXT,
    previous_status VARCHAR(20),
    new_status VARCHAR(20),
    detail TEXT,
    
    FOREIGN KEY (approval_id) REFERENCES meeting_approval_requests(id)
);

-- 3. 创建索引优化查询
CREATE INDEX IF NOT EXISTS idx_approval_status ON meeting_approval_requests(status);
CREATE INDEX IF NOT EXISTS idx_approval_type ON meeting_approval_requests(approval_type);
CREATE INDEX IF NOT EXISTS idx_approval_booking ON meeting_approval_requests(booking_id);
CREATE INDEX IF NOT EXISTS idx_approval_requester ON meeting_approval_requests(requester_id);
CREATE INDEX IF NOT EXISTS idx_approval_time ON meeting_approval_requests(request_time);
CREATE INDEX IF NOT EXISTS idx_approval_history_approval ON meeting_approval_history(approval_id);