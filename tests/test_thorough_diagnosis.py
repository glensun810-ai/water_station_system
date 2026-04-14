#!/usr/bin/env python3
"""
彻底的端到端验证测试
模拟真实浏览器操作，检查每个环节
"""

import requests
import json
import re
from datetime import datetime

BASE_URL = "http://127.0.0.1:8008"


class ThoroughEndToEndTester:
    def __init__(self):
        self.base_url = BASE_URL
        self.token = None
        self.user_info = None
        self.issues_found = []

    def print_section(self, title):
        print(f"\n{'=' * 80}")
        print(f"{title}")
        print(f"{'=' * 80}")

    def step1_login_and_set_storage(self):
        """步骤1: 登录并设置localStorage"""
        self.print_section("步骤1: 登录并设置localStorage")

        try:
            response = requests.post(
                f"{self.base_url}/api/v1/system/auth/login",
                json={"username": "admin", "password": "admin123"},
            )

            if response.status_code == 200:
                data = response.json()
                self.token = data["access_token"]

                # 模拟登录页设置localStorage（完全按照登录页逻辑）
                self.user_info = {
                    "id": data["user_info"]["user_id"],
                    "name": data["user_info"]["username"],
                    "username": data["user_info"]["username"],
                    "role": data["user_info"]["role"],
                    "roleName": data["user_info"]["role_name"],
                    "department": data["user_info"]["department"] or "",
                    "avatar": "👤",
                    "is_admin": data["user_info"]["role"]
                    in ["super_admin", "admin", "office_admin"],
                }

                print(f"✅ 登录成功")
                print(f"Token: {self.token[:50]}...")
                print(f"localStorage应该设置为:")
                print(f"  token: {self.token[:50]}...")
                print(f"  userInfo: {json.dumps(self.user_info, ensure_ascii=False)}")
                print(f"  userInfo.id: {self.user_info['id']}  # 关键字段!")

                return True
            else:
                self.issues_found.append(f"登录失败: {response.status_code}")
                return False
        except Exception as e:
            self.issues_found.append(f"登录异常: {str(e)}")
            return False

    def step2_check_portal_page_logic(self):
        """步骤2: 检查Portal首页的逻辑"""
        self.print_section("步骤2: 检查Portal首页的逻辑")

        try:
            response = requests.get(f"{self.base_url}/portal/index.html")
            content = response.text

            # 检查关键逻辑
            checks = {
                "包含auth.js": "/portal/assets/js/auth.js" in content,
                "包含checkAuth调用": "checkAuth" in content,
                "userInfo.value.id检查": "userInfo.value && userInfo.value.id"
                in content,
                "spaceNavHref逻辑": "spaceNavHref" in content,
            }

            print(f"Portal首页逻辑检查:")
            for check_name, result in checks.items():
                status = "✅" if result else "❌"
                print(f"  {status} {check_name}: {result}")
                if not result:
                    self.issues_found.append(f"Portal首页缺少: {check_name}")

            # 提取spaceNavHref逻辑
            pattern = r"const spaceNavHref = computed\(\(\) => \{[^}]+\}\)"
            match = re.search(pattern, content)

            if match:
                spaceNavHref_logic = match.group(0)
                print(f"\nspaceNavHref逻辑:")
                print(f"  {spaceNavHref_logic}")

                # 检查是否指向登录页
                if "/portal/admin/login.html" in spaceNavHref_logic:
                    print(f"\n❌ 问题：spaceNavHref逻辑包含跳转到登录页")
                    print(f"  当userInfo.value.id为null时，会跳转到login.html")

                    # 分析跳转条件
                    if "userInfo.value && userInfo.value.id" in spaceNavHref_logic:
                        print(
                            f"\n✅ 跳转条件正确：userInfo.value.id存在时跳转到/space-frontend/index.html"
                        )
                    else:
                        print(f"\n❌ 跳转条件不正确")
                        self.issues_found.append("spaceNavHref跳转条件不正确")
            else:
                print(f"\n❌ 未找到spaceNavHref逻辑")
                self.issues_found.append("Portal首页缺少spaceNavHref逻辑")

            return all(checks.values())
        except Exception as e:
            self.issues_found.append(f"Portal首页检查异常: {str(e)}")
            return False

    def step3_simulate_browser_operation(self):
        """步骤3: 模拟浏览器操作"""
        self.print_section("步骤3: 模拟浏览器操作")

        if not self.token or not self.user_info:
            print("❌ 缺少Token或userInfo，跳过此步骤")
            return False

        # 模拟浏览器操作流程
        print(f"模拟浏览器操作流程:")

        # 1. 登录页设置localStorage
        print(f"\n1. 登录页设置localStorage:")
        print(f"   localStorage.setItem('token', '{self.token[:50]}...')")
        print(
            f"   localStorage.setItem('userInfo', '{json.dumps(self.user_info, ensure_ascii=False)[:100]}...')"
        )
        print(
            f"   localStorage.setItem('token_timestamp', '{datetime.now().isoformat()}')"
        )

        # 2. 跳转到Portal首页
        print(f"\n2. 跳转到Portal首页:")
        print(f"   window.location.href = '/portal/index.html'")

        # 3. Portal首页加载并读取localStorage
        print(f"\n3. Portal首页加载并读取localStorage:")
        print(f"   loadUserData()执行...")
        print(f"   checkAuth()读取localStorage...")
        print(f"   getUserInfo()返回:")
        print(f"     id: {self.user_info['id']}")
        print(f"     name: {self.user_info['name']}")
        print(f"     role: {self.user_info['role']}")

        # 4. 设置userInfo.value
        print(f"\n4. Portal首页设置userInfo.value:")
        print(
            f"   userInfo.value = {json.dumps(self.user_info, ensure_ascii=False)[:100]}..."
        )
        print(f"   userInfo.value.id = {self.user_info['id']}  # 关键!")

        # 5. 计算spaceNavHref
        print(f"\n5. 计算spaceNavHref:")
        user_id = self.user_info["id"]
        spaceNavHref = (
            "/space-frontend/index.html" if user_id else "/portal/admin/login.html"
        )
        print(f"   userInfo.value.id = {user_id}")
        print(f"   spaceNavHref = '{spaceNavHref}'")

        if user_id:
            print(f"\n✅ 正确！spaceNavHref指向预约页面")
            print(f"   点击'空间服务-预约'应该跳转到: {spaceNavHref}")
        else:
            print(f"\n❌ 错误！userInfo.value.id为null")
            print(f"   spaceNavHref会指向登录页")
            self.issues_found.append("userInfo.value.id为null，导致跳转到登录页")

        return user_id is not None

    def step4_verify_actual_page_content(self):
        """步骤4: 验证实际页面内容"""
        self.print_section("步骤4: 验证实际页面内容")

        if not self.token:
            print("❌ 缺少Token，跳过此步骤")
            return False

        # 检查space-frontend/index.html是否有强制跳转
        try:
            response = requests.get(f"{self.base_url}/space-frontend/index.html")
            content = response.text

            print(f"space-frontend/index.html内容检查:")

            # 检查是否有强制跳转登录页的代码
            has_old_auth_token = "localStorage.getItem('auth_token')" in content
            has_login_redirect = (
                "window.location.href = '/space-frontend/login.html'" in content
            )
            has_auth_js = "/portal/assets/js/auth.js" in content
            has_checkAuth = "checkAuth" in content

            print(f"  ❌ 使用旧auth_token: {has_old_auth_token}")
            print(f"  ❌ 强制跳转登录页: {has_login_redirect}")
            print(f"  ✅ 包含auth.js: {has_auth_js}")
            print(f"  ✅ 使用checkAuth: {has_checkAuth}")

            if has_old_auth_token or has_login_redirect:
                print(f"\n❌ 严重问题：space-frontend/index.html仍有强制跳转逻辑")
                self.issues_found.append("space-frontend/index.html有强制跳转逻辑")
                return False

            if has_auth_js and has_checkAuth:
                print(f"\n✅ space-frontend/index.html已正确修复")
                return True
            else:
                print(f"\n❌ space-frontend/index.html修复不完整")
                self.issues_found.append(
                    "space-frontend/index.html缺少auth.js或checkAuth"
                )
                return False

        except Exception as e:
            self.issues_found.append(f"页面内容检查异常: {str(e)}")
            return False

    def step5_final_diagnosis(self):
        """步骤5: 最终诊断"""
        self.print_section("步骤5: 最终诊断")

        print(f"问题诊断结果:")

        if not self.issues_found:
            print(f"✅ 所有检查通过，逻辑正确")
            print(f"\n可能的问题原因:")
            print(f"  1. 浏览器缓存了旧版本的页面")
            print(f"  2. localStorage被清除或未正确设置")
            print(f"  3. 页面加载时机问题（userInfo未及时设置）")
            print(f"\n解决方案:")
            print(f"  1. 清除浏览器缓存（Ctrl+Shift+Delete）")
            print(f"  2. 清除localStorage（浏览器开发者工具）")
            print(f"  3. 重新登录")
            print(f"  4. 确保服务器已重启")
        else:
            print(f"❌ 发现以下问题:")
            for issue in self.issues_found:
                print(f"  - {issue}")

            print(f"\n需要修复:")
            print(f"  1. 检查Portal首页userInfo设置逻辑")
            print(f"  2. 检查space-frontend页面是否有强制跳转")
            print(f"  3. 检查登录页localStorage设置")

        return len(self.issues_found) == 0

    def run_thorough_test(self):
        """运行彻底测试"""
        self.print_section("彻底的端到端验证测试")
        print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"目标: 找出为什么点击'空间服务-预约'跳转到登录页")

        # 执行测试步骤
        step1_ok = self.step1_login_and_set_storage()
        step2_ok = self.step2_check_portal_page_logic()
        step3_ok = self.step3_simulate_browser_operation()
        step4_ok = self.step4_verify_actual_page_content()
        step5_ok = self.step5_final_diagnosis()

        # 总结
        self.print_section("测试总结")

        results = {
            "步骤1 - 登录设置": step1_ok,
            "步骤2 - Portal逻辑": step2_ok,
            "步骤3 - 浏览器模拟": step3_ok,
            "步骤4 - 页面验证": step4_ok,
            "步骤5 - 最终诊断": step5_ok,
        }

        for step, ok in results.items():
            status = "✅ 通过" if ok else "❌ 失败"
            print(f"{step}: {status}")

        if self.issues_found:
            print(f"\n发现的问题:")
            for issue in self.issues_found:
                print(f"  ❌ {issue}")

        return {"all_ok": len(self.issues_found) == 0, "issues": self.issues_found}


