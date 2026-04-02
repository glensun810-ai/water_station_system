"""
产品服务
处理产品相关的业务逻辑
"""

from typing import List, Optional
from sqlalchemy.orm import Session

from repositories.product_repository import ProductRepository, ProductCategoryRepository
from models.product import Product, ProductCategory


class ProductService:
    """产品服务"""

    def __init__(self, db: Session):
        self.db = db
        self.product_repo = ProductRepository(db)
        self.category_repo = ProductCategoryRepository(db)

    def get_products(self, skip: int = 0, limit: int = 100) -> List[Product]:
        """获取产品列表"""
        return self.product_repo.get_active_products(skip, limit)

    def get_product(self, product_id: int) -> Optional[Product]:
        """获取单个产品"""
        return self.product_repo.get(product_id)

    def get_products_by_category(
        self, category_id: int, skip: int = 0, limit: int = 100
    ) -> List[Product]:
        """根据分类获取产品"""
        return self.product_repo.get_by_category(category_id, skip, limit)

    def get_products_by_service_type(
        self, service_type: str, skip: int = 0, limit: int = 100
    ) -> List[Product]:
        """根据服务类型获取产品"""
        return self.product_repo.get_by_service_type(service_type, skip, limit)

    def search_products(
        self, keyword: str, skip: int = 0, limit: int = 100
    ) -> List[Product]:
        """搜索产品"""
        return self.product_repo.search(keyword, skip, limit)

    def create_product(self, product_data: dict) -> Product:
        """创建产品"""
        return self.product_repo.create(product_data)

    def update_product(self, product_id: int, product_data: dict) -> Optional[Product]:
        """更新产品"""
        return self.product_repo.update(product_id, product_data)

    def delete_product(self, product_id: int) -> bool:
        """删除产品（软删除）"""
        return self.product_repo.update(product_id, {"is_active": 0}) is not None

    def update_stock(self, product_id: int, quantity: int) -> bool:
        """更新库存"""
        return self.product_repo.update_stock(product_id, quantity)

    def decrease_stock(self, product_id: int, quantity: int) -> bool:
        """减少库存"""
        return self.product_repo.decrease_stock(product_id, quantity)

    # 分类相关方法
    def get_categories(self) -> List[ProductCategory]:
        """获取所有分类"""
        return self.category_repo.get_all_categories()

    def get_category(self, category_id: int) -> Optional[ProductCategory]:
        """获取单个分类"""
        return self.category_repo.get(category_id)

    def create_category(self, category_data: dict) -> ProductCategory:
        """创建分类"""
        return self.category_repo.create(category_data)
