"""
Test Package Management API endpoints
Phase 3: Package Management Feature Testing
"""

import sys
import os

backend_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "backend")
)
sys.path.insert(0, backend_path)

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_list_packages():
    """Test listing all packages"""
    response = client.get("/api/packages")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    print(f"✓ Listed {len(data)} packages")

    if len(data) > 0:
        pkg = data[0]
        assert "id" in pkg
        assert "name" in pkg
        assert "original_price" in pkg
        assert "package_price" in pkg
        assert "status" in pkg
        print(f"  Package: {pkg['name']} - ¥{pkg['package_price']}")


def test_get_package():
    """Test getting single package details"""
    response = client.get("/api/packages")
    packages = response.json()

    if len(packages) > 0:
        pkg_id = packages[0]["id"]
        response = client.get(f"/api/packages/{pkg_id}")
        assert response.status_code == 200
        pkg = response.json()
        assert pkg["id"] == pkg_id
        print(f"✓ Retrieved package #{pkg_id}: {pkg['name']}")

        if pkg.get("items"):
            print(f"  Contains {len(pkg['items'])} items")


def test_create_package():
    """Test creating a new package"""
    new_package = {
        "name": "测试套餐",
        "description": "这是一个测试套餐",
        "original_price": 1000.00,
        "package_price": 800.00,
        "discount_rate": 80.00,
        "valid_days": 30,
        "status": "active",
        "sort_order": 10,
        "items": [
            {
                "service_type": "meeting_room",
                "product_name": "会议室",
                "quantity": 5,
                "unit": "小时",
                "unit_price": 100.00,
                "subtotal": 500.00,
            },
            {
                "service_type": "tea_break",
                "product_name": "茶歇服务",
                "quantity": 10,
                "unit": "人次",
                "unit_price": 50.00,
                "subtotal": 500.00,
            },
        ],
    }

    response = client.post("/api/packages", json=new_package)
    assert response.status_code == 200
    pkg = response.json()
    assert pkg["name"] == "测试套餐"
    assert pkg["original_price"] == 1000.00
    assert pkg["package_price"] == 800.00
    print(f"✓ Created package #{pkg['id']}: {pkg['name']}")
    print(f"  Contains {len(pkg.get('items', []))} items")

    return pkg["id"]


def test_update_package(pkg_id):
    """Test updating a package"""
    update_data = {
        "name": "测试套餐（已更新）",
        "description": "这是更新后的测试套餐",
        "package_price": 750.00,
        "items": [
            {
                "service_type": "meeting_room",
                "product_name": "会议室",
                "quantity": 6,
                "unit": "小时",
                "unit_price": 100.00,
                "subtotal": 600.00,
            }
        ],
    }

    response = client.put(f"/api/packages/{pkg_id}", json=update_data)
    assert response.status_code == 200
    pkg = response.json()
    assert pkg["name"] == "测试套餐（已更新）"
    assert pkg["package_price"] == 750.00
    print(f"✓ Updated package #{pkg_id}: {pkg['name']}")
    print(f"  New price: ¥{pkg['package_price']}")


def test_delete_package(pkg_id):
    """Test deleting (soft delete) a package"""
    response = client.delete(f"/api/packages/{pkg_id}")
    assert response.status_code == 200
    result = response.json()
    assert result["package_id"] == pkg_id
    print(f"✓ Deleted (soft) package #{pkg_id}")

    response = client.get(f"/api/packages/{pkg_id}")
    pkg = response.json()
    assert pkg["status"] == "inactive"
    print(f"  Status changed to: {pkg['status']}")


def test_package_stats():
    """Test package statistics"""
    response = client.get("/api/packages/stats/summary")
    assert response.status_code == 200
    stats = response.json()
    assert "packages" in stats
    assert "orders" in stats
    assert "revenue" in stats
    print(f"✓ Package statistics:")
    print(f"  Total packages: {stats['packages']['total']}")
    print(f"  Active packages: {stats['packages']['active']}")
    print(f"  Total orders: {stats['orders']['total']}")
    print(f"  Total revenue: ¥{stats['revenue']['total']}")


def test_create_package_order():
    """Test creating a package order"""
    response = client.get("/api/packages?status=active")
    packages = response.json()

    if len(packages) > 0:
        pkg_id = packages[0]["id"]

        response = client.get("/api/offices")
        offices = response.json()

        if len(offices) > 0:
            office_id = offices[0]["id"]
            office_name = offices[0]["name"]

            order_data = {
                "package_id": pkg_id,
                "office_id": office_id,
                "office_name": office_name,
                "order_user_name": "测试用户",
                "note": "这是一个测试订单",
            }

            response = client.post(f"/api/packages/{pkg_id}/order", json=order_data)
            assert response.status_code == 200
            order = response.json()
            assert order["package_id"] == pkg_id
            assert order["office_id"] == office_id
            assert order["status"] == "pending"
            print(f"✓ Created order #{order['id']}")
            print(f"  Package: {order['package_name']}")
            print(f"  Office: {order['office_name']}")
            print(f"  Saved amount: ¥{order['saved_amount']}")

            return order["id"]

    print("✗ No active packages or offices available for order test")
    return None


def test_list_orders():
    """Test listing package orders"""
    response = client.get("/api/packages/orders/list")
    assert response.status_code == 200
    orders = response.json()
    assert isinstance(orders, list)
    print(f"✓ Listed {len(orders)} orders")


def test_update_order_status(order_id):
    """Test updating order status"""
    if order_id:
        response = client.put(f"/api/packages/orders/{order_id}/status?status=active")
        assert response.status_code == 200
        result = response.json()
        assert result["order_id"] == order_id
        assert result["status"] == "active"
        print(f"✓ Updated order #{order_id} status to active")


def run_tests():
    """Run all tests"""
    print("=" * 60)
    print("Package Management API Test Suite")
    print("=" * 60)
    print()

    try:
        print("1. Listing packages...")
        test_list_packages()
        print()

        print("2. Getting package details...")
        test_get_package()
        print()

        print("3. Creating new package...")
        pkg_id = test_create_package()
        print()

        print("4. Updating package...")
        test_update_package(pkg_id)
        print()

        print("5. Package statistics...")
        test_package_stats()
        print()

        print("6. Creating package order...")
        order_id = test_create_package_order()
        print()

        print("7. Listing orders...")
        test_list_orders()
        print()

        print("8. Updating order status...")
        test_update_order_status(order_id)
        print()

        print("9. Deleting package...")
        test_delete_package(pkg_id)
        print()

        print("=" * 60)
        print("All tests passed! ✓")
        print("=" * 60)

    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        import traceback

        traceback.print_exc()
        return False

    return True


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
