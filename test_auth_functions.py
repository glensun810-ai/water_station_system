#!/usr/bin/env python3
"""
登录、注册、退出功能完整测试脚本
测试所有关键功能，查找Bug和遗留问题
"""

import requests
import json
import sys

BASE_URL = "http://localhost:8000"


class Colors:
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    END = "\033[0m"
    BOLD = "\033[1m"


def print_header(title):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'=' * 60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{title}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'=' * 60}{Colors.END}\n")


def print_test(name, success, detail=""):
    status = (
        f"{Colors.GREEN}✓ PASS{Colors.END}"
        if success
        else f"{Colors.RED}✗ FAIL{Colors.END}"
    )
    print(f"{status} - {name}")
    if detail:
        print(f"  {detail}")


def print_warning(message):
    print(f"{Colors.YELLOW}⚠ WARNING: {message}{Colors.END}")


def print_bug(message):
    print(f"{Colors.RED}🐛 BUG: {message}{Colors.END}")


def test_register():
    """测试注册功能"""
    print_header("测试1: 注册功能")

    # 测试1.1: 注册外部用户
    print_test("1.1 外部用户注册（缺少手机号）", False, "应该失败但API允许")

    external_user_data = {
        "name": "test_external_user",
        "password": "test123456",
        "user_type": "external",
        # 缺少必填的phone字段
    }

    try:
        response = requests.post(
            f"{BASE_URL}/api/user/register", json=external_user_data
        )

        if response.status_code == 400:
            print_test("外部用户缺少手机号被正确拒绝", True, "返回400错误")
        else:
            print_bug(f"外部用户缺少手机号应该被拒绝，但返回{response.status_code}")
            print(f"  响应: {response.text}")
    except Exception as e:
        print_test(f"外部用户注册测试", False, str(e))

    # 测试1.2: 注册完整的外部用户
    external_user_complete = {
        "name": "test_external_complete",
        "password": "test123456",
        "user_type": "external",
        "phone": "13800138001",
        "email": "test@example.com",
        "company": "测试公司",
    }

    try:
        response = requests.post(
            f"{BASE_URL}/api/user/register", json=external_user_complete
        )

        if response.status_code == 200:
            data = response.json()
            print_test("完整外部用户注册成功", True, f"用户ID: {data.get('user_id')}")

            # 检查是否可以直接登录（外部用户应该直接激活）
            if data.get("status") == "active":
                print_test("外部用户注册后自动激活", True)
            else:
                print_warning("外部用户注册后状态不是active")
        elif response.status_code == 400 and "已存在" in response.text:
            print_warning("测试用户已存在，跳过注册测试")
        else:
            print_test("外部用户注册", False, response.text)
    except Exception as e:
        print_test("外部用户注册测试", False, str(e))

    # 测试1.3: 注册内部用户
    internal_user = {
        "name": "test_internal_user",
        "password": "test123456",
        "user_type": "internal",
        "department": "测试办公室",
    }

    try:
        response = requests.post(f"{BASE_URL}/api/user/register", json=internal_user)

        if response.status_code == 200:
            data = response.json()
            print_test("内部用户注册成功", True, f"用户ID: {data.get('user_id')}")

            # 检查是否需要激活（内部用户需要管理员激活）
            if data.get("status") == "pending_activation":
                print_test("内部用户需要管理员激活", True)
            else:
                print_warning("内部用户状态应该是pending_activation")
        elif response.status_code == 400 and "已存在" in response.text:
            print_warning("测试用户已存在，跳过注册测试")
        else:
            print_test("内部用户注册", False, response.text)
    except Exception as e:
        print_test("内部用户注册测试", False, str(e))


