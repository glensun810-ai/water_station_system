"""
买 N 赠 M 优惠字段迁移脚本

为 office_pickup 表添加：
- free_qty: 免费数量
- discount_desc: 优惠描述
"""

import sqlite3
from pathlib import Path

# 数据库路径
db_path = Path(__file__).parent / "waterms.db"

# 连接数据库
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("📋 开始迁移：添加买 N 赠 M 优惠字段")
print("=" * 60)

# 检查字段是否已存在
cursor.execute("PRAGMA table_info(office_pickup)")
columns = [col[1] for col in cursor.fetchall()]

# 添加 free_qty 字段
if 'free_qty' not in columns:
    cursor.execute("""
        ALTER TABLE office_pickup 
        ADD COLUMN free_qty INTEGER DEFAULT 0
    """)
    print("✅ 添加 free_qty 字段（免费数量）")
else:
    print("⚠️  free_qty 字段已存在")

# 添加 discount_desc 字段
if 'discount_desc' not in columns:
    cursor.execute("""
        ALTER TABLE office_pickup 
        ADD COLUMN discount_desc VARCHAR(500)
    """)
    print("✅ 添加 discount_desc 字段（优惠描述）")
else:
    print("⚠️  discount_desc 字段已存在")

# 提交更改
conn.commit()
conn.close()

print("=" * 60)
print("✅ 迁移完成！")
