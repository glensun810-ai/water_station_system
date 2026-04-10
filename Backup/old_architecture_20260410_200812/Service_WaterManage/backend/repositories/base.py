"""
基础仓库类
提供通用的CRUD操作
"""

from typing import TypeVar, Generic, Type, List, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import text

from models.base import Base

# 泛型类型
ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """基础仓库类"""

    def __init__(self, model: Type[ModelType], db: Session):
        """
        初始化仓库

        Args:
            model: 模型类
            db: 数据库会话
        """
        self.model = model
        self.db = db

    def create(self, obj_in: dict) -> ModelType:
        """
        创建记录

        Args:
            obj_in: 创建数据

        Returns:
            创建的模型实例
        """
        db_obj = self.model(**obj_in)
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def get(self, id: int) -> Optional[ModelType]:
        """
        根据ID获取记录

        Args:
            id: 记录ID

        Returns:
            模型实例或None
        """
        return self.db.query(self.model).filter(self.model.id == id).first()

    def get_multi(
        self, skip: int = 0, limit: int = 100, filters: dict = None
    ) -> List[ModelType]:
        """
        获取多条记录

        Args:
            skip: 跳过记录数
            limit: 返回记录数
            filters: 过滤条件

        Returns:
            模型实例列表
        """
        query = self.db.query(self.model)

        if filters:
            for key, value in filters.items():
                if hasattr(self.model, key):
                    query = query.filter(getattr(self.model, key) == value)

        return query.offset(skip).limit(limit).all()

    def update(self, id: int, obj_in: dict) -> Optional[ModelType]:
        """
        更新记录

        Args:
            id: 记录ID
            obj_in: 更新数据

        Returns:
            更新后的模型实例或None
        """
        db_obj = self.get(id)
        if not db_obj:
            return None

        for key, value in obj_in.items():
            if hasattr(db_obj, key):
                setattr(db_obj, key, value)

        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def delete(self, id: int) -> bool:
        """
        删除记录

        Args:
            id: 记录ID

        Returns:
            是否删除成功
        """
        db_obj = self.get(id)
        if not db_obj:
            return False

        self.db.delete(db_obj)
        self.db.commit()
        return True

    def count(self, filters: dict = None) -> int:
        """
        统计记录数

        Args:
            filters: 过滤条件

        Returns:
            记录数
        """
        query = self.db.query(self.model)

        if filters:
            for key, value in filters.items():
                if hasattr(self.model, key):
                    query = query.filter(getattr(self.model, key) == value)

        return query.count()

    def exists(self, id: int) -> bool:
        """
        检查记录是否存在

        Args:
            id: 记录ID

        Returns:
            是否存在
        """
        return self.get(id) is not None

    def execute_raw_sql(self, sql: str, params: dict = None) -> Any:
        """
        执行原生SQL

        Args:
            sql: SQL语句
            params: 参数

        Returns:
            执行结果
        """
        return self.db.execute(text(sql), params or {})
