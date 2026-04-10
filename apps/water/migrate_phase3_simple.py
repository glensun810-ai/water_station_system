"""
简化的数据库迁移脚本 - Phase 3会员支付系统
使用SQLAlchemy模型直接创建表
"""

import sys
import os

# 确保backend目录在路径中
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from config.database import db_manager
from models.base import Base
from models.membership_plan import MembershipPlan
from models.payment_order import PaymentOrder
from models.refund_record import RefundRecord
from models.invoice import Invoice
from sqlalchemy.orm import Session
from decimal import Decimal
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_tables():
    """创建所有表"""
    try:
        logger.info("开始创建表...")

        # 使用SQLAlchemy创建所有表
        Base.metadata.create_all(bind=db_manager.main_engine)

        logger.info("表创建成功！")
        return True
    except Exception as e:
        logger.error(f"创建表失败: {str(e)}")
        return False


def insert_initial_data():
    """插入初始会员套餐数据"""
    try:
        logger.info("开始插入初始数据...")

        # 创建会话
        session = Session(bind=db_manager.main_engine)

        # 检查是否已有数据
        existing_count = session.query(MembershipPlan).count()
        if existing_count > 0:
            logger.info(f"已存在 {existing_count} 个套餐，跳过插入")
            session.close()
            return True

        # 创建初始套餐
        plans = [
            MembershipPlan(
                name="月度会员",
                description="适合短期体验，灵活便捷",
                price=Decimal("99.00"),
                original_price=Decimal("129.00"),
                duration_months=1,
                features=[
                    "会议室预约9折优惠",
                    "专属客服支持",
                    "活动优先报名",
                    "资料下载权限",
                ],
                is_active=True,
                sort_order=1,
            ),
            MembershipPlan(
                name="季度会员",
                description="最受欢迎的选择，性价比高",
                price=Decimal("259.00"),
                original_price=Decimal("387.00"),
                duration_months=3,
                features=[
                    "会议室预约8.5折优惠",
                    "专属客服支持",
                    "活动优先报名",
                    "资料下载权限",
                    "免费停车位3次/月",
                ],
                is_active=True,
                sort_order=2,
            ),
            MembershipPlan(
                name="年度会员",
                description="最划算的方案，尊享更多权益",
                price=Decimal("899.00"),
                original_price=Decimal("1548.00"),
                duration_months=12,
                features=[
                    "会议室预约8折优惠",
                    "专属客服支持",
                    "活动优先报名",
                    "资料下载权限",
                    "免费停车位5次/月",
                    "企业培训课程",
                    "行业资源对接",
                ],
                is_active=True,
                sort_order=3,
            ),
        ]

        # 批量插入
        session.add_all(plans)
        session.commit()

        logger.info(f"成功插入 {len(plans)} 个会员套餐")

        # 查询验证
        all_plans = (
            session.query(MembershipPlan).order_by(MembershipPlan.sort_order).all()
        )
        for plan in all_plans:
            logger.info(f"  - {plan.name}: ¥{plan.price} (原价 ¥{plan.original_price})")

        session.close()
        return True

    except Exception as e:
        logger.error(f"插入初始数据失败: {str(e)}")
        return False


def verify_tables():
    """验证表是否创建成功"""
    try:
        logger.info("验证表结构...")

        from sqlalchemy import inspect

        inspector = inspect(db_manager.main_engine)

        tables = inspector.get_table_names()

        # 检查关键表
        required_tables = [
            "membership_plans",
            "payment_orders",
            "refund_records",
            "invoices",
            "payment_logs",
        ]

        for table in required_tables:
            if table in tables:
                logger.info(f"✓ 表 {table} 已创建")
            else:
                logger.warning(f"✗ 表 {table} 未找到")

        # 查询套餐数量
        session = Session(bind=db_manager.main_engine)
        count = session.query(MembershipPlan).count()
        logger.info(f"会员套餐表有 {count} 条记录")
        session.close()

        return True

    except Exception as e:
        logger.error(f"验证失败: {str(e)}")
        return False


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("Phase 3: 会员支付系统数据库迁移")
    print("=" * 60 + "\n")

    # 步骤1：创建表
    print("步骤1：创建数据库表...")
    success1 = create_tables()

    if success1:
        # 步骤2：插入初始数据
        print("\n步骤2：插入初始套餐数据...")
        success2 = insert_initial_data()

        if success2:
            # 步骤3：验证
            print("\n步骤3：验证迁移结果...")
            verify_tables()

            print("\n" + "=" * 60)
            print("✓ 数据库迁移成功！")
            print("=" * 60)
            print("\n下一步：")
            print("1. 配置支付参数（config/payment_config.py）")
            print("2. 启动服务：python main.py")
            print("3. 访问页面：http://localhost:8000/portal/membership-plans.html")
            print("\n详细说明请查看：docs/62-Phase3-快速启动指南.md")
            print("=" * 60 + "\n")
        else:
            print("\n✗ 插入初始数据失败")
    else:
        print("\n✗ 创建表失败")
