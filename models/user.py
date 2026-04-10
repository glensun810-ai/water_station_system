"""
用户相关模型
"""

from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime

from models.base import Base


class User(Base):
    """
    用户表

    角色说明：
    - super_admin: 超级管理员，系统最高权限
    - admin: 系统管理员，管理整个系统
    - office_admin: 办公室管理员，管理特定办公室（department字段指定）
    - user: 普通用户，使用服务的员工

    department字段说明：
    - 存储用户所属的办公室名称（不是部门）
    - office_admin角色的用户，此字段表示其管理的办公室
    """

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), nullable=False, unique=True)
    name = Column(String(100), nullable=True)
    department = Column(String(100), nullable=True, comment="所属办公室名称")
    role = Column(
        String(50), default="user", comment="角色：super_admin/admin/office_admin/user"
    )
    password_hash = Column(String(255), nullable=True)
    balance_credit = Column(Float, default=0)
    is_active = Column(Integer, default=1)
    user_type = Column(
        String(20), default="internal", comment="用户类型：internal/external"
    )
    phone = Column(String(20), nullable=True, comment="手机号")
    email = Column(String(100), nullable=True, comment="邮箱")
    company = Column(String(100), nullable=True, comment="公司名称")
    last_login = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    @property
    def role_name(self):
        role_names = {
            "super_admin": "超级管理员",
            "admin": "管理员",
            "office_admin": "办公室管理员",
            "user": "普通用户",
        }
        return role_names.get(self.role, "普通用户")

    transactions = relationship(
        "Transaction", foreign_keys="Transaction.user_id", back_populates="user"
    )
    notifications = relationship("Notification", back_populates="user")