if __name__ == "__main__":
    tester = ThoroughEndToEndTester()
    result = tester.run_thorough_test()

    # 生成诊断报告
    with open(
        "docs/space-service-refactor/彻底诊断报告.md", "w", encoding="utf-8"
    ) as f:
        f.write("# 点击空间服务跳转登录页问题 - 彻底诊断报告\n\n")
        f.write(f"**诊断时间:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("## 诊断结果\n\n")

        if result["all_ok"]:
            f.write("✅ **所有逻辑检查通过，代码正确**\n\n")
            f.write("## 可能的问题原因\n\n")
            f.write("1. **浏览器缓存** - 缓存了旧版本的页面\n")
            f.write("2. **localStorage被清除** - 用户清除了localStorage\n")
            f.write("3. **页面加载时机** - userInfo未及时设置\n")
            f.write("4. **服务器未重启** - 修改未生效\n\n")
            f.write("## 解决方案\n\n")
            f.write("### 方案1: 清除浏览器缓存\n\n")
            f.write("```\n")
            f.write("1. 按 Ctrl+Shift+Delete（Windows）或 Cmd+Shift+Delete（Mac）\n")
            f.write("2. 选择'缓存的图片和文件'\n")
            f.write("3. 点击'清除数据'\n")
            f.write("4. 重新访问Portal首页\n")
            f.write("```\n\n")
            f.write("### 方案2: 清除localStorage\n\n")
            f.write("```\n")
            f.write("1. 打开浏览器开发者工具（F12）\n")
            f.write("2. 切换到'Application'或'应用'标签\n")
            f.write("3. 点击'Local Storage' -> 'http://127.0.0.1:8008'\n")
            f.write("4. 右键 -> 'Clear' 或逐个删除token、userInfo\n")
            f.write("5. 重新登录\n")
            f.write("```\n\n")
            f.write("### 方案3: 重启服务器\n\n")
            f.write("```\n")
            f.write("killall uvicorn\n")
            f.write("python3 -m uvicorn apps.main:app --host 127.0.0.1 --port 8008\n")
            f.write("```\n\n")
            f.write("### 方案4: 强制刷新页面\n\n")
            f.write("```\n")
            f.write("按 Ctrl+F5（Windows）或 Cmd+Shift+R（Mac）强制刷新\n")
            f.write("```\n\n")
        else:
            f.write("❌ **发现代码逻辑问题**\n\n")
            f.write("## 问题列表\n\n")
            for issue in result["issues"]:
                f.write(f"- {issue}\n")

            f.write("\n## 需要修复\n\n")
            f.write("请检查上述问题，修复相应的代码逻辑。\n")

    print(f"\n详细诊断报告已保存到: docs/space-service-refactor/彻底诊断报告.md")
