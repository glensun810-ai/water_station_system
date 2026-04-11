"""
密码管理工具 - 国际顶级安全标准实现
提供密码哈希、验证、强度检查等功能
"""

import bcrypt
import secrets
import string
import re
from typing import Tuple, Optional
from datetime import datetime, timedelta

from config.settings import settings


class PasswordManager:
    """密码管理器 - 符合NIST和OWASP安全标准"""

    # bcrypt工作因子（推荐12-14，平衡安全性和性能）
    BCRYPT_ROUNDS = 12

    @staticmethod
    def hash_password(password: str) -> str:
        """
        使用bcrypt哈希密码（自动加盐）

        Args:
            password: 明文密码

        Returns:
            哈希后的密码字符串

        Security:
            - 使用bcrypt算法（符合OWASP推荐）
            - 自动生成随机salt
            - 工作因子12（约2^12轮计算）
        """
        if not password:
            raise ValueError("密码不能为空")

        salt = bcrypt.gensalt(rounds=PasswordManager.BCRYPT_ROUNDS)
        hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
        return hashed.decode("utf-8")

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """
        验证密码

        Args:
            plain_password: 明文密码
            hashed_password: 哈希密码

        Returns:
            是否匹配

        Security:
            - 使用bcrypt.checkpw防止时序攻击
            - 所有错误情况返回False，不泄露信息
        """
        if not plain_password or not hashed_password:
            return False

        try:
            return bcrypt.checkpw(
                plain_password.encode("utf-8"), hashed_password.encode("utf-8")
            )
        except Exception:
            return False

    @staticmethod
    def validate_password_strength(password: str) -> Tuple[bool, str]:
        """
        验证密码强度（符合NIST SP 800-63B标准）

        Args:
            password: 密码

        Returns:
            (是否通过, 错误信息)

        Rules:
            - 最少8位字符
            - 最多128位字符
            - 必须包含数字
            - 必须包含特殊字符
            - 必须包含大小写字母
            - 不允许常见弱密码
        """
        if not password:
            return False, "密码不能为空"

        if len(password) < settings.MIN_PASSWORD_LENGTH:
            return False, f"密码长度至少{settings.MIN_PASSWORD_LENGTH}位"

        if len(password) > settings.MAX_PASSWORD_LENGTH:
            return False, f"密码长度不能超过{settings.MAX_PASSWORD_LENGTH}位"

        if settings.REQUIRE_UPPERCASE:
            if not re.search(r"[A-Z]", password):
                return False, "密码必须包含大写字母"

        if settings.REQUIRE_LOWERCASE:
            if not re.search(r"[a-z]", password):
                return False, "密码必须包含小写字母"

        if settings.REQUIRE_NUMBER:
            if not re.search(r"\d", password):
                return False, "密码必须包含数字"

        if settings.REQUIRE_SPECIAL_CHAR:
            if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
                return False, "密码必须包含特殊字符"

        if PasswordManager.is_weak_password(password):
            return False, "密码过于简单，请使用更复杂的密码"

        return True, ""

    @staticmethod
    def is_weak_password(password: str) -> bool:
        """
        检查是否为常见弱密码

        Args:
            password: 密码

        Returns:
            是否为弱密码
        """
        common_weak_passwords = [
            "123456",
            "password",
            "admin",
            "letmein",
            "welcome",
            "monkey",
            "dragon",
            "master",
            "qwerty",
            "login",
            "abc123",
            "111111",
            "sunshine",
            "princess",
            "football",
            "iloveyou",
            "trustno1",
            "shadow",
            "superman",
            "michael",
            "654321",
            "123456789",
            "password1",
            "admin123",
        ]

        return password.lower() in common_weak_passwords

    @staticmethod
    def generate_random_password(length: int = 16) -> str:
        """
        生成随机强密码

        Args:
            length: 密码长度（默认16）

        Returns:
            随机密码

        Security:
            - 使用secrets模块（密码学安全的随机数）
            - 包含大小写字母、数字、特殊字符
        """
        if length < 8:
            length = 8

        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        password = "".join(secrets.choice(alphabet) for _ in range(length))

        while not PasswordManager.validate_password_strength(password)[0]:
            password = "".join(secrets.choice(alphabet) for _ in range(length))

        return password

    @staticmethod
    def needs_rehash(hashed_password: str) -> bool:
        """
        检查密码哈希是否需要重新计算

        Args:
            hashed_password: 哈希密码

        Returns:
            是否需要重新哈希

        Usage:
            - 登录成功后检查，如果工作因子低于当前标准则重新哈希
        """
        try:
            rounds = bcrypt.hashpw(b"test", hashed_password.encode("utf-8"))
            current_rounds = int(hashed_password.split("$")[2])
            return current_rounds < PasswordManager.BCRYPT_ROUNDS
        except:
            return False


password_manager = PasswordManager()


def hash_password(password: str) -> str:
    """哈希密码"""
    return password_manager.hash_password(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return password_manager.verify_password(plain_password, hashed_password)


def validate_password_strength(password: str) -> Tuple[bool, str]:
    """验证密码强度"""
    return password_manager.validate_password_strength(password)


def generate_random_password(length: int = 16) -> str:
    """生成随机密码"""
    return password_manager.generate_random_password(length)


def needs_rehash(hashed_password: str) -> bool:
    """检查是否需要重新哈希"""
    return password_manager.needs_rehash(hashed_password)
