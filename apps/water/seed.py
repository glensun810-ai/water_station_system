"""
Seed Data Script - 初始化演示数据
Run: python seed.py
"""
from main import engine, Base, SessionLocal, User, Product, Transaction
from datetime import datetime, timedelta
import random

def init_db():
    """Create database tables"""
    Base.metadata.create_all(bind=engine)
    print("✓ 数据库表已创建")


def seed_data():
    """Insert demo data"""
    db = SessionLocal()
    
    try:
        # Check if data already exists
        if db.query(User).count() > 0:
            print("⚠ 数据库已有数据，跳过初始化")
            db.close()
            return
        
        # 1. Create Products (水规格)
        products = [
            Product(
                name="桶装水",
                specification="18L",
                unit="桶",
                price=15.0,
                stock=50,
                promo_threshold=10,
                promo_gift=1
            ),
            Product(
                name="瓶装水",
                specification="500ml",
                unit="瓶",
                price=2.0,
                stock=200,
                promo_threshold=20,
                promo_gift=2
            ),
            Product(
                name="中桶水",
                specification="12L",
                unit="桶",
                price=10.0,
                stock=30,
                promo_threshold=15,
                promo_gift=1
            )
        ]
        db.add_all(products)
        db.commit()
        print(f"✓ 已创建 {len(products)} 个产品规格")
        
        # 2. Create Users (不同办公室的同事)
        users = [
            User(name="张三", department="研发部", role="staff"),
            User(name="李四", department="研发部", role="staff"),
            User(name="王五", department="行政部", role="staff"),
            User(name="赵六", department="行政部", role="staff"),
            User(name="钱七", department="销售部", role="staff"),
            User(name="孙八", department="销售部", role="staff"),
            User(name="周九", department="财务部", role="staff"),
            User(name="吴十", department="财务部", role="staff"),
            User(name="管理员", department="后勤部", role="admin")
        ]
        db.add_all(users)
        db.commit()
        print(f"✓ 已创建 {len(users)} 个用户")
        
        # 3. Create some sample transactions (模拟历史领取记录)
        base_date = datetime.now() - timedelta(days=15)
        sample_transactions = []
        
        # Generate random transactions for demonstration
        for i in range(30):
            user = random.choice(users[:-1])  # Exclude admin
            product = random.choice(products)
            days_ago = random.randint(0, 14)
            transaction_date = base_date + timedelta(days=days_ago)
            
            # Calculate if this transaction should be free (买 10 赠 1)
            count = sum(1 for t in sample_transactions 
                       if t.user_id == user.id 
                       and t.product_id == product.id 
                       and t.actual_price > 0)
            
            cycle = product.promo_threshold + product.promo_gift
            is_free = (count + 1) % cycle == 0
            actual_price = 0 if is_free else product.price
            
            note = f"买{product.promo_threshold}赠{product.promo_gift}" if is_free else None
            
            transaction = Transaction(
                user_id=user.id,
                product_id=product.id,
                quantity=1,
                actual_price=actual_price,
                type="pickup",
                status="unsettled" if random.random() > 0.3 else "settled",
                note=note,
                created_at=transaction_date
            )
            sample_transactions.append(transaction)
        
        db.add_all(sample_transactions)
        db.commit()
        print(f"✓ 已创建 {len(sample_transactions)} 条模拟交易记录")
        
        print("\n" + "="*50)
        print("🎉 演示数据初始化完成！")
        print("="*50)
        print("\n测试账号:")
        print("  用户：张三 (研发部) - ID: 1")
        print("  用户：李四 (研发部) - ID: 2")
        print("  管理员：管理员 - ID: 9")
        print("\n产品规格:")
        print("  桶装水 18L - ¥15/桶 (买 10 赠 1)")
        print("  瓶装水 500ml - ¥2/瓶 (买 20 赠 2)")
        print("  中桶水 12L - ¥10/桶 (买 15 赠 1)")
        print("\n启动服务:")
        print("  cd backend && python main.py")
        print("\n访问页面:")
        print("  用户端：frontend/index.html")
        print("  管理端：frontend/admin.html")
        
    except Exception as e:
        db.rollback()
        print(f"✗ 初始化失败：{e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    init_db()
    seed_data()
