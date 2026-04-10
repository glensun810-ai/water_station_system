"""
数据保护脚本
用途：系统发布时，一键保护所有真实业务数据

使用方法：
    python protect_data.py

执行后：
- 所有产品标记为 is_protected=1（受保护）
- 所有交易记录标记为 is_protected=1（受保护）
- 受保护的数据无法被删除

恢复测试：
    python protect_data.py --reset

执行后：
- 解除所有数据的保护状态
- 恢复可删除状态（测试用）
"""

import sys
import argparse
from main import SessionLocal, Product, Transaction


def protect_all_data():
    """保护所有数据"""
    db = SessionLocal()
    try:
        # 保护所有产品
        products = db.query(Product).all()
        for p in products:
            p.is_protected = 1
        print(f"✓ 已保护 {len(products)} 个产品")

        # 保护所有交易记录
        transactions = db.query(Transaction).all()
        for t in transactions:
            t.is_protected = 1
        print(f"✓ 已保护 {len(transactions)} 条交易记录")

        db.commit()
        print("\n🎉 数据保护完成！所有数据已受保护，无法删除。")
        print("\n发布前准备已完成，系统可以正式发布使用。")

    except Exception as e:
        db.rollback()
        print(f"✗ 错误: {e}")
        raise
    finally:
        db.close()


def reset_protection():
    """解除所有数据保护（测试用）"""
    db = SessionLocal()
    try:
        # 解除产品保护
        products = db.query(Product).all()
        for p in products:
            p.is_protected = 0
        print(f"✓ 已解除 {len(products)} 个产品的保护")

        # 解除交易记录保护
        transactions = db.query(Transaction).all()
        for t in transactions:
            t.is_protected = 0
        print(f"✓ 已解除 {len(transactions)} 条交易记录的保护")

        db.commit()
        print("\n🎉 数据保护已解除，可以正常删除数据（测试用）。")

    except Exception as e:
        db.rollback()
        print(f"✗ 错误: {e}")
        raise
    finally:
        db.close()


def show_status():
    """显示数据保护状态"""
    db = SessionLocal()
    try:
        # 产品状态
        total_products = db.query(Product).count()
        protected_products = db.query(Product).filter(Product.is_protected == 1).count()
        unprotected_products = total_products - protected_products

        print("=== 产品保护状态 ===")
        print(f"  总计: {total_products}")
        print(f"  已保护: {protected_products}")
        print(f"  未保护: {unprotected_products}")

        # 交易记录状态
        total_transactions = db.query(Transaction).count()
        protected_transactions = (
            db.query(Transaction).filter(Transaction.is_protected == 1).count()
        )
        unprotected_transactions = total_transactions - protected_transactions

        print("\n=== 交易记录保护状态 ===")
        print(f"  总计: {total_transactions}")
        print(f"  已保护: {protected_transactions}")
        print(f"  未保护: {unprotected_transactions}")

    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="数据保护脚本")
    parser.add_argument("--status", action="store_true", help="显示保护状态")
    parser.add_argument("--reset", action="store_true", help="解除所有保护（测试用）")

    args = parser.parse_args()

    if args.status:
        show_status()
    elif args.reset:
        confirm = input(
            "确定要解除所有数据保护吗？这将允许删除所有数据（测试用）。\n输入 'yes' 继续: "
        )
        if confirm.lower() == "yes":
            reset_protection()
        else:
            print("已取消操作")
    else:
        protect_all_data()
