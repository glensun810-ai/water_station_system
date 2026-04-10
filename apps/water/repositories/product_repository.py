"""
产品仓库
处理产品相关的数据访问
"""

from typing import List, Optional
from sqlalchemy.orm import Session

from repositories.base import BaseRepository
from models.product import Product, ProductCategory


class ProductRepository(BaseRepository[Product]):
    """产品仓库"""

    def __init__(self, db: Session):
        super().__init__(Product, db)

    def get_by_name(self, name: str) -> Optional[Product]:
        """根据名称获取产品"""
        return self.db.query(Product).filter(Product.name == name).first()

    def get_by_category(
        self, category_id: int, skip: int = 0, limit: int = 100
    ) -> List[Product]:
        """根据分类获取产品列表"""
        return (
            self.db.query(Product)
            .filter(Product.category_id == category_id, Product.is_active == 1)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_active_products(self, skip: int = 0, limit: int = 100) -> List[Product]:
        """获取所有活跃产品"""
        return (
            self.db.query(Product)
            .filter(Product.is_active == 1)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_service_type(
        self, service_type: str, skip: int = 0, limit: int = 100
    ) -> List[Product]:
        """根据服务类型获取产品"""
        return (
            self.db.query(Product)
            .filter(Product.service_type == service_type, Product.is_active == 1)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def search(self, keyword: str, skip: int = 0, limit: int = 100) -> List[Product]:
        """搜索产品"""
        return (
            self.db.query(Product)
            .filter(Product.name.contains(keyword), Product.is_active == 1)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def update_stock(self, product_id: int, quantity: int) -> bool:
        """更新库存"""
        product = self.get(product_id)
        if not product:
            return False

        product.stock += quantity
        self.db.commit()
        return True

    def decrease_stock(self, product_id: int, quantity: int) -> bool:
        """减少库存"""
        product = self.get(product_id)
        if not product or product.stock < quantity:
            return False

        product.stock -= quantity
        self.db.commit()
        return True


class ProductCategoryRepository(BaseRepository[ProductCategory]):
    """产品分类仓库"""

    def __init__(self, db: Session):
        super().__init__(ProductCategory, db)

    def get_by_name(self, name: str) -> Optional[ProductCategory]:
        """根据名称获取分类"""
        return (
            self.db.query(ProductCategory).filter(ProductCategory.name == name).first()
        )

    def get_all_categories(self) -> List[ProductCategory]:
        """获取所有分类"""
        return self.db.query(ProductCategory).all()
