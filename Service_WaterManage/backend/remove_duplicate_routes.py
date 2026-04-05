#!/usr/bin/env python3
"""
Phase 1: 清理main.py中与模块化文件重复的路由
通过注释而非删除的方式，便于回滚和验证
"""

import re
from pathlib import Path


def find_route_block(lines, start_idx):
    """找到路由函数的结束位置"""
    indent_level = 0
    in_function = False
    start_indent = None

    for i in range(start_idx, len(lines)):
        line = lines[i]

        # 检测函数开始
        if re.match(r"^@app\.(get|post|put|delete|patch)", line):
            in_function = True
            continue

        if in_function and re.match(r"^def\s+\w+\s*\(", line):
            start_indent = len(line) - len(line.lstrip())
            continue

        if start_indent is not None:
            current_indent = len(line) - len(line.lstrip())

            # 如果遇到同级或更高级的def或@，说明函数结束
            if line.strip() and current_indent <= start_indent:
                if re.match(
                    r"^(def\s|@app\.|class\s)", line.strip()
                ) or line.strip().startswith("@app"):
                    return i - 1

            # 如果到达文件末尾
            if i == len(lines) - 1:
                return i

    return len(lines) - 1


def comment_out_block(lines, start, end, message="DUPLICATE - 已移至模块化文件"):
    """注释掉指定范围的代码块"""
    result = []

    # 添加注释标记
    result.append(f"# ===== {message} =====\n")
    result.append(f"# 原始位置: 行 {start + 1}-{end + 1}\n")
    result.append(f"# ===== 以下代码已被注释 =====\n")

    # 注释每一行
    for i in range(start, end + 1):
        if lines[i].strip():
            result.append("# " + lines[i])
        else:
            result.append("\n")

    result.append("# ===== 注释结束 =====\n\n")

    return result


def main():
    main_py = Path(__file__).parent / "main.py"

    with open(main_py, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # 定义需要注释的重复路由
    # 格式: (路由模式, 描述)
    duplicate_routes = [
        # 认证API
        (r'@app\.post\("/api/auth/login"', "认证API - 已移至 api/auth.py"),
        (r'@app\.get\("/api/auth/me"', "认证API - 已移至 api/auth.py"),
        (r'@app\.post\("/api/auth/change-password"', "认证API - 已移至 api/auth.py"),
        # 用户办公室API
        (r'@app\.get\("/api/user/offices"', "用户办公室API - 已移至 api/water.py"),
        # 产品API
        (r'@app\.get\("/api/products"', "产品API - 已移至 api/products.py"),
        (r'@app\.post\("/api/products"', "产品API - 已移至 api/products.py"),
        (
            r'@app\.put\("/api/products/\{product_id\}"\)$',
            "产品API - 已移至 api/products.py",
        ),
        (
            r'@app\.delete\("/api/products/\{product_id\}"',
            "产品API - 已移至 api/products.py",
        ),
        (
            r'@app\.put\("/api/products/\{product_id\}/toggle"',
            "产品API - 已移至 api/products.py",
        ),
        (
            r'@app\.put\("/api/products/\{product_id\}/protect"',
            "产品API - 已移至 api/products.py",
        ),
        (
            r'@app\.put\("/api/products/\{product_id\}/stock"',
            "产品API - 已移至 api/products.py",
        ),
        (
            r'@app\.put\("/api/products/\{product_id\}/promo-toggle"',
            "产品API - 已移至 api/products.py",
        ),
        # 产品分类API
        (
            r'@app\.get\("/api/admin/product-categories"',
            "产品分类API - 已移至 api/products.py",
        ),
        (
            r'@app\.post\("/api/admin/product-categories"',
            "产品分类API - 已移至 api/products.py",
        ),
        (
            r'@app\.put\("/api/admin/product-categories/\{category_id\}"',
            "产品分类API - 已移至 api/products.py",
        ),
        (
            r'@app\.delete\("/api/admin/product-categories/\{category_id\}"',
            "产品分类API - 已移至 api/products.py",
        ),
        # 领水API
        (r'@app\.post\("/api/user/office-pickup"', "领水API - 已移至 api/water.py"),
        (
            r'@app\.put\("/api/admin/office-pickups/\{pickup_id\}"',
            "领水API - 已移至 api/water.py",
        ),
        (
            r'@app\.delete\("/api/admin/office-pickups/\{pickup_id\}"\)$',
            "领水API - 已移至 api/water.py",
        ),
        (r'@app\.get\("/api/user/office-pickups"', "领水API - 已移至 api/water.py"),
        (
            r'@app\.get\("/api/user/office-pickup-summary"',
            "领水API - 已移至 api/water.py",
        ),
        # 结算API
        (r'@app\.post\("/api/admin/settlement/apply"', "结算API - 已移至 api/water.py"),
        (
            r'@app\.post\("/api/admin/settlement/\{pickup_id\}/confirm"',
            "结算API - 已移至 api/water.py",
        ),
        (
            r'@app\.post\("/api/admin/settlement/\{pickup_id\}/reject"',
            "结算API - 已移至 api/water.py",
        ),
        (
            r'@app\.post\("/api/admin/settlement/batch-confirm"',
            "结算API - 已移至 api/water.py",
        ),
        # 回收站API
        (
            r'@app\.get\("/api/admin/office-pickups/trash"',
            "回收站API - 已移至 api/water.py",
        ),
        (
            r'@app\.post\("/api/admin/office-pickups/trash/restore"',
            "回收站API - 已移至 api/water.py",
        ),
        (
            r'@app\.delete\("/api/admin/office-pickups/trash/\{pickup_id\}"',
            "回收站API - 已移至 api/water.py",
        ),
    ]

    # 找到所有需要注释的路由
    routes_to_comment = []

    for i, line in enumerate(lines):
        for pattern, desc in duplicate_routes:
            if re.search(pattern, line):
                end = find_route_block(lines, i)
                routes_to_comment.append((i, end, desc))
                break

    # 按位置排序（从后往前处理，避免索引变化）
    routes_to_comment.sort(key=lambda x: x[0], reverse=True)

    # 注释掉这些路由
    modified_lines = lines.copy()

    for start, end, desc in routes_to_comment:
        # 注释掉这个代码块
        commented = comment_out_block(modified_lines, start, end, desc)

        # 替换原代码
        modified_lines = modified_lines[:start] + commented + modified_lines[end + 1 :]

        print(f"✅ 已注释: {desc} (原行 {start + 1}-{end + 1})")

    # 写回文件
    with open(main_py, "w", encoding="utf-8") as f:
        f.writelines(modified_lines)

    print(f"\n✅ Phase 1 完成！共注释 {len(routes_to_comment)} 个重复路由")
    print(f"   main.py: {len(lines)} 行 -> {len(modified_lines)} 行")


if __name__ == "__main__":
    main()
