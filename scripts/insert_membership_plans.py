"""
插入历史会员套餐数据
"""

import sys
import os

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from config.database import SessionLocal
from models.membership_plan import MembershipPlan
from decimal import Decimal


def insert_membership_plans():
    """插入会员套餐数据"""
    db = SessionLocal()

    try:
        # 检查是否已有数据
        existing_count = db.query(MembershipPlan).count()
        if existing_count > 0:
            print(f"数据库中已有 {existing_count} 个套餐，跳过插入")
            return

        # 插入历史套餐数据
        plans_data = [
            {
                "name": "月度会员",
                "description": "适合短期体验，灵活便捷",
                "price": Decimal("99.00"),
                "original_price": Decimal("129.00"),
                "duration_months": 1,
                "features": [
                    "会议室预约9折优惠",
                    "专属客服支持",
                    "活动优先报名",
                    "资料下载权限",
                ],
                "icon": "👑",
                "is_active": True,
                "sort_order": 1,
            },
            {
                "name": "季度会员",
                "description": "最受欢迎的选择，性价比高",
                "price": Decimal("259.00"),
                "original_price": Decimal("387.00"),
                "duration_months": 3,
                "features": [
                    "会议室预约8.5折优惠",
                    "专属客服支持",
                    "活动优先报名",
                    "资料下载权限",
                    "免费停车位3次/月",
                ],
                "icon": "🥇",
                "is_active": True,
                "sort_order": 2,
            },
            {
                "name": "年度会员",
                "description": "最划算的方案，尊享更多权益",
                "price": Decimal("899.00"),
                "original_price": Decimal("1548.00"),
                "duration_months": 12,
                "features": [
                    "会议室预约8折优惠",
                    "专属客服支持",
                    "活动优先报名",
                    "资料下载权限",
                    "免费停车位5次/月",
                    "企业培训课程",
                    "行业资源对接",
                ],
                "icon": "💎",
                "is_active": True,
                "sort_order": 3,
            },
        ]

        for plan_data in plans_data:
            plan = MembershipPlan(**plan_data)
            db.add(plan)

        db.commit()
        print("成功插入 3 个会员套餐")

        # 查询并显示插入的数据
        plans = db.query(MembershipPlan).order_by(MembershipPlan.sort_order).all()
        for plan in plans:
            print(f"  - {plan.name}: ¥{plan.price} (原价 ¥{plan.original_price})")

    except Exception as e:
        print(f"插入数据失败: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    insert_membership_plans()
