"""
服务基类
提供通用的数据库会话管理和业务逻辑封装
"""

from typing import TypeVar, Generic, Type, List, Optional, Any
from sqlalchemy.orm import Session
from config.database import get_db

ModelType = TypeVar("ModelType", bound=Any)


class BaseService(Generic[ModelType]):
    """
    服务基类

    提供通用的CRUD操作和业务逻辑封装

    用法:
        class UserService(BaseService[User]):
            def __init__(self, db: Session):
                super().__init__(User, db)
    """

    def __init__(self, model: Type[ModelType], db: Session):
        """
        初始化服务

        Args:
            model: 数据模型类
            db: 数据库会话
        """
        self.model = model
        self.db = db

    def get(self, id: int) -> Optional[ModelType]:
        """根据ID获取单个实体"""
        return self.db.query(self.model).filter(self.model.id == id).first()

    def get_multi(self, skip: int = 0, limit: int = 100, **filters) -> List[ModelType]:
        """获取多个实体"""
        query = self.db.query(self.model)

        # 应用过滤器
        for key, value in filters.items():
            if hasattr(self.model, key) and value is not None:
                query = query.filter(getattr(self.model, key) == value)

        return query.offset(skip).limit(limit).all()

    def create(self, obj_in: dict) -> ModelType:
        """创建实体"""
        db_obj = self.model(**obj_in)
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def update(self, id: int, obj_in: dict) -> Optional[ModelType]:
        """更新实体"""
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
        """删除实体"""
        db_obj = self.get(id)
        if not db_obj:
            return False

        self.db.delete(db_obj)
        self.db.commit()
        return True

    def count(self, **filters) -> int:
        """统计实体数量"""
        query = self.db.query(self.model)

        for key, value in filters.items():
            if hasattr(self.model, key) and value is not None:
                query = query.filter(getattr(self.model, key) == value)

        return query.count()
