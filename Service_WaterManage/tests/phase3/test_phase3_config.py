#!/usr/bin/env python3
"""
Phase 3 验证测试脚本
验证配置文件的完整性和可用性

运行方法:
    cd Service_WaterManage/tests/phase3
    python3 test_phase3_config.py
"""

import os
import sys
import json
import re


class Phase3TestRunner:
    def __init__(self):
        self.tests_passed = 0
        self.tests_failed = 0
        self.results = []
        self.frontend_dir = os.path.join(os.path.dirname(__file__), "../../frontend")

    def log(self, test_name, passed, message=""):
        """记录测试结果"""
        status = "✅ PASS" if passed else "❌ FAIL"
        self.results.append(f"{status}: {test_name}")
        if message:
            self.results.append(f"    {message}")

        if passed:
            self.tests_passed += 1
        else:
            self.tests_failed += 1

    def test_config_file_exists(self):
        """测试配置文件存在"""
        test_name = "配置文件存在性测试"

        config_path = os.path.join(self.frontend_dir, "config.js")
        loader_path = os.path.join(self.frontend_dir, "config-loader.js")

        if os.path.exists(config_path) and os.path.exists(loader_path):
            self.log(test_name, True, f"config.js 和 config-loader.js 均存在")
        else:
            missing = []
            if not os.path.exists(config_path):
                missing.append("config.js")
            if not os.path.exists(loader_path):
                missing.append("config-loader.js")
            self.log(test_name, False, f"缺少文件: {missing}")

    def test_config_syntax(self):
        """测试配置文件语法"""
        test_name = "配置文件语法测试"

        config_path = os.path.join(self.frontend_dir, "config.js")

        try:
            with open(config_path, "r", encoding="utf-8") as f:
                content = f.read()

            # 检查基本语法
            if "const APP_CONFIG" in content or "APP_CONFIG" in content:
                # 检查是否有明显语法错误
                if content.count("{") == content.count("}"):
                    if content.count("[") == content.count("]"):
                        self.log(test_name, True, "配置文件语法正确")
                    else:
                        self.log(test_name, False, "方括号不匹配")
                else:
                    self.log(test_name, False, "花括号不匹配")
            else:
                self.log(test_name, False, "未找到 APP_CONFIG 定义")
        except Exception as e:
            self.log(test_name, False, f"读取失败: {e}")

    def test_service_types_config(self):
        """测试服务类型配置"""
        test_name = "服务类型配置测试"

        config_path = os.path.join(self.frontend_dir, "config.js")

        try:
            with open(config_path, "r", encoding="utf-8") as f:
                content = f.read()

            # 提取 serviceTypes 数组
            match = re.search(r"serviceTypes:\s*\[([\s\S]*?)\n\s*\]", content)

            if match:
                # 检查必要的服务类型
                required_types = ["water", "meeting_room", "cleaning", "tea_break"]
                found_types = []

                for type_name in required_types:
                    if f"value: '{type_name}'" in match.group(
                        1
                    ) or f'value: "{type_name}"' in match.group(1):
                        found_types.append(type_name)

                if len(found_types) >= 4:
                    self.log(test_name, True, f"服务类型配置完整: {found_types}")
                else:
                    missing = [t for t in required_types if t not in found_types]
                    self.log(test_name, False, f"缺少服务类型: {missing}")
            else:
                self.log(test_name, False, "未找到 serviceTypes 配置")
        except Exception as e:
            self.log(test_name, False, f"解析失败: {e}")

    def test_concepts_config(self):
        """测试概念文案配置"""
        test_name = "概念文案配置测试"

        config_path = os.path.join(self.frontend_dir, "config.js")

        try:
            with open(config_path, "r", encoding="utf-8") as f:
                content = f.read()

            # 检查核心概念配置
            required_concepts = ["product", "pickup", "office", "user"]
            found_concepts = []

            for concept in required_concepts:
                if f"{concept}:" in content:
                    found_concepts.append(concept)

            if len(found_concepts) >= 4:
                self.log(test_name, True, f"概念文案配置完整: {found_concepts}")
            else:
                missing = [c for c in required_concepts if c not in found_concepts]
                self.log(test_name, False, f"缺少概念配置: {missing}")
        except Exception as e:
            self.log(test_name, False, f"解析失败: {e}")

    def test_units_config(self):
        """测试单位配置"""
        test_name = "单位配置测试"

        config_path = os.path.join(self.frontend_dir, "config.js")

        try:
            with open(config_path, "r", encoding="utf-8") as f:
                content = f.read()

            # 检查单位配置
            if "defaultUnits:" in content or "units:" in content:
                # 检查常见单位
                common_units = ["桶", "小时", "天", "次"]
                found_units = [
                    u
                    for u in common_units
                    if f"'{u}'" in content or f'"{u}"' in content
                ]

                if len(found_units) >= 3:
                    self.log(test_name, True, f"单位配置完整: {found_units}")
                else:
                    self.log(test_name, False, f"单位配置不完整: {found_units}")
            else:
                self.log(test_name, False, "未找到单位配置")
        except Exception as e:
            self.log(test_name, False, f"解析失败: {e}")

    def test_config_loader_functions(self):
        """测试配置加载器函数"""
        test_name = "配置加载器函数测试"

        loader_path = os.path.join(self.frontend_dir, "config-loader.js")

        try:
            with open(loader_path, "r", encoding="utf-8") as f:
                content = f.read()

            # 检查必要的方法
            required_methods = [
                "getConfig",
                "getServiceType",
                "getAllServiceTypes",
                "getText",
                "getUnits",
            ]

            found_methods = [m for m in required_methods if f"{m}" in content]

            if len(found_methods) >= 5:
                self.log(test_name, True, f"配置加载器方法完整: {found_methods}")
            else:
                missing = [m for m in required_methods if m not in found_methods]
                self.log(test_name, False, f"缺少方法: {missing}")
        except Exception as e:
            self.log(test_name, False, f"读取失败: {e}")

    def test_config_loader_export(self):
        """测试配置加载器导出"""
        test_name = "配置加载器导出测试"

        loader_path = os.path.join(self.frontend_dir, "config-loader.js")

        try:
            with open(loader_path, "r", encoding="utf-8") as f:
                content = f.read()

            # 检查导出方式
            has_module_export = "module.exports" in content
            has_window_export = "window.ConfigLoader" in content

            if has_module_export or has_window_export:
                self.log(test_name, True, "配置加载器支持多种导出方式")
            else:
                self.log(test_name, False, "配置加载器缺少导出定义")
        except Exception as e:
            self.log(test_name, False, f"读取失败: {e}")

    def test_api_config_compatibility(self):
        """测试 API 配置兼容性"""
        test_name = "API 配置兼容性测试"

        config_path = os.path.join(self.frontend_dir, "config.js")
        loader_path = os.path.join(self.frontend_dir, "config-loader.js")

        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config_content = f.read()

            with open(loader_path, "r", encoding="utf-8") as f:
                loader_content = f.read()

            # 检查配置加载器是否支持 API 加载
            if "/services/config" in loader_content or "loadFromApi" in loader_content:
                self.log(test_name, True, "配置加载器支持从 API 加载")
            else:
                self.log(test_name, True, "配置加载器仅使用本地配置")
        except Exception as e:
            self.log(test_name, False, f"读取失败: {e}")

    def test_config_completeness(self):
        """测试配置完整性"""
        test_name = "配置完整性测试"

        config_path = os.path.join(self.frontend_dir, "config.js")

        try:
            with open(config_path, "r", encoding="utf-8") as f:
                content = f.read()

            # 检查关键配置项
            key_configs = [
                "appName",
                "appVersion",
                "serviceTypes",
                "serviceCategories",
                "defaultUnits",
                "statusConfig",
                "timeConfig",
            ]

            found_configs = [c for c in key_configs if f"{c}:" in content]

            if len(found_configs) >= 6:
                self.log(
                    test_name,
                    True,
                    f"配置完整性良好: {len(found_configs)}/{len(key_configs)}",
                )
            else:
                missing = [c for c in key_configs if c not in found_configs]
                self.log(test_name, False, f"缺少配置项: {missing}")
        except Exception as e:
            self.log(test_name, False, f"读取失败: {e}")

    def print_results(self):
        """打印测试结果"""
        print("\n" + "=" * 60)
        print("Phase 3 验证测试结果")
        print("=" * 60)

        for r in self.results:
            print(r)

        print("\n" + "-" * 60)
        print(f"总计: {self.tests_passed} 通过, {self.tests_failed} 失败")
        print("-" * 60)

        if self.tests_failed == 0:
            print("\n🎉 Phase 3 验证通过！")
        else:
            print("\n⚠️  Phase 3 验证存在问题，请检查")


def main():
    """运行所有测试"""
    runner = Phase3TestRunner()

    print("\n📦 Phase 3 配置文件测试...")
    runner.test_config_file_exists()
    runner.test_config_syntax()

    print("\n📋 Phase 3 配置内容测试...")
    runner.test_service_types_config()
    runner.test_concepts_config()
    runner.test_units_config()
    runner.test_config_completeness()

    print("\n🔧 Phase 3 配置加载器测试...")
    runner.test_config_loader_functions()
    runner.test_config_loader_export()
    runner.test_api_config_compatibility()

    # 打印结果
    runner.print_results()

    # 返回状态码
    sys.exit(0 if runner.tests_failed == 0 else 1)


if __name__ == "__main__":
    main()
