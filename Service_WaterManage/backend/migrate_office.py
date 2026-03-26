"""
Migration script to create office management tables
创建办公室管理相关的数据表
"""

import sqlite3
from datetime import datetime

DATABASE_PATH = "waterms.db"


def migrate():
    """创建办公室管理相关的表"""
    
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # 1. Create Office table - 办公室信息表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS office (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(100) NOT NULL,
            room_number VARCHAR(50),
            description VARCHAR(500),
            is_active INTEGER DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # 2. Create OfficeAccount table - 办公室账户表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS office_account (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            office_id INTEGER NOT NULL,
            office_name VARCHAR(100) NOT NULL,
            office_room_number VARCHAR(50),
            product_id INTEGER NOT NULL,
            product_name VARCHAR(100) NOT NULL,
            product_specification VARCHAR(50),
            reserved_qty INTEGER DEFAULT 0,
            remaining_qty INTEGER DEFAULT 0,
            reserved_person VARCHAR(100),
            reserved_person_id INTEGER,
            note VARCHAR(500),
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(office_id, product_id)
        )
    """)
    
    # 3. Create OfficeRecharge table - 办公室充值记录表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS office_recharge (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            office_id INTEGER NOT NULL,
            office_name VARCHAR(100) NOT NULL,
            office_room_number VARCHAR(50),
            product_id INTEGER NOT NULL,
            product_name VARCHAR(100) NOT NULL,
            product_specification VARCHAR(50),
            quantity INTEGER NOT NULL,
            unit_price FLOAT NOT NULL,
            total_amount FLOAT NOT NULL,
            recharge_person VARCHAR(100),
            recharge_person_id INTEGER,
            note VARCHAR(500),
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # 4. Create OfficePickup table - 办公室领水记录表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS office_pickup (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            office_id INTEGER NOT NULL,
            office_name VARCHAR(100) NOT NULL,
            office_room_number VARCHAR(50),
            product_id INTEGER NOT NULL,
            product_name VARCHAR(100) NOT NULL,
            product_specification VARCHAR(50),
            quantity INTEGER NOT NULL,
            pickup_person VARCHAR(100),
            pickup_person_id INTEGER,
            pickup_time DATETIME NOT NULL,
            payment_mode VARCHAR(20) DEFAULT 'credit',
            note VARCHAR(500),
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # 5. Create OfficeSettlement table - 办公室结算记录表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS office_settlement (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            office_id INTEGER NOT NULL,
            office_name VARCHAR(100) NOT NULL,
            office_room_number VARCHAR(50),
            product_id INTEGER NOT NULL,
            product_name VARCHAR(100) NOT NULL,
            product_specification VARCHAR(50),
            quantity INTEGER NOT NULL,
            unit_price FLOAT NOT NULL,
            total_amount FLOAT NOT NULL,
            settlement_person VARCHAR(100),
            settlement_person_id INTEGER,
            note VARCHAR(500),
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            confirmed_at DATETIME,
            confirmed_by INTEGER
        )
    """)
    
    conn.commit()
    conn.close()
    
    print("✓ Office management tables created successfully!")
    print("✓ 办公室管理相关数据表创建成功!")


if __name__ == "__main__":
    migrate()