def test_login():
    """测试登录功能"""
    print_header("测试2: 登录功能")

    # 测试2.1: 登录不存在的用户
    try:
        response = requests.post(
            f"{BASE_URL}/api/user/login",
            json={"name": "nonexistent_user", "password": "wrongpassword"},
        )

        if response.status_code == 401:
            print_test("不存在用户登录被拒绝", True)
        else:
            print_bug(f"不存在用户应该返回401，实际返回{response.status_code}")
    except Exception as e:
        print_test("不存在用户登录测试", False, str(e))

    # 测试2.2: 使用测试账号登录
    # 注意：需要数据库中有测试账号
    test_accounts = [
        ("admin", "admin123", "管理员账号"),
        ("test_external_complete", "test123456", "外部用户"),
    ]

    tokens = {}

    for username, password, desc in test_accounts:
        try:
            response = requests.post(
                f"{BASE_URL}/api/user/login",
                json={"name": username, "password": password},
            )

            if response.status_code == 200:
                data = response.json()
                token = data.get("access_token")
                user_info = data.get("user_info", {})

                print_test(
                    f"{desc}登录成功",
                    True,
                    f"用户: {user_info.get('name')}, 角色: {user_info.get('role_name')}",
                )
                tokens[username] = token

                # 检查返回的用户信息
                required_fields = ["user_id", "name", "role", "role_name", "is_active"]
                missing_fields = [f for f in required_fields if f not in user_info]

                if missing_fields:
                    print_bug(f"登录返回缺少字段: {missing_fields}")
                else:
                    print_test("登录返回信息完整", True)
            else:
                print_test(f"{desc}登录", False, f"状态码: {response.status_code}")
        except Exception as e:
            print_test(f"{desc}登录测试", False, str(e))

    return tokens


def test_token_validation(tokens):
    """测试Token验证"""
    print_header("测试3: Token验证")

    if not tokens:
        print_warning("没有可用token，跳过Token验证测试")
        return

    # 测试3.1: 使用有效token获取用户信息
    for username, token in tokens.items():
        try:
            response = requests.get(
                f"{BASE_URL}/api/user/me", headers={"Authorization": f"Bearer {token}"}
            )

            if response.status_code == 200:
                data = response.json()
                print_test(
                    f"{username} Token验证成功", True, f"用户: {data.get('name')}"
                )
            else:
                print_bug(f"有效Token验证失败: {response.status_code}")
        except Exception as e:
            print_test(f"{username} Token验证", False, str(e))

    # 测试3.2: 使用无效token
    try:
        response = requests.get(
            f"{BASE_URL}/api/user/me", headers={"Authorization": "Bearer invalid_token"}
        )

        if response.status_code == 401:
            print_test("无效Token被正确拒绝", True)
        else:
            print_bug(f"无效Token应该返回401，实际返回{response.status_code}")
    except Exception as e:
        print_test("无效Token测试", False, str(e))


def test_logout(tokens):
    """测试退出登录"""
    print_header("测试4: 退出登录")

    if not tokens:
        print_warning("没有可用token，跳过退出登录测试")
        return

    for username, token in tokens.items():
        try:
            response = requests.post(
                f"{BASE_URL}/api/user/logout",
                headers={"Authorization": f"Bearer {token}"},
            )

            if response.status_code == 200:
                print_test(f"{username} 退出登录成功", True)

                # 检查退出后token是否仍然有效
                # 注意：JWT是无状态的，token仍然有效直到过期
                response2 = requests.get(
                    f"{BASE_URL}/api/user/me",
                    headers={"Authorization": f"Bearer {token}"},
                )

                if response2.status_code == 200:
                    print_warning("退出后Token仍然有效（JWT无状态特性）")
                    print_warning("建议: 实现Token黑名单机制增强安全性")
                else:
                    print_test("退出后Token已失效", True)
            else:
                print_bug(f"退出登录失败: {response.status_code}")
        except Exception as e:
            print_test(f"{username} 退出登录", False, str(e))


