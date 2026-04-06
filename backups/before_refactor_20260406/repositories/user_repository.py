"""
用户仓库
处理用户相关的数据访问
"""

from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import or_

from repositories.base import BaseRepository
from models.user import User


class UserRepository(BaseRepository[User]):
    """用户仓库"""

    def __init__(self, db: Session):
        super().__init__(User, db)

    def get_by_name(self, name: str) -> Optional[User]:
        """
        根据用户名获取用户

        Args:
            name: 用户名

        Returns:
            用户实例或None
        """
        return self.db.query(User).filter(User.name == name).first()

    def get_by_department(self, department: str) -> List[User]:
        """
        根据部门获取用户列表

        Args:
            department: 部门名称

        Returns:
            用户列表
        """
        return self.db.query(User).filter(User.department == department).all()

    def get_active_users(self) -> List[User]:
        """
        获取所有活跃用户

        Returns:
            活跃用户列表
        """
        return self.db.query(User).filter(User.is_active == 1).all()

    def get_by_role(self, role: str) -> List[User]:
        """
        根据角色获取用户列表

        Args:
            role: 角色名称

        Returns:
            用户列表
        """
        return self.db.query(User).filter(User.role == role).all()

    def name_exists(self, name: str, exclude_id: int = None) -> bool:
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

    def search(self, keyword: str) -> List[User]:
        """
        搜索用户（按名称或部门）

        Args:
            keyword: 搜索关键词

        Returns:
            用户列表
        """
        return (
            self.db.query(User)
            .filter(or_(User.name.contains(keyword), User.department.contains(keyword)))
            .all()
        )

    def update_password(self, user_id: int, password_hash: str) -> bool:
        """
        更新用户密码

        Args:
            user_id: 用户ID
            password_hash: 密码哈希

        Returns:
            是否更新成功
        """
        user = self.get(user_id)
        if not user:
            return False

        user.password_hash = password_hash
        self.db.commit()
        return True

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

        user.balance_credit += amount
        self.db.commit()
        return True

    def deactivate(self, user_id: int) -> bool:
        """
        停用用户

        Args:
            user_id: 用户ID

        Returns:
            是否停用成功
        """
        return self.update(user_id, {"is_active": 0}) is not None

    def activate(self, user_id: int) -> bool:
        """
        激活用户

        Args:
            user_id: 用户ID

        Returns:
            是否激活成功
        """
        return self.update(user_id, {"is_active": 1}) is not None
