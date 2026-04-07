"""
用户服务
处理用户相关的业务逻辑
"""

from typing import List, Optional
from sqlalchemy.orm import Session

from repositories.user_repository import UserRepository
from models.user import User
from utils.password import hash_password, verify_password


class UserService:
    """用户服务"""

    def __init__(self, db: Session):
        self.db = db
        self.user_repo = UserRepository(db)

    def get_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        """获取用户列表"""
        return self.user_repo.get_multi(skip, limit)

    def get_user(self, user_id: int) -> Optional[User]:
        """获取单个用户"""
        return self.user_repo.get(user_id)

    def get_user_by_name(self, name: str) -> Optional[User]:
        """根据用户名获取用户"""
        return self.user_repo.get_by_name(name)

    def get_users_by_department(self, department: str) -> List[User]:
        """根据部门获取用户列表"""
        return self.user_repo.get_by_department(department)

    def get_users_by_role(self, role: str) -> List[User]:
        """根据角色获取用户列表"""
        return self.user_repo.get_by_role(role)

    def get_active_users(self) -> List[User]:
        """获取所有活跃用户"""
        return self.user_repo.get_active_users()

    def search_users(self, keyword: str) -> List[User]:
        """搜索用户"""
        return self.user_repo.search(keyword)

    def create_user(
        self, name: str, department: str, role: str = "staff", password: str = None
    ) -> User:
        """
        创建用户

        Args:
            name: 用户名
            department: 部门
            role: 角色
            password: 密码（可选）

        Returns:
            创建的用户实例
        """
        if self.user_repo.name_exists(name):
            raise ValueError(f"用户名 '{name}' 已存在")

        user_data = {
            "name": name,
            "department": department,
            "role": role,
            "is_active": 1,
        }

        if password:
            user_data["password_hash"] = hash_password(password)

        return self.user_repo.create(user_data)

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
            if self.user_repo.name_exists(user_data["name"], exclude_id=user_id):
                raise ValueError(f"用户名 '{user_data['name']}' 已存在")

        return self.user_repo.update(user_id, user_data)

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
        user = self.user_repo.get(user_id)
        if not user:
            return False

        if user.password_hash and not verify_password(old_password, user.password_hash):
            raise ValueError("旧密码不正确")

        password_hash = hash_password(new_password)
        return self.user_repo.update_password(user_id, password_hash)

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
        return self.user_repo.update_password(user_id, password_hash)

    def update_balance(self, user_id: int, amount: float) -> bool:
        """
        更新用户余额

        Args:
            user_id: 用户ID
            amount: 变动金额（可正可负）

        Returns:
            是否更新成功
        """
        user = self.user_repo.get(user_id)
        if not user:
            return False

        new_balance = user.balance_credit + amount
        if new_balance < 0:
            raise ValueError("余额不足")

        return self.user_repo.update_balance(user_id, amount)

    def deactivate_user(self, user_id: int) -> bool:
        """停用用户"""
        return self.user_repo.deactivate(user_id)

    def activate_user(self, user_id: int) -> bool:
        """激活用户"""
        return self.user_repo.activate(user_id)

    def delete_user(self, user_id: int) -> bool:
        """
        删除用户

        Args:
            user_id: 用户ID

        Returns:
            是否删除成功
        """
        user = self.user_repo.get(user_id)
        if not user:
            return False

        return self.user_repo.delete(user_id)

    def authenticate(self, name: str, password: str) -> Optional[User]:
        """
        用户认证

        Args:
            name: 用户名
            password: 密码

        Returns:
            认证成功返回用户实例，否则返回None
        """
        user = self.user_repo.get_by_name(name)
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
        user = self.user_repo.get(user_id)
        return user is not None and user.role == "admin"
