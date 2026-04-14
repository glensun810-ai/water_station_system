#!/usr/bin/env python3
"""
统一登录管理模块验证测试
测试目标：验证登录、认证、退出等功能的完整性
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8008/api/v1/system"


class LoginModuleTester:
    def __init__(self):
        self.base_url = BASE_URL
        self.session = requests.Session()
        self.token = None
        self.user_info = None
        self.results = []

    def log_result(self, test_name, passed, message="", details=None):
        """记录测试结果"""
        result = {
            "test": test_name,
            "passed": passed,
            "message": message,
            "details": details,
            "timestamp": datetime.now().strftime("%H:%M:%S"),
        }
        self.results.append(result)
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} [{result['timestamp']}] {test_name}: {message}")
        if details and not passed:
            print(f"   Details: {json.dumps(details, ensure_ascii=False, indent=2)}")

    def test_login_api_endpoint(self):
        """测试1: 登录API端点可访问性"""
        try:
            # 测试GET请求（应该返回405 Method Not Allowed）
            response = requests.get(f"{self.base_url}/auth/login")
            if response.status_code == 405:
                self.log_result(
                    "登录端点GET请求", True, "正确返回405 Method Not Allowed"
                )
            else:
                self.log_result(
                    "登录端点GET请求", False, f"期望405，实际{response.status_code}"
                )
        except Exception as e:
            self.log_result("登录端点GET请求", False, str(e))

    def test_login_with_valid_credentials(self):
        """测试2: 正确凭据登录"""
        try:
            response = requests.post(
                f"{self.base_url}/auth/login",
                json={"username": "admin", "password": "admin123"},
                headers={"Content-Type": "application/json"},
            )

            if response.status_code == 200:
                data = response.json()
                if "access_token" in data and "user_info" in data:
                    self.token = data["access_token"]
                    self.user_info = data["user_info"]
                    self.log_result(
                        "正确凭据登录",
                        True,
                        f"登录成功，角色：{data['user_info']['role_name']}",
                        {
                            "user_id": data["user_info"]["user_id"],
                            "username": data["user_info"]["username"],
                            "role": data["user_info"]["role"],
                        },
                    )
                else:
                    self.log_result("正确凭据登录", False, "响应缺少必要字段", data)
            else:
                self.log_result(
                    "正确凭据登录",
                    False,
                    f"状态码：{response.status_code}",
                    response.text,
                )
        except Exception as e:
            self.log_result("正确凭据登录", False, str(e))

    def test_login_with_invalid_credentials(self):
        """测试3: 错误凭据登录"""
        try:
            response = requests.post(
                f"{self.base_url}/auth/login",
                json={"username": "invalid", "password": "wrong"},
                headers={"Content-Type": "application/json"},
            )

            if response.status_code == 401 or response.status_code == 400:
                self.log_result("错误凭据登录", True, "正确拒绝错误凭据")
            else:
                self.log_result(
                    "错误凭据登录", False, f"期望401/400，实际{response.status_code}"
                )
        except Exception as e:
            self.log_result("错误凭据登录", False, str(e))

    def test_get_profile_with_token(self):
        """测试4: 使用Token获取用户信息"""
        if not self.token:
            self.log_result("Token获取用户信息", False, "缺少Token，跳过测试")
            return

        try:
            response = requests.get(
                f"{self.base_url}/auth/profile",
                headers={"Authorization": f"Bearer {self.token}"},
            )

            if response.status_code == 200:
                data = response.json()
                if "username" in data and "role" in data:
                    self.log_result(
                        "Token获取用户信息",
                        True,
                        f"成功获取用户信息：{data['username']}",
                    )
                else:
                    self.log_result("Token获取用户信息", False, "响应格式错误", data)
            else:
                self.log_result(
                    "Token获取用户信息", False, f"状态码：{response.status_code}"
                )
        except Exception as e:
            self.log_result("Token获取用户信息", False, str(e))

    def test_get_profile_without_token(self):
        """测试5: 无Token获取用户信息"""
        try:
            response = requests.get(f"{self.base_url}/auth/profile")

            if response.status_code == 401:
                self.log_result("无Token获取用户信息", True, "正确返回401未授权")
            else:
                self.log_result(
                    "无Token获取用户信息", False, f"期望401，实际{response.status_code}"
                )
        except Exception as e:
            self.log_result("无Token获取用户信息", False, str(e))

    def test_get_sessions_with_token(self):
        """测试6: 使用Token获取会话列表"""
        if not self.token:
            self.log_result("Token获取会话列表", False, "缺少Token，跳过测试")
            return

        try:
            response = requests.get(
                f"{self.base_url}/auth/sessions",
                headers={"Authorization": f"Bearer {self.token}"},
            )

            if response.status_code == 200:
                data = response.json()
                self.log_result(
                    "Token获取会话列表",
                    True,
                    f"成功获取会话列表，共{len(data) if isinstance(data, list) else 0}个会话",
                )
            else:
                self.log_result(
                    "Token获取会话列表", False, f"状态码：{response.status_code}"
                )
        except Exception as e:
            self.log_result("Token获取会话列表", False, str(e))

    def test_change_password_validation(self):
        """测试7: 修改密码验证"""
        if not self.token:
            self.log_result("修改密码验证", False, "缺少Token，跳过测试")
            return

        try:
            # 测试错误旧密码
            response = requests.post(
                f"{self.base_url}/auth/change-password",
                json={"old_password": "wrong_password", "new_password": "newpass123"},
                headers={
                    "Authorization": f"Bearer {self.token}",
                    "Content-Type": "application/json",
                },
            )

            if response.status_code in [400, 401]:
                self.log_result("修改密码验证", True, "正确拒绝错误旧密码")
            else:
                self.log_result(
                    "修改密码验证", False, f"期望400/401，实际{response.status_code}"
                )
        except Exception as e:
            self.log_result("修改密码验证", False, str(e))

    def test_logout_with_token(self):
        """测试8: 使用Token退出登录"""
        if not self.token:
            self.log_result("Token退出登录", False, "缺少Token，跳过测试")
            return

        try:
            response = requests.post(
                f"{self.base_url}/auth/logout",
                headers={"Authorization": f"Bearer {self.token}"},
            )

            if response.status_code == 200:
                self.log_result("Token退出登录", True, "成功退出登录")
                # 清空Token
                self.token = None
            else:
                self.log_result(
                    "Token退出登录", False, f"状态码：{response.status_code}"
                )
        except Exception as e:
            self.log_result("Token退出登录", False, str(e))

    def test_use_token_after_logout(self):
        """测试9: 退出后使用旧Token"""
        # 先重新登录获取新Token
        try:
            response = requests.post(
                f"{self.base_url}/auth/login",
                json={"username": "admin", "password": "admin123"},
                headers={"Content-Type": "application/json"},
            )
            if response.status_code == 200:
                token = response.json()["access_token"]

                # 先退出
                requests.post(
                    f"{self.base_url}/auth/logout",
                    headers={"Authorization": f"Bearer {token}"},
                )

                # 尝试使用旧Token
                response = requests.get(
                    f"{self.base_url}/auth/profile",
                    headers={"Authorization": f"Bearer {token}"},
                )

                if response.status_code == 401:
                    self.log_result("退出后使用旧Token", True, "正确拒绝旧Token")
                else:
                    self.log_result(
                        "退出后使用旧Token",
                        False,
                        f"期望401，实际{response.status_code}",
                    )
            else:
                self.log_result("退出后使用旧Token", False, "无法获取测试Token")
        except Exception as e:
            self.log_result("退出后使用旧Token", False, str(e))

    def test_frontend_login_pages(self):
        """测试10: 前端登录页面可访问性"""
        pages = [
            ("space-frontend/login.html", "用户端登录"),
            ("portal/admin/login.html", "管理端登录"),
        ]

        for page, name in pages:
            try:
                response = requests.get(f"http://127.0.0.1:8008/{page}")
                if response.status_code == 200:
                    # 检查关键元素
                    if "login" in response.text.lower() or "登录" in response.text:
                        self.log_result(
                            f"{name}页面可访问", True, f"页面正常，包含登录元素"
                        )
                    else:
                        self.log_result(f"{name}页面可访问", False, "页面缺少登录元素")
                else:
                    self.log_result(
                        f"{name}页面可访问", False, f"状态码：{response.status_code}"
                    )
            except Exception as e:
                self.log_result(f"{name}页面可访问", False, str(e))

    def test_login_api_path(self):
        """测试11: 登录API路径正确性"""
        correct_path = "/api/v1/system/auth/login"

        try:
            # 测试正确路径
            response = requests.post(
                f"http://127.0.0.1:8008{correct_path}",
                json={"username": "admin", "password": "admin123"},
                headers={"Content-Type": "application/json"},
            )

            if response.status_code == 200:
                self.log_result(
                    "登录API路径正确性", True, f"正确路径{correct_path}可访问"
                )
            else:
                self.log_result(
                    "登录API路径正确性", False, f"正确路径返回{response.status_code}"
                )
        except Exception as e:
            self.log_result("登录API路径正确性", False, str(e))

    def run_all_tests(self):
        """运行所有测试"""
        print("\n" + "=" * 80)
        print("统一登录管理模块验证测试")
        print("=" * 80)
        print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"测试端点: {self.base_url}")
        print("=" * 80 + "\n")

        # 运行测试
        self.test_login_api_endpoint()
        self.test_login_with_valid_credentials()
        self.test_login_with_invalid_credentials()
        self.test_get_profile_with_token()
        self.test_get_profile_without_token()
        self.test_get_sessions_with_token()
        self.test_change_password_validation()
        self.test_logout_with_token()
        self.test_use_token_after_logout()
        self.test_frontend_login_pages()
        self.test_login_api_path()

        # 统计结果
        total = len(self.results)
        passed = sum(1 for r in self.results if r["passed"])
        failed = total - passed
        pass_rate = (passed / total * 100) if total > 0 else 0

        print("\n" + "=" * 80)
        print("测试结果汇总")
        print("=" * 80)
        print(f"总测试数: {total}")
        print(f"通过: {passed}")
        print(f"失败: {failed}")
        print(f"通过率: {pass_rate:.1f}%")
        print("=" * 80 + "\n")

        # 详细结果
        if failed > 0:
            print("\n失败测试详情:")
            for result in self.results:
                if not result["passed"]:
                    print(f"  - {result['test']}: {result['message']}")

        return {
            "total": total,
            "passed": passed,
            "failed": failed,
            "pass_rate": pass_rate,
            "results": self.results,
        }


if __name__ == "__main__":
    tester = LoginModuleTester()
    result = tester.run_all_tests()

    # 保存结果
    with open(
        "docs/space-service-refactor/登录模块验证报告.md", "w", encoding="utf-8"
    ) as f:
        f.write("# 统一登录管理模块验证报告\n\n")
        f.write(f"**测试时间:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"**测试端点:** {BASE_URL}\n\n")
        f.write("## 测试结果汇总\n\n")
        f.write(f"- **总测试数:** {result['total']}\n")
        f.write(f"- **通过:** {result['passed']}\n")
        f.write(f"- **失败:** {result['failed']}\n")
        f.write(f"- **通过率:** {result['pass_rate']:.1f}%\n\n")
        f.write("## 详细测试结果\n\n")
        f.write("| 测试项 | 状态 | 消息 |\n")
        f.write("|--------|------|------|\n")
        for r in result["results"]:
            status = "✅ 通过" if r["passed"] else "❌ 失败"
            f.write(f"| {r['test']} | {status} | {r['message']} |\n")

    print(f"\n详细报告已保存到: docs/space-service-refactor/登录模块验证报告.md")
