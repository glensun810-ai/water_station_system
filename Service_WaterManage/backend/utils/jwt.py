"""
JWT Token管理工具
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import jwt, JWTError

from config.settings import settings


class JWTManager:
    """JWT Token管理器"""

    @staticmethod
    def create_access_token(
        data: Dict[str, Any], expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        创建JWT Token

        Args:
            data: 要编码的数据（通常包含用户ID和角色）
            expires_delta: 过期时间增量

        Returns:
            JWT Token字符串
        """
        to_encode = data.copy()

        if expires_delta:
            expire = datetime.now() + expires_delta
        else:
            expire = datetime.now() + timedelta(
                hours=settings.ACCESS_TOKEN_EXPIRE_HOURS
            )

        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(
            to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
        )
        return encoded_jwt

    @staticmethod
    def verify_token(token: str) -> Optional[Dict[str, Any]]:
        """
        验证JWT Token

        Args:
            token: JWT Token字符串

        Returns:
            解码后的payload，失败返回None
        """
        try:
            payload = jwt.decode(
                token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
            )
            return payload
        except JWTError:
            return None

    @staticmethod
    def get_user_id_from_token(token: str) -> Optional[int]:
        """
        从Token中提取用户ID

        Args:
            token: JWT Token

        Returns:
            用户ID，失败返回None
        """
        payload = JWTManager.verify_token(token)
        if not payload:
            return None

        user_id = payload.get("sub")
        if not user_id:
            return None

        try:
            return int(user_id)
        except (ValueError, TypeError):
            return None


# 全局JWT管理器实例
jwt_manager = JWTManager()


# 便捷函数
def create_access_token(
    data: Dict[str, Any], expires_delta: Optional[timedelta] = None
) -> str:
    """创建JWT Token"""
    return jwt_manager.create_access_token(data, expires_delta)


def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """验证JWT Token"""
    return jwt_manager.verify_token(token)


def get_user_id_from_token(token: str) -> Optional[int]:
    """从Token中提取用户ID"""
    return jwt_manager.get_user_id_from_token(token)
