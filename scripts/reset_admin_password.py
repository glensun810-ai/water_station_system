#!/usr/bin/env python3
"""
Admin账号密码重置工具
用于重置admin账号密码并解锁账号
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.user import User
from utils.password import hash_password
from datetime import datetime
import sqlite3


def reset_admin_password(password="admin123"):
    """重置admin账号密码"""
    engine = create_engine("sqlite:///./data/app.db")
    Session = sessionmaker(bind=engine)
    db = Session()

    # 获取admin用户
    admin = db.query(User).filter(User.username == "admin").first()

    if admin:
        # 重置密码
        admin.password_hash = hash_password(password)
        admin.last_login = datetime.now()
        db.commit()
        print(f"✅ Admin密码已重置为: {password}")

        # 清除账号锁定和登录尝试记录
        conn = sqlite3.connect("data/app.db")
        conn.execute("DELETE FROM account_lockouts WHERE username='admin'")
        conn.execute("DELETE FROM login_attempts WHERE username='admin'")
        conn.commit()
        conn.close()
        print("✅ Admin账号锁定已清除")

        return True
    else:
        print("❌ Admin用户不存在")
        return False

    db.close()


if __name__ == "__main__":
    import sys

    # 默认密码为admin123
    password = sys.argv[1] if len(sys.argv) > 1 else "admin123"

    print(f"\n重置Admin密码为: {password}")
    success = reset_admin_password(password)

    if success:
        print("\n使用方法:")
        print(f"  用户名: admin")
        print(f"  密码: {password}")
        print("\n请使用此密码登录系统。")
    else:
        print("\n密码重置失败，请检查数据库连接。")
