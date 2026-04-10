"""
仓库测试
测试Repository层的数据访问功能
"""

import pytest
from repositories import UserRepository, ProductRepository, TransactionRepository
from models import User, Product, ProductCategory, Transaction


class TestUserRepository:
    """用户仓库测试"""

    def test_create_user(self, db_session):
        """测试创建用户"""
        repo = UserRepository(db_session)

        user_data = {"name": "test_user", "department": "技术部", "role": "staff"}

        user = repo.create(user_data)

        assert user.id is not None
        assert user.name == "test_user"

    def test_get_by_name(self, db_session):
        """测试根据用户名获取用户"""
        repo = UserRepository(db_session)

        user = repo.create(
            {"name": "unique_name", "department": "部门1", "role": "staff"}
        )

        found_user = repo.get_by_name("unique_name")

        assert found_user is not None
        assert found_user.id == user.id

    def test_get_by_department(self, db_session):
        """测试根据部门获取用户"""
        repo = UserRepository(db_session)

        repo.create({"name": "user1", "department": "技术部", "role": "staff"})
        repo.create({"name": "user2", "department": "技术部", "role": "staff"})
        repo.create({"name": "user3", "department": "市场部", "role": "staff"})

        tech_users = repo.get_by_department("技术部")

        assert len(tech_users) == 2

    def test_update_user(self, db_session):
        """测试更新用户"""
        repo = UserRepository(db_session)

        user = repo.create(
            {"name": "update_user", "department": "部门1", "role": "staff"}
        )

        updated_user = repo.update(user.id, {"department": "新部门"})

        assert updated_user.department == "新部门"

    def test_delete_user(self, db_session):
        """测试删除用户"""
        repo = UserRepository(db_session)

        user = repo.create(
            {"name": "delete_user", "department": "部门1", "role": "staff"}
        )

        success = repo.delete(user.id)

        assert success is True
        assert repo.get(user.id) is None


class TestProductRepository:
    """产品仓库测试"""

    def test_create_product(self, db_session):
        """测试创建产品"""
        category_repo = ProductRepository(db_session)
        category = category_repo.create_category(
            {"name": "分类1", "service_type": "water"}
        )

        repo = ProductRepository(db_session)

        product = repo.create(
            {
                "name": "产品1",
                "category_id": category.id,
                "price": 100.0,
                "service_type": "water",
            }
        )

        assert product.id is not None
        assert product.name == "产品1"

    def test_get_active_products(self, db_session):
        """测试获取活跃产品"""
        repo = ProductRepository(db_session)

        category = repo.create_category({"name": "分类1", "service_type": "water"})

        repo.create(
            {
                "name": "产品1",
                "category_id": category.id,
                "price": 100.0,
                "service_type": "water",
                "is_active": 1,
            }
        )

        repo.create(
            {
                "name": "产品2",
                "category_id": category.id,
                "price": 200.0,
                "service_type": "water",
                "is_active": 0,
            }
        )

        active_products = repo.get_active_products()

        assert len(active_products) == 1

    def test_update_stock(self, db_session):
        """测试更新库存"""
        repo = ProductRepository(db_session)

        category = repo.create_category({"name": "分类1", "service_type": "water"})

        product = repo.create(
            {
                "name": "产品1",
                "category_id": category.id,
                "price": 100.0,
                "service_type": "water",
                "stock": 50,
            }
        )

        success = repo.update_stock(product.id, 100)

        assert success is True
        updated_product = repo.get(product.id)
        assert updated_product.stock == 100


class TestTransactionRepository:
    """交易仓库测试"""

    def test_create_transaction(self, db_session):
        """测试创建交易"""
        user_repo = UserRepository(db_session)
        user = user_repo.create(
            {"name": "user1", "department": "部门1", "role": "staff"}
        )

        product_repo = ProductRepository(db_session)
        category = product_repo.create_category(
            {"name": "分类1", "service_type": "water"}
        )
        product = product_repo.create(
            {
                "name": "产品1",
                "category_id": category.id,
                "price": 100.0,
                "service_type": "water",
            }
        )

        repo = TransactionRepository(db_session)

        transaction = repo.create(
            {
                "user_id": user.id,
                "product_id": product.id,
                "quantity": 2,
                "actual_price": 200.0,
                "type": "pickup",
            }
        )

        assert transaction.id is not None

    def test_get_by_user(self, db_session):
        """测试根据用户获取交易"""
        user_repo = UserRepository(db_session)
        user1 = user_repo.create(
            {"name": "user1", "department": "部门1", "role": "staff"}
        )
        user2 = user_repo.create(
            {"name": "user2", "department": "部门1", "role": "staff"}
        )

        product_repo = ProductRepository(db_session)
        category = product_repo.create_category(
            {"name": "分类1", "service_type": "water"}
        )
        product = product_repo.create(
            {
                "name": "产品1",
                "category_id": category.id,
                "price": 100.0,
                "service_type": "water",
            }
        )

        repo = TransactionRepository(db_session)

        repo.create(
            {
                "user_id": user1.id,
                "product_id": product.id,
                "quantity": 1,
                "actual_price": 100.0,
            }
        )

        repo.create(
            {
                "user_id": user1.id,
                "product_id": product.id,
                "quantity": 2,
                "actual_price": 200.0,
            }
        )

        repo.create(
            {
                "user_id": user2.id,
                "product_id": product.id,
                "quantity": 3,
                "actual_price": 300.0,
            }
        )

        user1_transactions = repo.get_by_user(user1.id)

        assert len(user1_transactions) == 2
