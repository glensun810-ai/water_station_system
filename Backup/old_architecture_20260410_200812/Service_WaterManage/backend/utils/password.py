"""
密码管理工具
提供密码哈希、验证等功能
"""

import bcrypt
import secrets
import string
from typing import Tuple

from config.settings import settings


class PasswordManager:
    """密码管理器"""

    @staticmethod
    def hash_password(password: str) -> str:
        """
        使用bcrypt哈希密码

        Args:
            password: 明文密码

        Returns:
            哈希后的密码
        """
        return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """
        验证密码

        Args:
            plain_password: 明文密码
            hashed_password: 哈希密码

        Returns:
            是否匹配
        """
        try:
            return bcrypt.checkpw(
                plain_password.encode("utf-8"), hashed_password.encode("utf-8")
            )
        except Exception:
            return False

    @staticmethod
    def generate_random_password(length: int = 16) -> str:
        """
        生成随机密码

        Args:
            length: 密码长度

        Returns:
            随机密码
        """
        alphabet = string.ascii_letters + string.digits + string.punctuation
        password = "".join(secrets.choice(alphabet) for _ in range(length))
        return password

    @staticmethod
    def validate_password_strength(password: str) -> Tuple[bool, str]:
        """
        验证密码强度

        Args:
            password: 密码

        Returns:
            (是否通过, 错误信息)
        """
        if len(password) < settings.MIN_PASSWORD_LENGTH:
            return False, f"密码长度至少{settings.MIN_PASSWORD_LENGTH}位"

        if settings.REQUIRE_SPECIAL_CHAR:
            if not any(c in string.punctuation for c in password):
                return False, "密码必须包含特殊字符"

        if settings.REQUIRE_NUMBER:
            if not any(c.isdigit() for c in password):
                return False, "密码必须包含数字"

        return True, ""

    @staticmethod
    def get_default_password() -> str:
        """
        获取默认密码

        Returns:
            默认密码
        """
        # ⚠️ 警告：仅用于初始化，生产环境必须修改！
        return settings.DEFAULT_ADMIN_PASSWORD


# 全局密码管理器实例
password_manager = PasswordManager()


# 便捷函数
def hash_password(password: str) -> str:
    """哈希密码"""
    return password_manager.hash_password(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return password_manager.verify_password(plain_password, hashed_password)


def generate_random_password(length: int = 16) -> str:
    """生成随机密码"""
    return password_manager.generate_random_password(length)


def validate_password_strength(password: str) -> Tuple[bool, str]:
    """验证密码强度"""
    return password_manager.validate_password_strength(password)
