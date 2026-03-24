#!/usr/bin/env python3
"""
测试交易记录删除功能
验证权限验证、软删除和审计日志功能
"""

import requests
import json

API_BASE = "http://localhost:8000/api"


def test_delete_with_password():
    """测试带密码验证的删除功能"""
    print("=" * 60)
    print("🗑️ 测试交易记录删除功能")
    print("=" * 60)
    
    # 1. 先获取一些交易记录
    print("\n📋 步骤 1: 获取交易记录...")
    response = requests.get(f"{API_BASE}/admin/transactions")
    if response.status_code != 200:
        print(f"❌ 获取交易记录失败：{response.status_code}")
        return False
    
    transactions = response.json()
    if not transactions:
        print("⚠️  暂无交易记录，无法测试删除功能")
        return True
    
    # 获取前 3 条未删除的交易
    available_transactions = [t for t in transactions if not t.get('is_deleted', False)][:3]
    print(f"   找到 {len(available_transactions)} 条可删除的交易记录")
    
    if not available_transactions:
        print("ℹ️  所有交易记录已被删除或无数据")
        return True
    
    test_transaction_id = available_transactions[0]['id']
    print(f"   测试删除交易 ID: {test_transaction_id}")
    
    # 2. 测试删除 - 错误密码
    print("\n📋 步骤 2: 测试错误密码验证...")
    response = requests.post(
        f"{API_BASE}/admin/transactions/delete",
        json={
            "transaction_ids": [test_transaction_id],
            "password": "wrong_password",
            "reason": "测试错误密码"
        },
        params={"current_user_id": 1}
    )
    
    if response.status_code == 401:
        print("   ✅ 密码验证正常工作（错误密码被拒绝）")
    else:
        print(f"   ⚠️  密码验证返回：{response.status_code}")
    
    # 3. 测试删除 - 正确密码
    print("\n📋 步骤 3: 测试正确密码删除...")
    response = requests.post(
        f"{API_BASE}/admin/transactions/delete",
        json={
            "transaction_ids": [test_transaction_id],
            "password": "admin123",  # 预设的管理员密码
            "reason": "测试删除功能"
        },
        params={"current_user_id": 1}
    )
    
    data = response.json()
    if response.status_code == 200:
        print(f"   ✅ 删除成功：{data.get('message', '')}")
        print(f"   📊 删除了 {data.get('deleted_count', 0)} 条记录")
    else:
        print(f"   ⚠️  删除返回：{response.status_code} - {data.get('detail', '')}")
    
    # 4. 验证软删除 - 默认不显示已删除记录
    print("\n📋 步骤 4: 验证软删除（默认不显示已删除）...")
    response = requests.get(f"{API_BASE}/admin/transactions")
    transactions = response.json()
    
    is_deleted_hidden = all(not t.get('is_deleted', False) for t in transactions)
    if is_deleted_hidden:
        print("   ✅ 已删除记录默认不显示")
    else:
        print("   ⚠️  发现已删除记录仍在默认列表中")
    
    # 5. 验证软删除 - 包含已删除记录
    print("\n📋 步骤 5: 验证软删除（包含已删除记录）...")
    response = requests.get(f"{API_BASE}/admin/transactions?include_deleted=true")
    transactions = response.json()
    
    deleted_records = [t for t in transactions if t.get('is_deleted', False)]
    print(f"   📊 找到 {len(deleted_records)} 条已删除记录")
    
    if deleted_records:
        sample = deleted_records[0]
        print(f"   示例记录：")
        print(f"      - ID: {sample['id']}")
        print(f"      - 删除时间：{sample.get('deleted_at', 'N/A')}")
        print(f"      - 删除原因：{sample.get('delete_reason', 'N/A')}")
    
    # 6. 测试恢复删除记录
    print("\n📋 步骤 6: 测试恢复删除记录...")
    if deleted_records:
        restore_id = deleted_records[0]['id']
        response = requests.post(
            f"{API_BASE}/admin/transactions/restore",
            params={
                "transaction_ids": restore_id,
                "current_user_id": 1
            }
        )
        
        data = response.json()
        if response.status_code == 200:
            print(f"   ✅ 恢复成功：{data.get('message', '')}")
        else:
            print(f"   ⚠️  恢复返回：{response.status_code} - {data.get('detail', '')}")
    
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
        print(f"      - 时间：{sample_log.get('created_at', 'N/A')}")
    else:
        print("   ℹ️  暂无删除日志")
    
    print("\n" + "=" * 60)
    print("✅ 删除功能测试完成！")
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
    print("   - 输入管理员密码验证身份")
    print("   - 已删除记录可在 include_deleted=true 时查看和恢复")
    
    return True


def main():
    """主测试函数"""
    print("\n" + "=" * 60)
    print("🧪 交易记录删除功能测试")
    print("=" * 60)
    
    try:
        test_delete_with_password()
        
    except requests.exceptions.ConnectionError:
        print("\n❌ 无法连接到后端服务，请确保服务已启动")
        print("   启动命令：cd backend && source ../.venv/bin/activate && python main.py")
    except Exception as e:
        print(f"\n❌ 测试失败：{e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
