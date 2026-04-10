"""
数据库初始化脚本
创建所有必要的表
"""

from sqlalchemy import create_engine
from models.base import Base
from models import *

engine = create_engine("sqlite:///./data/app.db", echo=True)

Base.metadata.create_all(bind=engine)

print("数据库初始化完成")
