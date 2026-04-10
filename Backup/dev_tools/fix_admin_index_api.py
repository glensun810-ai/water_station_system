"""
手动修复管理后台首页API_BASE
"""

import re

file_path = "./portal/admin/index.html"

with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# 替换API_BASE定义
old_api_base = r"const API_BASE = window\.location\.origin;"
new_api_base = r"const API_BASE = `${window.location.protocol}//${window.location.hostname}:${window.location.port || '8008'}/api/v1`;"

content = re.sub(old_api_base, new_api_base, content)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)

print("✓ 已修复管理后台首页API_BASE")

# 验证修复
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

if (
    "const API_BASE = `${window.location.protocol}//${window.location.hostname}:${window.location.port || '8008'}/api/v1`;"
    in content
):
    print("✓ 验证成功：API_BASE已正确修复")
else:
    print("✗ 验证失败：API_BASE未修复")
