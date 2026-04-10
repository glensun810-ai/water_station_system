"""
数据库迁移脚本 - Phase 3会员支付系统
直接使用SQLAlchemy创建表，不依赖mysql命令行工具
"""

from sqlalchemy import create_engine, text
from config.settings import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def migrate():
    """执行Phase 3数据库迁移"""

    # 创建数据库引擎
    engine = create_engine(settings.DATABASE_URL, echo=True)

    # SQL迁移语句
    migration_sql = """
    -- 1. 会员套餐表
    CREATE TABLE IF NOT EXISTS membership_plans (
        id INT PRIMARY KEY AUTO_INCREMENT,
        name VARCHAR(100) NOT NULL COMMENT '套餐名称',
        description TEXT COMMENT '套餐描述',
        price DECIMAL(10,2) NOT NULL COMMENT '价格（元）',
        original_price DECIMAL(10,2) COMMENT '原价（元）',
        duration_months INT NOT NULL COMMENT '有效期（月）',
        features JSON COMMENT '套餐权益',
        is_active BOOLEAN DEFAULT TRUE COMMENT '是否启用',
        sort_order INT DEFAULT 0 COMMENT '排序',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='会员套餐表';
    
    -- 2. 支付订单表
    CREATE TABLE IF NOT EXISTS payment_orders (
        id INT PRIMARY KEY AUTO_INCREMENT,
        order_no VARCHAR(64) UNIQUE NOT NULL COMMENT '订单号',
        user_id INT NOT NULL COMMENT '用户ID',
        plan_id INT NOT NULL COMMENT '会员套餐ID',
        amount DECIMAL(10,2) NOT NULL COMMENT '订单金额',
        payment_method ENUM('alipay', 'wechat') COMMENT '支付方式',
        status ENUM('pending', 'paid', 'cancelled', 'refunded') DEFAULT 'pending' COMMENT '订单状态',
        paid_at TIMESTAMP NULL COMMENT '支付时间',
        trade_no VARCHAR(128) COMMENT '第三方交易号',
        cancel_reason VARCHAR(500) COMMENT '取消原因',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        INDEX idx_user_id (user_id),
        INDEX idx_order_no (order_no),
        INDEX idx_status (status),
        INDEX idx_created_at (created_at)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='支付订单表';
    
    -- 3. 退款记录表
    CREATE TABLE IF NOT EXISTS refund_records (
        id INT PRIMARY KEY AUTO_INCREMENT,
        refund_no VARCHAR(64) UNIQUE NOT NULL COMMENT '退款单号',
        order_id INT NOT NULL COMMENT '订单ID',
        user_id INT NOT NULL COMMENT '用户ID',
        original_amount DECIMAL(10,2) NOT NULL COMMENT '原订单金额',
        refund_amount DECIMAL(10,2) NOT NULL COMMENT '退款金额',
        used_days INT COMMENT '已使用天数',
        reason VARCHAR(500) COMMENT '退款原因',
        status ENUM('pending', 'success', 'failed') DEFAULT 'pending' COMMENT '退款状态',
        refund_at TIMESTAMP NULL COMMENT '退款时间',
        refund_trade_no VARCHAR(128) COMMENT '第三方退款交易号',
        reject_reason VARCHAR(500) COMMENT '拒绝原因',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        INDEX idx_order_id (order_id),
        INDEX idx_user_id (user_id),
        INDEX idx_status (status)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='退款记录表';
    
    -- 4. 发票表
    CREATE TABLE IF NOT EXISTS invoices (
        id INT PRIMARY KEY AUTO_INCREMENT,
        invoice_no VARCHAR(64) UNIQUE NOT NULL COMMENT '发票号码',
        order_id INT NOT NULL COMMENT '订单ID',
        user_id INT NOT NULL COMMENT '用户ID',
        invoice_type ENUM('individual', 'company') NOT NULL COMMENT '发票类型：个人/企业',
        title VARCHAR(200) NOT NULL COMMENT '发票抬头',
        tax_no VARCHAR(50) COMMENT '税号（企业必填）',
        address VARCHAR(200) COMMENT '地址',
        phone VARCHAR(50) COMMENT '电话',
        bank_name VARCHAR(100) COMMENT '开户银行',
        bank_account VARCHAR(50) COMMENT '银行账号',
        amount DECIMAL(10,2) NOT NULL COMMENT '金额',
        email VARCHAR(100) COMMENT '接收邮箱',
        file_path VARCHAR(255) COMMENT '发票文件路径',
        status ENUM('pending', 'issued', 'sent') DEFAULT 'pending' COMMENT '状态',
        issued_at TIMESTAMP NULL COMMENT '开具时间',
        issued_by INT COMMENT '开具人ID',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        INDEX idx_order_id (order_id),
        INDEX idx_user_id (user_id),
        INDEX idx_status (status)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='发票表';
    
    -- 5. 支付日志表
    CREATE TABLE IF NOT EXISTS payment_logs (
        id INT PRIMARY KEY AUTO_INCREMENT,
        order_no VARCHAR(64) COMMENT '订单号',
        action VARCHAR(50) NOT NULL COMMENT '操作类型',
        request_data TEXT COMMENT '请求数据',
        response_data TEXT COMMENT '响应数据',
        ip_address VARCHAR(50) COMMENT 'IP地址',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        INDEX idx_order_no (order_no),
        INDEX idx_created_at (created_at)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='支付日志表';
    
    -- 6. 插入初始会员套餐数据
    INSERT INTO membership_plans (name, description, price, original_price, duration_months, features, is_active, sort_order) VALUES
    ('月度会员', '适合短期体验，灵活便捷', 99.00, 129.00, 1, 
     '["会议室预约9折优惠", "专属客服支持", "活动优先报名", "资料下载权限"]', 
     TRUE, 1),
    ('季度会员', '最受欢迎的选择，性价比高', 259.00, 387.00, 3, 
     '["会议室预约8.5折优惠", "专属客服支持", "活动优先报名", "资料下载权限", "免费停车位3次/月"]', 
     TRUE, 2),
    ('年度会员', '最划算的方案，尊享更多权益', 899.00, 1548.00, 12, 
     '["会议室预约8折优惠", "专属客服支持", "活动优先报名", "资料下载权限", "免费停车位5次/月", "企业培训课程", "行业资源对接"]', 
     TRUE, 3)
    ON DUPLICATE KEY UPDATE updated_at = CURRENT_TIMESTAMP;
    """

    # 判断数据库类型
    if settings._is_sqlite:
        logger.info("检测到SQLite数据库，调整SQL语句...")
        # SQLite需要调整SQL语法
        migration_sql = migration_sql.replace(
            "ENGINE=InnoDB DEFAULT CHARSET=utf8mb4", ""
        )
        migration_sql = migration_sql.replace("COMMENT", "--")
        migration_sql = migration_sql.replace("ENUM", "VARCHAR(20)")
        migration_sql = migration_sql.replace("JSON", "TEXT")
        migration_sql = migration_sql.replace("BOOLEAN", "INTEGER")
        migration_sql = migration_sql.replace("TRUE", "1")
        migration_sql = migration_sql.replace("FALSE", "0")
        migration_sql = migration_sql.replace("AUTO_INCREMENT", "AUTOINCREMENT")
        # 移除外键约束（SQLite不支持）
        migration_sql = migration_sql.replace("FOREIGN KEY", "-- FOREIGN KEY")

    try:
        with engine.begin() as conn:
            # 分割SQL语句并逐个执行
            statements = [
                s.strip()
                for s in migration_sql.split(";")
                if s.strip() and not s.strip().startswith("--")
            ]

            for i, statement in enumerate(statements):
                if statement:
                    logger.info(f"执行第 {i + 1} 条SQL语句...")
                    conn.execute(text(statement))
                    logger.info(f"第 {i + 1} 条SQL语句执行成功")

            logger.info("数据库迁移完成！")

            # 查询验证
            result = conn.execute(text("SELECT COUNT(*) FROM membership_plans"))
            count = result.scalar()
            logger.info(f"会员套餐表中有 {count} 条记录")

            return True

    except Exception as e:
        logger.error(f"数据库迁移失败: {str(e)}")
        return False


