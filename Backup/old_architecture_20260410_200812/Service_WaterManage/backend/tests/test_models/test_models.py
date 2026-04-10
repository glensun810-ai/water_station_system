"""
模型测试
测试数据模型的创建和基本功能
"""

import pytest
from datetime import datetime
from models import User, Product, ProductCategory, Transaction


class TestUserModel:
    """用户模型测试"""

    def test_create_user(self, db_session):
        """测试创建用户"""
        user = User(name="test_user", department="技术部", role="staff", is_active=1)

        db_session.add(user)
        db_session.commit()

        assert user.id is not None
        assert user.name == "test_user"
        assert user.department == "技术部"
        assert user.role == "staff"
        assert user.is_active == 1
        assert user.balance_credit == 0
        assert user.created_at is not None

    def test_user_unique_name(self, db_session):
        """测试用户名唯一性"""
        user1 = User(name="unique_user", department="部门1", role="staff")
        user2 = User(name="unique_user", department="部门2", role="staff")

        db_session.add(user1)
        db_session.commit()

        db_session.add(user2)

        with pytest.raises(Exception):  # 应该抛出唯一性约束异常
            db_session.commit()


class TestProductModel:
    """产品模型测试"""

    def test_create_product(self, db_session):
        """测试创建产品"""
        category = ProductCategory(name="测试分类", service_type="water")
        db_session.add(category)
        db_session.commit()

        product = Product(
            name="测试产品",
            category_id=category.id,
            price=100.0,
            service_type="water",
            stock=50,
            is_active=1,
        )

        db_session.add(product)
        db_session.commit()

        assert product.id is not None
        assert product.name == "测试产品"
        assert product.price == 100.0
        assert product.stock == 50
        assert product.is_active == 1

    def test_product_category_relationship(self, db_session):
        """测试产品与分类的关系"""
        category = ProductCategory(name="分类1", service_type="water")
        db_session.add(category)
        db_session.commit()

        product = Product(
            name="产品1", category_id=category.id, price=50.0, service_type="water"
        )
        db_session.add(product)
        db_session.commit()

        assert product.category_id == category.id


class TestTransactionModel:
    """交易模型测试"""

    def test_create_transaction(self, db_session):
        """测试创建交易"""
        user = User(name="user1", department="部门1", role="staff")
        db_session.add(user)

        category = ProductCategory(name="分类1", service_type="water")
        db_session.add(category)

        product = Product(
            name="产品1", category_id=category.id, price=100.0, service_type="water"
        )
        db_session.add(product)
        db_session.commit()

        transaction = Transaction(
            user_id=user.id,
            product_id=product.id,
            quantity=2,
            actual_price=200.0,
            type="pickup",
            status="unsettled",
        )

        db_session.add(transaction)
        db_session.commit()

        assert transaction.id is not None
        assert transaction.user_id == user.id
        assert transaction.product_id == product.id
        assert transaction.quantity == 2
        assert transaction.status == "unsettled"
        assert transaction.is_deleted == 0
