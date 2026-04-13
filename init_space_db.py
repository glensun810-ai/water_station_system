"""
初始化Space服务数据库表
"""

from sqlalchemy import create_engine
from models.base import Base

# 导入所有space相关的模型（确保它们被注册到Base.metadata）
from shared.models.space.space_type import SpaceType
from shared.models.space.space_resource import SpaceResource
from shared.models.space.space_booking import SpaceBooking
from shared.models.space.space_approval import SpaceApproval
from shared.models.space.space_payment import SpacePayment
from shared.models.space.space_settlement import SpaceSettlement
from shared.models.space.notification import Notification
from shared.models.space.user_member_info import UserMemberInfo
from shared.models.space.user_space_quota import UserSpaceQuota

# 使用主数据库
engine = create_engine("sqlite:///./data/app.db", echo=True)

# 创建所有表
Base.metadata.create_all(bind=engine)

print("✓ Space服务数据库表创建完成")

# 验证表是否创建成功
from sqlalchemy import inspect

inspector = inspect(engine)
tables = inspector.get_table_names()
space_tables = [t for t in tables if "space" in t]
print(f"✓ 已创建的space相关表: {space_tables}")