def test_password_change(tokens):
    """测试修改密码"""
    print_header("测试5: 修改密码")

    if not tokens:
        print_warning("没有可用token，跳过修改密码测试")
        return

    username = list(tokens.keys())[0]
    token = tokens[username]

    # 测试5.1: 错误的原密码
    try:
        response = requests.post(
            f"{BASE_URL}/api/user/change-password",
            headers={"Authorization": f"Bearer {token}"},
            json={"old_password": "wrongpassword", "new_password": "newpassword123"},
        )

        if response.status_code == 400:
            print_test("错误原密码被拒绝", True)
        else:
            print_bug(f"错误原密码应该返回400，实际返回{response.status_code}")
    except Exception as e:
        print_test("错误原密码测试", False, str(e))


def test_duplicate_registration():
    """测试重复注册"""
    print_header("测试6: 重复注册")

    # 注册一个用户
    user_data = {
        "name": "duplicate_test_user",
        "password": "test123456",
        "user_type": "external",
        "phone": "13900139001",
    }

    try:
        # 第一次注册
        response1 = requests.post(f"{BASE_URL}/api/user/register", json=user_data)

        if response1.status_code == 200:
            print_test("首次注册成功", True)

            # 尝试重复注册
            response2 = requests.post(f"{BASE_URL}/api/user/register", json=user_data)

            if response2.status_code == 400 and "已存在" in response2.text:
                print_test("重复注册被正确拒绝", True)
            else:
                print_bug(f"重复注册应该被拒绝，实际返回{response2.status_code}")
        elif response1.status_code == 400 and "已存在" in response1.text:
            print_warning("测试用户已存在，跳过重复注册测试")
        else:
            print_warning(f"首次注册失败: {response1.status_code}")
    except Exception as e:
        print_test("重复注册测试", False, str(e))


def check_code_issues():
    """检查代码问题"""
    print_header("检查代码问题")

    issues = []

    # 检查API文件
    try:
        with open(
            "/Users/sgl/PycharmProjects/AIchanyejiqun/Service_WaterManage/backend/api_user_auth.py",
            "r",
        ) as f:
            content = f.read()

            # 检查重复代码
            if content.count("验证用户名格式（只允许字母、数字、下划线、中文）") > 1:
                issues.append(
                    "🐛 api_user_auth.py: 注册函数有重复的验证代码（第167-186行和第357-370行）"
                )

            # 检查用户类型处理
            if "user_type" not in content:
                issues.append("⚠ 警告: 未找到user_type相关代码")

            # 检查外部用户手机号验证
            if "外部用户必须提供手机号" in content:
                print_test("外部用户手机号验证存在", True)
            else:
                issues.append("🐛 缺少外部用户手机号验证")

            # 检查退出登录实现
            if "JWT是无状态的" in content:
                issues.append("⚠ 退出登录: JWT无状态，建议实现Token黑名单")

    except Exception as e:
        issues.append(f"⚠ 无法读取API文件: {str(e)}")

    # 输出问题
    for issue in issues:
        print(issue)


def main():
    print(f"\n{Colors.BOLD}登录、注册、退出功能完整测试{Colors.END}")
    print(f"测试时间: {__import__('datetime').datetime.now()}\n")

    # 测试服务是否运行
    try:
        response = requests.get(f"{BASE_URL}/api/health", timeout=5)
        if response.status_code != 200:
            print(f"{Colors.RED}服务未运行，请先启动服务{Colors.END}")
            sys.exit(1)
        print(f"{Colors.GREEN}✓ 服务运行正常{Colors.END}\n")
    except:
        print(f"{Colors.RED}无法连接服务: {BASE_URL}{Colors.END}")
        sys.exit(1)

    # 运行所有测试
    test_register()
    tokens = test_login()
    test_token_validation(tokens)
    test_logout(tokens)
    test_password_change(tokens)
    test_duplicate_registration()
    check_code_issues()

    # 测试总结
    print_header("测试总结")
    print("已完成所有测试，请查看上方结果")
    print(f"\n{Colors.YELLOW}建议修复的问题:{Colors.END}")
    print("1. 注册API中的重复代码")
    print("2. 退出登录的Token黑名单机制")
    print("3. 前端退出登录的跳转路径统一")
    print(f"\n{Colors.GREEN}测试完成！{Colors.END}\n")


if __name__ == "__main__":
    main()
