"""
办公室管理员关联模型
支持一个办公室配置多个管理员
"""

from sqlalchemy import Column, Integer, DateTime, UniqueConstraint
from datetime import datetime

from models.base import Base


class OfficeAdminRelation(Base):
    """
    办公室管理员关联表

    支持一个办公室有多个管理员
    管理员可以是负责人，也可以是指定的行政对接人等
    """

    __tablename__ = "office_admin_relations"
    __table_args__ = (
        UniqueConstraint("office_id", "user_id", name="unique_office_admin"),
    )

    id = Column(Integer, primary_key=True, index=True)
    office_id = Column(Integer, nullable=False, index=True, comment="办公室ID")
    user_id = Column(Integer, nullable=False, index=True, comment="管理员用户ID")
    is_primary = Column(Integer, default=0, comment="是否主要管理员(负责人)")
    role_type = Column(
        Integer, default=1, comment="管理员类型: 1=负责人 2=行政对接人 3=其他"
    )
    created_at = Column(DateTime, default=datetime.now)

    # 关系定义需要在使用时动态导入避免循环引用
