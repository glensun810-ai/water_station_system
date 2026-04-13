"""
初始化空间类型数据
创建5种默认的空间类型配置
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from shared.models.space.space_type import SpaceType
from models.base import Base

# 使用主数据库
engine = create_engine("sqlite:///./data/app.db", echo=False)
SessionLocal = sessionmaker(bind=engine)


def init_space_types():
    """初始化5种空间类型"""

    db = SessionLocal()

    try:
        # 检查是否已有数据
        existing_count = db.query(SpaceType).count()
        if existing_count > 0:
            print(f"✓ 已存在 {existing_count} 种空间类型，跳过初始化")
            return

        # 创建5种默认空间类型
        default_types = [
            {
                "type_code": "meeting_room",
                "type_name": "会议室",
                "type_name_en": "Meeting Room",
                "description": "小型会议室，适合10-20人会议",
                "min_duration_unit": "hour",
                "min_duration_value": 1,
                "max_duration_value": 8,
                "advance_booking_days": 7,
                "min_capacity": 10,
                "max_capacity": 20,
                "requires_approval": False,
                "requires_deposit": False,
                "standard_facilities": '["投影仪", "白板", "音响", "空调", "WiFi"]',
                "optional_addons": '["茶歇", "视频会议设备", "翻译设备"]',
                "icon": "🏢",
                "color_theme": "#2563EB",
                "sort_order": 1,
            },
            {
                "type_code": "auditorium",
                "type_name": "会场/多功能厅",
                "type_name_en": "Auditorium/Multipurpose Hall",
                "description": "大型会场，适合50-500人活动",
                "min_duration_unit": "session",
                "min_duration_value": 1,
                "max_duration_value": 2,
                "advance_booking_days": 30,
                "min_capacity": 50,
                "max_capacity": 500,
                "requires_approval": True,
                "approval_type": "manager_approval",
                "approval_deadline_hours": 48,
                "requires_deposit": True,
                "deposit_percentage": 0.3,
                "deposit_refund_rules": "提前7天取消全额退款，提前3天退款50%，3天内不退款",
                "standard_facilities": '["舞台", "专业音响", "LED大屏", "灯光系统", "空调"]',
                "optional_addons": '["直播设备", "摄影服务", "餐饮服务", "安保服务"]',
                "icon": "🎭",
                "color_theme": "#7C3AED",
                "sort_order": 2,
            },
            {
                "type_code": "lobby_screen",
                "type_name": "大堂大屏",
                "type_name_en": "Lobby LED Screen",
                "description": "大堂LED大屏，投放广告或展示",
                "min_duration_unit": "slot",
                "min_duration_value": 1,
                "max_duration_value": 10,
                "advance_booking_days": 14,
                "min_capacity": 0,
                "max_capacity": 0,
                "requires_approval": True,
                "approval_type": "content_review",
                "approval_deadline_hours": 24,
                "requires_deposit": False,
                "standard_facilities": '["LED大屏", "播放系统", "网络连接"]',
                "optional_addons": '["内容制作服务", "技术支持"]',
                "icon": "📺",
                "color_theme": "#F59E0B",
                "sort_order": 3,
            },
            {
                "type_code": "lobby_booth",
                "type_name": "大堂展位",
                "type_name_en": "Lobby Exhibition Booth",
                "description": "大堂展示展位，产品展示促销",
                "min_duration_unit": "day",
                "min_duration_value": 1,
                "max_duration_value": 30,
                "advance_booking_days": 14,
                "min_capacity": 0,
                "max_capacity": 0,
                "requires_approval": True,
                "approval_type": "plan_approval",
                "approval_deadline_hours": 48,
                "requires_deposit": True,
                "deposit_percentage": 0.2,
                "standard_facilities": '["展位框架", "照明", "电源"]',
                "optional_addons": '["展架租赁", "设计服务", "促销支持"]',
                "icon": "🏪",
                "color_theme": "#10B981",
                "sort_order": 4,
            },
            {
                "type_code": "vip_dining",
                "type_name": "VIP餐厅",
                "type_name_en": "VIP Dining Room",
                "description": "VIP餐厅包厢，高端商务用餐",
                "min_duration_unit": "meal",
                "min_duration_value": 1,
                "max_duration_value": 3,
                "advance_booking_days": 3,
                "min_capacity": 6,
                "max_capacity": 12,
                "requires_approval": False,
                "standard_facilities": '["独立包厢", "专属服务", "高品质餐具", "空调"]',
                "optional_addons": '["定制菜单", "酒水服务", "司仪服务"]',
                "icon": "🍽️",
                "color_theme": "#DC2626",
                "sort_order": 5,
            },
        ]

        # 创建类型
        for type_data in default_types:
            space_type = SpaceType(**type_data)
            db.add(space_type)

        db.commit()

        print(f"✓ 成功创建 {len(default_types)} 种空间类型")

        # 显示创建结果
        types = db.query(SpaceType).order_by(SpaceType.sort_order).all()
        for t in types:
            print(f"  {t.icon} {t.type_name} ({t.type_code}) - {t.description[:20]}...")

    except Exception as e:
        print(f"✗ 初始化失败: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    init_space_types()
