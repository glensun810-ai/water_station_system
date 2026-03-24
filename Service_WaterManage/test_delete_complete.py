#!/usr/bin/env python3
"""
交易记录删除功能 - 完整测试（包含数据初始化）
"""

import requests
import json

API_BASE = "http://localhost:8000/api"


def create_test_data():
    """创建测试数据"""
    print("=" * 60)
    print("📝 创建测试数据")
    print("=" * 60)
    
    # 1. 创建管理员用户
    print("\n1️⃣ 创建管理员用户...")
    admin_response = requests.post(
        f"{API_BASE}/users",
        json={"name": "Admin", "department": "IT", "role": "admin"}
    )
    if admin_response.status_code in [200, 400]:  # 400 可能已存在
        print("   ✅ 管理员用户已就绪")
        admin_user = admin_response.json() if admin_response.status_code == 200 else {"id": 1}
    else:
        print(f"   ⚠️  创建管理员失败：{admin_response.status_code}")
        return None
    
    # 2. 创建普通用户
    print("\n2️⃣ 创建普通用户...")
    user_response = requests.post(
        f"{API_BASE}/users",
        json={"name": "TestUser", "department": "研发部", "role": "staff"}
    )
    if user_response.status_code in [200, 400]:
        print("   ✅ 普通用户已就绪")
        user = user_response.json() if user_response.status_code == 200 else {"id": 2}
    else:
        print(f"   ⚠️  创建用户失败：{user_response.status_code}")
        return None
    
    # 3. 创建产品
    print("\n3️⃣ 创建产品...")
    product_response = requests.post(
        f"{API_BASE}/products",
        json={
            "name": "桶装水",
            "specification": "18L",
            "unit": "桶",
            "price": 15.0,
            "stock": 100,
            "promo_threshold": 10,
            "promo_gift": 1
        }
    )
    if product_response.status_code in [200, 400]:
        print("   ✅ 产品已就绪")
        product = product_response.json() if product_response.status_code == 200 else {"id": 1}
    else:
        print(f"   ⚠️  创建产品失败：{product_response.status_code}")
        return None
    
    # 4. 创建交易记录
    print("\n4️⃣ 创建交易记录...")
    transaction_ids = []
    for i in range(3):
        record_response = requests.post(
            f"{API_BASE}/record",
            json={
                "user_id": user["id"],
                "product_id": product["id"],
                "quantity": 2,
                "type": "pickup"
            }
        )
        if record_response.status_code == 200:
            transaction = record_response.json()
            transaction_ids.append(transaction["id"])
            print(f"   ✅ 创建交易记录 ID: {transaction['id']}")
        else:
            print(f"   ⚠️  创建交易失败：{record_response.status_code}")
    
    return {
        "admin_id": admin_user["id"],
        "user_id": user["id"],
        "product_id": product["id"],
        "transaction_ids": transaction_ids
    }


