-- 会议室管理数据库表
CREATE TABLE IF NOT EXISTS meeting_rooms (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    location VARCHAR(100),
    capacity INTEGER DEFAULT 10,
    facilities TEXT,
    price_per_hour DECIMAL(10, 2) DEFAULT 0,
    free_hours_per_month INTEGER DEFAULT 0,
    is_active INTEGER DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS meeting_bookings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    booking_no VARCHAR(50) UNIQUE,
    room_id INTEGER NOT NULL,
    room_name VARCHAR(100),
    user_id INTEGER,
    user_name VARCHAR(100),
    user_phone VARCHAR(20),
    department VARCHAR(100),
    booking_date DATE NOT NULL,
    start_time VARCHAR(10) NOT NULL,
    end_time VARCHAR(10) NOT NULL,
    duration DECIMAL(4, 1),
    meeting_title VARCHAR(200),
    attendees_count INTEGER DEFAULT 1,
    total_fee DECIMAL(10, 2) DEFAULT 0,
    status VARCHAR(20) DEFAULT 'pending',
    cancel_reason VARCHAR(500),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (room_id) REFERENCES meeting_rooms(id)
);

INSERT INTO meeting_rooms (name, location, capacity, facilities, price_per_hour, free_hours_per_month, is_active)
VALUES 
('小型会议室A', '3楼301', 10, '["投影仪", "白板", "WiFi"]', 100.00, 5, 1),
('中型会议室B', '4楼401', 20, '["投影仪", "白板", "视频会议", "WiFi"]', 200.00, 3, 1),
('大型会议室C', '5楼501', 50, '["投影仪", "音响", "舞台", "视频会议", "WiFi"]', 300.00, 2, 1),
('VIP会议室', '6楼601', 12, '["投影仪", "白板", "视频会议", "WiFi", "茶水服务"]', 500.00, 1, 1);

INSERT INTO meeting_bookings (booking_no, room_id, room_name, user_name, user_phone, department, booking_date, start_time, end_time, duration, meeting_title, attendees_count, total_fee, status)
VALUES 
('MT20260401001', 1, '小型会议室A', '张三', '13800138001', '技术部', '2026-04-02', '09:00', '12:00', 3, '产品需求评审', 8, 300.00, 'pending'),
('MT20260401002', 2, '中型会议室B', '李四', '13800138002', '市场部', '2026-04-02', '14:00', '18:00', 4, '季度总结会', 15, 800.00, 'confirmed');
