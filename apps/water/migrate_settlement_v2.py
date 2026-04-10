"""
结算模块v2迁移脚本
创建新的结算相关数据表: settlement_applications, settlement_items, monthly_settlements

执行时间: 2026-04-08
版本: v2.0
"""

import sqlite3
import os
from datetime import datetime


def get_db_path():
    """获取数据库路径"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(current_dir, "waterms.db")


def backup_database(db_path):
    """备份数据库"""
    backup_path = db_path + ".backup_" + datetime.now().strftime("%Y%m%d_%H%M%S")
    import shutil

    shutil.copy2(db_path, backup_path)
    print(f"✅ 数据库已备份到: {backup_path}")
    return backup_path


def check_table_exists(cursor, table_name):
    """检查表是否存在"""
    cursor.execute(f"""
        SELECT name FROM sqlite_master
        WHERE type='table' AND name='{table_name}'
    """)
    return cursor.fetchone() is not None


def create_settlement_applications_table(cursor):
    """创建结算申请单表"""
    sql = """
    CREATE TABLE IF NOT EXISTS settlement_applications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,

        -- 申请单编号
        application_no VARCHAR(50) UNIQUE NOT NULL,

        -- 办公室信息
        office_id INTEGER NOT NULL,
        office_name VARCHAR(100) NOT NULL,
        office_room_number VARCHAR(50),

        -- 申请人信息
        applicant_id INTEGER NOT NULL,
        applicant_name VARCHAR(100) NOT NULL,
        applicant_role VARCHAR(20),

        -- 申请内容
        record_count INTEGER NOT NULL DEFAULT 0,
        total_amount DECIMAL(10,2) NOT NULL DEFAULT 0.00,

        -- 状态: pending/applied/approved/confirmed/settled/disputed/cancelled
        status VARCHAR(20) NOT NULL DEFAULT 'applied',

        -- 时间信息
        applied_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        approved_at DATETIME,
        approved_by INTEGER,
        approved_by_name VARCHAR(100),
        confirmed_at DATETIME,
        confirmed_by INTEGER,
        confirmed_by_name VARCHAR(100),
        settled_at DATETIME,
        settled_by INTEGER,
        settled_by_name VARCHAR(100),

        -- 支付信息
        payment_method VARCHAR(50),
        payment_account VARCHAR(100),
        payment_reference VARCHAR(100),
        payment_at DATETIME,

        -- 备注
        note VARCHAR(500),
        reject_reason VARCHAR(500),

        -- 审计字段
        created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
    )
    """

    cursor.execute(sql)
    print("✅ settlement_applications表创建成功")


def create_settlement_items_table(cursor):
    """创建结算明细表"""
    sql = """
    CREATE TABLE IF NOT EXISTS settlement_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,

        -- 关联申请单
        application_id INTEGER NOT NULL,

        -- 领水记录信息
        pickup_id INTEGER NOT NULL,

        -- 产品信息
        product_name VARCHAR(100),
        product_id INTEGER,

        -- 数量和金额
        quantity INTEGER NOT NULL,
        unit_price DECIMAL(10,2),
        amount DECIMAL(10,2) NOT NULL,

        -- 状态
        pickup_status VARCHAR(20) NOT NULL DEFAULT 'applied',

        -- 时间信息
        pickup_time DATETIME,

        -- 领取人信息
        pickup_person VARCHAR(100),
        pickup_person_id INTEGER,

        -- 备注
        note VARCHAR(500),

        -- 审计字段
        created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

        FOREIGN KEY (application_id) REFERENCES settlement_applications(id) ON DELETE CASCADE
    )
    """

    cursor.execute(sql)
    print("✅ settlement_items表创建成功")


def create_monthly_settlements_table(cursor):
    """创建月度结算单表"""
    sql = """
    CREATE TABLE IF NOT EXISTS monthly_settlements (
        id INTEGER PRIMARY KEY AUTOINCREMENT,

        -- 结算单编号
        settlement_no VARCHAR(50) UNIQUE NOT NULL,

        -- 办公室信息
        office_id INTEGER NOT NULL,
        office_name VARCHAR(100) NOT NULL,
        office_room_number VARCHAR(50),

        -- 结算周期
        settlement_period VARCHAR(20) NOT NULL,
        start_date DATE NOT NULL,
        end_date DATE NOT NULL,

        -- 结算内容
        record_count INTEGER NOT NULL DEFAULT 0,
        total_amount DECIMAL(10,2) NOT NULL DEFAULT 0.00,

        -- 状态: pending/approved/settled/cancelled
        status VARCHAR(20) NOT NULL DEFAULT 'pending',

        -- 审核信息
        approved_at DATETIME,
        approved_by INTEGER,
        approved_by_name VARCHAR(100),

        -- 结算信息
        settled_at DATETIME,
        settled_by INTEGER,
        settled_by_name VARCHAR(100),

        -- 支付信息
        payment_method VARCHAR(50),
        payment_account VARCHAR(100),
        payment_reference VARCHAR(100),
        payment_at DATETIME,

        -- 备注
        note VARCHAR(500),

        -- 审计字段
        created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
    )
    """

    cursor.execute(sql)
    print("✅ monthly_settlements表创建成功")


def create_indexes(cursor):
    """创建索引以提升查询性能"""
    indexes = [
        ("idx_applications_office", "settlement_applications", "office_id, status"),
        ("idx_applications_status", "settlement_applications", "status, applied_at"),
        ("idx_applications_no", "settlement_applications", "application_no"),
        (
            "idx_applications_applicant",
            "settlement_applications",
            "applicant_id, applied_at",
        ),
        ("idx_items_application", "settlement_items", "application_id"),
        ("idx_items_pickup", "settlement_items", "pickup_id"),
        ("idx_monthly_office", "monthly_settlements", "office_id, settlement_period"),
        ("idx_monthly_status", "monthly_settlements", "status, settlement_period"),
        ("idx_monthly_no", "monthly_settlements", "settlement_no"),
    ]

    for index_name, table_name, columns in indexes:
        try:
            cursor.execute(f"""
                CREATE INDEX IF NOT EXISTS {index_name}
                ON {table_name}({columns})
            """)
            print(f"  ✓ 索引 {index_name} 创建成功")
        except Exception as e:
            print(f"  ✗ 索引 {index_name} 创建失败: {e}")


def verify_migration(cursor):
    """验证迁移结果"""
    tables_to_check = [
        (
            "settlement_applications",
            [
                "id",
                "application_no",
                "office_id",
                "office_name",
                "applicant_id",
                "applicant_name",
                "record_count",
                "total_amount",
                "status",
                "applied_at",
                "created_at",
                "updated_at",
            ],
        ),
        (
            "settlement_items",
            [
                "id",
                "application_id",
                "pickup_id",
                "product_name",
                "quantity",
                "amount",
                "pickup_status",
                "created_at",
            ],
        ),
        (
            "monthly_settlements",
            [
                "id",
                "settlement_no",
                "office_id",
                "settlement_period",
                "start_date",
                "end_date",
                "record_count",
                "total_amount",
                "status",
                "created_at",
                "updated_at",
            ],
        ),
    ]

    all_valid = True

    for table_name, expected_columns in tables_to_check:
        if not check_table_exists(cursor, table_name):
            print(f"❌ 验证失败: {table_name}表不存在")
            all_valid = False
            continue

        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        actual_columns = [col[1] for col in columns]

        for expected in expected_columns:
            if expected not in actual_columns:
                print(f"❌ 验证失败: {table_name}表缺少字段 {expected}")
                all_valid = False

    if all_valid:
        print("✅ 验证成功: 所有表结构完整")
        return True
    else:
        return False


def main():
    """主函数"""
    print("=" * 60)
    print("开始执行数据库迁移: 结算模块v2")
    print("=" * 60)

    db_path = get_db_path()
    print(f"\n数据库路径: {db_path}")

    if not os.path.exists(db_path):
        print(f"❌ 错误: 数据库文件不存在: {db_path}")
        return False

    try:
        # 1. 备份数据库
        print("\n步骤1: 备份数据库...")
        backup_path = backup_database(db_path)

        # 2. 连接数据库
        print("\n步骤2: 连接数据库...")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # 3. 检查表是否已存在
        print("\n步骤3: 检查表是否存在...")

        if not check_table_exists(cursor, "settlement_applications"):
            print("步骤4: 创建settlement_applications表...")
            create_settlement_applications_table(cursor)
        else:
            print("⚠️  警告: settlement_applications表已存在,跳过创建")

        if not check_table_exists(cursor, "settlement_items"):
            print("步骤5: 创建settlement_items表...")
            create_settlement_items_table(cursor)
        else:
            print("⚠️  警告: settlement_items表已存在,跳过创建")

        if not check_table_exists(cursor, "monthly_settlements"):
            print("步骤6: 创建monthly_settlements表...")
            create_monthly_settlements_table(cursor)
        else:
            print("⚠️  警告: monthly_settlements表已存在,跳过创建")

        # 7. 创建索引
        print("\n步骤7: 创建索引...")
        create_indexes(cursor)

        # 8. 验证迁移
        print("\n步骤8: 验证迁移...")
        if not verify_migration(cursor):
            conn.rollback()
            print("\n❌ 迁移失败,已回滚")
            return False

        # 9. 提交事务
        conn.commit()
        print("\n✅ 事务已提交")

        # 10. 关闭连接
        conn.close()
        print("✅ 数据库连接已关闭")

        print("\n" + "=" * 60)
        print("✅ 数据库迁移成功完成!")
        print("=" * 60)
        print(f"\n备份文件: {backup_path}")
        print("新表:")
        print("  - settlement_applications (结算申请单表)")
        print("  - settlement_items (结算明细表)")
        print("  - monthly_settlements (月度结算单表)")
        print("\n下一步: 创建对应的ORM模型并实现数据迁移")

        return True

    except Exception as e:
        print(f"\n❌ 迁移过程中发生错误: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
