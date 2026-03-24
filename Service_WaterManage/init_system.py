#!/usr/bin/env python3
"""
初始化系统 - 创建超级管理员并设置密码
Usage: python init_system.py
"""

import sys
import os
import secrets

# 切换到 backend 目录
os.chdir(os.path.join(os.path.dirname(__file__), 'backend'))

from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, func
from sqlalchemy.orm import sessionmaker, declarative_base
from datetime import datetime
import bcrypt

SQLALCHEMY_DATABASE_URL = "sqlite:///./waterms.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)
    department = Column(String, nullable=False)
    role = Column(String, default="staff")
    password_hash = Column(String, nullable=True)
    balance_credit = Column(Float, default=0)
    is_active = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.now)


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def init_system():
    """初始化系统"""
    print("=" * 60)
    print("🔧 系统初始化")
    print("=" * 60)
    
    # 创建表
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    try:
        # 1. 检查是否已有超级管理员
        super_admin = db.query(User).filter(User.role == "super_admin").first()
        
        if super_admin:
            print("\n✅ 超级管理员已存在")
            print(f"   用户名：{super_admin.name}")
            print(f"   部门：{super_admin.department}")
        else:
            # 2. 创建超级管理员
            print("\n📝 创建超级管理员...")
            
            # 生成随机初始密码
            initial_password = secrets.token_urlsafe(8)
            
            super_admin = User(
                name="admin",
                department="IT",
                role="super_admin",
                password_hash=hash_password(initial_password),
                is_active=1
            )
            
            db.add(super_admin)
            db.commit()
            db.refresh(super_admin)
            
            print("\n✅ 超级管理员创建成功！")
            print(f"   用户名：admin")
            print(f"   初始密码：{initial_password}")
            print(f"\n⚠️  重要：请立即登录系统修改密码！")
        
        # 3. 检查其他管理员
        admins = db.query(User).filter(User.role == "admin").all()
        if admins:
            print(f"\n📋 当前有 {len(admins)} 个普通管理员")
        else:
            print(f"\nℹ️  暂无普通管理员")
        
        # 4. 用户统计
        total_users = db.query(User).count()
        print(f"\n📊 用户统计：")
        print(f"   总用户数：{total_users}")
        
        roles = db.query(User.role, func.count(User.id)).group_by(User.role).all()
        for role, count in roles:
            print(f"   - {role}: {count} 人")
        
        print("\n" + "=" * 60)
        print("✅ 系统初始化完成！")
        print("=" * 60)
        
        print("\n📋 使用说明：")
        print("   1. 使用超级管理员账号登录系统")
        print("   2. 立即修改超级管理员密码")
        print("   3. 创建普通管理员账号")
        print("   4. 为员工创建普通账号")
        
        print("\n🔐 角色权限说明：")
        print("   - super_admin: 删除/恢复交易记录 + 用户管理 + 密码管理")
        print("   - admin:       删除/恢复交易记录")
        print("   - staff:       只读权限（查看、领取）")
        
    finally:
        db.close()


if __name__ == "__main__":
    init_system()
