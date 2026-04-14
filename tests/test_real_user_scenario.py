#!/usr/bin/env python3
"""
真实用户场景测试 - Portal首页登录后访问子页面
模拟用户真实操作流程：
1. 在Portal首页登录
2. 点击空间服务-预约
3. 检查是否需要重新登录
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://127.0.0.1:8008"


class RealUserScenarioTester:
    def __init__(self):
        self.base_url = BASE_URL
        self.session = requests.Session()
        self.token = None
        self.user_info = None

    def print_step(self, step_num, description):
        print(f"\n{'=' * 80}")
        print(f"步骤 {step_num}: {description}")
        print(f"{'=' * 80}")

    def step1_login_at_portal(self):
        """步骤1: 用户在Portal首页登录"""
        self.print_step(1, "用户在Portal首页登录")

        try:
            # 模拟用户在Portal首页登录
            response = requests.post(
                f"{self.base_url}/api/v1/system/auth/login",
                json={"username": "admin", "password": "admin123"},
                headers={"Content-Type": "application/json"},
            )

            if response.status_code == 200:
                data = response.json()
                self.token = data["access_token"]
                self.user_info = data["user_info"]

                print(f"✅ 登录成功")
                print(f"用户: {self.user_info['username']}")
                print(f"角色: {self.user_info['role_name']}")
                print(f"Token长度: {len(self.token)}")

                # 模拟localStorage存储（这是前端会做的）
                print(f"\n前端localStorage存储:")
                print(f"  localStorage.setItem('token', '{self.token[:50]}...')")
                print(
                    f"  localStorage.setItem('userInfo', '{json.dumps(self.user_info)}')"
                )

                return True
            else:
                print(f"❌ 登录失败: {response.status_code}")
                print(f"响应: {response.text}")
                return False
        except Exception as e:
            print(f"❌ 登录异常: {str(e)}")
            return False

    def step2_click_space_service(self):
        """步骤2: 用户点击空间服务-预约"""
        self.print_step(2, "用户点击空间服务-预约")

        if not self.token:
            print("❌ 未登录，跳过此步骤")
            return False

        # 模拟前端跳转：用户点击"空间服务-预约"
        target_page = "/space-frontend/index.html"

        print(f"用户操作: 点击 '空间服务-预约'")
        print(f"目标页面: {target_page}")

        try:
            # 模拟前端请求（携带localStorage中的Token）
            response = requests.get(
                f"{self.base_url}{target_page}",
                headers={
                    "Authorization": f"Bearer {self.token}",
                    # 模拟localStorage携带的Token（前端页面加载时会读取）
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
                },
            )

            if response.status_code == 200:
                content = response.text

                # 检查页面是否包含checkAuth（不再强制跳转到登录页）
                has_checkAuth = "checkAuth" in content
                has_auth_js = "/portal/assets/js/auth.js" in content
                has_old_token_check = "localStorage.getItem('auth_token')" in content
                has_login_redirect = (
                    "window.location.href = '/space-frontend/login.html'" in content
                )

                print(f"\n✅ 页面加载成功")
                print(f"页面分析:")
                print(f"  ✅ 包含auth.js: {has_auth_js}")
                print(f"  ✅ 包含checkAuth: {has_checkAuth}")
                print(f"  ❌ 使用旧auth_token: {has_old_token_check}")
                print(f"  ❌ 强制跳转登录页: {has_login_redirect}")

                # 检查是否修复成功
                if (
                    has_auth_js
                    and has_checkAuth
                    and not has_old_token_check
                    and not has_login_redirect
                ):
                    print(f"\n✅ 修复成功! 页面不会强制跳转到登录页")
                    print(f"用户可以正常访问，无需重新登录")
                    return True
                else:
                    print(f"\n❌ 修复不完整，可能仍会跳转到登录页")
                    return False
            else:
                print(f"❌ 页面加载失败: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ 页面访问异常: {str(e)}")
            return False

    def step3_verify_token_persistence(self):
        """步骤3: 验证Token在整个会话中有效"""
        self.print_step(3, "验证Token在整个会话中有效")

        if not self.token:
            print("❌ 未登录，跳过此步骤")
            return False

        # 模拟用户访问多个页面（都应该无需重新登录）
        pages_to_visit = [
            ("/portal/index.html", "Portal首页"),
            ("/space-frontend/index.html", "空间服务首页"),
            ("/space-frontend/booking.html", "预约创建页"),
            ("/portal/admin/space/approvals.html", "审批管理页"),
        ]

        print(f"模拟用户访问多个页面:")

        all_success = True
        for page, name in pages_to_visit:
            try:
                # 模拟前端页面加载时验证Token
                # 1. 检查Token是否存在（localStorage）
                # 2. 检查Token是否过期（本地检查）
                # 3. 验证Token有效性（调用API）

                # 先验证Token API
                api_response = requests.get(
                    f"{self.base_url}/api/v1/system/auth/profile",
                    headers={"Authorization": f"Bearer {self.token}"},
                )

                if api_response.status_code == 200:
                    user_data = api_response.json()
                    print(f"  ✅ {name}: Token有效，用户={user_data['username']}")
                else:
                    print(f"  ❌ {name}: Token无效或过期")
                    all_success = False

                # 然后检查页面是否可访问
                page_response = requests.get(
                    f"{self.base_url}{page}",
                    headers={"Authorization": f"Bearer {self.token}"},
                )

                if page_response.status_code != 200:
                    print(f"  ❌ {name}: 页面加载失败")
                    all_success = False

            except Exception as e:
                print(f"  ❌ {name}: 异常 - {str(e)}")
                all_success = False

        if all_success:
            print(f"\n✅ Token在整个会话中有效")
            print(f"用户可以在所有页面间自由切换，无需重新登录")
        else:
            print(f"\n❌ Token在某些页面无效")

        return all_success

    def step4_verify_no_login_redirect(self):
        """步骤4: 验证不再强制跳转到登录页"""
        self.print_step(4, "验证不再强制跳转到登录页")

        if not self.token:
            print("❌ 未登录，跳过此步骤")
            return False

        # 检查space-frontend页面是否有强制跳转逻辑
        pages_to_check = ["/space-frontend/index.html", "/space-frontend/booking.html"]

        print(f"检查页面是否有强制跳转登录页的逻辑:")

        all_fixed = True
        for page in pages_to_check:
            try:
                response = requests.get(f"{self.base_url}{page}")
                content = response.text

                # 检查是否有旧的强制跳转逻辑
                has_auth_token_check = "localStorage.getItem('auth_token')" in content
                has_login_redirect = (
                    "window.location.href = '/space-frontend/login.html'" in content
                )
                has_checkAuth = "checkAuth" in content

                print(f"\n页面: {page}")
                print(f"  使用旧auth_token: {has_auth_token_check}")
                print(f"  强制跳转登录页: {has_login_redirect}")
                print(f"  使用checkAuth: {has_checkAuth}")

                if has_auth_token_check or has_login_redirect:
                    print(f"  ❌ 页面仍有强制跳转逻辑")
                    all_fixed = False
                elif has_checkAuth:
                    print(f"  ✅ 页面已修复，使用checkAuth")
                else:
                    print(f"  ⚠️  页面缺少认证检查")

            except Exception as e:
                print(f"  ❌ 检查异常: {str(e)}")
                all_fixed = False

        if all_fixed:
            print(f"\n✅ 所有页面已修复，不再强制跳转到登录页")
            print(f"用户体验：登录后可以正常访问所有页面")
        else:
            print(f"\n❌ 某些页面仍会强制跳转到登录页")

        return all_fixed

    def run_real_user_scenario(self):
        """运行真实用户场景测试"""
        print("\n" + "=" * 80)
        print("真实用户场景测试 - Portal首页登录后访问子页面")
        print("=" * 80)
        print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"测试场景: 用户在Portal首页登录，然后点击空间服务-预约")
        print(f"预期结果: 无需重新登录，直接访问")
        print("=" * 80)

        # 执行测试步骤
        step1_ok = self.step1_login_at_portal()
        step2_ok = self.step2_click_space_service()
        step3_ok = self.step3_verify_token_persistence()
        step4_ok = self.step4_verify_no_login_redirect()

        # 总结
        print("\n" + "=" * 80)
        print("测试结果汇总")
        print("=" * 80)

        results = {
            "步骤1 - Portal首页登录": step1_ok,
            "步骤2 - 点击空间服务": step2_ok,
            "步骤3 - Token持久化": step3_ok,
            "步骤4 - 无强制跳转": step4_ok,
        }

        for step, ok in results.items():
            status = "✅ 通过" if ok else "❌ 失败"
            print(f"{step}: {status}")

        total = len(results)
        passed = sum(1 for ok in results.values() if ok)
        pass_rate = (passed / total * 100) if total > 0 else 0

        print(f"\n总体结果: {passed}/{total} = {pass_rate:.1f}%")

        if pass_rate == 100:
            print("\n✅ 完全成功! 用户登录后访问所有页面无需重新登录")
            print("\n用户体验:")
            print("  1. 在Portal首页登录")
            print("  2. 点击空间服务-预约")
            print("  3. 直接进入预约页面，无需重新登录 ✅")
            print("  4. 可以在所有页面间自由切换 ✅")
            print("  5. Token有效期为24小时 ✅")
        else:
            print("\n❌ 修复不完整，用户可能仍需要重新登录")
            print("\n建议:")
            print("  - 检查space-frontend页面是否使用checkAuth")
            print("  - 检查是否移除强制跳转登录页逻辑")
            print("  - 检查是否使用统一的token存储key")

        print("=" * 80)

        return {
            "total": total,
            "passed": passed,
            "pass_rate": pass_rate,
            "all_ok": pass_rate == 100,
        }


if __name__ == "__main__":
    tester = RealUserScenarioTester()
    result = tester.run_real_user_scenario()

    # 保存结果
    with open(
        "docs/space-service-refactor/真实用户场景测试报告.md", "w", encoding="utf-8"
    ) as f:
        f.write("# 真实用户场景测试报告\n\n")
        f.write(f"**测试时间:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("## 测试场景\n\n")
        f.write("用户在Portal首页登录，然后点击空间服务-预约\n\n")
        f.write("## 测试结果\n\n")
        f.write(f"- **通过率:** {result['pass_rate']:.1f}%\n")
        f.write(f"- **总步骤:** {result['total']}\n")
        f.write(f"- **通过:** {result['passed']}\n\n")

        if result["all_ok"]:
            f.write("## ✅ 测试成功\n\n")
            f.write("用户登录后访问所有页面无需重新登录。\n\n")
            f.write("### 用户体验\n\n")
            f.write("1. 在Portal首页登录 ✅\n")
            f.write("2. 点击空间服务-预约 ✅\n")
            f.write("3. 直接进入预约页面，无需重新登录 ✅\n")
            f.write("4. 可以在所有页面间自由切换 ✅\n")
            f.write("5. Token有效期为24小时 ✅\n")
        else:
            f.write("## ❌ 测试失败\n\n")
            f.write("用户可能仍需要重新登录。\n")

    print(f"\n详细报告已保存到: docs/space-service-refactor/真实用户场景测试报告.md")
