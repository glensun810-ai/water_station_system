"""
添加结算操作日志表 - 数据库迁移脚本
用于记录所有结算相关操作,提供审计追溯能力

执行时间: 2026-04-08
版本: v1.0
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


def create_settlement_logs_table(cursor):
    """创建结算操作日志表"""
    sql = """
    CREATE TABLE IF NOT EXISTS settlement_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        
        -- 操作信息
        operation_type VARCHAR(50) NOT NULL,
        operation_status VARCHAR(20) NOT NULL DEFAULT 'success',
        
        -- 操作对象
        target_type VARCHAR(20) NOT NULL,
        target_id INTEGER NOT NULL,
        
        -- 状态变更
        old_status VARCHAR(20),
        new_status VARCHAR(20),
        
        -- 操作人信息
        operator_id INTEGER NOT NULL,
        operator_name VARCHAR(100) NOT NULL,
        operator_role VARCHAR(20),
        
        -- 操作详情
        operation_detail TEXT,
        note VARCHAR(500),
        
        -- 时间和设备信息
        operated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        ip_address VARCHAR(50),
        device_info VARCHAR(200)
    )
    """

    cursor.execute(sql)
    print("✅ settlement_logs表创建成功")


def create_indexes(cursor):
    """创建索引以提升查询性能"""
    indexes = [
        ("idx_logs_operation_type", "operation_type, operated_at"),
        ("idx_logs_target", "target_type, target_id"),
        ("idx_logs_operator", "operator_id, operated_at"),
        ("idx_logs_operated_at", "operated_at"),
    ]

    for index_name, columns in indexes:
        try:
            cursor.execute(f"""
                CREATE INDEX IF NOT EXISTS {index_name} 
                ON settlement_logs({columns})
            """)
            print(f"  ✓ 索引 {index_name} 创建成功")
        except Exception as e:
            print(f"  ✗ 索引 {index_name} 创建失败: {e}")


def add_sample_logs(cursor):
    """添加示例日志记录(可选)"""
    sample_logs = [
        {
            "operation_type": "system_init",
            "operation_status": "success",
            "target_type": "system",
            "target_id": 0,
            "operator_id": 0,
            "operator_name": "System",
            "operator_role": "system",
            "operation_detail": '{"action": "settlement_logs_table_created"}',
            "note": "结算操作日志表初始化",
        }
    ]

    for log in sample_logs:
        cursor.execute(
            """
            INSERT INTO settlement_logs 
            (operation_type, operation_status, target_type, target_id, 
             operator_id, operator_name, operator_role, operation_detail, note)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                log["operation_type"],
                log["operation_status"],
                log["target_type"],
                log["target_id"],
                log["operator_id"],
                log["operator_name"],
                log["operator_role"],
                log["operation_detail"],
                log["note"],
            ),
        )

    print("✅ 示例日志记录已添加")


def verify_migration(cursor):
    """验证迁移结果"""
    # 检查表是否存在
    if not check_table_exists(cursor, "settlement_logs"):
        print("❌ 验证失败: settlement_logs表不存在")
        return False

    # 检查表结构
    cursor.execute("PRAGMA table_info(settlement_logs)")
    columns = cursor.fetchall()

    expected_columns = [
        "id",
        "operation_type",
        "operation_status",
        "target_type",
        "target_id",
        "old_status",
        "new_status",
        "operator_id",
        "operator_name",
        "operator_role",
        "operation_detail",
        "note",
        "operated_at",
        "ip_address",
        "device_info",
    ]

    actual_columns = [col[1] for col in columns]

    for expected in expected_columns:
        if expected not in actual_columns:
            print(f"❌ 验证失败: 缺少字段 {expected}")
            return False

    # 检查索引
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='index' AND tbl_name='settlement_logs'
    """)
    indexes = cursor.fetchall()

    if len(indexes) < 4:
        print(f"⚠️  警告: 只创建了 {len(indexes)} 个索引,预期 4 个")

    print("✅ 验证成功: settlement_logs表结构完整")
    return True


def main():
    """主函数"""
    print("=" * 60)
    print("开始执行数据库迁移: 添加结算操作日志表")
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
        if check_table_exists(cursor, "settlement_logs"):
            print("⚠️  警告: settlement_logs表已存在,跳过创建")
        else:
            # 4. 创建表
            print("\n步骤4: 创建settlement_logs表...")
            create_settlement_logs_table(cursor)

            # 5. 创建索引
            print("\n步骤5: 创建索引...")
            create_indexes(cursor)

            # 6. 添加示例日志
            print("\n步骤6: 添加示例日志...")
            add_sample_logs(cursor)

        # 7. 验证迁移
        print("\n步骤7: 验证迁移...")
        if not verify_migration(cursor):
            conn.rollback()
            print("\n❌ 迁移失败,已回滚")
            return False

        # 8. 提交事务
        conn.commit()
        print("\n✅ 事务已提交")

        # 9. 关闭连接
        conn.close()
        print("✅ 数据库连接已关闭")

        print("\n" + "=" * 60)
        print("✅ 数据库迁移成功完成!")
        print("=" * 60)
        print(f"\n备份文件: {backup_path}")
        print("新表: settlement_logs")
        print("用途: 记录所有结算相关操作,提供审计追溯能力")
        print("\n下一步: 更新后端API以记录操作日志")

        return True

    except Exception as e:
        print(f"\n❌ 迁移过程中发生错误: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
