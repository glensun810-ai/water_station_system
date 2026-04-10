"""
会议室用户模型
会议室系统独立用户模型，支持内部用户和外部用户
"""

from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime

from models.base import Base, TimestampMixin


class User(Base, TimestampMixin):
    """
    会议室用户表

    角色说明：
    - super_admin: 超级管理员，系统最高权限
    - admin: 系统管理员，管理整个会议室系统
    - office_admin: 办公室管理员，管理特定办公室（department字段指定）
    - user: 普通用户，使用会议室服务的员工

    用户类型：
    - internal: 内部用户（集群员工）
    - external: 外部用户（外部企业/个人）
    """

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), nullable=False, unique=True)
    name = Column(String(100), nullable=False)
    department = Column(String(100), nullable=True)
    department_id = Column(Integer, nullable=True)
    role = Column(String(50), default="user")
    user_type = Column(String(20), default="internal")
    password_hash = Column(String(255), nullable=True)
    phone = Column(String(20), nullable=True)
    email = Column(String(100), nullable=True)
    company = Column(String(100), nullable=True)
    balance_credit = Column(Float, default=0)
    is_active = Column(Integer, default=1)