def verify_migration():
    """验证数据库迁移结果"""

    engine = create_engine(settings.DATABASE_URL)

    try:
        with engine.connect() as conn:
            # 检查表是否存在
            if settings._is_sqlite:
                tables_query = text("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name IN (
                        'membership_plans', 'payment_orders', 
                        'refund_records', 'invoices', 'payment_logs'
                    )
                """)
            else:
                tables_query = text("""
                    SHOW TABLES LIKE '%membership%' OR LIKE '%payment%' 
                    OR LIKE '%refund%' OR LIKE '%invoice%'
                """)

            result = conn.execute(tables_query)
            tables = [row[0] for row in result]

            logger.info(f"已创建的表: {tables}")

            # 查询套餐数据
            result = conn.execute(text("SELECT id, name, price FROM membership_plans"))
            plans = result.fetchall()

            logger.info("会员套餐数据:")
            for plan in plans:
                logger.info(f"  - ID: {plan[0]}, 名称: {plan[1]}, 价格: ¥{plan[2]}")

            return True

    except Exception as e:
        logger.error(f"验证失败: {str(e)}")
        return False


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("Phase 3: 会员支付系统数据库迁移")
    print("=" * 60 + "\n")

    # 执行迁移
    success = migrate()

    if success:
        print("\n迁移成功！正在验证...")
        verify_migration()

        print("\n" + "=" * 60)
        print("数据库迁移完成！")
        print("=" * 60)
        print("\n下一步：")
        print("1. 配置支付参数（config/payment_config.py）")
        print("2. 启动服务：python main.py")
        print("3. 访问页面：http://localhost:8000/portal/membership-plans.html")
        print("\n详细说明请查看：docs/62-Phase3-快速启动指南.md")
        print("=" * 60 + "\n")
    else:
        print("\n迁移失败，请检查错误信息")
