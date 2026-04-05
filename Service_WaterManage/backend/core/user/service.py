"""
用户管理服务 - 核心域
提供用户管理的核心业务逻辑
"""

from typing import List, Optional
from sqlalchemy.orm import Session

from services.base import BaseService
from models.user import User
from utils.password import hash_password, verify_password


class UserService(BaseService[User]):
    """用户服务 - 核心域"""

    def __init__(self, db: Session):
        super().__init__(User, db)

    def get_by_name(self, name: str) -> Optional[User]:
        """根据用户名获取用户"""
        return self.db.query(User).filter(User.name == name).first()

    def get_by_department(
        self, department: str, skip: int = 0, limit: int = 100
    ) -> List[User]:
        """根据部门获取用户列表"""
        return (
            self.db.query(User)
            .filter(User.department == department)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_role(self, role: str, skip: int = 0, limit: int = 100) -> List[User]:
        """根据角色获取用户列表"""
        return (
            self.db.query(User)
            .filter(User.role == role)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_active_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        """获取所有活跃用户"""
        return (
            self.db.query(User)
            .filter(User.is_active == 1)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def search_users(self, keyword: str, skip: int = 0, limit: int = 100) -> List[User]:
        """搜索用户（按名称或部门）"""
        from sqlalchemy import or_

        return (
            self.db.query(User)
            .filter(or_(User.name.contains(keyword), User.department.contains(keyword)))
            .offset(skip)
            .limit(limit)
            .all()
        )

    def create_user(
        self,
        name: str,
        department: str,
        role: str = "staff",
        password: Optional[str] = None,
        balance_credit: float = 0.0,
    ) -> User:
        """
        创建用户

        Args:
            name: 用户名
            department: 部门
            role: 角色
            password: 密码（可选）
            balance_credit: 初始余额

        Returns:
            创建的用户实例
        """
        if self.name_exists(name):
            raise ValueError(f"用户名 '{name}' 已存在")

        user_data = {
            "name": name,
            "department": department,
            "role": role,
            "balance_credit": balance_credit,
            "is_active": 1,
        }

        if password:
            user_data["password_hash"] = hash_password(password)

        return self.create(user_data)

    def update_user(self, user_id: int, user_data: dict) -> Optional[User]:
        """
        更新用户信息

        Args:
            user_id: 用户ID
            user_data: 更新数据

        Returns:
            更新后的用户实例
        """
        if "name" in user_data:
            if self.name_exists(user_data["name"], exclude_id=user_id):
                raise ValueError(f"用户名 '{user_data['name']}' 已存在")

        return self.update(user_id, user_data)

    def update_password(
        self, user_id: int, old_password: str, new_password: str
    ) -> bool:
        """
        更新用户密码

        Args:
            user_id: 用户ID
            old_password: 旧密码
            new_password: 新密码

        Returns:
            是否更新成功
        """
        user = self.get(user_id)
        if not user:
            return False

        if user.password_hash and not verify_password(old_password, user.password_hash):
            raise ValueError("旧密码不正确")

        password_hash = hash_password(new_password)
        return self.update(user_id, {"password_hash": password_hash}) is not None

    def reset_password(self, user_id: int, new_password: str) -> bool:
        """
        重置用户密码（管理员操作）

        Args:
            user_id: 用户ID
            new_password: 新密码

        Returns:
            是否重置成功
        """
        password_hash = hash_password(new_password)
        return self.update(user_id, {"password_hash": password_hash}) is not None

    def update_balance(self, user_id: int, amount: float) -> bool:
        """
        更新用户余额

        Args:
            user_id: 用户ID
            amount: 变动金额（可正可负）

        Returns:
            是否更新成功
        """
        user = self.get(user_id)
        if not user:
            return False

        new_balance = user.balance_credit + amount
        if new_balance < 0:
            raise ValueError("余额不足")

        return self.update(user_id, {"balance_credit": new_balance}) is not None

    def deactivate_user(self, user_id: int) -> bool:
        """停用用户"""
        return self.update(user_id, {"is_active": 0}) is not None

    def activate_user(self, user_id: int) -> bool:
        """激活用户"""
        return self.update(user_id, {"is_active": 1}) is not None

    def authenticate(self, name: str, password: str) -> Optional[User]:
        """
        用户认证

        Args:
            name: 用户名
            password: 密码

        Returns:
            认证成功返回用户实例，否则返回None
        """
        user = self.get_by_name(name)
        if not user:
            return None

        if not user.is_active:
            return None

        if not user.password_hash:
            return None

        if not verify_password(password, user.password_hash):
            return None

        return user

    def is_admin(self, user_id: int) -> bool:
        """
        检查用户是否为管理员

        Args:
            user_id: 用户ID

        Returns:
            是否为管理员
        """
        user = self.get(user_id)
        return user is not None and user.role == "admin"

    def name_exists(self, name: str, exclude_id: Optional[int] = None) -> bool:
        """
        检查用户名是否已存在

        Args:
            name: 用户名
            exclude_id: 排除的用户ID（用于更新时检查）

        Returns:
            是否存在
        """
        query = self.db.query(User).filter(User.name == name)
        if exclude_id:
            query = query.filter(User.id != exclude_id)
        return query.first() is not None
