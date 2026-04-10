"""
服务测试
测试Service层的业务逻辑功能
"""

import pytest
from services import UserService, ProductService, TransactionService
from models import User, Product, ProductCategory


class TestUserService:
    """用户服务测试"""

    def test_create_user(self, db_session):
        """测试创建用户"""
        service = UserService(db_session)

        user = service.create_user(name="test_user", department="技术部", role="staff")

        assert user.id is not None
        assert user.name == "test_user"

    def test_create_duplicate_user(self, db_session):
        """测试创建重复用户"""
        service = UserService(db_session)

        service.create_user(name="user1", department="部门1")

        with pytest.raises(ValueError):
            service.create_user(name="user1", department="部门2")

    def test_update_user(self, db_session):
        """测试更新用户"""
        service = UserService(db_session)

        user = service.create_user(name="update_user", department="部门1")

        updated = service.update_user(user.id, {"department": "新部门"})

        assert updated.department == "新部门"

    def test_authenticate_user(self, db_session):
        """测试用户认证"""
        service = UserService(db_session)

        service.create_user(
            name="auth_user", department="部门1", password="password123"
        )

        # 正确密码
        authenticated = service.authenticate("auth_user", "password123")
        assert authenticated is not None

        # 错误密码
        not_authenticated = service.authenticate("auth_user", "wrong_password")
        assert not_authenticated is None


class TestProductService:
    """产品服务测试"""

    def test_create_product(self, db_session):
        """测试创建产品"""
        service = ProductService(db_session)

        category = service.create_category({"name": "分类1", "service_type": "water"})

        product = service.create_product(
            {
                "name": "产品1",
                "category_id": category.id,
                "price": 100.0,
                "service_type": "water",
            }
        )

        assert product.id is not None
        assert product.name == "产品1"

    def test_update_stock(self, db_session):
        """测试更新库存"""
        service = ProductService(db_session)

        category = service.create_category({"name": "分类1", "service_type": "water"})

        product = service.create_product(
            {
                "name": "产品1",
                "category_id": category.id,
                "price": 100.0,
                "service_type": "water",
                "stock": 50,
            }
        )

        success = service.update_stock(product.id, 100)

        assert success is True

        updated = service.get_product(product.id)
        assert updated.stock == 100

    def test_decrease_stock(self, db_session):
        """测试减少库存"""
        service = ProductService(db_session)

        category = service.create_category({"name": "分类1", "service_type": "water"})

        product = service.create_product(
            {
                "name": "产品1",
                "category_id": category.id,
                "price": 100.0,
                "service_type": "water",
                "stock": 50,
            }
        )

        success = service.decrease_stock(product.id, 10)

        assert success is True

        updated = service.get_product(product.id)
        assert updated.stock == 40

    def test_search_products(self, db_session):
        """测试搜索产品"""
        service = ProductService(db_session)

        category = service.create_category({"name": "分类1", "service_type": "water"})

        service.create_product(
            {
                "name": "矿泉水",
                "category_id": category.id,
                "price": 100.0,
                "service_type": "water",
            }
        )

        service.create_product(
            {
                "name": "纯净水",
                "category_id": category.id,
                "price": 100.0,
                "service_type": "water",
            }
        )

        results = service.search_products("水")

        assert len(results) == 2


class TestTransactionService:
    """交易服务测试"""

    def test_create_transaction(self, db_session):
        """测试创建交易"""
        user_service = UserService(db_session)
        user = user_service.create_user(name="user1", department="部门1")

        product_service = ProductService(db_session)
        category = product_service.create_category(
            {"name": "分类1", "service_type": "water"}
        )
        product = product_service.create_product(
            {
                "name": "产品1",
                "category_id": category.id,
                "price": 100.0,
                "service_type": "water",
                "stock": 50,
            }
        )

        service = TransactionService(db_session)

        transaction = service.create_transaction(
            user_id=user.id, product_id=product.id, quantity=2
        )

        assert transaction.id is not None
        assert transaction.quantity == 2

        # 检查库存是否减少
        updated_product = product_service.get_product(product.id)
        assert updated_product.stock == 48

    def test_settle_transaction(self, db_session):
        """测试结算交易"""
        user_service = UserService(db_session)
        user = user_service.create_user(name="user1", department="部门1")

        product_service = ProductService(db_session)
        category = product_service.create_category(
            {"name": "分类1", "service_type": "water"}
        )
        product = product_service.create_product(
            {
                "name": "产品1",
                "category_id": category.id,
                "price": 100.0,
                "service_type": "water",
                "stock": 50,
            }
        )

        service = TransactionService(db_session)

        transaction = service.create_transaction(
            user_id=user.id, product_id=product.id, quantity=2
        )

        success = service.settle_transaction(transaction.id)

        assert success is True

        settled = service.get_transaction(transaction.id)
        assert settled.status == "settled"

    def test_get_user_transactions(self, db_session):
        """测试获取用户交易"""
        user_service = UserService(db_session)
        user = user_service.create_user(name="user1", department="部门1")

        product_service = ProductService(db_session)
        category = product_service.create_category(
            {"name": "分类1", "service_type": "water"}
        )
        product = product_service.create_product(
            {
                "name": "产品1",
                "category_id": category.id,
                "price": 100.0,
                "service_type": "water",
                "stock": 100,
            }
        )

        service = TransactionService(db_session)

        service.create_transaction(user_id=user.id, product_id=product.id, quantity=1)
        service.create_transaction(user_id=user.id, product_id=product.id, quantity=2)

        transactions = service.get_user_transactions(user.id)

        assert len(transactions) == 2