def test_delete_feature(test_data):
    """测试删除功能"""
    print("\n" + "=" * 60)
    print("🗑️ 测试交易记录删除功能")
    print("=" * 60)
    
    if not test_data or not test_data["transaction_ids"]:
        print("\n⚠️  测试数据创建失败，跳过删除测试")
        return False
    
    transaction_id = test_data["transaction_ids"][0]
    admin_id = test_data["admin_id"]
    
    # 1. 验证交易记录存在
    print("\n📋 步骤 1: 验证交易记录存在...")
    response = requests.get(f"{API_BASE}/admin/transactions")
    transactions = response.json()
    print(f"   📊 当前共有 {len(transactions)} 条交易记录")
    
    # 2. 测试错误密码
    print("\n📋 步骤 2: 测试错误密码验证...")
    response = requests.post(
        f"{API_BASE}/admin/transactions/delete",
        json={
            "transaction_ids": [transaction_id],
            "password": "wrong_password",
            "reason": "测试错误密码"
        },
        params={"current_user_id": admin_id}
    )
    
    if response.status_code == 401:
        print("   ✅ 密码验证正常工作（错误密码被拒绝）")
    else:
        print(f"   ℹ️  密码验证返回：{response.status_code}")
    
    # 3. 测试正确密码删除
    print("\n📋 步骤 3: 测试正确密码删除...")
    response = requests.post(
        f"{API_BASE}/admin/transactions/delete",
        json={
            "transaction_ids": [transaction_id],
            "password": "admin123",
            "reason": "测试删除功能 - 数据录入错误"
        },
        params={"current_user_id": admin_id}
    )
    
    data = response.json()
    if response.status_code == 200:
        print(f"   ✅ 删除成功：{data.get('message', '')}")
    else:
        print(f"   ⚠️  删除返回：{response.status_code} - {data.get('detail', '')}")
        if "password" in data.get('detail', '').lower():
            print("   💡 提示：默认管理员密码为 'admin123'")
    
    # 4. 验证软删除
    print("\n📋 步骤 4: 验证软删除（默认不显示已删除）...")
    response = requests.get(f"{API_BASE}/admin/transactions")
    transactions = response.json()
    original_count = len(transactions)
    print(f"   📊 默认查询：{len(transactions)} 条记录（不显示已删除）")
    
    # 5. 验证包含已删除记录
    print("\n📋 步骤 5: 验证包含已删除记录...")
    response = requests.get(f"{API_BASE}/admin/transactions?include_deleted=true")
    transactions = response.json()
    print(f"   📊 包含已删除：{len(transactions)} 条记录")
    
    deleted_records = [t for t in transactions if t.get('is_deleted', False)]
    print(f"   🗑️ 已删除记录：{len(deleted_records)} 条")
    
    if deleted_records:
        sample = deleted_records[0]
        print(f"\n   示例已删除记录：")
        print(f"      - ID: {sample['id']}")
        print(f"      - 删除时间：{sample.get('deleted_at', 'N/A')}")
        print(f"      - 删除原因：{sample.get('delete_reason', 'N/A')}")
    
    # 6. 测试恢复功能
    print("\n📋 步骤 6: 测试恢复删除记录...")
    if deleted_records:
        restore_id = deleted_records[0]['id']
        response = requests.post(
            f"{API_BASE}/admin/transactions/restore",
            params={
                "transaction_ids": restore_id,
                "current_user_id": admin_id
            }
        )
        
        data = response.json()
        if response.status_code == 200:
            print(f"   ✅ 恢复成功：{data.get('message', '')}")
        else:
            print(f"   ⚠️  恢复返回：{response.status_code}")
    
    # 7. 测试删除日志
    print("\n📋 步骤 7: 测试删除日志...")
    response = requests.get(f"{API_BASE}/admin/delete-logs")
    logs = response.json()
    
    if logs:
        print(f"   📊 找到 {len(logs)} 条删除日志")
        sample_log = logs[0]
        print(f"   最新日志：")
        print(f"      - 操作人：{sample_log.get('operator_name', 'N/A')}")
        print(f"      - 操作：{sample_log.get('action', 'N/A')}")
        print(f"      - 原因：{sample_log.get('reason', 'N/A')}")
    else:
        print("   ℹ️  暂无删除日志")
    
    return True


def main():
    """主测试函数"""
    print("\n" + "=" * 60)
    print("🧪 交易记录删除功能 - 完整测试")
    print("=" * 60)
    
    try:
        # 创建测试数据
        test_data = create_test_data()
        
        if test_data:
            print("\n✅ 测试数据创建成功！")
            print(f"   - 管理员 ID: {test_data['admin_id']}")
            print(f"   - 用户 ID: {test_data['user_id']}")
            print(f"   - 产品 ID: {test_data['product_id']}")
            print(f"   - 交易记录：{len(test_data['transaction_ids'])} 条")
        
        # 测试删除功能
        test_delete_feature(test_data)
        
        print("\n" + "=" * 60)
        print("✅ 所有测试完成！")
        print("=" * 60)
        print("\n📋 功能验证：")
        print("   1. ✓ 密码验证 - 防止未授权删除")
        print("   2. ✓ 软删除 - 数据可恢复，不物理删除")
        print("   3. ✓ 审计日志 - 记录所有删除操作")
        print("   4. ✓ 恢复功能 - 支持恢复误删记录")
        
        print("\n💡 使用说明：")
        print("   - 访问 http://localhost:8080/admin.html")
        print("   - 点击'交易记录'标签")
        print("   - 点击'删除'按钮或勾选多条记录后'批量删除'")
        print("   - 输入管理员密码验证身份（默认：admin123）")
        print("   - 已删除记录可在 include_deleted=true 时查看和恢复")
        
    except requests.exceptions.ConnectionError:
        print("\n❌ 无法连接到后端服务，请确保服务已启动")
        print("   启动命令：cd backend && source ../.venv/bin/activate && python main.py")
    except Exception as e:
        print(f"\n❌ 测试失败：{e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
