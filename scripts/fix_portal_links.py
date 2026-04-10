#!/usr/bin/env python3
"""
Portal链接修复工具
自动修复HTML文件中的错误路径
"""

import os
import re
from pathlib import Path


class LinkFixer:
    def __init__(self, base_dir):
        self.base_dir = Path(base_dir)
        self.fixes = []

    def fix_all(self):
        """修复所有链接问题"""
        print("开始修复portal链接...")

        # 修复portal目录下的HTML文件
        portal_dir = self.base_dir / "portal"
        if portal_dir.exists():
            self.fix_portal_files(portal_dir)

        # 输出修复报告
        self.print_report()

    def fix_portal_files(self, portal_dir):
        """修复portal目录下的文件"""
        # 修复portal/xxx.html文件（一级目录）
        for html_file in portal_dir.glob("*.html"):
            self.fix_portal_root_file(html_file)

        # 修复portal/admin/water文件
        water_dir = portal_dir / "admin" / "water"
        if water_dir.exists():
            for html_file in water_dir.glob("*.html"):
                self.fix_water_admin_file(html_file)

        # 修复portal/admin/meeting文件
        meeting_dir = portal_dir / "admin" / "meeting"
        if meeting_dir.exists():
            for html_file in meeting_dir.glob("*.html"):
                self.fix_meeting_admin_file(html_file)

    def fix_portal_root_file(self, file_path):
        """修复portal根目录下的HTML文件"""
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        original_content = content

        # 修复CSS路径: ../assets/css/ -> ./assets/css/ 或 /portal/assets/css/
        content = re.sub(
            r'href=["\']\.\./assets/css/', 'href="/portal/assets/css/', content
        )

        # 修复components路径: ../components/ -> ./components/ 或 /portal/components/
        content = re.sub(
            r'(href|src)=["\']\.\./components/', r'\1="/portal/components/', content
        )

        if content != original_content:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            self.fixes.append(
                {"file": file_path.name, "fix": "修复CSS和components路径"}
            )

    def fix_water_admin_file(self, file_path):
        """修复portal/admin/water目录下的HTML文件"""
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        original_content = content

        # 修复Vue引用: ../../node_modules/vue/ -> CDN
        content = re.sub(
            r'<script src=["\']\.\./\.\./node_modules/vue/dist/vue\.global\.prod\.js["\']></script>',
            '<script src="https://unpkg.com/vue@3/dist/vue.global.prod.js"></script>',
            content,
        )

        # 修复api-config.js路径
        content = re.sub(
            r'src=["\']\.\./\.\./shared/utils/api-config\.js["\']',
            'src="/shared/utils/api-config.js"',
            content,
        )

        if content != original_content:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            self.fixes.append(
                {
                    "file": f"admin/water/{file_path.name}",
                    "fix": "修复Vue和api-config路径",
                }
            )

    def fix_meeting_admin_file(self, file_path):
        """修复portal/admin/meeting目录下的HTML文件"""
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        original_content = content

        # 修复api-config.js路径
        content = re.sub(
            r'src=["\']\.\./\.\./shared/utils/api-config\.js["\']',
            'src="/shared/utils/api-config.js"',
            content,
        )

        if content != original_content:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            self.fixes.append(
                {"file": f"admin/meeting/{file_path.name}", "fix": "修复api-config路径"}
            )

    def print_report(self):
        """打印修复报告"""
        if self.fixes:
            print(f"\n✅ 已修复 {len(self.fixes)} 个文件:\n")
            for fix in self.fixes:
                print(f"📄 {fix['file']}: {fix['fix']}")
        else:
            print("\n✅ 没有需要修复的文件")


if __name__ == "__main__":
    fixer = LinkFixer("/Users/sgl/PycharmProjects/AIchanyejiqun")
    fixer.fix_all()
