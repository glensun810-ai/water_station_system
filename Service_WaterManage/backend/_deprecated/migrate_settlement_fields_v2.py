"""
数据库迁移脚本 - 为 transactions_v2 添加结算字段

新增字段:
- settlement_status: pending | settled | partially_settled
- paid_amount: 已结算金额
- remaining_amount: 待结算金额

并扩展 status 语义:
- pending: 待结算
- applied: 已支付待确认
- settled: 已结算
"""

import sqlite3

DB_PATH = "waterms.db"


def migrate():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("PRAGMA table_info(transactions_v2)")
    columns = [desc[1] for desc in cursor.fetchall()]

    def add_col(name: str, ddl: str):
        if name in columns:
            print(f"⚠️  {name} 字段已存在")
            return
        print(f"添加 {name} 字段...")
        cursor.execute(ddl)
        print(f"✅ {name} 字段添加成功")

    add_col("settlement_status", """
        ALTER TABLE transactions_v2
        ADD COLUMN settlement_status TEXT DEFAULT 'pending'
    """)
    add_col("paid_amount", """
        ALTER TABLE transactions_v2
        ADD COLUMN paid_amount REAL DEFAULT 0.0
    """)
    add_col("remaining_amount", """
        ALTER TABLE transactions_v2
        ADD COLUMN remaining_amount REAL DEFAULT 0.0
    """)

    # 兼容旧数据：根据 mode/status 回填
    print("回填历史数据...")
    cursor.execute("""
        UPDATE transactions_v2
        SET
            settlement_status = CASE
                WHEN status = 'settled' THEN 'settled'
                ELSE 'pending'
            END,
            paid_amount = CASE
                WHEN status = 'settled' THEN actual_price
                ELSE 0.0
            END,
            remaining_amount = CASE
                WHEN status = 'settled' THEN 0.0
                ELSE actual_price
            END
        WHERE settlement_status IS NULL
           OR paid_amount IS NULL
           OR remaining_amount IS NULL
    """)

    conn.commit()
    conn.close()
    print("\n✅ 数据库迁移完成!")
    print("📁 数据库文件:", DB_PATH)


if __name__ == "__main__":
    migrate()

