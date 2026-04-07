#!/usr/bin/env python3
"""
完整流程测试：用户注册 → 管理员审核 → 用户登录
验证整个生命周期是否正确实现
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"


class Colors:
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    END = "\033[0m"
    BOLD = "\033[1m"


def print_step(step_num, description):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'=' * 60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}步骤 {step_num}: {description}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'=' * 60}{Colors.END}\n")


def print_success(message):
    print(f"{Colors.GREEN}✓ {message}{Colors.END}")


def print_error(message):
    print(f"{Colors.RED}✗ {message}{Colors.END}")


def print_warning(message):
    print(f"{Colors.YELLOW}⚠ {message}{Colors.END}")


def print_info(message):
    print(f"  {message}")


def test_complete_flow():
    """测试完整的用户注册→审核→登录流程"""

    print(f"\n{Colors.BOLD}用户注册→审核→登录完整流程测试{Colors.END}")
    print(f"测试时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")

    # 生成唯一用户名
    timestamp = int(time.time())
    test_username = f"flow_test_{timestamp}"
    test_password = "Test@123456"
    test_phone = f"138{timestamp % 100000000:08d}"

    print_info(f"测试用户名: {test_username}")
    print_info(f"测试密码: {test_password}")

    # ========== 步骤1: 内部用户注册 ==========
    print_step(1, "内部用户注册")

    try:
        response = requests.post(
            f"{BASE_URL}/api/user/register",
            json={
                "name": test_username,
                "password": test_password,
                "user_type": "internal",
                "department": "测试部门",
            },
        )

        if response.status_code == 200:
            data = response.json()
            print_success(f"注册成功")
            print_info(f"用户ID: {data.get('user_id')}")
            print_info(f"状态: {data.get('status')}")
            print_info(f"消息: {data.get('message')}")

            if data.get("status") == "pending_activation":
                print_success("状态正确：待激活")
            else:
                print_error(
                    f"状态错误：应该是pending_activation，实际是{data.get('status')}"
                )
                return False
        else:
            print_error(f"注册失败: {response.status_code}")
            print_info(response.text)
            return False

    except Exception as e:
        print_error(f"注册异常: {str(e)}")
        return False

    # ========== 步骤2: 尝试登录（应该失败） ==========
    print_step(2, "尝试登录（未激活状态）")

    try:
        response = requests.post(
            f"{BASE_URL}/api/user/login",
            json={"name": test_username, "password": test_password},
        )

        if response.status_code == 403:
            print_success("登录被正确拒绝（账户未激活）")

            try:
                error_data = response.json()
                print_info(f"错误信息: {error_data.get('detail')}")
            except:
                print_info(f"响应: {response.text}")
        elif response.status_code == 200:
            print_error("登录成功！这是错误的，账户应该未激活")
            return False
        else:
            print_warning(f"意外的响应状态: {response.status_code}")
            print_info(response.text)

    except Exception as e:
        print_error(f"登录测试异常: {str(e)}")
        return False

    # ========== 步骤3: 管理员查看待激活用户 ==========
    print_step(3, "管理员查看待激活用户")

    try:
        # 登录管理员账号
        admin_login = requests.post(
            f"{BASE_URL}/api/user/login", json={"name": "admin", "password": "admin123"}
        )

        if admin_login.status_code != 200:
            print_warning("无法登录管理员账号，跳过此步骤")
        else:
            print_success("管理员登录成功")

            # 查询待激活用户
            response = requests.get(f"{BASE_URL}/api/users?is_active=0")

            if response.status_code == 200:
                inactive_users = response.json()
                print_success(f"找到 {len(inactive_users)} 个待激活用户")

                # 检查我们的测试用户是否在列表中
                found = any(u.get("name") == test_username for u in inactive_users)
                if found:
                    print_success(f"测试用户 '{test_username}' 在待激活列表中")
                else:
                    print_warning(f"测试用户 '{test_username}' 未在待激活列表中")
            else:
                print_error(f"查询失败: {response.status_code}")

    except Exception as e:
        print_warning(f"管理员操作异常: {str(e)}")

    # ========== 步骤4: 管理员激活用户 ==========
    print_step(4, "管理员激活用户")

    try:
        # 获取用户ID
        user_list = requests.get(f"{BASE_URL}/api/users?search={test_username}")

        if user_list.status_code != 200:
            print_error("无法获取用户列表")
            return False

        users = user_list.json()
        test_user = next((u for u in users if u.get("name") == test_username), None)

        if not test_user:
            print_error("未找到测试用户")
            return False

        user_id = test_user.get("id")
        print_info(f"用户ID: {user_id}")

        # 激活用户
        activate_response = requests.post(f"{BASE_URL}/api/users/{user_id}/activate")

        if activate_response.status_code == 200:
            data = activate_response.json()
            print_success("激活成功")
            print_info(f"消息: {data.get('message')}")
        else:
            print_error(f"激活失败: {activate_response.status_code}")
            print_info(activate_response.text)
            return False

    except Exception as e:
        print_error(f"激活操作异常: {str(e)}")
        return False

    # ========== 步骤5: 验证激活状态 ==========
    print_step(5, "验证用户已激活")

    try:
        # 查询用户状态
        user_list = requests.get(f"{BASE_URL}/api/users?search={test_username}")
        users = user_list.json()
        test_user = next((u for u in users if u.get("name") == test_username), None)

        if test_user and test_user.get("is_active") == 1:
            print_success("用户状态已更新为已激活")
            print_info(f"is_active: {test_user.get('is_active')}")
        else:
            print_error("用户状态未正确更新")
            print_info(
                f"is_active: {test_user.get('is_active') if test_user else 'N/A'}"
            )
            return False

    except Exception as e:
        print_error(f"状态验证异常: {str(e)}")
        return False

    # ========== 步骤6: 用户登录（应该成功） ==========
    print_step(6, "用户登录（已激活状态）")

    try:
        response = requests.post(
            f"{BASE_URL}/api/user/login",
            json={"name": test_username, "password": test_password},
        )

        if response.status_code == 200:
            data = response.json()
            print_success("登录成功！")
            print_info(f"用户: {data.get('user_info', {}).get('name')}")
            print_info(f"角色: {data.get('user_info', {}).get('role_name')}")
            print_info(f"用户类型: {data.get('user_info', {}).get('user_type')}")
            print_info(f"Token已生成: {data.get('access_token')[:50]}...")

            return True
        else:
            print_error(f"登录失败: {response.status_code}")
            print_info(response.text)
            return False

    except Exception as e:
        print_error(f"登录异常: {str(e)}")
        return False


def test_external_user_flow():
    """测试外部用户流程（应该自动激活）"""

    print(f"\n{Colors.BOLD}外部用户流程测试（自动激活）{Colors.END}\n")

    timestamp = int(time.time())
    test_username = f"ext_test_{timestamp}"
    test_password = "Test@123456"
    test_phone = f"139{timestamp % 100000000:08d}"

    print_step(1, "外部用户注册")

    try:
        response = requests.post(
            f"{BASE_URL}/api/user/register",
            json={
                "name": test_username,
                "password": test_password,
                "user_type": "external",
                "phone": test_phone,
                "email": f"{test_username}@test.com",
            },
        )

        if response.status_code == 200:
            data = response.json()
            print_success("注册成功")
            print_info(f"状态: {data.get('status')}")

            if data.get("status") == "active":
                print_success("外部用户自动激活正确")
            else:
                print_error("外部用户应该自动激活")
                return False
        else:
            print_error(f"注册失败")
            return False

    except Exception as e:
        print_error(f"注册异常: {str(e)}")
        return False

    print_step(2, "外部用户立即登录（无需审核）")

    try:
        response = requests.post(
            f"{BASE_URL}/api/user/login",
            json={"name": test_username, "password": test_password},
        )

        if response.status_code == 200:
            print_success("外部用户登录成功（自动激活流程正确）")
            return True
        else:
            print_error("外部用户登录失败")
            return False

    except Exception as e:
        print_error(f"登录异常: {str(e)}")
        return False


def main():
    print("=" * 60)
    print("完整流程测试")
    print("=" * 60)

    # 测试服务
    try:
        response = requests.get(f"{BASE_URL}/api/health", timeout=5)
        if response.status_code != 200:
            print("服务未运行")
            return
    except:
        print("无法连接服务")
        return

    # 测试内部用户流程
    internal_result = test_complete_flow()

    # 测试外部用户流程
    external_result = test_external_user_flow()

    # 总结
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'=' * 60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}测试总结{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'=' * 60}{Colors.END}\n")

    if internal_result:
        print_success("内部用户流程：注册→审核→激活→登录 ✓")
    else:
        print_error("内部用户流程：存在问题 ✗")

    if external_result:
        print_success("外部用户流程：注册→自动激活→登录 ✓")
    else:
        print_error("外部用户流程：存在问题 ✗")

    print()
    if internal_result and external_result:
        print(f"{Colors.GREEN}{Colors.BOLD}✓ 完整流程测试全部通过！{Colors.END}")
    else:
        print(f"{Colors.RED}{Colors.BOLD}✗ 流程存在问题，需要修复{Colors.END}")

    print("=" * 60)


if __name__ == "__main__":
    main()
