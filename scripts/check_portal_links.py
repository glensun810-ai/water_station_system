#!/usr/bin/env python3
"""
Portal系统链接检查工具
检查所有HTML文件中的链接是否正确
"""

import os
import re
from pathlib import Path
from urllib.parse import urlparse


class LinkChecker:
    def __init__(self, base_dir):
        self.base_dir = Path(base_dir)
        self.errors = []
        self.warnings = []
        self.checked_files = []

    def check_all(self):
        """检查所有HTML文件"""
        print("=" * 80)
        print("AI产业集群Portal系统链接检查报告")
        print("=" * 80)
        print()

        # 检查portal目录下所有HTML文件
        portal_dir = self.base_dir / "portal"
        if portal_dir.exists():
            self.check_directory(portal_dir)

        # 输出报告
        self.print_report()

    def check_directory(self, directory):
        """递归检查目录下的所有HTML文件"""
        for item in directory.iterdir():
            if item.is_file() and item.suffix == ".html":
                self.check_html_file(item)
            elif item.is_dir() and item.name not in [
                "Backup",
                "backup",
                "node_modules",
            ]:
                self.check_directory(item)

    def check_html_file(self, file_path):
        """检查单个HTML文件中的所有链接"""
        relative_path = file_path.relative_to(self.base_dir)
        self.checked_files.append(str(relative_path))

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # 提取所有href属性
            href_pattern = r'href=["\']([^"\']+)["\']'
            hrefs = re.findall(href_pattern, content)

            # 提取所有src属性
            src_pattern = r'src=["\']([^"\']+)["\']'
            srcs = re.findall(src_pattern, content)

            all_links = hrefs + srcs

            for link in all_links:
                self.check_link(link, file_path)

        except Exception as e:
            self.errors.append(
                {
                    "file": str(relative_path),
                    "link": "N/A",
                    "error": f"文件读取失败: {str(e)}",
                }
            )

    def check_link(self, link, source_file):
        """检查单个链接"""
        # 跳过外部链接、锚点、JavaScript和特殊协议
        if (
            link.startswith("http://")
            or link.startswith("https://")
            or link.startswith("#")
            or link.startswith("javascript:")
            or link.startswith("mailto:")
            or link.startswith("tel:")
            or link.startswith("data:")
        ):
            return

        # 检查路径问题
        issues = []

        # 1. 检查是否有重复的admin
        if "/admin/admin/" in link:
            issues.append(f"❌ 路径重复: 包含/admin/admin/")

        # 2. 检查是否指向旧架构路径
        old_paths = [
            "/water/frontend/",
            "/meeting/frontend/",
            "/Service_WaterManage/",
            "/Service_MeetingRoom/",
        ]
        for old_path in old_paths:
            if old_path in link:
                issues.append(f"⚠️  旧架构路径: 包含{old_path}")

        # 3. 检查是否以/portal开头（应该是）
        if (
            link.startswith("/")
            and not link.startswith("/portal/")
            and not link.startswith("/shared/")
        ):
            # 允许的例外
            allowed_exceptions = [
                "/meeting-frontend/",  # 会议室前端独立部署
                "/water/",  # 水站前端独立部署（待重构）
                "/api/",  # API路径
                "/docs",  # 文档路径
                "/favicon.svg",  # favicon
            ]
            if not any(link.startswith(exc) for exc in allowed_exceptions):
                issues.append(f"⚠️  路径不规范: 应以/portal/开头")

        # 4. 检查文件是否存在（仅对相对路径和portal路径）
        if (
            link.startswith("/portal/")
            or link.startswith("./")
            or link.startswith("../")
            or (not link.startswith("/"))
        ):
            target_path = self.resolve_link_path(link, source_file)
            if target_path and not target_path.exists():
                # 检查是否是目录（有些链接指向目录，会自动加载index.html）
                if not (
                    target_path.is_dir()
                    or (target_path.parent.exists() and target_path.name == "")
                ):
                    issues.append(f"❌ 文件不存在: {link}")

        # 记录问题
        if issues:
            relative_source = source_file.relative_to(self.base_dir)
            for issue in issues:
                self.errors.append(
                    {"file": str(relative_source), "link": link, "error": issue}
                )

    def resolve_link_path(self, link, source_file):
        """解析链接的实际文件路径"""
        try:
            if link.startswith("/portal/"):
                # 绝对路径，从base_dir开始
                return self.base_dir / link.lstrip("/")
            elif link.startswith("/"):
                # 其他绝对路径（如/shared/）
                return self.base_dir / link.lstrip("/")
            elif link.startswith("./") or link.startswith("../"):
                # 相对路径
                return (source_file.parent / link).resolve()
            else:
                # 相对路径（无./前缀）
                return (source_file.parent / link).resolve()
        except:
            return None

    def print_report(self):
        """打印检查报告"""
        print(f"✅ 已检查 {len(self.checked_files)} 个HTML文件\n")

        if self.errors:
            print(f"❌ 发现 {len(self.errors)} 个链接问题:\n")

            # 按文件分组
            errors_by_file = {}
            for error in self.errors:
                file = error["file"]
                if file not in errors_by_file:
                    errors_by_file[file] = []
                errors_by_file[file].append(error)

            for file, errors in errors_by_file.items():
                print(f"📄 {file}")
                for error in errors:
                    print(f"   {error['error']}")
                    print(f"   链接: {error['link']}")
                    print()
        else:
            print("✅ 所有链接检查通过!\n")

        # 统计信息
        print("=" * 80)
        print("检查完成!")
        print(f"检查文件数: {len(self.checked_files)}")
        print(f"发现问题数: {len(self.errors)}")
        print("=" * 80)


if __name__ == "__main__":
    checker = LinkChecker("/Users/sgl/PycharmProjects/AIchanyejiqun")
    checker.check_all()
