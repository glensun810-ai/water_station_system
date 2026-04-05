#!/usr/bin/env python3
"""
注释main.py中重复的路由
"""

from pathlib import Path
import re


def comment_route_block(content, route_pattern, start_hint=None):
    """注释掉匹配的路由块"""
    lines = content.split("\n")

    # 找到路由开始
    start_idx = None
    for i, line in enumerate(lines):
        if re.search(route_pattern, line):
            if start_hint is None or start_hint in line:
                start_idx = i
                break

    if start_idx is None:
        return content, False

    # 找到函数结束
    # 向下查找，直到遇到下一个同级定义或空行后的新定义
    indent_count = 0
    func_started = False
    end_idx = start_idx

    for i in range(start_idx, len(lines)):
        line = lines[i]

        # 检测装饰器
        if line.strip().startswith("@app."):
            if i > start_idx:
                # 遇到下一个路由装饰器，结束
                end_idx = i - 1
                break

        # 检测函数定义
        if line.strip().startswith("def "):
            func_started = True
            # 获取缩进级别
            indent_count = len(line) - len(line.lstrip())

        # 检测下一个同级定义
        if func_started and line.strip() and not line.strip().startswith("#"):
            current_indent = len(line) - len(line.lstrip())
            if current_indent <= indent_count and (
                line.strip().startswith("def ")
                or line.strip().startswith("@app.")
                or line.strip().startswith("class ")
            ):
                end_idx = i - 1
                break

        end_idx = i

    # 注释掉这个块
    commented_lines = []
    for i in range(start_idx, end_idx + 1):
        if lines[i].strip():
            commented_lines.append("    # " + lines[i])
        else:
            commented_lines.append("")

    # 替换原内容
    new_lines = lines[:start_idx] + commented_lines + lines[end_idx + 1 :]

    return "\n".join(new_lines), True


def main():
    main_py = Path(__file__).parent / "main.py"

    with open(main_py, "r", encoding="utf-8") as f:
        content = f.read()

    original_lines = len(content.split("\n"))

    # 定义要注释的路由
    routes_to_comment = [
        # 产品API
        (r'@app\.get\("/api/products"', None),
        (r'@app\.post\("/api/products"', None),
        (r'@app\.get\("/api/products/\{product_id\}"', None),
        (r'@app\.delete\("/api/products/\{product_id\}"\)', None),
        (r'@app\.put\("/api/products/\{product_id\}/toggle"', None),
        (r'@app\.put\("/api/products/\{product_id\}/protect"', None),
        (r'@app\.put\("/api/products/\{product_id\}"\)', "def update_product"),
        (r'@app\.put\("/api/products/\{product_id\}/stock"', None),
        (r'@app\.put\("/api/products/\{product_id\}/promo-toggle"', None),
        # 分类API
        (r'@app\.get\("/api/admin/product-categories"', None),
        (r'@app\.post\("/api/admin/product-categories"', None),
        (r'@app\.put\("/api/admin/product-categories/\{category_id\}"', None),
        (r'@app\.delete\("/api/admin/product-categories/\{category_id\}"', None),
    ]

    for pattern, hint in routes_to_comment:
        content, success = comment_route_block(content, pattern, hint)
        if success:
            print(f"✅ 注释: {pattern}")
        else:
            print(f"⚠️  未找到: {pattern}")

    with open(main_py, "w", encoding="utf-8") as f:
        f.write(content)

    new_lines = len(content.split("\n"))
    print(f"\n✅ 完成！行数: {original_lines} -> {new_lines}")


if __name__ == "__main__":
    main()
